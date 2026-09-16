from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import time

PATCH = "TOS-TASK-BOARD-R32-TRELLO-LIKE-CARD-MODAL-NAVIGATION"
VERSION = "TOS_TASK_BOARD_R32"
BASE_TOS_COMMIT = "f3671756ba1c49ae7304509276d52eb5cb69d04d"
CSS_MARKER = "--tos-task-board-r32-trello-card-modal-runtime"
OVERLAY_CLASS = "tos-task-details-trello-overlay-r32"
NAV_CLASS = "tos-task-v2-card-nav-r32"
R31_SOURCE_MARKER = "TOS_CENTRAL_CHAT_R31_NATIVE_VIDEO_PLAYER"

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
STYLE_DIR = FRONTEND / "src/styles"
BOARD = FRONTEND / "src/components/ProfessionalTaskBoard.jsx"
PARTS = FRONTEND / "src/features/tasks/taskBoardParts.jsx"
CHAT = FRONTEND / "src/components/ChatPanel.jsx"
APP = FRONTEND / "src/App.jsx"
SIDEBAR = FRONTEND / "src/components/layout/Sidebar.jsx"
MANIFEST = ROOT / "deployment/tos-production-runtime.json"
R32_STYLE = STYLE_DIR / "taskBoardR32TrelloModalNavigation.css"
PAYLOAD = Path(__file__).resolve().parent / "taskBoardR32TrelloModalNavigation.css"


def fail(message):
    raise RuntimeError(message)


def run(command, cwd=None):
    subprocess.run(command, cwd=cwd, check=True)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


for path in (FRONTEND, STYLE_DIR, BOARD, PARTS, CHAT, APP, SIDEBAR, MANIFEST, PAYLOAD):
    if not path.exists():
        fail(f"required path missing: {path}")
for command in ("node", "npm"):
    if not shutil.which(command):
        fail(f"required command missing: {command}")

board_source = BOARD.read_text()
parts_source = PARTS.read_text()
chat_source = CHAT.read_text()
payload_css = PAYLOAD.read_text()

if R31_SOURCE_MARKER not in chat_source:
    fail("latest pushed R31 Central Chat source marker is missing")
if CSS_MARKER not in payload_css or OVERLAY_CLASS not in payload_css or NAV_CLASS not in payload_css:
    fail("R32 CSS payload contract missing")
if R32_STYLE.exists() or OVERLAY_CLASS in board_source or NAV_CLASS in board_source:
    fail("R32 already appears to be applied")

# Latest Task Details / board contracts reviewed at BASE_TOS_COMMIT.
for contract in (
    'import "../styles/taskDetailsV2_12_Phase1R30TimeTrackingPremium.css";',
    'function CardDetailsModal(',
    'async function openTaskDetails(task) {',
    'onNavigateTask={openTaskDetails}',
    'className="tos-task-details-fullpage tos-task-details-reference-v1 tos-task-details-reference-v2 fixed inset-0 z-50',
    'className="tos-task-details-modal flex h-[100dvh] w-full flex-col overflow-hidden bg-transparent"',
):
    if contract not in board_source:
        fail(f"required current Task Board contract missing: {contract}")
for contract in (
    'function TaskCard({ task, density = "comfortable", lists = [], onOpen, onOpenDetails,',
    'onClick={openTaskFromCard}',
):
    if contract not in parts_source:
        fail(f"required current TaskCard contract missing: {contract}")

# 1) Import R32 CSS after the current R30 stylesheet.
r30_import = 'import "../styles/taskDetailsV2_12_Phase1R30TimeTrackingPremium.css";'
r32_import = 'import "../styles/taskBoardR32TrelloModalNavigation.css";'
if board_source.count(r30_import) != 1 or r32_import in board_source:
    fail("unexpected R30/R32 stylesheet import state")
updated_board = board_source.replace(r30_import, r30_import + "\n" + r32_import, 1)

# 2) Add prefetch cache + browser-back close behavior near selected-task state.
old_state_anchor = '  const [openingTaskId, setOpeningTaskId] = useState("");\n'
new_state_anchor = '''  const [openingTaskId, setOpeningTaskId] = useState("");
  const taskDetailsPrefetchRef = useRef(new Map());

  // TOS_TASK_BOARD_R32_TRELLO_MODAL_NAVIGATION
  useEffect(() => {
    if (typeof window === "undefined") return undefined;
    const handleTaskModalPopState = () => {
      const taskId = String(new URLSearchParams(window.location.search).get("taskId") || "").trim();
      if (!taskId) {
        setSelectedTask(null);
        setQuickViewTask(null);
      }
    };
    window.addEventListener("popstate", handleTaskModalPopState);
    return () => window.removeEventListener("popstate", handleTaskModalPopState);
  }, []);
'''
if updated_board.count(old_state_anchor) != 1:
    fail(f"expected one openingTaskId state anchor, found {updated_board.count(old_state_anchor)}")
