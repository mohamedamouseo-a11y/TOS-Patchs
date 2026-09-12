from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import time

VERSION = "TOS_TASK_DETAILS_V2_11E_R1"
PATCH_NAME = "TOS-UXUI-TASK-DETAILS-V2-11E-R1-FLOATING-ASSISTANTS-RAIL-COLLISION-FIX"
BASELINE_CHAIN = "TOS_TASK_DETAILS_V2_11E"
BASE_TOS_COMMIT = "fd10edb0885a148dd53a8cbd6346bbea7f2d6ab4"
MICRO_STEP = "FLOATING_ASSISTANTS_RAIL_COLLISION_FIX_ONLY"

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
BOARD = FRONTEND / "src/components/ProfessionalTaskBoard.jsx"
PARTS = FRONTEND / "src/features/tasks/taskBoardParts.jsx"
TCS_COMPONENT = FRONTEND / "src/components/TcsFloatingLauncher.jsx"
RAMZY_COMPONENT = FRONTEND / "src/components/RamzyAssistant.jsx"
STYLE = FRONTEND / "src/styles/taskDetailsCanonicalReferenceV2.css"
MANIFEST = ROOT / "deployment/tos-production-runtime.json"
DIST = FRONTEND / "dist"
PATCH_DIR = Path(__file__).resolve().parent
PAYLOAD = PATCH_DIR / "taskDetailsV2_11ER1FloatingAssistantsRailCollisionFix.css"

RUNTIME = "--tos-task-details-v2-11e-r1-floating-assistants-rail-collision-fix-runtime"
E_RUNTIME = "--tos-task-details-v2-11e-right-rail-premium-rebuild-runtime"
R1_RUNTIME = "--tos-task-details-v2-11d-r1-editor-right-rail-collision-fix-runtime"
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
    R1_RUNTIME,
    E_RUNTIME,
)


def fail(message):
    raise RuntimeError(message)


def run(command, cwd=None):
    subprocess.run(command, cwd=cwd, check=True)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


for required in (
    FRONTEND,
    BOARD,
    PARTS,
    TCS_COMPONENT,
    RAMZY_COMPONENT,
    STYLE,
    MANIFEST,
    PAYLOAD,
):
    if not required.exists():
        fail(f"required path missing: {required}")

for command in ("node", "npm"):
    if not shutil.which(command):
        fail(f"required command not found: {command}")

board_source = BOARD.read_text()
parts_source = PARTS.read_text()
tcs_source = TCS_COMPONENT.read_text()
ramzy_source = RAMZY_COMPONENT.read_text()
style_source = STYLE.read_text()
payload_css = PAYLOAD.read_text()

source_hashes_before = {
    BOARD: sha256(BOARD),
    PARTS: sha256(PARTS),
    TCS_COMPONENT: sha256(TCS_COMPONENT),
    RAMZY_COMPONENT: sha256(RAMZY_COMPONENT),
}

for marker in REQUIRED_LINEAGE:
    if marker not in style_source:
        fail(f"required lineage runtime missing: {marker}")
if RUNTIME in style_source:
    fail("V2.11E_R1 already applied")

for marker in (
    'className="tos-task-reference-v2-rail"',
    "tos-task-v2-quick-actions",
    "tos-task-v2-info-card",
    "tos-task-v2-tags",
    "tos-task-v2-tcs-card",
    "tos-task-description-panel",
    'className="tos-task-detail-tabs',
):
    if marker not in board_source:
        fail(f"required current Task Details marker missing: {marker}")

for marker in (
    "PremiumTaskRichTextEditor",
    "tos-task-rich-editor-shell",
    "tos-task-editor-toolbar",
    "tos-task-rich-editor-content",
):
    combined = board_source + "\n" + parts_source
    if marker not in combined:
        fail(f"required frozen editor marker missing: {marker}")

for marker in (
    'className={`tcs-floating-launcher',
    'style={{ left: `${position.x}px`, top: `${position.y}px` }}',
    'data-testid="tcs-floating-launcher"',
):
    if marker not in tcs_source:
        fail(f"required TCS launcher marker missing: {marker}")

for marker in (
    "ramzy-launcher-wrap",
    "style={{ left: launcherPosition.x, top: launcherPosition.y }}",
    "ramzy-launcher-label",
    "ramzy-greeting",
):
    if marker not in ramzy_source:
        fail(f"required Ramzy launcher marker missing: {marker}")

if RUNTIME not in payload_css:
    fail("V2.11E_R1 runtime marker missing from payload")

for selector in (
    ".tcs-floating-launcher",
    ".tcs-floating-launcher-copy",
    ".ramzy-launcher-wrap",
    ".ramzy-launcher-label",
    ".ramzy-greeting",
):
    if selector not in payload_css:
        fail(f"required V2.11E_R1 assistant selector missing: {selector}")

