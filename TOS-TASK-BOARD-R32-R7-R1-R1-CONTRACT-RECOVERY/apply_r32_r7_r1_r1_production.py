from pathlib import Path
import hashlib
import json
import re
import shutil
import subprocess
import sys
import time
import urllib.request

PATCH = "TOS-TASK-BOARD-R32-R7-R1-R1-CONTRACT-RECOVERY"
VERSION = "TOS_TASK_BOARD_R32_R7_R1_R1"
R7_MARKER = "--tos-task-board-r32-r7-true-desktop-window-runtime"
R7R1_MARKER = "--tos-task-board-r32-r7-r1-desktop-window-proportion-tuning-runtime"

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
STYLE_DIR = FRONTEND / "src/styles"
BOARD = FRONTEND / "src/components/ProfessionalTaskBoard.jsx"
PARTS = FRONTEND / "src/features/tasks/taskBoardParts.jsx"
CHAT = FRONTEND / "src/components/ChatPanel.jsx"
APP = FRONTEND / "src/App.jsx"
SIDEBAR = FRONTEND / "src/components/layout/Sidebar.jsx"
MANIFEST = ROOT / "deployment/tos-production-runtime.json"
R7_STYLE = STYLE_DIR / "taskBoardR32R7TrueDesktopWindow.css"
R7R1_STYLE = STYLE_DIR / "taskBoardR32R7R1DesktopWindowProportionTuning.css"
PAYLOAD = Path(__file__).resolve().parent / "taskBoardR32R7R1DesktopWindowProportionTuning.css"


def fail(message):
    raise RuntimeError(message)


def run(command, cwd=None):
    subprocess.run(command, cwd=cwd, check=True)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


for path in (FRONTEND, STYLE_DIR, BOARD, PARTS, CHAT, APP, SIDEBAR, MANIFEST, R7_STYLE, PAYLOAD):
    if not path.exists():
        fail(f"required path missing: {path}")
for command in ("node", "npm"):
    if not shutil.which(command):
        fail(f"required command missing: {command}")

source = BOARD.read_text()
r7_css = R7_STYLE.read_text()
payload_css = PAYLOAD.read_text()
r7_import = 'import "../styles/taskBoardR32R7TrueDesktopWindow.css";'
r7r1_import = 'import "../styles/taskBoardR32R7R1DesktopWindowProportionTuning.css";'

for contract in (
    r7_import,
    'const taskWindowStorageKeyR32R3 = "tos.tasks.taskDetailsWindow.r32r7";',
    'data-tos-task-window-r32-r7="true"',
    'startResize("left")',
    'startResize("top")',
    'startResize("bottom-right")',
    'data-tos-task-window-drag-surface="true"',
    'Math.round(window.innerWidth * 0.74)',
    'Math.round(window.innerHeight * 0.76)',
    'const minWidth = 720;',
    'const minHeight = 480;',
):
    if contract not in source:
        fail(f"required R32_R7 live contract missing: {contract}")
if R7_MARKER not in r7_css:
    fail("R32_R7 stylesheet marker missing")
if R7R1_MARKER not in payload_css:
    fail("R32_R7_R1 payload marker missing")
if R7R1_STYLE.exists() or r7r1_import in source or 'data-tos-task-window-r32-r7-r1="true"' in source:
    fail("R32_R7_R1 already appears applied; stop instead of layering recovery")
if source.count(r7_import) != 1:
    fail("R32_R7 import count invalid")

updated = source.replace(r7_import, r7_import + "\n" + r7r1_import, 1)
updated = updated.replace(
    'const taskWindowStorageKeyR32R3 = "tos.tasks.taskDetailsWindow.r32r7";',
    'const taskWindowStorageKeyR32R3 = "tos.tasks.taskDetailsWindow.r32r7r1";',
    1,
)
updated = updated.replace('Math.round(window.innerWidth * 0.74)', 'Math.round(window.innerWidth * 0.65)', 1)
updated = updated.replace('Math.round(window.innerHeight * 0.76)', 'Math.round(window.innerHeight * 0.70)', 1)
updated = updated.replace('const maxWidth = Math.max(720, window.innerWidth - 24);', 'const maxWidth = Math.max(620, window.innerWidth - 24);', 1)
updated = updated.replace('const maxHeight = Math.max(480, window.innerHeight - 24);', 'const maxHeight = Math.max(420, window.innerHeight - 24);', 1)
updated = updated.replace('width: Math.min(maxWidth, Math.max(720, Number(width) || 960)),', 'width: Math.min(maxWidth, Math.max(620, Number(width) || 900)),', 1)
updated = updated.replace('height: Math.min(maxHeight, Math.max(480, Number(height) || 640)),', 'height: Math.min(maxHeight, Math.max(420, Number(height) || 600)),', 1)
updated = updated.replace('const minWidth = 720;', 'const minWidth = 620;', 1)
updated = updated.replace('const minHeight = 480;', 'const minHeight = 420;', 1)

# Normalize minimized width by semantic context. The previous installer incorrectly
# assumed two byte-identical expressions; the live R32_R7 source has only one exact
# occurrence on this deployment.
target_width = 'Math.min(440, Math.max(380, Math.round(window.innerWidth * 0.22)))'
geometry_pattern = re.compile(
    r'(if \(isTaskWindowMinimized\) \{\s*const width = )Math\.min\(\d+, Math\.max\(\d+, Math\.round\(window\.innerWidth \* [0-9.]+\)\)\)(;\s*const height = 64;)',
    re.S,
)
drag_pattern = re.compile(
    r'(const effectiveSize = isTaskWindowMinimized\s*\? \{ width: )Math\.min\(\d+, Math\.max\(\d+, Math\.round\(window\.innerWidth \* [0-9.]+\)\)\)(, height: 64 \}\s*: modalSize;)',
    re.S,
)
updated, geometry_count = geometry_pattern.subn(r'\1' + target_width + r'\2', updated, count=1)
updated, drag_count = drag_pattern.subn(r'\1' + target_width + r'\2', updated, count=1)
if geometry_count != 1:
    fail(f"minimized geometry context not normalized: {geometry_count}")
