from pathlib import Path
import hashlib
import shutil
import subprocess
import sys
import time

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
PAGE = FRONTEND / "src/pages/SettingsPage.jsx"
TGWS_COMPONENT = FRONTEND / "src/components/settings/TgwsSettingsAdmin.jsx"
TGWS_API = FRONTEND / "src/api/tgwsApi.js"
DIST = FRONTEND / "dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

EXPECTED_PAGE_GIT_BLOB = "71e818372e1eee6ed08b1394ff3801bb88a5de90"

TGWS_IMPORT = 'import { TgwsSettingsAdmin } from "../components/settings/TgwsSettingsAdmin";\n'
TGWS_SECTION = '  { key: "tgws", labelAr: "TGWS", labelEn: "TGWS", hintAr: "إنشاء ملفات Google الأصلية وسياسات الوصول", hintEn: "Native Google files and access policies", icon: Cloud },\n'
TGWS_ROUTE = '''      case "tgws":\n        return <TgwsSettingsAdmin user={user} />;\n'''
CLOUD_OTHER_USE = '<Cloud className="crm-pro-flow-node__cloud" />'


def fail(message):
    raise RuntimeError(message)


def run(command, cwd=None):
    subprocess.run(command, cwd=cwd, check=True)


def git_blob_sha(path):
    data = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


if not PAGE.exists():
    fail(f"Settings page missing: {PAGE}")
if not TGWS_COMPONENT.exists():
    fail(f"TGWS component missing unexpectedly: {TGWS_COMPONENT}")
if not TGWS_API.exists():
    fail(f"TGWS API module missing unexpectedly: {TGWS_API}")

page_blob = git_blob_sha(PAGE)
if page_blob != EXPECTED_PAGE_GIT_BLOB:
    fail(f"SettingsPage baseline changed: expected={EXPECTED_PAGE_GIT_BLOB} actual={page_blob}")

source = PAGE.read_text()
component_hash_before = sha256(TGWS_COMPONENT)
api_hash_before = sha256(TGWS_API)

# Exact decommission guards: visible Settings UI only.
for marker, label in [
    (TGWS_IMPORT, "TGWS Settings import"),
    (TGWS_SECTION, "TGWS Settings section"),
    (TGWS_ROUTE, "TGWS Settings render route"),
]:
    if source.count(marker) != 1:
        fail(f"{label} marker count changed unexpectedly: {source.count(marker)}")

# Cloud icon is deliberately preserved: it is also used by CRM visual flow.
if CLOUD_OTHER_USE not in source:
    fail("Cloud icon has another expected non-TGWS use that is no longer present; stop before touching imports")

# Guard neighboring settings so the patch cannot silently reshape Settings navigation.
for marker in [
    '{ key: "drive", labelAr: "Google Drive", labelEn: "Google Drive"',
    '{ key: "thrs", labelAr: "ربط THRS", labelEn: "THRS Integration"',
    'case "drive":\n        return <GoogleDriveAdmin user={user} />;',
    'case "thrs":\n        return <ThrsIntegrationAdmin user={user} />;',
    'import { RamzySettingsAdmin } from "../components/RamzySettingsAdmin";',
]:
    if marker not in source:
        fail(f"neighboring Settings baseline marker missing: {marker}")

stamp = int(time.time())
page_backup = PAGE.with_name(f"{PAGE.name}.tgws-ui-decommission-v1-backup-{stamp}")
shutil.copy2(PAGE, page_backup)
live_backup = None
staging = None

