from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import time

VERSION = "TOS_TASK_DETAILS_V2_11J_R3"
PATCH_NAME = "TOS-UXUI-TASK-DETAILS-V2-11J-R3-DARK-HERO-TABS-SPECIFICITY-FIX"
BASELINE_CHAIN = "TOS_TASK_DETAILS_V2_11J_R2"
R1_RUNTIME = "--tos-task-details-v2-11j-r1-primary-tabs-responsive-fix-runtime"
R2_RUNTIME = "--tos-task-details-v2-11j-r2-dark-premium-polish-runtime"
R3_RUNTIME = "--tos-task-details-v2-11j-r3-dark-hero-tabs-specificity-fix-runtime"

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
APP = FRONTEND / "src/App.jsx"
BOARD = FRONTEND / "src/components/ProfessionalTaskBoard.jsx"
STYLE = FRONTEND / "src/styles/taskDetailsCanonicalReferenceV2.css"
MANIFEST = ROOT / "deployment/tos-production-runtime.json"
PATCH_DIR = Path(__file__).resolve().parent
PAYLOAD = PATCH_DIR / "taskDetailsV2_11J_R3DarkHeroTabsSpecificityFix.css"


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

# Baseline chain guards.
if "TOS_TASK_DETAILS_V2_11J_TNC_COMMENTS_DEEP_LINK" not in app_source:
    fail("required V2.11J notification deep-link marker missing")
if "TOS_TASK_DETAILS_V2_11J_COMMENTS_PRIMARY_TAB" not in board_source:
    fail("required V2.11J Comments primary-tab marker missing")
if "TOS_TASK_DETAILS_V2_11H_HERO_DESCRIPTION_REMOVED" not in board_source:
    fail("required V2.11H Hero marker missing")
if "TOS_TASK_DETAILS_V2_11G_WAITING_CLIENT_BELOW_DESCRIPTION" not in board_source:
    fail("required V2.11G Waiting Client marker missing")
if R1_RUNTIME not in style_source:
    fail("required V2.11J_R1 responsive-tabs marker missing")
if R2_RUNTIME not in style_source:
    fail("required V2.11J_R2 dark-polish marker missing")
if R3_RUNTIME in style_source:
    fail("V2.11J_R3 already applied")

# Confirm the exact live specificity problem still exists before touching CSS.
for source_contract in (
    "body:has(.tos-task-details-reference-v1[data-content-dir])",
    ".tos-task-summary-controls",
    ".tos-task-v2-assignee-picker-trigger",
    ".tos-task-v2-premium-select-trigger",
    ".tos-task-v2-status-control",
    ".tos-task-v2-priority-control",
    ".tos-task-v2-date-trigger",
    ".tos-task-detail-tabs",
    ".tos-task-reference-tab[data-active=\"true\"]",
):
    if source_contract not in style_source:
        fail(f"live selector contract missing: {source_contract}")

# Payload is deliberately restricted to the two failed visual areas.
for payload_contract in (
    R3_RUNTIME,
    "html.dark body:has(.tos-task-details-reference-v1[data-content-dir])",
    ".tos-task-summary-controls > *:not(.tos-task-start-date-card)",
    ".tos-task-v2-assignee-picker-trigger",
    ".tos-task-v2-status-control .tos-task-v2-premium-select-trigger",
    ".tos-task-v2-priority-control .tos-task-v2-premium-select-trigger",
    ".tos-task-v2-date-trigger",
    ".tos-task-detail-tabs",
    ".tos-task-reference-tab[data-active=\"true\"]",
):
    if payload_contract not in payload_css:
        fail(f"R3 CSS contract missing: {payload_contract}")

# Explicitly forbid layout/logic drift in the payload.
for forbidden in (
    "grid-template-columns:",
    "flex-direction:",
    "order:",
    "position:fixed",
    "display:none",
):
    if forbidden in payload_css:
        fail(f"R3 payload contains forbidden geometry token: {forbidden}")

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

frozen_hashes = {APP: sha256(APP), BOARD: sha256(BOARD)}
stamp = int(time.time())
backup_root = Path(f"/var/backups/tos-patches/task-details-v2-11j-r3-{stamp}")
backup_root.mkdir(parents=True, exist_ok=False)
style_backup = backup_root / STYLE.name
shutil.copy2(STYLE, style_backup)

LIVE.parent.mkdir(parents=True, exist_ok=True)
staging = LIVE.parent / f"build.task-details-v2-11j-r3-staging-{stamp}"
live_backup = LIVE.parent / f"build.task-details-v2-11j-r3-backup-{stamp}"
live_swapped = False

try:
    STYLE.write_text(style_source.rstrip() + "\n\n" + payload_css.strip() + "\n")
    written_style = STYLE.read_text()
    if R3_RUNTIME not in written_style:
        fail("V2.11J_R3 runtime marker missing after stylesheet write")

    for path, expected in frozen_hashes.items():
        if sha256(path) != expected:
            fail(f"frozen source changed unexpectedly: {path}")

    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists() or not (DIST / "index.html").exists():
        fail("frontend dist missing after build")

    built_css = "\n".join(p.read_text(errors="ignore") for p in DIST.rglob("*.css"))
    if R3_RUNTIME not in built_css:
        fail("V2.11J_R3 runtime marker missing from built CSS")

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
    if R3_RUNTIME not in live_css:
        fail("V2.11J_R3 runtime marker missing from live CSS")

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
print("R2_BASELINE_PRESERVED=YES")
print("HERO_CONTROLS_SPECIFICITY_FIX=YES")
print("HERO_ASSIGNEE_DARK_OVERRIDE=YES")
print("HERO_STATUS_DARK_OVERRIDE=YES")
print("HERO_PRIORITY_DARK_OVERRIDE=YES")
print("HERO_DUE_DATE_DARK_OVERRIDE=YES")
print("PRIMARY_TABS_SPECIFICITY_FIX=YES")
print("PRIMARY_TABS_DARK_OVERRIDE=YES")
print("ACTIVE_TAB_GOLD_OVERRIDE=YES")
print("R1_RESPONSIVE_GEOMETRY_CHANGED=NO")
print("DESCRIPTION_CHANGED=NO")
print("RIGHT_RAIL_CHANGED=NO")
print("COMMENTS_LOGIC_CHANGED=NO")
print("TNC_ROUTING_CHANGED=NO")
print("WAITING_CLIENT_CHANGED=NO")
print("TCS_CHANGED=NO")
print("RAMZY_CHANGED=NO")
print("APP_JS_CHANGED=NO")
print("TASK_BOARD_JSX_CHANGED=NO")
print("BACKEND_CHANGED=NO")
print("API_CHANGED=NO")
print("DATABASE_CHANGED=NO")
print("PUSH=NO")
print("STATUS=READY_FOR_VISUAL_QA")