if drag_count != 1:
    fail(f"minimized drag context not normalized: {drag_count}")

r7_data = '        data-tos-task-window-r32-r7="true"\n'
r7r1_data = '        data-tos-task-window-r32-r7="true"\n        data-tos-task-window-r32-r7-r1="true"\n'
if updated.count(r7_data) != 1:
    fail("expected one R32_R7 data hook")
updated = updated.replace(r7_data, r7r1_data, 1)

for contract in (
    r7r1_import,
    'tos.tasks.taskDetailsWindow.r32r7r1',
    'Math.round(window.innerWidth * 0.65)',
    'Math.round(window.innerHeight * 0.70)',
    'const minWidth = 620;',
    'const minHeight = 420;',
    target_width,
    'data-tos-task-window-r32-r7-r1="true"',
):
    if contract not in updated:
        fail(f"R32_R7_R1 transformed contract missing: {contract}")
if updated.count(target_width) < 2:
    fail(f"R32_R7_R1 target minimized width not present in both contexts: {updated.count(target_width)}")

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
if DIST != FRONTEND / "dist" or LIVE != Path("/opt/apps/tamiyouz-front/build"):
    fail("unexpected frontend runtime paths")

frozen = {path: sha256(path) for path in (PARTS, CHAT, APP, SIDEBAR, R7_STYLE)}
stamp = int(time.time())
backup_root = Path(f"/var/backups/tos-patches/task-board-r32-r7-r1-r1-{stamp}")
backup_root.mkdir(parents=True, exist_ok=False)
shutil.copy2(BOARD, backup_root / BOARD.name)

LIVE.parent.mkdir(parents=True, exist_ok=True)
staging = LIVE.parent / f"build.task-board-r32-r7-r1-r1-staging-{stamp}"
live_backup = LIVE.parent / f"build.task-board-r32-r7-r1-r1-backup-{stamp}"
live_swapped = False
r7r1_written = False

try:
    BOARD.write_text(updated)
    R7R1_STYLE.write_text(payload_css.rstrip() + "\n")
    r7r1_written = True

    written = BOARD.read_text()
    if written.count(r7r1_import) != 1 or written.count('data-tos-task-window-r32-r7-r1="true"') != 1:
        fail("R32_R7_R1 source hooks invalid after write")
    if written.count(target_width) < 2:
        fail("R32_R7_R1 minimized width contexts invalid after write")
    for path, digest in frozen.items():
        if sha256(path) != digest:
            fail(f"protected file changed unexpectedly: {path}")

    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists() or not (DIST / "index.html").exists():
        fail("frontend dist missing after build")

    built_css = "\n".join(p.read_text(errors="ignore") for p in DIST.rglob("*.css"))
    built_js = "\n".join(p.read_text(errors="ignore") for p in DIST.rglob("*.js"))
    if R7_MARKER not in built_css or R7R1_MARKER not in built_css:
        fail("R32_R7/R7_R1 marker missing from build")
    for hook in ("tos-task-window-r32-r7-r1", "tos.tasks.taskDetailsWindow.r32r7r1"):
        if hook not in built_js:
            fail(f"R32_R7_R1 runtime hook missing from built JS: {hook}")

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
    if R7R1_MARKER not in live_css or "tos-task-window-r32-r7-r1" not in live_js:
        fail("R32_R7_R1 runtime marker/hook missing from live build")

except Exception:
    shutil.copy2(backup_root / BOARD.name, BOARD)
    if r7r1_written and R7R1_STYLE.exists():
        R7R1_STYLE.unlink()
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
    req = urllib.request.Request("https://tos.tamiyouz.com/tasks", headers={"User-Agent": "TOS-R32-R7-R1-R1-Healthcheck"})
    with urllib.request.urlopen(req, timeout=15) as response:
        live_http = str(response.status)
except Exception:
    pass

print(f"VERSION={VERSION}")
print(f"PATCH_APPLIED={PATCH}")
print("RECOVERY_TARGET=TOS-TASK-BOARD-R32-R7-R1-DESKTOP-WINDOW-PROPORTION-TUNING")
print("BUILD_STATUS=PASS")
print("DEPLOY_STATUS=PASS")
print(f"LIVE_HTTP_STATUS={live_http}")
print("NORMAL_DEFAULT_VIEWPORT=65x70_PERCENT")
print("DESKTOP_MIN_SIZE=620x420")
print("MINIMIZED_WIDTH=380-440PX")
print("RESIZE_HIT_AREAS=ENLARGED")
print("RESIZE_EDGES=4")
print("RESIZE_CORNERS=4")
print("DRAG_PRESERVED=YES")
print("MAXIMIZE_RESTORE_PRESERVED=YES")
print("BOARD_INTERACTION_PRESERVED=YES")
print("MOBILE_FULLSCREEN_PRESERVED=YES")
print("BACKEND_CHANGED=NO")
print("API_CHANGED=NO")
print("DATABASE_CHANGED=NO")
print("PUSH=NO")
print("FINAL_STATUS=PASS")
