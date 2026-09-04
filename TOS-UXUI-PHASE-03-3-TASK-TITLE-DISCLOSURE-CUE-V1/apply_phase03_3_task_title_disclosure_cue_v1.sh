#!/usr/bin/env bash
set -euo pipefail

echo "RUNNING=PHASE03_3_TASK_TITLE_DISCLOSURE_CUE_V1"

ROOT="${1:-/var/www/TOS}"
PATCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCH_REPO_ROOT="$(cd "$PATCH_DIR/.." && pwd)"
SOURCE_CSS="$PATCH_DIR/task-title-disclosure-cue-v1.css"

BOARD_TARGET="frontend/src/components/ProfessionalTaskBoard.jsx"
WORKSPACE_TARGET="frontend/src/pages/MyTaskWorkspace.jsx"
CSS_TARGET="frontend/src/styles/tasks-projects-premium-reference.css"
PARTS_TARGET="frontend/src/features/tasks/taskBoardParts.jsx"

ROOT_HOOK='tos-task-details-modal'
DECLUTTER_RUNTIME='--tos-task-details-declutter-v1-runtime'
MINIMAL_RUNTIME='--tos-task-details-minimal-v1-runtime'
MINIMAL_BUTTON_HOOK='tos-task-more-details-button'
SIDE_TOGGLE_HOOK='tos-task-side-rail-toggle'
TITLE_HOOK='tos-task-title-input'
CUE_RUNTIME='--tos-task-title-disclosure-cue-v1-runtime'

DIST="$ROOT/frontend/dist"
LIVE_PARENT="/opt/apps/tamiyouz-front"
LIVE="$LIVE_PARENT/build"
STAMP="$(date +%Y%m%d-%H%M%S)"
STAGE="$LIVE_PARENT/build.phase03-3-title-cue-v1.new.$$"
BACKUP="$LIVE_PARENT/build.phase03-3-title-cue-v1.backup-$STAMP"

fail() {
  echo "PHASE03_3_TASK_TITLE_DISCLOSURE_CUE_V1=FAIL"
  echo "ERROR=$1" >&2
  exit "${2:-1}"
}

[ -d "$ROOT/.git" ] || fail "TOS repository not found" 2
[ -d "$PATCH_REPO_ROOT/.git" ] || fail "TOS-Patchs repository not found" 3
[ -f "$SOURCE_CSS" ] || fail "Phase 03.3 CSS source missing" 4
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
    *) fail "Unexpected tracked change before Phase 03.3: $path" 8 ;;
  esac
done <<< "$PRE_CHANGED"

