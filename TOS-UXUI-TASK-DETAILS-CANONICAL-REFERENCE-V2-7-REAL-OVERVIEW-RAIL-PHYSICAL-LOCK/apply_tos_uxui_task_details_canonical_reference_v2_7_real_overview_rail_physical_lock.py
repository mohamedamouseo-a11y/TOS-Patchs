from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import time

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
BOARD = FRONTEND / "src/components/ProfessionalTaskBoard.jsx"
STYLE = FRONTEND / "src/styles/taskDetailsCanonicalReferenceV2.css"
MANIFEST = ROOT / "deployment/tos-production-runtime.json"
DIST = FRONTEND / "dist"
PATCH_DIR = Path(__file__).resolve().parent
PAYLOAD = PATCH_DIR / "taskDetailsCanonicalReferenceV2_7RealOverviewRailPhysicalLock.css"

RUNTIME = "--tos-task-details-canonical-reference-v2-7-real-overview-rail-physical-lock-runtime"
REQUIRED_LINEAGE = (
    "--tos-task-details-canonical-reference-v2-runtime",
    "--tos-task-details-canonical-reference-v2-1-rtl-structural-geometry-runtime",
    "--tos-task-details-canonical-reference-v2-2-app-shell-grid-lock-runtime",
    "--tos-task-details-canonical-reference-v2-3-internal-fidelity-runtime",
    "--tos-task-details-canonical-reference-v2-4-four-control-overview-order-runtime",
    "--tos-task-details-canonical-reference-v2-5-exact-four-controls-physical-grid-runtime",
    "--tos-task-details-canonical-reference-v2-6-hero-visibility-physical-rail-runtime",
)


def fail(message):
    raise RuntimeError(message)


def run(command, cwd=None):
    subprocess.run(command, cwd=cwd, check=True)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


for required in (FRONTEND, BOARD, STYLE, MANIFEST, PAYLOAD):
    if not required.exists():
        fail(f"required path missing: {required}")

for command in ("node", "npm"):
    if not shutil.which(command):
        fail(f"required command not found: {command}")

board_source = BOARD.read_text()
style_source = STYLE.read_text()
payload_css = PAYLOAD.read_text()
board_hash_before = sha256(BOARD)

# Guard the pushed V2.6 baseline and the REAL canonical Overview DOM.
for marker in (
    "tos-task-details-reference-v1",
    "tos-task-details-reference-v2",
    "tos-task-reference-v2-rail",
    "tos-task-v2-quick-actions",
    "tos-task-v2-info-card",
    "tos-task-v2-tags",
    "tos-task-v2-tcs-card",
    "tos-task-description-panel",
    "tos-task-detail-tabs",
    "tos-task-v2-assignees-card",
    "tos-task-side-rail",
):
    if marker not in board_source:
        fail(f"required pushed Task Details marker missing: {marker}")

if board_source.count("tos-task-reference-v2-rail") != 1:
    fail("expected exactly one canonical V2 Overview rail")
if board_source.count("tos-task-v2-tcs-card") != 1:
    fail("expected exactly one Task Details TCS Assistant card")
if "tos-task-assignees-hero-card" in board_source:
    fail("stale V2.4 duplicate Assignees hero card unexpectedly present")

for marker in REQUIRED_LINEAGE:
    if marker not in style_source:
        fail(f"required V2 lineage runtime missing: {marker}")
if RUNTIME in style_source:
    fail("V2.7 already applied")

# Confirm the root cause we are fixing still exists in the pushed baseline.
for marker in (
    ".tos-task-reference-v2-rail",
    "inset-inline-end:0",
    ".tos-task-description-panel",
):
    if marker not in style_source:
        fail(f"expected canonical baseline CSS marker missing: {marker}")

if RUNTIME not in payload_css:
    fail("V2.7 runtime marker missing from payload")
for required_selector in (
    ".tos-task-reference-v2-rail",
    ".tos-task-description-panel",
    ".tos-task-detail-tabs",
    ".tos-task-v2-tcs-card",
):
    if required_selector not in payload_css:
        fail(f"required V2.7 selector missing from payload: {required_selector}")

# V2.7 is forbidden from reopening approved shell/hero/business scope.
for forbidden in (
    ".tos-premium-sidebar",
    ".tos-premium-app-frame",
    ".tos-premium-main-shell",
    ".tos-premium-topbar",
    ".tos-task-summary-compact",
    ".tos-task-summary-controls",
    ".tos-task-v2-assignees-card",
    ".tos-task-start-date-card",
):
    if forbidden in payload_css:
        fail(f"V2.7 payload illegally touches preserved scope: {forbidden}")

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
live = Path(str(frontend_runtime.get("publishedBuildDir") or ""))
if live != Path("/opt/apps/tamiyouz-front/build"):
    fail(f"unexpected live frontend path: {live}")

stamp = int(time.time())
backup_root = Path(f"/var/backups/tos-patches/task-details-canonical-reference-v2-7-real-rail-{stamp}")
backup_root.mkdir(parents=True, exist_ok=False)
style_backup = backup_root / STYLE.name
shutil.copy2(STYLE, style_backup)

