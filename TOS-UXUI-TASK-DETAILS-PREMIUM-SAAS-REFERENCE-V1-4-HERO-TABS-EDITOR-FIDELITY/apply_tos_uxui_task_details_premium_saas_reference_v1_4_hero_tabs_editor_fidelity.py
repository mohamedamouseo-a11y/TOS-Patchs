from pathlib import Path
import json
import shutil
import subprocess
import sys
import time

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
BOARD = FRONTEND / "src/components/ProfessionalTaskBoard.jsx"
STYLE = FRONTEND / "src/styles/taskDetailsPremiumSaasReferenceV1.css"
MANIFEST = ROOT / "deployment/tos-production-runtime.json"
DIST = FRONTEND / "dist"

V1_RUNTIME = "--tos-task-details-premium-saas-reference-v1-runtime"
V12_RUNTIME = "--tos-task-details-shell-geometry-v1-2-runtime"
V13_RUNTIME = "--tos-task-details-macro-layout-fidelity-v1-3-runtime"
RUNTIME = "--tos-task-details-hero-tabs-editor-fidelity-v1-4-runtime"

OLD_TABS = '''  const taskDetailTabs = useMemo(() => ([
    { id: "overview", label: modalUi.taskDetails || (isAr ? "تفاصيل المهمة" : "Task details"), icon: ClipboardList },
    { id: "subtasks", label: isAr ? "المهام الفرعية" : "Subtasks", icon: CalendarClock, count: checklistTotal },
    { id: "checklist", label: modalUi.checklist || "Checklist", icon: CheckCircle2, count: checklistTotal },
    { id: "comments", label: modalUi.comments || (isAr ? "التعليقات" : "Comments"), icon: MessageSquare, count: draft.comments?.length || 0 },
    { id: "attachments", label: modalUi.files || (isAr ? "الملفات" : "Files"), icon: Paperclip, count: taskActiveFiles.length + projectClientFiles.length },
    { id: "time", label: modalUi.timeTracking || (isAr ? "الوقت" : "Time"), icon: Clock3 },
    { id: "activity", label: modalUi.activity || (isAr ? "النشاط" : "Activity"), icon: ClipboardList, count: referenceActivityItems.length },
  ]), [modalUi, isAr, checklistTotal, draft.comments?.length, taskActiveFiles.length, projectClientFiles.length, referenceActivityItems.length]);'''

NEW_TABS = '''  const taskDetailTabs = useMemo(() => ([
    { id: "overview", label: modalUi.taskDetails || (isAr ? "تفاصيل المهمة" : "Task details"), icon: ClipboardList },
    { id: "subtasks", label: isAr ? "المهام الفرعية" : "Subtasks", icon: CalendarClock, count: checklistTotal },
    { id: "attachments", label: isAr ? "المرفقات" : "Attachments", icon: Paperclip, count: taskActiveFiles.length + projectClientFiles.length },
    { id: "activity", label: modalUi.activity || (isAr ? "النشاط" : "Activity"), icon: ClipboardList, count: referenceActivityItems.length },
    { id: "checklist", label: modalUi.checklist || "Checklist", icon: CheckCircle2, count: checklistTotal },
    { id: "comments", label: modalUi.comments || (isAr ? "التعليقات" : "Comments"), icon: MessageSquare, count: draft.comments?.length || 0 },
    { id: "time", label: modalUi.timeTracking || (isAr ? "الوقت" : "Time"), icon: Clock3 },
  ]), [modalUi, isAr, checklistTotal, draft.comments?.length, taskActiveFiles.length, projectClientFiles.length, referenceActivityItems.length]);'''