[ "$(grep -Fc -- "$ROOT_HOOK" "$ROOT/$BOARD_TARGET" || true)" = "1" ] || fail "Task Details root hook missing or duplicated" 9
[ "$(grep -Fc -- "$DECLUTTER_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "Phase 03.1 runtime missing or duplicated" 10
[ "$(grep -Fc -- "$MINIMAL_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "Phase 03.2 runtime missing or duplicated" 11
[ "$(grep -Fc -- "$MINIMAL_BUTTON_HOOK" "$ROOT/$BOARD_TARGET" || true)" = "1" ] || fail "More details hook missing or duplicated" 12
[ "$(grep -Fc -- "$SIDE_TOGGLE_HOOK" "$ROOT/$BOARD_TARGET" || true)" = "1" ] || fail "Side details toggle hook missing or duplicated" 13

SOURCE_REL="${SOURCE_CSS#$PATCH_REPO_ROOT/}"
[ "$(git -C "$PATCH_REPO_ROOT" hash-object "$SOURCE_CSS")" = "$(git -C "$PATCH_REPO_ROOT" rev-parse "HEAD:$SOURCE_REL")" ] || fail "Phase 03.3 CSS differs from TOS-Patchs HEAD" 14

TITLE_COUNT="$(grep -Fc -- "$TITLE_HOOK" "$ROOT/$BOARD_TARGET" || true)"
CUE_COUNT="$(grep -Fc -- "$CUE_RUNTIME" "$ROOT/$CSS_TARGET" || true)"

if [ "$TITLE_COUNT" = "0" ] && [ "$CUE_COUNT" = "0" ]; then
  python3 - "$ROOT/$BOARD_TARGET" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text()
anchor = 'aria-label={modalUi.taskTitle}'
start = text.find(anchor)
if start < 0:
    raise SystemExit('task title input anchor missing')
window_end = min(len(text), start + 1800)
window = text[start:window_end]
needle = 'className="w-full rounded-xl border border-transparent bg-transparent px-2 py-1.5 text-right text-3xl font-black tracking-[-0.03em] text-slate-950 outline-none transition hover:border-slate-100 focus:border-amber-200 focus:bg-amber-50/40 focus:ring-4 focus:ring-amber-50 dark:text-white dark:hover:border-white/10 dark:focus:bg-amber-500/10"'
if window.count(needle) != 1:
    raise SystemExit(f'task title class anchor count={window.count(needle)}')
window = window.replace(needle, needle.replace('className="', 'className="tos-task-title-input ', 1), 1)
text = text[:start] + window + text[window_end:]
path.write_text(text)
PY

  printf '\n' >> "$ROOT/$CSS_TARGET"
  cat "$SOURCE_CSS" >> "$ROOT/$CSS_TARGET"
  PATCH_ACTION="APPLIED"
elif [ "$TITLE_COUNT" = "1" ] && [ "$CUE_COUNT" = "1" ]; then
  PATCH_ACTION="VALIDATED_EXISTING"
else
  fail "Partial Phase 03.3 state detected" 15
fi

[ "$(grep -Fc -- "$TITLE_HOOK" "$ROOT/$BOARD_TARGET" || true)" = "1" ] || fail "Task title hook missing or duplicated" 16
[ "$(grep -Fc -- "$CUE_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "Phase 03.3 runtime missing or duplicated" 17
[ "$(grep -Fc -- "$MINIMAL_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "Phase 03.2 runtime changed" 18

git -C "$ROOT" diff --check -- "$BOARD_TARGET" "$WORKSPACE_TARGET" "$CSS_TARGET" "$PARTS_TARGET"

cd "$ROOT/frontend"
npm run build
cd "$ROOT"

[ -f "$DIST/index.html" ] || fail "Built dist index missing" 19
grep -RFlq -- "$CUE_RUNTIME" "$DIST/assets" || fail "Phase 03.3 runtime missing from dist assets" 20
grep -RFlq -- "$TITLE_HOOK" "$DIST/assets" || fail "Task title hook missing from dist assets" 21
grep -RFlq -- "$MINIMAL_BUTTON_HOOK" "$DIST/assets" || fail "More details hook missing from dist assets" 22

rm -rf "$STAGE"
mkdir -p "$STAGE"
cp -a "$DIST/." "$STAGE/"
[ -f "$STAGE/index.html" ] || fail "Staged index missing" 23
grep -RFlq -- "$CUE_RUNTIME" "$STAGE/assets" || fail "Phase 03.3 runtime missing from staged assets" 24

mv "$LIVE" "$BACKUP"
if ! mv "$STAGE" "$LIVE"; then
  mv "$BACKUP" "$LIVE" || true
  fail "Failed to activate Phase 03.3 build; rollback attempted" 25
fi
if ! grep -RFlq -- "$CUE_RUNTIME" "$LIVE/assets"; then
  rm -rf "$LIVE"
  mv "$BACKUP" "$LIVE" || true
  fail "Live Phase 03.3 runtime missing; rolled back" 26
fi

POST_CHANGED="$(git -C "$ROOT" diff --name-only | sort)"
while IFS= read -r path; do
  [ -z "$path" ] && continue
  case "$path" in
    "$BOARD_TARGET"|"$WORKSPACE_TARGET"|"$CSS_TARGET"|"$PARTS_TARGET") ;;
    *) fail "Unexpected tracked change after Phase 03.3: $path" 27 ;;
  esac
done <<< "$POST_CHANGED"

git -C "$ROOT" diff --cached --quiet || fail "Unexpected staged changes after Phase 03.3" 28

BOARD_SHA="$(sha256sum "$ROOT/$BOARD_TARGET" | awk '{print $1}')"
WORKSPACE_SHA="$(sha256sum "$ROOT/$WORKSPACE_TARGET" | awk '{print $1}')"
CSS_SHA="$(sha256sum "$ROOT/$CSS_TARGET" | awk '{print $1}')"
PARTS_SHA="$(sha256sum "$ROOT/$PARTS_TARGET" | awk '{print $1}')"

echo "PHASE03_3_TASK_TITLE_DISCLOSURE_CUE_V1=PASS"
echo "SCREEN=Task_Details"
echo "FIX=Long_title_fit_and_more_details_discoverability_motion"
echo "PATCH_ACTION=$PATCH_ACTION"
echo "LIGHT_DARK=SUPPORTED"
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
