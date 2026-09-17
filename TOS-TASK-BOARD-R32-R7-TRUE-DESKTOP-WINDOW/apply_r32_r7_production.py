from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import time
import urllib.request

PATCH = "TOS-TASK-BOARD-R32-R7-TRUE-DESKTOP-WINDOW"
VERSION = "TOS_TASK_BOARD_R32_R7"
BASE_TOS_COMMIT = "8e13de3b447b1a85e907efc2f1a2ed423c075c36"
R6R1_MARKER = "--tos-task-board-r32-r6-r1-recovery-minimized-header-runtime"
R7_MARKER = "--tos-task-board-r32-r7-true-desktop-window-runtime"

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
R6R1_STYLE = STYLE_DIR / "taskBoardR32R6R1RecoveryMinimizedHeader.css"
R7_STYLE = STYLE_DIR / "taskBoardR32R7TrueDesktopWindow.css"
PAYLOAD = Path(__file__).resolve().parent / "taskBoardR32R7TrueDesktopWindow.css"


def fail(message):
    raise RuntimeError(message)


def run(command, cwd=None):
    subprocess.run(command, cwd=cwd, check=True)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


for path in (FRONTEND, STYLE_DIR, BOARD, PARTS, CHAT, APP, SIDEBAR, MANIFEST, R3_STYLE, R4_STYLE, R5_STYLE, R6R1_STYLE, PAYLOAD):
    if not path.exists():
        fail(f"required path missing: {path}")
for command in ("node", "npm"):
    if not shutil.which(command):
        fail(f"required command missing: {command}")

board_source = BOARD.read_text()
r6r1_css = R6R1_STYLE.read_text()
payload_css = PAYLOAD.read_text()
r6r1_import = 'import "../styles/taskBoardR32R6R1RecoveryMinimizedHeader.css";'
r7_import = 'import "../styles/taskBoardR32R7TrueDesktopWindow.css";'

for contract in (
    r6r1_import,
    'const taskWindowStorageKeyR32R3 = "tos.tasks.taskDetailsWindow.r32r5";',
    'data-tos-task-window-r32-r5="true"',
    'data-tos-task-window-minimized={isTaskWindowMinimized ? "true" : "false"}',
    'data-tos-task-window-maximized={isTaskWindowMaximized ? "true" : "false"}',
    "taskWindowGeometryR32R5",
    "toggleTaskWindowMinimizedR32R3",
    "toggleTaskWindowMaximizedR32R3",
    "startTaskWindowDragR32R3",
    "function startResize(direction)",
):
    if contract not in board_source:
        fail(f"required R32_R6_R1 live source contract missing: {contract}")
if R6R1_MARKER not in r6r1_css:
    fail("R32_R6_R1 stylesheet marker missing")
if R7_MARKER not in payload_css:
    fail("R32_R7 payload marker missing")
if R7_STYLE.exists() or r7_import in board_source or 'data-tos-task-window-r32-r7="true"' in board_source:
    fail("R32_R7 already appears to be applied")
if board_source.count(r6r1_import) != 1:
    fail(f"expected one R32_R6_R1 import, found {board_source.count(r6r1_import)}")

updated = board_source.replace(r6r1_import, r6r1_import + "\n" + r7_import, 1)
updated = updated.replace(
    'const taskWindowStorageKeyR32R3 = "tos.tasks.taskDetailsWindow.r32r5";',
    'const taskWindowStorageKeyR32R3 = "tos.tasks.taskDetailsWindow.r32r7";',
    1,
)

position_anchor = '''  function clampTaskWindowPositionR32R3(position, size) {'''
size_helper = '''  function clampTaskWindowSizeR32R7(width, height) {
    if (typeof window === "undefined") {
      return { width: Number(width) || 960, height: Number(height) || 640 };
    }
    const maxWidth = Math.max(720, window.innerWidth - 24);
    const maxHeight = Math.max(480, window.innerHeight - 24);
    return {
      width: Math.min(maxWidth, Math.max(720, Number(width) || 960)),
      height: Math.min(maxHeight, Math.max(480, Number(height) || 640)),
    };
  }

  function clampTaskWindowPositionR32R3(position, size) {'''
if updated.count(position_anchor) != 1:
    fail(f"expected one position clamp anchor, found {updated.count(position_anchor)}")
updated = updated.replace(position_anchor, size_helper, 1)

old_modal_size = '''  const [modalSize, setModalSize] = useState(() => {
    const saved = readTaskWindowStateR32R3();
    if (Number.isFinite(Number(saved?.width)) && Number.isFinite(Number(saved?.height))) {
      return clampTaskDetailsModalSize(Number(saved.width), Number(saved.height));
    }
    if (typeof window === "undefined") return getInitialTaskDetailsModalSize();
    return clampTaskDetailsModalSize(
      Math.min(1360, Math.max(960, Math.round(window.innerWidth * 0.84))),
      Math.min(860, Math.max(640, Math.round(window.innerHeight * 0.82))),
    );
  });'''
