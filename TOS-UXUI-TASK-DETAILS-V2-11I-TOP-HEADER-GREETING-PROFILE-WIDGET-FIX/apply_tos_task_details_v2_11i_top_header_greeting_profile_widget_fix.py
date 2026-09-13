from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import time

VERSION = "TOS_TASK_DETAILS_V2_11I"
PATCH_NAME = "TOS-UXUI-TASK-DETAILS-V2-11I-TOP-HEADER-GREETING-PROFILE-WIDGET-FIX"
BASELINE_CHAIN = "TOS_TASK_DETAILS_V2_11H"
BASE_TOS_COMMIT = "LIVE_AHEAD_OF_GITHUB_MAIN_ALLOWED"
MICRO_STEP = "TOP_HEADER_GREETING_PROFILE_WIDGET_FIX_ONLY"

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
BOARD = FRONTEND / "src/components/ProfessionalTaskBoard.jsx"
PARTS = FRONTEND / "src/features/tasks/taskBoardParts.jsx"
STYLE = FRONTEND / "src/styles/taskDetailsCanonicalReferenceV2.css"
TCS = FRONTEND / "src/components/TcsFloatingLauncher.jsx"
RAMZY = FRONTEND / "src/components/RamzyAssistant.jsx"
MANIFEST = ROOT / "deployment/tos-production-runtime.json"
DIST = FRONTEND / "dist"
PATCH_DIR = Path(__file__).resolve().parent
PAYLOAD = PATCH_DIR / "taskDetailsV2_11ITopHeaderGreetingProfileWidgetFix.css"

RUNTIME = "--tos-task-details-v2-11i-top-header-greeting-profile-widget-fix-runtime"
H_SOURCE_MARKER = "TOS_TASK_DETAILS_V2_11H_HERO_DESCRIPTION_REMOVED"
ER1_RUNTIME = "--tos-task-details-v2-11e-r1-floating-assistants-rail-collision-fix-runtime"
R2_RUNTIME = "--tos-task-details-v2-11f-r2-editor-toolbar-live-scope-wrap-more-fix-runtime"


def fail(message):
    raise RuntimeError(message)


def run(command, cwd=None):
    subprocess.run(command, cwd=cwd, check=True)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


for path in (FRONTEND, BOARD, PARTS, STYLE, TCS, RAMZY, MANIFEST, PAYLOAD):
    if not path.exists():
        fail(f"required path missing: {path}")

for command in ("node", "npm"):
    if not shutil.which(command):
        fail(f"required command not found: {command}")

board_source = BOARD.read_text()
parts_source = PARTS.read_text()
style_source = STYLE.read_text()
tcs_source = TCS.read_text()
ramzy_source = RAMZY.read_text()
payload_css = PAYLOAD.read_text()

if H_SOURCE_MARKER not in board_source:
    fail("required V2.11H source marker missing")
if ER1_RUNTIME not in style_source:
    fail("required V2.11E_R1 assistant collision runtime missing")
if R2_RUNTIME not in style_source:
    fail("required V2.11F_R2 runtime missing")
if RUNTIME in style_source:
    fail("V2.11I already applied")
if RUNTIME not in payload_css:
    fail("V2.11I runtime marker missing from payload")

for marker in (
    "tos-task-description-panel",
    "PremiumTaskRichTextEditor",
    "tos-task-reference-v2-rail",
    "tos-task-reference-tabs-main",
):
    if marker not in board_source + "\n" + parts_source:
        fail(f"required protected Task Details marker missing: {marker}")

for marker in (
    'className={`tcs-floating-launcher',
    'data-testid="tcs-floating-launcher"',
):
    if marker not in tcs_source:
        fail(f"required TCS marker missing: {marker}")

for marker in (
    "ramzy-launcher-wrap",
    "ramzy-launcher-avatar-wrap",
    "ramzy-avatar-ring",
    "ramzy-launcher-label",
    "ramzy-greeting",
    'style={{ left: launcherPosition.x, top: launcherPosition.y }}',
):
    if marker not in ramzy_source:
        fail(f"required Ramzy launcher marker missing: {marker}")

for selector in (
    ".ramzy-launcher-wrap",
    ".ramzy-launcher-avatar-wrap",
    ".ramzy-avatar-ring",
    ".ramzy-launcher-label",
    ".ramzy-greeting",
    ".ramzy-launcher-close",
):
    if selector not in payload_css:
        fail(f"required V2.11I selector missing from payload: {selector}")

for contract in (
    "@media (min-width: 1440px)",
    "width: 156px !important",
    "writing-mode: horizontal-tb !important",
    "word-break: normal !important",
    "@media (min-width: 1280px) and (max-width: 1366px)",
    "display: none !important",
):
    if contract not in payload_css:
        fail(f"required V2.11I visual contract missing: {contract}")

