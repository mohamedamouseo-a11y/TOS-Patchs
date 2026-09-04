#!/usr/bin/env bash
set -euo pipefail

echo "RUNNING=PHASE03_2_TASK_DETAILS_MINIMAL_VIEW_V1"

ROOT="${1:-/var/www/TOS}"
PATCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCH_REPO_ROOT="$(cd "$PATCH_DIR/.." && pwd)"
SOURCE_CSS="$PATCH_DIR/task-details-minimal-view-v1.css"

BOARD_TARGET="frontend/src/components/ProfessionalTaskBoard.jsx"
WORKSPACE_TARGET="frontend/src/pages/MyTaskWorkspace.jsx"
CSS_TARGET="frontend/src/styles/tasks-projects-premium-reference.css"
PARTS_TARGET="frontend/src/features/tasks/taskBoardParts.jsx"

ROOT_HOOK='tos-task-details-modal'
WORKSPACE_HOOK='tos-my-workspace'
DECLUTTER_LAYOUT_HOOK='tos-task-details-layout'
DECLUTTER_PROGRESS_HOOK='tos-task-progress-compact'
DECLUTTER_SIDE_HOOK='tos-task-side-rail'
DECLUTTER_TOOLBAR_HOOK='tos-task-editor-toolbar'
DECLUTTER_RUNTIME='--tos-task-details-declutter-v1-runtime'
MINIMAL_RUNTIME='--tos-task-details-minimal-v1-runtime'
MINIMAL_BUTTON_HOOK='tos-task-more-details-button'
MINIMAL_CONTROLS_HOOK='tos-task-summary-controls'
MINIMAL_START_HOOK='tos-task-start-date-card'
MINIMAL_TIME_HOOK='tos-task-execution-time-card'

DIST="$ROOT/frontend/dist"
LIVE_PARENT="/opt/apps/tamiyouz-front"
LIVE="$LIVE_PARENT/build"
STAMP="$(date +%Y%m%d-%H%M%S)"
STAGE="$LIVE_PARENT/build.phase03-2-minimal-v1.new.$$"
BACKUP="$LIVE_PARENT/build.phase03-2-minimal-v1.backup-$STAMP"

fail() {
  echo "PHASE03_2_TASK_DETAILS_MINIMAL_VIEW_V1=FAIL"
  echo "ERROR=$1" >&2
  exit "${2:-1}"
}

[ -d "$ROOT/.git" ] || fail "TOS repository not found" 2
[ -d "$PATCH_REPO_ROOT/.git" ] || fail "TOS-Patchs repository not found" 3
[ -f "$SOURCE_CSS" ] || fail "Minimal View CSS source missing" 4
for path in "$BOARD_TARGET" "$WORKSPACE_TARGET" "$CSS_TARGET" "$PARTS_TARGET"; do
  [ -f "$ROOT/$path" ] || fail "Missing target: $path" 5
done
[ -d "$LIVE" ] || fail "Live frontend root missing" 6

git -C "$ROOT" diff --cached --quiet || fail "Staged changes exist; stop" 7

# Allow only the known Phase 03/03.1 tracked files. Never touch unrelated work.
PRE_CHANGED="$(git -C "$ROOT" diff --name-only | sort)"
while IFS= read -r path; do
  [ -z "$path" ] && continue
  case "$path" in
    "$BOARD_TARGET"|"$WORKSPACE_TARGET"|"$CSS_TARGET"|"$PARTS_TARGET") ;;
    *) fail "Unexpected tracked change before Phase 03.2: $path" 8 ;;
  esac
done <<< "$PRE_CHANGED"