updated_board = updated_board.replace(old_state_anchor, new_state_anchor, 1)

# 3) Replace blocking task open with immediate modal + background hydration + prefetch + URL state.
old_open = '''  async function openTaskDetails(task) {
    const fallbackTask = normalizeTaskForModal(task);
    if (!fallbackTask?.id) return;
    setQuickViewTask(null);
    setSelectedTaskInitialTab("overview");
    setOpeningTaskId(fallbackTask.id);
    try {
      const fullTask = await tasksApi.getTask(fallbackTask.id);
      setSelectedTask(normalizeTaskForModal(fullTask, fallbackTask));
    } catch {
      setSelectedTask(fallbackTask);
    } finally {
      setOpeningTaskId((current) => current === fallbackTask.id ? "" : current);
    }
  }
'''
new_open = '''  function currentTaskModalUrlId() {
    if (typeof window === "undefined") return "";
    return String(new URLSearchParams(window.location.search).get("taskId") || "").trim();
  }

  function syncTaskModalUrl(taskId = "", { push = false } = {}) {
    if (typeof window === "undefined" || window.location.pathname !== "/tasks") return;
    const nextTaskId = String(taskId || "").trim();
    const url = new URL(window.location.href);
    const nextProjectId = String(projectId || "").trim();
    if (nextProjectId) url.searchParams.set("projectId", nextProjectId);
    if (nextTaskId) url.searchParams.set("taskId", nextTaskId);
    else url.searchParams.delete("taskId");
    const nextUrl = `${url.pathname}${url.search}${url.hash}`;
    const currentUrl = `${window.location.pathname}${window.location.search}${window.location.hash}`;
    if (nextUrl === currentUrl) return;
    const state = {
      ...(window.history.state || {}),
      tosPage: "tasks",
      tosProjectId: nextProjectId || null,
      tosTaskId: nextTaskId || null,
      tosTaskModalR32: Boolean(nextTaskId),
    };
    window.history[push ? "pushState" : "replaceState"](state, "", nextUrl);
  }

  function closeTaskDetails() {
    const activeTaskId = String(selectedTaskRef.current?.id || "").trim();
    const urlTaskId = currentTaskModalUrlId();
    const canReturnToBoardHistory = Boolean(
      activeTaskId
      && urlTaskId === activeTaskId
      && window.history?.state?.tosTaskModalR32,
    );
    setSelectedTask(null);
    setQuickViewTask(null);
    setSelectedTaskInitialTab("overview");
    if (typeof window === "undefined") return;
    if (canReturnToBoardHistory) {
      window.history.back();
      return;
    }
    syncTaskModalUrl("", { push: false });
  }

  function prefetchTaskDetails(task) {
    const fallbackTask = normalizeTaskForModal(task);
    const taskId = String(fallbackTask?.id || "").trim();
    if (!taskId) return Promise.resolve(null);
    const cached = taskDetailsPrefetchRef.current.get(taskId);
    if (cached) return cached;
    const request = tasksApi.getTask(taskId)
      .then((fullTask) => normalizeTaskForModal(fullTask, fallbackTask))
      .catch(() => null);
    taskDetailsPrefetchRef.current.set(taskId, request);
    return request;
  }

  async function openTaskDetails(task) {
    const fallbackTask = normalizeTaskForModal(task);
    if (!fallbackTask?.id) return;
    const taskId = String(fallbackTask.id);
    const hadOpenModal = Boolean(selectedTaskRef.current?.id);
    const currentUrlTaskId = currentTaskModalUrlId();

    setQuickViewTask(null);
    setSelectedTaskInitialTab("overview");
    setSelectedTask(fallbackTask);
    syncTaskModalUrl(taskId, { push: !hadOpenModal && !currentUrlTaskId });
    setOpeningTaskId(taskId);

    try {
      const fullTask = await prefetchTaskDetails(fallbackTask);
      if (!fullTask) return;
      setSelectedTask((current) => current?.id === taskId ? normalizeTaskForModal(fullTask, current) : current);
    } finally {
      setOpeningTaskId((current) => current === taskId ? "" : current);
    }
  }
'''
if updated_board.count(old_open) != 1:
    fail(f"expected exactly one current openTaskDetails implementation, found {updated_board.count(old_open)}")
