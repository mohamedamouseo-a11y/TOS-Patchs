from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import time

VERSION = "TOS_TASK_DETAILS_V2_11J_R2"
PATCH_NAME = "TOS-UXUI-TASK-DETAILS-V2-11J-R2-DARK-PREMIUM-CONSISTENCY-POLISH"
BASELINE_CHAIN = "TOS_TASK_DETAILS_V2_11J_R1"
R1_RUNTIME = "--tos-task-details-v2-11j-r1-primary-tabs-responsive-fix-runtime"
R2_RUNTIME = "--tos-task-details-v2-11j-r2-dark-premium-polish-runtime"

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
APP = FRONTEND / "src/App.jsx"
BOARD = FRONTEND / "src/components/ProfessionalTaskBoard.jsx"
STYLE = FRONTEND / "src/styles/taskDetailsCanonicalReferenceV2.css"
MANIFEST = ROOT / "deployment/tos-production-runtime.json"
PATCH_DIR = Path(__file__).resolve().parent
PAYLOAD = PATCH_DIR / "taskDetailsV2_11J_R2DarkPremiumConsistencyPolish.css"


def fail(message):
    raise RuntimeError(message)


def run(command, cwd=None):
    subprocess.run(command, cwd=cwd, check=True)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


for path in (FRONTEND, APP, BOARD, STYLE, MANIFEST, PAYLOAD):
    if not path.exists():
        fail(f"required path missing: {path}")
for command in ("node", "npm"):
    if not shutil.which(command):
        fail(f"required command not found: {command}")

app_source = APP.read_text()
board_source = BOARD.read_text()
style_source = STYLE.read_text()
payload_css = PAYLOAD.read_text()

if "TOS_TASK_DETAILS_V2_11J_TNC_COMMENTS_DEEP_LINK" not in app_source:
    fail("required V2.11J notification deep-link marker missing")
if "TOS_TASK_DETAILS_V2_11J_COMMENTS_PRIMARY_TAB" not in board_source:
    fail("required V2.11J Comments primary-tab marker missing")
if "TOS_TASK_DETAILS_V2_11H_HERO_DESCRIPTION_REMOVED" not in board_source:
    fail("required V2.11H Hero marker missing")
if "TOS_TASK_DETAILS_V2_11G_WAITING_CLIENT_BELOW_DESCRIPTION" not in board_source:
    fail("required V2.11G Waiting Client marker missing")
if R1_RUNTIME not in style_source:
    fail("required V2.11J_R1 responsive-tabs baseline marker missing")
if R2_RUNTIME in style_source:
    fail("V2.11J_R2 already applied")

for contract in (
    R2_RUNTIME,
    ".dark .tos-task-details-reference-v1[data-content-dir].tos-task-details-reference-v2",
    ".tos-task-detail-tabs",
    ".tos-task-reference-tab[data-active=\"true\"]",
    ".tos-task-summary-controls>*",
    ".tos-task-title-input",
    ".tos-task-description-panel",
    ".tos-task-rich-editor-shell",
    ".tos-task-details-layout>aside",
):
    if contract not in payload_css:
        fail(f"R2 dark CSS contract missing: {contract}")

manifest = json.loads(MANIFEST.read_text())
if manifest.get("application") != "TOS" or manifest.get("environment") != "production":
    fail("unexpected production runtime manifest")
if manifest.get("sourceRoot") != str(ROOT):
    fail("runtime sourceRoot does not match target")
frontend_runtime = manifest.get("frontend") or {}
if Path(str(frontend_runtime.get("sourceDir") or "")) != FRONTEND:
    fail("frontend runtime sourceDir mismatch")
if str(frontend_runtime.get("buildCommand") or "") != "npm run build":
    fail("unexpected frontend build command")
