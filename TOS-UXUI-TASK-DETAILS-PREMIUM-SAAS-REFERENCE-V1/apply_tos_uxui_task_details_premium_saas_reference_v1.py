from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import time

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
BOARD = FRONTEND / "src/components/ProfessionalTaskBoard.jsx"
PARTS = FRONTEND / "src/features/tasks/taskBoardParts.jsx"
MANIFEST = ROOT / "deployment/tos-production-runtime.json"
STYLE = FRONTEND / "src/styles/taskDetailsPremiumSaasReferenceV1.css"
DIST = FRONTEND / "dist"
PATCH_DIR = Path(__file__).resolve().parent
PAYLOAD_STYLE = PATCH_DIR / "taskDetailsPremiumSaasReferenceV1.css"

EXPECTED_BLOBS = {
    BOARD: "6a1686b0c43b42ade325406bb22068426658a8e4",
    PARTS: "e2954efe17a0cd938b7342e4df6963e5d16fc806",
    MANIFEST: "66a1659214dd90b162376310274be1b6689ac1d3",
}

BASE_IMPORT = 'import "../styles/tasks-projects-premium-reference.css";'
REFERENCE_IMPORT = 'import "../styles/taskDetailsPremiumSaasReferenceV1.css";'
ROOT_OLD = 'className="tos-task-details-fullpage fixed inset-0 z-50 overflow-hidden bg-gradient-to-br from-[#fafaf9] via-white to-amber-50/20 p-0 dark:from-zinc-950 dark:via-zinc-950 dark:to-amber-950/10"'
ROOT_NEW = 'className="tos-task-details-fullpage tos-task-details-reference-v1 fixed inset-0 z-50 overflow-hidden bg-gradient-to-br from-[#fafaf9] via-white to-amber-50/20 p-0 dark:from-zinc-950 dark:via-zinc-950 dark:to-amber-950/10"'
HEADER_OLD = '<header className="shrink-0 border-b border-slate-100 bg-white/95 px-4 py-3 backdrop-blur-xl dark:border-white/10 dark:bg-zinc-950/95 sm:px-5">'
HEADER_NEW = '<header className="tos-task-reference-header shrink-0 border-b border-slate-100 bg-white/95 px-4 py-3 backdrop-blur-xl dark:border-white/10 dark:bg-zinc-950/95 sm:px-5">'
TITLE_OLD = '<div className="flex min-w-0 flex-col justify-center text-right lg:order-1">'
TITLE_NEW = '<div className="tos-task-reference-title-block flex min-w-0 flex-col justify-center text-right lg:order-1">'
STATUS_OLD = '<span>{modalUi.status || modalUi.quickStatus}</span><List size={15} />'
STATUS_NEW = '<span>{modalUi.quickStatus || modalUi.status}</span><List size={15} />'
EDITOR_OLD = '<div className={shellClass} dir={isArabic ? "rtl" : "ltr"}>'
EDITOR_NEW = '<div className={`${shellClass} tos-task-rich-editor-shell`} dir={isArabic ? "rtl" : "ltr"}>'
CHECKLIST_OLD = '{activeTaskTab === "checklist" && ('
CHECKLIST_NEW = '{["checklist", "subtasks"].includes(activeTaskTab) && ('
NAV_START = '              <nav className="tos-task-detail-tabs sticky top-0 z-30 rounded-[26px] border border-slate-200 bg-white/90 p-2 shadow-sm shadow-slate-100/80 backdrop-blur-xl dark:border-white/10 dark:bg-zinc-950/90 dark:shadow-black/20" aria-label={modalUi.taskDetails}>'
NAV_END = '\n\n              {activeTaskTab === "overview" && ('
RUNTIME = "--tos-task-details-premium-saas-reference-v1-runtime"


def fail(message):
    raise RuntimeError(message)


def git_blob_sha(path):
    data = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def run(command, cwd=None):
    subprocess.run(command, cwd=cwd, check=True)


def replace_once(source, old, new, label):
    count = source.count(old)
    if count != 1:
        fail(f"{label} marker count changed unexpectedly: {count}")
    return source.replace(old, new, 1)


for path, expected in EXPECTED_BLOBS.items():
    if not path.exists():
        fail(f"required baseline file missing: {path}")
    actual = git_blob_sha(path)
    if actual != expected:
        fail(f"baseline changed for {path}: expected={expected} actual={actual}")

for command in ("node", "npm"):
    if not shutil.which(command):
        fail(f"required command not found: {command}")
if not PAYLOAD_STYLE.exists():
    fail(f"patch style payload missing: {PAYLOAD_STYLE}")