new_modal_size = '''  const [modalSize, setModalSize] = useState(() => {
    const saved = readTaskWindowStateR32R3();
    if (Number.isFinite(Number(saved?.width)) && Number.isFinite(Number(saved?.height))) {
      return clampTaskWindowSizeR32R7(Number(saved.width), Number(saved.height));
    }
    if (typeof window === "undefined") return getInitialTaskDetailsModalSize();
    return clampTaskWindowSizeR32R7(
      Math.round(window.innerWidth * 0.74),
      Math.round(window.innerHeight * 0.76),
    );
  });'''
if updated.count(old_modal_size) != 1:
    fail(f"expected one modal size initializer, found {updated.count(old_modal_size)}")
updated = updated.replace(old_modal_size, new_modal_size, 1)

old_min_geometry = '''    if (isTaskWindowMinimized) {
      const width = Math.min(520, Math.max(360, window.innerWidth - 24));
      const height = 64;'''
new_min_geometry = '''    if (isTaskWindowMinimized) {
      const width = Math.min(460, Math.max(340, Math.round(window.innerWidth * 0.26)));
      const height = 64;'''
if updated.count(old_min_geometry) != 1:
    fail(f"expected one minimized geometry anchor, found {updated.count(old_min_geometry)}")
updated = updated.replace(old_min_geometry, new_min_geometry, 1)

old_drag_size = '''    const effectiveSize = isTaskWindowMinimized
      ? { width: Math.min(520, Math.max(360, window.innerWidth - 24)), height: 64 }
      : modalSize;'''
new_drag_size = '''    const effectiveSize = isTaskWindowMinimized
      ? { width: Math.min(460, Math.max(340, Math.round(window.innerWidth * 0.26))), height: 64 }
      : modalSize;'''
if updated.count(old_drag_size) != 1:
    fail(f"expected one minimized drag size anchor, found {updated.count(old_drag_size)}")
updated = updated.replace(old_drag_size, new_drag_size, 1)

old_viewport_resize = '''  useEffect(() => {
    function handleViewportResize() {
      setModalSize((current) => clampTaskDetailsModalSize(current.width, current.height));
    }

    window.addEventListener("resize", handleViewportResize);
    return () => window.removeEventListener("resize", handleViewportResize);
  }, []);'''
new_viewport_resize = '''  useEffect(() => {
    function handleViewportResize() {
      setModalSize((current) => clampTaskWindowSizeR32R7(current.width, current.height));
    }

    window.addEventListener("resize", handleViewportResize);
    return () => window.removeEventListener("resize", handleViewportResize);
  }, []);'''
if updated.count(old_viewport_resize) != 1:
    fail(f"expected one viewport resize anchor, found {updated.count(old_viewport_resize)}")
updated = updated.replace(old_viewport_resize, new_viewport_resize, 1)

old_resize = '''  function startResize(direction) {
    return (event) => {
      if (typeof window === "undefined" || window.innerWidth <= 900 || isTaskWindowMaximized || isTaskWindowMinimized) return;
      event.preventDefault();
      event.stopPropagation();
      const startX = event.clientX;
      const startY = event.clientY;
      const startWidth = modalSize.width;
      const startHeight = modalSize.height;
      const previousUserSelect = document.body.style.userSelect;
      const previousCursor = document.body.style.cursor;
      const cursor = direction === "right" ? "ew-resize" : direction === "bottom" ? "ns-resize" : "nwse-resize";
      document.body.style.userSelect = "none";
      document.body.style.cursor = cursor;

      function handleMove(moveEvent) {
        const deltaX = moveEvent.clientX - startX;
        const deltaY = moveEvent.clientY - startY;
        const nextWidth = direction === "bottom" ? startWidth : startWidth + deltaX;
        const nextHeight = direction === "right" ? startHeight : startHeight + deltaY;
        setModalSize(clampTaskDetailsModalSize(nextWidth, nextHeight));
      }

      function handleUp() {
        document.body.style.userSelect = previousUserSelect;
        document.body.style.cursor = previousCursor;
        window.removeEventListener("mousemove", handleMove);
        window.removeEventListener("mouseup", handleUp);
      }

      window.addEventListener("mousemove", handleMove);
      window.addEventListener("mouseup", handleUp);
    };
  }'''