[ "$(grep -Fc -- "$ROOT_HOOK" "$ROOT/$BOARD_TARGET" || true)" = "1" ] || fail "Task Details root hook missing or duplicated" 9
[ "$(grep -Fc -- "$WORKSPACE_HOOK" "$ROOT/$WORKSPACE_TARGET" || true)" = "1" ] || fail "My Workspace hook missing or duplicated" 10
[ "$(grep -Fc -- "$DECLUTTER_LAYOUT_HOOK" "$ROOT/$BOARD_TARGET" || true)" = "1" ] || fail "Phase 03.1 layout hook missing or duplicated" 11
[ "$(grep -Fc -- "$DECLUTTER_PROGRESS_HOOK" "$ROOT/$BOARD_TARGET" || true)" = "1" ] || fail "Phase 03.1 progress hook missing or duplicated" 12
[ "$(grep -Fc -- "$DECLUTTER_SIDE_HOOK" "$ROOT/$BOARD_TARGET" || true)" -ge "1" ] || fail "Phase 03.1 side rail hook missing" 13
[ "$(grep -Fc -- "$DECLUTTER_TOOLBAR_HOOK" "$ROOT/$PARTS_TARGET" || true)" = "1" ] || fail "Phase 03.1 editor toolbar hook missing or duplicated" 14
[ "$(grep -Fc -- "$DECLUTTER_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "Phase 03.1 runtime missing or duplicated" 15

SOURCE_REL="${SOURCE_CSS#$PATCH_REPO_ROOT/}"
[ "$(git -C "$PATCH_REPO_ROOT" hash-object "$SOURCE_CSS")" = "$(git -C "$PATCH_REPO_ROOT" rev-parse "HEAD:$SOURCE_REL")" ] || fail "Minimal View CSS differs from TOS-Patchs HEAD" 16

MINIMAL_COUNT="$(grep -Fc -- "$MINIMAL_RUNTIME" "$ROOT/$CSS_TARGET" || true)"
BUTTON_COUNT="$(grep -Fc -- "$MINIMAL_BUTTON_HOOK" "$ROOT/$BOARD_TARGET" || true)"
CONTROLS_COUNT="$(grep -Fc -- "$MINIMAL_CONTROLS_HOOK" "$ROOT/$BOARD_TARGET" || true)"

if [ "$MINIMAL_COUNT" = "0" ] && [ "$BUTTON_COUNT" = "0" ] && [ "$CONTROLS_COUNT" = "0" ]; then
  python3 - "$ROOT/$BOARD_TARGET" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text()

def replace_once(old, new, label):
    global text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label} anchor count={count}")
    text = text.replace(old, new, 1)

replace_once(
    '  const [taskSidebarExpanded, setTaskSidebarExpanded] = useState(false);\n  const [isFullScreenWorkspace, setIsFullScreenWorkspace] = useState(true);',
    '  const [taskSidebarExpanded, setTaskSidebarExpanded] = useState(false);\n  const [taskMoreDetailsOpen, setTaskMoreDetailsOpen] = useState(false);\n  const [isFullScreenWorkspace, setIsFullScreenWorkspace] = useState(true);',
    'minimal state',
)

replace_once(
    '    setTaskSidebarExpanded(false);\n    setIsFullScreenWorkspace(true);',
    '    setTaskSidebarExpanded(false);\n    setTaskMoreDetailsOpen(false);\n    setIsFullScreenWorkspace(true);',
    'minimal reset',
)

replace_once(
    '<main className="tos-task-main-column min-w-0 space-y-4 text-right xl:order-2" dir={modalDirection}>',
    '<main className="tos-task-main-column min-w-0 space-y-4 text-right xl:order-2" data-more-details={taskMoreDetailsOpen ? "true" : "false"} dir={modalDirection}>',
    'main disclosure state',
)

replace_once(
    '<div className="grid gap-3 sm:grid-cols-2 lg:order-3">',
    '<div className="tos-task-summary-controls grid gap-3 sm:grid-cols-2 lg:order-3">',
    'summary controls hook',
)

start_anchor = '''<div className="rounded-[18px] border border-slate-100 bg-slate-50/80 px-3.5 py-3 dark:border-white/10 dark:bg-zinc-900/80">
                      <p className="flex items-center justify-between gap-2 text-xs font-black text-slate-400 dark:text-zinc-500"><span>{modalUi.startDate}</span><CalendarClock size={15} /></p>'''
start_repl = start_anchor.replace('<div className="', '<div className="tos-task-start-date-card ', 1)
replace_once(start_anchor, start_repl, 'start date hook')

replace_once(
    '<div className="mt-4 rounded-[20px] border border-amber-100 bg-gradient-to-br from-white to-amber-50/55 px-4 py-3 shadow-sm dark:border-amber-400/20 dark:from-zinc-950 dark:to-amber-500/10">',
    '<div className="tos-task-execution-time-card mt-4 rounded-[20px] border border-amber-100 bg-gradient-to-br from-white to-amber-50/55 px-4 py-3 shadow-sm dark:border-amber-400/20 dark:from-zinc-950 dark:to-amber-500/10">',
    'execution time hook',
)

replace_once(
    '<p className="mt-4 max-w-2xl border-r-[3px] border-amber-300 pr-3 text-sm font-bold leading-7 text-slate-500 dark:text-zinc-400">{taskHeaderDescription.slice(0, 170)}</p>',
    '<p className="tos-task-header-description mt-4 max-w-2xl border-r-[3px] border-amber-300 pr-3 text-sm font-bold leading-7 text-slate-500 dark:text-zinc-400">{taskHeaderDescription.slice(0, 170)}</p>',
    'header description hook',
)

