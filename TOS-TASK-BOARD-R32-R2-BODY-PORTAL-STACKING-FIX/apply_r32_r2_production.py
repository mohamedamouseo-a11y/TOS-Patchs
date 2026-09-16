from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import time

PATCH = "TOS-TASK-BOARD-R32-R2-BODY-PORTAL-STACKING-FIX"
VERSION = "TOS_TASK_BOARD_R32_R2"
BASE_TOS_COMMIT = "f3671756ba1c49ae7304509276d52eb5cb69d04d"
R32_MARKER = "--tos-task-board-r32-trello-card-modal-runtime"
R1_MARKER = "--tos-task-board-r32-r1-modal-visibility-runtime"
R2_MARKER = "--tos-task-board-r32-r2-body-portal-runtime"
R32_CLASS = "tos-task-details-trello-overlay-r32"
R2_HOST = "tos-task-r32-r2-portal-host"
R2_DATA = 'data-tos-task-modal-portal="body"'

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
STYLE_DIR = FRONTEND / "src/styles"
BOARD = FRONTEND / "src/components/ProfessionalTaskBoard.jsx"
PARTS = FRONTEND / "src/features/tasks/taskBoardParts.jsx"
CHAT = FRONTEND / "src/components/ChatPanel.jsx"
APP = FRONTEND / "src/App.jsx"
SIDEBAR = FRONTEND / "src/components/layout/Sidebar.jsx"
MANIFEST = ROOT / "deployment/tos-production-runtime.json"
R32_STYLE = STYLE_DIR / "taskBoardR32TrelloModalNavigation.css"
R1_STYLE = STYLE_DIR / "taskBoardR32R1ModalVisibilityRecovery.css"
R2_STYLE = STYLE_DIR / "taskBoardR32R2BodyPortalStackingFix.css"
PAYLOAD = Path(__file__).resolve().parent / "taskBoardR32R2BodyPortalStackingFix.css"


def fail(message):
    raise RuntimeError(message)


def run(command, cwd=None):
    subprocess.run(command, cwd=cwd, check=True)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


for path in (FRONTEND, STYLE_DIR, BOARD, PARTS, CHAT, APP, SIDEBAR, MANIFEST, R32_STYLE, R1_STYLE, PAYLOAD):
    if not path.exists():
        fail(f"required path missing: {path}")
for command in ("node", "npm"):
    if not shutil.which(command):
        fail(f"required command missing: {command}")

board_source = BOARD.read_text()
r32_css = R32_STYLE.read_text()
r1_css = R1_STYLE.read_text()
payload_css = PAYLOAD.read_text()

r1_import = 'import "../styles/taskBoardR32R1ModalVisibilityRecovery.css";'
r2_import = 'import "../styles/taskBoardR32R2BodyPortalStackingFix.css";'

for contract in (
    'import { createPortal } from "react-dom";',
    r1_import,
    R32_CLASS,
    "TOS_TASK_BOARD_R32_TRELLO_MODAL_NAVIGATION",
    "prefetchTaskDetails",
    "syncTaskModalUrl",
    "closeTaskDetails",
):
    if contract not in board_source:
        fail(f"required R32/R32_R1 live source contract missing: {contract}")
if R32_MARKER not in r32_css:
    fail("R32 stylesheet marker missing")
if R1_MARKER not in r1_css:
    fail("R32_R1 stylesheet marker missing")
if R2_MARKER not in payload_css or R2_HOST not in payload_css:
    fail("R32_R2 payload contract missing")
if R2_STYLE.exists() or r2_import in board_source or R2_HOST in board_source:
    fail("R32_R2 already appears to be applied")
if board_source.count(r1_import) != 1:
    fail(f"expected exactly one R32_R1 import, found {board_source.count(r1_import)}")

old_render = '''        {selectedTask && activeBoard && (
          <TaskDetailsErrorBoundary resetKey={`${selectedTask.id}-${selectedTask.updatedAt || ""}`} onClose={closeTaskDetails} ui={ui}>
            <CardDetailsModal task={selectedTask} tasks={tasks} dependencyTasks={dependencyTasks} lists={lists} labels={labels} members={members} projectMembers={projectMembers} availableProjectUsers={availableProjectUsers} taskServices={taskServices} permissions={permissions} user={user} onClose={closeTaskDetails} onUpdate={replaceTask} onDeleteLocal={removeLocalTask} onLabelCreated={addLabelLocal} onRequestArchive={requestArchiveTaskFromCard} onNavigateTask={openTaskDetails} initialTab={selectedTaskInitialTab} />
          </TaskDetailsErrorBoundary>
        )}'''

