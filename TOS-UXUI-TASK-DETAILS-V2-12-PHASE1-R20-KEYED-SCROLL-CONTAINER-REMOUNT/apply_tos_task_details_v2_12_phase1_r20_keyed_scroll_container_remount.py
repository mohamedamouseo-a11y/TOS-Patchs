from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import time

VERSION = "TOS_TASK_DETAILS_V2_12_PHASE1_R20_KEYED_SCROLL_CONTAINER_REMOUNT"
PATCH_NAME = "TOS-UXUI-TASK-DETAILS-V2-12-PHASE1-R20-KEYED-SCROLL-CONTAINER-REMOUNT"
R19_MARKER = "--tos-task-details-v2-12-phase1-r19-reset-actual-scroll-owners-runtime"
R20_MARKER = "--tos-task-details-v2-12-phase1-r20-keyed-scroll-container-remount-runtime"

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
STYLE_DIR = FRONTEND / "src/styles"
BOARD = FRONTEND / "src/components/ProfessionalTaskBoard.jsx"
APP = FRONTEND / "src/App.jsx"
SIDEBAR = FRONTEND / "src/components/layout/Sidebar.jsx"
R19_STYLE = STYLE_DIR / "taskDetailsV2_12_Phase1R19ResetActualScrollOwners.css"
R20_STYLE = STYLE_DIR / "taskDetailsV2_12_Phase1R20KeyedScrollContainerRemount.css"
MANIFEST = ROOT / "deployment/tos-production-runtime.json"
PATCH_DIR = Path(__file__).resolve().parent
PAYLOAD = PATCH_DIR / "taskDetailsV2_12_Phase1R20KeyedScrollContainerRemount.css"

def fail(message):
    raise RuntimeError(message)

def run(command, cwd=None):
    subprocess.run(command, cwd=cwd, check=True)

def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

for path in (FRONTEND, STYLE_DIR, BOARD, APP, SIDEBAR, R19_STYLE, MANIFEST, PAYLOAD):
    if not path.exists():
        fail(f"required path missing: {path}")
for command in ("node", "npm"):
    if not shutil.which(command):
        fail(f"required command not found: {command}")

board_source = BOARD.read_text()
r19_source = R19_STYLE.read_text()
payload_css = PAYLOAD.read_text()

if R19_MARKER not in r19_source:
    fail("required R19 baseline marker missing")
if R20_STYLE.exists() or 'key={String(task?.id || "task-details")}' in board_source:
    fail("Phase 1 R20 already appears to be applied")
if R20_MARKER not in payload_css:
    fail("R20 payload runtime marker missing")
if 'scroller.dataset.tosTaskDetailsScrollReset = "r19";' not in board_source:
    fail("required R19 JS reset contract missing")

old_body = '<div ref={taskDetailsBodyRef} onScroll={handleTaskDetailsScroll} className="min-h-0 flex-1 overflow-y-auto p-3 dark:from-zinc-950 dark:via-zinc-950 dark:to-blue-950/20 sm:p-4">'
new_body = '<div key={String(task?.id || "task-details")} ref={taskDetailsBodyRef} onScroll={handleTaskDetailsScroll} className="min-h-0 flex-1 overflow-y-auto p-3 dark:from-zinc-950 dark:via-zinc-950 dark:to-blue-950/20 sm:p-4">'

if board_source.count(old_body) != 1:
    fail(f"expected exactly one Task Details scroll container, found {board_source.count(old_body)}")
updated_board = board_source.replace(old_body, new_body, 1)

r19_import = 'import "../styles/taskDetailsV2_12_Phase1R19ResetActualScrollOwners.css";'
r20_import = 'import "../styles/taskDetailsV2_12_Phase1R20KeyedScrollContainerRemount.css";'
if r19_import not in updated_board:
    fail("R19 stylesheet import missing")
if r20_import in updated_board:
    fail("R20 stylesheet import already exists")
updated_board = updated_board.replace(r19_import, r19_import + "\n" + r20_import, 1)

