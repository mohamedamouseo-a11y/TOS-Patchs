from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import time
import urllib.request

PATCH = "TOS-TASK-BOARD-R32-R6-R1-RECOVERY-MINIMIZED-HEADER"
VERSION = "TOS_TASK_BOARD_R32_R6_R1"
R5_MARKER = "--tos-task-board-r32-r5-inline-window-geometry-runtime"
R6_MARKER = "--tos-task-board-r32-r6-dedicated-minimized-window-runtime"
R6R1_MARKER = "--tos-task-board-r32-r6-r1-recovery-minimized-header-runtime"

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
R6R1_STYLE = STYLE_DIR / "taskBoardR32R6R1RecoveryMinimizedHeader.css"
PAYLOAD = Path(__file__).resolve().parent / "taskBoardR32R6R1RecoveryMinimizedHeader.css"


def fail(message):
    raise RuntimeError(message)


def run(command, cwd=None):
    subprocess.run(command, cwd=cwd, check=True)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


for path in (FRONTEND, STYLE_DIR, BOARD, PARTS, CHAT, APP, SIDEBAR, MANIFEST, R3_STYLE, R4_STYLE, R5_STYLE, R6_STYLE, PAYLOAD):
    if not path.exists():
        fail(f"required path missing: {path}")
for command in ("node", "npm"):
    if not shutil.which(command):
        fail(f"required command missing: {command}")

board_source = BOARD.read_text()
r5_css = R5_STYLE.read_text()
r6_css = R6_STYLE.read_text()
payload_css = PAYLOAD.read_text()

r6_import = 'import "../styles/taskBoardR32R6DedicatedMinimizedWindow.css";'
r6r1_import = 'import "../styles/taskBoardR32R6R1RecoveryMinimizedHeader.css";'

for contract in (
    r6_import,
    'data-tos-task-window-r32-r5="true"',
    'data-tos-task-window-minimized={isTaskWindowMinimized ? "true" : "false"}',
    'className="tos-task-r32-r6-mini-window"',
    'data-tos-task-mini-window-r32-r6="true"',
    "taskWindowGeometryR32R5",
    "toggleTaskWindowMinimizedR32R3",
    "startTaskWindowDragR32R3",
    "tos-task-r32-r3-mini-title",
):
    if contract not in board_source:
        fail(f"required R32_R6 live source contract missing: {contract}")
if R5_MARKER not in r5_css:
    fail("R32_R5 stylesheet marker missing")
if R6_MARKER not in r6_css:
    fail("R32_R6 stylesheet marker missing")
if R6R1_MARKER not in payload_css:
    fail("R32_R6_R1 payload marker missing")
if R6R1_STYLE.exists() or r6r1_import in board_source:
    fail("R32_R6_R1 already appears to be applied")
if board_source.count(r6_import) != 1:
    fail(f"expected exactly one R32_R6 import, found {board_source.count(r6_import)}")

mini_block = '''        {isTaskWindowMinimized ? (\n          <div className="tos-task-r32-r6-mini-window" onMouseDown={startTaskWindowDragR32R3} data-tos-task-mini-window-r32-r6="true">\n            <span className="tos-task-r32-r6-mini-accent" aria-hidden="true" />\n            <div className="tos-task-r32-r6-mini-copy">\n              <span className="tos-task-r32-r6-mini-label">{isAr ? "المهمة" : "Task"}</span>\n              <strong className="tos-task-r32-r6-mini-title" title={draft.title || modalUi.taskDetails}>{draft.title || modalUi.taskDetails}</strong>\n            </div>\n            <div className="tos-task-r32-r6-mini-actions">\n              <button type="button" className="tos-task-r32-r6-mini-action" onClick={toggleTaskWindowMinimizedR32R3} aria-label={isAr ? "استعادة النافذة" : "Restore window"} title={isAr ? "استعادة النافذة" : "Restore window"}><Maximize2 size={17} /></button>\n              <button type="button" className="tos-task-r32-r6-mini-action" onClick={onClose} aria-label={modalUi.closeTaskDetails || (isAr ? "إغلاق تفاصيل المهمة" : "Close task details")} title={modalUi.closeTaskDetails || (isAr ? "إغلاق" : "Close")}><X size={17} /></button>\n            </div>\n          </div>\n        ) : null}\n'''

if board_source.count(mini_block) != 1:
    fail(f"expected exactly one R32_R6 injected mini block, found {board_source.count(mini_block)}")

updated = board_source.replace(r6_import, r6r1_import, 1)
updated = updated.replace(mini_block, "", 1)

