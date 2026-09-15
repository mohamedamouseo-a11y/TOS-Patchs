from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import time

VERSION = "TOS_TASK_DETAILS_V2_12_PHASE1_R5_SIDEBAR_STAYS_RIGHT"
PATCH_NAME = "TOS-UXUI-TASK-DETAILS-V2-12-PHASE1-R5-SIDEBAR-STAYS-RIGHT-WHILE-TASK-OPEN"
R4_MARKER = "--tos-task-details-v2-12-phase1-r4-shell-rtl-physical-overlay-lock-runtime"
R5_MARKER = "--tos-task-details-v2-12-phase1-r5-sidebar-stays-right-runtime"

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
BOARD = FRONTEND / "src/components/ProfessionalTaskBoard.jsx"
APP = FRONTEND / "src/App.jsx"
SIDEBAR = FRONTEND / "src/components/layout/Sidebar.jsx"
R4_STYLE = FRONTEND / "src/styles/taskDetailsV2_12_Phase1R4ShellRtlPhysicalOverlayLock.css"
R5_STYLE = FRONTEND / "src/styles/taskDetailsV2_12_Phase1R5SidebarStaysRight.css"
MANIFEST = ROOT / "deployment/tos-production-runtime.json"
PATCH_DIR = Path(__file__).resolve().parent
PAYLOAD = PATCH_DIR / "taskDetailsV2_12_Phase1R5SidebarStaysRight.css"


def fail(message):
    raise RuntimeError(message)


def run(command, cwd=None):
    subprocess.run(command, cwd=cwd, check=True)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


for path in (FRONTEND, BOARD, APP, SIDEBAR, R4_STYLE, MANIFEST, PAYLOAD):
    if not path.exists():
        fail(f"required path missing: {path}")
for command in ("node", "npm"):
    if not shutil.which(command):
        fail(f"required command not found: {command}")

board_source = BOARD.read_text()
app_source = APP.read_text()
sidebar_source = SIDEBAR.read_text()
r4_source = R4_STYLE.read_text()
payload_css = PAYLOAD.read_text()

if R4_MARKER not in r4_source:
    fail("required R4 baseline marker missing")
if R5_STYLE.exists() or R5_MARKER in board_source or R5_MARKER in app_source:
    fail("Phase 1 R5 already appears to be applied")
if R5_MARKER not in payload_css:
    fail("R5 payload runtime marker missing")

r4_import = 'import "../styles/taskDetailsV2_12_Phase1R4ShellRtlPhysicalOverlayLock.css";'
r5_import = 'import "../styles/taskDetailsV2_12_Phase1R5SidebarStaysRight.css";'
if r4_import not in board_source:
    fail("R4 stylesheet import anchor missing")
if r5_import in board_source:
    fail("R5 stylesheet import already exists")

# Confirm the production shell contracts R5 is intended to lock without editing them.
for contract in (
    '<div dir={isAr ? "rtl" : "ltr"} className="tos-premium-system-v14',
    'className="tos-premium-app-frame relative flex h-full w-full max-w-none gap-2 overflow-hidden lg:gap-3"',
    '<Sidebar active={active} setActive={handleSidebarPageChange}',
    'className="tos-premium-main-shell min-w-0 flex-1 overflow-hidden',
):
    if contract not in app_source:
        fail(f"App shell contract missing: {contract}")
if 'className={cn(\n        "tos-premium-sidebar' not in sidebar_source:
    fail("Sidebar shell contract missing")

for contract in (
    'direction:rtl!important',
    'flex-direction:row!important',
    '> .tos-premium-sidebar',
    '> .tos-premium-main-shell',
    'order:0!important',
    'order:1!important',
):
    if contract not in payload_css:
        fail(f"R5 CSS contract missing: {contract}")

updated_board = board_source.replace(r4_import, r4_import + "\n" + r5_import, 1)
if r5_import not in updated_board:
    fail("failed to add R5 stylesheet import")

app_hash = sha256(APP)
sidebar_hash = sha256(SIDEBAR)
r4_hash = sha256(R4_STYLE)

manifest = json.loads(MANIFEST.read_text())
if manifest.get("application") != "TOS" or manifest.get("environment") != "production":
    fail("unexpected production runtime manifest")
if manifest.get("sourceRoot") != str(ROOT):
    fail("runtime sourceRoot does not match target")
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

stamp = int(time.time())
backup_root = Path(f"/var/backups/tos-patches/task-details-v2-12-phase1-r5-{stamp}")
backup_root.mkdir(parents=True, exist_ok=False)
board_backup = backup_root / BOARD.name
shutil.copy2(BOARD, board_backup)

LIVE.parent.mkdir(parents=True, exist_ok=True)
staging = LIVE.parent / f"build.task-details-v2-12-phase1-r5-staging-{stamp}"
live_backup = LIVE.parent / f"build.task-details-v2-12-phase1-r5-backup-{stamp}"
live_swapped = False
r5_written = False

try:
    BOARD.write_text(updated_board)
    R5_STYLE.write_text(payload_css.rstrip() + "\n")
    r5_written = True

    if sha256(APP) != app_hash:
        fail("App.jsx changed unexpectedly")
    if sha256(SIDEBAR) != sidebar_hash:
        fail("Sidebar.jsx changed unexpectedly")
    if sha256(R4_STYLE) != r4_hash:
        fail("R4 stylesheet changed unexpectedly")

    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists() or not (DIST / "index.html").exists():
        fail("frontend dist missing after build")

    built_css = "\n".join(p.read_text(errors="ignore") for p in DIST.rglob("*.css"))
    for marker in (R5_MARKER, R4_MARKER):
        if marker not in built_css:
            fail(f"required runtime marker missing from built CSS: {marker}")

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
    for marker in (R5_MARKER, R4_MARKER):
        if marker not in live_css:
            fail(f"required runtime marker missing from live CSS: {marker}")

    if sha256(APP) != app_hash:
        fail("App.jsx changed after deploy")
    if sha256(SIDEBAR) != sidebar_hash:
        fail("Sidebar.jsx changed after deploy")
    if sha256(R4_STYLE) != r4_hash:
        fail("R4 stylesheet changed after deploy")

except Exception:
    shutil.copy2(board_backup, BOARD)
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

print(f"VERSION={VERSION}")
print(f"PATCH={PATCH_NAME}")
print("PASS/FAIL=PASS")
print("BUILD_RESULT=PASS")
print("LIVE_DEPLOY=PASS")
print("SIDEBAR_RTL_SHELL_LOCK=YES")
print("SIDEBAR_ORDER=0")
print("MAIN_SHELL_ORDER=1")
print("APP_JS_CHANGED=NO")
print("SIDEBAR_JS_CHANGED=NO")
print("R4_PRESERVED=YES")
print("BACKEND_CHANGED=NO")
print("DATABASE_CHANGED=NO")
print("TCS_CHANGED=NO")
print("RAMZY_CHANGED=NO")
print("NO_BROWSER_QA=YES")
print("NO_SCREENSHOTS=YES")
print("PUSH=NO")
print(f"BACKUP={backup_root}")
print("STATUS=DEPLOYED__MANUAL_VISUAL_QA_REQUIRED")
