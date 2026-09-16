from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import time

PATCH = "TOS-TASK-BOARD-R32-R3-USER-CONTROLLABLE-TASK-WINDOW"
VERSION = "TOS_TASK_BOARD_R32_R3"
BASE_TOS_COMMIT = "3bb74d81ab67db42da9d435b391c6530bf29c96d"
R32_MARKER = "--tos-task-board-r32-trello-card-modal-runtime"
R1_MARKER = "--tos-task-board-r32-r1-modal-visibility-runtime"
R2_MARKER = "--tos-task-board-r32-r2-body-portal-runtime"
R3_MARKER = "--tos-task-board-r32-r3-user-controllable-window-runtime"
R32_CLASS = "tos-task-details-trello-overlay-r32"
R2_HOST = "tos-task-r32-r2-portal-host"
R3_DATA = 'data-tos-task-window-r32-r3="true"'
R3_STORAGE_KEY = "tos.tasks.taskDetailsWindow.r32r3"

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
R3_STYLE = STYLE_DIR / "taskBoardR32R3UserControllableWindow.css"
PAYLOAD = Path(__file__).resolve().parent / "taskBoardR32R3UserControllableWindow.css"


def fail(message):
    raise RuntimeError(message)


def run(command, cwd=None):
    subprocess.run(command, cwd=cwd, check=True)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


for path in (FRONTEND, STYLE_DIR, BOARD, PARTS, CHAT, APP, SIDEBAR, MANIFEST, R32_STYLE, R1_STYLE, R2_STYLE, PAYLOAD):
    if not path.exists():
        fail(f"required path missing: {path}")
for command in ("node", "npm"):
    if not shutil.which(command):
        fail(f"required command missing: {command}")

board_source = BOARD.read_text()
r32_css = R32_STYLE.read_text()
r1_css = R1_STYLE.read_text()
r2_css = R2_STYLE.read_text()
payload_css = PAYLOAD.read_text()

r2_import = 'import "../styles/taskBoardR32R2BodyPortalStackingFix.css";'
r3_import = 'import "../styles/taskBoardR32R3UserControllableWindow.css";'

for contract in (
    'import { createPortal } from "react-dom";',
    r2_import,
    R32_CLASS,
    R2_HOST,
    'data-tos-task-modal-portal="body"',
    "TOS_TASK_BOARD_R32_TRELLO_MODAL_NAVIGATION",
    "prefetchTaskDetails",
    "syncTaskModalUrl",
    "closeTaskDetails",
    'const [modalSize, setModalSize] = useState(getInitialTaskDetailsModalSize);',
    "function startResize(direction)",
):
    if contract not in board_source:
        fail(f"required R32_R2 live source contract missing: {contract}")
for marker, css in ((R32_MARKER, r32_css), (R1_MARKER, r1_css), (R2_MARKER, r2_css)):
    if marker not in css:
        fail(f"required prior stylesheet marker missing: {marker}")
if R3_MARKER not in payload_css:
    fail("R32_R3 payload marker missing")
for css_contract in (
    'data-tos-task-window-r32-r3="true"',
    'data-tos-task-window-minimized="true"',
    'data-tos-task-window-maximized="true"',
    "tos-task-r32-r3-resize-handle",
    "tos-task-r32-r3-window-controls",
    "@media(max-width:900px)",
):
    if css_contract not in payload_css:
        fail(f"R32_R3 CSS contract missing: {css_contract}")
if R3_STYLE.exists() or r3_import in board_source or R3_DATA in board_source or R3_STORAGE_KEY in board_source:
    fail("R32_R3 already appears to be applied")
if board_source.count(r2_import) != 1:
    fail(f"expected exactly one R32_R2 import, found {board_source.count(r2_import)}")

updated = board_source.replace(r2_import, r2_import + "\n" + r3_import, 1)

