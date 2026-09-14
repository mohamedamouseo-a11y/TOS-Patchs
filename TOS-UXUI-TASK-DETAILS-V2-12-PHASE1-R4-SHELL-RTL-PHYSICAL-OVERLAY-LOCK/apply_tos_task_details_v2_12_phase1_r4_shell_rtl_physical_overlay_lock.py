from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import time

VERSION = "TOS_TASK_DETAILS_V2_12_PHASE1_R4_SHELL_RTL_PHYSICAL_OVERLAY_LOCK"
PATCH_NAME = "TOS-UXUI-TASK-DETAILS-V2-12-PHASE1-R4-SHELL-RTL-PHYSICAL-OVERLAY-LOCK"
OLD_R3_MARKER = "--tos-task-details-v2-11j-r3-dark-hero-tabs-specificity-fix-runtime"
PHASE1_MARKER = "--tos-task-details-v2-12-phase1-zero-overlap-runtime"
R1_MARKER = "--tos-task-details-v2-12-phase1-r1-rtl-description-zero-overlap-runtime"
R2_MARKER = "--tos-task-details-v2-12-phase1-r2-rtl-tabs-description-runtime"
R3_MARKER = "--tos-task-details-v2-12-phase1-r3-outer-shell-physical-geometry-runtime"
R4_MARKER = "--tos-task-details-v2-12-phase1-r4-shell-rtl-physical-overlay-lock-runtime"

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
R4_STYLE = FRONTEND / "src/styles/taskDetailsV2_12_Phase1R4ShellRtlPhysicalOverlayLock.css"
MANIFEST = ROOT / "deployment/tos-production-runtime.json"
PATCH_DIR = Path(__file__).resolve().parent
PAYLOAD = PATCH_DIR / "taskDetailsV2_12_Phase1R4ShellRtlPhysicalOverlayLock.css"


def fail(message):
    raise RuntimeError(message)


def run(command, cwd=None):
    subprocess.run(command, cwd=cwd, check=True)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


required_paths = (FRONTEND, BOARD, PARTS, APP, CANONICAL, PHASE1_STYLE, R1_STYLE, R2_STYLE, R3_STYLE, MANIFEST, PAYLOAD)
for path in required_paths:
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
r3_source = R3_STYLE.read_text()
payload_css = PAYLOAD.read_text()

parts_hash = sha256(PARTS)
app_hash = sha256(APP)
canonical_hash = sha256(CANONICAL)
phase1_hash = sha256(PHASE1_STYLE)
r1_hash = sha256(R1_STYLE)
r2_hash = sha256(R2_STYLE)
r3_hash = sha256(R3_STYLE)

for marker, source, label in (
    (OLD_R3_MARKER, canonical_source, "V2.11J R3"),
    (PHASE1_MARKER, phase1_source + canonical_source, "Phase 1"),
    (R1_MARKER, r1_source + canonical_source, "R1"),
    (R2_MARKER, r2_source + canonical_source, "R2"),
    (R3_MARKER, r3_source + canonical_source, "R3"),
):
    if marker not in source:
        fail(f"required {label} baseline marker missing")

if R4_STYLE.exists() or R4_MARKER in board_source or R4_MARKER in canonical_source:
    fail("Phase 1 R4 already appears to be applied")
if R4_MARKER not in payload_css:
    fail("R4 payload runtime marker missing")

# R3 regression: outer Task Details shell was forced to LTR.
outer_old = 'dir="ltr" data-content-dir={modalDirection}'
outer_new = 'dir={modalDirection} data-content-dir={modalDirection}'
outer_count = board_source.count(outer_old)
if outer_count != 1:
    fail(f"R3 outer LTR contract expected exactly once, found {outer_count}")
updated_board = board_source.replace(outer_old, outer_new, 1)

layout_contract = 'className="tos-task-details-layout grid gap-4 xl:grid-cols-[minmax(0,1fr)_304px]" dir={modalDirection}'
if layout_contract not in updated_board:
    fail("inner Task Details direction contract missing")

assignee_contract = 'const estimatedHeight = Math.min(300, Math.max(220, filteredMembers.length * 48 + 112));'
if assignee_contract not in updated_board:
    fail("R1 assignee geometry contract missing")

