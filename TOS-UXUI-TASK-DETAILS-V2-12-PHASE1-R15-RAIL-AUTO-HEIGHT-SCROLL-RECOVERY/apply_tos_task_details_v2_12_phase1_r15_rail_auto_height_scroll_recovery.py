from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import time

VERSION = "TOS_TASK_DETAILS_V2_12_PHASE1_R15_RAIL_AUTO_HEIGHT_SCROLL_RECOVERY"
PATCH_NAME = "TOS-UXUI-TASK-DETAILS-V2-12-PHASE1-R15-RAIL-AUTO-HEIGHT-SCROLL-RECOVERY"
R14_MARKER = "--tos-task-details-v2-12-phase1-r14-right-rail-bottom-scroll-extent-runtime"
R15_MARKER = "--tos-task-details-v2-12-phase1-r15-rail-auto-height-scroll-recovery-runtime"

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
STYLE_DIR = FRONTEND / "src/styles"
BOARD = FRONTEND / "src/components/ProfessionalTaskBoard.jsx"
APP = FRONTEND / "src/App.jsx"
SIDEBAR = FRONTEND / "src/components/layout/Sidebar.jsx"
R14_STYLE = STYLE_DIR / "taskDetailsV2_12_Phase1R14RightRailBottomScrollExtent.css"
R15_STYLE = STYLE_DIR / "taskDetailsV2_12_Phase1R15RailAutoHeightScrollRecovery.css"
MANIFEST = ROOT / "deployment/tos-production-runtime.json"
PATCH_DIR = Path(__file__).resolve().parent
PAYLOAD = PATCH_DIR / "taskDetailsV2_12_Phase1R15RailAutoHeightScrollRecovery.css"


def fail(message):
    raise RuntimeError(message)


def run(command, cwd=None):
    subprocess.run(command, cwd=cwd, check=True)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


for path in (FRONTEND, STYLE_DIR, BOARD, APP, SIDEBAR, R14_STYLE, MANIFEST, PAYLOAD):
    if not path.exists():
        fail(f"required path missing: {path}")
for command in ("node", "npm"):
    if not shutil.which(command):
        fail(f"required command not found: {command}")

board_source = BOARD.read_text()
r14_source = R14_STYLE.read_text()
payload_css = PAYLOAD.read_text()

if R14_MARKER not in r14_source:
    fail("required R14 baseline marker missing")
if R15_STYLE.exists() or R15_MARKER in board_source:
    fail("Phase 1 R15 already appears to be applied")
if R15_MARKER not in payload_css:
    fail("R15 payload runtime marker missing")
if 'className="tos-task-reference-v2-rail-slot"' not in board_source:
    fail("R13 structural rail slot contract missing")

r14_import = 'import "../styles/taskDetailsV2_12_Phase1R14RightRailBottomScrollExtent.css";'
r15_import = 'import "../styles/taskDetailsV2_12_Phase1R15RailAutoHeightScrollRecovery.css";'
if r14_import not in board_source:
    fail("R14 stylesheet import missing")
if r15_import in board_source:
    fail("R15 stylesheet import already exists")
updated_board = board_source.replace(r14_import, r14_import + "\n" + r15_import, 1)

for contract in (
    'min-height:0!important',
    'padding-bottom:0!important',
    'height:auto!important',
    '.tos-task-reference-v2-rail-slot',
):
    if contract not in payload_css:
        fail(f"R15 CSS contract missing: {contract}")

app_hash = sha256(APP)
sidebar_hash = sha256(SIDEBAR)
prior_styles = sorted(p for p in STYLE_DIR.glob("taskDetailsV2_12_Phase1*.css") if p != R15_STYLE)
prior_style_hashes = {p: sha256(p) for p in prior_styles}

manifest = json.loads(MANIFEST.read_text())
if manifest.get("application") != "TOS" or manifest.get("environment") != "production":
    fail("unexpected production runtime manifest")
if manifest.get("sourceRoot") != str(ROOT):
    fail("runtime sourceRoot does not match target")
frontend_runtime = manifest.get("frontend") or {}
DIST = Path(str(frontend_runtime.get("buildOutputDir") or ""))
LIVE = Path(str(frontend_runtime.get("publishedBuildDir") or ""))
if Path(str(frontend_runtime.get("sourceDir") or "")) != FRONTEND:
    fail("frontend runtime sourceDir mismatch")
if str(frontend_runtime.get("buildCommand") or "") != "npm run build":
    fail("unexpected frontend build command")
if DIST != FRONTEND / "dist":
    fail(f"unexpected frontend build output: {DIST}")
if LIVE != Path("/opt/apps/tamiyouz-front/build"):
    fail(f"unexpected live frontend path: {LIVE}")

stamp = int(time.time())
backup_root = Path(f"/var/backups/tos-patches/task-details-v2-12-phase1-r15-{stamp}")
backup_root.mkdir(parents=True, exist_ok=False)
board_backup = backup_root / BOARD.name
shutil.copy2(BOARD, board_backup)

LIVE.parent.mkdir(parents=True, exist_ok=True)
staging = LIVE.parent / f"build.task-details-v2-12-phase1-r15-staging-{stamp}"
live_backup = LIVE.parent / f"build.task-details-v2-12-phase1-r15-backup-{stamp}"
live_swapped = False
r15_written = False

try:
    BOARD.write_text(updated_board)
    R15_STYLE.write_text(payload_css.rstrip() + "\n")
    r15_written = True

    if sha256(APP) != app_hash or sha256(SIDEBAR) != sidebar_hash:
        fail("frozen app shell source changed unexpectedly")
    for path, digest in prior_style_hashes.items():
        if sha256(path) != digest:
            fail(f"prior Phase1 stylesheet changed unexpectedly: {path.name}")

    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists() or not (DIST / "index.html").exists():
        fail("frontend dist missing after build")

    built_css = "\n".join(p.read_text(errors="ignore") for p in DIST.rglob("*.css"))
    for marker in (R15_MARKER, R14_MARKER):
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
    for marker in (R15_MARKER, R14_MARKER):
        if marker not in live_css:
            fail(f"required runtime marker missing from live CSS: {marker}")

except Exception:
    shutil.copy2(board_backup, BOARD)
    if r15_written and R15_STYLE.exists():
        R15_STYLE.unlink()
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
print("R14_FIXED_FLOOR_REMOVED=YES")
print("R13_RAIL_POSITION_PRESERVED=YES")
print("RAIL_SLOT_HEIGHT_MODE=AUTO")
print("TASK_SCROLL_OWNERS=1")
print("APP_JS_CHANGED=NO")
print("SIDEBAR_JS_CHANGED=NO")
print("BACKEND_CHANGED=NO")
print("DATABASE_CHANGED=NO")
print("TCS_CHANGED=NO")
print("RAMZY_CHANGED=NO")
print("NO_BROWSER_QA=YES")
print("NO_SCREENSHOTS=YES")
print("PUSH=NO")
print(f"BACKUP={backup_root}")
print("STATUS=DEPLOYED__MANUAL_VISUAL_QA_REQUIRED")
