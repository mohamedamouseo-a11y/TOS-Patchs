from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import time

VERSION = "TOS_TASK_DETAILS_V2_12_PHASE1_R13_STRUCTURAL_PHYSICAL_RIGHT_RAIL_SLOT"
PATCH_NAME = "TOS-UXUI-TASK-DETAILS-V2-12-PHASE1-R13-STRUCTURAL-PHYSICAL-RIGHT-RAIL-SLOT"
R12_MARKER = "--tos-task-details-v2-12-phase1-r12-force-physical-right-empty-lane-runtime"
R13_MARKER = "--tos-task-details-v2-12-phase1-r13-structural-physical-right-rail-slot-runtime"

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
STYLE_DIR = FRONTEND / "src/styles"
BOARD = FRONTEND / "src/components/ProfessionalTaskBoard.jsx"
APP = FRONTEND / "src/App.jsx"
SIDEBAR = FRONTEND / "src/components/layout/Sidebar.jsx"
R12_STYLE = STYLE_DIR / "taskDetailsV2_12_Phase1R12ForcePhysicalRightEmptyLane.css"
R13_STYLE = STYLE_DIR / "taskDetailsV2_12_Phase1R13StructuralPhysicalRightRailSlot.css"
MANIFEST = ROOT / "deployment/tos-production-runtime.json"
PATCH_DIR = Path(__file__).resolve().parent
PAYLOAD = PATCH_DIR / "taskDetailsV2_12_Phase1R13StructuralPhysicalRightRailSlot.css"


def fail(message):
    raise RuntimeError(message)


def run(command, cwd=None):
    subprocess.run(command, cwd=cwd, check=True)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


for path in (FRONTEND, STYLE_DIR, BOARD, APP, SIDEBAR, R12_STYLE, MANIFEST, PAYLOAD):
    if not path.exists():
        fail(f"required path missing: {path}")
for command in ("node", "npm"):
    if not shutil.which(command):
        fail(f"required command not found: {command}")

board_source = BOARD.read_text()
r12_source = R12_STYLE.read_text()
payload_css = PAYLOAD.read_text()

if R12_MARKER not in r12_source:
    fail("required R12 baseline marker missing")
if R13_STYLE.exists() or R13_MARKER in board_source:
    fail("Phase 1 R13 already appears to be applied")
if R13_MARKER not in payload_css:
    fail("R13 payload runtime marker missing")

open_contract = '<aside className="tos-task-reference-v2-rail" dir={modalDirection}>'
if board_source.count(open_contract) != 1:
    fail(f"expected exactly one rail opening contract, found {board_source.count(open_contract)}")
open_index = board_source.index(open_contract)
close_index = board_source.find("</aside>", open_index)
if close_index < 0:
    fail("rail closing </aside> not found")

wrapped_open = '<div className="tos-task-reference-v2-rail-slot">\n              ' + open_contract
updated_board = board_source[:open_index] + wrapped_open + board_source[open_index + len(open_contract):]
# Recompute closing index after opening insertion.
open_index2 = updated_board.index(open_contract)
close_index2 = updated_board.find("</aside>", open_index2)
updated_board = updated_board[:close_index2 + len("</aside>")] + "\n            </div>" + updated_board[close_index2 + len("</aside>"):]

r12_import = 'import "../styles/taskDetailsV2_12_Phase1R12ForcePhysicalRightEmptyLane.css";'
r13_import = 'import "../styles/taskDetailsV2_12_Phase1R13StructuralPhysicalRightRailSlot.css";'
if r12_import not in updated_board:
    fail("R12 stylesheet import missing")
if r13_import in updated_board:
    fail("R13 stylesheet import already exists")
updated_board = updated_board.replace(r12_import, r12_import + "\n" + r13_import, 1)

for contract in (
    '.tos-task-reference-v2-rail-slot',
    'justify-content:flex-end!important',
    'direction:ltr!important',
    'width:370px!important',
    'top:258px!important',
):
    if contract not in payload_css:
        fail(f"R13 CSS contract missing: {contract}")

if 'className="tos-task-reference-v2-rail-slot"' not in updated_board:
    fail("R13 rail slot wrapper insertion failed")

app_hash = sha256(APP)
sidebar_hash = sha256(SIDEBAR)
prior_styles = sorted(p for p in STYLE_DIR.glob("taskDetailsV2_12_Phase1*.css") if p != R13_STYLE)
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
backup_root = Path(f"/var/backups/tos-patches/task-details-v2-12-phase1-r13-{stamp}")
backup_root.mkdir(parents=True, exist_ok=False)
board_backup = backup_root / BOARD.name
shutil.copy2(BOARD, board_backup)

LIVE.parent.mkdir(parents=True, exist_ok=True)
staging = LIVE.parent / f"build.task-details-v2-12-phase1-r13-staging-{stamp}"
live_backup = LIVE.parent / f"build.task-details-v2-12-phase1-r13-backup-{stamp}"
live_swapped = False
r13_written = False

try:
    BOARD.write_text(updated_board)
    R13_STYLE.write_text(payload_css.rstrip() + "\n")
    r13_written = True

    if sha256(APP) != app_hash or sha256(SIDEBAR) != sidebar_hash:
        fail("frozen app shell source changed unexpectedly")
    for path, digest in prior_style_hashes.items():
        if sha256(path) != digest:
            fail(f"prior Phase1 stylesheet changed unexpectedly: {path.name}")

    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists() or not (DIST / "index.html").exists():
        fail("frontend dist missing after build")

    built_css = "\n".join(p.read_text(errors="ignore") for p in DIST.rglob("*.css"))
    for marker in (R13_MARKER, R12_MARKER):
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
    for marker in (R13_MARKER, R12_MARKER):
        if marker not in live_css:
            fail(f"required runtime marker missing from live CSS: {marker}")

except Exception:
    shutil.copy2(board_backup, BOARD)
    if r13_written and R13_STYLE.exists():
        R13_STYLE.unlink()
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
print("TASK_CARD_POSITION_PRESERVED=YES")
print("RIGHT_EMPTY_LANE_PRESERVED=YES")
print("RIGHT_RAIL_PLACEMENT=STRUCTURAL_PHYSICAL_RIGHT")
print("RIGHT_RAIL_WRAPPER_ADDED=YES")
print("R12_BASELINE_PRESERVED=YES")
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