r3_import = 'import "../styles/taskDetailsV2_12_Phase1R3OuterShellPhysicalGeometryFix.css";'
r4_import = 'import "../styles/taskDetailsV2_12_Phase1R4ShellRtlPhysicalOverlayLock.css";'
if r4_import in updated_board:
    fail("R4 stylesheet import already exists")
if r3_import not in updated_board:
    fail("R3 stylesheet import anchor missing")
updated_board = updated_board.replace(r3_import, r3_import + "\n" + r4_import, 1)

for contract in (outer_new, layout_contract, assignee_contract, r3_import, r4_import):
    if contract not in updated_board:
        fail(f"post-edit contract missing: {contract}")

for contract in (
    R4_MARKER,
    'position:fixed!important',
    'right:0!important',
    'left:0!important',
    'width:100vw!important',
    '[data-content-dir="rtl"]',
    'direction:rtl!important',
):
    if contract not in payload_css:
        fail(f"R4 CSS contract missing: {contract}")

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
backup_root = Path(f"/var/backups/tos-patches/task-details-v2-12-phase1-r4-{stamp}")
backup_root.mkdir(parents=True, exist_ok=False)
board_backup = backup_root / BOARD.name
shutil.copy2(BOARD, board_backup)
for source_path in (CANONICAL, PHASE1_STYLE, R1_STYLE, R2_STYLE, R3_STYLE):
    shutil.copy2(source_path, backup_root / source_path.name)

LIVE.parent.mkdir(parents=True, exist_ok=True)
staging = LIVE.parent / f"build.task-details-v2-12-phase1-r4-staging-{stamp}"
live_backup = LIVE.parent / f"build.task-details-v2-12-phase1-r4-backup-{stamp}"
live_swapped = False
r4_written = False

try:
    BOARD.write_text(updated_board)
    R4_STYLE.write_text(payload_css.rstrip() + "\n")
    r4_written = True

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
    if sha256(R3_STYLE) != r3_hash:
        fail("R3 stylesheet changed unexpectedly")

    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists() or not (DIST / "index.html").exists():
        fail("frontend dist missing after build")

    built_css = "\n".join(p.read_text(errors="ignore") for p in DIST.rglob("*.css"))
    for marker in (R4_MARKER, R3_MARKER, R2_MARKER, R1_MARKER, PHASE1_MARKER, OLD_R3_MARKER):
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
    for marker in (R4_MARKER, R3_MARKER, R2_MARKER, R1_MARKER, PHASE1_MARKER, OLD_R3_MARKER):
        if marker not in live_css:
            fail(f"required runtime marker missing from live CSS: {marker}")

    if sha256(PARTS) != parts_hash or sha256(APP) != app_hash or sha256(CANONICAL) != canonical_hash:
        fail("frozen core source changed after deploy")
    if sha256(PHASE1_STYLE) != phase1_hash or sha256(R1_STYLE) != r1_hash or sha256(R2_STYLE) != r2_hash or sha256(R3_STYLE) != r3_hash:
        fail("prior patch stylesheet changed after deploy")

except Exception:
    shutil.copy2(board_backup, BOARD)
    if r4_written and R4_STYLE.exists():
        R4_STYLE.unlink()
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
print("OUTER_SHELL_DIR=MODAL_DIRECTION")
print("PHYSICAL_OVERLAY_LOCK=YES")
print("INNER_LAYOUT_DIR_MODAL_DIRECTION=PRESERVED")
print("ASSIGNEE_R1_GEOMETRY_PRESERVED=YES")
print("R2_TABS_DESCRIPTION_PRESERVED=YES")
print("R3_STYLESHEET_PRESERVED=YES")
print("TASK_BOARD_PARTS_CHANGED=NO")
print("APP_JS_CHANGED=NO")
print("CANONICAL_CSS_CHANGED=NO")
print("PHASE1_CSS_CHANGED=NO")
print("R1_CSS_CHANGED=NO")
print("R2_CSS_CHANGED=NO")
print("R3_CSS_CHANGED=NO")
print("TCS_CHANGED=NO")
print("RAMZY_CHANGED=NO")
print("BACKEND_CHANGED=NO")
print("DATABASE_CHANGED=NO")
print("NO_BROWSER_QA=YES")
print("NO_SCREENSHOTS=YES")
print("PUSH=NO")
print(f"BACKUP={backup_root}")
print("STATUS=DEPLOYED__MANUAL_VISUAL_QA_REQUIRED")