for contract in (
    "@media (min-width: 1280px) and (max-width: 1366px)",
    "left: calc(100vw - 500px) !important",
    "left: calc(100% - 320px) !important",
    "top: 14px !important",
    "top: 12px !important",
):
    if contract not in payload_css:
        fail(f"responsive assistant geometry contract missing: {contract}")

# Frozen scope: this corrective layer may target only global assistant launcher geometry/presentation.
for forbidden in (
    ".tos-task-reference-v2-rail",
    ".tos-task-v2-rail-card",
    ".tos-task-v2-quick-actions",
    ".tos-task-v2-info-card",
    ".tos-task-v2-tags",
    ".tos-task-v2-tcs-card",
    ".tos-task-description-panel",
    ".tos-task-rich-editor-shell",
    ".tos-task-editor-toolbar",
    ".tos-task-rich-editor-content",
    ".tos-save-description-button",
    ".tos-task-detail-tabs",
    ".tos-task-reference-tab",
    ".tos-task-summary-compact",
    ".tos-task-summary-controls",
    ".tos-task-v2-assignees-card",
    ".tos-task-v2-status-control",
    ".tos-task-v2-priority-control",
    ".tos-task-v2-due-date-control",
    ".tcs-desktop-window",
    ".ramzy-panel",
):
    if forbidden in payload_css:
        fail(f"V2.11E_R1 payload illegally touches frozen scope: {forbidden}")

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
backup_root = Path(f"/var/backups/tos-patches/task-details-v2-11e-r1-assistants-{stamp}")
backup_root.mkdir(parents=True, exist_ok=False)
style_backup = backup_root / STYLE.name
shutil.copy2(STYLE, style_backup)

live.parent.mkdir(parents=True, exist_ok=True)
staging = live.parent / f"build.task-details-v2-11e-r1-staging-{stamp}"
live_backup = live.parent / f"build.task-details-v2-11e-r1-backup-{stamp}"
live_swapped = False

try:
    STYLE.write_text(style_source.rstrip() + "\n\n" + payload_css.strip() + "\n")
    updated_style = STYLE.read_text()

    for marker in (*REQUIRED_LINEAGE, RUNTIME):
        if marker not in updated_style:
            fail(f"runtime marker missing after stylesheet update: {marker}")

    for path, expected_hash in source_hashes_before.items():
        if sha256(path) != expected_hash:
            fail(f"CSS-only patch unexpectedly changed source file: {path}")

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
        "tos-task-description-panel",
        "tos-task-reference-tab",
        "tcs-floating-launcher",
        "ramzy-launcher-wrap",
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

    for marker in (RUNTIME, E_RUNTIME, R1_RUNTIME, D_RUNTIME, C_RUNTIME, B3_RUNTIME):
        if marker not in live_css:
            fail(f"required V2.11E_R1/frozen runtime missing from live CSS: {marker}")

    for marker in (
        "tos-task-reference-v2-rail",
        "tos-task-description-panel",
        "tcs-floating-launcher",
        "ramzy-launcher-wrap",
    ):
        if marker not in live_js:
            fail(f"required live JS marker missing: {marker}")

    print(f"VERSION={VERSION}")
    print(f"PATCH={PATCH_NAME}")
    print(f"BASELINE_CHAIN={BASELINE_CHAIN}")
    print(f"BASE_TOS_COMMIT={BASE_TOS_COMMIT}")
    print(f"MICRO_STEP={MICRO_STEP}")
    print("PASS/FAIL=PASS")
    print("BUILD_RESULT=PASS")
    print("LIVE_DEPLOY=PASS")
    print("FLOATING_ASSISTANTS_RAIL_COLLISION_FIX=YES")
    print("TCS_RESPONSIVE_DOCK=YES")
    print("RAMZY_RESPONSIVE_DOCK=YES")
    print("ASSISTANT_LOGIC_CHANGED=NO")
    print("TCS_SOURCE_CHANGED=NO")
    print("RAMZY_SOURCE_CHANGED=NO")
    print("RIGHT_RAIL_STYLE_CHANGED=NO")
    print("V2_11E_RIGHT_RAIL=PRESERVED")
    print("V2_11D_R1=PRESERVED")
    print("PRIMARY_TABS_V2_11C=PRESERVED")
    print("HERO_B1_B2_B3=PRESERVED")
    print("BOARD_SOURCE_CHANGED=NO")
    print("EDITOR_SOURCE_CHANGED=NO")
    print("PUSH=NO")
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
    print(f"BASE_TOS_COMMIT={BASE_TOS_COMMIT}")
    print(f"MICRO_STEP={MICRO_STEP}")
    print("PASS/FAIL=FAIL")
    print(f"ERROR={exc}")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("PUSH=NO")
    print("STATUS=STOPPED")
    raise SystemExit(1)
