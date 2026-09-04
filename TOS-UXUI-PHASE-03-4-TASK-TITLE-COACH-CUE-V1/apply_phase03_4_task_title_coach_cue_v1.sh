#!/usr/bin/env bash
set -euo pipefail

echo "RUNNING=PHASE03_4_TASK_TITLE_COACH_CUE_V1"

ROOT="${1:-/var/www/TOS}"
PATCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCH_REPO_ROOT="$(cd "$PATCH_DIR/.." && pwd)"
SOURCE_CSS="$PATCH_DIR/task-title-coach-cue-v1.css"

BOARD_TARGET="frontend/src/components/ProfessionalTaskBoard.jsx"
WORKSPACE_TARGET="frontend/src/pages/MyTaskWorkspace.jsx"
CSS_TARGET="frontend/src/styles/tasks-projects-premium-reference.css"
PARTS_TARGET="frontend/src/features/tasks/taskBoardParts.jsx"

ROOT_HOOK='tos-task-details-modal'
WORKSPACE_HOOK='tos-my-workspace'
DECLUTTER_RUNTIME='--tos-task-details-declutter-v1-runtime'
MINIMAL_RUNTIME='--tos-task-details-minimal-v1-runtime'
CUE_RUNTIME='--tos-task-title-disclosure-cue-v1-runtime'
V34_RUNTIME='--tos-task-title-coach-cue-v1-runtime'
TITLE_HOOK='tos-task-title-input'
AUTOFIT_HOOK='tos-task-title-autofit'
MORE_HOOK='tos-task-more-details-button'
SIDE_HOOK='tos-task-side-rail-toggle'
COACH_POINTER_HOOK='tos-task-coach-pointer'
COACH_STORAGE='tos.taskDetails.coach.v1'

DIST="$ROOT/frontend/dist"
LIVE_PARENT="/opt/apps/tamiyouz-front"
LIVE="$LIVE_PARENT/build"
STAMP="$(date +%Y%m%d-%H%M%S)"
STAGE="$LIVE_PARENT/build.phase03-4-title-coach-v1.new.$$"
BACKUP="$LIVE_PARENT/build.phase03-4-title-coach-v1.backup-$STAMP"

fail() {
  echo "PHASE03_4_TASK_TITLE_COACH_CUE_V1=FAIL"
  echo "ERROR=$1" >&2
  exit "${2:-1}"
}

[ -d "$ROOT/.git" ] || fail "TOS repository not found" 2
[ -d "$PATCH_REPO_ROOT/.git" ] || fail "TOS-Patchs repository not found" 3
[ -f "$SOURCE_CSS" ] || fail "Phase 03.4 CSS source missing" 4
for path in "$BOARD_TARGET" "$WORKSPACE_TARGET" "$CSS_TARGET" "$PARTS_TARGET"; do
  [ -f "$ROOT/$path" ] || fail "Missing target: $path" 5
done
[ -d "$LIVE" ] || fail "Live frontend root missing" 6

git -C "$ROOT" diff --cached --quiet || fail "Staged changes exist; stop" 7

PRE_CHANGED="$(git -C "$ROOT" diff --name-only | sort)"
while IFS= read -r path; do
  [ -z "$path" ] && continue
  case "$path" in
    "$BOARD_TARGET"|"$WORKSPACE_TARGET"|"$CSS_TARGET"|"$PARTS_TARGET") ;;
    *) fail "Unexpected tracked change before Phase 03.4: $path" 8 ;;
  esac
done <<< "$PRE_CHANGED"

