from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import time

VERSION = "TOS_TASK_DETAILS_V2_12_PHASE1_R1_RTL_DESCRIPTION_ZERO_OVERLAP"
PATCH_NAME = "TOS-UXUI-TASK-DETAILS-V2-12-PHASE1-R1-RTL-DESCRIPTION-ZERO-OVERLAP-FIX"
PHASE1_MARKER = "--tos-task-details-v2-12-phase1-zero-overlap-runtime"
R3_MARKER = "--tos-task-details-v2-11j-r3-dark-hero-tabs-specificity-fix-runtime"
R1_MARKER = "--tos-task-details-v2-12-phase1-r1-rtl-description-zero-overlap-runtime"

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
BOARD = FRONTEND / "src/components/ProfessionalTaskBoard.jsx"
PARTS = FRONTEND / "src/features/tasks/taskBoardParts.jsx"
APP = FRONTEND / "src/App.jsx"
CANONICAL = FRONTEND / "src/styles/taskDetailsCanonicalReferenceV2.css"
PHASE1_STYLE = FRONTEND / "src/styles/taskDetailsV2_12_Phase1ZeroOverlap.css"
R1_STYLE = FRONTEND / "src/styles/taskDetailsV2_12_Phase1R1RtlDescriptionZeroOverlapFix.css"
MANIFEST = ROOT / "deployment/tos-production-runtime.json"
PATCH_DIR = Path(__file__).resolve().parent
PAYLOAD = PATCH_DIR / "taskDetailsV2_12_Phase1R1RtlDescriptionZeroOverlapFix.css"


def fail(message):
    raise RuntimeError(message)


def run(command, cwd=None):
    subprocess.run(command, cwd=cwd, check=True)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replace_once_or_verify(source, old, new, label):
    count = source.count(old)
    if count == 1:
        return source.replace(old, new, 1), True
    if count > 1:
        fail(f"{label}: expected one old contract, found {count}")
    if new in source:
        return source, False
    fail(f"{label}: neither old nor fixed contract found")


for path in (FRONTEND, BOARD, PARTS, APP, CANONICAL, MANIFEST, PAYLOAD):
    if not path.exists():
        fail(f"required path missing: {path}")
for command in ("node", "npm"):
    if not shutil.which(command):
        fail(f"required command not found: {command}")

board_source = BOARD.read_text()
parts_hash = sha256(PARTS)
app_hash = sha256(APP)
canonical_hash = sha256(CANONICAL)
canonical_source = CANONICAL.read_text()
phase1_source = PHASE1_STYLE.read_text() if PHASE1_STYLE.exists() else ""
payload_css = PAYLOAD.read_text()

if R3_MARKER not in canonical_source:
    fail("required V2.11J_R3 baseline marker missing")
if PHASE1_MARKER not in canonical_source and PHASE1_MARKER not in phase1_source:
    fail("required V2.12 Phase 1 baseline marker missing")
if R1_STYLE.exists() or R1_MARKER in canonical_source or R1_MARKER in board_source:
    fail("Phase 1 R1 already appears to be applied")
if R1_MARKER not in payload_css:
    fail("R1 payload runtime marker missing")

# Real screenshot-confirmed source contracts.
outer_old = 'dir="ltr" data-content-dir={modalDirection}'
outer_new = 'dir={modalDirection} data-content-dir={modalDirection}'
layout_old = 'className="tos-task-details-layout grid gap-4 xl:grid-cols-[minmax(0,1fr)_304px]" dir="ltr"'
layout_new = 'className="tos-task-details-layout grid gap-4 xl:grid-cols-[minmax(0,1fr)_304px]" dir={modalDirection}'
assignee_old = 'const estimatedHeight = Math.min(480, Math.max(240, filteredMembers.length * 52 + 116));'
assignee_new = 'const estimatedHeight = Math.min(300, Math.max(220, filteredMembers.length * 48 + 112));'

updated_board, outer_changed = replace_once_or_verify(board_source, outer_old, outer_new, "root RTL direction")
updated_board, layout_changed = replace_once_or_verify(updated_board, layout_old, layout_new, "layout RTL direction")
updated_board, assignee_changed = replace_once_or_verify(updated_board, assignee_old, assignee_new, "assignee bounded-height geometry")

r1_import = 'import "../styles/taskDetailsV2_12_Phase1R1RtlDescriptionZeroOverlapFix.css";'
phase1_import = 'import "../styles/taskDetailsV2_12_Phase1ZeroOverlap.css";'
canonical_import = 'import "../styles/taskDetailsCanonicalReferenceV2.css";'