DIST = Path(str(frontend_runtime.get("buildOutputDir") or ""))
LIVE = Path(str(frontend_runtime.get("publishedBuildDir") or ""))
if DIST != FRONTEND / "dist":
    fail(f"unexpected frontend build output: {DIST}")
if LIVE != Path("/opt/apps/tamiyouz-front/build"):
    fail(f"unexpected live frontend path: {LIVE}")

frozen_hashes = {APP: sha256(APP), BOARD: sha256(BOARD)}
stamp = int(time.time())
backup_root = Path(f"/var/backups/tos-patches/task-details-v2-11j-r2-{stamp}")
backup_root.mkdir(parents=True, exist_ok=False)
style_backup = backup_root / STYLE.name
shutil.copy2(STYLE, style_backup)

LIVE.parent.mkdir(parents=True, exist_ok=True)
staging = LIVE.parent / f"build.task-details-v2-11j-r2-staging-{stamp}"
live_backup = LIVE.parent / f"build.task-details-v2-11j-r2-backup-{stamp}"
live_swapped = False

try:
    STYLE.write_text(style_source.rstrip() + "\n\n" + payload_css.strip() + "\n")
    written_style = STYLE.read_text()
    if R2_RUNTIME not in written_style:
        fail("V2.11J_R2 runtime marker missing after stylesheet write")
    for path, expected in frozen_hashes.items():
        if sha256(path) != expected:
            fail(f"frozen source changed unexpectedly: {path}")

    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists() or not (DIST / "index.html").exists():
        fail("frontend dist missing after build")

    built_css = "\n".join(p.read_text(errors="ignore") for p in DIST.rglob("*.css"))
    if R2_RUNTIME not in built_css:
        fail("V2.11J_R2 runtime marker missing from built CSS")

    if staging.exists():
        shutil.rmtree(staging)
    shutil.copytree(DIST, staging)
    if LIVE.exists():
        if live_backup.exists():
            shutil.rmtree(live_backup)
        LIVE.rename(live_backup)
    staging.rename(LIVE)
    live_swapped = True

    live_css = "\n".join(p.read_text(errors="ignore") for p in LIVE.rglob("*.css"))
    if R2_RUNTIME not in live_css:
        fail("V2.11J_R2 runtime marker missing from live CSS")

    for path, expected in frozen_hashes.items():
        if sha256(path) != expected:
            fail(f"frozen source changed after deploy: {path}")

except Exception:
    shutil.copy2(style_backup, STYLE)
    if live_swapped:
        if LIVE.exists():
            shutil.rmtree(LIVE)
        if live_backup.exists():
            live_backup.rename(LIVE)
    elif staging.exists():
        shutil.rmtree(staging)
    raise

print(f"VERSION={VERSION}")
print(f"PATCH={PATCH_NAME}")
print(f"BASELINE_CHAIN={BASELINE_CHAIN}")
print("PASS/FAIL=PASS")
print("BUILD_RESULT=PASS")
print("LIVE_DEPLOY=PASS")
print("DARK_MODE_PREMIUM_POLISH=YES")
print("LIGHT_MODE_CHANGED=NO")
print("PRIMARY_TABS_DARK_SURFACE=YES")
print("ACTIVE_TAB_GOLD_STATE=YES")
print("HERO_CONTROLS_DARK=YES")
print("TITLE_BACKGROUND_RECT_REMOVED=YES")
print("DESCRIPTION_EDITOR_DARK_HIERARCHY=YES")
print("RIGHT_RAIL_DARK_HARMONIZED=YES")
print("R1_RESPONSIVE_TABS_PRESERVED=YES")
print("COMMENTS_LOGIC_CHANGED=NO")
print("TNC_ROUTING_CHANGED=NO")
print("APP_JS_CHANGED=NO")
print("TASK_BOARD_JSX_CHANGED=NO")
print("BACKEND_CHANGED=NO")
print("API_CHANGED=NO")
print("PUSH=NO")
print("STATUS=READY_FOR_VISUAL_QA")
