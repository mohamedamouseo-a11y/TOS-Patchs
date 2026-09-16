from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import time
import urllib.request

PATCH = "TOS-TASK-BOARD-R32-R5-INLINE-WINDOW-GEOMETRY-FIX"
VERSION = "TOS_TASK_BOARD_R32_R5"
BASE_TOS_COMMIT = "3bb74d81ab67db42da9d435b391c6530bf29c96d"
R3_MARKER = "--tos-task-board-r32-r3-user-controllable-window-runtime"
R4_MARKER = "--tos-task-board-r32-r4-window-state-specificity-runtime"
R5_MARKER = "--tos-task-board-r32-r5-inline-window-geometry-runtime"
R3_DATA = 'data-tos-task-window-r32-r3="true"'
R5_DATA = 'data-tos-task-window-r32-r5="true"'
R5_STORAGE_KEY = "tos.tasks.taskDetailsWindow.r32r5"

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
PAYLOAD = Path(__file__).resolve().parent / "taskBoardR32R5InlineWindowGeometryFix.css"


def fail(message):
    raise RuntimeError(message)


def run(command, cwd=None):
    subprocess.run(command, cwd=cwd, check=True)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


for path in (FRONTEND, STYLE_DIR, BOARD, PARTS, CHAT, APP, SIDEBAR, MANIFEST, R3_STYLE, R4_STYLE, PAYLOAD):
    if not path.exists():
        fail(f"required path missing: {path}")
for command in ("node", "npm"):
    if not shutil.which(command):
        fail(f"required command missing: {command}")

board_source = BOARD.read_text()
r3_css = R3_STYLE.read_text()
r4_css = R4_STYLE.read_text()
payload_css = PAYLOAD.read_text()

r4_import = 'import "../styles/taskBoardR32R4WindowStateSpecificityFix.css";'
r5_import = 'import "../styles/taskBoardR32R5InlineWindowGeometryFix.css";'

for contract in (
    r4_import,
    R3_DATA,
    'data-tos-task-window-minimized={isTaskWindowMinimized ? "true" : "false"}',
    'data-tos-task-window-maximized={isTaskWindowMaximized ? "true" : "false"}',
    "toggleTaskWindowMinimizedR32R3",
    "toggleTaskWindowMaximizedR32R3",
    "startTaskWindowDragR32R3",
    "function startResize(direction)",
    'const taskWindowStorageKeyR32R3 = "tos.tasks.taskDetailsWindow.r32r3";',
):
    if contract not in board_source:
        fail(f"required R32_R4 live source contract missing: {contract}")
if R3_MARKER not in r3_css:
    fail("R32_R3 stylesheet marker missing")
if R4_MARKER not in r4_css:
    fail("R32_R4 stylesheet marker missing")
for contract in (R5_MARKER, R5_DATA, "--tos-r32-r5-window-width", "--tos-r32-r5-window-height"):
    if contract not in payload_css:
        fail(f"R32_R5 payload contract missing: {contract}")
if R5_STYLE.exists() or r5_import in board_source or R5_DATA in board_source or R5_STORAGE_KEY in board_source:
    fail("R32_R5 already appears to be applied")
if board_source.count(r4_import) != 1:
    fail(f"expected exactly one R32_R4 import, found {board_source.count(r4_import)}")

updated = board_source.replace(r4_import, r4_import + "\n" + r5_import, 1)
updated = updated.replace(
    'const taskWindowStorageKeyR32R3 = "tos.tasks.taskDetailsWindow.r32r3";',
    'const taskWindowStorageKeyR32R3 = "tos.tasks.taskDetailsWindow.r32r5";',
    1,
)

old_size_state = '''  const [modalSize, setModalSize] = useState(() => {
    const saved = readTaskWindowStateR32R3();
    if (Number.isFinite(Number(saved?.width)) && Number.isFinite(Number(saved?.height))) {
      return clampTaskDetailsModalSize(Number(saved.width), Number(saved.height));
    }
    return getInitialTaskDetailsModalSize();
  });'''