# Add persisted size/position plus desktop drag/minimize/maximize controls.
old_window_state = '''  const [showBackToTop, setShowBackToTop] = useState(false);
  const [modalSize, setModalSize] = useState(getInitialTaskDetailsModalSize);
  useModalFocusTrap(modalRef, closeButtonRef, onClose, "task-details-modal");'''
new_window_state = '''  const [showBackToTop, setShowBackToTop] = useState(false);
  const taskWindowStorageKeyR32R3 = "tos.tasks.taskDetailsWindow.r32r3";

  function readTaskWindowStateR32R3() {
    if (typeof window === "undefined") return null;
    try {
      const parsed = JSON.parse(window.localStorage.getItem(taskWindowStorageKeyR32R3) || "null");
      return parsed && typeof parsed === "object" ? parsed : null;
    } catch {
      return null;
    }
  }

  function clampTaskWindowPositionR32R3(position, size) {
    if (typeof window === "undefined") return position || { x: 12, y: 12 };
    const padding = 12;
    const safeSize = size || getInitialTaskDetailsModalSize();
    const width = Math.min(Number(safeSize.width) || 960, Math.max(320, window.innerWidth - (padding * 2)));
    const height = Math.min(Number(safeSize.height) || 640, Math.max(64, window.innerHeight - (padding * 2)));
    const maxX = Math.max(padding, window.innerWidth - width - padding);
    const maxY = Math.max(padding, window.innerHeight - height - padding);
    return {
      x: Math.min(maxX, Math.max(padding, Number(position?.x) || padding)),
      y: Math.min(maxY, Math.max(padding, Number(position?.y) || padding)),
    };
  }

  const [modalSize, setModalSize] = useState(() => {
    const saved = readTaskWindowStateR32R3();
    if (Number.isFinite(Number(saved?.width)) && Number.isFinite(Number(saved?.height))) {
      return clampTaskDetailsModalSize(Number(saved.width), Number(saved.height));
    }
    return getInitialTaskDetailsModalSize();
  });
  const [modalPosition, setModalPosition] = useState(() => {
    if (typeof window === "undefined") return { x: 12, y: 12 };
    const saved = readTaskWindowStateR32R3();
    const centered = {
      x: Math.max(12, Math.round((window.innerWidth - modalSize.width) / 2)),
      y: Math.max(12, Math.round((window.innerHeight - modalSize.height) / 2)),
    };
    if (!Number.isFinite(Number(saved?.x)) || !Number.isFinite(Number(saved?.y))) return clampTaskWindowPositionR32R3(centered, modalSize);
    return clampTaskWindowPositionR32R3({ x: Number(saved.x), y: Number(saved.y) }, modalSize);
  });
  const [isTaskWindowMinimized, setIsTaskWindowMinimized] = useState(false);
  const [isTaskWindowMaximized, setIsTaskWindowMaximized] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined" || window.innerWidth <= 900 || isTaskWindowMinimized || isTaskWindowMaximized) return;
    try {
      window.localStorage.setItem(taskWindowStorageKeyR32R3, JSON.stringify({
        width: modalSize.width,
        height: modalSize.height,
        x: modalPosition.x,
        y: modalPosition.y,
      }));
    } catch {
      // Persistence is an enhancement only.
    }
  }, [modalSize.width, modalSize.height, modalPosition.x, modalPosition.y, isTaskWindowMinimized, isTaskWindowMaximized]);

  useEffect(() => {
    if (typeof window === "undefined" || window.innerWidth <= 900) return;
    setModalPosition((current) => clampTaskWindowPositionR32R3(current, modalSize));
  }, [modalSize.width, modalSize.height]);

  function startTaskWindowDragR32R3(event) {
    if (typeof window === "undefined" || window.innerWidth <= 900 || isTaskWindowMaximized) return;
    if (event.button !== 0) return;
    if (event.target?.closest?.("button,a,input,select,textarea,[role='button']")) return;
    event.preventDefault();
    const effectiveSize = isTaskWindowMinimized
      ? { width: Math.min(520, Math.max(360, window.innerWidth - 24)), height: 64 }
      : modalSize;
    const startX = event.clientX;
    const startY = event.clientY;
    const startPosition = modalPosition;
    const previousUserSelect = document.body.style.userSelect;
    const previousCursor = document.body.style.cursor;
    document.body.style.userSelect = "none";
    document.body.style.cursor = "grabbing";

    function handleMove(moveEvent) {
      setModalPosition(clampTaskWindowPositionR32R3({
        x: startPosition.x + (moveEvent.clientX - startX),
        y: startPosition.y + (moveEvent.clientY - startY),
      }, effectiveSize));
    }

    function handleUp() {
      document.body.style.userSelect = previousUserSelect;
      document.body.style.cursor = previousCursor;
      window.removeEventListener("mousemove", handleMove);
      window.removeEventListener("mouseup", handleUp);
    }

    window.addEventListener("mousemove", handleMove);
    window.addEventListener("mouseup", handleUp);
  }

  function toggleTaskWindowMinimizedR32R3() {
    if (typeof window === "undefined" || window.innerWidth <= 900) return;
    setIsTaskWindowMaximized(false);
    setIsTaskWindowMinimized((current) => !current);
  }

  function toggleTaskWindowMaximizedR32R3() {
    if (typeof window === "undefined" || window.innerWidth <= 900) return;
    setIsTaskWindowMinimized(false);
    setIsTaskWindowMaximized((current) => !current);
  }

  useModalFocusTrap(modalRef, closeButtonRef, onClose, "task-details-modal");'''