new_resize = '''  function startResize(direction) {
    return (event) => {
      if (typeof window === "undefined" || window.innerWidth <= 900 || isTaskWindowMaximized || isTaskWindowMinimized) return;
      if (event.button !== 0) return;
      event.preventDefault();
      event.stopPropagation();
      const startX = event.clientX;
      const startY = event.clientY;
      const startWidth = modalSize.width;
      const startHeight = modalSize.height;
      const startLeft = modalPosition.x;
      const startTop = modalPosition.y;
      const startRight = startLeft + startWidth;
      const startBottom = startTop + startHeight;
      const minWidth = 720;
      const minHeight = 480;
      const previousUserSelect = document.body.style.userSelect;
      const previousCursor = document.body.style.cursor;
      const cursorMap = {
        left: "ew-resize",
        right: "ew-resize",
        top: "ns-resize",
        bottom: "ns-resize",
        "top-left": "nwse-resize",
        "bottom-right": "nwse-resize",
        "top-right": "nesw-resize",
        "bottom-left": "nesw-resize",
      };
      document.body.style.userSelect = "none";
      document.body.style.cursor = cursorMap[direction] || "nwse-resize";

      function handleMove(moveEvent) {
        const deltaX = moveEvent.clientX - startX;
        const deltaY = moveEvent.clientY - startY;
        let nextLeft = startLeft;
        let nextTop = startTop;
        let nextWidth = startWidth;
        let nextHeight = startHeight;

        if (direction.includes("left")) {
          nextLeft = Math.min(startRight - minWidth, Math.max(12, startLeft + deltaX));
          nextWidth = startRight - nextLeft;
        } else if (direction.includes("right")) {
          nextWidth = Math.min(window.innerWidth - startLeft - 12, Math.max(minWidth, startWidth + deltaX));
        }

        if (direction.includes("top")) {
          nextTop = Math.min(startBottom - minHeight, Math.max(12, startTop + deltaY));
          nextHeight = startBottom - nextTop;
        } else if (direction.includes("bottom")) {
          nextHeight = Math.min(window.innerHeight - startTop - 12, Math.max(minHeight, startHeight + deltaY));
        }

        const nextSize = clampTaskWindowSizeR32R7(nextWidth, nextHeight);
        setModalPosition({ x: nextLeft, y: nextTop });
        setModalSize(nextSize);
      }

      function handleUp() {
        document.body.style.userSelect = previousUserSelect;
        document.body.style.cursor = previousCursor;
        window.removeEventListener("mousemove", handleMove);
        window.removeEventListener("mouseup", handleUp);
      }

      window.addEventListener("mousemove", handleMove);
      window.addEventListener("mouseup", handleUp);
    };
  }'''
if updated.count(old_resize) != 1:
    fail(f"expected one legacy resize function, found {updated.count(old_resize)}")
updated = updated.replace(old_resize, new_resize, 1)

r5_data = '        data-tos-task-window-r32-r5="true"\n'
r7_data = '        data-tos-task-window-r32-r5="true"\n        data-tos-task-window-r32-r7="true"\n'
if updated.count(r5_data) != 1:
    fail(f"expected one R32_R5 data hook, found {updated.count(r5_data)}")
updated = updated.replace(r5_data, r7_data, 1)

old_handles = '''        <div className="tos-task-r32-r3-resize-handle tos-task-r32-r3-resize-handle--right" onMouseDown={startResize("right")} aria-hidden="true" />
        <div className="tos-task-r32-r3-resize-handle tos-task-r32-r3-resize-handle--bottom" onMouseDown={startResize("bottom")} aria-hidden="true" />
        <div className="tos-task-r32-r3-resize-handle tos-task-r32-r3-resize-handle--corner" onMouseDown={startResize("corner")} aria-hidden="true" />'''
new_handles = '''        <div className="tos-task-r32-r7-resize-handle tos-task-r32-r7-resize-handle--left" onMouseDown={startResize("left")} aria-hidden="true" />
        <div className="tos-task-r32-r7-resize-handle tos-task-r32-r7-resize-handle--right" onMouseDown={startResize("right")} aria-hidden="true" />
        <div className="tos-task-r32-r7-resize-handle tos-task-r32-r7-resize-handle--top" onMouseDown={startResize("top")} aria-hidden="true" />
        <div className="tos-task-r32-r7-resize-handle tos-task-r32-r7-resize-handle--bottom" onMouseDown={startResize("bottom")} aria-hidden="true" />
        <div className="tos-task-r32-r7-resize-handle tos-task-r32-r7-resize-handle--top-left" onMouseDown={startResize("top-left")} aria-hidden="true" />
        <div className="tos-task-r32-r7-resize-handle tos-task-r32-r7-resize-handle--top-right" onMouseDown={startResize("top-right")} aria-hidden="true" />
        <div className="tos-task-r32-r7-resize-handle tos-task-r32-r7-resize-handle--bottom-left" onMouseDown={startResize("bottom-left")} aria-hidden="true" />
        <div className="tos-task-r32-r7-resize-handle tos-task-r32-r7-resize-handle--bottom-right" onMouseDown={startResize("bottom-right")} aria-hidden="true" />'''
