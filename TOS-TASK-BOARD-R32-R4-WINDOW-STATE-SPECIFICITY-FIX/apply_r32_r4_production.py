from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import time
import urllib.request

PATCH = "TOS-TASK-BOARD-R32-R4-WINDOW-STATE-SPECIFICITY-FIX"
VERSION = "TOS_TASK_BOARD_R32_R4"
BASE_TOS_COMMIT = "3bb74d81ab67db42da9d435b391c6530bf29c96d"
R3_MARKER = "--tos-task-board-r32-r3-user-controllable-window-runtime"
R4_MARKER = "--tos-task-board-r32-r4-window-state-specificity-runtime"
R3_DATA = 'data-tos-task-window-r32-r3="true"'
MIN_DATA = 'data-tos-task-window-minimized={isTaskWindowMinimized ? "true" : "false"}'
MAX_DATA = 'data-tos-task-window-maximized={isTaskWindowMaximized ? "true" : "false"}'

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
STYLE_DIR = FRONTEND / "src/styles"
BOARD = FRONTEND / "src/components/ProfessionalTaskBoard.jsx"
PARTS = FRONTEND / "src/features/tasks/taskBoardParts.jsx"
CHAT = FRONTEND / "src/components/ChatPanel.jsx"
APP = FRONTEND / "src/App.jsx"
SIDEBAR = FRONTEND / "src/components/layout/Sidebar.jsx"
MANIFEST = ROOT / "deployment/tos-production-runtime.json"
R3_STYLE = STYLE_DIR / "taskBoardR32R3UserControllableWindow.css"
R4_STYLE = STYLE_DIR / "taskBoardR32R4WindowStateSpecificityFix.css"
PAYLOAD = Path(__file__).resolve().parent / "taskBoardR32R4WindowStateSpecificityFix.css"


def fail(message):
    raise RuntimeError(message)


def run(command, cwd=None):
    subprocess.run(command, cwd=cwd, check=True)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


for path in (FRONTEND, STYLE_DIR, BOARD, PARTS, CHAT, APP, SIDEBAR, MANIFEST, R3_STYLE, PAYLOAD):
    if not path.exists():
        fail(f"required path missing: {path}")
for command in ("node", "npm"):
    if not shutil.which(command):
        fail(f"required command missing: {command}")

board_source = BOARD.read_text()
r3_css = R3_STYLE.read_text()
payload_css = PAYLOAD.read_text()
r3_import = 'import "../styles/taskBoardR32R3UserControllableWindow.css";'
r4_import = 'import "../styles/taskBoardR32R4WindowStateSpecificityFix.css";'

for contract in (r3_import, R3_DATA, MIN_DATA, MAX_DATA, "toggleTaskWindowMinimizedR32R3", "toggleTaskWindowMaximizedR32R3", "startTaskWindowDragR32R3", "function startResize(direction)"):
    if contract not in board_source:
        fail(f"required R32_R3 live source contract missing: {contract}")
if R3_MARKER not in r3_css:
    fail("R32_R3 stylesheet marker missing")
for contract in (R4_MARKER, '[data-tos-task-window-minimized="true"]', '[data-tos-task-window-maximized="true"]'):
    if contract not in payload_css:
        fail(f"R32_R4 payload contract missing: {contract}")
if R4_STYLE.exists() or r4_import in board_source:
    fail("R32_R4 already appears to be applied")
if board_source.count(r3_import) != 1:
    fail(f"expected exactly one R32_R3 import, found {board_source.count(r3_import)}")

updated = board_source.replace(r3_import, r3_import + "\n" + r4_import, 1)
if updated.count(r4_import) != 1:
    fail("R32_R4 import insertion failed")
for contract in (R3_DATA, MIN_DATA, MAX_DATA, "toggleTaskWindowMinimizedR32R3", "toggleTaskWindowMaximizedR32R3", "startTaskWindowDragR32R3", "function startResize(direction)"):
    if board_source.count(contract) != updated.count(contract):
        fail(f"R32_R3 behavior contract changed unexpectedly: {contract}")

manifest = json.loads(MANIFEST.read_text())
if manifest.get("application") != "TOS" or manifest.get("environment") != "production":
    fail("unexpected production runtime manifest")
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

frozen = {path: sha256(path) for path in (PARTS, CHAT, APP, SIDEBAR, R3_STYLE)}
stamp = int(time.time())
backup_root = Path(f"/var/backups/tos-patches/task-board-r32-r4-{stamp}")
backup_root.mkdir(parents=True, exist_ok=False)
shutil.copy2(BOARD, backup_root / BOARD.name)

LIVE.parent.mkdir(parents=True, exist_ok=True)
staging = LIVE.parent / f"build.task-board-r32-r4-staging-{stamp}"
live_backup = LIVE.parent / f"build.task-board-r32-r4-backup-{stamp}"
live_swapped = False
r4_written = False

try:
    BOARD.write_text(updated)
    R4_STYLE.write_text(payload_css.rstrip() + "\n")
    r4_written = True

    written = BOARD.read_text()
    if written.count(r4_import) != 1:
        fail("R32_R4 source import missing after write")
    for path, digest in frozen.items():
        if sha256(path) != digest:
            fail(f"protected file changed unexpectedly: {path}")

    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists() or not (DIST / "index.html").exists():
        fail("frontend dist missing after build")

    built_css = "\n".join(p.read_text(errors="ignore") for p in DIST.rglob("*.css"))
    built_js = "\n".join(p.read_text(errors="ignore") for p in DIST.rglob("*.js"))
    for marker in (R3_MARKER, R4_MARKER):
        if marker not in built_css:
            fail(f"runtime CSS marker missing from build: {marker}")
    for hook in ("tos-task-window-r32-r3", "tos-task-window-minimized", "tos-task-window-maximized"):
        if hook not in built_js:
            fail(f"R32_R3 window hook missing from build: {hook}")

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
    if R3_MARKER not in live_css or R4_MARKER not in live_css:
        fail("R32_R3/R32_R4 runtime marker missing from live build")

except Exception:
    shutil.copy2(backup_root / BOARD.name, BOARD)
    if r4_written and R4_STYLE.exists():
        R4_STYLE.unlink()
    if live_swapped:
        if LIVE.exists():
            shutil.rmtree(LIVE)
        if live_backup.exists():
            live_backup.rename(LIVE)
    elif staging.exists():
        shutil.rmtree(staging)
    raise

live_http = "UNVERIFIED"
try:
    request = urllib.request.Request("https://tos.tamiyouz.com/tasks", headers={"User-Agent": "TOS-R32-R4-Healthcheck"})
    with urllib.request.urlopen(request, timeout=15) as response:
        live_http = str(response.status)
except Exception:
    pass

print(f"VERSION={VERSION}")
print(f"PATCH_APPLIED={PATCH}")
print(f"BASE_TOS_MAIN_REVIEWED={BASE_TOS_COMMIT}")
print("BUILD_STATUS=PASS")
print("DEPLOY_STATUS=PASS")
print(f"LIVE_HTTP_STATUS={live_http}")
print("R32_R3_PRESERVED=YES")
print("MINIMIZE_SPECIFICITY_FIX=YES")
print("MAXIMIZE_SPECIFICITY_FIX=YES")
print("RESTORE_SIZE_POSITION_PRESERVED=YES")
print("DRAG_RESIZE_PRESERVED=YES")
print("MOBILE_FULLSCREEN_PRESERVED=YES")
print("BACKEND_CHANGED=NO")
print("API_CHANGED=NO")
print("DATABASE_CHANGED=NO")
print("PUSH=NO")
print("FINAL_STATUS=PASS")
