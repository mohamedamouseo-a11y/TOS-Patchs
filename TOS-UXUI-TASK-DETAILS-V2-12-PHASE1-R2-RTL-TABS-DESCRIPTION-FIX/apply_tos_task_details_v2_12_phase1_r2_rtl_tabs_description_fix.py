from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import time

VERSION = "TOS_TASK_DETAILS_V2_12_PHASE1_R2_RTL_TABS_DESCRIPTION"
PATCH_NAME = "TOS-UXUI-TASK-DETAILS-V2-12-PHASE1-R2-RTL-TABS-DESCRIPTION-FIX"
R3_MARKER = "--tos-task-details-v2-11j-r3-dark-hero-tabs-specificity-fix-runtime"
PHASE1_MARKER = "--tos-task-details-v2-12-phase1-zero-overlap-runtime"
R1_MARKER = "--tos-task-details-v2-12-phase1-r1-rtl-description-zero-overlap-runtime"
R2_MARKER = "--tos-task-details-v2-12-phase1-r2-rtl-tabs-description-runtime"

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
BOARD = FRONTEND / "src/components/ProfessionalTaskBoard.jsx"
PARTS = FRONTEND / "src/features/tasks/taskBoardParts.jsx"
APP = FRONTEND / "src/App.jsx"
CANONICAL = FRONTEND / "src/styles/taskDetailsCanonicalReferenceV2.css"
PHASE1_STYLE = FRONTEND / "src/styles/taskDetailsV2_12_Phase1ZeroOverlap.css"
R1_STYLE = FRONTEND / "src/styles/taskDetailsV2_12_Phase1R1RtlDescriptionZeroOverlapFix.css"
R2_STYLE = FRONTEND / "src/styles/taskDetailsV2_12_Phase1R2RtlTabsDescriptionFix.css"
MANIFEST = ROOT / "deployment/tos-production-runtime.json"
PATCH_DIR = Path(__file__).resolve().parent
PAYLOAD = PATCH_DIR / "taskDetailsV2_12_Phase1R2RtlTabsDescriptionFix.css"


def fail(message):
    raise RuntimeError(message)


def run(command, cwd=None):
    subprocess.run(command, cwd=cwd, check=True)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


for path in (FRONTEND, BOARD, PARTS, APP, CANONICAL, R1_STYLE, MANIFEST, PAYLOAD):
    if not path.exists():
        fail(f"required path missing: {path}")
for command in ("node", "npm"):
    if not shutil.which(command):
        fail(f"required command not found: {command}")

board_source = BOARD.read_text()
canonical_source = CANONICAL.read_text()
phase1_source = PHASE1_STYLE.read_text() if PHASE1_STYLE.exists() else ""
r1_source = R1_STYLE.read_text()
payload_css = PAYLOAD.read_text()

# Baseline guards.
if R3_MARKER not in canonical_source:
    fail("required V2.11J_R3 marker missing")
if PHASE1_MARKER not in canonical_source and PHASE1_MARKER not in phase1_source:
    fail("required V2.12 Phase 1 marker missing")
if R1_MARKER not in r1_source:
    fail("required V2.12 Phase 1 R1 marker missing")
if R2_STYLE.exists() or R2_MARKER in board_source or R2_MARKER in canonical_source or R2_MARKER in r1_source:
    fail("Phase 1 R2 already appears to be applied")
if R2_MARKER not in payload_css:
    fail("R2 payload runtime marker missing")

# R1 source contracts must remain present. R2 must not regress them.
for contract in (
    'dir={modalDirection} data-content-dir={modalDirection}',
    'className="tos-task-details-layout grid gap-4 xl:grid-cols-[minmax(0,1fr)_304px]" dir={modalDirection}',
    'const estimatedHeight = Math.min(300, Math.max(220, filteredMembers.length * 48 + 112));',
):
    if contract not in board_source:
        fail(f"R1 source contract missing: {contract}")

r1_import = 'import "../styles/taskDetailsV2_12_Phase1R1RtlDescriptionZeroOverlapFix.css";'
r2_import = 'import "../styles/taskDetailsV2_12_Phase1R2RtlTabsDescriptionFix.css";'
if r1_import not in board_source:
    fail("R1 stylesheet import missing")
if r2_import in board_source:
    fail("R2 stylesheet import already exists")

# R2 changes only stylesheet loading. No other JSX logic is touched.
updated_board = board_source.replace(r1_import, r1_import + "\n" + r2_import, 1)
if updated_board.count(r2_import) != 1:
    fail("R2 stylesheet import insertion failed")