# This patch may style only the closed Ramzy launcher. It must not style Task Details,
# TCS, Ramzy panel/chat internals, user profile, editor, rail or hero elements.
for forbidden in (
    ".tos-task-summary-compact",
    ".tos-task-description-panel",
    ".tos-task-reference-v2-rail",
    ".tos-task-detail-tabs",
    ".tos-task-reference-tab",
    ".tos-task-editor-toolbar",
    ".tos-task-rich-editor-content",
    ".tcs-floating-launcher",
    ".tcs-desktop-window",
    ".ramzy-panel",
    ".ramzy-messages",
    ".ramzy-composer",
):
    if forbidden in payload_css:
        fail(f"V2.11I payload illegally touches frozen scope: {forbidden}")

frozen_hashes = {
    BOARD: sha256(BOARD),
    PARTS: sha256(PARTS),
    TCS: sha256(TCS),
    RAMZY: sha256(RAMZY),
}

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

LIVE = Path(str(frontend_runtime.get("publishedBuildDir") or ""))
if DIST != FRONTEND / "dist":
    fail(f"unexpected frontend dist path: {DIST}")
if LIVE != Path("/opt/apps/tamiyouz-front/build"):
    fail(f"unexpected live frontend path: {LIVE}")

stamp = int(time.time())
backup_root = Path(f"/var/backups/tos-patches/task-details-v2-11i-header-widget-{stamp}")
backup_root.mkdir(parents=True, exist_ok=False)
style_backup = backup_root / STYLE.name
shutil.copy2(STYLE, style_backup)

LIVE.parent.mkdir(parents=True, exist_ok=True)
staging = LIVE.parent / f"build.task-details-v2-11i-staging-{stamp}"
live_backup = LIVE.parent / f"build.task-details-v2-11i-backup-{stamp}"
live_swapped = False

try:
    STYLE.write_text(style_source.rstrip() + "\n\n" + payload_css.strip() + "\n")
    updated_style = STYLE.read_text()
    for marker in (ER1_RUNTIME, R2_RUNTIME, RUNTIME):
        if marker not in updated_style:
            fail(f"runtime marker missing after stylesheet update: {marker}")

    for path, expected_hash in frozen_hashes.items():
        if sha256(path) != expected_hash:
            fail(f"CSS-only patch unexpectedly changed source file: {path}")

    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists() or not (DIST / "index.html").exists():
        fail("frontend dist missing after build")

    built_css = "\n".join(path.read_text(errors="ignore") for path in DIST.rglob("*.css"))
    built_js = "\n".join(path.read_text(errors="ignore") for path in DIST.rglob("*.js"))
    for marker in (ER1_RUNTIME, R2_RUNTIME, RUNTIME):
        if marker not in built_css:
            fail(f"runtime marker missing from built CSS: {marker}")
    for marker in (
        "tos-task-description-panel",
        "tos-task-reference-v2-rail",
        "ramzy-launcher-wrap",
        "ramzy-greeting",
        "tcs-floating-launcher",
    ):
        if marker not in built_js:
            fail(f"required protected runtime JS marker missing: {marker}")

    if staging.exists():
        shutil.rmtree(staging)
    shutil.copytree(DIST, staging)

    if LIVE.exists():
        if live_backup.exists():
            shutil.rmtree(live_backup)
        LIVE.rename(live_backup)
    staging.rename(LIVE)
    live_swapped = True

    live_css = "\n".join(path.read_text(errors="ignore") for path in LIVE.rglob("*.css"))
    live_js = "\n".join(path.read_text(errors="ignore") for path in LIVE.rglob("*.js"))
    if RUNTIME not in live_css:
        fail("V2.11I runtime marker missing from live CSS")
    for marker in ("ramzy-launcher-wrap", "ramzy-greeting", "tcs-floating-launcher", "tos-task-description-panel"):
        if marker not in live_js:
            fail(f"required marker missing from live JS: {marker}")

    for path, expected_hash in frozen_hashes.items():
        if sha256(path) != expected_hash:
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
print(f"BASE_TOS_COMMIT={BASE_TOS_COMMIT}")
print(f"MICRO_STEP={MICRO_STEP}")
print("PASS/FAIL=PASS")
print("BUILD_RESULT=PASS")
print("LIVE_DEPLOY=PASS")
print("TOP_HEADER_GREETING_PROFILE_FIX_APPLIED=YES")
print("RAMZY_LAUNCHER_COMPONENT_CHANGED=NO")
print("TCS_COMPONENT_CHANGED=NO")
print("TASK_DETAILS_CHANGED=NO")
print("HERO_CHANGED=NO")
print("DESCRIPTION_CHANGED=NO")
print("DESCRIPTION_DATA_CHANGED=NO")
print("PRIMARY_TABS_CHANGED=NO")
print("RIGHT_RAIL_CHANGED=NO")
print("WAITING_CLIENT_LAYOUT_CHANGED=NO")
print("PUSH=NO")
print("STATUS=READY_FOR_VISUAL_QA")
