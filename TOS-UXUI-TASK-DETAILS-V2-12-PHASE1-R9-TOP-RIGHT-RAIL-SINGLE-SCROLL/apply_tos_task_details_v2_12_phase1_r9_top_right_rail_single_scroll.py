from pathlib import Path
import hashlib
import json
import re
import shutil
import subprocess
import sys
import time

VERSION = "TOS_TASK_DETAILS_V2_12_PHASE1_R9_TOP_RIGHT_RAIL_SINGLE_SCROLL"
PATCH_NAME = "TOS-UXUI-TASK-DETAILS-V2-12-PHASE1-R9-TOP-RIGHT-RAIL-SINGLE-SCROLL"
R4_MARKER = "--tos-task-details-v2-12-phase1-r4-shell-rtl-physical-overlay-lock-runtime"
R5_MARKER = "--tos-task-details-v2-12-phase1-r5-sidebar-stays-right-runtime"
R7_MARKER = "--tos-task-details-v2-12-phase1-r7-inner-grid-right-rail-containment-runtime"
R8_MARKER = "--tos-task-details-v2-12-phase1-r8-restore-canonical-right-rail-no-clip-runtime"
R9_MARKER = "--tos-task-details-v2-12-phase1-r9-top-right-rail-single-scroll-runtime"

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
STYLE_DIR = FRONTEND / "src/styles"
BOARD = FRONTEND / "src/components/ProfessionalTaskBoard.jsx"
APP = FRONTEND / "src/App.jsx"
SIDEBAR = FRONTEND / "src/components/layout/Sidebar.jsx"
R4_STYLE = STYLE_DIR / "taskDetailsV2_12_Phase1R4ShellRtlPhysicalOverlayLock.css"
R5_STYLE = STYLE_DIR / "taskDetailsV2_12_Phase1R5SidebarStaysRight.css"
R7_STYLE = STYLE_DIR / "taskDetailsV2_12_Phase1R7InnerGridRightRailContainment.css"
R8_STYLE = STYLE_DIR / "taskDetailsV2_12_Phase1R8RestoreCanonicalRightRailNoClip.css"
R9_STYLE = STYLE_DIR / "taskDetailsV2_12_Phase1R9TopRightRailSingleScroll.css"
MANIFEST = ROOT / "deployment/tos-production-runtime.json"
PATCH_DIR = Path(__file__).resolve().parent
PAYLOAD = PATCH_DIR / "taskDetailsV2_12_Phase1R9TopRightRailSingleScroll.css"


def fail(message):
    raise RuntimeError(message)


def run(command, cwd=None):
    subprocess.run(command, cwd=cwd, check=True)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


for path in (FRONTEND, STYLE_DIR, BOARD, APP, SIDEBAR, R4_STYLE, R5_STYLE, R7_STYLE, R8_STYLE, MANIFEST, PAYLOAD):
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
r7_source = R7_STYLE.read_text()
r8_source = R8_STYLE.read_text()
payload_css = PAYLOAD.read_text()

for marker, source, label in (
    (R4_MARKER, r4_source, "R4"),
    (R5_MARKER, r5_source, "R5"),
    (R7_MARKER, r7_source, "R7"),
    (R8_MARKER, r8_source, "R8"),
):
    if marker not in source:
        fail(f"required {label} baseline marker missing")

if R9_STYLE.exists() or R9_MARKER in board_source:
    fail("Phase 1 R9 already appears to be applied")
if R9_MARKER not in payload_css:
    fail("R9 payload runtime marker missing")

for contract in (
    'className="tos-task-details-layout grid gap-4 xl:grid-cols-[minmax(0,1fr)_304px]"',
    'className="tos-task-main-column min-w-0 space-y-4 text-right xl:order-1"',
    'className="tos-task-reference-v2-rail"',
    'overflow-y-auto',
):
    if contract not in board_source:
        fail(f"Task Details DOM contract missing: {contract}")
if 'tos-premium-page-viewport' not in app_source:
    fail("app page viewport contract missing")

