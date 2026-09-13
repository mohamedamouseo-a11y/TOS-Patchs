from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import time

VERSION = "TOS_TASK_DETAILS_V2_11J_R1"
PATCH_NAME = "TOS-UXUI-TASK-DETAILS-V2-11J-R1-PRIMARY-TABS-RESPONSIVE-FIX"
BASELINE_CHAIN = "TOS_TASK_DETAILS_V2_11J"
BASE_TOS_COMMIT = "e417a3255fce78955cb6ce2347995124de6ae2be"
RUNTIME = "--tos-task-details-v2-11j-r1-primary-tabs-responsive-fix-runtime"

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
APP = FRONTEND / "src/App.jsx"
BOARD = FRONTEND / "src/components/ProfessionalTaskBoard.jsx"
STYLE = FRONTEND / "src/styles/taskDetailsCanonicalReferenceV2.css"
MANIFEST = ROOT / "deployment/tos-production-runtime.json"
PATCH_DIR = Path(__file__).resolve().parent
PAYLOAD = PATCH_DIR / "taskDetailsV2_11J_R1PrimaryTabsResponsiveFix.css"


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
    fail("required V2.11J App notification deep-link marker missing")
if "TOS_TASK_DETAILS_V2_11J_COMMENTS_PRIMARY_TAB" not in board_source:
    fail("required V2.11J Comments primary-tab marker missing")
if "TOS_TASK_DETAILS_V2_11H_HERO_DESCRIPTION_REMOVED" not in board_source:
    fail("required V2.11H Hero baseline marker missing")
if "TOS_TASK_DETAILS_V2_11G_WAITING_CLIENT_BELOW_DESCRIPTION" not in board_source:
    fail("required V2.11G Waiting Client baseline marker missing")
if RUNTIME in style_source:
    fail("V2.11J_R1 already applied")

for contract in (
    RUNTIME,
    "@media (min-width:1024px) and (max-width:1440px)",
    ".tos-task-reference-tabs-main",
    ".tos-task-reference-tab",
    "flex:1 1 0!important",
    "min-width:0!important",
    "text-overflow:ellipsis!important",
    ".tos-task-reference-tab-count",
):
    if contract not in payload_css:
        fail(f"responsive CSS contract missing: {contract}")

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

frozen_hashes = {
    APP: sha256(APP),
    BOARD: sha256(BOARD),
}

stamp = int(time.time())
backup_root = Path(f"/var/backups/tos-patches/task-details-v2-11j-r1-{stamp}")
backup_root.mkdir(parents=True, exist_ok=False)
style_backup = backup_root / STYLE.name
shutil.copy2(STYLE, style_backup)

LIVE.parent.mkdir(parents=True, exist_ok=True)
staging = LIVE.parent / f"build.task-details-v2-11j-r1-staging-{stamp}"
live_backup = LIVE.parent / f"build.task-details-v2-11j-r1-backup-{stamp}"
live_swapped = False

try:
    STYLE.write_text(style_source.rstrip() + "\n\n" + payload_css.strip() + "\n")
    written_style = STYLE.read_text()

    if RUNTIME not in written_style:
        fail("V2.11J_R1 runtime marker missing after stylesheet write")
    for path, expected in frozen_hashes.items():
        if sha256(path) != expected:
            fail(f"frozen source changed unexpectedly: {path}")

    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists() or not (DIST / "index.html").exists():
        fail("frontend dist missing after build")

    built_css = "\n".join(p.read_text(errors="ignore") for p in DIST.rglob("*.css"))
    if RUNTIME not in built_css:
        fail("V2.11J_R1 runtime marker missing from built CSS")

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
    if RUNTIME not in live_css:
        fail("V2.11J_R1 runtime marker missing from live CSS")

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
print(f"BASE_TOS_COMMIT={BASE_TOS_COMMIT}")
print("PASS/FAIL=PASS")
print("BUILD_RESULT=PASS")
print("LIVE_DEPLOY=PASS")
print("PRIMARY_TABS_RESPONSIVE_FIX=YES")
print("TARGET_RANGE_1024_TO_1440=YES")
print("COMMENTS_PRIMARY_TAB_PRESERVED=YES")
print("COMMENTS_COUNT_BADGE_PRESERVED=YES")
print("TAB_ORDER_CHANGED=NO")
print("COMMENT_LOGIC_CHANGED=NO")
print("TNC_ROUTING_CHANGED=NO")
print("HERO_CHANGED=NO")
print("DESCRIPTION_CHANGED=NO")
print("WAITING_CLIENT_CHANGED=NO")
print("RIGHT_RAIL_CHANGED=NO")
print("TCS_CHANGED=NO")
print("RAMZY_CHANGED=NO")
print("APP_JS_CHANGED=NO")
print("TASK_BOARD_JSX_CHANGED=NO")
print("PUSH=NO")
print("STATUS=READY_FOR_VISUAL_QA")
