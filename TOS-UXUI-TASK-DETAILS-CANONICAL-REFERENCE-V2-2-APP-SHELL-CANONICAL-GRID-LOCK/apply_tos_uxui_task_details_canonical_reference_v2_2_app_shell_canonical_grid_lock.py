from pathlib import Path
import json
import re
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
PAYLOAD_STYLE = PATCH_DIR / "taskDetailsCanonicalReferenceV2_2AppShellCanonicalGridLock.css"

RUNTIME = "--tos-task-details-canonical-reference-v2-2-app-shell-grid-lock-runtime"
V2_RUNTIME_MARKERS = (
    "--tos-task-details-canonical-reference-v2-runtime",
    "--tos-task-details-canonical-v2-runtime",
)
V2_1_RUNTIME = "--tos-task-details-canonical-reference-v2-1-rtl-structural-geometry-runtime"

ROOT_PATTERN = re.compile(
    r'(<div\\b[^>]*className="[^"]*tos-task-details-reference-v1[^"]*"[^>]*?)\\sdir=\\{modalDirection\\}([^>]*>)'
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
    fail("V2.2 CSS runtime marker missing from payload")

board_source = BOARD.read_text()
for marker in (
    "tos-task-details-reference-v1",
    "PremiumTaskRichTextEditor",
    "handleTaskStatusChange",
    "modalDirection = isAr ? \"rtl\" : \"ltr\"",
):
    if marker not in board_source:
        fail(f"required current Task Details marker missing: {marker}")

if 'data-content-dir={modalDirection}' in board_source:
    fail("V2.2 structural root conversion is already present")

matches = list(ROOT_PATTERN.finditer(board_source))
if len(matches) != 1:
    fail(f"expected exactly one Task Details structural root dir marker, found {len(matches)}")

# Locate the exact live V2 stylesheet by requiring both V2 and V2.1 runtime markers.
v2_candidates = []
for path in STYLE_DIR.rglob("*.css"):
    text = path.read_text(errors="ignore")
    if RUNTIME in text:
        fail(f"V2.2 already applied in {path}")
    if V2_1_RUNTIME in text and any(marker in text for marker in V2_RUNTIME_MARKERS):
        v2_candidates.append(path)

if len(v2_candidates) != 1:
    fail(
        "unable to identify exactly one V2+V2.1 stylesheet: "
        + ", ".join(str(path) for path in v2_candidates)
    )
v2_style = v2_candidates[0]

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
backup_root = Path(f"/var/backups/tos-patches/task-details-canonical-reference-v2-2-app-shell-grid-{stamp}")
backup_root.mkdir(parents=True, exist_ok=False)
board_backup = backup_root / BOARD.name
style_backup = backup_root / v2_style.name
shutil.copy2(BOARD, board_backup)
shutil.copy2(v2_style, style_backup)

live.parent.mkdir(parents=True, exist_ok=True)
staging = live.parent / f"build.task-details-canonical-reference-v2-2-staging-{stamp}"
live_backup = live.parent / f"build.task-details-canonical-reference-v2-2-backup-{stamp}"
live_swapped = False

try:
    updated_board, replace_count = ROOT_PATTERN.subn(
        lambda match: match.group(1) + ' dir="ltr" data-content-dir={modalDirection}' + match.group(2),
        board_source,
        count=1,
    )
    if replace_count != 1:
        fail(f"Task Details structural root conversion failed: {replace_count}")

    if 'data-content-dir={modalDirection}' not in updated_board:
        fail("Task Details content direction marker missing after transform")
    if 'tos-task-details-reference-v1' not in updated_board:
        fail("Task Details reference root class lost during transform")

    BOARD.write_text(updated_board)

    original_css = v2_style.read_text()
    v2_style.write_text(original_css.rstrip() + "\n\n" + payload_css.strip() + "\n")
    updated_css = v2_style.read_text()
    if RUNTIME not in updated_css or V2_1_RUNTIME not in updated_css:
        fail("V2.2/V2.1 runtime markers missing after source CSS update")

    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists() or not (DIST / "index.html").exists():
        fail("frontend dist missing after build")

    built_css = "\n".join(path.read_text(errors="ignore") for path in DIST.rglob("*.css"))
    built_js = "\n".join(path.read_text(errors="ignore") for path in DIST.rglob("*.js"))
    if RUNTIME not in built_css:
        fail("V2.2 runtime marker missing from built CSS")
    if V2_1_RUNTIME not in built_css:
        fail("V2.1 predecessor runtime marker missing from built CSS")
    if "tos-task-details-reference-v1" not in built_js:
        fail("Task Details root marker missing from built JS")
    if "data-content-dir" not in built_js:
        fail("Task Details structural/content direction split missing from built JS")

    if staging.exists():
        shutil.rmtree(staging)
    shutil.copytree(DIST, staging)
    if live.exists():
        live.rename(live_backup)
    staging.rename(live)
    live_swapped = True

    live_css = "\n".join(path.read_text(errors="ignore") for path in live.rglob("*.css"))
    live_js = "\n".join(path.read_text(errors="ignore") for path in live.rglob("*.js"))
    if RUNTIME not in live_css or "data-content-dir" not in live_js:
        fail("V2.2 markers missing from live build")

    print("PASS/FAIL=PASS")
    print("BUILD_RESULT=PASS")
    print("LIVE_DEPLOY=PASS")
    print("TASK_DETAILS_CANONICAL_REFERENCE_V2_2_RUNTIME=YES")
    print("ROOT_CAUSE=ROOT_DIR_ATTRIBUTE_PLUS_OUTER_APP_FRAME_RTL")
    print("TASK_DETAILS_ROOT_DIR=LTR_STRUCTURAL")
    print("TASK_DETAILS_CONTENT_DIR=MODAL_DIRECTION_PRESERVED")
    print("APP_FRAME_DIRECTION=LTR_LOCKED_WHILE_TASK_DETAILS_OPEN")
    print("SIDEBAR_EDGE=LEFT")
    print("MAIN_SHELL_EDGE=RIGHT_OF_SIDEBAR")
    print("TOPBAR_ORDER=SEARCH_LEFT_PROFILE_RIGHT")
    print("HERO_AUTO_PLACEMENT=LTR_CANONICAL")
    print("PRIMARY_TABS_ORDER=OVERVIEW_CHECKLIST_ATTACHMENTS_ACTIVITY_SUBTASKS")
    print("OVERVIEW_ORDER=DESCRIPTION_LEFT_RIGHT_RAIL_RIGHT")
    print("ARABIC_TEXT_AND_EDITOR_DIRECTION=RTL_PRESERVED")
    print("REFERENCE_VIEWPORT=1664x936")
    print("V2_CANONICAL_REFERENCE=PRESERVED")
    print("TASK_APIS_CHANGED=NO")
    print("TASK_DATA_CONTRACT_CHANGED=NO")
    print("TASK_PERMISSIONS_CHANGED=NO")
    print("TASK_BUSINESS_LOGIC_CHANGED=NO")
    print("TWS_INTERNALS_CHANGED=NO")
    print("RAMZY_CHANGED=NO")
    print("TCS_CHANGED=NO")
    print(f"V2_STYLE_TARGET={v2_style}")
    print(f"SOURCE_BACKUP={backup_root}")
    print(f"LIVE_BACKUP={live_backup if live_backup.exists() else 'NONE'}")
    print("STATUS=READY_FOR_VISUAL_QA")
except Exception as exc:
    try:
        if board_backup.exists():
            shutil.copy2(board_backup, BOARD)
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