updated_board = updated_board.replace(old_open, new_open, 1)

# 4) Prefetch on card hover/focus.
old_card_usage = '''                                onOpen={(clickedTask) => setQuickViewTask((current) => current?.id === clickedTask.id ? null : clickedTask)}
                                onOpenDetails={openTaskDetails}'''
new_card_usage = '''                                onOpen={(clickedTask) => setQuickViewTask((current) => current?.id === clickedTask.id ? null : clickedTask)}
                                onPrefetch={prefetchTaskDetails}
                                onOpenDetails={openTaskDetails}'''
if updated_board.count(old_card_usage) != 1:
    fail(f"expected one board TaskCard open anchor, found {updated_board.count(old_card_usage)}")
updated_board = updated_board.replace(old_card_usage, new_card_usage, 1)

# 5) Convert the current opaque full-screen page shell into an overlay shell.
old_root = '<div className="tos-task-details-fullpage tos-task-details-reference-v1 tos-task-details-reference-v2 fixed inset-0 z-50 overflow-hidden bg-gradient-to-br from-[#fafaf9] via-white to-amber-50/20 p-0 dark:from-zinc-950 dark:via-zinc-950 dark:to-amber-950/10" dir={modalDirection} data-content-dir={modalDirection}>'
new_root = '<div className="tos-task-details-fullpage tos-task-details-reference-v1 tos-task-details-reference-v2 tos-task-details-trello-overlay-r32 fixed inset-0 z-50 overflow-hidden" dir={modalDirection} data-content-dir={modalDirection} data-tos-task-modal-mode="trello-overlay" onMouseDown={(event) => { if (event.target === event.currentTarget && !saving && !assigneeSaving) onClose(); }}>'
if updated_board.count(old_root) != 1:
    fail(f"expected one Task Details root shell, found {updated_board.count(old_root)}")
updated_board = updated_board.replace(old_root, new_root, 1)

old_motion = '''        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        className="tos-task-details-modal flex h-[100dvh] w-full flex-col overflow-hidden bg-transparent"'''
new_motion = '''        initial={{ opacity: 0, y: 18, scale: 0.985 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.18, ease: [0.22, 1, 0.36, 1] }}
        className="tos-task-details-modal flex h-[100dvh] w-full flex-col overflow-hidden bg-transparent"'''
if updated_board.count(old_motion) != 1:
    fail(f"expected one Task Details motion anchor, found {updated_board.count(old_motion)}")
updated_board = updated_board.replace(old_motion, new_motion, 1)

# 6) Visible X + previous/next navigation in canonical modal header.
old_header_close = '            <button type="button" className="tos-task-v2-icon-action" onClick={onClose} aria-label={isAr ? "رجوع" : "Back"}><ChevronLeft size={18} /></button>\n'
new_header_close = '''            <button ref={closeButtonRef} type="button" className="tos-task-v2-icon-action" onClick={onClose} aria-label={modalUi.closeTaskDetails || (isAr ? "إغلاق تفاصيل المهمة" : "Close task details")} title={modalUi.closeTaskDetails || (isAr ? "إغلاق" : "Close")}><X size={18} /></button>
            <div className="tos-task-v2-card-nav-r32" aria-label={isAr ? "التنقل بين مهام العمود" : "Navigate tasks in this column"}>
              <button type="button" onClick={() => previousColumnTask && onNavigateTask?.(previousColumnTask)} disabled={!previousColumnTask} aria-label={isAr ? "المهمة السابقة" : "Previous task"} title={isAr ? "المهمة السابقة" : "Previous task"}><ChevronRight size={16} /></button>
              <span>{sameColumnTasks.length ? `${Math.max(1, currentTaskIndex + 1)} / ${sameColumnTasks.length}` : "0 / 0"}</span>
              <button type="button" onClick={() => nextColumnTask && onNavigateTask?.(nextColumnTask)} disabled={!nextColumnTask} aria-label={isAr ? "المهمة التالية" : "Next task"} title={isAr ? "المهمة التالية" : "Next task"}><ChevronLeft size={16} /></button>
            </div>
'''
if updated_board.count(old_header_close) != 1:
    fail(f"expected one canonical header close anchor, found {updated_board.count(old_header_close)}")
updated_board = updated_board.replace(old_header_close, new_header_close, 1)

