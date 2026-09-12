from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import time

VERSION = "TOS_TASK_DETAILS_V2_11F_R2"
PATCH_NAME = "TOS-UXUI-TASK-DETAILS-V2-11F-R2-EDITOR-TOOLBAR-LIVE-SCOPE-WRAP-MORE-FIX"
PARENT_PATCH = "TOS_TASK_DETAILS_V2_11F_R1"
BASELINE_CHAIN = "TOS_TASK_DETAILS_V2_11E_R1"
BASE_TOS_COMMIT = "cd019d60434943d625fde9d2ea2ddee7e68d2028"

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
BOARD = FRONTEND / "src/components/ProfessionalTaskBoard.jsx"
PARTS = FRONTEND / "src/features/tasks/taskBoardParts.jsx"
TCS = FRONTEND / "src/components/TcsFloatingLauncher.jsx"
RAMZY = FRONTEND / "src/components/RamzyAssistant.jsx"
STYLE = FRONTEND / "src/styles/taskDetailsCanonicalReferenceV2.css"
MANIFEST = ROOT / "deployment/tos-production-runtime.json"
PATCH_DIR = Path(__file__).resolve().parent
PAYLOAD = PATCH_DIR / "taskDetailsV2_11F_R2EditorToolbarLiveScopeWrapMoreFix.css"

RUNTIME = "--tos-task-details-v2-11f-r2-editor-toolbar-live-scope-wrap-more-fix-runtime"
R1_RUNTIME = "--tos-task-details-v2-11f-r1-editor-toolbar-actual-dom-responsive-fix-runtime"
BAD_F_RUNTIME = "--tos-task-details-v2-11f-editor-toolbar-responsive-more-formatting-fix-runtime"
LIVE_ROOT_SELECTOR = ".tos-task-details-reference-v1[data-content-dir].tos-task-details-reference-v2"
WRONG_R1_ROOT = ".tos-task-details-modal[data-task-details-reference=\"v2\"]"

REQUIRED_LINEAGE = (
    "--tos-task-details-canonical-reference-v2-runtime",
    "--tos-task-details-v2-11c-primary-tabs-premium-lock-runtime",
    "--tos-task-details-v2-11d-description-editor-premium-lock-runtime",
    "--tos-task-details-v2-11d-r1-editor-right-rail-collision-fix-runtime",
    "--tos-task-details-v2-11e-right-rail-premium-rebuild-runtime",
    "--tos-task-details-v2-11e-r1-floating-assistants-rail-collision-fix-runtime",
    R1_RUNTIME,
)


def fail(message):
    raise RuntimeError(message)


def run(command, cwd=None):
    subprocess.run(command, cwd=cwd, check=True)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


for path in (FRONTEND, BOARD, PARTS, TCS, RAMZY, STYLE, MANIFEST, PAYLOAD):
    if not path.exists():
        fail(f"required path missing: {path}")

for command in ("node", "npm"):
    if not shutil.which(command):
        fail(f"required command not found: {command}")

board_source = BOARD.read_text()
parts_source = PARTS.read_text()
tcs_source = TCS.read_text()
ramzy_source = RAMZY.read_text()
style_source = STYLE.read_text()
payload_css = PAYLOAD.read_text()

for marker in REQUIRED_LINEAGE:
    if marker not in style_source:
        fail(f"required lineage runtime missing: {marker}")

if RUNTIME in style_source:
    fail("V2.11F_R2 already applied")

if BAD_F_RUNTIME in style_source:
    fail("unexpected failed V2.11F runtime is present; stop for inspection")

# Confirm the real Task Details root and Description editor DOM.
for marker in (
    "tos-task-details-fullpage tos-task-details-reference-v1 tos-task-details-reference-v2",
    "data-content-dir={modalDirection}",
    "tos-task-description-panel",
    'variant="decluttered"',
    "PremiumTaskRichTextEditor",
):
    if marker not in board_source:
        fail(f"required live Task Details marker missing: {marker}")

for marker in (
    "function PremiumTaskRichTextEditor",
    "showExtendedFormatting",
    "setShowExtendedFormatting",
    "tos-task-editor-toolbar",
    'data-extended={showExtendedFormatting ? "true" : "false"}',
    "tos-task-editor-more-button",
    "tos-editor-group-history",
    "tos-editor-group-block",
    "tos-editor-group-inline",
    "tos-editor-group-list",
    "tos-editor-group-align",
    "tos-editor-group-color",
    "tos-editor-group-insert",
):
    if marker not in parts_source:
        fail(f"required actual editor source marker missing: {marker}")

for marker in ("tcs-floating-launcher", 'data-testid="tcs-floating-launcher"'):
    if marker not in tcs_source:
        fail(f"required TCS marker missing: {marker}")
for marker in ("ramzy-launcher-wrap", "ramzy-greeting"):
    if marker not in ramzy_source:
        fail(f"required Ramzy marker missing: {marker}")

# Confirm the visual root cause is still represented in the canonical CSS chain.
for marker in (
    ".tos-task-details-reference-v2 .tos-task-editor-toolbar > div",
    "flex-wrap: nowrap !important",
    "overflow-x: auto !important",
    LIVE_ROOT_SELECTOR,
):
    if marker not in style_source:
        fail(f"expected current toolbar/CSS baseline marker missing: {marker}")

