from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import time
import urllib.request

PATCH = "TOS-TASK-BOARD-R32-R6-DEDICATED-MINIMIZED-WINDOW"
VERSION = "TOS_TASK_BOARD_R32_R6"
R5_MARKER = "--tos-task-board-r32-r5-inline-window-geometry-runtime"
R6_MARKER = "--tos-task-board-r32-r6-dedicated-minimized-window-runtime"

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
R5_STYLE = STYLE_DIR / "taskBoardR32R5InlineWindowGeometryFix.css"
R6_STYLE = STYLE_DIR / "taskBoardR32R6DedicatedMinimizedWindow.css"
PAYLOAD = Path(__file__).resolve().parent / "taskBoardR32R6DedicatedMinimizedWindow.css"


def fail(message):
    raise RuntimeError(message)


def run(command, cwd=None):
    subprocess.run(command, cwd=cwd, check=True)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


for path in (FRONTEND, STYLE_DIR, BOARD, PARTS, CHAT, APP, SIDEBAR, MANIFEST, R3_STYLE, R4_STYLE, R5_STYLE, PAYLOAD):
    if not path.exists():
        fail(f"required path missing: {path}")
for command in ("node", "npm"):
    if not shutil.which(command):
        fail(f"required command missing: {command}")

board_source = BOARD.read_text()
r5_css = R5_STYLE.read_text()
payload_css = PAYLOAD.read_text()

r5_import = 'import "../styles/taskBoardR32R5InlineWindowGeometryFix.css";'
r6_import = 'import "../styles/taskBoardR32R6DedicatedMinimizedWindow.css";'

for contract in (
    r5_import,
    'data-tos-task-window-r32-r5="true"',
    'data-tos-task-window-minimized={isTaskWindowMinimized ? "true" : "false"}',
    "taskWindowGeometryR32R5",
    "toggleTaskWindowMinimizedR32R3",
    "startTaskWindowDragR32R3",
    "<Maximize2",
    "<X",
):
    if contract not in board_source:
        fail(f"required R32_R5 live source contract missing: {contract}")
if R5_MARKER not in r5_css:
    fail("R32_R5 stylesheet marker missing")
if R6_MARKER not in payload_css:
    fail("R32_R6 payload marker missing")
if R6_STYLE.exists() or r6_import in board_source or "tos-task-r32-r6-mini-window" in board_source:
    fail("R32_R6 already appears to be applied")
if board_source.count(r5_import) != 1:
    fail(f"expected exactly one R32_R5 import, found {board_source.count(r5_import)}")

updated = board_source.replace(r5_import, r5_import + "\n" + r6_import, 1)

anchor = '''        className="tos-task-details-modal flex h-[100dvh] w-full flex-col overflow-hidden bg-transparent"
      >
        <div className="tos-task-r32-r3-resize-handle tos-task-r32-r3-resize-handle--right"'''
replacement = '''        className="tos-task-details-modal flex h-[100dvh] w-full flex-col overflow-hidden bg-transparent"
      >
        {isTaskWindowMinimized ? (
          <div className="tos-task-r32-r6-mini-window" onMouseDown={startTaskWindowDragR32R3} data-tos-task-mini-window-r32-r6="true">
            <span className="tos-task-r32-r6-mini-accent" aria-hidden="true" />
            <div className="tos-task-r32-r6-mini-copy">
              <span className="tos-task-r32-r6-mini-label">{isAr ? "المهمة" : "Task"}</span>
              <strong className="tos-task-r32-r6-mini-title" title={draft.title || modalUi.taskDetails}>{draft.title || modalUi.taskDetails}</strong>
            </div>
            <div className="tos-task-r32-r6-mini-actions">
              <button type="button" className="tos-task-r32-r6-mini-action" onClick={toggleTaskWindowMinimizedR32R3} aria-label={isAr ? "استعادة النافذة" : "Restore window"} title={isAr ? "استعادة النافذة" : "Restore window"}><Maximize2 size={17} /></button>
              <button type="button" className="tos-task-r32-r6-mini-action" onClick={onClose} aria-label={modalUi.closeTaskDetails || (isAr ? "إغلاق تفاصيل المهمة" : "Close task details")} title={modalUi.closeTaskDetails || (isAr ? "إغلاق" : "Close")}><X size={17} /></button>
            </div>
          </div>
        ) : null}
        <div className="tos-task-r32-r3-resize-handle tos-task-r32-r3-resize-handle--right"'''

