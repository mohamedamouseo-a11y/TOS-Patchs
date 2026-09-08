from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
PAGE = FRONTEND / "src/pages/SettingsPage.jsx"
STYLE = FRONTEND / "src/pages/settingsOverviewFlagshipV1.css"
DIST = FRONTEND / "dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

V1_IMPORT = 'import "./settingsOverviewFlagshipV1.css";'
V1_RUNTIME = "--tos-settings-overview-flagship-v1-runtime"
V11_RUNTIME = "--tos-settings-overview-flagship-v1-1-runtime"

CSS_FIX = r'''

/* TOS Settings Overview Flagship V1.1 — dark KPI value contrast only */
:root { --tos-settings-overview-flagship-v1-1-runtime: 1; }

.dark .tos-settings-flagship-v1 .tos-settings-overview-v1 .tos-settings-overview-stats > .tos-premium-stat > .flex > div:first-child > div:first-child {
  color: #f6efe2 !important;
  text-shadow: 0 1px 0 rgba(255,255,255,.035), 0 7px 22px rgba(224,181,80,.08);
}
'''


def fail(message):
    raise RuntimeError(message)


def run(command, cwd=None):
    subprocess.run(command, cwd=cwd, check=True)


if not PAGE.exists():
    fail(f"Settings page missing: {PAGE}")
if not STYLE.exists():
    fail(f"Settings Flagship V1 style missing: {STYLE}")

page_text = PAGE.read_text()
style_text = STYLE.read_text()

required_page_markers = [
    V1_IMPORT,
    "tos-settings-flagship-v1",
    "tos-settings-overview-v1",
    "tos-settings-overview-stats",
]
for marker in required_page_markers:
    if marker not in page_text:
        fail(f"required Settings Overview V1 page marker missing: {marker}")

required_style_markers = [
    V1_RUNTIME,
    ".dark .tos-settings-overview-v1 .tos-settings-overview-stats > *",
]
for marker in required_style_markers:
    if marker not in style_text:
        fail(f"required Settings Overview V1 style marker missing: {marker}")

if V11_RUNTIME in style_text:
    fail("Settings Overview V1.1 dark KPI contrast fix already present")

stamp = int(time.time())
style_backup = STYLE.with_name(f"{STYLE.name}.v1-1-backup-{stamp}")
shutil.copy2(STYLE, style_backup)
live_backup = None
staging = None

try:
    STYLE.write_text(style_text.rstrip() + CSS_FIX + "\n")

    updated = STYLE.read_text()
    if V11_RUNTIME not in updated:
        fail("V1.1 runtime marker missing after CSS write")
    if "#f6efe2 !important" not in updated:
        fail("V1.1 KPI contrast rule missing after CSS write")

    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists():
        fail("frontend dist missing after build")

    built_css = ""
    for css_file in DIST.rglob("*.css"):
        built_css += css_file.read_text(errors="ignore")
    if V11_RUNTIME not in built_css:
        fail("Settings Overview V1.1 runtime marker missing from built CSS")
    if "#f6efe2" not in built_css.lower():
        fail("Settings Overview V1.1 KPI contrast color missing from built CSS")

    LIVE_PARENT.mkdir(parents=True, exist_ok=True)
    staging = LIVE_PARENT / f"build.settings-overview-v1-1-staging-{stamp}"
    live_backup = LIVE_PARENT / f"build.settings-overview-v1-1-backup-{stamp}"
    if staging.exists():
        shutil.rmtree(staging)
    shutil.copytree(DIST, staging)

    if LIVE.exists():
        LIVE.rename(live_backup)
    staging.rename(LIVE)

    live_css = ""
    for css_file in LIVE.rglob("*.css"):
        live_css += css_file.read_text(errors="ignore")
    if V11_RUNTIME not in live_css:
        fail("Settings Overview V1.1 runtime marker missing from live build")
    if "#f6efe2" not in live_css.lower():
        fail("Settings Overview V1.1 KPI contrast color missing from live build")

    print("PASS/FAIL=PASS")
    print("BUILD_RESULT=PASS")
    print("LIVE_DEPLOY=PASS")
    print("SETTINGS_OVERVIEW_FLAGSHIP_V1_1_RUNTIME=YES")
    print("SETTINGS_V1_BASELINE=PRESERVED")
    print("SETTINGS_V11_SCOPE=DARK_KPI_VALUE_CONTRAST_ONLY")
    print("SETTINGS_DARK_KPI_VALUES=IVORY_CHAMPAGNE_HIGH_CONTRAST")
    print("SETTINGS_LIGHT_MODE_CHANGED=NO")
    print("SETTINGS_HEADER_CHANGED=NO")
    print("SETTINGS_SECTION_CARDS_CHANGED=NO")
    print("SETTINGS_NAVIGATION_LOGIC_CHANGED=NO")
    print("SETTINGS_PERMISSIONS_CHANGED=NO")
    print("SETTINGS_API_CHANGED=NO")
    print("SETTINGS_SAVE_LOGIC_CHANGED=NO")
    print("SETTINGS_INTEGRATIONS_CHANGED=NO")
    print("SETTINGS_IDENTITY_LOGIC_CHANGED=NO")
    print("SETTINGS_OPERATIONS_LOGIC_CHANGED=NO")
    print("TWS_CHANGED=NO")
    print("SLA_CHANGED=NO")
    print("RAMZY_LOGIC_CHANGED=NO")
    print("TCS_CHANGED=NO")
    print(f"LIVE_BACKUP={live_backup if live_backup and live_backup.exists() else 'NONE'}")
    print("STATUS=READY")
except Exception as exc:
    try:
        if style_backup.exists():
            shutil.copy2(style_backup, STYLE)
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