# Screenshot-driven CSS contracts.
for contract in (
    R2_MARKER,
    '.tos-task-reference-tabs-main',
    '.tos-task-summary-controls',
    '.tos-task-description-panel .tos-task-editor-toolbar > div',
    '.tos-task-rich-editor-content',
    'body > .tos-task-v2-assignee-popover[dir="rtl"]',
):
    if contract not in payload_css:
        fail(f"R2 CSS contract missing: {contract}")

# Explicitly forbid the two R1 geometry areas from being redesigned in R2.
for forbidden in (
    ':has(.tos-task-v2-assignee-picker-trigger[aria-expanded="true"])',
    '.tos-task-side-rail[data-more-details="true"]{',
    'position:fixed',
):
    if forbidden in payload_css:
        fail(f"R2 payload unexpectedly touches frozen geometry: {forbidden}")

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

# Frozen-source hashes.
parts_hash = sha256(PARTS)
app_hash = sha256(APP)
canonical_hash = sha256(CANONICAL)
phase1_hash = sha256(PHASE1_STYLE) if PHASE1_STYLE.exists() else None
r1_hash = sha256(R1_STYLE)

stamp = int(time.time())
backup_root = Path(f"/var/backups/tos-patches/task-details-v2-12-phase1-r2-{stamp}")
backup_root.mkdir(parents=True, exist_ok=False)
board_backup = backup_root / BOARD.name
shutil.copy2(BOARD, board_backup)

LIVE.parent.mkdir(parents=True, exist_ok=True)
staging = LIVE.parent / f"build.task-details-v2-12-phase1-r2-staging-{stamp}"
live_backup = LIVE.parent / f"build.task-details-v2-12-phase1-r2-backup-{stamp}"
live_swapped = False
r2_written = False

try:
    BOARD.write_text(updated_board)
    R2_STYLE.write_text(payload_css.rstrip() + "\n")
    r2_written = True

    # Only BOARD import + new R2 CSS are allowed.
    if sha256(PARTS) != parts_hash:
        fail("taskBoardParts.jsx changed unexpectedly")
    if sha256(APP) != app_hash:
        fail("App.jsx changed unexpectedly")
    if sha256(CANONICAL) != canonical_hash:
        fail("canonical stylesheet changed unexpectedly")
    if PHASE1_STYLE.exists() and sha256(PHASE1_STYLE) != phase1_hash:
        fail("Phase 1 stylesheet changed unexpectedly")
    if sha256(R1_STYLE) != r1_hash:
        fail("R1 stylesheet changed unexpectedly")

    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists() or not (DIST / "index.html").exists():
        fail("frontend dist missing after build")

    built_css = "\n".join(p.read_text(errors="ignore") for p in DIST.rglob("*.css"))
    for marker in (PHASE1_MARKER, R1_MARKER, R2_MARKER):
        if marker not in built_css:
            fail(f"required marker missing from built CSS: {marker}")

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
    for marker in (PHASE1_MARKER, R1_MARKER, R2_MARKER):
        if marker not in live_css:
            fail(f"required marker missing from live CSS: {marker}")

    if sha256(PARTS) != parts_hash or sha256(APP) != app_hash or sha256(CANONICAL) != canonical_hash or sha256(R1_STYLE) != r1_hash:
        fail("frozen source changed after deploy")

except Exception:
    shutil.copy2(board_backup, BOARD)
    if r2_written and R2_STYLE.exists():
        R2_STYLE.unlink()
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
print("PATCH_SCOPE=RTL_TABS_AND_DESCRIPTION_ONLY")
print("R2_CSS_IMPORT_ADDED=YES")
print("TRUE_RTL_TABS_OVERRIDE=YES")
print("HERO_CONTROLS_RTL_OVERRIDE=YES")
print("DESCRIPTION_TOOLBAR_RTL_HARDENING=YES")
print("DESCRIPTION_EDITOR_MIN_HEIGHT_REDUCED=YES")
print("ASSIGNEE_R1_GEOMETRY_CHANGED=NO")
print("MORE_DETAILS_R1_GEOMETRY_CHANGED=NO")
print("TASK_BOARD_PARTS_CHANGED=NO")
print("APP_JS_CHANGED=NO")
print("CANONICAL_CSS_CHANGED=NO")
print("PHASE1_CSS_CHANGED=NO")
print("R1_CSS_CHANGED=NO")
print("TCS_CHANGED=NO")
print("RAMZY_CHANGED=NO")
print("BACKEND_CHANGED=NO")
print("API_CHANGED=NO")
print("DATABASE_CHANGED=NO")
print("NO_BROWSER_QA=YES")
print("NO_SCREENSHOTS=YES")
print("PUSH=NO")
print(f"BACKUP={backup_root}")
print("STATUS=DEPLOYED__MANUAL_VISUAL_QA_REQUIRED")
