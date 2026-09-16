from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import time

PATCH = "TOS-TASK-BOARD-R32-R1-MODAL-VISIBILITY-RECOVERY"
VERSION = "TOS_TASK_BOARD_R32_R1"
BASE_TOS_COMMIT = "f3671756ba1c49ae7304509276d52eb5cb69d04d"
R32_MARKER = "--tos-task-board-r32-trello-card-modal-runtime"
R32_CLASS = "tos-task-details-trello-overlay-r32"
R32_NAV = "tos-task-v2-card-nav-r32"
R1_MARKER = "--tos-task-board-r32-r1-modal-visibility-runtime"

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
PAYLOAD = Path(__file__).resolve().parent / "taskBoardR32R1ModalVisibilityRecovery.css"


def fail(message):
    raise RuntimeError(message)


def run(command, cwd=None):
    subprocess.run(command, cwd=cwd, check=True)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


for path in (FRONTEND, STYLE_DIR, BOARD, PARTS, CHAT, APP, SIDEBAR, MANIFEST, R32_STYLE, PAYLOAD):
    if not path.exists():
        fail(f"required path missing: {path}")
for command in ("node", "npm"):
    if not shutil.which(command):
        fail(f"required command missing: {command}")

board_source = BOARD.read_text()
r32_css = R32_STYLE.read_text()
payload_css = PAYLOAD.read_text()

r32_import = 'import "../styles/taskBoardR32TrelloModalNavigation.css";'
r1_import = 'import "../styles/taskBoardR32R1ModalVisibilityRecovery.css";'

for contract in (r32_import, R32_CLASS, R32_NAV, "TOS_TASK_BOARD_R32_TRELLO_MODAL_NAVIGATION"):
    if contract not in board_source:
        fail(f"R32 live source contract missing: {contract}")
if R32_MARKER not in r32_css:
    fail("R32 stylesheet marker missing")
if R1_MARKER not in payload_css:
    fail("R32_R1 payload marker missing")
if R1_STYLE.exists() or r1_import in board_source:
    fail("R32_R1 already appears to be applied")

old_motion = '''        initial={{ opacity: 0, y: 18, scale: 0.985 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.18, ease: [0.22, 1, 0.36, 1] }}
        className="tos-task-details-modal flex h-[100dvh] w-full flex-col overflow-hidden bg-transparent"'''
new_motion = '''        className="tos-task-details-modal flex h-[100dvh] w-full flex-col overflow-hidden bg-transparent"'''
if board_source.count(old_motion) != 1:
    fail(f"expected exactly one R32 dialog motion anchor, found {board_source.count(old_motion)}")
if board_source.count(r32_import) != 1:
    fail(f"expected exactly one R32 import, found {board_source.count(r32_import)}")

updated = board_source.replace(r32_import, r32_import + "\n" + r1_import, 1)
updated = updated.replace(old_motion, new_motion, 1)

if updated.count(r1_import) != 1:
    fail("R32_R1 import verification failed")
if old_motion in updated:
    fail("conflicting R32 Framer entrance state still present")
for contract in (R32_CLASS, R32_NAV, "prefetchTaskDetails", "syncTaskModalUrl", "closeTaskDetails"):
    if board_source.count(contract) != updated.count(contract):
        fail(f"R32 behavior contract changed unexpectedly: {contract}")
for contract in (R1_MARKER, "opacity:1!important", "visibility:visible!important", "transform:none!important", "@keyframes tos-task-r32-r1-dialog-in"):
    if contract not in payload_css:
        fail(f"R32_R1 CSS contract missing: {contract}")

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

frozen = {path: sha256(path) for path in (PARTS, CHAT, APP, SIDEBAR, R32_STYLE)}
stamp = int(time.time())
backup_root = Path(f"/var/backups/tos-patches/task-board-r32-r1-{stamp}")
backup_root.mkdir(parents=True, exist_ok=False)
shutil.copy2(BOARD, backup_root / BOARD.name)

LIVE.parent.mkdir(parents=True, exist_ok=True)
staging = LIVE.parent / f"build.task-board-r32-r1-staging-{stamp}"
live_backup = LIVE.parent / f"build.task-board-r32-r1-backup-{stamp}"
live_swapped = False
r1_written = False

try:
    BOARD.write_text(updated)
    R1_STYLE.write_text(payload_css.rstrip() + "\n")
    r1_written = True

    written = BOARD.read_text()
    if written.count(r1_import) != 1 or old_motion in written:
        fail("R32_R1 source transformation failed after write")
    for path, digest in frozen.items():
        if sha256(path) != digest:
            fail(f"protected file changed unexpectedly: {path}")

    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists() or not (DIST / "index.html").exists():
        fail("frontend dist missing after build")

    built_css = "\n".join(p.read_text(errors="ignore") for p in DIST.rglob("*.css"))
    built_js = "\n".join(p.read_text(errors="ignore") for p in DIST.rglob("*.js"))
    if R32_MARKER not in built_css or R1_MARKER not in built_css:
        fail("R32/R32_R1 runtime CSS marker missing from build")
    if R32_CLASS not in built_js or R32_NAV not in built_js:
        fail("R32 modal/navigation hook missing from build")

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
    if R32_MARKER not in live_css or R1_MARKER not in live_css:
        fail("R32/R32_R1 runtime CSS marker missing from live build")
    if R32_CLASS not in live_js:
        fail("R32 modal hook missing from live JS")

except Exception:
    shutil.copy2(backup_root / BOARD.name, BOARD)
    if r1_written and R1_STYLE.exists():
        R1_STYLE.unlink()
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
print("R32_PRESERVED=YES")
print("MODAL_VISIBILITY_RECOVERY=YES")
print("FRAMER_ENTRANCE_CONFLICT_REMOVED=YES")
print("BOARD_CONTEXT_PRESERVED=YES")
print("PREFETCH_PRESERVED=YES")
print("URL_BACK_NAV_PRESERVED=YES")
print("PREV_NEXT_PRESERVED=YES")
print("BACKEND_CHANGED=NO")
print("API_CHANGED=NO")
print("DATABASE_CHANGED=NO")
print("PUSH=NO")
print("FINAL_STATUS=PASS")