if r1_import in updated_board:
    fail("R1 stylesheet import already exists")
if phase1_import in updated_board:
    updated_board = updated_board.replace(phase1_import, phase1_import + "\n" + r1_import, 1)
elif canonical_import in updated_board:
    updated_board = updated_board.replace(canonical_import, canonical_import + "\n" + r1_import, 1)
else:
    fail("Task Details stylesheet import anchor missing")

# Verify the exact three intentional JSX changes plus one CSS import.
for contract in (outer_new, layout_new, assignee_new, r1_import):
    if contract not in updated_board:
        fail(f"post-edit board contract missing: {contract}")

# Verify payload contains each screenshot-driven fix area.
for contract in (
    R1_MARKER,
    '[data-content-dir="rtl"]',
    '.tos-task-description-panel .tos-task-editor-toolbar > div',
    ':has(.tos-task-v2-assignee-picker-trigger[aria-expanded="true"])',
    '.tos-task-side-rail[data-more-details="true"]',
):
    if contract not in payload_css:
        fail(f"R1 CSS contract missing: {contract}")

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
backup_root = Path(f"/var/backups/tos-patches/task-details-v2-12-phase1-r1-{stamp}")
backup_root.mkdir(parents=True, exist_ok=False)
board_backup = backup_root / BOARD.name
canonical_backup = backup_root / CANONICAL.name
shutil.copy2(BOARD, board_backup)
shutil.copy2(CANONICAL, canonical_backup)
phase1_backup = None
if PHASE1_STYLE.exists():
    phase1_backup = backup_root / PHASE1_STYLE.name
    shutil.copy2(PHASE1_STYLE, phase1_backup)

LIVE.parent.mkdir(parents=True, exist_ok=True)
staging = LIVE.parent / f"build.task-details-v2-12-phase1-r1-staging-{stamp}"
live_backup = LIVE.parent / f"build.task-details-v2-12-phase1-r1-backup-{stamp}"
live_swapped = False
r1_written = False

try:
    BOARD.write_text(updated_board)
    R1_STYLE.write_text(payload_css.rstrip() + "\n")
    r1_written = True

    # Frozen files must stay frozen.
    if sha256(PARTS) != parts_hash:
        fail("taskBoardParts.jsx changed unexpectedly")
    if sha256(APP) != app_hash:
        fail("App.jsx changed unexpectedly")
    if sha256(CANONICAL) != canonical_hash:
        fail("canonical stylesheet changed unexpectedly")

    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists() or not (DIST / "index.html").exists():
        fail("frontend dist missing after build")

    built_css = "\n".join(p.read_text(errors="ignore") for p in DIST.rglob("*.css"))
    built_js = "\n".join(p.read_text(errors="ignore") for p in DIST.rglob("*.js"))
    if R1_MARKER not in built_css:
        fail("R1 runtime marker missing from built CSS")
    if PHASE1_MARKER not in built_css:
        fail("Phase 1 baseline marker missing from built CSS")

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
    if R1_MARKER not in live_css:
        fail("R1 runtime marker missing from live CSS")
    if PHASE1_MARKER not in live_css:
        fail("Phase 1 baseline marker missing from live CSS")

    if sha256(PARTS) != parts_hash or sha256(APP) != app_hash or sha256(CANONICAL) != canonical_hash:
        fail("frozen source changed after deploy")

except Exception:
    shutil.copy2(board_backup, BOARD)
    shutil.copy2(canonical_backup, CANONICAL)
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
print(f"PATCH={PATCH_NAME}")
print("PASS/FAIL=PASS")
print("BUILD_RESULT=PASS")
print("LIVE_DEPLOY=PASS")
print("PATCH_SCOPE=FRONTEND_RTL_AND_LAYOUT_HOTFIX")
print(f"ROOT_RTL_SOURCE_CHANGED={'YES' if outer_changed else 'ALREADY_FIXED'}")
print(f"LAYOUT_RTL_SOURCE_CHANGED={'YES' if layout_changed else 'ALREADY_FIXED'}")
print(f"ASSIGNEE_HEIGHT_SOURCE_CHANGED={'YES' if assignee_changed else 'ALREADY_FIXED'}")
print("DESCRIPTION_EDITOR_RTL_CONTAINMENT=YES")
print("ASSIGNEE_ZERO_OVERLAP_RESERVATION=YES")
print("MORE_DETAILS_FLOATING_OVERLAP_REMOVED=YES")
print("TASK_BOARD_PARTS_CHANGED=NO")
print("APP_JS_CHANGED=NO")
print("CANONICAL_CSS_CHANGED=NO")
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
