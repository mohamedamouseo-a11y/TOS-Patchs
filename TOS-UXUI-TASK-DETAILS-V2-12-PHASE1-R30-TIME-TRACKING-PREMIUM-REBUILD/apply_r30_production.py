from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import time

PATCH = "TOS-UXUI-TASK-DETAILS-V2-12-PHASE1-R30-TIME-TRACKING-PREMIUM-REBUILD"
VERSION = "TOS_TASK_DETAILS_V2_12_PHASE1_R30"
BASE_TOS_COMMIT = "dc1357a5dcf64000d42dcb98da3df8577efdb0ae"
R29_MARKER = "--tos-task-details-v2-12-phase1-r29-remove-legacy-side-details-runtime"
R30_MARKER = "--tos-task-details-v2-12-phase1-r30-time-tracking-premium-runtime"
R30_HOOK = "tos-task-time-tracking-panel"

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
STYLE_DIR = FRONTEND / "src/styles"
BOARD = FRONTEND / "src/components/ProfessionalTaskBoard.jsx"
APP = FRONTEND / "src/App.jsx"
SIDEBAR = FRONTEND / "src/components/layout/Sidebar.jsx"
R29_STYLE = STYLE_DIR / "taskDetailsV2_12_Phase1R29RemoveLegacySideDetails.css"
R30_STYLE = STYLE_DIR / "taskDetailsV2_12_Phase1R30TimeTrackingPremium.css"
MANIFEST = ROOT / "deployment/tos-production-runtime.json"
PAYLOAD = Path(__file__).resolve().parent / "taskDetailsV2_12_Phase1R30TimeTrackingPremium.css"


def fail(message):
    raise RuntimeError(message)


def run(command, cwd=None):
    subprocess.run(command, cwd=cwd, check=True)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


for path in (FRONTEND, STYLE_DIR, BOARD, APP, SIDEBAR, R29_STYLE, MANIFEST, PAYLOAD):
    if not path.exists():
        fail(f"required path missing: {path}")
for command in ("node", "npm"):
    if not shutil.which(command):
        fail(f"required command missing: {command}")

board_source = BOARD.read_text()
r29_source = R29_STYLE.read_text()
payload_css = PAYLOAD.read_text()

if R29_MARKER not in r29_source:
    fail("R29 production baseline marker missing")
if R30_MARKER not in payload_css:
    fail("R30 payload marker missing")
if R30_STYLE.exists():
    fail("R30 stylesheet already exists")
if R30_HOOK in board_source:
    fail("R30 Time Tracking hook already exists")

# Latest-code functional contracts. These must stay untouched by R30.
for contract in (
    'activeTaskTab === "time"',
    "updateEstimatedHours",
    "startTimeTimer",
    "pauseTimeTimer",
    "stopTimeTimer",
    "cancelTimeTimer",
    "addManualTimeEntry",
    "liveTrackedHours",
    "timeBudget.overBy",
):
    if contract not in board_source:
        fail(f"latest Time Tracking contract missing: {contract}")

r29_import = 'import "../styles/taskDetailsV2_12_Phase1R29RemoveLegacySideDetails.css";'
r30_import = 'import "../styles/taskDetailsV2_12_Phase1R30TimeTrackingPremium.css";'
if board_source.count(r29_import) != 1:
    fail(f"expected exactly one R29 import, found {board_source.count(r29_import)}")
if r30_import in board_source:
    fail("R30 import already exists")

old_time_anchor = '''{activeTaskTab === "time" && (
              <section className="rounded-[32px] border border-slate-200 bg-white p-5 shadow-sm shadow-slate-100/80 dark:border-white/10 dark:bg-zinc-950 dark:shadow-black/20">'''
new_time_anchor = '''{activeTaskTab === "time" && (
              <section className="tos-task-time-tracking-panel rounded-[32px] border border-slate-200 bg-white p-5 shadow-sm shadow-slate-100/80 dark:border-white/10 dark:bg-zinc-950 dark:shadow-black/20">'''

if board_source.count(old_time_anchor) != 1:
    fail(f"expected exactly one current Time Tracking section anchor, found {board_source.count(old_time_anchor)}")

updated = board_source.replace(r29_import, r29_import + "\n" + r30_import, 1)
updated = updated.replace(old_time_anchor, new_time_anchor, 1)

if updated.count(r30_import) != 1 or updated.count(R30_HOOK) != 1:
    fail("R30 source transformation verification failed")

# Guard functional source: only the import + one semantic class hook may differ.
functional_contracts = (
    "updateEstimatedHours",
    "startTimeTimer",
    "pauseTimeTimer",
    "stopTimeTimer",
    "cancelTimeTimer",
    "addManualTimeEntry",
)
for contract in functional_contracts:
    if board_source.count(contract) != updated.count(contract):
        fail(f"functional contract count changed unexpectedly: {contract}")