replace_once(
    '<span className="rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-black tracking-wider text-slate-500 dark:border-white/10 dark:bg-zinc-900 dark:text-zinc-300">#{draft.id ? String(draft.id).slice(-8).toUpperCase() : "TASK"}</span>',
    '<span className="tos-task-id-badge rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-black tracking-wider text-slate-500 dark:border-white/10 dark:bg-zinc-900 dark:text-zinc-300">#{draft.id ? String(draft.id).slice(-8).toUpperCase() : "TASK"}</span>',
    'task id hook',
)

summary_end = '''              </section>

              {(String(draft.status || "").toUpperCase() === "WAITING_CLIENT" || waitingClientConversation.length > 0) && ('''
summary_new = '''              </section>

              <div className="tos-task-more-details-row">
                <button
                  type="button"
                  className="tos-task-more-details-button"
                  aria-expanded={taskMoreDetailsOpen}
                  onClick={() => {
                    const nextOpen = !taskMoreDetailsOpen;
                    setTaskMoreDetailsOpen(nextOpen);
                    if (!nextOpen && !["overview", "checklist"].includes(activeTaskTab)) setActiveTaskTab("overview");
                  }}
                >
                  <span>{taskMoreDetailsOpen ? (isAr ? "إخفاء التفاصيل الإضافية" : "Hide more details") : (isAr ? "تفاصيل أكثر" : "More details")}</span>
                  <ChevronDown size={15} className={`transition-transform ${taskMoreDetailsOpen ? "rotate-180" : ""}`} />
                </button>
              </div>

              {(String(draft.status || "").toUpperCase() === "WAITING_CLIENT" || waitingClientConversation.length > 0) && ('''
replace_once(summary_end, summary_new, 'more details control')

replace_once(
    '{taskDetailTabs.map((tab) => {',
    '{taskDetailTabs.filter((tab) => taskMoreDetailsOpen || ["overview", "checklist"].includes(tab.id)).map((tab) => {',
    'minimal tabs',
)

replace_once(
    '<aside className="tos-task-side-rail min-w-0 space-y-5 text-right xl:order-1 xl:sticky xl:top-0 xl:self-start" data-expanded={taskSidebarExpanded ? "true" : "false"} dir={modalDirection}>',
    '<aside className="tos-task-side-rail min-w-0 space-y-5 text-right xl:order-1 xl:sticky xl:top-0 xl:self-start" data-expanded={taskSidebarExpanded ? "true" : "false"} data-more-details={taskMoreDetailsOpen ? "true" : "false"} dir={modalDirection}>',
    'side rail disclosure state',
)

side_summary = '''                    <span>{isAr ? "المكلفون" : "Assignees"}: {currentAssigneeIds.length}</span>
                    <span>{isAr ? "المشروع" : "Project"}: {draft.project?.name || modalUi.noProject || "—"}</span>
                    <span>{isAr ? "النشاط" : "Activity"}: {draft.activities?.length || 0}</span>'''
side_new = '''                    <span>{isAr ? "المكلفون" : "Assignees"}: {currentAssigneeIds.length}</span>
                    {taskMoreDetailsOpen && <span>{isAr ? "المشروع" : "Project"}: {draft.project?.name || modalUi.noProject || "—"}</span>}
                    {taskMoreDetailsOpen && <span>{isAr ? "النشاط" : "Activity"}: {draft.activities?.length || 0}</span>}'''
replace_once(side_summary, side_new, 'minimal side summary')

path.write_text(text)
PY

  printf '\n' >> "$ROOT/$CSS_TARGET"
  cat "$SOURCE_CSS" >> "$ROOT/$CSS_TARGET"
  PATCH_ACTION="APPLIED"
elif [ "$MINIMAL_COUNT" = "1" ] && [ "$BUTTON_COUNT" = "1" ] && [ "$CONTROLS_COUNT" = "1" ]; then
  PATCH_ACTION="VALIDATED_EXISTING"
else
  fail "Partial Phase 03.2 minimal state detected" 17
fi