if updated.count(old_window_state) != 1:
    fail(f"expected one task window state anchor, found {updated.count(old_window_state)}")
updated = updated.replace(old_window_state, new_window_state, 1)

# Existing resize implementation is already present; only gate it for desktop normal-window mode.
old_resize_head = '''  function startResize(direction) {
    return (event) => {
      if (typeof window === "undefined") return;'''
new_resize_head = '''  function startResize(direction) {
    return (event) => {
      if (typeof window === "undefined" || window.innerWidth <= 900 || isTaskWindowMaximized || isTaskWindowMinimized) return;'''
if updated.count(old_resize_head) != 1:
    fail(f"expected one startResize anchor, found {updated.count(old_resize_head)}")
updated = updated.replace(old_resize_head, new_resize_head, 1)

# Turn the visible R32_R2 dialog into a positioned desktop-like window and expose resize handles.
old_motion = '''      <motion.div
        ref={modalRef}
        tabIndex={-1}
        role="dialog"
        aria-modal="true"
        aria-label={draft.title || modalUi.taskDetails}
        className="tos-task-details-modal flex h-[100dvh] w-full flex-col overflow-hidden bg-transparent"
      >
        <div className="tos-task-reference-v2-topbar">'''
new_motion = '''      <motion.div
        ref={modalRef}
        tabIndex={-1}
        role="dialog"
        aria-modal="true"
        aria-label={draft.title || modalUi.taskDetails}
        data-tos-task-window-r32-r3="true"
        data-tos-task-window-minimized={isTaskWindowMinimized ? "true" : "false"}
        data-tos-task-window-maximized={isTaskWindowMaximized ? "true" : "false"}
        style={{
          "--tos-r32-r3-window-width": `${modalSize.width}px`,
          "--tos-r32-r3-window-height": `${modalSize.height}px`,
          "--tos-r32-r3-window-left": `${modalPosition.x}px`,
          "--tos-r32-r3-window-top": `${modalPosition.y}px`,
        }}
        className="tos-task-details-modal flex h-[100dvh] w-full flex-col overflow-hidden bg-transparent"
      >
        <div className="tos-task-r32-r3-resize-handle tos-task-r32-r3-resize-handle--right" onMouseDown={startResize("right")} aria-hidden="true" />
        <div className="tos-task-r32-r3-resize-handle tos-task-r32-r3-resize-handle--bottom" onMouseDown={startResize("bottom")} aria-hidden="true" />
        <div className="tos-task-r32-r3-resize-handle tos-task-r32-r3-resize-handle--corner" onMouseDown={startResize("corner")} aria-hidden="true" />
        <div className="tos-task-reference-v2-topbar">'''