for contract in (
    R30_MARKER,
    ".tos-task-time-tracking-panel",
    "grid-template-columns:minmax(230px,1fr) 300px minmax(230px,1fr)",
    "html.dark",
    "@media (min-width:1180px) and (max-width:1440px)",
    "@media (max-width:1179px)",
):
    if contract not in payload_css:
        fail(f"R30 CSS contract missing: {contract}")

manifest = json.loads(MANIFEST.read_text())
if manifest.get("application") != "TOS" or manifest.get("environment") != "production":
    fail("unexpected production runtime manifest")
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

app_hash = sha256(APP)
sidebar_hash = sha256(SIDEBAR)
prior_styles = sorted(p for p in STYLE_DIR.glob("taskDetailsV2_12_Phase1*.css") if p != R30_STYLE)
prior_style_hashes = {p: sha256(p) for p in prior_styles}

stamp = int(time.time())
backup_root = Path(f"/var/backups/tos-patches/task-details-v2-12-phase1-r30-{stamp}")
backup_root.mkdir(parents=True, exist_ok=False)
shutil.copy2(BOARD, backup_root / BOARD.name)

LIVE.parent.mkdir(parents=True, exist_ok=True)
staging = LIVE.parent / f"build.task-details-r30-staging-{stamp}"
live_backup = LIVE.parent / f"build.task-details-r30-backup-{stamp}"
live_swapped = False
r30_written = False

try:
    BOARD.write_text(updated)
    R30_STYLE.write_text(payload_css.rstrip() + "\n")
    r30_written = True

    written_board = BOARD.read_text()
    if written_board.count(r30_import) != 1 or written_board.count(R30_HOOK) != 1:
        fail("R30 source hook/import missing after write")
    if sha256(APP) != app_hash or sha256(SIDEBAR) != sidebar_hash:
        fail("app shell changed unexpectedly")
    for path, digest in prior_style_hashes.items():
        if sha256(path) != digest:
            fail(f"prior Phase1 stylesheet changed unexpectedly: {path.name}")

    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists() or not (DIST / "index.html").exists():
        fail("frontend dist missing after build")

    built_css = "\n".join(p.read_text(errors="ignore") for p in DIST.rglob("*.css"))
    built_js = "\n".join(p.read_text(errors="ignore") for p in DIST.rglob("*.js"))
    if R29_MARKER not in built_css or R30_MARKER not in built_css:
        fail("R29/R30 runtime marker missing from build")
    if R30_HOOK not in built_js:
        fail("R30 Time Tracking semantic hook missing from built JS")

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
    live_js = "\n".join(p.read_text(errors="ignore") for p in LIVE.rglob("*.js"))
    if R29_MARKER not in live_css or R30_MARKER not in live_css:
        fail("R29/R30 runtime marker missing from live build")
    if R30_HOOK not in live_js:
        fail("R30 Time Tracking semantic hook missing from live JS")

    if sha256(APP) != app_hash or sha256(SIDEBAR) != sidebar_hash:
        fail("app shell changed after deploy")
    for path, digest in prior_style_hashes.items():
        if sha256(path) != digest:
            fail(f"prior Phase1 stylesheet changed after deploy: {path.name}")

except Exception:
    shutil.copy2(backup_root / BOARD.name, BOARD)
    if r30_written and R30_STYLE.exists():
        R30_STYLE.unlink()
    if live_swapped:
        if LIVE.exists():
            shutil.rmtree(LIVE)
        if live_backup.exists():
            live_backup.rename(LIVE)
    elif staging.exists():
        shutil.rmtree(staging)
    raise

print(f"VERSION={VERSION}")
print(f"PATCH_APPLIED={PATCH}")
print(f"BASE_TOS_COMMIT_REVIEWED={BASE_TOS_COMMIT}")
print("BUILD_STATUS=PASS")
print("DEPLOY_STATUS=PASS")
print("TIME_TRACKING_PREMIUM_REBUILD=YES")
print("TIME_TRACKING_LOGIC_CHANGED=NO")
print("TIMER_FUNCTIONS_CHANGED=NO")
print("PERMISSIONS_CHANGED=NO")
print("BACKEND_CHANGED=NO")
print("DATABASE_CHANGED=NO")
print("R29_PRESERVED=YES")
print("RIGHT_RAIL_CHANGED=NO")
print("TCS_CHANGED=NO")
print("RAMZY_CHANGED=NO")
print("PUSH=NO")
print("STATUS=READY_FOR_VISUAL_QA")