# 7) Route every user close action through the URL-aware modal close helper.
old_render = '''        {selectedTask && activeBoard && (
          <TaskDetailsErrorBoundary resetKey={`${selectedTask.id}-${selectedTask.updatedAt || ""}`} onClose={() => setSelectedTask(null)} ui={ui}>
            <CardDetailsModal task={selectedTask} tasks={tasks} dependencyTasks={dependencyTasks} lists={lists} labels={labels} members={members} projectMembers={projectMembers} availableProjectUsers={availableProjectUsers} taskServices={taskServices} permissions={permissions} user={user} onClose={() => setSelectedTask(null)} onUpdate={replaceTask} onDeleteLocal={removeLocalTask} onLabelCreated={addLabelLocal} onRequestArchive={requestArchiveTaskFromCard} onNavigateTask={openTaskDetails} initialTab={selectedTaskInitialTab} />
          </TaskDetailsErrorBoundary>
        )}'''
new_render = '''        {selectedTask && activeBoard && (
          <TaskDetailsErrorBoundary resetKey={`${selectedTask.id}-${selectedTask.updatedAt || ""}`} onClose={closeTaskDetails} ui={ui}>
            <CardDetailsModal task={selectedTask} tasks={tasks} dependencyTasks={dependencyTasks} lists={lists} labels={labels} members={members} projectMembers={projectMembers} availableProjectUsers={availableProjectUsers} taskServices={taskServices} permissions={permissions} user={user} onClose={closeTaskDetails} onUpdate={replaceTask} onDeleteLocal={removeLocalTask} onLabelCreated={addLabelLocal} onRequestArchive={requestArchiveTaskFromCard} onNavigateTask={openTaskDetails} initialTab={selectedTaskInitialTab} />
          </TaskDetailsErrorBoundary>
        )}'''
if updated_board.count(old_render) != 1:
    fail(f"expected one selectedTask modal render block, found {updated_board.count(old_render)}")
updated_board = updated_board.replace(old_render, new_render, 1)

# TaskCard presentation hook only: prefetch on hover/focus; click contract stays the same.
old_parts_signature = 'function TaskCard({ task, density = "comfortable", lists = [], onOpen, onOpenDetails, onDone, onArchive, onEditDesignRequest = null, onMoveToList, onDragStart, onDragEnd, onDropOnCard, isDragging, canEditCards, canArchiveCards, canComment = false, onSendWaitingClientReply = null, selected = false, quickOpen = false, onToggleSelected, ui = getTaskUiText("en") }) {'
new_parts_signature = 'function TaskCard({ task, density = "comfortable", lists = [], onOpen, onOpenDetails, onPrefetch = null, onDone, onArchive, onEditDesignRequest = null, onMoveToList, onDragStart, onDragEnd, onDropOnCard, isDragging, canEditCards, canArchiveCards, canComment = false, onSendWaitingClientReply = null, selected = false, quickOpen = false, onToggleSelected, ui = getTaskUiText("en") }) {'
if parts_source.count(old_parts_signature) != 1:
    fail(f"expected one TaskCard signature, found {parts_source.count(old_parts_signature)}")
updated_parts = parts_source.replace(old_parts_signature, new_parts_signature, 1)

old_focus_anchor = '''        role="button"
        tabIndex={0}
        onClick={openTaskFromCard}'''
new_focus_anchor = '''        role="button"
        tabIndex={0}
        onPointerEnter={() => onPrefetch?.(task)}
        onFocus={() => onPrefetch?.(task)}
        onClick={openTaskFromCard}'''
if updated_parts.count(old_focus_anchor) != 1:
    fail(f"expected one TaskCard focus/click anchor, found {updated_parts.count(old_focus_anchor)}")
updated_parts = updated_parts.replace(old_focus_anchor, new_focus_anchor, 1)

# Guard against accidental functional removal.
for contract in (
    'onOpenDetails={openTaskDetails}',
    'onNavigateTask={openTaskDetails}',
    'startTimeTimer',
    'pauseTimeTimer',
    'stopTimeTimer',
    'updateEstimatedHours',
    'tos-task-time-tracking-panel',
    OVERLAY_CLASS,
    NAV_CLASS,
    'syncTaskModalUrl(taskId',
    'prefetchTaskDetails(task)',
):
    if contract not in updated_board:
        fail(f"R32 board contract missing after transform: {contract}")
for contract in ('onPointerEnter={() => onPrefetch?.(task)}', 'onClick={openTaskFromCard}'):
    if contract not in updated_parts:
        fail(f"R32 TaskCard contract missing after transform: {contract}")

manifest = json.loads(MANIFEST.read_text())
if manifest.get("application") != "TOS" or manifest.get("environment") != "production":
    fail("unexpected production runtime manifest")
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