if updated.count(old_motion) != 1:
    fail(f"expected one R32_R2 dialog motion anchor, found {updated.count(old_motion)}")
updated = updated.replace(old_motion, new_motion, 1)

# Header is the drag surface.
old_header = '<header className="tos-task-reference-v2-header">'
new_header = '<header className="tos-task-reference-v2-header" onMouseDown={startTaskWindowDragR32R3}>'
if updated.count(old_header) != 1:
    fail(f"expected one canonical Task Details header, found {updated.count(old_header)}")
updated = updated.replace(old_header, new_header, 1)

# Add a compact title used only while minimized.
old_breadcrumb_actions = '''            <strong>{isAr ? "تفاصيل المهمة" : "Task details"}</strong>
          </div>
          <div className="tos-task-v2-header-actions">
            <button ref={closeButtonRef} type="button" className="tos-task-v2-icon-action" onClick={onClose} aria-label={modalUi.closeTaskDetails || (isAr ? "إغلاق تفاصيل المهمة" : "Close task details")} title={modalUi.closeTaskDetails || (isAr ? "إغلاق" : "Close")}><X size={18} /></button>'''
new_breadcrumb_actions = '''            <strong>{isAr ? "تفاصيل المهمة" : "Task details"}</strong>
          </div>
          <div className="tos-task-r32-r3-mini-title" title={draft.title || modalUi.taskDetails}>{draft.title || modalUi.taskDetails}</div>
          <div className="tos-task-v2-header-actions">
            <button ref={closeButtonRef} type="button" className="tos-task-v2-icon-action" onClick={onClose} aria-label={modalUi.closeTaskDetails || (isAr ? "إغلاق تفاصيل المهمة" : "Close task details")} title={modalUi.closeTaskDetails || (isAr ? "إغلاق" : "Close")}><X size={18} /></button>
            <div className="tos-task-r32-r3-window-controls">
              <button type="button" className="tos-task-v2-icon-action" onClick={toggleTaskWindowMinimizedR32R3} aria-label={isTaskWindowMinimized ? (isAr ? "استعادة النافذة" : "Restore window") : (isAr ? "تصغير النافذة" : "Minimize window")} title={isTaskWindowMinimized ? (isAr ? "استعادة النافذة" : "Restore window") : (isAr ? "تصغير النافذة" : "Minimize window")}>{isTaskWindowMinimized ? <Maximize2 size={17} /> : <Minimize2 size={17} />}</button>
              <button type="button" className="tos-task-v2-icon-action" onClick={toggleTaskWindowMaximizedR32R3} aria-label={isTaskWindowMaximized ? (isAr ? "استعادة الحجم" : "Restore size") : (isAr ? "تكبير النافذة" : "Maximize window")} title={isTaskWindowMaximized ? (isAr ? "استعادة الحجم" : "Restore size") : (isAr ? "تكبير النافذة" : "Maximize window")}>{isTaskWindowMaximized ? <Square size={15} /> : <Maximize2 size={17} />}</button>
            </div>'''
if updated.count(old_breadcrumb_actions) != 1:
    fail(f"expected one canonical header actions anchor, found {updated.count(old_breadcrumb_actions)}")
updated = updated.replace(old_breadcrumb_actions, new_breadcrumb_actions, 1)

# Verify transformations before touching production files.
for contract in (
    r3_import,
    R3_DATA,
    R3_STORAGE_KEY,
    "startTaskWindowDragR32R3",
    "toggleTaskWindowMinimizedR32R3",
    "toggleTaskWindowMaximizedR32R3",
    "tos-task-r32-r3-window-controls",
    "tos-task-r32-r3-resize-handle--corner",
    'data-tos-task-window-minimized={isTaskWindowMinimized ? "true" : "false"}',
    'data-tos-task-window-maximized={isTaskWindowMaximized ? "true" : "false"}',
):
    if contract not in updated:
        fail(f"R32_R3 source contract missing after transform: {contract}")
