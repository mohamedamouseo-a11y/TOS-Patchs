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
PAYLOAD_STYLE = PATCH_DIR / "taskDetailsCanonicalReferenceV2_5ExactFourControlsPhysicalGridLock.css"

RUNTIME = "--tos-task-details-canonical-reference-v2-5-exact-four-controls-physical-grid-runtime"
V2_4_RUNTIME = "--tos-task-details-canonical-reference-v2-4-four-control-overview-order-runtime"
V2_3_RUNTIME = "--tos-task-details-canonical-reference-v2-3-internal-fidelity-runtime"
V2_2_RUNTIME = "--tos-task-details-canonical-reference-v2-2-app-shell-grid-lock-runtime"
V2_1_RUNTIME = "--tos-task-details-canonical-reference-v2-1-rtl-structural-geometry-runtime"
V2_RUNTIME_MARKERS = (
    "--tos-task-details-canonical-reference-v2-runtime",
    "--tos-task-details-canonical-v2-runtime",
)

# Exact V2.4 insertion. V2.5 removes this duplicate only; it does not touch the
# pre-existing canonical Assignees control.
V24_DUPLICATE_ASSIGNEE_CARD = r'''
                    <button
                      type="button"
                      onClick={() => setTaskSidebarExpanded(true)}
                      className="tos-task-assignees-hero-card rounded-[18px] border border-slate-100 bg-white px-3.5 py-3 text-start shadow-sm dark:border-white/10 dark:bg-zinc-900"
                      aria-label={isAr ? "المكلفون" : "Assignees"}
                      aria-pressed={taskSidebarExpanded}
                      title={isAr ? "فتح تفاصيل التكليف" : "Open assignee details"}
                      dir={modalDirection}
                    >
                      <span className="mb-2 flex items-center justify-between gap-2 text-xs font-black text-slate-400 dark:text-zinc-500">
                        <span>{modalUi.assignee}</span>
                        <Users size={15} />
                      </span>
                      <span className="tos-task-assignees-hero-value mt-auto flex min-w-0 items-center justify-between gap-2">
                        <span className="truncate text-sm font-black text-slate-950 dark:text-white">
                          {currentAssigneeIds.length
                            ? `${currentAssigneeIds.length} ${isAr ? "مكلف" : "assigned"}`
                            : (isAr ? "غير مسندة" : "Unassigned")}
                        </span>
                        <span className="inline-flex min-w-7 items-center justify-center rounded-full bg-amber-50 px-2 py-1 text-[11px] font-black text-amber-700 ring-1 ring-amber-100 dark:bg-amber-500/10 dark:text-amber-200 dark:ring-amber-400/20">
                          {currentAssigneeIds.length}
                        </span>
                      </span>
                    </button>'''

LAYOUT_PATTERN = re.compile(r'(className="[^"]*\btos-task-details-layout\b[^"]*)xl:grid-cols-\[320px_minmax\(0,1fr\)\]([^\"]*")')
MAIN_PATTERN = re.compile(r'(className="[^"]*\btos-task-main-column\b[^"]*)xl:order-2([^\"]*")')
RAIL_PATTERN = re.compile(r'(className="[^"]*\btos-task-side-rail\b[^"]*)xl:order-1([^\"]*")')


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
    fail("V2.5 CSS runtime marker missing from payload")

# Preserved scope: V2.5 is not allowed to reopen shell/topbar/tabs/hero-height.
for forbidden in (
    ".tos-premium-sidebar",
    ".tos-premium-app-frame",
    ".tos-premium-main-shell",
    ".tos-premium-topbar",
    ".tos-task-detail-tabs",
    ".tos-task-reference-tabs-main",
    "--tos-v23-hero-height",
):
    if forbidden in payload_css:
        fail(f"V2.5 payload illegally touches preserved scope: {forbidden}")

board_source = BOARD.read_text()
for marker in (
    "tos-task-details-reference-v1",
    'data-content-dir={modalDirection}',
    "tos-task-details-layout",
    "tos-task-main-column",
    "tos-task-side-rail",
    "tos-task-summary-controls",
    "tos-task-start-date-card",
    "tos-task-assignees-hero-card",
    "PremiumTaskRichTextEditor",
):
    if marker not in board_source:
        fail(f"required V2.4 Task Details marker missing: {marker}")

if board_source.count("tos-task-assignees-hero-card") != 1:
    fail("expected exactly one V2.4 duplicate Assignees Hero card")
if board_source.count(V24_DUPLICATE_ASSIGNEE_CARD) != 1:
    fail("exact V2.4 duplicate Assignees card block does not match current source")
if board_source.count("tos-task-start-date-card") != 1:
    fail("expected exactly one preserved Start date advanced control")

for pattern, label in (
    (LAYOUT_PATTERN, "legacy layout grid token"),
    (MAIN_PATTERN, "legacy main order token"),
    (RAIL_PATTERN, "legacy rail order token"),
):
    matches = list(pattern.finditer(board_source))
    if len(matches) != 1:
        fail(f"expected exactly one {label}, found {len(matches)}")

# Locate the single canonical stylesheet with the complete V2 -> V2.4 lineage.
v2_candidates = []
for path in STYLE_DIR.rglob("*.css"):
    text = path.read_text(errors="ignore")
    if RUNTIME in text:
        fail(f"V2.5 already applied in {path}")
    if (
        V2_4_RUNTIME in text
        and V2_3_RUNTIME in text
        and V2_2_RUNTIME in text
        and V2_1_RUNTIME in text
        and any(marker in text for marker in V2_RUNTIME_MARKERS)
    ):
        v2_candidates.append(path)