new_render = '''        {selectedTask && activeBoard && typeof document !== "undefined" && createPortal(
          <div className="tos-task-r32-r2-portal-host" data-tos-task-modal-portal="body">
            <TaskDetailsErrorBoundary resetKey={`${selectedTask.id}-${selectedTask.updatedAt || ""}`} onClose={closeTaskDetails} ui={ui}>
              <CardDetailsModal task={selectedTask} tasks={tasks} dependencyTasks={dependencyTasks} lists={lists} labels={labels} members={members} projectMembers={projectMembers} availableProjectUsers={availableProjectUsers} taskServices={taskServices} permissions={permissions} user={user} onClose={closeTaskDetails} onUpdate={replaceTask} onDeleteLocal={removeLocalTask} onLabelCreated={addLabelLocal} onRequestArchive={requestArchiveTaskFromCard} onNavigateTask={openTaskDetails} initialTab={selectedTaskInitialTab} />
            </TaskDetailsErrorBoundary>
          </div>,
          document.body,
        )}'''

if board_source.count(old_render) != 1:
    fail(f"expected exactly one R32_R1 selectedTask render block, found {board_source.count(old_render)}")

updated = board_source.replace(r1_import, r1_import + "\n" + r2_import, 1)
updated = updated.replace(old_render, new_render, 1)

if updated.count(r2_import) != 1 or updated.count(R2_HOST) != 1 or updated.count(R2_DATA) != 1:
    fail("R32_R2 source transformation verification failed")
if updated.count("createPortal(") != board_source.count("createPortal(") + 1:
    fail("R32_R2 expected exactly one new createPortal call")
for contract in (R32_CLASS, "prefetchTaskDetails", "syncTaskModalUrl", "closeTaskDetails", "onNavigateTask={openTaskDetails}"):
    if board_source.count(contract) != updated.count(contract):
        fail(f"R32 behavior contract changed unexpectedly: {contract}")

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

frozen = {path: sha256(path) for path in (PARTS, CHAT, APP, SIDEBAR, R32_STYLE, R1_STYLE)}
stamp = int(time.time())
backup_root = Path(f"/var/backups/tos-patches/task-board-r32-r2-{stamp}")
backup_root.mkdir(parents=True, exist_ok=False)
shutil.copy2(BOARD, backup_root / BOARD.name)

LIVE.parent.mkdir(parents=True, exist_ok=True)
staging = LIVE.parent / f"build.task-board-r32-r2-staging-{stamp}"
live_backup = LIVE.parent / f"build.task-board-r32-r2-backup-{stamp}"
live_swapped = False
r2_written = False

try:
    BOARD.write_text(updated)
    R2_STYLE.write_text(payload_css.rstrip() + "\n")
    r2_written = True

    written = BOARD.read_text()
    if written.count(r2_import) != 1 or written.count(R2_HOST) != 1 or written.count(R2_DATA) != 1:
        fail("R32_R2 source hooks missing after write")
    for path, digest in frozen.items():
        if sha256(path) != digest:
            fail(f"protected file changed unexpectedly: {path}")

    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists() or not (DIST / "index.html").exists():
        fail("frontend dist missing after build")

    built_css = "\n".join(p.read_text(errors="ignore") for p in DIST.rglob("*.css"))
    built_js = "\n".join(p.read_text(errors="ignore") for p in DIST.rglob("*.js"))
    for marker in (R32_MARKER, R1_MARKER, R2_MARKER):
        if marker not in built_css:
            fail(f"runtime CSS marker missing from build: {marker}")
    if R32_CLASS not in built_js or R2_HOST not in built_js or "tos-task-modal-portal" not in built_js:
        fail("R32_R2 modal portal hooks missing from built JS")

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
    for marker in (R32_MARKER, R1_MARKER, R2_MARKER):
        if marker not in live_css:
            fail(f"runtime CSS marker missing from live build: {marker}")
    if R32_CLASS not in live_js or R2_HOST not in live_js:
        fail("R32_R2 modal portal hooks missing from live JS")

except Exception:
    shutil.copy2(backup_root / BOARD.name, BOARD)
    if r2_written and R2_STYLE.exists():
        R2_STYLE.unlink()
    if live_swapped:
        if LIVE.exists():
            shutil.rmtree(LIVE)
        if live_backup.exists():
            live_backup.rename(LIVE)
    elif staging.exists():
        shutil.rmtree(staging)
    raise

print(f"VERSION={VERSION}")
print(f"PATCH_APPLIED={PATCH}")
print(f"BASE_TOS_COMMIT_REVIEWED={BASE_TOS_COMMIT}")
print("BUILD_STATUS=PASS")
print("DEPLOY_STATUS=PASS")
print("BODY_PORTAL=YES")
print("VIEWPORT_STACKING_FIX=YES")
print("R32_PRESERVED=YES")
print("R32_R1_PRESERVED=YES")
print("BOARD_CONTEXT_PRESERVED=YES")
print("PREFETCH_PRESERVED=YES")
print("URL_BACK_NAV_PRESERVED=YES")
print("PREV_NEXT_PRESERVED=YES")
print("BACKEND_CHANGED=NO")
print("API_CHANGED=NO")
print("DATABASE_CHANGED=NO")
print("PUSH=NO")
print("FINAL_STATUS=PASS")
