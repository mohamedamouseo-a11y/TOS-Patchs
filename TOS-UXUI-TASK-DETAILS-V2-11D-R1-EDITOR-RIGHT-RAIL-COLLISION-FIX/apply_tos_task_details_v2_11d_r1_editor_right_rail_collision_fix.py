from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import time

VERSION = "TOS_TASK_DETAILS_V2_11D_R1"
PATCH_NAME = "TOS-UXUI-TASK-DETAILS-V2-11D-R1-EDITOR-RIGHT-RAIL-COLLISION-FIX"
BASELINE_CHAIN = "TOS_TASK_DETAILS_V2_11D"
MICRO_STEP = "EDITOR_RIGHT_RAIL_COLLISION_FIX_ONLY"

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
BOARD = FRONTEND / "src/components/ProfessionalTaskBoard.jsx"
PARTS = FRONTEND / "src/features/tasks/taskBoardParts.jsx"
STYLE = FRONTEND / "src/styles/taskDetailsCanonicalReferenceV2.css"
MANIFEST = ROOT / "deployment/tos-production-runtime.json"
DIST = FRONTEND / "dist"
PATCH_DIR = Path(__file__).resolve().parent
PAYLOAD = PATCH_DIR / "taskDetailsV2_11DR1EditorRightRailCollisionFix.css"

RUNTIME = "--tos-task-details-v2-11d-r1-editor-right-rail-collision-fix-runtime"
D_RUNTIME = "--tos-task-details-v2-11d-description-editor-premium-lock-runtime"
C_RUNTIME = "--tos-task-details-v2-11c-primary-tabs-premium-lock-runtime"
B3_RUNTIME = "--tos-task-details-v2-11b3-assignees-custom-selector-runtime"

REQUIRED_LINEAGE = (
    "--tos-task-details-canonical-reference-v2-runtime",
    "--tos-task-details-canonical-reference-v2-2-app-shell-grid-lock-runtime",
    "--tos-task-details-canonical-reference-v2-5-exact-four-controls-physical-grid-runtime",
    "--tos-task-details-canonical-reference-v2-6-hero-visibility-physical-rail-runtime",
    "--tos-task-details-canonical-reference-v2-7-real-overview-rail-physical-lock-runtime",
    "--tos-task-details-v2-8d-right-rail-tcs-viewport-fit-runtime",
    "--tos-task-details-v2-9d-hero-internal-clip-bidi-cleanup-runtime",
    "--tos-task-details-v2-10d-hero-bottom-spacing-global-assistant-collision-fix-runtime",
    "--tos-task-details-v2-11a-hero-shell-task-identity-lock-runtime",
    "--tos-task-details-v2-11a-r1-hero-full-canvas-physical-placement-runtime",
    "--tos-task-details-v2-11a-r2-hero-width-only-runtime",
    "--tos-task-details-v2-11b-four-hero-controls-premium-lock-runtime",
    "--tos-task-details-v2-11b1-status-priority-custom-dropdowns-runtime",
    "--tos-task-details-v2-11b2-due-date-custom-premium-calendar-runtime",
    B3_RUNTIME,
    C_RUNTIME,
    D_RUNTIME,
)


def fail(message):
    raise RuntimeError(message)


def run(command, cwd=None):
    subprocess.run(command, cwd=cwd, check=True)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


for required in (FRONTEND, BOARD, PARTS, STYLE, MANIFEST, PAYLOAD):
    if not required.exists():
        fail(f"required path missing: {required}")
for command in ("node", "npm"):
    if not shutil.which(command):
        fail(f"required command not found: {command}")

board_source = BOARD.read_text()
parts_source = PARTS.read_text()
style_source = STYLE.read_text()
payload_css = PAYLOAD.read_text()
board_hash_before = sha256(BOARD)
parts_hash_before = sha256(PARTS)

for marker in REQUIRED_LINEAGE:
    if marker not in style_source:
        fail(f"required lineage runtime missing: {marker}")
if RUNTIME in style_source:
    fail("V2.11D_R1 already applied")

# Source/DOM guards for the approved V2.11D layout.
for marker in (
    'tos-task-description-panel',
    'tos-task-v2-description-actions',
    'tos-save-description-button',
    'PremiumTaskRichTextEditor',
    'variant="decluttered"',
    'className="tos-task-detail-tabs',
    'tos-task-reference-v2-rail',
    'function TaskHeroPremiumSelect(',
    'function TaskHeroPremiumDatePicker(',
    'function TaskHeroPremiumAssigneePicker(',
):
    if marker not in board_source:
        fail(f"required current Task Details marker missing: {marker}")

for marker in (
    'function PremiumTaskRichTextEditor(',
    'tos-task-rich-editor-shell',
    'tos-task-editor-toolbar',
    'tos-task-rich-editor-content',
):
    if marker not in parts_source:
        fail(f"required current editor marker missing: {marker}")

# The collision came from a stale width:100% body rule surviving later in the cascade.
for marker in (
    'body:has(.tos-task-details-reference-v1[data-content-dir])',
    '.tos-task-description-panel',
    'width: 100% !important',
):
    if marker not in style_source:
        fail(f"expected pre-R1 collision context missing: {marker}")

if RUNTIME not in payload_css:
    fail("V2.11D_R1 runtime marker missing from payload")
for selector in (
    ".tos-task-description-panel",
    ".tos-task-rich-editor-shell",
    ".tos-task-editor-toolbar",
    ".tos-task-rich-editor-content",
):
    if selector not in payload_css:
        fail(f"required R1 selector missing from payload: {selector}")