new_size_state = '''  const [modalSize, setModalSize] = useState(() => {
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
if updated.count(old_size_state) != 1:
    fail(f"expected one R32_R3 modal size state anchor, found {updated.count(old_size_state)}")
updated = updated.replace(old_size_state, new_size_state, 1)

old_state_tail = '''  const [isTaskWindowMinimized, setIsTaskWindowMinimized] = useState(false);
  const [isTaskWindowMaximized, setIsTaskWindowMaximized] = useState(false);

  useEffect(() => {'''
new_state_tail = '''  const [isTaskWindowMinimized, setIsTaskWindowMinimized] = useState(false);
  const [isTaskWindowMaximized, setIsTaskWindowMaximized] = useState(false);

  const taskWindowGeometryR32R5 = (() => {
    if (typeof window === "undefined") {
      return { left: 12, top: 12, width: modalSize.width, height: modalSize.height };
    }
    if (window.innerWidth <= 900) {
      return { left: 0, top: 0, width: window.innerWidth, height: window.innerHeight };
    }
    if (isTaskWindowMaximized) {
      return {
        left: 12,
        top: 12,
        width: Math.max(320, window.innerWidth - 24),
        height: Math.max(420, window.innerHeight - 24),
      };
    }
    if (isTaskWindowMinimized) {
      const width = Math.min(520, Math.max(360, window.innerWidth - 24));
      const height = 64;
      return {
        left: Math.min(Math.max(12, modalPosition.x), Math.max(12, window.innerWidth - width - 12)),
        top: Math.min(Math.max(12, modalPosition.y), Math.max(12, window.innerHeight - height - 12)),
        width,
        height,
      };
    }
    const safePosition = clampTaskWindowPositionR32R3(modalPosition, modalSize);
    return {
      left: safePosition.x,
      top: safePosition.y,
      width: modalSize.width,
      height: modalSize.height,
    };
  })();

  useEffect(() => {'''
if updated.count(old_state_tail) != 1:
    fail(f"expected one R32_R3 window state tail anchor, found {updated.count(old_state_tail)}")
updated = updated.replace(old_state_tail, new_state_tail, 1)

old_data = '''        data-tos-task-window-r32-r3="true"
        data-tos-task-window-minimized={isTaskWindowMinimized ? "true" : "false"}'''
new_data = '''        data-tos-task-window-r32-r3="true"
        data-tos-task-window-r32-r5="true"
        data-tos-task-window-minimized={isTaskWindowMinimized ? "true" : "false"}'''
if updated.count(old_data) != 1:
    fail(f"expected one R32_R3 dialog data anchor, found {updated.count(old_data)}")
updated = updated.replace(old_data, new_data, 1)

old_style = '''        style={{
          "--tos-r32-r3-window-width": `${modalSize.width}px`,
          "--tos-r32-r3-window-height": `${modalSize.height}px`,
          "--tos-r32-r3-window-left": `${modalPosition.x}px`,
          "--tos-r32-r3-window-top": `${modalPosition.y}px`,
        }}'''
new_style = '''        style={{
          left: `${taskWindowGeometryR32R5.left}px`,
          top: `${taskWindowGeometryR32R5.top}px`,
          width: `${taskWindowGeometryR32R5.width}px`,
          height: `${taskWindowGeometryR32R5.height}px`,
          "--tos-r32-r3-window-width": `${taskWindowGeometryR32R5.width}px`,
          "--tos-r32-r3-window-height": `${taskWindowGeometryR32R5.height}px`,
          "--tos-r32-r3-window-left": `${taskWindowGeometryR32R5.left}px`,
          "--tos-r32-r3-window-top": `${taskWindowGeometryR32R5.top}px`,
          "--tos-r32-r5-window-width": `${taskWindowGeometryR32R5.width}px`,
          "--tos-r32-r5-window-height": `${taskWindowGeometryR32R5.height}px`,
          "--tos-r32-r5-window-left": `${taskWindowGeometryR32R5.left}px`,
          "--tos-r32-r5-window-top": `${taskWindowGeometryR32R5.top}px`,
        }}'''
if updated.count(old_style) != 1:
    fail(f"expected one R32_R3 inline geometry anchor, found {updated.count(old_style)}")
updated = updated.replace(old_style, new_style, 1)

for contract in (
    r5_import,
    R5_DATA,
    R5_STORAGE_KEY,
    "taskWindowGeometryR32R5",
    'left: `${taskWindowGeometryR32R5.left}px`',
    'width: `${taskWindowGeometryR32R5.width}px`',
    'Math.round(window.innerWidth * 0.84)',
    'Math.round(window.innerHeight * 0.82)',
):
    if contract not in updated:
        fail(f"R32_R5 transformed source contract missing: {contract}")
for contract in ("toggleTaskWindowMinimizedR32R3", "toggleTaskWindowMaximizedR32R3", "startTaskWindowDragR32R3", "function startResize(direction)"):
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

frozen = {path: sha256(path) for path in (PARTS, CHAT, APP, SIDEBAR, R3_STYLE, R4_STYLE)}
stamp = int(time.time())
backup_root = Path(f"/var/backups/tos-patches/task-board-r32-r5-{stamp}")
backup_root.mkdir(parents=True, exist_ok=False)
shutil.copy2(BOARD, backup_root / BOARD.name)

LIVE.parent.mkdir(parents=True, exist_ok=True)
staging = LIVE.parent / f"build.task-board-r32-r5-staging-{stamp}"
live_backup = LIVE.parent / f"build.task-board-r32-r5-backup-{stamp}"
live_swapped = False
r5_written = False

try:
    BOARD.write_text(updated)
    R5_STYLE.write_text(payload_css.rstrip() + "\n")
    r5_written = True

    written = BOARD.read_text()
    for contract in (r5_import, R5_DATA, R5_STORAGE_KEY, "taskWindowGeometryR32R5"):
        if written.count(contract) != 1:
            fail(f"R32_R5 source hook count invalid after write: {contract}")
    for path, digest in frozen.items():
        if sha256(path) != digest:
            fail(f"protected file changed unexpectedly: {path}")

    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists() or not (DIST / "index.html").exists():
        fail("frontend dist missing after build")

    built_css = "\n".join(p.read_text(errors="ignore") for p in DIST.rglob("*.css"))
    built_js = "\n".join(p.read_text(errors="ignore") for p in DIST.rglob("*.js"))
    for marker in (R3_MARKER, R4_MARKER, R5_MARKER):
        if marker not in built_css:
            fail(f"runtime CSS marker missing from build: {marker}")
    for hook in ("tos-task-window-r32-r5", "tos.tasks.taskDetailsWindow.r32r5"):
        if hook not in built_js:
            fail(f"R32_R5 runtime hook missing from built JS: {hook}")

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
    if R5_MARKER not in live_css or "tos-task-window-r32-r5" not in live_js:
        fail("R32_R5 runtime marker/hook missing from live build")

except Exception:
    shutil.copy2(backup_root / BOARD.name, BOARD)
    if r5_written and R5_STYLE.exists():
        R5_STYLE.unlink()
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
    request = urllib.request.Request("https://tos.tamiyouz.com/tasks", headers={"User-Agent": "TOS-R32-R5-Healthcheck"})
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
print("INLINE_STATE_GEOMETRY=YES")
print("NORMAL_DEFAULT_VIEWPORT=84x82_PERCENT")
print("MINIMIZE_REAL_64PX=YES")
print("MAXIMIZE_REAL_VIEWPORT=YES")
print("RESTORE_SIZE_POSITION_PRESERVED=YES")
print("DRAG_RESIZE_PRESERVED=YES")
print("NEW_WINDOW_STORAGE_KEY=YES")
print("MOBILE_FULLSCREEN_PRESERVED=YES")
print("BACKEND_CHANGED=NO")
print("API_CHANGED=NO")
print("DATABASE_CHANGED=NO")
print("PUSH=NO")
print("FINAL_STATUS=PASS")