[ "$(grep -Fc -- "$MINIMAL_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "Minimal runtime missing or duplicated" 18
[ "$(grep -Fc -- "$MINIMAL_BUTTON_HOOK" "$ROOT/$BOARD_TARGET" || true)" = "1" ] || fail "More details button hook missing or duplicated" 19
[ "$(grep -Fc -- "$MINIMAL_CONTROLS_HOOK" "$ROOT/$BOARD_TARGET" || true)" = "1" ] || fail "Summary controls hook missing or duplicated" 20
[ "$(grep -Fc -- "$MINIMAL_START_HOOK" "$ROOT/$BOARD_TARGET" || true)" = "1" ] || fail "Start date hook missing or duplicated" 21
[ "$(grep -Fc -- "$MINIMAL_TIME_HOOK" "$ROOT/$BOARD_TARGET" || true)" = "1" ] || fail "Execution time hook missing or duplicated" 22
[ "$(grep -Fc -- 'taskMoreDetailsOpen' "$ROOT/$BOARD_TARGET" || true)" -ge "8" ] || fail "Minimal disclosure state incomplete" 23
[ "$(grep -Fc -- "$DECLUTTER_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "Phase 03.1 runtime changed" 24

git -C "$ROOT" diff --check -- "$BOARD_TARGET" "$WORKSPACE_TARGET" "$CSS_TARGET" "$PARTS_TARGET"

cd "$ROOT/frontend"
npm run build
cd "$ROOT"

[ -f "$DIST/index.html" ] || fail "Built dist index missing" 25
grep -RFlq -- "$MINIMAL_RUNTIME" "$DIST/assets" || fail "Minimal runtime missing from dist assets" 26
grep -RFlq -- "$MINIMAL_BUTTON_HOOK" "$DIST/assets" || fail "More details control missing from dist assets" 27
grep -RFlq -- "$DECLUTTER_TOOLBAR_HOOK" "$DIST/assets" || fail "Declutter editor toolbar missing from dist assets" 28

rm -rf "$STAGE"
mkdir -p "$STAGE"
cp -a "$DIST/." "$STAGE/"
[ -f "$STAGE/index.html" ] || fail "Staged index missing" 29
grep -RFlq -- "$MINIMAL_RUNTIME" "$STAGE/assets" || fail "Minimal runtime missing from staged assets" 30

mv "$LIVE" "$BACKUP"
if ! mv "$STAGE" "$LIVE"; then
  mv "$BACKUP" "$LIVE" || true
  fail "Failed to activate Phase 03.2 build; rollback attempted" 31
fi
if ! grep -RFlq -- "$MINIMAL_RUNTIME" "$LIVE/assets"; then
  rm -rf "$LIVE"
  mv "$BACKUP" "$LIVE" || true
  fail "Live minimal runtime missing; rolled back" 32
fi

POST_CHANGED="$(git -C "$ROOT" diff --name-only | sort)"
while IFS= read -r path; do
  [ -z "$path" ] && continue
  case "$path" in
    "$BOARD_TARGET"|"$WORKSPACE_TARGET"|"$CSS_TARGET"|"$PARTS_TARGET") ;;
    *) fail "Unexpected tracked change after Phase 03.2: $path" 33 ;;
  esac
done <<< "$POST_CHANGED"

git -C "$ROOT" diff --cached --quiet || fail "Unexpected staged changes after Phase 03.2" 34

BOARD_SHA="$(sha256sum "$ROOT/$BOARD_TARGET" | awk '{print $1}')"
WORKSPACE_SHA="$(sha256sum "$ROOT/$WORKSPACE_TARGET" | awk '{print $1}')"
CSS_SHA="$(sha256sum "$ROOT/$CSS_TARGET" | awk '{print $1}')"
PARTS_SHA="$(sha256sum "$ROOT/$PARTS_TARGET" | awk '{print $1}')"

echo "PHASE03_2_TASK_DETAILS_MINIMAL_VIEW_V1=PASS"
echo "SCREEN=Task_Details"
echo "MODE=Minimal_default_with_more_details_disclosure"
echo "PATCH_ACTION=$PATCH_ACTION"
echo "DEFAULT_VISIBLE=Title_Status_Priority_DueDate_Assignee_Description"
echo "MORE_DETAILS=StartDate_ExecutionTime_Progress_Project_Activity_SecondaryTabs"
echo "BUSINESS_LOGIC_CHANGED=NO"
echo "BUILD_RESULT=PASS"
echo "LIVE_DEPLOY=PASS"
echo "BOARD_SHA256=$BOARD_SHA"
echo "MY_WORKSPACE_SHA256=$WORKSPACE_SHA"
echo "TASKS_CSS_SHA256=$CSS_SHA"
echo "TASK_BOARD_PARTS_SHA256=$PARTS_SHA"
echo "NO_COMMIT_OR_PUSH=YES"
echo "--- GIT STATUS ---"
git -C "$ROOT" status --short
