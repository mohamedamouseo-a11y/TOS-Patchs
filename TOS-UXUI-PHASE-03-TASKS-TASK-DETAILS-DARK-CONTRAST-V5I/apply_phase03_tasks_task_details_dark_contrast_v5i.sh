#!/usr/bin/env bash
set -euo pipefail

echo "RUNNING=V5I_TASK_DETAILS_DARK_CONTRAST"

ROOT="${1:-/var/www/TOS}"
PATCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCH_REPO_ROOT="$(cd "$PATCH_DIR/.." && pwd)"
SOURCE_CSS="$PATCH_DIR/task-details-dark-contrast-v5i.css"

BOARD_TARGET="frontend/src/components/ProfessionalTaskBoard.jsx"
WORKSPACE_TARGET="frontend/src/pages/MyTaskWorkspace.jsx"
CSS_TARGET="frontend/src/styles/tasks-projects-premium-reference.css"

EXPECTED_BOARD_HEAD_BLOB="1dd10123d251767a819fd6f9eb4392fbb5aeffd6"
EXPECTED_WORKSPACE_HEAD_BLOB="7b5e0d1c4d62a439dbdfc3fa056a9a4eea4cbf0e"
V5G_RUNTIME='--tos-my-workspace-dark-select-v5g-runtime'
V5I_RUNTIME='--tos-task-details-dark-contrast-v5i-runtime'
ROOT_HOOK='tos-task-details-modal'

DIST="$ROOT/frontend/dist"
LIVE_PARENT="/opt/apps/tamiyouz-front"
LIVE="$LIVE_PARENT/build"
STAMP="$(date +%Y%m%d-%H%M%S)"
STAGE="$LIVE_PARENT/build.phase03-v5i.new.$$"
BACKUP="$LIVE_PARENT/build.phase03-v5i.backup-$STAMP"

fail() {
  echo "PHASE03_TASKS_TASK_DETAILS_DARK_CONTRAST_V5I=FAIL"
  echo "ERROR=$1" >&2
  exit "${2:-1}"
}

[ -d "$ROOT/.git" ] || fail "TOS repository not found" 2
[ -d "$PATCH_REPO_ROOT/.git" ] || fail "TOS-Patchs repository not found" 3
[ -f "$SOURCE_CSS" ] || fail "V5I CSS source missing" 4
[ -f "$ROOT/$BOARD_TARGET" ] || fail "ProfessionalTaskBoard.jsx missing" 5
[ -f "$ROOT/$WORKSPACE_TARGET" ] || fail "MyTaskWorkspace.jsx missing" 6
[ -f "$ROOT/$CSS_TARGET" ] || fail "Tasks stylesheet missing" 7
[ -d "$LIVE" ] || fail "Live frontend root missing" 8

git -C "$ROOT" diff --cached --quiet || fail "Staged changes exist; stop" 9
[ "$(git -C "$ROOT" rev-parse "HEAD:$BOARD_TARGET")" = "$EXPECTED_BOARD_HEAD_BLOB" ] || fail "Committed ProfessionalTaskBoard baseline changed" 10
[ "$(git -C "$ROOT" rev-parse "HEAD:$WORKSPACE_TARGET")" = "$EXPECTED_WORKSPACE_HEAD_BLOB" ] || fail "Committed MyTaskWorkspace baseline changed" 11

# V5H left exactly MyTaskWorkspace + Tasks stylesheet modified. Preserve that state.
PRE_CHANGED="$(git -C "$ROOT" diff --name-only | sort)"
EXPECTED_PRE="$(printf '%s\n%s\n' "$WORKSPACE_TARGET" "$CSS_TARGET" | sort)"
[ "$PRE_CHANGED" = "$EXPECTED_PRE" ] || {
  echo "--- PRE-EXISTING TRACKED CHANGES ---"
  printf '%s\n' "$PRE_CHANGED"
  fail "Unexpected tracked state before V5I" 12
}