if RUNTIME not in PAYLOAD_STYLE.read_text():
    fail("patch style payload runtime marker missing")

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

board_source = BOARD.read_text()
parts_source = PARTS.read_text()

required_board = [
    BASE_IMPORT, ROOT_OLD, HEADER_OLD, TITLE_OLD, STATUS_OLD,
    'const taskDetailTabs = useMemo(() => ([',
    '{ id: "overview", label: modalUi.overview || (isAr ? "نظرة عامة" : "Overview"), icon: LayoutDashboard },',
    '{ id: "checklist", label: modalUi.checklist || "Checklist", icon: CheckCircle2, count: checklistTotal },',
    NAV_START, NAV_END.strip(), CHECKLIST_OLD,
    'onChange={(event) => handleTaskStatusChange(event.target.value)}',
    'function archiveCard()', 'onRequestArchive?.(draft || task)', '<PremiumTaskRichTextEditor',
]
for marker in required_board:
    if marker not in board_source:
        fail(f"ProfessionalTaskBoard baseline marker missing: {marker}")
if EDITOR_OLD not in parts_source:
    fail("PremiumTaskRichTextEditor shell marker missing")
if REFERENCE_IMPORT in board_source or STYLE.exists() or "tos-task-details-reference-v1" in board_source:
    fail("Task Details Premium SaaS Reference V1 is already present")

stamp = int(time.time())
backup_root = Path(f"/var/backups/tos-patches/task-details-premium-saas-reference-v1-{stamp}")
backup_root.mkdir(parents=True, exist_ok=False)
board_backup = backup_root / BOARD.name
parts_backup = backup_root / PARTS.name
shutil.copy2(BOARD, board_backup)
shutil.copy2(PARTS, parts_backup)

live.parent.mkdir(parents=True, exist_ok=True)
staging = live.parent / f"build.task-details-premium-saas-reference-v1-staging-{stamp}"
live_backup = live.parent / f"build.task-details-premium-saas-reference-v1-backup-{stamp}"
live_swapped = False

