from pathlib import Path
import hashlib
import re
import shutil
import subprocess
import sys
import time

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
PAGE = FRONTEND / "src/pages/SettingsPage.jsx"
STYLE = FRONTEND / "src/pages/smtpSettingsFlagshipLuxuryV1.css"
DIST = FRONTEND / "dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

PATCH_ROOT = Path(__file__).resolve().parent.parent
V1_INSTALLER = PATCH_ROOT / "TOS-UXUI-SYSTEM-SETTINGS-SMTP-EMAIL-FLAGSHIP-LUXURY-V1" / "apply_tos_uxui_system_settings_smtp_email_flagship_luxury_v1.py"

EXPECTED_PAGE_GIT_BLOB = "5d60d9802b5c65dfcd14690bea9240f0f2b37ab7"
IMPORT_ANCHOR = 'import "./settingsOverviewFlagshipV2_1FidelityPolish.css";'
IMPORT_STYLE = 'import "./smtpSettingsFlagshipLuxuryV1.css";'
SMTP_START = "function EmailSettingsAdmin({ user })"
SMTP_END = "\nfunction GoogleDriveAdmin({ user })"
ROOT_OLD = '''  return (\n    <Card>\n      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">'''
ROOT_NEW = '''  return (\n    <Card className="tos-smtp-settings-flagship-v1">\n      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">'''
RUNTIME_MARKER = "--tos-smtp-settings-flagship-luxury-v1-runtime"


def fail(message):
    raise RuntimeError(message)


def git_blob_sha(path: Path):
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def run(command, cwd=None):
    subprocess.run(command, cwd=cwd, check=True)


def extract_v1_css():
    if not V1_INSTALLER.exists():
        fail(f"original SMTP V1 installer missing: {V1_INSTALLER}")
    text = V1_INSTALLER.read_text()
    match = re.search(r"CSS = r'''(.*?)'''\n\n\ndef fail", text, flags=re.S)
    if not match:
        fail("unable to extract CSS payload from original SMTP V1 installer")
    css = match.group(1)
    if RUNTIME_MARKER not in css:
        fail("original SMTP V1 CSS runtime marker missing")
    if ".tos-smtp-settings-flagship-v1" not in css:
        fail("original SMTP V1 CSS scope marker missing")
    return css


if not PAGE.exists():
    fail(f"Settings page missing: {PAGE}")

page_blob = git_blob_sha(PAGE)
if page_blob != EXPECTED_PAGE_GIT_BLOB:
    fail(f"Settings page baseline mismatch: expected={EXPECTED_PAGE_GIT_BLOB} actual={page_blob}")

source = PAGE.read_text()
for marker in [
    IMPORT_ANCHOR,
    SMTP_START,
    SMTP_END,
    "api.emailSettings.status()",
    "api.emailSettings.update(payload)",
    "api.emailSettings.test({ to: form.testTo.trim() || undefined })",
    'Email / SMTP',
    'SMTP Email Settings',
]:
    if marker not in source:
        fail(f"required SMTP baseline marker missing: {marker}")

if IMPORT_STYLE in source or STYLE.exists():
    fail("SMTP Settings Flagship Luxury V1 already present")

smtp_start = source.index(SMTP_START)
smtp_end = source.index(SMTP_END, smtp_start)
smtp_segment = source[smtp_start:smtp_end]

# R1 fix: the generic Card return marker occurs in several Settings subcomponents.
# Guard and replace ONLY inside EmailSettingsAdmin.
if smtp_segment.count(ROOT_OLD) != 1:
    fail(f"SMTP scoped root marker count unexpected: {smtp_segment.count(ROOT_OLD)}")

css = extract_v1_css()

stamp = int(time.time())
page_backup = PAGE.with_name(f"{PAGE.name}.smtp-settings-v1-r1-backup-{stamp}")
shutil.copy2(PAGE, page_backup)
live_backup = None
staging = None

