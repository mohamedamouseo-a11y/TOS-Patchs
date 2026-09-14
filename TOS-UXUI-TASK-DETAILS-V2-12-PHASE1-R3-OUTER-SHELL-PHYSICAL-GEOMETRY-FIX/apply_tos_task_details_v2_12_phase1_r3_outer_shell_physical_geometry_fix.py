from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import time

VERSION = "TOS_TASK_DETAILS_V2_12_PHASE1_R3_OUTER_SHELL_PHYSICAL_GEOMETRY"
PATCH_NAME = "TOS-UXUI-TASK-DETAILS-V2-12-PHASE1-R3-OUTER-SHELL-PHYSICAL-GEOMETRY-FIX"
R3_OLD_MARKER = "--tos-task-details-v2-11j-r3-dark-hero-tabs-specificity-fix-runtime"
PHASE1_MARKER = "--tos-task-details-v2-12-phase1-zero-overlap-runtime"
R1_MARKER = "--tos-task-details-v2-12-phase1-r1-rtl-description-zero-overlap-runtime"
R2_MARKER = "--tos-task-details-v2-12-phase1-r2-rtl-tabs-description-runtime"
R3_MARKER = "--tos-task-details-v2-12-phase1-r3-outer-shell-physical-geometry-runtime"

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
BOARD = FRONTEND / "src/components/ProfessionalTaskBoard.jsx"
PARTS = FRONTEND / "src/features/tasks/taskBoardParts.jsx"
APP = FRONTEND / "src/App.jsx"
CANONICAL = FRONTEND / "src/styles/taskDetailsCanonicalReferenceV2.css"
PHASE1_STYLE = FRONTEND / "src/styles/taskDetailsV2_12_Phase1ZeroOverlap.css"
R1_STYLE = FRONTEND / "src/styles/taskDetailsV2_12_Phase1R1RtlDescriptionZeroOverlapFix.css"
R2_STYLE = FRONTEND / "src/styles/taskDetailsV2_12_Phase1R2RtlTabsDescriptionFix.css"
R3_STYLE = FRONTEND / "src/styles/taskDetailsV2_12_Phase1R3OuterShellPhysicalGeometryFix.css"
MANIFEST = ROOT / "deployment/tos-production-runtime.json"
PATCH_DIR = Path(__file__).resolve().parent
PAYLOAD = PATCH_DIR / "taskDetailsV2_12_Phase1R3OuterShellPhysicalGeometryFix.css"


def fail(message):
    raise RuntimeError(message)


def run(command, cwd=None):
    subprocess.run(command, cwd=cwd, check=True)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


for path in (FRONTEND, BOARD, PARTS, APP, CANONICAL, PHASE1_STYLE, R1_STYLE, R2_STYLE, MANIFEST, PAYLOAD):
    if not path.exists():
        fail(f"required path missing: {path}")
for command in ("node", "npm"):
    if not shutil.which(command):
        fail(f"required command not found: {command}")

board_source = BOARD.read_text()
canonical_source = CANONICAL.read_text()
phase1_source = PHASE1_STYLE.read_text()
r1_source = R1_STYLE.read_text()
r2_source = R2_STYLE.read_text()
payload_css = PAYLOAD.read_text()

parts_hash = sha256(PARTS)
app_hash = sha256(APP)
canonical_hash = sha256(CANONICAL)
phase1_hash = sha256(PHASE1_STYLE)
r1_hash = sha256(R1_STYLE)
r2_hash = sha256(R2_STYLE)

# Required deployed baseline.
for marker, source, label in (
    (R3_OLD_MARKER, canonical_source, "V2.11J R3"),
    (PHASE1_MARKER, phase1_source + canonical_source, "Phase 1"),
    (R1_MARKER, r1_source + canonical_source, "R1"),
    (R2_MARKER, r2_source + canonical_source, "R2"),
):
    if marker not in source:
        fail(f"required {label} baseline marker missing")

if R3_STYLE.exists() or R3_MARKER in board_source or R3_MARKER in canonical_source:
    fail("Phase 1 R3 already appears to be applied")
if R3_MARKER not in payload_css:
    fail("R3 payload runtime marker missing")

# Screenshot-confirmed regression contract from R1: the outer fullscreen shell must be restored to physical LTR.
outer_old = 'dir={modalDirection} data-content-dir={modalDirection}'
outer_new = 'dir="ltr" data-content-dir={modalDirection}'
outer_count = board_source.count(outer_old)
if outer_count != 1:
    fail(f"outer shell RTL contract expected exactly once, found {outer_count}")
updated_board = board_source.replace(outer_old, outer_new, 1)

# Inner Task Details layout MUST remain semantically directed by modalDirection.
layout_contract = 'className="tos-task-details-layout grid gap-4 xl:grid-cols-[minmax(0,1fr)_304px]" dir={modalDirection}'
if layout_contract not in updated_board:
    fail("inner Task Details layout RTL contract missing; refusing to regress content RTL")