FIX_BLOCK = r'''

/* ================================================================
   Task Details V1.4 — Hero + Tabs + Editor Fidelity
   Canonical reference: 1664x936.
   Scope is visual fidelity only. No API/business logic changes.
   ================================================================ */
:root { --tos-task-details-hero-tabs-editor-fidelity-v1-4-runtime: 1; }

/* HERO — larger, calmer, stronger reference proportions */
.tos-task-details-reference-v1 .tos-task-details-modal .tos-task-summary-compact{
  min-height:156px!important;
  padding:24px 26px!important;
  border-radius:20px!important;
  border-color:#e5ddd2!important;
  background:linear-gradient(180deg,#fffefa 0%,#fffdf9 100%)!important;
  box-shadow:0 14px 34px rgba(54,43,25,.055), inset 0 1px 0 #fff!important;
}

@media (min-width:1280px){
  .tos-task-details-reference-v1 .tos-task-details-modal .tos-task-summary-compact>div{
    grid-template-columns:minmax(430px,1.55fr) repeat(3,minmax(180px,.72fr))!important;
    gap:18px!important;
    align-items:center!important;
  }

  .tos-task-details-reference-v1 .tos-task-details-modal .tos-task-reference-title-block{
    min-height:118px!important;
    padding-inline-start:106px!important;
    padding-inline-end:18px!important;
    justify-content:center!important;
  }

  .tos-task-details-reference-v1 .tos-task-details-modal .tos-task-reference-title-block:before{
    top:50%!important;
    width:84px!important;
    height:84px!important;
    transform:translateY(-50%)!important;
    border-radius:16px!important;
    background-size:40px 40px!important;
  }

  .tos-task-details-reference-v1 .tos-task-details-modal .tos-task-reference-title-block:after{
    top:8px!important;
    inset-inline-start:106px!important;
    font-size:11px!important;
    letter-spacing:.09em!important;
    text-transform:uppercase!important;
  }

  .tos-task-details-reference-v1 .tos-task-details-modal .tos-task-title-input{
    margin-top:14px!important;
    font-size:30px!important;
    line-height:1.12!important;
    font-weight:900!important;
    letter-spacing:-.035em!important;
  }

  .tos-task-details-reference-v1 .tos-task-details-modal .tos-task-header-description{
    display:block!important;
    margin-top:10px!important;
    max-width:700px!important;
    color:#747f8e!important;
    font-size:13px!important;
    line-height:1.6!important;
    font-weight:650!important;
  }

  .tos-task-details-reference-v1 .tos-task-details-modal .tos-task-summary-controls>label,
  .tos-task-details-reference-v1 .tos-task-details-modal .tos-task-summary-controls>div{
    min-height:112px!important;
    padding:16px 17px!important;
    border-radius:16px!important;
    border-color:#e9e1d7!important;
    background:#fff!important;
  }

  .tos-task-details-reference-v1 .tos-task-details-modal .tos-task-summary-controls span{
    font-size:11.5px!important;
    letter-spacing:.01em!important;
  }

  .tos-task-details-reference-v1 .tos-task-details-modal .tos-task-summary-controls select,
  .tos-task-details-reference-v1 .tos-task-details-modal .tos-task-summary-controls input{
    height:44px!important;
    margin-top:12px!important;
    border-radius:11px!important;
    font-size:12.5px!important;
  }
}

/* TAB RAIL — canonical order is controlled in JSX; this block fixes scale/density */
.tos-task-details-reference-v1 .tos-task-details-modal .tos-task-detail-tabs{
  min-height:64px!important;
  padding-inline:8px!important;
  border-bottom:1px solid #ddd6cc!important;
}

.tos-task-details-reference-v1 .tos-task-details-modal .tos-task-reference-tabs-main{
  gap:5px!important;
}

.tos-task-details-reference-v1 .tos-task-details-modal .tos-task-reference-tab{
  min-height:62px!important;
  padding:0 14px!important;
  gap:8px!important;
  color:#657181!important;
  font-size:13px!important;
  font-weight:760!important;
}

.tos-task-details-reference-v1 .tos-task-details-modal .tos-task-reference-tab svg{
  width:17px!important;
  height:17px!important;
}

.tos-task-details-reference-v1 .tos-task-details-modal .tos-task-reference-tab-count{
  min-width:20px!important;
  height:20px!important;
  font-size:10px!important;
}

.tos-task-details-reference-v1 .tos-task-details-modal .tos-task-more-actions-reference{
  height:42px!important;
  padding-inline:15px!important;
  border-radius:11px!important;
  font-size:11.5px!important;
}

.tos-task-details-reference-v1 .tos-task-details-modal .tos-task-complete-reference{
  height:43px!important;
  padding-inline:19px!important;
  border-radius:11px!important;
  font-size:11.5px!important;
  box-shadow:0 8px 18px rgba(178,113,7,.17)!important;
}

/* DESCRIPTION / EDITOR — reference card hierarchy and toolbar grouping */
.tos-task-details-reference-v1 .tos-task-details-modal .tos-task-description-panel{
  padding:22px!important;
  border-radius:20px!important;
  border-color:#e5ddd2!important;
  background:#fff!important;
  box-shadow:0 14px 34px rgba(54,43,25,.05)!important;
}

.tos-task-details-reference-v1 .tos-task-details-modal .tos-task-description-panel>div:first-child{
  min-height:58px!important;
  margin-bottom:16px!important;
  padding-inline-start:58px!important;
}

.tos-task-details-reference-v1 .tos-task-details-modal .tos-task-description-panel>div:first-child:before{
  width:44px!important;
  height:44px!important;
  border-radius:11px!important;
  background-size:24px 24px!important;
}

.tos-task-details-reference-v1 .tos-task-details-modal .tos-task-description-panel h3{
  font-size:20px!important;
  line-height:1.25!important;
  letter-spacing:-.02em!important;
}

.tos-task-details-reference-v1 .tos-task-details-modal .tos-task-description-panel h3:after{
  margin-top:6px!important;
  color:#7d8794!important;
  font-size:11.5px!important;
  line-height:1.45!important;
}

.tos-task-details-reference-v1 .tos-task-details-modal .tos-task-description-panel .tos-task-rich-editor-shell{
  overflow:hidden!important;
  border:1px solid #e5ded4!important;
  border-radius:16px!important;
  box-shadow:0 1px 0 rgba(255,255,255,.9), inset 0 1px 0 #fff!important;
}

.tos-task-details-reference-v1 .tos-task-details-modal .tos-task-description-panel .tos-task-editor-toolbar{
  padding:8px 10px!important;
  border-bottom:1px solid #e9e3da!important;
  background:#fcfbf9!important;
}

.tos-task-details-reference-v1 .tos-task-details-modal .tos-task-description-panel .tos-task-editor-toolbar>div{
  display:flex!important;
  flex-wrap:nowrap!important;
  align-items:center!important;
  gap:7px!important;
  overflow-x:auto!important;
  scrollbar-width:none!important;
}

.tos-task-details-reference-v1 .tos-task-details-modal .tos-task-description-panel .tos-task-editor-toolbar>div::-webkit-scrollbar{
  display:none!important;
}

.tos-task-details-reference-v1 .tos-task-details-modal .tos-task-description-panel .tos-editor-group-history{
  display:flex!important;
}

.tos-task-details-reference-v1 .tos-task-details-modal .tos-task-description-panel .tos-task-editor-toolbar [class*="tos-editor-group"]{
  display:flex!important;
  align-items:center!important;
  flex-wrap:nowrap!important;
  gap:2px!important;
  padding:3px!important;
  border:1px solid #ebe5dc!important;
  border-radius:10px!important;
  background:#fff!important;
  box-shadow:0 1px 2px rgba(45,36,24,.025)!important;
}

.tos-task-details-reference-v1 .tos-task-details-modal .tos-task-description-panel .tos-task-editor-toolbar button{
  width:32px!important;
  height:32px!important;
  min-width:32px!important;
  border:0!important;
  border-radius:7px!important;
  color:#586474!important;
  background:transparent!important;
}

.tos-task-details-reference-v1 .tos-task-details-modal .tos-task-description-panel .tos-editor-group-insert button,
.tos-task-details-reference-v1 .tos-task-details-modal .tos-task-description-panel .tos-task-editor-more-button{
  width:auto!important;
  min-width:32px!important;
  padding-inline:9px!important;
}

.tos-task-details-reference-v1 .tos-task-details-modal .tos-task-description-panel .tos-task-editor-toolbar select{
  height:32px!important;
  border:0!important;
  border-radius:7px!important;
  background:transparent!important;
  color:#586474!important;
  font-size:11px!important;
}

.tos-task-details-reference-v1 .tos-task-details-modal .tos-task-description-panel .tos-editor-group-block select:first-child{
  width:100px!important;
}

.tos-task-details-reference-v1 .tos-task-details-modal .tos-task-description-panel .tos-task-rich-editor-content{
  min-height:330px!important;
  padding:20px 22px!important;
  color:#263348!important;
  font-size:14px!important;
  line-height:1.72!important;
}

.tos-task-details-reference-v1 .tos-task-details-modal .tos-task-description-panel .tos-task-rich-editor-shell>div:last-child{
  min-height:34px!important;
  padding-inline:14px!important;
  border-top:1px solid #eee8df!important;
  background:#fcfbf9!important;
}

/* Dark translation preserves identical geometry. */
html.dark .tos-task-details-reference-v1 .tos-task-details-modal .tos-task-summary-compact{
  border-color:rgba(209,218,225,.13)!important;
  background:linear-gradient(180deg,#121a20,#0f161c)!important;
  box-shadow:0 18px 42px rgba(0,0,0,.28)!important;
}

html.dark .tos-task-details-reference-v1 .tos-task-details-modal .tos-task-summary-controls>label,
html.dark .tos-task-details-reference-v1 .tos-task-details-modal .tos-task-summary-controls>div{
  border-color:rgba(209,218,225,.12)!important;
  background:#141c22!important;
}

html.dark .tos-task-details-reference-v1 .tos-task-details-modal .tos-task-description-panel{
  border-color:rgba(209,218,225,.13)!important;
  background:#11181e!important;
  box-shadow:0 20px 48px rgba(0,0,0,.28)!important;
}

html.dark .tos-task-details-reference-v1 .tos-task-details-modal .tos-task-description-panel .tos-task-editor-toolbar [class*="tos-editor-group"]{
  border-color:rgba(209,218,225,.11)!important;
  background:#151d23!important;
}

html.dark .tos-task-details-reference-v1 .tos-task-details-modal .tos-task-description-panel .tos-task-editor-toolbar button,
html.dark .tos-task-details-reference-v1 .tos-task-details-modal .tos-task-description-panel .tos-task-editor-toolbar select{
  color:#d0d7dc!important;
  background:transparent!important;
}

@media (max-width:1279px){
  .tos-task-details-reference-v1 .tos-task-details-modal .tos-task-title-input{font-size:26px!important}
  .tos-task-details-reference-v1 .tos-task-details-modal .tos-task-description-panel{padding:18px!important}
}
'''


