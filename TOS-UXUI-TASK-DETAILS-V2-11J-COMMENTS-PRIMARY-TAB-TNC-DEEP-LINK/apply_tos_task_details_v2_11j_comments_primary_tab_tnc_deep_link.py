from pathlib import Path
import hashlib
import json
import re
import shutil
import subprocess
import sys
import time

VERSION = "TOS_TASK_DETAILS_V2_11J"
PATCH_NAME = "TOS-UXUI-TASK-DETAILS-V2-11J-COMMENTS-PRIMARY-TAB-TNC-DEEP-LINK"
BASELINE_CHAIN = "TOS_TASK_DETAILS_V2_11I"
BASE_TOS_COMMIT = "29f9e8865fec1acd3468f9f94d236231c1569ebf"
APP_MARKER = "TOS_TASK_DETAILS_V2_11J_TNC_COMMENTS_DEEP_LINK"
BOARD_MARKER = "TOS_TASK_DETAILS_V2_11J_COMMENTS_PRIMARY_TAB"

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
APP = FRONTEND / "src/App.jsx"
BOARD = FRONTEND / "src/components/ProfessionalTaskBoard.jsx"
MANIFEST = ROOT / "deployment/tos-production-runtime.json"


def fail(message):
    raise RuntimeError(message)


def run(command, cwd=None):
    subprocess.run(command, cwd=cwd, check=True)


