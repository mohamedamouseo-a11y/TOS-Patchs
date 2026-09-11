from pathlib import Path
import json
import shutil
import subprocess
import sys
import time

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
BOARD = FRONTEND / "src/components/ProfessionalTaskBoard.jsx"
STYLE_DIR = FRONTEND / "src/styles"
MANIFEST = ROOT / "deployment/tos-production-runtime.json"
DIST = FRONTEND / "dist"
PATCH_DIR = Path(__file__).resolve().parent
PAYLOAD_STYLE = PATCH_DIR / "taskDetailsCanonicalReferenceV2_6HeroVisibilityPhysicalRailFix.css"

RUNTIME = "--tos-task-details-canonical-reference-v2-6-hero-visibility-physical-rail-runtime"
V2_5_RUNTIME = "--tos-task-details-canonical-reference-v2-5-exact-four-controls-physical-grid-runtime"
V2_4_RUNTIME = "--tos-task-details-canonical-reference-v2-4-four-control-overview-order-runtime"
V2_3_RUNTIME = "--tos-task-details-canonical-reference-v2-3-internal-fidelity-runtime"
V2_2_RUNTIME = "--tos-task-details-canonical-reference-v2-2-app-shell-grid-lock-runtime"
V2_1_RUNTIME = "--tos-task-details-canonical-reference-v2-1-rtl-structural-geometry-runtime"
V2_RUNTIME_MARKERS = (
    "--tos-task-details-canonical-reference-v2-runtime",
    "--tos-task-details-canonical-v2-runtime",
)


def fail(message):
    raise RuntimeError(message)


def run(command, cwd=None):
    subprocess.run(command, cwd=cwd, check=True)


for required in (FRONTEND, BOARD, STYLE_DIR, MANIFEST, PAYLOAD_STYLE):
    if not required.exists():
        fail(f"required path missing: {required}")

for command in ("node", "npm"):
    if not shutil.which(command):
        fail(f"required command not found: {command}")

payload_css = PAYLOAD_STYLE.read_text()
if RUNTIME not in payload_css:
    fail("V2.6 CSS runtime marker missing from payload")

# V2.6 is intentionally presentation-only. It must not reopen the approved
# outer shell/topbar/breadcrumb/tabs logic or touch application contracts.
for forbidden in (
    ".tos-premium-sidebar",
    ".tos-premium-app-frame",
    ".tos-premium-main-shell",
    ".tos-premium-topbar",
    ".tos-task-detail-tabs",
    ".tos-task-reference-tabs-main",
    "tasksApi.",
    "fetch(",
    "axios",
    "localStorage",
):
    if forbidden in payload_css:
        fail(f"V2.6 payload illegally touches preserved scope: {forbidden}")

for selector in (
    ".tos-task-details-fullpage .tos-task-details-layout",
    ".tos-task-details-fullpage .tos-task-main-column",
    ".tos-task-details-fullpage .tos-task-side-rail",
    ".tos-task-details-fullpage .tos-task-summary-controls",
    ".tos-task-start-date-card",
):
    if selector not in payload_css:
        fail(f"required V2.6 selector missing from payload: {selector}")

board_source = BOARD.read_text()
for marker in (
    "tos-task-details-fullpage",
    "tos-task-details-reference-v1",
    'data-content-dir={modalDirection}',
    "tos-task-details-layout",
    "tos-task-main-column",
    "tos-task-side-rail",
    "tos-task-summary-compact",
    "tos-task-summary-controls",
    "tos-task-start-date-card",
    "tos-task-description-panel",
    "PremiumTaskRichTextEditor",
):
    if marker not in board_source:
        fail(f"required current Task Details marker missing: {marker}")

# V2.5 must already have removed the duplicate Assignees card and locked the
# JSX/Tailwind geometry. V2.6 does not mutate JSX again.
if "tos-task-assignees-hero-card" in board_source:
    fail("V2.5 duplicate Assignees card still present; refusing V2.6")
for marker in (
    "xl:grid-cols-[minmax(0,1fr)_304px]",
    "tos-task-main-column min-w-0 space-y-4 text-right xl:order-1",
    "tos-task-side-rail min-w-0 space-y-5 text-right xl:order-2",
):
    if marker not in board_source:
        fail(f"required V2.5 physical-grid source marker missing: {marker}")

# Locate the one canonical stylesheet containing the complete V2 -> V2.5 lineage.
v2_candidates = []
for path in STYLE_DIR.rglob("*.css"):
    text = path.read_text(errors="ignore")
    if RUNTIME in text:
        fail(f"V2.6 already applied in {path}")
    if (
        V2_5_RUNTIME in text
        and V2_4_RUNTIME in text
        and V2_3_RUNTIME in text
        and V2_2_RUNTIME in text
        and V2_1_RUNTIME in text
        and any(marker in text for marker in V2_RUNTIME_MARKERS)
    ):
        v2_candidates.append(path)

if len(v2_candidates) != 1:
    fail(
        "unable to identify exactly one V2 through V2.5 stylesheet: "
        + ", ".join(str(path) for path in v2_candidates)
    )