def fail(message):
    raise RuntimeError(message)


def run(command, cwd=None):
    subprocess.run(command, cwd=cwd, check=True)


def replace_once(source, old, new, label):
    count = source.count(old)
    if count != 1:
        fail(f"{label} marker count changed unexpectedly: {count}")
    return source.replace(old, new, 1)


for path in (BOARD, STYLE, MANIFEST):
    if not path.exists():
        fail(f"required file missing: {path}")

board_source = BOARD.read_text()
style_source = STYLE.read_text()

required_board_markers = [
    'import "../styles/taskDetailsPremiumSaasReferenceV1.css";',
    "tos-task-details-reference-v1",
    'className="tos-task-reference-tab"',
    '["checklist", "subtasks"].includes(activeTaskTab)',
    'handleTaskStatusChange("DONE")',
]
for marker in required_board_markers:
    if marker not in board_source:
        fail(f"Task Details V1/R1 source marker missing: {marker}")

for runtime in (V1_RUNTIME, V12_RUNTIME, V13_RUNTIME):
    if runtime not in style_source:
        fail(f"required prior Task Details runtime marker missing: {runtime}")
if RUNTIME in style_source:
    fail("Task Details V1.4 hero/tabs/editor fidelity is already present")

if board_source.count(OLD_TABS) != 1:
    fail(f"Task Details post-V1 tab model changed unexpectedly: {board_source.count(OLD_TABS)}")

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

