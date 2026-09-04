#!/usr/bin/env bash
set -euo pipefail

echo "RUNNING=V5L_TASK_DETAILS_DARK_VISIBILITY_FINAL"

ROOT="${1:-/var/www/TOS}"
PATCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCH_REPO_ROOT="$(cd "$PATCH_DIR/.." && pwd)"
SOURCE_CSS="$PATCH_DIR/task-details-dark-visibility-v5l.css"

BOARD_TARGET="frontend/src/components/ProfessionalTaskBoard.jsx"
WORKSPACE_TARGET="frontend/src/pages/MyTaskWorkspace.jsx"
CSS_TARGET="frontend/src/styles/tasks-projects-premium-reference.css"

ROOT_HOOK='tos-task-details-modal'
WORKSPACE_HOOK='tos-my-workspace'
SAVE_HOOK='tos-save-description-button'
DATE_HOOK='tos-task-date-input'
V5G_RUNTIME='--tos-my-workspace-dark-select-v5g-runtime'
V5I_RUNTIME='--tos-task-details-dark-contrast-v5i-runtime'
V5K_RUNTIME='--tos-task-details-dark-visibility-v5k-runtime'
V5L_RUNTIME='--tos-task-details-dark-visibility-v5l-runtime'

DIST="$ROOT/frontend/dist"
LIVE_PARENT="/opt/apps/tamiyouz-front"
LIVE="$LIVE_PARENT/build"
STAMP="$(date +%Y%m%d-%H%M%S)"
STAGE="$LIVE_PARENT/build.phase03-v5l.new.$$"
BACKUP="$LIVE_PARENT/build.phase03-v5l.backup-$STAMP"

fail() {
  echo "PHASE03_TASKS_TASK_DETAILS_DARK_VISIBILITY_V5L=FAIL"
  echo "ERROR=$1" >&2
  exit "${2:-1}"
}

[ -d "$ROOT/.git" ] || fail "TOS repository not found" 2
[ -d "$PATCH_REPO_ROOT/.git" ] || fail "TOS-Patchs repository not found" 3
[ -f "$SOURCE_CSS" ] || fail "V5L CSS source missing" 4
[ -f "$ROOT/$BOARD_TARGET" ] || fail "ProfessionalTaskBoard.jsx missing" 5
[ -f "$ROOT/$WORKSPACE_TARGET" ] || fail "MyTaskWorkspace.jsx missing" 6
[ -f "$ROOT/$CSS_TARGET" ] || fail "Tasks stylesheet missing" 7
[ -d "$LIVE" ] || fail "Live frontend root missing" 8

git -C "$ROOT" diff --cached --quiet || fail "Staged changes exist; stop" 9

CHANGED_BEFORE="$(git -C "$ROOT" diff --name-only | sort)"
EXPECTED_CHANGED="$(printf '%s\n%s\n%s\n' "$BOARD_TARGET" "$WORKSPACE_TARGET" "$CSS_TARGET" | sort)"
[ "$CHANGED_BEFORE" = "$EXPECTED_CHANGED" ] || {
  echo "--- TRACKED CHANGES BEFORE V5L ---"
  printf '%s\n' "$CHANGED_BEFORE"
  fail "Unexpected tracked state before V5L" 10
}