v2_style = v2_candidates[0]
original_css = v2_style.read_text()

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
backup_root = Path(
    f"/var/backups/tos-patches/task-details-canonical-reference-v2-6-hero-visibility-physical-rail-{stamp}"
)
backup_root.mkdir(parents=True, exist_ok=False)
style_backup = backup_root / v2_style.name
shutil.copy2(v2_style, style_backup)

live.parent.mkdir(parents=True, exist_ok=True)
staging = live.parent / f"build.task-details-canonical-reference-v2-6-staging-{stamp}"
live_backup = live.parent / f"build.task-details-canonical-reference-v2-6-backup-{stamp}"
live_swapped = False

try:
    # CSS-only correction. Do not mutate ProfessionalTaskBoard.jsx.
    board_before = BOARD.read_bytes()
    v2_style.write_text(original_css.rstrip() + "\n\n" + payload_css.strip() + "\n")
    updated_css = v2_style.read_text()

    for marker in (
        RUNTIME,
        V2_5_RUNTIME,
        V2_4_RUNTIME,
        V2_3_RUNTIME,
        V2_2_RUNTIME,
        V2_1_RUNTIME,
    ):
        if marker not in updated_css:
            fail(f"required runtime marker missing after CSS update: {marker}")

    if BOARD.read_bytes() != board_before:
        fail("ProfessionalTaskBoard.jsx changed during CSS-only V2.6")

    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists() or not (DIST / "index.html").exists():
        fail("frontend dist missing after build")

    built_css = "\n".join(path.read_text(errors="ignore") for path in DIST.rglob("*.css"))
    built_js = "\n".join(path.read_text(errors="ignore") for path in DIST.rglob("*.js"))

    for marker in (
        RUNTIME,
        V2_5_RUNTIME,
        V2_4_RUNTIME,
        V2_3_RUNTIME,
        V2_2_RUNTIME,
        V2_1_RUNTIME,
    ):
        if marker not in built_css:
            fail(f"required runtime marker missing from built CSS: {marker}")

    for marker in (
        "tos-task-details-fullpage",
        "tos-task-details-reference-v1",
        "data-content-dir",
        "tos-task-summary-controls",
        "tos-task-start-date-card",
        "tos-task-description-panel",
    ):
        if marker not in built_js:
            fail(f"required Task Details marker missing from built JS: {marker}")
    if "tos-task-assignees-hero-card" in built_js:
        fail("removed V2.4 duplicate Assignees card reappeared in built JS")

    if staging.exists():
        shutil.rmtree(staging)
    shutil.copytree(DIST, staging)
    if live.exists():
        live.rename(live_backup)
    staging.rename(live)
    live_swapped = True

    live_css = "\n".join(path.read_text(errors="ignore") for path in live.rglob("*.css"))
    live_js = "\n".join(path.read_text(errors="ignore") for path in live.rglob("*.js"))
    if RUNTIME not in live_css or V2_5_RUNTIME not in live_css:
        fail("V2.6/V2.5 markers missing from live build")
    if "tos-task-details-fullpage" not in live_js or "tos-task-description-panel" not in live_js:
        fail("Task Details structural markers missing from live JS")
    if "tos-task-assignees-hero-card" in live_js:
        fail("removed V2.4 duplicate Assignees card reappeared in live JS")

    print("PASS/FAIL=PASS")
    print("BUILD_RESULT=PASS")
    print("LIVE_DEPLOY=PASS")
    print("TASK_DETAILS_CANONICAL_REFERENCE_V2_6_RUNTIME=YES")
    print("V2_2_APP_SHELL_LOCK=PRESERVED")
    print("V2_2_STRUCTURAL_LTR=PRESERVED")
    print("V2_3_HERO_CONTAINER_GEOMETRY=PRESERVED")
    print("V2_3_TABS_PLACEMENT_LOGIC=PRESERVED")
    print("V2_4_START_DATE_ADVANCED_PATH=PRESERVED")
    print("V2_5_EXACT_FOUR_CONTROLS=PRESERVED")
    print("HERO_PRIMARY_CONTROLS_VISIBILITY=COMPACTED_AND_LIFTED")
    print("HERO_PRIMARY_CONTROLS=ASSIGNEES_STATUS_PRIORITY_DUE_DATE")
    print("OVERVIEW_LAYOUT_ENGINE=PHYSICAL_LTR_FLEX_LOCK")
    print("OVERVIEW_PHYSICAL_ORDER=DESCRIPTION_LEFT_RIGHT_RAIL_RIGHT")
    print("RIGHT_RAIL_WIDTH=304PX")
    print("RIGHT_RAIL_DENSITY=COMPACTED_PRESERVING_CONTENT")
    print("RIGHT_RAIL_CONTENT=UNCHANGED")
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
    print(f"V2_STYLE_TARGET={v2_style}")
    print(f"SOURCE_BACKUP={backup_root}")
    print(f"LIVE_BACKUP={live_backup if live_backup.exists() else 'NONE'}")
    print("STATUS=READY_FOR_VISUAL_QA")
except Exception as exc:
    try:
        if style_backup.exists():
            shutil.copy2(style_backup, v2_style)
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
