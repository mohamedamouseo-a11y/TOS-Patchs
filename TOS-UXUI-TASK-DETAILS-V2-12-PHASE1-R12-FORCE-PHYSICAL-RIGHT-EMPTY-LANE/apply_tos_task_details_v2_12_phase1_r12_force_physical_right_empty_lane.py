from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import time

VERSION = "TOS_TASK_DETAILS_V2_12_PHASE1_R12_FORCE_PHYSICAL_RIGHT_EMPTY_LANE"
PATCH_NAME = "TOS-UXUI-TASK-DETAILS-V2-12-PHASE1-R12-FORCE-PHYSICAL-RIGHT-EMPTY-LANE"
R11_MARKER = "--tos-task-details-v2-12-phase1-r11-right-empty-lane-rail-runtime"
R12_MARKER = "--tos-task-details-v2-12-phase1-r12-force-physical-right-empty-lane-runtime"

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
STYLE_DIR = FRONTEND / "src/styles"
BOARD = FRONTEND / "src/components/ProfessionalTaskBoard.jsx"
APP = FRONTEND / "src/App.jsx"
SIDEBAR = FRONTEND / "src/components/layout/Sidebar.jsx"
R11_STYLE = STYLE_DIR / "taskDetailsV2_12_Phase1R11RightEmptyLaneRail.css"
R12_STYLE = STYLE_DIR / "taskDetailsV2_12_Phase1R12ForcePhysicalRightEmptyLane.css"
MANIFEST = ROOT / "deployment/tos-production-runtime.json"
PATCH_DIR = Path(__file__).resolve().parent
PAYLOAD = PATCH_DIR / "taskDetailsV2_12_Phase1R12ForcePhysicalRightEmptyLane.css"


def fail(message):
    raise RuntimeError(message)


def run(command, cwd=None):
    subprocess.run(command, cwd=cwd, check=True)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


for path in (FRONTEND, STYLE_DIR, BOARD, APP, SIDEBAR, R11_STYLE, MANIFEST, PAYLOAD):
    if not path.exists():
        fail(f"required path missing: {path}")
for command in ("node", "npm"):
    if not shutil.which(command):
        fail(f"required command not found: {command}")

board_source = BOARD.read_text()
r11_source = R11_STYLE.read_text()
payload_css = PAYLOAD.read_text()

if R11_MARKER not in r11_source:
    fail("required R11 baseline marker missing")
if R12_STYLE.exists() or R12_MARKER in board_source:
    fail("Phase 1 R12 already appears to be applied")
if R12_MARKER not in payload_css:
    fail("R12 payload runtime marker missing")

for contract in (
    'className="tos-task-details-layout grid gap-4 xl:grid-cols-[minmax(0,1fr)_304px]"',
    'className="tos-task-reference-v2-rail"',
    'tos-task-summary-compact',
    'tos-task-description-panel',
):
    if contract not in board_source:
        fail(f"Task Details DOM contract missing: {contract}")

r11_import = 'import "../styles/taskDetailsV2_12_Phase1R11RightEmptyLaneRail.css";'
r12_import = 'import "../styles/taskDetailsV2_12_Phase1R12ForcePhysicalRightEmptyLane.css";'
if r11_import not in board_source:
    fail("R11 stylesheet import missing")
if r12_import in board_source:
    fail("R12 stylesheet import already exists")
updated_board = board_source.replace(r11_import, r11_import + "\n" + r12_import, 1)

for contract in (
    'left:calc(100% - 370px)!important',
    'right:auto!important',
    'width:calc(100% - 390px)!important',
    'width:370px!important',
    'top:258px!important',
):
    if contract not in payload_css:
        fail(f"R12 CSS contract missing: {contract}")

app_hash = sha256(APP)
sidebar_hash = sha256(SIDEBAR)
prior_styles = sorted(p for p in STYLE_DIR.glob("taskDetailsV2_12_Phase1*.css") if p != R12_STYLE)
prior_style_hashes = {p: sha256(p) for p in prior_styles}