if len(v2_candidates) != 1:
    fail(
        "unable to identify exactly one V2 through V2.4 stylesheet: "
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
backup_root = Path(f"/var/backups/tos-patches/task-details-canonical-reference-v2-5-exact-four-grid-{stamp}")
backup_root.mkdir(parents=True, exist_ok=False)
board_backup = backup_root / BOARD.name
style_backup = backup_root / v2_style.name
shutil.copy2(BOARD, board_backup)
shutil.copy2(v2_style, style_backup)

live.parent.mkdir(parents=True, exist_ok=True)
staging = live.parent / f"build.task-details-canonical-reference-v2-5-staging-{stamp}"
live_backup = live.parent / f"build.task-details-canonical-reference-v2-5-backup-{stamp}"
live_swapped = False

try:
    # 1) Remove only the V2.4 duplicate card. The original canonical Assignees
    # control remains untouched.
    updated_board = board_source.replace(V24_DUPLICATE_ASSIGNEE_CARD, "", 1)
    if "tos-task-assignees-hero-card" in updated_board:
        fail("V2.4 duplicate Assignees card marker still present after removal")

    # 2) Lock physical Overview geometry in JSX/Tailwind, not only CSS order.
    updated_board, layout_count = LAYOUT_PATTERN.subn(
        r'\1xl:grid-cols-[minmax(0,1fr)_304px]\2', updated_board, count=1
    )
    updated_board, main_count = MAIN_PATTERN.subn(r'\1xl:order-1\2', updated_board, count=1)
    updated_board, rail_count = RAIL_PATTERN.subn(r'\1xl:order-2\2', updated_board, count=1)
    if (layout_count, main_count, rail_count) != (1, 1, 1):
        fail(f"physical grid transform counts invalid: layout={layout_count}, main={main_count}, rail={rail_count}")

    for required_after in (
        "xl:grid-cols-[minmax(0,1fr)_304px]",
        "tos-task-main-column",
        "tos-task-side-rail",
        "tos-task-start-date-card",
        'data-content-dir={modalDirection}',
    ):
        if required_after not in updated_board:
            fail(f"required source marker missing after V2.5 transform: {required_after}")

    BOARD.write_text(updated_board)

    v2_style.write_text(original_css.rstrip() + "\n\n" + payload_css.strip() + "\n")
    updated_css = v2_style.read_text()
    for marker in (RUNTIME, V2_4_RUNTIME, V2_3_RUNTIME, V2_2_RUNTIME, V2_1_RUNTIME):
        if marker not in updated_css:
            fail(f"required runtime marker missing after CSS update: {marker}")

    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists() or not (DIST / "index.html").exists():
        fail("frontend dist missing after build")

    built_css = "\n".join(path.read_text(errors="ignore") for path in DIST.rglob("*.css"))
    built_js = "\n".join(path.read_text(errors="ignore") for path in DIST.rglob("*.js"))

    for marker in (RUNTIME, V2_4_RUNTIME, V2_3_RUNTIME, V2_2_RUNTIME, V2_1_RUNTIME):
        if marker not in built_css:
            fail(f"required runtime marker missing from built CSS: {marker}")

    if "tos-task-assignees-hero-card" in built_js:
        fail("duplicate V2.4 Assignees card survived in built JS")
    for marker in (
        "tos-task-details-reference-v1",
        "data-content-dir",
        "tos-task-summary-controls",
        "tos-task-start-date-card",
    ):
        if marker not in built_js:
            fail(f"required Task Details marker missing from built JS: {marker}")

    if staging.exists():
        shutil.rmtree(staging)
    shutil.copytree(DIST, staging)
    if live.exists():
        live.rename(live_backup)
    staging.rename(live)
    live_swapped = True

    live_css = "\n".join(path.read_text(errors="ignore") for path in live.rglob("*.css"))
    live_js = "\n".join(path.read_text(errors="ignore") for path in live.rglob("*.js"))
    if RUNTIME not in live_css or V2_4_RUNTIME not in live_css:
        fail("V2.5/V2.4 markers missing from live build")
    if "tos-task-assignees-hero-card" in live_js:
        fail("duplicate V2.4 Assignees card survived in live JS")
    if "data-content-dir" not in live_js:
        fail("V2.2 direction marker missing from live JS")

    print("PASS/FAIL=PASS")
    print("BUILD_RESULT=PASS")
    print("LIVE_DEPLOY=PASS")
    print("TASK_DETAILS_CANONICAL_REFERENCE_V2_5_RUNTIME=YES")
    print("V2_2_APP_SHELL_LOCK=PRESERVED")
    print("V2_2_STRUCTURAL_LTR=PRESERVED")
    print("V2_3_HERO_HEIGHT=PRESERVED")
    print("V2_3_TABS_PLACEMENT=PRESERVED")
    print("V2_4_START_DATE_ADVANCED_PATH=PRESERVED")
    print("V2_4_DUPLICATE_ASSIGNEE_CARD=REMOVED")
    print("HERO_VISIBLE_PRIMARY_CONTROLS=EXACTLY_FOUR_EXPECTED")
    print("HERO_PRIMARY_CONTROLS=ASSIGNEES_STATUS_PRIORITY_DUE_DATE")
    print("OVERVIEW_DOM_GRID=MAIN_FIRST_RAIL_SECOND")
    print("OVERVIEW_PHYSICAL_ORDER=DESCRIPTION_LEFT_RIGHT_RAIL_RIGHT")
    print("RIGHT_RAIL_WIDTH=304PX")
    print("RIGHT_RAIL_CONTENT=PRESERVED")
    print("FLOATING_TCS_LAUNCHER=UNCHANGED")
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