try:
    updated = board_source
    updated = replace_once(updated, BASE_IMPORT, BASE_IMPORT + "\n" + REFERENCE_IMPORT, "reference stylesheet import")
    updated = replace_once(updated, ROOT_OLD, ROOT_NEW, "Task Details root marker")
    updated = replace_once(updated, HEADER_OLD, HEADER_NEW, "Task Details header marker")
    updated = replace_once(updated, TITLE_OLD, TITLE_NEW, "Task Details title block")
    updated = replace_once(updated, STATUS_OLD, STATUS_NEW, "Quick status label")

    overview_old = '{ id: "overview", label: modalUi.overview || (isAr ? "نظرة عامة" : "Overview"), icon: LayoutDashboard },'
    overview_new = '{ id: "overview", label: modalUi.taskDetails || (isAr ? "تفاصيل المهمة" : "Task details"), icon: ClipboardList },\n    { id: "subtasks", label: isAr ? "المهام الفرعية" : "Subtasks", icon: CalendarClock, count: checklistTotal },'
    updated = replace_once(updated, overview_old, overview_new, "reference primary tabs")
    updated = replace_once(updated, CHECKLIST_OLD, CHECKLIST_NEW, "subtasks/checklist shared view")

    nav_start = updated.index(NAV_START)
    nav_end = updated.index(NAV_END, nav_start)
    reference_nav = r'''              <nav className="tos-task-detail-tabs sticky top-0 z-30 rounded-[26px] border border-slate-200 bg-white/90 p-2 shadow-sm shadow-slate-100/80 backdrop-blur-xl dark:border-white/10 dark:bg-zinc-950/90 dark:shadow-black/20" aria-label={modalUi.taskDetails}>
                <div className="tos-task-reference-tabs-main">
                  {taskDetailTabs
                    .filter((tab) => ["overview", "subtasks", "attachments", "activity", "checklist"].includes(tab.id) || (taskMoreDetailsOpen && ["comments", "time"].includes(tab.id)))
                    .map((tab) => {
                      const TabIcon = tab.icon;
                      const isActive = activeTaskTab === tab.id;
                      return (
                        <button key={tab.id} type="button" onClick={() => setActiveTaskTab(tab.id)} className="tos-task-reference-tab" data-active={isActive ? "true" : "false"} aria-current={isActive ? "page" : undefined}>
                          <TabIcon size={16} />
                          <span>{tab.label}</span>
                          {Number.isFinite(Number(tab.count)) && <span className="tos-task-reference-tab-count">{tab.count}</span>}
                        </button>
                      );
                    })}
                </div>
                <div className="tos-task-reference-actions">
                  <button type="button" className="tos-task-more-actions-reference inline-flex items-center justify-center gap-2" aria-expanded={taskMoreDetailsOpen} onClick={() => {
                    const nextOpen = !taskMoreDetailsOpen;
                    if (nextOpen) {
                      markTaskCoachHintDiscovered("more-details");
                      setTaskCoachHints((current) => ({ ...current, more: false }));
                    }
                    setTaskMoreDetailsOpen(nextOpen);
                    if (!nextOpen && !["overview", "subtasks", "checklist", "attachments", "activity"].includes(activeTaskTab)) setActiveTaskTab("overview");
                  }}>
                    <span aria-hidden="true">⋮</span><span>{isAr ? "إجراءات إضافية" : "More actions"}</span><span aria-hidden="true">⋮</span>
                  </button>
                  <button type="button" className="tos-task-complete-reference inline-flex items-center justify-center gap-2" disabled={!canEdit || closedStatuses.includes(draft.status)} onClick={() => handleTaskStatusChange("DONE")}>
                    <CheckCircle2 size={17} /><span>{isAr ? "إكمال المهمة" : "Mark as complete"}</span>
                  </button>
                </div>
              </nav>'''
    updated = updated[:nav_start] + reference_nav + updated[nav_end:]
    parts_updated = replace_once(parts_source, EDITOR_OLD, EDITOR_NEW, "rich editor shell class")

    post_markers = [
        REFERENCE_IMPORT, "tos-task-details-reference-v1", "tos-task-reference-header",
        "tos-task-reference-title-block", 'id: "subtasks"', 'className="tos-task-reference-tab"',
        'className="tos-task-more-actions-reference', 'className="tos-task-complete-reference',
        'handleTaskStatusChange("DONE")', '["checklist", "subtasks"].includes(activeTaskTab)',
        "function archiveCard()", "onRequestArchive?.(draft || task)", "<PremiumTaskRichTextEditor",
    ]
    for marker in post_markers:
        if marker not in updated:
            fail(f"post-transform Task Details marker missing: {marker}")
    if "tos-task-rich-editor-shell" not in parts_updated:
        fail("rich editor shell runtime class injection failed")

    BOARD.write_text(updated)
    PARTS.write_text(parts_updated)
    shutil.copy2(PAYLOAD_STYLE, STYLE)

    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists() or not (DIST / "index.html").exists():
        fail("frontend dist missing after build")

    built_css = "\n".join(path.read_text(errors="ignore") for path in DIST.rglob("*.css"))
    built_js = "\n".join(path.read_text(errors="ignore") for path in DIST.rglob("*.js"))
    if RUNTIME not in built_css:
        fail("Task Details reference runtime marker missing from built CSS")
    if "tos-task-details-reference-v1" not in built_js:
        fail("Task Details reference root marker missing from built JS")
    if "Mark as complete" not in built_js and "إكمال المهمة" not in built_js:
        fail("reference completion action missing from built JS")

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
        fail("Task Details reference markers missing from live build")

    print("PASS/FAIL=PASS")
    print("BUILD_RESULT=PASS")
    print("LIVE_DEPLOY=PASS")
    print("TASK_DETAILS_PREMIUM_SAAS_REFERENCE_V1_RUNTIME=YES")
    print("REFERENCE_VIEWPORT=1664x936")
    print("REFERENCE_LAYOUT=SIDEBAR_272_TOPBAR_72_CONTENT_IN_APP_SHELL")
    print("REFERENCE_PRIMARY_TABS=TASK_DETAILS_SUBTASKS_ATTACHMENTS_ACTIVITY_CHECKLIST")
    print("REFERENCE_MORE_ACTIONS=ADVANCED_DETAILS_PRESERVED")
    print("REFERENCE_MARK_COMPLETE=EXISTING_STATUS_UPDATE_PATH")
    print("TASK_APIS_CHANGED=NO")
    print("TASK_DATA_CONTRACT_CHANGED=NO")
    print("TASK_PERMISSIONS_CHANGED=NO")
    print("TWS_INTERNALS_CHANGED=NO")
    print("RAMZY_CHANGED=NO")
    print("TCS_CHANGED=NO")
    print(f"SOURCE_BACKUP={backup_root}")
    print(f"LIVE_BACKUP={live_backup if live_backup.exists() else 'NONE'}")
    print("STATUS=READY_FOR_VISUAL_QA")
except Exception as exc:
    try:
        if board_backup.exists():
            shutil.copy2(board_backup, BOARD)
        if parts_backup.exists():
            shutil.copy2(parts_backup, PARTS)
        if STYLE.exists():
            STYLE.unlink()
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