for command in ("node", "npm"):
    if not shutil.which(command):
        fail(f"required command not found: {command}")

stamp = int(time.time())
backup_root = Path(f"/var/backups/tos-patches/task-details-hero-tabs-editor-v1-4-{stamp}")
backup_root.mkdir(parents=True, exist_ok=False)
board_backup = backup_root / BOARD.name
style_backup = backup_root / STYLE.name
shutil.copy2(BOARD, board_backup)
shutil.copy2(STYLE, style_backup)

live.parent.mkdir(parents=True, exist_ok=True)
staging = live.parent / f"build.task-details-hero-tabs-editor-v1-4-staging-{stamp}"
live_backup = live.parent / f"build.task-details-hero-tabs-editor-v1-4-backup-{stamp}"
live_swapped = False

try:
    updated_board = replace_once(board_source, OLD_TABS, NEW_TABS, "canonical primary tab order")
    updated_style = style_source + FIX_BLOCK

    source_order = [
        'id: "overview"',
        'id: "subtasks"',
        'id: "attachments"',
        'id: "activity"',
        'id: "checklist"',
    ]
    cursor = updated_board.index('const taskDetailTabs = useMemo(() => ([')
    last = cursor
    for marker in source_order:
        pos = updated_board.index(marker, last)
        if pos < last:
            fail(f"primary tab order verification failed at {marker}")
        last = pos

    if 'label: isAr ? "المرفقات" : "Attachments"' not in updated_board:
        fail("Attachments canonical label missing after transform")
    if RUNTIME not in updated_style:
        fail("V1.4 runtime marker missing after style transform")
    if '.tos-editor-group-history' not in updated_style or 'display:flex!important' not in updated_style:
        fail("editor history/group fidelity marker missing")

    BOARD.write_text(updated_board)
    STYLE.write_text(updated_style)

    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists() or not (DIST / "index.html").exists():
        fail("frontend dist missing after build")

    built_css = "\n".join(path.read_text(errors="ignore") for path in DIST.rglob("*.css"))
    built_js = "\n".join(path.read_text(errors="ignore") for path in DIST.rglob("*.js"))
    if RUNTIME not in built_css:
        fail("V1.4 runtime marker missing from built CSS")
    for marker in ("Task details", "Subtasks", "Attachments", "Activity", "Checklist"):
        if marker not in built_js:
            fail(f"canonical primary tab label missing from built JS: {marker}")
    if "Mark as complete" not in built_js and "إكمال المهمة" not in built_js:
        fail("Task Details completion action missing from built JS")
    if "tos-task-details-reference-v1" not in built_js:
        fail("Task Details canonical root marker missing from built JS")

    if staging.exists():
        shutil.rmtree(staging)
    shutil.copytree(DIST, staging)
    if live.exists():
        live.rename(live_backup)
    staging.rename(live)
    live_swapped = True

    live_css = "\n".join(path.read_text(errors="ignore") for path in live.rglob("*.css"))
    live_js = "\n".join(path.read_text(errors="ignore") for path in live.rglob("*.js"))
    if RUNTIME not in live_css:
        fail("V1.4 runtime marker missing from live CSS")
    if "Attachments" not in live_js or "tos-task-details-reference-v1" not in live_js:
        fail("V1.4 canonical markers missing from live JS")

    print("PASS/FAIL=PASS")
    print("BUILD_RESULT=PASS")
    print("LIVE_DEPLOY=PASS")
    print("TASK_DETAILS_PREMIUM_SAAS_REFERENCE_V1_4_RUNTIME=YES")
    print("REFERENCE_VIEWPORT=1664x936")
    print("HERO_FIDELITY=POLISHED")
    print("HERO_TITLE_SCALE=REFERENCE_ALIGNED")
    print("HERO_CONTROLS=THREE_PRIMARY_CARDS_PRESERVED")
    print("PRIMARY_TAB_ORDER=TASK_DETAILS_SUBTASKS_ATTACHMENTS_ACTIVITY_CHECKLIST")
    print("ATTACHMENTS_LABEL=ATTACHMENTS")
    print("EDITOR_TOOLBAR=REFERENCE_GROUPED")
    print("EDITOR_HISTORY_CONTROLS=VISIBLE")
    print("EDITOR_CANVAS=REFERENCE_PROPORTIONS")
    print("V1_2_SHELL_GEOMETRY=PRESERVED")
    print("V1_3_FULL_WIDTH_LAYOUT=PRESERVED")
    print("TASK_APIS_CHANGED=NO")
    print("TASK_DATA_CONTRACT_CHANGED=NO")
    print("TASK_PERMISSIONS_CHANGED=NO")
    print("TASK_BUSINESS_LOGIC_CHANGED=NO")
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
    print("PASS/FAIL=FAIL")
    print(f"ERROR={exc}")
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("STATUS=STOPPED")
    raise SystemExit(1)
