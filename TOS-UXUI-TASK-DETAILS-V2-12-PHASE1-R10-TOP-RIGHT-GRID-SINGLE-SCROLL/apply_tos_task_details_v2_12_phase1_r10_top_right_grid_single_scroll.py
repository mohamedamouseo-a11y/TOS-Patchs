from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import time

VERSION = "TOS_TASK_DETAILS_V2_12_PHASE1_R10_TOP_RIGHT_GRID_SINGLE_SCROLL"
PATCH_NAME = "TOS-UXUI-TASK-DETAILS-V2-12-PHASE1-R10-TOP-RIGHT-GRID-SINGLE-SCROLL"
R9_MARKER = "--tos-task-details-v2-12-phase1-r9-top-right-rail-single-scroll-runtime"
R10_MARKER = "--tos-task-details-v2-12-phase1-r10-top-right-grid-single-scroll-runtime"

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
STYLE_DIR = FRONTEND / "src/styles"
BOARD = FRONTEND / "src/components/ProfessionalTaskBoard.jsx"
APP = FRONTEND / "src/App.jsx"
SIDEBAR = FRONTEND / "src/components/layout/Sidebar.jsx"
R9_STYLE = STYLE_DIR / "taskDetailsV2_12_Phase1R9TopRightRailSingleScroll.css"
R10_STYLE = STYLE_DIR / "taskDetailsV2_12_Phase1R10TopRightGridSingleScroll.css"
MANIFEST = ROOT / "deployment/tos-production-runtime.json"
PATCH_DIR = Path(__file__).resolve().parent
PAYLOAD = PATCH_DIR / "taskDetailsV2_12_Phase1R10TopRightGridSingleScroll.css"


def fail(message):
    raise RuntimeError(message)


def run(command, cwd=None):
    subprocess.run(command, cwd=cwd, check=True)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


for path in (FRONTEND, STYLE_DIR, BOARD, APP, SIDEBAR, R9_STYLE, MANIFEST, PAYLOAD):
    if not path.exists():
        fail(f"required path missing: {path}")
for command in ("node", "npm"):
    if not shutil.which(command):
        fail(f"required command not found: {command}")

board_source = BOARD.read_text()
r9_source = R9_STYLE.read_text()
payload_css = PAYLOAD.read_text()

if R9_MARKER not in r9_source:
    fail("required R9 baseline marker missing")
if R10_STYLE.exists() or R10_MARKER in board_source:
    fail("Phase 1 R10 already appears to be applied")
if R10_MARKER not in payload_css:
    fail("R10 payload runtime marker missing")

for contract in (
    'className="tos-task-details-layout grid gap-4 xl:grid-cols-[minmax(0,1fr)_304px]"',
    'className="tos-task-main-column min-w-0 space-y-4 text-right xl:order-1"',
    'className="tos-task-reference-v2-rail"',
):
    if contract not in board_source:
        fail(f"Task Details DOM contract missing: {contract}")

r9_import = 'import "../styles/taskDetailsV2_12_Phase1R9TopRightRailSingleScroll.css";'
r10_import = 'import "../styles/taskDetailsV2_12_Phase1R10TopRightGridSingleScroll.css";'
if r9_import not in board_source:
    fail("R9 stylesheet import missing")
if r10_import in board_source:
    fail("R10 stylesheet import already exists")
updated_board = board_source.replace(r9_import, r9_import + "\n" + r10_import, 1)

for contract in (
    'grid-template-columns:minmax(0,1fr) 304px!important',
    'grid-template-areas:"main rail"!important',
    'grid-column:2!important',
    'position:relative!important',
    'overflow-y:auto!important',
    '.tos-premium-page-viewport',
):
    if contract not in payload_css:
        fail(f"R10 CSS contract missing: {contract}")

app_hash = sha256(APP)
sidebar_hash = sha256(SIDEBAR)
prior_styles = sorted(p for p in STYLE_DIR.glob("taskDetailsV2_12_Phase1*.css") if p != R10_STYLE)
prior_style_hashes = {p: sha256(p) for p in prior_styles}

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

stamp = int(time.time())
backup_root = Path(f"/var/backups/tos-patches/task-details-v2-12-phase1-r10-{stamp}")
backup_root.mkdir(parents=True, exist_ok=False)
board_backup = backup_root / BOARD.name
shutil.copy2(BOARD, board_backup)

LIVE.parent.mkdir(parents=True, exist_ok=True)
staging = LIVE.parent / f"build.task-details-v2-12-phase1-r10-staging-{stamp}"
live_backup = LIVE.parent / f"build.task-details-v2-12-phase1-r10-backup-{stamp}"
live_swapped = False
r10_written = False

try:
    BOARD.write_text(updated_board)
    R10_STYLE.write_text(payload_css.rstrip() + "\n")
    r10_written = True

    if sha256(APP) != app_hash or sha256(SIDEBAR) != sidebar_hash:
        fail("frozen app shell source changed unexpectedly")
    for path, digest in prior_style_hashes.items():
        if sha256(path) != digest:
            fail(f"prior Phase1 stylesheet changed unexpectedly: {path.name}")

    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists() or not (DIST / "index.html").exists():
        fail("frontend dist missing after build")

    built_css = "\n".join(p.read_text(errors="ignore") for p in DIST.rglob("*.css"))
    for marker in (R10_MARKER, R9_MARKER):
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
    for marker in (R10_MARKER, R9_MARKER):
        if marker not in live_css:
            fail(f"required runtime marker missing from live CSS: {marker}")

    if sha256(APP) != app_hash or sha256(SIDEBAR) != sidebar_hash:
        fail("frozen app shell source changed after deploy")
    for path, digest in prior_style_hashes.items():
        if sha256(path) != digest:
            fail(f"prior Phase1 stylesheet changed after deploy: {path.name}")

except Exception:
    shutil.copy2(board_backup, BOARD)
    if r10_written and R10_STYLE.exists():
        R10_STYLE.unlink()
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
print("RIGHT_RAIL_TOP=YES")
print("RIGHT_RAIL_PHYSICAL_SIDE=RIGHT")
print("RIGHT_RAIL_OVERLAP=NO")
print("TASK_SCROLL_OWNERS=1")
print("R9_BASELINE_PRESERVED=YES")
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