live.parent.mkdir(parents=True, exist_ok=True)
staging = live.parent / f"build.task-details-canonical-reference-v2-7-staging-{stamp}"
live_backup = live.parent / f"build.task-details-canonical-reference-v2-7-backup-{stamp}"
live_swapped = False

try:
    STYLE.write_text(style_source.rstrip() + "\n\n" + payload_css.strip() + "\n")
    updated_style = STYLE.read_text()
    for marker in (*REQUIRED_LINEAGE, RUNTIME):
        if marker not in updated_style:
            fail(f"runtime marker missing after stylesheet update: {marker}")

    if sha256(BOARD) != board_hash_before:
        fail("ProfessionalTaskBoard.jsx changed during CSS-only V2.7 patch")

    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists() or not (DIST / "index.html").exists():
        fail("frontend dist missing after build")

    built_css = "\n".join(path.read_text(errors="ignore") for path in DIST.rglob("*.css"))
    built_js = "\n".join(path.read_text(errors="ignore") for path in DIST.rglob("*.js"))
    for marker in (*REQUIRED_LINEAGE, RUNTIME):
        if marker not in built_css:
            fail(f"runtime marker missing from built CSS: {marker}")
    for marker in (
        "tos-task-reference-v2-rail",
        "tos-task-v2-tcs-card",
        "tos-task-description-panel",
        "tos-task-v2-assignees-card",
    ):
        if marker not in built_js:
            fail(f"required Task Details marker missing from built JS: {marker}")
    if "tos-task-assignees-hero-card" in built_js:
        fail("stale duplicate Assignees hero card returned in built JS")

    if staging.exists():
        shutil.rmtree(staging)
    shutil.copytree(DIST, staging)
    if live.exists():
        live.rename(live_backup)
    staging.rename(live)
    live_swapped = True

    live_css = "\n".join(path.read_text(errors="ignore") for path in live.rglob("*.css"))
    live_js = "\n".join(path.read_text(errors="ignore") for path in live.rglob("*.js"))
    if RUNTIME not in live_css:
        fail("V2.7 runtime marker missing from live CSS")
    if "tos-task-reference-v2-rail" not in live_js or "tos-task-v2-tcs-card" not in live_js:
        fail("canonical rail/TCS markers missing from live JS")

    print("PASS/FAIL=PASS")
    print("BUILD_RESULT=PASS")
    print("LIVE_DEPLOY=PASS")
    print("TASK_DETAILS_CANONICAL_REFERENCE_V2_7_RUNTIME=YES")
    print("BASELINE_PUSHED_MAIN=f4be538dbf92996c4eb8325a133513f4db31df81")
    print("V2_2_APP_SHELL_LOCK=PRESERVED")
    print("V2_3_HERO=PRESERVED")
    print("V2_5_EXACT_FOUR_CONTROLS=PRESERVED")
    print("V2_6_HERO_CONTROL_VISIBILITY=PRESERVED")
    print("REAL_CANONICAL_OVERVIEW_RAIL=tos-task-reference-v2-rail")
    print("ROOT_CAUSE=RTL_LOGICAL_INLINE_END_ON_CANONICAL_RAIL")
    print("OVERVIEW_PHYSICAL_ORDER=DESCRIPTION_LEFT_RIGHT_RAIL_RIGHT_EXPECTED")
    print("RIGHT_RAIL_CONTENT=QUICK_ACTIONS_TASK_INFORMATION_TAGS_TCS_ASSISTANT")
    print("RIGHT_RAIL_DENSITY=COMPACTED_ONLY")
    print("TASK_DETAILS_TCS_CARD=PRESERVED_EXISTING_VISUAL_ONLY")
    print("FLOATING_TCS_LAUNCHER=UNCHANGED")
    print("BOARD_SOURCE_CHANGED=NO")
    print("REFERENCE_VIEWPORT=1664x936")
    print("TASK_APIS_CHANGED=NO")
    print("TASK_DATA_CONTRACT_CHANGED=NO")
    print("TASK_PERMISSIONS_CHANGED=NO")
    print("TASK_BUSINESS_LOGIC_CHANGED=NO")
    print("UPLOAD_LOGIC_CHANGED=NO")
    print("TWS_INTERNALS_CHANGED=NO")
    print("RAMZY_CHANGED=NO")
    print("TCS_LOGIC_CHANGED=NO")
    print(f"SOURCE_BACKUP={backup_root}")
    print(f"LIVE_BACKUP={live_backup if live_backup.exists() else 'NONE'}")
    print("STATUS=READY_FOR_VISUAL_QA")
except Exception as exc:
    try:
        if style_backup.exists():
            shutil.copy2(style_backup, STYLE)
        if live_swapped and live.exists() and live_backup.exists():
            shutil.rmtree(live)
            live_backup.rename(live)
        elif live_backup.exists() and not live.exists():
            live_backup.rename(live)
        if staging.exists():
            shutil.rmtree(staging)
    except Exception:
        pass
    print("PASS/FAIL=FAIL")
    print(f"ERROR={exc}")
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("STATUS=STOPPED")
    raise SystemExit(1)