for preserved in (R32_CLASS, R2_HOST, "prefetchTaskDetails", "syncTaskModalUrl", "closeTaskDetails", "onNavigateTask={openTaskDetails}"):
    if board_source.count(preserved) != updated.count(preserved):
        fail(f"prior R32 behavior contract changed unexpectedly: {preserved}")

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

frozen = {path: sha256(path) for path in (PARTS, CHAT, APP, SIDEBAR, R32_STYLE, R1_STYLE, R2_STYLE)}
stamp = int(time.time())
backup_root = Path(f"/var/backups/tos-patches/task-board-r32-r3-{stamp}")
backup_root.mkdir(parents=True, exist_ok=False)
shutil.copy2(BOARD, backup_root / BOARD.name)

LIVE.parent.mkdir(parents=True, exist_ok=True)
staging = LIVE.parent / f"build.task-board-r32-r3-staging-{stamp}"
live_backup = LIVE.parent / f"build.task-board-r32-r3-backup-{stamp}"
live_swapped = False
r3_written = False

try:
    BOARD.write_text(updated)
    R3_STYLE.write_text(payload_css.rstrip() + "\n")
    r3_written = True

    written = BOARD.read_text()
    for contract in (r3_import, R3_DATA, R3_STORAGE_KEY, "tos-task-r32-r3-window-controls", "tos-task-r32-r3-resize-handle--corner"):
        if contract not in written:
            fail(f"R32_R3 source hook missing after write: {contract}")
    for path, digest in frozen.items():
        if sha256(path) != digest:
            fail(f"protected file changed unexpectedly: {path}")

    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists() or not (DIST / "index.html").exists():
        fail("frontend dist missing after build")

    built_css = "\n".join(p.read_text(errors="ignore") for p in DIST.rglob("*.css"))
    built_js = "\n".join(p.read_text(errors="ignore") for p in DIST.rglob("*.js"))
    for marker in (R32_MARKER, R1_MARKER, R2_MARKER, R3_MARKER):
        if marker not in built_css:
            fail(f"runtime CSS marker missing from build: {marker}")
    for hook in (R32_CLASS, R2_HOST, "tos-task-window-r32-r3", R3_STORAGE_KEY, "tos-task-r32-r3-window-controls"):
        if hook not in built_js:
            fail(f"R32_R3 runtime JS hook missing from build: {hook}")

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
    for marker in (R32_MARKER, R1_MARKER, R2_MARKER, R3_MARKER):
        if marker not in live_css:
            fail(f"runtime CSS marker missing from live build: {marker}")
    for hook in (R2_HOST, "tos-task-window-r32-r3", R3_STORAGE_KEY):
        if hook not in live_js:
            fail(f"R32_R3 runtime JS hook missing from live build: {hook}")

except Exception:
    shutil.copy2(backup_root / BOARD.name, BOARD)
    if r3_written and R3_STYLE.exists():
        R3_STYLE.unlink()
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
print("DRAGGABLE_WINDOW=YES")
print("RESIZABLE_WINDOW=YES")
print("MINIMIZE_RESTORE=YES")
print("MAXIMIZE_RESTORE=YES")
print("SIZE_POSITION_PERSISTENCE=LOCAL_STORAGE")
print("MOBILE_FULLSCREEN_PRESERVED=YES")
print("R32_R2_BODY_PORTAL_PRESERVED=YES")
print("BOARD_CONTEXT_PRESERVED=YES")
print("PREFETCH_PRESERVED=YES")
print("URL_BACK_NAV_PRESERVED=YES")
print("PREV_NEXT_PRESERVED=YES")
print("BACKEND_CHANGED=NO")
print("API_CHANGED=NO")
print("DATABASE_CHANGED=NO")
print("PUSH=NO")
print("FINAL_STATUS=PASS")