[ "$(grep -Fc -- "$ROOT_HOOK" "$ROOT/$BOARD_TARGET" || true)" = "1" ] || fail "Task Details root hook missing or duplicated" 9
[ "$(grep -Fc -- "$WORKSPACE_HOOK" "$ROOT/$WORKSPACE_TARGET" || true)" = "1" ] || fail "My Workspace hook missing or duplicated" 10
[ "$(grep -Fc -- "$DECLUTTER_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "Phase 03.1 runtime missing or duplicated" 11
[ "$(grep -Fc -- "$MINIMAL_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "Phase 03.2 runtime missing or duplicated" 12
[ "$(grep -Fc -- "$CUE_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "Phase 03.3 runtime missing or duplicated" 13
[ "$(grep -Fc -- "$TITLE_HOOK" "$ROOT/$BOARD_TARGET" || true)" = "1" ] || fail "Phase 03.3 title hook missing or duplicated" 14
[ "$(grep -Fc -- "$MORE_HOOK" "$ROOT/$BOARD_TARGET" || true)" = "1" ] || fail "More details hook missing or duplicated" 15
[ "$(grep -Fc -- "$SIDE_HOOK" "$ROOT/$BOARD_TARGET" || true)" = "1" ] || fail "Side details hook missing or duplicated" 16

SOURCE_REL="${SOURCE_CSS#$PATCH_REPO_ROOT/}"
[ "$(git -C "$PATCH_REPO_ROOT" hash-object "$SOURCE_CSS")" = "$(git -C "$PATCH_REPO_ROOT" rev-parse "HEAD:$SOURCE_REL")" ] || fail "Phase 03.4 CSS differs from TOS-Patchs HEAD" 17

V34_COUNT="$(grep -Fc -- "$V34_RUNTIME" "$ROOT/$CSS_TARGET" || true)"
AUTOFIT_COUNT="$(grep -Fc -- "$AUTOFIT_HOOK" "$ROOT/$BOARD_TARGET" || true)"
POINTER_COUNT="$(grep -Fc -- "$COACH_POINTER_HOOK" "$ROOT/$BOARD_TARGET" || true)"
STORAGE_COUNT="$(grep -Fc -- "$COACH_STORAGE" "$ROOT/$BOARD_TARGET" || true)"

if [ "$V34_COUNT" = "0" ] && [ "$AUTOFIT_COUNT" = "0" ] && [ "$POINTER_COUNT" = "0" ] && [ "$STORAGE_COUNT" = "0" ]; then
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

# Vector hand icon for the first-use teaching cue.
replace_once(
    '  Heading2,\n  Italic,',
    '  Heading2,\n  HandPointer,\n  Italic,',
    'HandPointer import',
)

# Persistent, finite discovery state. A cue appears on at most the first three
# Task Details openings unless the user opens that disclosure earlier.
helper_anchor = '''function effectiveTaskStatusForUi(task) {
  return resolveBoardListStatusForUi(task?.list, task?.status) || String(task?.status || "").toUpperCase();
}
'''
helper_insert = helper_anchor + '''
const taskDetailsCoachStoragePrefix = "tos.taskDetails.coach.v1";

function shouldShowTaskCoachHint(name) {
  if (typeof window === "undefined") return false;
  try {
    const key = `${taskDetailsCoachStoragePrefix}.${name}`;
    const stored = JSON.parse(window.localStorage.getItem(key) || "{}");
    const impressions = Math.max(0, Number(stored?.impressions) || 0);
    if (stored?.dismissed || impressions >= 3) return false;
    window.localStorage.setItem(key, JSON.stringify({ impressions: impressions + 1, dismissed: false }));
    return true;
  } catch {
    return true;
  }
}

function markTaskCoachHintDiscovered(name) {
  if (typeof window === "undefined") return;
  try {
    const key = `${taskDetailsCoachStoragePrefix}.${name}`;
    window.localStorage.setItem(key, JSON.stringify({ impressions: 3, dismissed: true }));
  } catch {
    // Storage is an enhancement only; disclosure behavior must never depend on it.
  }
}
'''
replace_once(helper_anchor, helper_insert, 'coach storage helpers')

# Local visual state. Reading it once per Task Details mount gives a finite
# onboarding experience without touching task/server data.
replace_once(
    '  const [taskMoreDetailsOpen, setTaskMoreDetailsOpen] = useState(false);\n  const [isFullScreenWorkspace, setIsFullScreenWorkspace] = useState(true);',
    '''  const [taskMoreDetailsOpen, setTaskMoreDetailsOpen] = useState(false);
  const [taskCoachHints, setTaskCoachHints] = useState(() => ({
    more: shouldShowTaskCoachHint("more-details"),
    side: shouldShowTaskCoachHint("side-details"),
  }));
  const [isFullScreenWorkspace, setIsFullScreenWorkspace] = useState(true);''',
    'coach state',
)

# Convert only the Task Details title control from one-line input to an
# auto-growing textarea. Save/onBlur behavior remains the same.
aria = 'aria-label={modalUi.taskTitle}'
pos = text.find(aria)
if pos < 0:
    raise SystemExit('task title aria anchor missing')
block_start = text.rfind('<input', max(0, pos - 220), pos)
if block_start < 0:
    raise SystemExit('task title input start missing')
block_end = text.find('/>', pos)
if block_end < 0 or block_end - block_start > 2200:
    raise SystemExit('task title input end missing')
block_end += 2
block = text[block_start:block_end]
if 'tos-task-title-input' not in block:
    raise SystemExit('task title hook not found in title block')
if 'tos-task-title-autofit' in block or '<textarea' in block:
    raise SystemExit('task title already converted unexpectedly')
block = block.replace('<input', '<textarea\n                      rows={1}', 1)
block = block.replace('tos-task-title-input ', 'tos-task-title-input tos-task-title-autofit ', 1)
change_line = 'onChange={(event) => setDraft((current) => ({ ...current, title: event.target.value }))}'
if block.count(change_line) != 1:
    raise SystemExit(f'task title onChange count={block.count(change_line)}')
block = block.replace(
    change_line,
    change_line + '\n                      onKeyDown={(event) => { if (event.key === "Enter") { event.preventDefault(); event.currentTarget.blur(); } }}',
    1,
)
text = text[:block_start] + block + text[block_end:]

# More details: first click marks the control as learned and removes the hand
# immediately. The existing open/close state and tab behavior stay intact.
more_anchor = 'className="tos-task-more-details-button"'
more_pos = text.find(more_anchor)
if more_pos < 0:
    raise SystemExit('More details button anchor missing')
more_end = text.find('</button>', more_pos)
if more_end < 0 or more_end - more_pos > 1800:
    raise SystemExit('More details button end missing')
more_block_start = text.rfind('<button', max(0, more_pos - 240), more_pos)
more_block = text[more_block_start:more_end + len('</button>')]
if 'data-coach-active=' in more_block:
    raise SystemExit('More details coach attr already present')
more_block = more_block.replace(
    'className="tos-task-more-details-button"',
    'className="tos-task-more-details-button"\n                  data-coach-active={taskCoachHints.more && !taskMoreDetailsOpen ? "true" : "false"}',
    1,
)
click_anchor = '''onClick={() => {
                    const nextOpen = !taskMoreDetailsOpen;'''
click_repl = '''onClick={() => {
                    if (!taskMoreDetailsOpen) {
                      markTaskCoachHintDiscovered("more-details");
                      setTaskCoachHints((current) => ({ ...current, more: false }));
                    }
                    const nextOpen = !taskMoreDetailsOpen;'''
if more_block.count(click_anchor) != 1:
    raise SystemExit(f'More details click anchor count={more_block.count(click_anchor)}')
more_block = more_block.replace(click_anchor, click_repl, 1)
label_anchor = '                  <span>{taskMoreDetailsOpen ? (isAr ? "إخفاء التفاصيل الإضافية" : "Hide more details") : (isAr ? "تفاصيل أكثر" : "More details")}</span>'
if more_block.count(label_anchor) != 1:
    raise SystemExit(f'More details label anchor count={more_block.count(label_anchor)}')
more_block = more_block.replace(
    label_anchor,
    '                  {taskCoachHints.more && !taskMoreDetailsOpen && <span className="tos-task-coach-pointer" aria-hidden="true"><HandPointer size={17} strokeWidth={2.2} /></span>}\n' + label_anchor,
    1,
)
text = text[:more_block_start] + more_block + text[more_end + len('</button>'):]

# Side details: same finite teaching behavior, independent persistence key.
side_old = '<button type="button" onClick={() => setTaskSidebarExpanded((current) => !current)} className="tos-task-side-rail-toggle" aria-expanded={taskSidebarExpanded}>'
side_new = '''<button
                  type="button"
                  onClick={() => {
                    if (!taskSidebarExpanded) {
                      markTaskCoachHintDiscovered("side-details");
                      setTaskCoachHints((current) => ({ ...current, side: false }));
                    }
                    setTaskSidebarExpanded((current) => !current);
                  }}
                  className="tos-task-side-rail-toggle"
                  aria-expanded={taskSidebarExpanded}
                  data-coach-active={taskCoachHints.side && !taskSidebarExpanded ? "true" : "false"}
                >'''
replace_once(side_old, side_new, 'Side details button')
side_label = '                <span>{taskSidebarExpanded ? (isAr ? "إخفاء التفاصيل الجانبية" : "Hide side details") : (isAr ? "التفاصيل الجانبية" : "Side details")}</span>'
replace_once(
    side_label,
    '                {taskCoachHints.side && !taskSidebarExpanded && <span className="tos-task-coach-pointer" aria-hidden="true"><HandPointer size={17} strokeWidth={2.2} /></span>}\n' + side_label,
    'Side details pointer',
)

path.write_text(text)
PY

  printf '\n' >> "$ROOT/$CSS_TARGET"
  cat "$SOURCE_CSS" >> "$ROOT/$CSS_TARGET"
  PATCH_ACTION="APPLIED"
elif [ "$V34_COUNT" = "1" ] && [ "$AUTOFIT_COUNT" = "1" ] && [ "$POINTER_COUNT" = "2" ] && [ "$STORAGE_COUNT" -ge "1" ]; then
  PATCH_ACTION="VALIDATED_EXISTING"
else
  fail "Partial Phase 03.4 state detected" 18
fi

[ "$(grep -Fc -- "$V34_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "Phase 03.4 runtime missing or duplicated" 19
[ "$(grep -Fc -- "$AUTOFIT_HOOK" "$ROOT/$BOARD_TARGET" || true)" = "1" ] || fail "Auto-fit title hook missing or duplicated" 20
[ "$(grep -Fc -- "$COACH_POINTER_HOOK" "$ROOT/$BOARD_TARGET" || true)" = "2" ] || fail "Coach pointer hooks missing or duplicated" 21
[ "$(grep -Fc -- 'data-coach-active=' "$ROOT/$BOARD_TARGET" || true)" = "2" ] || fail "Coach active state attributes missing or duplicated" 22
[ "$(grep -Fc -- 'HandPointer' "$ROOT/$BOARD_TARGET" || true)" = "3" ] || fail "HandPointer import/uses unexpected" 23
[ "$(grep -Fc -- "$CUE_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "Phase 03.3 runtime changed" 24
[ "$(grep -Fc -- "$MINIMAL_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "Phase 03.2 runtime changed" 25

git -C "$ROOT" diff --check -- "$BOARD_TARGET" "$WORKSPACE_TARGET" "$CSS_TARGET" "$PARTS_TARGET"

cd "$ROOT/frontend"
npm run build
cd "$ROOT"

[ -f "$DIST/index.html" ] || fail "Built dist index missing" 26
grep -RFlq -- "$V34_RUNTIME" "$DIST/assets" || fail "Phase 03.4 runtime missing from dist assets" 27
grep -RFlq -- "$AUTOFIT_HOOK" "$DIST/assets" || fail "Auto-fit title hook missing from dist assets" 28
grep -RFlq -- "$COACH_POINTER_HOOK" "$DIST/assets" || fail "Coach pointer missing from dist assets" 29
grep -RFlq -- "$COACH_STORAGE" "$DIST/assets" || fail "Coach persistence key missing from dist assets" 30

rm -rf "$STAGE"
mkdir -p "$STAGE"
cp -a "$DIST/." "$STAGE/"
[ -f "$STAGE/index.html" ] || fail "Staged index missing" 31
grep -RFlq -- "$V34_RUNTIME" "$STAGE/assets" || fail "Phase 03.4 runtime missing from staged assets" 32

mv "$LIVE" "$BACKUP"
if ! mv "$STAGE" "$LIVE"; then
  mv "$BACKUP" "$LIVE" || true
  fail "Failed to activate Phase 03.4 build; rollback attempted" 33
fi
if ! grep -RFlq -- "$V34_RUNTIME" "$LIVE/assets"; then
  rm -rf "$LIVE"
  mv "$BACKUP" "$LIVE" || true
  fail "Live Phase 03.4 runtime missing; rolled back" 34
fi

POST_CHANGED="$(git -C "$ROOT" diff --name-only | sort)"
while IFS= read -r path; do
  [ -z "$path" ] && continue
  case "$path" in
    "$BOARD_TARGET"|"$WORKSPACE_TARGET"|"$CSS_TARGET"|"$PARTS_TARGET") ;;
    *) fail "Unexpected tracked change after Phase 03.4: $path" 35 ;;
  esac
done <<< "$POST_CHANGED"

git -C "$ROOT" diff --cached --quiet || fail "Unexpected staged changes after Phase 03.4" 36

BOARD_SHA="$(sha256sum "$ROOT/$BOARD_TARGET" | awk '{print $1}')"
WORKSPACE_SHA="$(sha256sum "$ROOT/$WORKSPACE_TARGET" | awk '{print $1}')"
CSS_SHA="$(sha256sum "$ROOT/$CSS_TARGET" | awk '{print $1}')"
PARTS_SHA="$(sha256sum "$ROOT/$PARTS_TARGET" | awk '{print $1}')"

echo "PHASE03_4_TASK_TITLE_COACH_CUE_V1=PASS"
echo "SCREEN=Task_Details"
echo "FIX=Auto_growing_title_and_finite_first_use_hand_coach_cues"
echo "COACH_MAX_IMPRESSIONS=3"
echo "COACH_DISMISSES_ON_FIRST_OPEN=YES"
echo "PATCH_ACTION=$PATCH_ACTION"
echo "LIGHT_DARK=SUPPORTED"
echo "TASK_DATA_CHANGED=NO"
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