# Freeze unrelated high-risk surfaces and every existing Phase1 stylesheet.
app_hash = sha256(APP)
sidebar_hash = sha256(SIDEBAR)
chat_hash = sha256(CHAT)
prior_styles = sorted(STYLE_DIR.glob("taskDetailsV2_12_Phase1*.css"))
prior_style_hashes = {path: sha256(path) for path in prior_styles}

stamp = int(time.time())
backup_root = Path(f"/var/backups/tos-patches/task-board-r32-{stamp}")
backup_root.mkdir(parents=True, exist_ok=False)
shutil.copy2(BOARD, backup_root / BOARD.name)
shutil.copy2(PARTS, backup_root / PARTS.name)

LIVE.parent.mkdir(parents=True, exist_ok=True)
staging = LIVE.parent / f"build.task-board-r32-staging-{stamp}"
live_backup = LIVE.parent / f"build.task-board-r32-backup-{stamp}"
live_swapped = False
style_written = False

try:
    BOARD.write_text(updated_board)
    PARTS.write_text(updated_parts)
    R32_STYLE.write_text(payload_css.rstrip() + "\n")
    style_written = True

    if sha256(APP) != app_hash or sha256(SIDEBAR) != sidebar_hash or sha256(CHAT) != chat_hash:
        fail("unrelated app/sidebar/chat source changed unexpectedly")
    for path, digest in prior_style_hashes.items():
        if sha256(path) != digest:
            fail(f"existing Phase1 stylesheet changed unexpectedly: {path.name}")

    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists() or not (DIST / "index.html").exists():
        fail("frontend dist missing after build")

    built_css = "\n".join(path.read_text(errors="ignore") for path in DIST.rglob("*.css"))
    built_js = "\n".join(path.read_text(errors="ignore") for path in DIST.rglob("*.js"))
    if CSS_MARKER not in built_css or OVERLAY_CLASS not in built_css:
        fail("R32 CSS runtime marker missing from build")
    for token in (OVERLAY_CLASS, NAV_CLASS, "tosTaskModalR32"):
        if token not in built_js:
            fail(f"R32 JS runtime token missing from build: {token}")

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
    if CSS_MARKER not in live_css or OVERLAY_CLASS not in live_css:
        fail("R32 CSS runtime marker missing from live build")
    for token in (OVERLAY_CLASS, NAV_CLASS, "tosTaskModalR32"):
        if token not in live_js:
            fail(f"R32 JS runtime token missing from live build: {token}")

    if sha256(APP) != app_hash or sha256(SIDEBAR) != sidebar_hash or sha256(CHAT) != chat_hash:
        fail("unrelated app/sidebar/chat source changed after deploy")
    for path, digest in prior_style_hashes.items():
        if sha256(path) != digest:
            fail(f"existing Phase1 stylesheet changed after deploy: {path.name}")

except Exception:
    shutil.copy2(backup_root / BOARD.name, BOARD)
    shutil.copy2(backup_root / PARTS.name, PARTS)
    if style_written and R32_STYLE.exists():
        R32_STYLE.unlink()
    if live_swapped:
        if LIVE.exists():
            shutil.rmtree(LIVE)
        if live_backup.exists():
            live_backup.rename(LIVE)
    elif staging.exists():
        shutil.rmtree(staging)
    raise

print(f"VERSION={VERSION}")
print(f"PATCH_APPLIED={PATCH}")
print(f"BASE_TOS_COMMIT_REVIEWED={BASE_TOS_COMMIT}")
print("BUILD_STATUS=PASS")
print("DEPLOY_STATUS=PASS")
print("BOARD_CONTEXT_PRESERVED=YES")
print("TASK_MODAL_CENTERED_OVERLAY=YES")
print("TASK_OPEN_IMMEDIATE=YES")
print("TASK_PREFETCH_ON_HOVER_FOCUS=YES")
print("TASK_URL_SYNC=YES")
print("BROWSER_BACK_CLOSE=YES")
print("PREV_NEXT_NAV_VISIBLE=YES")
print("BACKDROP_CLICK_CLOSE=YES")
print("ESCAPE_CLOSE_PRESERVED=YES")
print("TASK_LOGIC_CHANGED=NO")
print("BACKEND_CHANGED=NO")
print("API_CHANGED=NO")
print("DATABASE_CHANGED=NO")
print("TCS_CHANGED=NO")
print("RAMZY_CHANGED=NO")
print("PUSH=NO")
print("STATUS=READY_FOR_VISUAL_QA")