for contract in (
    'key={String(task?.id || "task-details")}',
    'ref={taskDetailsBodyRef}',
    'scroller.dataset.tosTaskDetailsScrollReset = "r19";',
    r20_import,
):
    if contract not in updated_board:
        fail(f"R20 source contract missing after edit: {contract}")

app_hash = sha256(APP)
sidebar_hash = sha256(SIDEBAR)
prior_styles = sorted(p for p in STYLE_DIR.glob("taskDetailsV2_12_Phase1*.css") if p != R20_STYLE)
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
backup_root = Path(f"/var/backups/tos-patches/task-details-v2-12-phase1-r20-{stamp}")
backup_root.mkdir(parents=True, exist_ok=False)
board_backup = backup_root / BOARD.name
shutil.copy2(BOARD, board_backup)

LIVE.parent.mkdir(parents=True, exist_ok=True)
staging = LIVE.parent / f"build.task-details-v2-12-phase1-r20-staging-{stamp}"
live_backup = LIVE.parent / f"build.task-details-v2-12-phase1-r20-backup-{stamp}"
live_swapped = False
r20_written = False

try:
    BOARD.write_text(updated_board)
    R20_STYLE.write_text(payload_css.rstrip() + "\n")
    r20_written = True

    if sha256(APP) != app_hash or sha256(SIDEBAR) != sidebar_hash:
        fail("frozen app shell source changed unexpectedly")
    for path, digest in prior_style_hashes.items():
        if sha256(path) != digest:
            fail(f"prior Phase1 stylesheet changed unexpectedly: {path.name}")

    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists() or not (DIST / "index.html").exists():
        fail("frontend dist missing after build")

    built_css = "\n".join(p.read_text(errors="ignore") for p in DIST.rglob("*.css"))
    built_js = "\n".join(p.read_text(errors="ignore") for p in DIST.rglob("*.js"))
    for marker in (R20_MARKER, R19_MARKER):
        if marker not in built_css:
            fail(f"required runtime marker missing from built CSS: {marker}")
    if "task-details" not in built_js or "tosTaskDetailsScrollReset" not in built_js:
        fail("R20 keyed remount or R19 reset missing from built JS")

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
    live_js = "\n".join(p.read_text(errors="ignore") for p in LIVE.rglob("*.js"))
    for marker in (R20_MARKER, R19_MARKER):
        if marker not in live_css:
            fail(f"required runtime marker missing from live CSS: {marker}")
    if "task-details" not in live_js or "tosTaskDetailsScrollReset" not in live_js:
        fail("R20 keyed remount or R19 reset missing from live JS")

    if sha256(APP) != app_hash or sha256(SIDEBAR) != sidebar_hash:
        fail("frozen app shell source changed after deploy")
    for path, digest in prior_style_hashes.items():
        if sha256(path) != digest:
            fail(f"prior Phase1 stylesheet changed after deploy: {path.name}")

except Exception:
    shutil.copy2(board_backup, BOARD)
    if r20_written and R20_STYLE.exists():
        R20_STYLE.unlink()
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
print("TASK_DETAILS_SCROLL_CONTAINER_KEYED_BY_TASK_ID=YES")
print("SCROLL_CONTAINER_REMOUNTS_ON_TASK_CHANGE=YES")
print("R19_MULTI_OWNER_RESET_PRESERVED=YES")
print("LAYOUT_CHANGED=NO")
print("APP_JS_CHANGED=NO")
print("SIDEBAR_JS_CHANGED=NO")
print("BACKEND_CHANGED=NO")
print("DATABASE_CHANGED=NO")
print("TCS_CHANGED=NO")
print("RAMZY_CHANGED=NO")
print("NO_BROWSER_QA=YES")
print("NO_SCREENSHOTS=YES")
print("PUSH=NO")
print(f"BACKUP={backup_root}")
print("STATUS=DEPLOYED__MANUAL_VISUAL_QA_REQUIRED")