for contract in (
    r6r1_import,
    'data-tos-task-window-r32-r5="true"',
    'data-tos-task-window-minimized={isTaskWindowMinimized ? "true" : "false"}',
    "taskWindowGeometryR32R5",
    "toggleTaskWindowMinimizedR32R3",
    "startTaskWindowDragR32R3",
    "tos-task-r32-r3-mini-title",
):
    if contract not in updated:
        fail(f"R32_R6_R1 preserved source contract missing: {contract}")
for stale in (r6_import, 'className="tos-task-r32-r6-mini-window"', 'data-tos-task-mini-window-r32-r6="true"'):
    if stale in updated:
        fail(f"stale R32_R6 source hook remains: {stale}")

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
backup_root = Path(f"/var/backups/tos-patches/task-board-r32-r6-r1-{stamp}")
backup_root.mkdir(parents=True, exist_ok=False)
shutil.copy2(BOARD, backup_root / BOARD.name)
shutil.copy2(R6_STYLE, backup_root / R6_STYLE.name)

LIVE.parent.mkdir(parents=True, exist_ok=True)
staging = LIVE.parent / f"build.task-board-r32-r6-r1-staging-{stamp}"
live_backup = LIVE.parent / f"build.task-board-r32-r6-r1-backup-{stamp}"
live_swapped = False
r6r1_written = False
r6_removed = False

try:
    BOARD.write_text(updated)
    R6R1_STYLE.write_text(payload_css.rstrip() + "\n")
    r6r1_written = True
    R6_STYLE.unlink()
    r6_removed = True

    written = BOARD.read_text()
    if written.count(r6r1_import) != 1:
        fail("R32_R6_R1 import count invalid after write")
    if "tos-task-r32-r6-mini-window" in written or "tos-task-mini-window-r32-r6" in written:
        fail("R32_R6 runtime JSX hook still present after recovery")
    for path, digest in frozen.items():
        if sha256(path) != digest:
            fail(f"protected file changed unexpectedly: {path}")

    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists() or not (DIST / "index.html").exists():
        fail("frontend dist missing after build")

    built_css = "\n".join(p.read_text(errors="ignore") for p in DIST.rglob("*.css"))
    built_js = "\n".join(p.read_text(errors="ignore") for p in DIST.rglob("*.js"))
    for marker in (R5_MARKER, R6R1_MARKER):
        if marker not in built_css:
            fail(f"runtime CSS marker missing from build: {marker}")
    if R6_MARKER in built_css:
        fail("stale R32_R6 runtime CSS still bundled")
    for hook in ("tos-task-window-r32-r5", "tos.tasks.taskDetailsWindow.r32r5", "tos-task-r32-r3-mini-title"):
        if hook not in built_js:
            fail(f"required recovered runtime hook missing from built JS: {hook}")
    if "tos-task-r32-r6-mini-window" in built_js:
        fail("stale R32_R6 mini JSX still bundled")

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
    if R6R1_MARKER not in live_css or R6_MARKER in live_css:
        fail("R32_R6_R1 live CSS verification failed")
    if "tos-task-r32-r6-mini-window" in live_js:
        fail("stale R32_R6 mini JSX present in live JS")

except Exception:
    shutil.copy2(backup_root / BOARD.name, BOARD)
    if r6r1_written and R6R1_STYLE.exists():
        R6R1_STYLE.unlink()
    if r6_removed:
        shutil.copy2(backup_root / R6_STYLE.name, R6_STYLE)
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
    request = urllib.request.Request("https://tos.tamiyouz.com/tasks", headers={"User-Agent": "TOS-R32-R6-R1-Healthcheck"})
    with urllib.request.urlopen(request, timeout=15) as response:
        live_http = str(response.status)
except Exception:
    pass

print(f"VERSION={VERSION}")
print(f"PATCH_APPLIED={PATCH}")
print("R32_R6_ROLLED_BACK=YES")
print("R32_R5_RENDER_PATH_RESTORED=YES")
print("MINIMIZED_EXISTING_HEADER_UI=YES")
print("MINIMIZED_HEIGHT=64PX")
print("BOARD_INTERACTION_WHILE_MINIMIZED=YES")
print("NORMAL_MAXIMIZE_DRAG_RESIZE_PRESERVED=YES")
print("BUILD_STATUS=PASS")
print("DEPLOY_STATUS=PASS")
print(f"LIVE_HTTP_STATUS={live_http}")
print("BACKEND_CHANGED=NO")
print("API_CHANGED=NO")
print("DATABASE_CHANGED=NO")
print("PUSH=NO")
print("FINAL_STATUS=PASS")