[ "$(git -C "$ROOT" hash-object "$BOARD_TARGET")" = "$EXPECTED_BOARD_HEAD_BLOB" ] || fail "ProfessionalTaskBoard worktree is not clean baseline" 13
[ "$(grep -Fc -- 'tos-my-workspace' "$ROOT/$WORKSPACE_TARGET" || true)" = "1" ] || fail "V5G My Workspace hook missing" 14
[ "$(grep -Fc -- "$V5G_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "V5G runtime missing" 15
[ "$(grep -Fc -- "$V5I_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "0" ] || fail "V5I already present unexpectedly" 16
[ "$(grep -Fc -- "$ROOT_HOOK" "$ROOT/$BOARD_TARGET" || true)" = "0" ] || fail "Task Details V5I hook already present unexpectedly" 17

SOURCE_REL="${SOURCE_CSS#$PATCH_REPO_ROOT/}"
[ "$(git -C "$PATCH_REPO_ROOT" hash-object "$SOURCE_CSS")" = "$(git -C "$PATCH_REPO_ROOT" rev-parse "HEAD:$SOURCE_REL")" ] || fail "V5I CSS source differs from TOS-Patchs HEAD" 18

python3 - "$ROOT/$BOARD_TARGET" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text()
old = 'className="flex h-[100dvh] w-full flex-col overflow-hidden bg-transparent"'
new = 'className="tos-task-details-modal flex h-[100dvh] w-full flex-col overflow-hidden bg-transparent"'
count = text.count(old)
if count != 1:
    raise SystemExit(f"Task Details root anchor count={count}")
path.write_text(text.replace(old, new, 1))
PY

printf '\n' >> "$ROOT/$CSS_TARGET"
cat "$SOURCE_CSS" >> "$ROOT/$CSS_TARGET"

[ "$(grep -Fc -- "$ROOT_HOOK" "$ROOT/$BOARD_TARGET" || true)" = "1" ] || fail "Task Details root hook missing after patch" 19
[ "$(grep -Fc -- "$V5I_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "V5I runtime missing after append" 20
[ "$(grep -Fc -- 'tos-task-rich-editor-content' "$ROOT/$CSS_TARGET" || true)" -ge "1" ] || fail "Rich editor contrast selectors missing" 21

git -C "$ROOT" diff --check -- "$BOARD_TARGET" "$WORKSPACE_TARGET" "$CSS_TARGET"

cd "$ROOT/frontend"
npm run build
cd "$ROOT"

[ -f "$DIST/index.html" ] || fail "Built dist index missing" 22
grep -RFlq -- "$V5I_RUNTIME" "$DIST/assets" || fail "V5I runtime missing from dist assets" 23
grep -RFlq -- "$ROOT_HOOK" "$DIST/assets" || fail "Task Details root hook missing from dist assets" 24
grep -RFlq -- 'tos-task-rich-editor-content' "$DIST/assets" || fail "Rich editor selector missing from dist assets" 25

rm -rf "$STAGE"
mkdir -p "$STAGE"
cp -a "$DIST/." "$STAGE/"
[ -f "$STAGE/index.html" ] || fail "Staged index missing" 26
grep -RFlq -- "$V5I_RUNTIME" "$STAGE/assets" || fail "V5I runtime missing from staged assets" 27

mv "$LIVE" "$BACKUP"
if ! mv "$STAGE" "$LIVE"; then
  mv "$BACKUP" "$LIVE" || true
  fail "Failed to activate V5I live build; rollback attempted" 28
fi
if ! grep -RFlq -- "$V5I_RUNTIME" "$LIVE/assets"; then
  rm -rf "$LIVE"
  mv "$BACKUP" "$LIVE" || true
  fail "Live V5I runtime missing; rolled back" 29
fi

POST_CHANGED="$(git -C "$ROOT" diff --name-only | sort)"
EXPECTED_POST="$(printf '%s\n%s\n%s\n' "$BOARD_TARGET" "$WORKSPACE_TARGET" "$CSS_TARGET" | sort)"
[ "$POST_CHANGED" = "$EXPECTED_POST" ] || {
  echo "--- TRACKED CHANGES ---"
  printf '%s\n' "$POST_CHANGED"
  fail "Unexpected tracked files after V5I" 30
}

git -C "$ROOT" diff --cached --quiet || fail "Unexpected staged changes after V5I" 31

BOARD_SHA="$(sha256sum "$ROOT/$BOARD_TARGET" | awk '{print $1}')"
WORKSPACE_SHA="$(sha256sum "$ROOT/$WORKSPACE_TARGET" | awk '{print $1}')"
CSS_SHA="$(sha256sum "$ROOT/$CSS_TARGET" | awk '{print $1}')"

echo "PHASE03_TASKS_TASK_DETAILS_DARK_CONTRAST_V5I=PASS"
echo "SCREEN=Task_Details"
echo "FIX=Dark_title_and_rich_description_readability"
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