r8_import = 'import "../styles/taskDetailsV2_12_Phase1R8RestoreCanonicalRightRailNoClip.css";'
r9_import = 'import "../styles/taskDetailsV2_12_Phase1R9TopRightRailSingleScroll.css";'
if r8_import not in board_source:
    fail("R8 stylesheet import missing")
if r9_import in board_source:
    fail("R9 stylesheet import already exists")
updated_board = board_source.replace(r8_import, r8_import + "\n" + r9_import, 1)

for contract in (
    '.tos-premium-page-viewport',
    'overflow:hidden!important',
    '--tos-r9-rail-width:304px',
    'top:0!important',
    'right:0!important',
    'width:calc(100% - var(--tos-r9-rail-width) - var(--tos-r9-rail-gap))!important',
    'overflow-y:auto!important',
):
    if contract not in payload_css:
        fail(f"R9 CSS contract missing: {contract}")

app_hash = sha256(APP)
sidebar_hash = sha256(SIDEBAR)
prior_styles = sorted(p for p in STYLE_DIR.glob("taskDetailsV2_12_Phase1*.css") if p != R9_STYLE)
prior_style_hashes = {p: sha256(p) for p in prior_styles}
r6_marker_pattern = re.compile(r'--tos-task-details-v2-12-phase1-r6[-a-z0-9]*-runtime')
r6_markers = set()
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
backup_root = Path(f"/var/backups/tos-patches/task-details-v2-12-phase1-r9-{stamp}")
backup_root.mkdir(parents=True, exist_ok=False)
board_backup = backup_root / BOARD.name
shutil.copy2(BOARD, board_backup)

LIVE.parent.mkdir(parents=True, exist_ok=True)
staging = LIVE.parent / f"build.task-details-v2-12-phase1-r9-staging-{stamp}"
live_backup = LIVE.parent / f"build.task-details-v2-12-phase1-r9-backup-{stamp}"
live_swapped = False
r9_written = False

try:
    BOARD.write_text(updated_board)
    R9_STYLE.write_text(payload_css.rstrip() + "\n")
    r9_written = True

    if sha256(APP) != app_hash or sha256(SIDEBAR) != sidebar_hash:
        fail("frozen app shell source changed unexpectedly")
    for path, digest in prior_style_hashes.items():
        if sha256(path) != digest:
            fail(f"prior Phase1 stylesheet changed unexpectedly: {path.name}")

    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists() or not (DIST / "index.html").exists():
        fail("frontend dist missing after build")

    built_css = "\n".join(p.read_text(errors="ignore") for p in DIST.rglob("*.css"))
    for marker in (R9_MARKER, R8_MARKER, R7_MARKER, R5_MARKER, R4_MARKER, *sorted(r6_markers)):
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
    for marker in (R9_MARKER, R8_MARKER, R7_MARKER, R5_MARKER, R4_MARKER, *sorted(r6_markers)):
        if marker not in live_css:
            fail(f"required runtime marker missing from live CSS: {marker}")

    if sha256(APP) != app_hash or sha256(SIDEBAR) != sidebar_hash:
        fail("frozen app shell source changed after deploy")
    for path, digest in prior_style_hashes.items():
        if sha256(path) != digest:
            fail(f"prior Phase1 stylesheet changed after deploy: {path.name}")

except Exception:
    shutil.copy2(board_backup, BOARD)
    if r9_written and R9_STYLE.exists():
        R9_STYLE.unlink()
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
print("RIGHT_RAIL_TOP_ALIGNED=YES")
print("RIGHT_RAIL_PHYSICAL_SIDE=RIGHT")
print("RIGHT_RAIL_WIDTH=304PX")
print("MAIN_COLUMN_RESERVED_LANE=YES")
print("SINGLE_TASK_SCROLL=YES")
print("APP_PAGE_SCROLL_DISABLED_WHILE_TASK_OPEN=YES")
print("R8_CLIPPING_FIX_PRESERVED=YES")
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