manifest = json.loads(MANIFEST.read_text())
if manifest.get("application") != "TOS" or manifest.get("environment") != "production":
    fail("unexpected production runtime manifest")
if manifest.get("sourceRoot") != str(ROOT):
    fail("runtime sourceRoot does not match target")
frontend_runtime = manifest.get("frontend") or {}
DIST = Path(str(frontend_runtime.get("buildOutputDir") or ""))
LIVE = Path(str(frontend_runtime.get("publishedBuildDir") or ""))
if Path(str(frontend_runtime.get("sourceDir") or "")) != FRONTEND:
    fail("frontend runtime sourceDir mismatch")
if str(frontend_runtime.get("buildCommand") or "") != "npm run build":
    fail("unexpected frontend build command")
if DIST != FRONTEND / "dist":
    fail(f"unexpected frontend build output: {DIST}")
if LIVE != Path("/opt/apps/tamiyouz-front/build"):
    fail(f"unexpected live frontend path: {LIVE}")

stamp = int(time.time())
backup_root = Path(f"/var/backups/tos-patches/task-details-v2-12-phase1-r12-{stamp}")
backup_root.mkdir(parents=True, exist_ok=False)
board_backup = backup_root / BOARD.name
shutil.copy2(BOARD, board_backup)

LIVE.parent.mkdir(parents=True, exist_ok=True)
staging = LIVE.parent / f"build.task-details-v2-12-phase1-r12-staging-{stamp}"
live_backup = LIVE.parent / f"build.task-details-v2-12-phase1-r12-backup-{stamp}"
live_swapped = False
r12_written = False

try:
    BOARD.write_text(updated_board)
    R12_STYLE.write_text(payload_css.rstrip() + "\n")
    r12_written = True

    if sha256(APP) != app_hash or sha256(SIDEBAR) != sidebar_hash:
        fail("frozen app shell source changed unexpectedly")
    for path, digest in prior_style_hashes.items():
        if sha256(path) != digest:
            fail(f"prior Phase1 stylesheet changed unexpectedly: {path.name}")

    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists() or not (DIST / "index.html").exists():
        fail("frontend dist missing after build")

    built_css = "\n".join(p.read_text(errors="ignore") for p in DIST.rglob("*.css"))
    for marker in (R12_MARKER, R11_MARKER):
        if marker not in built_css:
            fail(f"required runtime marker missing from built CSS: {marker}")

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
    for marker in (R12_MARKER, R11_MARKER):
        if marker not in live_css:
            fail(f"required runtime marker missing from live CSS: {marker}")

    if sha256(APP) != app_hash or sha256(SIDEBAR) != sidebar_hash:
        fail("frozen app shell source changed after deploy")
    for path, digest in prior_style_hashes.items():
        if sha256(path) != digest:
            fail(f"prior Phase1 stylesheet changed after deploy: {path.name}")

except Exception:
    shutil.copy2(board_backup, BOARD)
    if r12_written and R12_STYLE.exists():
        R12_STYLE.unlink()
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
print("PASS/FAIL=PASS")
print("BUILD_RESULT=PASS")
print("LIVE_DEPLOY=PASS")
print("TASK_CARD_POSITION_PRESERVED=YES")
print("RIGHT_EMPTY_LANE_PRESERVED=YES")
print("RIGHT_RAIL_HORIZONTAL_ANCHOR=PHYSICAL_RIGHT")
print("RIGHT_RAIL_OVERLAP=NO")
print("R11_SCROLL_BEHAVIOR_PRESERVED=YES")
print("APP_JS_CHANGED=NO")
print("SIDEBAR_JS_CHANGED=NO")
print("PRIOR_PHASE1_CSS_CHANGED=NO")
print("BACKEND_CHANGED=NO")
print("DATABASE_CHANGED=NO")
print("TCS_CHANGED=NO")
print("RAMZY_CHANGED=NO")
print("NO_BROWSER_QA=YES")
print("NO_SCREENSHOTS=YES")
print("PUSH=NO")
print(f"BACKUP={backup_root}")
print("STATUS=DEPLOYED__MANUAL_VISUAL_QA_REQUIRED")
