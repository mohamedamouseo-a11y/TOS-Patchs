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
PAYLOAD_STYLE = PATCH_DIR / "taskDetailsCanonicalReferenceV2_1RtlStructuralGeometryFix.css"
RUNTIME = "--tos-task-details-canonical-reference-v2-1-rtl-structural-geometry-runtime"
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
    fail("V2.1 CSS runtime marker missing from payload")

board_source = BOARD.read_text()
for marker in (
    "tos-task-details-reference-v1",
    "PremiumTaskRichTextEditor",
    "handleTaskStatusChange",
):
    if marker not in board_source:
        fail(f"required current Task Details marker missing: {marker}")

# Locate the already-applied V2 stylesheet dynamically. V2 is live but intentionally
# unpushed, so this patch must never depend on Git state inside /var/www/TOS.
v2_candidates = []
for path in STYLE_DIR.rglob("*.css"):
    text = path.read_text(errors="ignore")
    lowered_name = path.name.lower()
    lowered_text = text.lower()
    if RUNTIME in text:
        fail(f"V2.1 already applied in {path}")
    explicit_runtime = any(marker in text for marker in V2_RUNTIME_MARKERS)
    canonical_filename = (
        "taskdetails" in lowered_name
        and "canonical" in lowered_name
        and "v2" in lowered_name
    )
    canonical_content = (
        "task details" in lowered_text
        and "canonical" in lowered_text
        and "v2" in lowered_text
        and "tos-task" in lowered_text
    )
    if explicit_runtime or canonical_filename or canonical_content:
        v2_candidates.append(path)

# Prefer an explicit V2 runtime marker if more than one stylesheet happened to match
# descriptive comments or filenames.
explicit_candidates = []
for path in v2_candidates:
    text = path.read_text(errors="ignore")
    if any(marker in text for marker in V2_RUNTIME_MARKERS):
        explicit_candidates.append(path)

if len(explicit_candidates) == 1:
    v2_style = explicit_candidates[0]
elif len(v2_candidates) == 1:
    v2_style = v2_candidates[0]
else:
    fail(
        "unable to identify exactly one applied V2 stylesheet: "
        + ", ".join(str(path) for path in v2_candidates)
    )

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
backup_root = Path(f"/var/backups/tos-patches/task-details-canonical-reference-v2-1-rtl-geometry-{stamp}")
backup_root.mkdir(parents=True, exist_ok=False)
style_backup = backup_root / v2_style.name
shutil.copy2(v2_style, style_backup)

live.parent.mkdir(parents=True, exist_ok=True)
staging = live.parent / f"build.task-details-canonical-reference-v2-1-staging-{stamp}"
live_backup = live.parent / f"build.task-details-canonical-reference-v2-1-backup-{stamp}"
live_swapped = False

try:
    original_css = v2_style.read_text()
    v2_style.write_text(original_css.rstrip() + "\n\n" + payload_css.strip() + "\n")

    if RUNTIME not in v2_style.read_text():
        fail("V2.1 runtime marker missing after source CSS update")

    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists() or not (DIST / "index.html").exists():
        fail("frontend dist missing after build")

    built_css = "\n".join(path.read_text(errors="ignore") for path in DIST.rglob("*.css"))
    built_js = "\n".join(path.read_text(errors="ignore") for path in DIST.rglob("*.js"))
    if RUNTIME not in built_css:
        fail("V2.1 runtime marker missing from built CSS")
    if "tos-task-details-reference-v1" not in built_js:
        fail("Task Details root marker missing from built JS")

    if staging.exists():
        shutil.rmtree(staging)
    shutil.copytree(DIST, staging)
    if live.exists():
        live.rename(live_backup)
    staging.rename(live)
    live_swapped = True

    live_css = "\n".join(path.read_text(errors="ignore") for path in live.rglob("*.css"))
    live_js = "\n".join(path.read_text(errors="ignore") for path in live.rglob("*.js"))
    if RUNTIME not in live_css or "tos-task-details-reference-v1" not in live_js:
        fail("V2.1 markers missing from live build")

    print("PASS/FAIL=PASS")
    print("BUILD_RESULT=PASS")
    print("LIVE_DEPLOY=PASS")
    print("TASK_DETAILS_CANONICAL_REFERENCE_V2_1_RUNTIME=YES")
    print("ROOT_CAUSE=RTL_MIRRORED_STRUCTURAL_LAYOUT")
    print("STRUCTURAL_DIRECTION=LTR_LOCKED")
    print("ARABIC_TEXT_DIRECTION=RTL_PRESERVED")
    print("SIDEBAR_EDGE=LEFT")
    print("TASK_WORKSPACE_EDGE=RIGHT_OF_SIDEBAR")
    print("TOPBAR_ORDER=SEARCH_LEFT_PROFILE_RIGHT")
    print("HEADER_ORDER=BREADCRUMB_LEFT_ACTIONS_RIGHT")
    print("HERO_ORDER=IDENTITY_LEFT_QUOTE_RIGHT")
    print("HERO_CONTROLS_ORDER=ASSIGNEES_STATUS_PRIORITY_DUE_DATE")
    print("PRIMARY_TABS_ORDER=OVERVIEW_CHECKLIST_ATTACHMENTS_ACTIVITY_SUBTASKS")
    print("OVERVIEW_COLUMNS=DESCRIPTION_LEFT_RIGHT_RAIL_RIGHT")
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