# The rail class may be used only as a :has() geometry anchor; no rail styling is allowed.
for forbidden in (
    ".tos-task-reference-v2-rail {",
    ".tos-task-reference-v2-rail{",
    ".tos-task-v2-quick-actions",
    ".tos-task-v2-info-card",
    ".tos-task-v2-tags",
    ".tos-task-v2-tcs-card",
    ".tos-task-summary-compact",
    ".tos-task-summary-controls",
    ".tos-task-v2-assignees-card",
    ".tos-task-v2-status-control",
    ".tos-task-v2-priority-control",
    ".tos-task-v2-due-date-control",
    ".tos-task-detail-tabs",
    ".tos-task-reference-tab",
    ".tcs-floating-launcher",
    ".ramzy-launcher",
    ".ramzy-assistant-root",
):
    if forbidden in payload_css:
        fail(f"V2.11D_R1 payload illegally touches frozen scope: {forbidden}")

if "calc(100% - 390px)" not in payload_css:
    fail("desktop physical main-column width contract missing")
if "calc(100% - 348px)" not in payload_css:
    fail("medium desktop physical main-column width contract missing")

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
backup_root = Path(f"/var/backups/tos-patches/task-details-v2-11d-r1-collision-{stamp}")
backup_root.mkdir(parents=True, exist_ok=False)
style_backup = backup_root / STYLE.name
shutil.copy2(STYLE, style_backup)

live.parent.mkdir(parents=True, exist_ok=True)
staging = live.parent / f"build.task-details-v2-11d-r1-staging-{stamp}"
live_backup = live.parent / f"build.task-details-v2-11d-r1-backup-{stamp}"
live_swapped = False

try:
    STYLE.write_text(style_source.rstrip() + "\n\n" + payload_css.strip() + "\n")
    updated_style = STYLE.read_text()
    for marker in (*REQUIRED_LINEAGE, RUNTIME):
        if marker not in updated_style:
            fail(f"runtime marker missing after stylesheet update: {marker}")

    if sha256(BOARD) != board_hash_before:
        fail("ProfessionalTaskBoard.jsx changed during CSS-only V2.11D_R1 patch")
    if sha256(PARTS) != parts_hash_before:
        fail("taskBoardParts.jsx changed during CSS-only V2.11D_R1 patch")

    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists() or not (DIST / "index.html").exists():
        fail("frontend dist missing after build")

    built_css = "\n".join(path.read_text(errors="ignore") for path in DIST.rglob("*.css"))
    built_js = "\n".join(path.read_text(errors="ignore") for path in DIST.rglob("*.js"))
    for marker in (*REQUIRED_LINEAGE, RUNTIME):
        if marker not in built_css:
            fail(f"runtime marker missing from built CSS: {marker}")
    for marker in (
        "tos-task-description-panel",
        "tos-task-rich-editor-shell",
        "tos-task-editor-toolbar",
        "tos-task-reference-v2-rail",
        "tos-task-reference-tab",
        "tos-task-v2-assignee-picker-trigger",
        "tos-task-v2-date-trigger",
        "tos-task-v2-premium-select-trigger",
    ):
        if marker not in built_js:
            fail(f"required frozen/current JS marker missing from build: {marker}")

    if staging.exists():
        shutil.rmtree(staging)
    shutil.copytree(DIST, staging)
    if live.exists():
        live.rename(live_backup)
    staging.rename(live)
    live_swapped = True

    live_css = "\n".join(path.read_text(errors="ignore") for path in live.rglob("*.css"))
    live_js = "\n".join(path.read_text(errors="ignore") for path in live.rglob("*.js"))
    for marker in (RUNTIME, D_RUNTIME, C_RUNTIME, B3_RUNTIME):
        if marker not in live_css:
            fail(f"required R1/frozen runtime missing from live CSS: {marker}")
    for marker in (
        "tos-task-description-panel",
        "tos-task-rich-editor-shell",
        "tos-task-reference-v2-rail",
        "tos-task-reference-tab",
        "tos-task-v2-assignee-picker-trigger",
    ):
        if marker not in live_js:
            fail(f"required live JS marker missing: {marker}")

    print(f"VERSION={VERSION}")
    print(f"PATCH={PATCH_NAME}")
    print(f"BASELINE_CHAIN={BASELINE_CHAIN}")
    print(f"MICRO_STEP={MICRO_STEP}")
    print("PASS/FAIL=PASS")
    print("BUILD_RESULT=PASS")
    print("LIVE_DEPLOY=PASS")
    print("EDITOR_RIGHT_RAIL_OVERLAP=TARGET_ZERO")
    print("DESCRIPTION_PHYSICAL_MAIN_WIDTH=LOCKED")
    print("EDITOR_TOOLBAR=COMPACTED_WITHIN_MAIN_COLUMN")
    print("RIGHT_RAIL_STYLE_CHANGED=NO")
    print("RICH_TEXT_LOGIC_CHANGED=NO")
    print("HERO_CONTROLS_B1_B2_B3=PRESERVED")
    print("PRIMARY_TABS_V2_11C=PRESERVED")
    print("DESCRIPTION_EDITOR_V2_11D=PRESERVED")
    print("BOARD_SOURCE_CHANGED=NO")
    print("EDITOR_SOURCE_CHANGED=NO")
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
    print(f"MICRO_STEP={MICRO_STEP}")
    print("PASS/FAIL=FAIL")
    print(f"ERROR={exc}")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("STATUS=STOPPED")
    raise SystemExit(1)
