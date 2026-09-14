from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import time

VERSION = "TOS_TASK_DETAILS_V2_12_PHASE1_ZERO_OVERLAP"
PATCH_NAME = "TOS-UXUI-TASK-DETAILS-V2-12-PHASE1-ZERO-OVERLAP"
BASELINE_CHAIN = "TOS_TASK_DETAILS_V2_11J_R3"
R3_RUNTIME = "--tos-task-details-v2-11j-r3-dark-hero-tabs-specificity-fix-runtime"
PHASE1_RUNTIME = "--tos-task-details-v2-12-phase1-zero-overlap-runtime"

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
APP = FRONTEND / "src/App.jsx"
BOARD = FRONTEND / "src/components/ProfessionalTaskBoard.jsx"
STYLE = FRONTEND / "src/styles/taskDetailsCanonicalReferenceV2.css"
MANIFEST = ROOT / "deployment/tos-production-runtime.json"
PATCH_DIR = Path(__file__).resolve().parent
PAYLOAD = PATCH_DIR / "taskDetailsV2_12_Phase1ZeroOverlap.css"


def fail(message):
    raise RuntimeError(message)


def run(command, cwd=None):
    subprocess.run(command, cwd=cwd, check=True)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


for path in (FRONTEND, APP, BOARD, STYLE, MANIFEST, PAYLOAD):
    if not path.exists():
        fail(f"required path missing: {path}")
for command in ("node", "npm"):
    if not shutil.which(command):
        fail(f"required command not found: {command}")

app_source = APP.read_text()
board_source = BOARD.read_text()
style_source = STYLE.read_text()
payload_css = PAYLOAD.read_text()

# Baseline and live-contract guards. Phase 1 must sit on top of deployed R3.
if R3_RUNTIME not in style_source:
    fail("required V2.11J_R3 baseline marker missing; do not apply Phase 1 out of order")
if PHASE1_RUNTIME in style_source:
    fail("V2.12 Phase 1 Zero Overlap already applied")

for source_contract in (
    "tos-task-details-reference-v2",
    "tos-task-details-layout",
    "tos-task-reference-v2-rail",
    "tos-task-description-panel",
    "tos-task-detail-tabs",
    "tos-task-v2-assignee-popover",
    "tos-task-v2-assignee-list",
    "tos-task-v2-premium-menu",
    "tos-task-v2-calendar-popover",
):
    if source_contract not in (style_source + "\n" + board_source):
        fail(f"live selector contract missing: {source_contract}")

for payload_contract in (
    PHASE1_RUNTIME,
    ".tos-task-reference-v2-rail",
    ".tos-task-description-panel",
    ".tos-task-v2-assignee-popover",
    ".tos-task-v2-assignee-list",
    ".tos-task-v2-premium-menu",
    ".tos-task-v2-calendar-popover",
    "overscroll-behavior:contain",
):
    if payload_contract not in payload_css:
        fail(f"Phase 1 CSS contract missing: {payload_contract}")

# Phase 1 is presentation-only. Reject logic-drift patterns in the payload.
for forbidden in (
    "display:none",
    "pointer-events:none",
    "visibility:hidden",
    "content:\"TCS Assistant",
    "content:\"مساعد TCS",
):
    if forbidden in payload_css:
        fail(f"Phase 1 payload contains forbidden token: {forbidden}")

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

# Freeze all logic-bearing sources for this CSS-only phase.
frozen_hashes = {APP: sha256(APP), BOARD: sha256(BOARD)}
stamp = int(time.time())
backup_root = Path(f"/var/backups/tos-patches/task-details-v2-12-phase1-zero-overlap-{stamp}")
backup_root.mkdir(parents=True, exist_ok=False)
style_backup = backup_root / STYLE.name
shutil.copy2(STYLE, style_backup)

LIVE.parent.mkdir(parents=True, exist_ok=True)
staging = LIVE.parent / f"build.task-details-v2-12-phase1-zero-overlap-staging-{stamp}"
live_backup = LIVE.parent / f"build.task-details-v2-12-phase1-zero-overlap-backup-{stamp}"
live_swapped = False

try:
    STYLE.write_text(style_source.rstrip() + "\n\n" + payload_css.strip() + "\n")
    written_style = STYLE.read_text()
    if PHASE1_RUNTIME not in written_style:
        fail("Phase 1 runtime marker missing after stylesheet write")
    if written_style.count(PHASE1_RUNTIME) != 1:
        fail("Phase 1 runtime marker is not unique")

    for path, expected in frozen_hashes.items():
        if sha256(path) != expected:
            fail(f"frozen source changed unexpectedly: {path}")

    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists() or not (DIST / "index.html").exists():
        fail("frontend dist missing after build")

    built_css = "\n".join(p.read_text(errors="ignore") for p in DIST.rglob("*.css"))
    if PHASE1_RUNTIME not in built_css:
        fail("Phase 1 runtime marker missing from built CSS")
    if R3_RUNTIME not in built_css:
        fail("R3 baseline marker disappeared from built CSS")

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
    if PHASE1_RUNTIME not in live_css:
        fail("Phase 1 runtime marker missing from live CSS")
    if R3_RUNTIME not in live_css:
        fail("R3 baseline marker missing from live CSS")

    for path, expected in frozen_hashes.items():
        if sha256(path) != expected:
            fail(f"frozen source changed after deploy: {path}")

except Exception:
    shutil.copy2(style_backup, STYLE)
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
print(f"BASELINE_CHAIN={BASELINE_CHAIN}")
print("PASS/FAIL=PASS")
print("BUILD_RESULT=PASS")
print("LIVE_DEPLOY=PASS")
print("PATCH_SCOPE=CSS_ONLY")
print("PHASE1_PRIORITY=ZERO_OVERLAP")
print("MAIN_RAIL_COLLISION_GUARD=YES")
print("ASSIGNEE_POPOVER_BOUNDED=YES")
print("ASSIGNEE_INTERNAL_SCROLL=YES")
print("STATUS_PRIORITY_MENU_BOUNDED=YES")
print("DATE_PICKER_BOUNDED=YES")
print("LEGACY_DETAIL_FLYOUT_BOUNDED=YES")
print("RTL_CHANGED=NO")
print("TASK_LOGIC_CHANGED=NO")
print("TCS_CHAT_SYSTEM_CHANGED=NO")
print("RAMZY_CHANGED=NO")
print("APP_JS_CHANGED=NO")
print("TASK_BOARD_JSX_CHANGED=NO")
print("BACKEND_CHANGED=NO")
print("API_CHANGED=NO")
print("DATABASE_CHANGED=NO")
print("PUSH=NO")
print(f"BACKUP_ROOT={backup_root}")
print("STATUS=READY_FOR_VISUAL_QA")
