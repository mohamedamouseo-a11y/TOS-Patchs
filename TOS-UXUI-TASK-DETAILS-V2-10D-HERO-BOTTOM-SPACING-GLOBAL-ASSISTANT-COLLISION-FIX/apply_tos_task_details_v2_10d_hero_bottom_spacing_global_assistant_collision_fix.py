from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import time

VERSION = "TOS_TASK_DETAILS_V2_10D"
PATCH_NAME = "TOS-UXUI-TASK-DETAILS-V2-10D-HERO-BOTTOM-SPACING-GLOBAL-ASSISTANT-COLLISION-FIX"
BASELINE_CHAIN = "TOS_TASK_DETAILS_V2_9D"

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
BOARD = FRONTEND / "src/components/ProfessionalTaskBoard.jsx"
APP = FRONTEND / "src/App.jsx"
TCS = FRONTEND / "src/components/TcsFloatingLauncher.jsx"
RAMZY = FRONTEND / "src/components/RamzyAssistant.jsx"
STYLE = FRONTEND / "src/styles/taskDetailsCanonicalReferenceV2.css"
MANIFEST = ROOT / "deployment/tos-production-runtime.json"
DIST = FRONTEND / "dist"
PATCH_DIR = Path(__file__).resolve().parent
PAYLOAD = PATCH_DIR / "taskDetailsV2_10DHeroBottomSpacingGlobalAssistantCollisionFix.css"

RUNTIME = "--tos-task-details-v2-10d-hero-bottom-spacing-global-assistant-collision-fix-runtime"
V29D_RUNTIME = "--tos-task-details-v2-9d-hero-internal-clip-bidi-cleanup-runtime"
V28D_RUNTIME = "--tos-task-details-v2-8d-right-rail-tcs-viewport-fit-runtime"
V27_RUNTIME = "--tos-task-details-canonical-reference-v2-7-real-overview-rail-physical-lock-runtime"
REQUIRED_LINEAGE = (
    "--tos-task-details-canonical-reference-v2-runtime",
    "--tos-task-details-canonical-reference-v2-2-app-shell-grid-lock-runtime",
    "--tos-task-details-canonical-reference-v2-5-exact-four-controls-physical-grid-runtime",
    "--tos-task-details-canonical-reference-v2-6-hero-visibility-physical-rail-runtime",
    V27_RUNTIME,
    V28D_RUNTIME,
    V29D_RUNTIME,
)


def fail(message):
    raise RuntimeError(message)


def run(command, cwd=None):
    subprocess.run(command, cwd=cwd, check=True)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


for required in (FRONTEND, BOARD, APP, TCS, RAMZY, STYLE, MANIFEST, PAYLOAD):
    if not required.exists():
        fail(f"required path missing: {required}")

for command in ("node", "npm"):
    if not shutil.which(command):
        fail(f"required command not found: {command}")

board_source = BOARD.read_text()
app_source = APP.read_text()
tcs_source = TCS.read_text()
ramzy_source = RAMZY.read_text()
style_source = STYLE.read_text()
payload_css = PAYLOAD.read_text()
source_hashes_before = {
    BOARD: sha256(BOARD),
    APP: sha256(APP),
    TCS: sha256(TCS),
    RAMZY: sha256(RAMZY),
}

# Guard the current V2.9D Task Details structure.
for marker in (
    "tos-task-details-reference-v2",
    "tos-task-details-fullpage",
    "tos-task-summary-compact",
    "tos-task-summary-controls",
    "tos-task-v2-assignees-card",
    "tos-task-reference-v2-rail",
    "tos-task-description-panel",
    "tos-task-v2-tcs-card",
):
    if marker not in board_source:
        fail(f"required Task Details marker missing: {marker}")

if "tos-task-assignees-hero-card" in board_source:
    fail("stale duplicate Assignees hero card unexpectedly present")

# Guard the real global assistant components/selectors used by the live screen.
for marker in (
    "TcsFloatingLauncher",
    "RamzyAssistant",
    "tos-premium-app-frame",
):
    if marker not in app_source:
        fail(f"required App assistant/frame marker missing: {marker}")
for marker in (
    "tcs-floating-launcher-root",
    "tcs-floating-launcher",
    "data-testid=\"tcs-floating-launcher\"",
):
    if marker not in tcs_source:
        fail(f"required TCS launcher marker missing: {marker}")
for marker in (
    "ramzy-assistant-root",
    "ramzy-launcher-wrap",
    "ramzy-launcher-label",
    "ramzy-greeting",
    "ramzy-avatar-ring",
):
    if marker not in ramzy_source:
        fail(f"required Ramzy launcher marker missing: {marker}")

for marker in REQUIRED_LINEAGE:
    if marker not in style_source:
        fail(f"required lineage runtime missing: {marker}")
if RUNTIME in style_source:
    fail("V2.10D already applied")

# Confirm the exact visual baseline being repaired.
for marker in (
    "--tos-v23-hero-height: 236px",
    "transform: translateY(-20px)",
    "--tos-v28d-rail-gap",
    "--tos-v29d-control-box-height",
):
    if marker not in style_source:
        fail(f"required V2.9D visual baseline marker missing: {marker}")