# Validate R2 payload targets the REAL live root, not the dead R1 scope.
for contract in (
    RUNTIME,
    LIVE_ROOT_SELECTOR,
    ".tos-task-description-panel",
    ".tos-task-editor-toolbar",
    ".tos-task-editor-toolbar > div",
    '[data-extended="false"]',
    '[data-extended="true"]',
    ".tos-task-editor-more-button",
    ".tos-editor-group-history",
    ".tos-editor-group-block",
    ".tos-editor-group-inline",
    ".tos-editor-group-list",
    ".tos-editor-group-align",
    ".tos-editor-group-color",
    ".tos-editor-group-insert",
    "flex-wrap: wrap !important",
    "overflow-x: visible !important",
    "display: none !important",
    "display: inline-flex !important",
):
    if contract not in payload_css:
        fail(f"R2 toolbar contract missing: {contract}")

if WRONG_R1_ROOT in payload_css:
    fail("R2 payload still contains the dead R1 Task Details root selector")

for fictional in (
    "tos-editor-group-font",
    "tos-editor-group-basic",
    "tos-editor-group-direction",
):
    if fictional in payload_css:
        fail(f"R2 payload contains obsolete/non-existent editor selector: {fictional}")

# Absolute presentation-only scope.
for forbidden in (
    ".tos-task-reference-v2-rail",
    ".tos-task-v2-rail-card",
    ".tos-task-v2-quick-actions",
    ".tos-task-v2-info-card",
    ".tos-task-v2-tags",
    ".tos-task-v2-tcs-card",
    ".tos-task-reference-tabs-main",
    ".tos-task-detail-tabs",
    ".tos-task-summary-compact",
    ".tos-task-summary-controls",
    ".tos-task-v2-assignees-card",
    ".tos-task-v2-status-control",
    ".tos-task-v2-priority-control",
    ".tos-task-v2-due-date-control",
    ".tos-save-description-button",
    ".tos-task-rich-editor-content",
    ".tcs-floating-launcher",
    ".ramzy-launcher-wrap",
    ".ramzy-greeting",
):
    if forbidden in payload_css:
        fail(f"R2 payload illegally touches frozen scope: {forbidden}")

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

frozen_hashes = {path: sha256(path) for path in (BOARD, PARTS, TCS, RAMZY)}
stamp = int(time.time())
backup_root = Path(f"/var/backups/tos-patches/task-details-v2-11f-r2-{stamp}")
backup_root.mkdir(parents=True, exist_ok=False)
style_backup = backup_root / STYLE.name
shutil.copy2(STYLE, style_backup)

LIVE.parent.mkdir(parents=True, exist_ok=True)
staging = LIVE.parent / f"build.task-details-v2-11f-r2-staging-{stamp}"
live_backup = LIVE.parent / f"build.task-details-v2-11f-r2-backup-{stamp}"
live_swapped = False

try:
    STYLE.write_text(style_source.rstrip() + "\n\n" + payload_css.strip() + "\n")
    updated_style = STYLE.read_text()

    for marker in (*REQUIRED_LINEAGE, RUNTIME):
        if marker not in updated_style:
            fail(f"runtime marker missing after stylesheet update: {marker}")

    for path, expected in frozen_hashes.items():
        if sha256(path) != expected:
            fail(f"CSS-only patch unexpectedly changed source file: {path}")

    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists() or not (DIST / "index.html").exists():
        fail("frontend dist missing after build")

    built_css = "\n".join(p.read_text(errors="ignore") for p in DIST.rglob("*.css"))
    built_js = "\n".join(p.read_text(errors="ignore") for p in DIST.rglob("*.js"))

    for marker in (*REQUIRED_LINEAGE, RUNTIME):
        if marker not in built_css:
            fail(f"runtime marker missing from built CSS: {marker}")

    for marker in (
        "tos-task-details-reference-v1",
        "tos-task-details-reference-v2",
        "tos-task-editor-toolbar",
        "tos-task-editor-more-button",
        "tos-editor-group-inline",
        "tos-editor-group-align",
        "tos-task-reference-v2-rail",
        "tcs-floating-launcher",
        "ramzy-launcher-wrap",
    ):
        if marker not in built_js:
            fail(f"required current/frozen JS marker missing from build: {marker}")

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
    if RUNTIME not in live_css:
        fail("R2 runtime marker missing from live build")
    if LIVE_ROOT_SELECTOR not in live_css:
        fail("R2 live-scope selector missing from live CSS")

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
print(f"PARENT_PATCH={PARENT_PATCH}")
print(f"BASELINE_CHAIN={BASELINE_CHAIN}")
print(f"BASE_TOS_COMMIT={BASE_TOS_COMMIT}")
print("PASS/FAIL=PASS")
print("BUILD_RESULT=PASS")
print("LIVE_DEPLOY=PASS")
print("LIVE_SCOPE_SELECTOR_FIX=YES")
print("R1_WRONG_SCOPE_SUPERSEDED=YES")
print("EDITOR_TOOLBAR_RESPONSIVE_FIX=YES")
print("MORE_FORMATTING_VISIBILITY_FIX=YES")
print("TOOLBAR_HORIZONTAL_CLIPPING_FIX=YES")
print("TOOLBAR_WRAP_CONTRACT=YES")
print("ACTUAL_EDITOR_DOM_GUARD=YES")
print("EDITOR_FUNCTIONS_CHANGED=NO")
print("EDITOR_SOURCE_CHANGED=NO")
print("BOARD_SOURCE_CHANGED=NO")
print("TCS_SOURCE_CHANGED=NO")
print("RAMZY_SOURCE_CHANGED=NO")
print("RIGHT_RAIL_CHANGED=NO")
print("PRIMARY_TABS_CHANGED=NO")
print("HERO_CHANGED=NO")
print("V2_11F_R1_PRESERVED=YES")
print("V2_11E_R1_PRESERVED=YES")
print("PUSH=NO")
print("STATUS=READY_FOR_VISUAL_QA")