try:
    source = source.replace(IMPORT_ANCHOR, IMPORT_ANCHOR + "\n" + IMPORT_STYLE, 1)

    smtp_start = source.index(SMTP_START)
    smtp_end = source.index(SMTP_END, smtp_start)
    smtp_segment = source[smtp_start:smtp_end]
    smtp_segment = smtp_segment.replace(ROOT_OLD, ROOT_NEW, 1)
    source = source[:smtp_start] + smtp_segment + source[smtp_end:]

    post_segment = source[source.index(SMTP_START):source.index(SMTP_END, source.index(SMTP_START))]
    for marker in [
        IMPORT_STYLE,
        'className="tos-smtp-settings-flagship-v1"',
        "api.emailSettings.status()",
        "api.emailSettings.update(payload)",
        "api.emailSettings.test({ to: form.testTo.trim() || undefined })",
    ]:
        if marker == IMPORT_STYLE:
            if marker not in source:
                fail(f"post-transform marker missing: {marker}")
        elif marker not in post_segment:
            fail(f"post-transform SMTP marker missing: {marker}")

    PAGE.write_text(source)
    STYLE.write_text(css)

    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists():
        fail("frontend dist missing after build")

    built_css = ""
    for css_file in DIST.rglob("*.css"):
        built_css += css_file.read_text(errors="ignore")
    if RUNTIME_MARKER not in built_css:
        fail("SMTP Settings Flagship Luxury V1 runtime marker missing from built CSS")

    LIVE_PARENT.mkdir(parents=True, exist_ok=True)
    staging = LIVE_PARENT / f"build.smtp-settings-v1-r1-staging-{stamp}"
    live_backup = LIVE_PARENT / f"build.smtp-settings-v1-r1-backup-{stamp}"
    if staging.exists():
        shutil.rmtree(staging)
    shutil.copytree(DIST, staging)

    if LIVE.exists():
        LIVE.rename(live_backup)
    staging.rename(LIVE)

    live_css = ""
    for css_file in LIVE.rglob("*.css"):
        live_css += css_file.read_text(errors="ignore")
    if RUNTIME_MARKER not in live_css:
        fail("SMTP Settings Flagship Luxury V1 runtime marker missing from live build")

    print("PASS/FAIL=PASS")
    print("BUILD_RESULT=PASS")
    print("LIVE_DEPLOY=PASS")
    print("SMTP_SETTINGS_FLAGSHIP_LUXURY_V1_R1_RUNTIME=YES")
    print("SMTP_ROOT_RECONCILE=EMAIL_SETTINGS_ADMIN_SCOPED")
    print("SMTP_GENERIC_ROOT_COLLISIONS_OUTSIDE_SCOPE=IGNORED_SAFELY")
    print("SMTP_SETTINGS_SCOPE=VISUAL_ONLY")
    print("SMTP_LIGHT_MODE=PEARL_IVORY_CHAMPAGNE_EMERALD")
    print("SMTP_DARK_MODE=OBSIDIAN_TITANIUM_CHAMPAGNE_EMERALD")
    print("SMTP_HEADER=EXECUTIVE_DELIVERY_CONTROL")
    print("SMTP_KPIS=LUXURY_STATUS_HARDWARE")
    print("SMTP_CONFIGURATION=SECURE_VAULT_PANEL")
    print("SMTP_FIELDS=PREMIUM_HIGH_CONTRAST")
    print("SMTP_ACTIONS=METALLIC_CHAMPAGNE_AND_EMERALD")
    print("SMTP_TEST_DELIVERY=PREMIUM_SIGNAL_PANEL")
    print("SMTP_API_CHANGED=NO")
    print("SMTP_SAVE_LOGIC_CHANGED=NO")
    print("SMTP_TEST_LOGIC_CHANGED=NO")
    print("SMTP_PERMISSIONS_CHANGED=NO")
    print("SMTP_DATA_CONTRACT_CHANGED=NO")
    print("TWS_CHANGED=NO")
    print("SLA_CHANGED=NO")
    print("RAMZY_LOGIC_CHANGED=NO")
    print("TCS_CHANGED=NO")
    print(f"SETTINGS_PAGE_BASELINE_GIT_BLOB={EXPECTED_PAGE_GIT_BLOB}")
    print(f"LIVE_BACKUP={live_backup if live_backup and live_backup.exists() else 'NONE'}")
    print("STATUS=READY")
except Exception as exc:
    try:
        if page_backup.exists():
            shutil.copy2(page_backup, PAGE)
        if STYLE.exists():
            STYLE.unlink()
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
