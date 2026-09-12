from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import time

VERSION = "TOS_TASK_DETAILS_V2_11D"
PATCH_NAME = "TOS-UXUI-TASK-DETAILS-V2-11D-DESCRIPTION-EDITOR-PREMIUM-LOCK"
BASELINE_CHAIN = "TOS_TASK_DETAILS_V2_11C"
MICRO_STEP = "DESCRIPTION_EDITOR_ONLY"

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
BOARD = FRONTEND / "src/components/ProfessionalTaskBoard.jsx"
PARTS = FRONTEND / "src/features/tasks/taskBoardParts.jsx"
STYLE = FRONTEND / "src/styles/taskDetailsCanonicalReferenceV2.css"
MANIFEST = ROOT / "deployment/tos-production-runtime.json"
DIST = FRONTEND / "dist"
PATCH_DIR = Path(__file__).resolve().parent
PAYLOAD = PATCH_DIR / "taskDetailsV2_11DDescriptionEditorPremiumLock.css"

RUNTIME = "--tos-task-details-v2-11d-description-editor-premium-lock-runtime"
C_RUNTIME = "--tos-task-details-v2-11c-primary-tabs-premium-lock-runtime"
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
    "--tos-task-details-v2-11b3-assignees-custom-selector-runtime",
    C_RUNTIME,
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
    fail("V2.11D already applied")

# Current Overview/Description source must match the approved chain.
for marker in (
    'tos-task-description-panel',
    'tos-task-v2-description-actions',
    'tos-save-description-button',
    'PremiumTaskRichTextEditor',
    'variant="decluttered"',
    'activeTaskTab === "overview"',
    'className="tos-task-detail-tabs',
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
    'showExtendedFormatting',
    'isFullscreen',
):
    if marker not in parts_source:
        fail(f"required editor implementation marker missing: {marker}")

if RUNTIME not in payload_css:
    fail("V2.11D runtime marker missing from payload")
for selector in (
    ".tos-task-description-panel",
    ".tos-task-v2-description-actions",
    ".tos-task-rich-editor-shell",
    ".tos-task-editor-toolbar",
    ".tos-task-rich-editor-content",
    ".tos-save-description-button",
):
    if selector not in payload_css:
        fail(f"required V2.11D selector missing from payload: {selector}")

# Strict micro-step boundary: no Hero, tabs, rail, assistants or business-flow presentation.
for forbidden in (
    ".tos-task-summary-compact",
    ".tos-task-summary-controls",
    ".tos-task-v2-assignees-card",
    ".tos-task-v2-status-control",
    ".tos-task-v2-priority-control",
    ".tos-task-v2-due-date-control",
    ".tos-task-v2-assignee-popover",
    ".tos-task-v2-calendar-popover",
    ".tos-task-v2-premium-menu",
    ".tos-task-detail-tabs",
    ".tos-task-reference-tab",
    ".tos-task-reference-v2-rail",
    ".tos-task-v2-quick-actions",
    ".tos-task-v2-info-card",
    ".tos-task-v2-tags",
    ".tos-task-v2-tcs-card",
    ".tcs-floating-launcher",
    ".ramzy-launcher",
    ".ramzy-assistant-root",
):
    if forbidden in payload_css:
        fail(f"V2.11D payload illegally touches frozen scope: {forbidden}")

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
backup_root = Path(f"/var/backups/tos-patches/task-details-v2-11d-description-{stamp}")
backup_root.mkdir(parents=True, exist_ok=False)
style_backup = backup_root / STYLE.name
shutil.copy2(STYLE, style_backup)

live.parent.mkdir(parents=True, exist_ok=True)
staging = live.parent / f"build.task-details-v2-11d-staging-{stamp}"
live_backup = live.parent / f"build.task-details-v2-11d-backup-{stamp}"
live_swapped = False

try:
    STYLE.write_text(style_source.rstrip() + "\n\n" + payload_css.strip() + "\n")
    updated_style = STYLE.read_text()
    for marker in (*REQUIRED_LINEAGE, RUNTIME):
        if marker not in updated_style:
            fail(f"runtime marker missing after stylesheet update: {marker}")

    if sha256(BOARD) != board_hash_before:
        fail("ProfessionalTaskBoard.jsx changed during CSS-only V2.11D patch")
    if sha256(PARTS) != parts_hash_before:
        fail("taskBoardParts.jsx changed during CSS-only V2.11D patch")

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
        "tos-task-v2-description-actions",
        "tos-save-description-button",
        "tos-task-rich-editor-shell",
        "tos-task-editor-toolbar",
        "tos-task-rich-editor-content",
        "tos-task-reference-tab",
        "tos-task-v2-assignee-picker-trigger",
        "tos-task-v2-date-trigger",
        "tos-task-v2-premium-select-trigger",
    ):
        if marker not in built_js:
            fail(f"required current/frozen JS marker missing from build: {marker}")

    if staging.exists():
        shutil.rmtree(staging)
    shutil.copytree(DIST, staging)
    if live.exists():
        live.rename(live_backup)
    staging.rename(live)
    live_swapped = True

    live_css = "\n".join(path.read_text(errors="ignore") for path in live.rglob("*.css"))
    live_js = "\n".join(path.read_text(errors="ignore") for path in live.rglob("*.js"))
    if RUNTIME not in live_css or C_RUNTIME not in live_css:
        fail("V2.11D/V2.11C runtime marker missing from live CSS")
    for marker in (
        "tos-task-description-panel",
        "tos-task-rich-editor-shell",
        "tos-task-editor-toolbar",
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
    print("DESCRIPTION_PANEL=PREMIUM_LOCK_TARGET")
    print("EDITOR_HEADER=RESTORED")
    print("EDITOR_TOOLBAR=RESTORED_PREMIUM")
    print("EDITOR_CONTENT=PREMIUM_CANVAS_TARGET")
    print("RICH_TEXT_LOGIC_CHANGED=NO")
    print("TAB_CONTENT_LOGIC_CHANGED=NO")
    print("HERO_CONTROLS_B1_B2_B3=PRESERVED")
    print("PRIMARY_TABS_V2_11C=PRESERVED")
    print("RIGHT_RAIL_CHANGED=NO")
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