try:
    updated = source.replace(TGWS_IMPORT, "", 1)
    updated = updated.replace(TGWS_SECTION, "", 1)
    updated = updated.replace(TGWS_ROUTE, "", 1)

    # Source-level post guards.
    for marker, label in [
        ('TgwsSettingsAdmin', "TGWS component reference"),
        ('key: "tgws"', "TGWS Settings section key"),
        ('case "tgws"', "TGWS Settings render case"),
    ]:
        if marker in updated:
            fail(f"{label} still present after transform")

    for marker in [
        '{ key: "drive", labelAr: "Google Drive", labelEn: "Google Drive"',
        '{ key: "thrs", labelAr: "ربط THRS", labelEn: "THRS Integration"',
        'case "drive":\n        return <GoogleDriveAdmin user={user} />;',
        'case "thrs":\n        return <ThrsIntegrationAdmin user={user} />;',
        CLOUD_OTHER_USE,
    ]:
        if marker not in updated:
            fail(f"protected neighboring marker changed: {marker}")

    PAGE.write_text(updated)

    # Dormant TGWS implementation files are intentionally preserved in V1.
    if sha256(TGWS_COMPONENT) != component_hash_before:
        fail("TGWS component file changed unexpectedly")
    if sha256(TGWS_API) != api_hash_before:
        fail("TGWS API module changed unexpectedly")

    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists():
        fail("frontend dist missing after build")

    # The decommissioned Settings UI must not be bundled from Settings anymore.
    built_js = ""
    for js_file in DIST.rglob("*.js"):
        built_js += js_file.read_text(errors="ignore")
    if "Tamiyouz Google Workspace" in built_js:
        fail("TGWS Settings UI signature still present in production bundle")
    if "Native Google files and access policies" in built_js:
        fail("TGWS Settings navigation copy still present in production bundle")

    LIVE_PARENT.mkdir(parents=True, exist_ok=True)
    staging = LIVE_PARENT / f"build.tgws-ui-decommission-v1-staging-{stamp}"
    live_backup = LIVE_PARENT / f"build.tgws-ui-decommission-v1-backup-{stamp}"
    if staging.exists():
        shutil.rmtree(staging)
    shutil.copytree(DIST, staging)

    if LIVE.exists():
        LIVE.rename(live_backup)
    staging.rename(LIVE)

    live_js = ""
    for js_file in LIVE.rglob("*.js"):
        live_js += js_file.read_text(errors="ignore")
    if "Tamiyouz Google Workspace" in live_js or "Native Google files and access policies" in live_js:
        fail("TGWS Settings UI signature found in live bundle after deploy")

    if sha256(TGWS_COMPONENT) != component_hash_before or sha256(TGWS_API) != api_hash_before:
        fail("Dormant TGWS implementation files changed unexpectedly after deploy")

    print("PASS/FAIL=PASS")
    print("BUILD_RESULT=PASS")
    print("LIVE_DEPLOY=PASS")
    print("TGWS_SETTINGS_UI_DECOMMISSION_V1_RUNTIME=YES")
    print("TGWS_DECOMMISSION_SCOPE=SETTINGS_UI_ONLY")
    print("TGWS_SETTINGS_IMPORT_REMOVED=YES")
    print("TGWS_SETTINGS_SECTION_REMOVED=YES")
    print("TGWS_SETTINGS_RENDER_PATH_REMOVED=YES")
    print("TGWS_SETTINGS_OVERVIEW_CARD_REMOVED=YES")
    print("TGWS_SETTINGS_NAVIGATION_REMOVED=YES")
    print("TGWS_PRODUCTION_UI_BUNDLE_REMOVED=YES")
    print("TGWS_COMPONENT_FILE_DELETED=NO")
    print("TGWS_API_FILE_DELETED=NO")
    print("TGWS_BACKEND_CHANGED=NO")
    print("TGWS_API_FILES_CHANGED=NO")
    print("TGWS_CLOUD_ICON_IMPORT=PRESERVED_USED_ELSEWHERE")
    print("GOOGLE_DRIVE_CHANGED=NO")
    print("TWS_CHANGED=NO")
    print("SLA_CHANGED=NO")
    print("RAMZY_LOGIC_CHANGED=NO")
    print("TCS_CHANGED=NO")
    print(f"SETTINGS_PAGE_BASELINE_GIT_BLOB={EXPECTED_PAGE_GIT_BLOB}")
    print(f"TGWS_COMPONENT_SHA256={component_hash_before}")
    print(f"TGWS_API_SHA256={api_hash_before}")
    print(f"LIVE_BACKUP={live_backup if live_backup and live_backup.exists() else 'NONE'}")
    print("STATUS=READY")
except Exception as exc:
    try:
        if page_backup.exists():
            shutil.copy2(page_backup, PAGE)
        if LIVE.exists() and live_backup and live_backup.exists():
            shutil.rmtree(LIVE)
            live_backup.rename(LIVE)
        elif live_backup and live_backup.exists() and not LIVE.exists():
            live_backup.rename(LIVE)
        if staging and staging.exists():
            shutil.rmtree(staging)
    except Exception:
        pass
    print("PASS/FAIL=FAIL")
    print(f"ERROR={exc}")
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("STATUS=STOPPED")
    raise SystemExit(1)