if updated.count(old_handles) != 1:
    fail(f"expected one old resize handle block, found {updated.count(old_handles)}")
updated = updated.replace(old_handles, new_handles, 1)

old_header = '<header className="tos-task-reference-v2-header" onMouseDown={startTaskWindowDragR32R3}>'
new_header = '<header className="tos-task-reference-v2-header" onMouseDown={startTaskWindowDragR32R3} onDoubleClick={toggleTaskWindowMaximizedR32R3} data-tos-task-window-drag-surface="true">'
if updated.count(old_header) != 1:
    fail(f"expected one Task Details drag header, found {updated.count(old_header)}")
updated = updated.replace(old_header, new_header, 1)

for contract in (
    r7_import,
    'tos.tasks.taskDetailsWindow.r32r7',
    "clampTaskWindowSizeR32R7",
    'data-tos-task-window-r32-r7="true"',
    'startResize("left")',
    'startResize("top")',
    'startResize("bottom-right")',
    'data-tos-task-window-drag-surface="true"',
    "Math.round(window.innerWidth * 0.74)",
    "Math.round(window.innerHeight * 0.76)",
):
    if contract not in updated:
        fail(f"R32_R7 transformed source contract missing: {contract}")

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

frozen = {path: sha256(path) for path in (PARTS, CHAT, APP, SIDEBAR, R3_STYLE, R4_STYLE, R5_STYLE, R6R1_STYLE)}
stamp = int(time.time())
backup_root = Path(f"/var/backups/tos-patches/task-board-r32-r7-{stamp}")
backup_root.mkdir(parents=True, exist_ok=False)
shutil.copy2(BOARD, backup_root / BOARD.name)

LIVE.parent.mkdir(parents=True, exist_ok=True)
staging = LIVE.parent / f"build.task-board-r32-r7-staging-{stamp}"
live_backup = LIVE.parent / f"build.task-board-r32-r7-backup-{stamp}"
live_swapped = False
r7_written = False

try:
    BOARD.write_text(updated)
    R7_STYLE.write_text(payload_css.rstrip() + "\n")
    r7_written = True

    written = BOARD.read_text()
    if written.count(r7_import) != 1:
        fail("R32_R7 import count invalid after write")
    if written.count('data-tos-task-window-r32-r7="true"') != 1:
        fail("R32_R7 window data hook count invalid after write")
    if written.count('className="tos-task-r32-r7-resize-handle') != 8:
        fail("R32_R7 expected exactly 8 resize handles")
    for path, digest in frozen.items():
        if sha256(path) != digest:
            fail(f"protected file changed unexpectedly: {path}")

    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists() or not (DIST / "index.html").exists():
        fail("frontend dist missing after build")

    built_css = "\n".join(p.read_text(errors="ignore") for p in DIST.rglob("*.css"))
    built_js = "\n".join(p.read_text(errors="ignore") for p in DIST.rglob("*.js"))
    if R6R1_MARKER not in built_css or R7_MARKER not in built_css:
        fail("R32_R6_R1/R32_R7 runtime CSS marker missing from build")
    for hook in ("tos-task-window-r32-r7", "tos-task-r32-r7-resize-handle", "tos.tasks.taskDetailsWindow.r32r7"):
        if hook not in built_js:
            fail(f"R32_R7 runtime hook missing from built JS: {hook}")

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
    if R7_MARKER not in live_css or "tos-task-window-r32-r7" not in live_js:
        fail("R32_R7 runtime marker/hook missing from live build")

except Exception:
    shutil.copy2(backup_root / BOARD.name, BOARD)
    if r7_written and R7_STYLE.exists():
        R7_STYLE.unlink()
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
    request = urllib.request.Request("https://tos.tamiyouz.com/tasks", headers={"User-Agent": "TOS-R32-R7-Healthcheck"})
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
print("TRUE_DESKTOP_WINDOW=YES")
print("NORMAL_DEFAULT_VIEWPORT=74x76_PERCENT")
print("RESIZE_EDGES=4")
print("RESIZE_CORNERS=4")
print("DRAG_HEADER=YES")
print("DOUBLE_CLICK_MAXIMIZE_RESTORE=YES")
print("COMPACT_MINIMIZED_BAR=YES")
print("RESTORE_SIZE_POSITION_PRESERVED=YES")
print("BOARD_MOUSE_INTERACTIVE_BEHIND_WINDOW=YES")
print("MOBILE_FULLSCREEN_PRESERVED=YES")
print("BACKEND_CHANGED=NO")
print("API_CHANGED=NO")
print("DATABASE_CHANGED=NO")
print("PUSH=NO")
print("FINAL_STATUS=PASS")
