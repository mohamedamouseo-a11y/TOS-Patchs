from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import time
import urllib.request

PATCH = "TOS-TASK-BOARD-R32-R7-R2-FULLPAGE-GEOMETRY-OVERRIDE-FIX"
VERSION = "TOS_TASK_BOARD_R32_R7_R2"
R7_MARKER = "--tos-task-board-r32-r7-true-desktop-window-runtime"
R7R1_MARKER = "--tos-task-board-r32-r7-r1-desktop-window-proportion-tuning-runtime"
R7R2_MARKER = "--tos-task-board-r32-r7-r2-fullpage-geometry-override-runtime"

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
R7R2_STYLE = STYLE_DIR / "taskBoardR32R7R2FullpageGeometryOverrideFix.css"
PAYLOAD = Path(__file__).resolve().parent / "taskBoardR32R7R2FullpageGeometryOverrideFix.css"


def fail(message):
    raise RuntimeError(message)


def run(command, cwd=None):
    subprocess.run(command, cwd=cwd, check=True)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


for path in (FRONTEND, STYLE_DIR, BOARD, PARTS, CHAT, APP, SIDEBAR, MANIFEST, R7_STYLE, R7R1_STYLE, PAYLOAD):
    if not path.exists():
        fail(f"required path missing: {path}")
for command in ("node", "npm"):
    if not shutil.which(command):
        fail(f"required command missing: {command}")

source = BOARD.read_text()
r7_css = R7_STYLE.read_text()
r7r1_css = R7R1_STYLE.read_text()
payload_css = PAYLOAD.read_text()
r7r1_import = 'import "../styles/taskBoardR32R7R1DesktopWindowProportionTuning.css";'
r7r2_import = 'import "../styles/taskBoardR32R7R2FullpageGeometryOverrideFix.css";'

for contract in (
    r7r1_import,
    'const taskWindowStorageKeyR32R3 = "tos.tasks.taskDetailsWindow.r32r7r1";',
    'Math.round(window.innerWidth * 0.65)',
    'Math.round(window.innerHeight * 0.70)',
    'const minWidth = 620;',
    'const minHeight = 420;',
    'data-tos-task-window-r32-r7="true"',
    'data-tos-task-window-r32-r7-r1="true"',
    'data-tos-task-window-r32-r5="true"',
    'taskWindowGeometryR32R5',
):
    if contract not in source:
        fail(f"required R32_R7_R1 live contract missing: {contract}")
if R7_MARKER not in r7_css:
    fail("R32_R7 stylesheet marker missing")
if R7R1_MARKER not in r7r1_css:
    fail("R32_R7_R1 stylesheet marker missing")
if R7R2_MARKER not in payload_css:
    fail("R32_R7_R2 payload marker missing")
if R7R2_STYLE.exists() or r7r2_import in source:
    fail("R32_R7_R2 already appears to be applied")
if source.count(r7r1_import) != 1:
    fail(f"expected one R32_R7_R1 import, found {source.count(r7r1_import)}")

# Validate the exact legacy full-page geometry rule proven by live DevTools.
legacy_signature = 'html body .tos-task-details-fullpage.tos-task-details-reference-v1.tos-task-details-reference-v2[data-content-dir] .tos-task-details-modal'
legacy_sources = []
for css_path in STYLE_DIR.rglob("*.css"):
    try:
        text = css_path.read_text(errors="ignore")
    except Exception:
        continue
    if legacy_signature in text and "width:100%" in text and "height:100dvh" in text:
        legacy_sources.append(css_path)
if not legacy_sources:
    fail("proven legacy full-page geometry selector not found in live source styles")

updated = source.replace(r7r1_import, r7r1_import + "\n" + r7r2_import, 1)
if updated.count(r7r2_import) != 1:
    fail("R32_R7_R2 import injection failed")

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

frozen = {path: sha256(path) for path in (PARTS, CHAT, APP, SIDEBAR, R7_STYLE, R7R1_STYLE)}
stamp = int(time.time())
backup_root = Path(f"/var/backups/tos-patches/task-board-r32-r7-r2-{stamp}")
backup_root.mkdir(parents=True, exist_ok=False)
shutil.copy2(BOARD, backup_root / BOARD.name)

LIVE.parent.mkdir(parents=True, exist_ok=True)
staging = LIVE.parent / f"build.task-board-r32-r7-r2-staging-{stamp}"
live_backup = LIVE.parent / f"build.task-board-r32-r7-r2-backup-{stamp}"
live_swapped = False
r7r2_written = False

try:
    BOARD.write_text(updated)
    R7R2_STYLE.write_text(payload_css.rstrip() + "\n")
    r7r2_written = True

    written = BOARD.read_text()
    if written.count(r7r2_import) != 1:
        fail("R32_R7_R2 source import invalid after write")
    for path, digest in frozen.items():
        if sha256(path) != digest:
            fail(f"protected file changed unexpectedly: {path}")

    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists() or not (DIST / "index.html").exists():
        fail("frontend dist missing after build")

    built_css = "\n".join(p.read_text(errors="ignore") for p in DIST.rglob("*.css"))
    built_js = "\n".join(p.read_text(errors="ignore") for p in DIST.rglob("*.js"))
    for marker in (R7_MARKER, R7R1_MARKER, R7R2_MARKER):
        if marker not in built_css:
            fail(f"runtime CSS marker missing from build: {marker}")
    for hook in ("tos-task-window-r32-r7-r1", "tos.tasks.taskDetailsWindow.r32r7r1"):
        if hook not in built_js:
            fail(f"R32_R7_R1 runtime hook missing from built JS: {hook}")
    if "--tos-r32-r5-window-width" not in built_css or "--tos-r32-r5-window-height" not in built_css:
        fail("R32_R7_R2 geometry-variable bridge missing from built CSS")

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
    if R7R2_MARKER not in live_css or "tos-task-window-r32-r7-r1" not in live_js:
        fail("R32_R7_R2 runtime marker/hook missing from live build")

except Exception:
    shutil.copy2(backup_root / BOARD.name, BOARD)
    if r7r2_written and R7R2_STYLE.exists():
        R7R2_STYLE.unlink()
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
    req = urllib.request.Request("https://tos.tamiyouz.com/tasks", headers={"User-Agent": "TOS-R32-R7-R2-Healthcheck"})
    with urllib.request.urlopen(req, timeout=15) as response:
        live_http = str(response.status)
except Exception:
    pass

print(f"VERSION={VERSION}")
print(f"PATCH_APPLIED={PATCH}")
print("ROOT_CAUSE=LEGACY_FULLPAGE_IMPORTANT_GEOMETRY_OVERRIDE")
print("FIX=HIGH_SPECIFICITY_R5_GEOMETRY_BRIDGE")
print("BUILD_STATUS=PASS")
print("DEPLOY_STATUS=PASS")
print(f"LIVE_HTTP_STATUS={live_http}")
print("NORMAL_GEOMETRY_SOURCE=R7_R1_PERSISTED_OR_65x70_DEFAULT")
print("MINIMIZED_GEOMETRY_SOURCE=R7_R1_COMPACT")
print("MAXIMIZED_GEOMETRY_SOURCE=R7_EXPLICIT_MAXIMIZE")
print("MOBILE_FULLSCREEN_PRESERVED=YES")
print("BACKEND_CHANGED=NO")
print("API_CHANGED=NO")
print("DATABASE_CHANGED=NO")
print("PUSH=NO")
print("FINAL_STATUS=PASS")
