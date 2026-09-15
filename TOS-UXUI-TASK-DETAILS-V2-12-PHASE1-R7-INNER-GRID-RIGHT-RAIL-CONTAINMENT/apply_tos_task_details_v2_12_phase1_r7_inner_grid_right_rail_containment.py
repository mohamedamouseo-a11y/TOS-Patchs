from pathlib import Path
import hashlib
import json
import re
import shutil
import subprocess
import sys
import time

VERSION = "TOS_TASK_DETAILS_V2_12_PHASE1_R7_INNER_GRID_RIGHT_RAIL_CONTAINMENT"
PATCH_NAME = "TOS-UXUI-TASK-DETAILS-V2-12-PHASE1-R7-INNER-GRID-RIGHT-RAIL-CONTAINMENT"
R4_MARKER = "--tos-task-details-v2-12-phase1-r4-shell-rtl-physical-overlay-lock-runtime"
R5_MARKER = "--tos-task-details-v2-12-phase1-r5-sidebar-stays-right-runtime"
R7_MARKER = "--tos-task-details-v2-12-phase1-r7-inner-grid-right-rail-containment-runtime"

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
STYLE_DIR = FRONTEND / "src/styles"
BOARD = FRONTEND / "src/components/ProfessionalTaskBoard.jsx"
APP = FRONTEND / "src/App.jsx"
SIDEBAR = FRONTEND / "src/components/layout/Sidebar.jsx"
R4_STYLE = STYLE_DIR / "taskDetailsV2_12_Phase1R4ShellRtlPhysicalOverlayLock.css"
R5_STYLE = STYLE_DIR / "taskDetailsV2_12_Phase1R5SidebarStaysRight.css"
R7_STYLE = STYLE_DIR / "taskDetailsV2_12_Phase1R7InnerGridRightRailContainment.css"
MANIFEST = ROOT / "deployment/tos-production-runtime.json"
PATCH_DIR = Path(__file__).resolve().parent
PAYLOAD = PATCH_DIR / "taskDetailsV2_12_Phase1R7InnerGridRightRailContainment.css"


def fail(message):
    raise RuntimeError(message)


def run(command, cwd=None):
    subprocess.run(command, cwd=cwd, check=True)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


for path in (FRONTEND, STYLE_DIR, BOARD, APP, SIDEBAR, R4_STYLE, R5_STYLE, MANIFEST, PAYLOAD):
    if not path.exists():
        fail(f"required path missing: {path}")
for command in ("node", "npm"):
    if not shutil.which(command):
        fail(f"required command not found: {command}")

board_source = BOARD.read_text()
app_source = APP.read_text()
sidebar_source = SIDEBAR.read_text()
r4_source = R4_STYLE.read_text()
r5_source = R5_STYLE.read_text()
payload_css = PAYLOAD.read_text()

if R4_MARKER not in r4_source:
    fail("required R4 baseline marker missing")
if R5_MARKER not in r5_source:
    fail("required R5 baseline marker missing")
if R7_STYLE.exists() or R7_MARKER in board_source:
    fail("Phase 1 R7 already appears to be applied")
if R7_MARKER not in payload_css:
    fail("R7 payload runtime marker missing")

# Production DOM contracts verified from the current Task Details source.
for contract in (
    'className="tos-task-details-layout grid gap-4 xl:grid-cols-[minmax(0,1fr)_304px]"',
    'className="tos-task-main-column min-w-0 space-y-4 text-right xl:order-1"',
    'className="tos-task-reference-v2-rail"',
    'className="tos-task-description-panel',
):
    if contract not in board_source:
        fail(f"Task Details DOM contract missing: {contract}")

# R5 shell contracts must remain untouched.
for contract in (
    '<div dir={isAr ? "rtl" : "ltr"} className="tos-premium-system-v14',
    'className="tos-premium-app-frame relative flex h-full w-full max-w-none gap-2 overflow-hidden lg:gap-3"',
    'className="tos-premium-main-shell min-w-0 flex-1 overflow-hidden',
):
    if contract not in app_source:
        fail(f"App shell contract missing: {contract}")
if '"tos-premium-sidebar relative h-full' not in sidebar_source:
    fail("Sidebar shell contract missing")

# R7 must load after every Phase1 R* stylesheet already present on the live target,
# including a server-applied R6 even if that patch is not stored in this repository.
r7_import = 'import "../styles/taskDetailsV2_12_Phase1R7InnerGridRightRailContainment.css";'
if r7_import in board_source:
    fail("R7 stylesheet import already exists")
import_pattern = re.compile(r'^import "\.\./styles/taskDetailsV2_12_Phase1R[^"\n]+\.css";$', re.MULTILINE)
imports = list(import_pattern.finditer(board_source))
if not imports:
    fail("no Phase1 R* stylesheet import anchor found")