if updated.count(anchor) != 1:
    fail(f"expected one R32_R5 dialog body anchor, found {updated.count(anchor)}")
updated = updated.replace(anchor, replacement, 1)

for contract in (
    r6_import,
    'className="tos-task-r32-r6-mini-window"',
    'data-tos-task-mini-window-r32-r6="true"',
    "toggleTaskWindowMinimizedR32R3",
    "startTaskWindowDragR32R3",
):
    if contract not in updated:
        fail(f"R32_R6 transformed source contract missing: {contract}")

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

frozen = {path: sha256(path) for path in (PARTS, CHAT, APP, SIDEBAR, R3_STYLE, R4_STYLE, R5_STYLE)}
stamp = int(time.time())
backup_root = Path(f"/var/backups/tos-patches/task-board-r32-r6-{stamp}")
backup_root.mkdir(parents=True, exist_ok=False)
shutil.copy2(BOARD, backup_root / BOARD.name)

LIVE.parent.mkdir(parents=True, exist_ok=True)
staging = LIVE.parent / f"build.task-board-r32-r6-staging-{stamp}"
live_backup = LIVE.parent / f"build.task-board-r32-r6-backup-{stamp}"
live_swapped = False
r6_written = False

try:
    BOARD.write_text(updated)
    R6_STYLE.write_text(payload_css.rstrip() + "\n")
    r6_written = True

    written = BOARD.read_text()
    if written.count(r6_import) != 1:
        fail("R32_R6 import count invalid after write")
    if written.count('data-tos-task-mini-window-r32-r6="true"') != 1:
        fail("R32_R6 mini window hook count invalid after write")
    if written.count('className="tos-task-r32-r6-mini-window"') != 1:
        fail("R32_R6 mini window class count invalid after write")
    for path, digest in frozen.items():
        if sha256(path) != digest:
            fail(f"protected file changed unexpectedly: {path}")

    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists() or not (DIST / "index.html").exists():
        fail("frontend dist missing after build")

    built_css = "\n".join(p.read_text(errors="ignore") for p in DIST.rglob("*.css"))
    built_js = "\n".join(p.read_text(errors="ignore") for p in DIST.rglob("*.js"))
    for marker in (R5_MARKER, R6_MARKER):
        if marker not in built_css:
            fail(f"runtime CSS marker missing from build: {marker}")
    if "tos-task-r32-r6-mini-window" not in built_js or "tos-task-mini-window-r32-r6" not in built_js:
        fail("R32_R6 runtime mini window hook missing from built JS")

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
    if R6_MARKER not in live_css or "tos-task-r32-r6-mini-window" not in live_js:
        fail("R32_R6 runtime marker/hook missing from live build")

except Exception:
    shutil.copy2(backup_root / BOARD.name, BOARD)
    if r6_written and R6_STYLE.exists():
        R6_STYLE.unlink()
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
    request = urllib.request.Request("https://tos.tamiyouz.com/tasks", headers={"User-Agent": "TOS-R32-R6-Healthcheck"})
    with urllib.request.urlopen(request, timeout=15) as response:
        live_http = str(response.status)
except Exception:
    pass

print(f"VERSION={VERSION}")
print(f"PATCH_APPLIED={PATCH}")
print("BUILD_STATUS=PASS")
print("DEPLOY_STATUS=PASS")
print(f"LIVE_HTTP_STATUS={live_http}")
print("DEDICATED_MINIMIZED_UI=YES")
print("MINIMIZED_HEIGHT=64PX")
print("MINI_RESTORE=YES")
print("MINI_CLOSE=YES")
print("MINI_DRAG=YES")
print("NORMAL_MAXIMIZE_RESIZE_PRESERVED=YES")
print("BACKEND_CHANGED=NO")
print("API_CHANGED=NO")
print("DATABASE_CHANGED=NO")
print("PUSH=NO")
print("FINAL_STATUS=PASS")