[ "$(grep -Fc -- "$ROOT_HOOK" "$ROOT/$BOARD_TARGET" || true)" = "1" ] || fail "Task Details root hook missing or duplicated" 11
[ "$(grep -Fc -- "$WORKSPACE_HOOK" "$ROOT/$WORKSPACE_TARGET" || true)" = "1" ] || fail "My Workspace hook missing or duplicated" 12
[ "$(grep -Fc -- "$V5G_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "V5G runtime missing or duplicated" 13
[ "$(grep -Fc -- "$V5I_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "V5I runtime missing or duplicated" 14
[ "$(grep -Fc -- "$V5K_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "V5K runtime missing or duplicated" 15

SOURCE_REL="${SOURCE_CSS#$PATCH_REPO_ROOT/}"
[ "$(git -C "$PATCH_REPO_ROOT" hash-object "$SOURCE_CSS")" = "$(git -C "$PATCH_REPO_ROOT" rev-parse "HEAD:$SOURCE_REL")" ] || fail "V5L CSS source differs from TOS-Patchs HEAD" 16

SAVE_COUNT="$(grep -Fc -- "$SAVE_HOOK" "$ROOT/$BOARD_TARGET" || true)"
DATE_COUNT="$(grep -Fc -- "$DATE_HOOK" "$ROOT/$BOARD_TARGET" || true)"
V5L_COUNT="$(grep -Fc -- "$V5L_RUNTIME" "$ROOT/$CSS_TARGET" || true)"

if [ "$SAVE_COUNT" = "0" ] && [ "$DATE_COUNT" = "0" ] && [ "$V5L_COUNT" = "0" ]; then
  python3 - "$ROOT/$BOARD_TARGET" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text()

save_old = 'className={primaryActionClass}><Save size={14} /> {modalUi.saveDescription}</button>'
save_new = 'className={`${primaryActionClass} tos-save-description-button`}><Save size={14} /> {modalUi.saveDescription}</button>'
if text.count(save_old) != 1:
    raise SystemExit(f"save description anchor count={text.count(save_old)}")
text = text.replace(save_old, save_new, 1)

date_old = 'className="mt-2 w-full bg-transparent text-base font-black text-slate-950 outline-none disabled:text-slate-500 dark:text-white"'
date_new = 'className="tos-task-date-input mt-2 w-full bg-transparent text-base font-black text-slate-950 outline-none disabled:text-slate-500 dark:text-white"'
if text.count(date_old) != 2:
    raise SystemExit(f"task date class anchor count={text.count(date_old)}")
text = text.replace(date_old, date_new)

path.write_text(text)
PY

  printf '\n' >> "$ROOT/$CSS_TARGET"
  cat "$SOURCE_CSS" >> "$ROOT/$CSS_TARGET"
  PATCH_ACTION="APPLIED"
elif [ "$SAVE_COUNT" = "1" ] && [ "$DATE_COUNT" = "2" ] && [ "$V5L_COUNT" = "1" ]; then
  PATCH_ACTION="VALIDATED_EXISTING"
else
  fail "Partial V5L state detected" 17
fi

[ "$(grep -Fc -- "$SAVE_HOOK" "$ROOT/$BOARD_TARGET" || true)" = "1" ] || fail "Save Description hook missing or duplicated" 18
[ "$(grep -Fc -- "$DATE_HOOK" "$ROOT/$BOARD_TARGET" || true)" = "2" ] || fail "Task date hooks missing or duplicated" 19
[ "$(grep -Fc -- "$V5L_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "V5L runtime missing or duplicated" 20
[ "$(grep -Fc -- "$V5K_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "V5K runtime changed during V5L" 21

git -C "$ROOT" diff --check -- "$BOARD_TARGET" "$WORKSPACE_TARGET" "$CSS_TARGET"

cd "$ROOT/frontend"
npm run build
cd "$ROOT"

[ -f "$DIST/index.html" ] || fail "Built dist index missing" 22
grep -RFlq -- "$V5L_RUNTIME" "$DIST/assets" || fail "V5L runtime missing from dist assets" 23
grep -RFlq -- "$SAVE_HOOK" "$DIST/assets" || fail "Save Description hook missing from dist assets" 24
grep -RFlq -- "$DATE_HOOK" "$DIST/assets" || fail "Task date hook missing from dist assets" 25

rm -rf "$STAGE"
mkdir -p "$STAGE"
cp -a "$DIST/." "$STAGE/"
[ -f "$STAGE/index.html" ] || fail "Staged index missing" 26
grep -RFlq -- "$V5L_RUNTIME" "$STAGE/assets" || fail "V5L runtime missing from staged assets" 27

mv "$LIVE" "$BACKUP"
if ! mv "$STAGE" "$LIVE"; then
  mv "$BACKUP" "$LIVE" || true
  fail "Failed to activate V5L live build; rollback attempted" 28
fi
if ! grep -RFlq -- "$V5L_RUNTIME" "$LIVE/assets"; then
  rm -rf "$LIVE"
  mv "$BACKUP" "$LIVE" || true
  fail "Live V5L runtime missing; rolled back" 29
fi

CHANGED_AFTER="$(git -C "$ROOT" diff --name-only | sort)"
[ "$CHANGED_AFTER" = "$EXPECTED_CHANGED" ] || {
  echo "--- TRACKED CHANGES AFTER V5L ---"
  printf '%s\n' "$CHANGED_AFTER"
  fail "Unexpected tracked files after V5L" 30
}

git -C "$ROOT" diff --cached --quiet || fail "Unexpected staged changes after V5L" 31

BOARD_SHA="$(sha256sum "$ROOT/$BOARD_TARGET" | awk '{print $1}')"
WORKSPACE_SHA="$(sha256sum "$ROOT/$WORKSPACE_TARGET" | awk '{print $1}')"
CSS_SHA="$(sha256sum "$ROOT/$CSS_TARGET" | awk '{print $1}')"

echo "PHASE03_TASKS_TASK_DETAILS_DARK_VISIBILITY_V5L=PASS"
echo "SCREEN=Task_Details"
echo "FIX=Native_date_value_and_save_description_visibility"
echo "PATCH_ACTION=$PATCH_ACTION"
echo "LIGHT_MODE_CHANGED=NO"
echo "BUSINESS_LOGIC_CHANGED=NO"
echo "BUILD_RESULT=PASS"
echo "LIVE_DEPLOY=PASS"
echo "BOARD_SHA256=$BOARD_SHA"
echo "MY_WORKSPACE_SHA256=$WORKSPACE_SHA"
echo "TASKS_CSS_SHA256=$CSS_SHA"
echo "NO_COMMIT_OR_PUSH=YES"
echo "--- GIT STATUS ---"
git -C "$ROOT" status --short