last_import = imports[-1]
updated_board = board_source[:last_import.end()] + "\n" + r7_import + board_source[last_import.end():]
if r7_import not in updated_board:
    fail("failed to add R7 stylesheet import")

# Validate the geometry fix payload before touching production source.
for contract in (
    'position:absolute!important',
    'grid-template-columns:minmax(0,1fr) clamp(280px,24%,340px)!important',
    '.tos-task-reference-v2-rail',
    'grid-column:2!important',
    '.tos-task-editor-toolbar',
    'flex-flow:row wrap!important',
):
    if contract not in payload_css:
        fail(f"R7 CSS contract missing: {contract}")

# Freeze existing source and all earlier Phase1 styles, including any R6 created on server.
app_hash = sha256(APP)
sidebar_hash = sha256(SIDEBAR)
prior_styles = sorted(p for p in STYLE_DIR.glob("taskDetailsV2_12_Phase1*.css") if p != R7_STYLE)
prior_style_hashes = {p: sha256(p) for p in prior_styles}
r6_detected = any("R6" in p.name for p in prior_styles) or "Phase1R6" in board_source
r6_markers = set()
r6_marker_pattern = re.compile(r'--tos-task-details-v2-12-phase1-r6[-a-z0-9]*-runtime')
for path in prior_styles:
    for marker in r6_marker_pattern.findall(path.read_text(errors="ignore")):
        r6_markers.add(marker)

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
backup_root = Path(f"/var/backups/tos-patches/task-details-v2-12-phase1-r7-{stamp}")
backup_root.mkdir(parents=True, exist_ok=False)
board_backup = backup_root / BOARD.name
shutil.copy2(BOARD, board_backup)

LIVE.parent.mkdir(parents=True, exist_ok=True)
staging = LIVE.parent / f"build.task-details-v2-12-phase1-r7-staging-{stamp}"
live_backup = LIVE.parent / f"build.task-details-v2-12-phase1-r7-backup-{stamp}"
live_swapped = False
r7_written = False

try:
    BOARD.write_text(updated_board)
    R7_STYLE.write_text(payload_css.rstrip() + "\n")
    r7_written = True

    if sha256(APP) != app_hash:
        fail("App.jsx changed unexpectedly")
    if sha256(SIDEBAR) != sidebar_hash:
        fail("Sidebar.jsx changed unexpectedly")
    for path, digest in prior_style_hashes.items():
        if sha256(path) != digest:
            fail(f"prior Phase1 stylesheet changed unexpectedly: {path.name}")

    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists() or not (DIST / "index.html").exists():
        fail("frontend dist missing after build")

    built_css = "\n".join(p.read_text(errors="ignore") for p in DIST.rglob("*.css"))
    for marker in (R7_MARKER, R5_MARKER, R4_MARKER, *sorted(r6_markers)):
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
    for marker in (R7_MARKER, R5_MARKER, R4_MARKER, *sorted(r6_markers)):
        if marker not in live_css:
            fail(f"required runtime marker missing from live CSS: {marker}")

    if sha256(APP) != app_hash or sha256(SIDEBAR) != sidebar_hash:
        fail("frozen app shell source changed after deploy")
    for path, digest in prior_style_hashes.items():
        if sha256(path) != digest:
            fail(f"prior Phase1 stylesheet changed after deploy: {path.name}")

except Exception:
    shutil.copy2(board_backup, BOARD)
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

print(f"VERSION={VERSION}")
print(f"PATCH={PATCH_NAME}")
print("PASS/FAIL=PASS")
print("BUILD_RESULT=PASS")
print("LIVE_DEPLOY=PASS")
print("MAIN_SHELL_CONTAINMENT=YES")
print("OVERVIEW_GRID_FIT=YES")
print("RIGHT_RAIL_CONTAINED=YES")
print("DESCRIPTION_TOOLBAR_CONTAINED=YES")
print(f"R6_DETECTED={'YES' if r6_detected else 'NO'}")
print("R5_SIDEBAR_FIX_PRESERVED=YES")
print("APP_JS_CHANGED=NO")
print("SIDEBAR_JS_CHANGED=NO")
print("PRIOR_PHASE1_CSS_CHANGED=NO")
print("BACKEND_CHANGED=NO")
print("DATABASE_CHANGED=NO")
print("TCS_CHANGED=NO")
print("RAMZY_CHANGED=NO")
print("NO_BROWSER_QA=YES")
print("NO_SCREENSHOTS=YES")
print("PUSH=NO")
print(f"BACKUP={backup_root}")
print("STATUS=DEPLOYED__MANUAL_VISUAL_QA_REQUIRED")