def sha256_text(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        fail(f"{label}: expected exactly one anchor, found {count}")
    return text.replace(old, new, 1)


def extract_add_comment(text):
    start = text.find("  async function addComment(event) {")
    end = text.find("  async function sendWaitingClientReply(event) {", start)
    if start < 0 or end < 0 or end <= start:
        fail("could not isolate existing addComment function")
    return text[start:end]


for path in (FRONTEND, APP, BOARD, MANIFEST):
    if not path.exists():
        fail(f"required path missing: {path}")
for command in ("node", "npm"):
    if not shutil.which(command):
        fail(f"required command not found: {command}")

app_source = APP.read_text()
board_source = BOARD.read_text()

if APP_MARKER in app_source or BOARD_MARKER in board_source:
    fail("V2.11J appears already applied or partially applied")
if "TOS_TASK_DETAILS_V2_11H_HERO_DESCRIPTION_REMOVED" not in board_source:
    fail("required Task Details V2.11H baseline marker missing")
if "TOS_TASK_DETAILS_V2_11G_WAITING_CLIENT_BELOW_DESCRIPTION" not in board_source:
    fail("required Waiting Client V2.11G baseline marker missing")

comment_logic_hash = sha256_text(extract_add_comment(board_source))

# App.jsx — derive a safe Task Details initial tab from the existing TNC item.
app_old = '    setPendingOpenTask({ projectId: target.projectId, taskId: target.taskId || "" });'
app_new = '''    // TOS_TASK_DETAILS_V2_11J_TNC_COMMENTS_DEEP_LINK
    const requestedTaskTab = String(target.taskTab || target.tab || item?.metadata?.taskTab || "").trim().toLowerCase();
    const notificationType = String(item?.type || "").trim().toUpperCase();
    const taskTab = requestedTaskTab === "comments" || notificationType.includes("COMMENT") ? "comments" : "overview";
    setPendingOpenTask({ projectId: target.projectId, taskId: target.taskId || "", taskTab });'''
app_updated = replace_once(app_source, app_old, app_new, "App TNC task-open anchor")

app_prop_old = '                    initialTaskId={pendingOpenTask?.projectId === activeProjectId ? pendingOpenTask.taskId : ""}\n                    onInitialTaskHandled={() => setPendingOpenTask(null)}'
app_prop_new = '                    initialTaskId={pendingOpenTask?.projectId === activeProjectId ? pendingOpenTask.taskId : ""}\n                    initialTaskTab={pendingOpenTask?.projectId === activeProjectId ? pendingOpenTask.taskTab || "overview" : "overview"}\n                    onInitialTaskHandled={() => setPendingOpenTask(null)}'
app_updated = replace_once(app_updated, app_prop_old, app_prop_new, "ProfessionalTaskBoard initial tab prop")

# Board — CardDetailsModal receives and uses an initial tab only at mount.
card_sig_old = 'function CardDetailsModal({ task, tasks = [], dependencyTasks = [], lists, labels, members, projectMembers = [], availableProjectUsers = [], taskServices = [], permissions, user = null, onClose, onUpdate, onDeleteLocal, onLabelCreated, onRequestArchive, onNavigateTask }) {'
card_sig_new = 'function CardDetailsModal({ task, tasks = [], dependencyTasks = [], lists, labels, members, projectMembers = [], availableProjectUsers = [], taskServices = [], permissions, user = null, onClose, onUpdate, onDeleteLocal, onLabelCreated, onRequestArchive, onNavigateTask, initialTab = "overview" }) {'
board_updated = replace_once(board_source, card_sig_old, card_sig_new, "CardDetailsModal signature")

active_tab_old = '  const [activeTaskTab, setActiveTaskTab] = useState("overview");'
active_tab_new = '  // TOS_TASK_DETAILS_V2_11J_COMMENTS_PRIMARY_TAB\n  const [activeTaskTab, setActiveTaskTab] = useState(() => initialTab === "comments" ? "comments" : "overview");'
board_updated = replace_once(board_updated, active_tab_old, active_tab_new, "CardDetailsModal active tab state")

# Comments becomes the second permanent tab, preserving the existing object/count.
tabs_old = '''  const taskDetailTabs = useMemo(() => ([
    { id: "overview", label: isAr ? "نظرة عامة" : "Overview", icon: Edit3 },
    { id: "checklist", label: modalUi.checklist || "Checklist", icon: CheckCircle2, count: checklistTotal },
    { id: "attachments", label: isAr ? "المرفقات" : "Attachments", icon: Paperclip, count: taskActiveFiles.length + projectClientFiles.length },
    { id: "activity", label: modalUi.activity || (isAr ? "النشاط" : "Activity"), icon: ClipboardList, count: referenceActivityItems.length },
    { id: "subtasks", label: isAr ? "المهام الفرعية" : "Subtasks", icon: List, count: checklistTotal },
    { id: "comments", label: modalUi.comments || (isAr ? "التعليقات" : "Comments"), icon: MessageSquare, count: draft.comments?.length || 0 },
    { id: "time", label: modalUi.timeTracking || (isAr ? "الوقت" : "Time"), icon: Clock3 },
  ]), [modalUi, isAr, checklistTotal, draft.comments?.length, taskActiveFiles.length, projectClientFiles.length, referenceActivityItems.length]);'''
tabs_new = '''  const taskDetailTabs = useMemo(() => ([
    { id: "overview", label: isAr ? "نظرة عامة" : "Overview", icon: Edit3 },
    { id: "comments", label: modalUi.comments || (isAr ? "التعليقات" : "Comments"), icon: MessageSquare, count: draft.comments?.length || 0 },
    { id: "checklist", label: modalUi.checklist || "Checklist", icon: CheckCircle2, count: checklistTotal },
    { id: "attachments", label: isAr ? "المرفقات" : "Attachments", icon: Paperclip, count: taskActiveFiles.length + projectClientFiles.length },
    { id: "activity", label: modalUi.activity || (isAr ? "النشاط" : "Activity"), icon: ClipboardList, count: referenceActivityItems.length },
    { id: "subtasks", label: isAr ? "المهام الفرعية" : "Subtasks", icon: List, count: checklistTotal },
    { id: "time", label: modalUi.timeTracking || (isAr ? "الوقت" : "Time"), icon: Clock3 },
  ]), [modalUi, isAr, checklistTotal, draft.comments?.length, taskActiveFiles.length, projectClientFiles.length, referenceActivityItems.length]);'''
board_updated = replace_once(board_updated, tabs_old, tabs_new, "taskDetailTabs order")

filter_old = '                    .filter((tab) => ["overview", "checklist", "attachments", "activity", "subtasks"].includes(tab.id) || (taskMoreDetailsOpen && ["comments", "time"].includes(tab.id)))'
filter_new = '                    .filter((tab) => ["overview", "comments", "checklist", "attachments", "activity", "subtasks"].includes(tab.id) || (taskMoreDetailsOpen && tab.id === "time"))'
board_updated = replace_once(board_updated, filter_old, filter_new, "primary tab filter")

# There are two More toggles; after promotion, only Time is gated by More.
reset_patterns = [
    'if (!nextOpen && !["overview", "checklist"].includes(activeTaskTab)) setActiveTaskTab("overview");',
    'if (!nextOpen && !["overview", "subtasks", "checklist", "attachments", "activity"].includes(activeTaskTab)) setActiveTaskTab("overview");',
]
for index, old in enumerate(reset_patterns, start=1):
    board_updated = replace_once(board_updated, old, 'if (!nextOpen && activeTaskTab === "time") setActiveTaskTab("overview");', f"More toggle reset #{index}")

# Board public prop and per-open initial-tab state.
board_export_old = 'export default function ProfessionalTaskBoard({ projectId, user = null, projects = [], activeProjectId = projectId, onProjectChange = null, onBackToProjectPicker = null, onOpenProjectDetails = null, initialTaskId = "", onInitialTaskHandled = null }) {'
board_export_new = 'export default function ProfessionalTaskBoard({ projectId, user = null, projects = [], activeProjectId = projectId, onProjectChange = null, onBackToProjectPicker = null, onOpenProjectDetails = null, initialTaskId = "", initialTaskTab = "overview", onInitialTaskHandled = null }) {'
board_updated = replace_once(board_updated, board_export_old, board_export_new, "ProfessionalTaskBoard signature")

selected_state_old = '  const [selectedTask, setSelectedTask] = useState(null);\n  const selectedTaskRef = useRef(null);'
selected_state_new = '  const [selectedTask, setSelectedTask] = useState(null);\n  const [selectedTaskInitialTab, setSelectedTaskInitialTab] = useState("overview");\n  const selectedTaskRef = useRef(null);'
board_updated = replace_once(board_updated, selected_state_old, selected_state_new, "selected task initial-tab state")

initial_open_old = '''        initialTaskHandledIdRef.current = initialTaskId;
        setQuickViewTask(null);
        setSelectedTask(fullTask);
        onInitialTaskHandled?.();'''
initial_open_new = '''        initialTaskHandledIdRef.current = initialTaskId;
        setQuickViewTask(null);
        setSelectedTaskInitialTab(initialTaskTab === "comments" ? "comments" : "overview");
        setSelectedTask(fullTask);
        onInitialTaskHandled?.();'''
board_updated = replace_once(board_updated, initial_open_old, initial_open_new, "initial task open tab selection")

deps_old = '  }, [initialTaskId, activeTaskProject?.id, activeBoard?.id, activeBoard?.projectId, activeBoardId, isAr, loading]);'
deps_new = '  }, [initialTaskId, initialTaskTab, activeTaskProject?.id, activeBoard?.id, activeBoard?.projectId, activeBoardId, isAr, loading]);'
board_updated = replace_once(board_updated, deps_old, deps_new, "initial task effect dependencies")

# Manual/board navigation always starts on Overview.
open_task_match = re.search(r'(  async function openTaskDetails\(task\) \{\n(?:.|\n)*?    setQuickViewTask\(null\);\n)', board_updated)
if not open_task_match:
    fail("openTaskDetails anchor not found")
open_task_block = open_task_match.group(1)
if 'setSelectedTaskInitialTab("overview")' in open_task_block:
    fail("openTaskDetails initial tab already modified")
open_task_replacement = open_task_block + '    setSelectedTaskInitialTab("overview");\n'
board_updated = board_updated[:open_task_match.start()] + open_task_replacement + board_updated[open_task_match.end():]

modal_old = 'onRequestArchive={requestArchiveTaskFromCard} onNavigateTask={openTaskDetails} />'
modal_new = 'onRequestArchive={requestArchiveTaskFromCard} onNavigateTask={openTaskDetails} initialTab={selectedTaskInitialTab} />'
board_updated = replace_once(board_updated, modal_old, modal_new, "CardDetailsModal initialTab prop")

# Source contracts.
if app_updated.count(APP_MARKER) != 1 or board_updated.count(BOARD_MARKER) != 1:
    fail("V2.11J marker count invalid")
if 'notificationType.includes("COMMENT") ? "comments" : "overview"' not in app_updated:
    fail("TNC comment deep-link contract missing")
if '["overview", "comments", "checklist", "attachments", "activity", "subtasks"].includes(tab.id)' not in board_updated:
    fail("Comments primary-tab contract missing")
if '(taskMoreDetailsOpen && tab.id === "time")' not in board_updated:
    fail("More Actions Time-only contract missing")
if board_updated.count('if (!nextOpen && activeTaskTab === "time") setActiveTaskTab("overview");') != 2:
    fail("More toggle preservation contract missing")
if 'initialTaskTab={pendingOpenTask?.projectId === activeProjectId ? pendingOpenTask.taskTab || "overview" : "overview"}' not in app_updated:
    fail("App -> ProfessionalTaskBoard initialTaskTab wiring missing")
if 'initialTab={selectedTaskInitialTab}' not in board_updated:
    fail("Board -> CardDetailsModal initialTab wiring missing")
if sha256_text(extract_add_comment(board_updated)) != comment_logic_hash:
    fail("existing addComment function changed unexpectedly")
if "TOS_TASK_DETAILS_V2_11G_WAITING_CLIENT_BELOW_DESCRIPTION" not in board_updated:
    fail("Waiting Client baseline marker was lost")
if "TOS_TASK_DETAILS_V2_11H_HERO_DESCRIPTION_REMOVED" not in board_updated:
    fail("Hero baseline marker was lost")

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

stamp = int(time.time())
backup_root = Path(f"/var/backups/tos-patches/task-details-v2-11j-{stamp}")
backup_root.mkdir(parents=True, exist_ok=False)
app_backup = backup_root / "App.jsx"
board_backup = backup_root / "ProfessionalTaskBoard.jsx"
shutil.copy2(APP, app_backup)
shutil.copy2(BOARD, board_backup)

LIVE.parent.mkdir(parents=True, exist_ok=True)
staging = LIVE.parent / f"build.task-details-v2-11j-staging-{stamp}"
live_backup = LIVE.parent / f"build.task-details-v2-11j-backup-{stamp}"
live_swapped = False

try:
    APP.write_text(app_updated)
    BOARD.write_text(board_updated)

    written_app = APP.read_text()
    written_board = BOARD.read_text()
    if APP_MARKER not in written_app or BOARD_MARKER not in written_board:
        fail("source markers missing after write")
    if sha256_text(extract_add_comment(written_board)) != comment_logic_hash:
        fail("addComment changed after write")

    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists() or not (DIST / "index.html").exists():
        fail("frontend dist missing after build")

    if staging.exists():
        shutil.rmtree(staging)
    shutil.copytree(DIST, staging)
    if LIVE.exists():
        if live_backup.exists():
            shutil.rmtree(live_backup)
        LIVE.rename(live_backup)
    staging.rename(LIVE)
    live_swapped = True

    if not (LIVE / "index.html").exists():
        fail("live frontend index missing after deploy")

except Exception:
    shutil.copy2(app_backup, APP)
    shutil.copy2(board_backup, BOARD)
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
print("PASS/FAIL=PASS")
print("BUILD_RESULT=PASS")
print("LIVE_DEPLOY=PASS")
print("COMMENTS_PRIMARY_TAB=YES")
print("COMMENTS_POSITION_AFTER_OVERVIEW=YES")
print("COMMENTS_COUNT_BADGE_PRESERVED=YES")
print("MORE_ACTIONS_TIME_ONLY=YES")
print("MORE_CLOSE_COMMENTS_PRESERVED=YES")
print("TNC_COMMENT_DEEP_LINK=YES")
print("TNC_NON_COMMENT_DEFAULT_OVERVIEW=YES")
print("MANUAL_TASK_DEFAULT_OVERVIEW=YES")
print("COMMENT_SUBMIT_LOGIC_CHANGED=NO")
print("BACKEND_CHANGED=NO")
print("API_CHANGED=NO")
print("HERO_CHANGED=NO")
print("DESCRIPTION_CHANGED=NO")
print("WAITING_CLIENT_CHANGED=NO")
print("RIGHT_RAIL_CHANGED=NO")
print("TCS_CHANGED=NO")
print("RAMZY_CHANGED=NO")
print("PUSH=NO")
print("STATUS=READY_FOR_VISUAL_QA")