# Preserve R1 assignee geometry exactly.
assignee_contract = 'const estimatedHeight = Math.min(300, Math.max(220, filteredMembers.length * 48 + 112));'
if assignee_contract not in updated_board:
    fail("R1 assignee bounded-height contract missing")

r2_import = 'import "../styles/taskDetailsV2_12_Phase1R2RtlTabsDescriptionFix.css";'
r3_import = 'import "../styles/taskDetailsV2_12_Phase1R3OuterShellPhysicalGeometryFix.css";'
if r3_import in updated_board:
    fail("R3 stylesheet import already exists")
if r2_import not in updated_board:
    fail("R2 stylesheet import anchor missing")
updated_board = updated_board.replace(r2_import, r2_import + "\n" + r3_import, 1)

for contract in (outer_new, layout_contract, assignee_contract, r2_import, r3_import):
    if contract not in updated_board:
        fail(f"post-edit contract missing: {contract}")

# Ensure the old outer root contract is gone but inner RTL remains.
if outer_old in updated_board:
    fail("outer root still carries modalDirection")

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
backup_root = Path(f"/var/backups/tos-patches/task-details-v2-12-phase1-r3-{stamp}")
backup_root.mkdir(parents=True, exist_ok=False)
board_backup = backup_root / BOARD.name
shutil.copy2(BOARD, board_backup)
for source_path in (PHASE1_STYLE, R1_STYLE, R2_STYLE, CANONICAL):
    shutil.copy2(source_path, backup_root / source_path.name)

LIVE.parent.mkdir(parents=True, exist_ok=True)
staging = LIVE.parent / f"build.task-details-v2-12-phase1-r3-staging-{stamp}"
live_backup = LIVE.parent / f"build.task-details-v2-12-phase1-r3-backup-{stamp}"
live_swapped = False
r3_written = False

try:
    BOARD.write_text(updated_board)
    R3_STYLE.write_text(payload_css.rstrip() + "\n")
    r3_written = True

    # Frozen files and prior patch payloads must remain byte-identical.
    if sha256(PARTS) != parts_hash:
        fail("taskBoardParts.jsx changed unexpectedly")
    if sha256(APP) != app_hash:
        fail("App.jsx changed unexpectedly")
    if sha256(CANONICAL) != canonical_hash:
        fail("canonical stylesheet changed unexpectedly")
    if sha256(PHASE1_STYLE) != phase1_hash:
        fail("Phase1 stylesheet changed unexpectedly")
    if sha256(R1_STYLE) != r1_hash:
        fail("R1 stylesheet changed unexpectedly")
    if sha256(R2_STYLE) != r2_hash:
        fail("R2 stylesheet changed unexpectedly")

    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists() or not (DIST / "index.html").exists():
        fail("frontend dist missing after build")

    built_css = "\n".join(p.read_text(errors="ignore") for p in DIST.rglob("*.css"))
    for marker in (R3_MARKER, R2_MARKER, R1_MARKER, PHASE1_MARKER, R3_OLD_MARKER):
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
    for marker in (R3_MARKER, R2_MARKER, R1_MARKER, PHASE1_MARKER, R3_OLD_MARKER):
        if marker not in live_css:
            fail(f"required runtime marker missing from live CSS: {marker}")

    if sha256(PARTS) != parts_hash or sha256(APP) != app_hash or sha256(CANONICAL) != canonical_hash:
        fail("frozen core source changed after deploy")
    if sha256(PHASE1_STYLE) != phase1_hash or sha256(R1_STYLE) != r1_hash or sha256(R2_STYLE) != r2_hash:
        fail("prior patch stylesheet changed after deploy")

except Exception:
    shutil.copy2(board_backup, BOARD)
    if r3_written and R3_STYLE.exists():
        R3_STYLE.unlink()
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
print("OUTER_SHELL_DIR=LTR")
print("CONTENT_DIRECTION_DATA=PRESERVED")
print("INNER_LAYOUT_DIR_MODAL_DIRECTION=PRESERVED")
print("ASSIGNEE_R1_GEOMETRY_PRESERVED=YES")
print("R2_TABS_DESCRIPTION_PRESERVED=YES")
print("TASK_BOARD_PARTS_CHANGED=NO")
print("APP_JS_CHANGED=NO")
print("CANONICAL_CSS_CHANGED=NO")
print("PHASE1_CSS_CHANGED=NO")
print("R1_CSS_CHANGED=NO")
print("R2_CSS_CHANGED=NO")
print("TCS_CHANGED=NO")
print("RAMZY_CHANGED=NO")
print("BACKEND_CHANGED=NO")
print("DATABASE_CHANGED=NO")
print("NO_BROWSER_QA=YES")
print("NO_SCREENSHOTS=YES")
print("PUSH=NO")
print(f"BACKUP={backup_root}")
print("STATUS=DEPLOYED__MANUAL_VISUAL_QA_REQUIRED")