if RUNTIME not in payload_css:
    fail("V2.10D runtime marker missing from payload")
for required_selector in (
    ".tos-task-summary-compact",
    ".tos-task-reference-v2-rail",
    ".tcs-floating-launcher",
    ".ramzy-launcher-wrap",
    ".ramzy-avatar-ring",
):
    if required_selector not in payload_css:
        fail(f"required V2.10D selector missing from payload: {required_selector}")

# Freeze approved Task Details content and all assistant internals/logic.
for forbidden in (
    ".tos-task-v2-quick-actions",
    ".tos-task-v2-info-card",
    ".tos-task-v2-tags",
    ".tos-task-v2-tcs-card",
    ".tos-task-description-panel",
    ".tos-task-detail-tabs",
    ".tos-task-title-input",
    ".tos-task-header-description",
    ".tcs-desktop-window",
    ".ramzy-panel",
    ".ramzy-messages",
    ".ramzy-composer",
):
    if forbidden in payload_css:
        fail(f"V2.10D payload illegally touches frozen scope: {forbidden}")

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
backup_root = Path(f"/var/backups/tos-patches/task-details-v2-10d-visual-collision-{stamp}")
backup_root.mkdir(parents=True, exist_ok=False)
style_backup = backup_root / STYLE.name
shutil.copy2(STYLE, style_backup)

live.parent.mkdir(parents=True, exist_ok=True)
staging = live.parent / f"build.task-details-v2-10d-staging-{stamp}"
live_backup = live.parent / f"build.task-details-v2-10d-backup-{stamp}"
live_swapped = False

try:
    STYLE.write_text(style_source.rstrip() + "\n\n" + payload_css.strip() + "\n")
    updated_style = STYLE.read_text()
    for marker in (*REQUIRED_LINEAGE, RUNTIME):
        if marker not in updated_style:
            fail(f"runtime marker missing after stylesheet update: {marker}")

    # CSS-only means all React sources must remain byte-identical.
    for path, before_hash in source_hashes_before.items():
        if sha256(path) != before_hash:
            fail(f"source changed during CSS-only V2.10D patch: {path}")

    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists() or not (DIST / "index.html").exists():
        fail("frontend dist missing after build")

    built_css = "\n".join(path.read_text(errors="ignore") for path in DIST.rglob("*.css"))
    built_js = "\n".join(path.read_text(errors="ignore") for path in DIST.rglob("*.js"))
    for marker in (*REQUIRED_LINEAGE, RUNTIME):
        if marker not in built_css:
            fail(f"runtime marker missing from built CSS: {marker}")
    for marker in (
        "tos-task-summary-controls",
        "tos-task-reference-v2-rail",
        "tcs-floating-launcher",
        "ramzy-launcher-wrap",
        "tos-task-v2-tcs-card",
    ):
        if marker not in built_js:
            fail(f"required live marker missing from built JS: {marker}")

    if staging.exists():
        shutil.rmtree(staging)
    shutil.copytree(DIST, staging)
    if live.exists():
        live.rename(live_backup)
    staging.rename(live)
    live_swapped = True

    live_css = "\n".join(path.read_text(errors="ignore") for path in live.rglob("*.css"))
    live_js = "\n".join(path.read_text(errors="ignore") for path in live.rglob("*.js"))
    if RUNTIME not in live_css or V29D_RUNTIME not in live_css:
        fail("V2.10D/V2.9D runtime marker missing from live CSS")
    for marker in ("tcs-floating-launcher", "ramzy-launcher-wrap", "tos-task-reference-v2-rail"):
        if marker not in live_js:
            fail(f"required marker missing from live JS: {marker}")

    print(f"VERSION={VERSION}")
    print(f"PATCH={PATCH_NAME}")
    print(f"BASELINE_CHAIN={BASELINE_CHAIN}")
    print("PASS/FAIL=PASS")
    print("BUILD_RESULT=PASS")
    print("LIVE_DEPLOY=PASS")
    print("HERO_BOTTOM_BREATHING_ROOM=TARGET_FIXED")
    print("GLOBAL_TCS_TASK_DETAILS_DOCK=TARGET_FIXED")
    print("GLOBAL_RAMZY_TASK_DETAILS_DOCK=TARGET_FIXED")
    print("OVERVIEW_CONTENT=PRESERVED")
    print("TASK_DETAILS_TCS_CARD=PRESERVED")
    print("ASSISTANT_LOGIC_CHANGED=NO")
    print("REACT_SOURCE_CHANGED=NO")
    print("REFERENCE_VIEWPORT=1664x936")
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
    print(f"VERSION={VERSION}")
    print(f"PATCH={PATCH_NAME}")
    print(f"BASELINE_CHAIN={BASELINE_CHAIN}")
    print("PASS/FAIL=FAIL")
    print(f"ERROR={exc}")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("STATUS=STOPPED")
    raise SystemExit(1)
