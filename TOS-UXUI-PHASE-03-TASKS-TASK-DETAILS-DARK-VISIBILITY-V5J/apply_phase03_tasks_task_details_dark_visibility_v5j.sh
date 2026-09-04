#!/usr/bin/env bash
set -euo pipefail

echo "RUNNING=V5J_TASK_DETAILS_DARK_VISIBILITY"

ROOT="${1:-/var/www/TOS}"
PATCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCH_REPO_ROOT="$(cd "$PATCH_DIR/.." && pwd)"
SOURCE_CSS="$PATCH_DIR/task-details-dark-visibility-v5j.css"

BOARD_TARGET="frontend/src/components/ProfessionalTaskBoard.jsx"
WORKSPACE_TARGET="frontend/src/pages/MyTaskWorkspace.jsx"
CSS_TARGET="frontend/src/styles/tasks-projects-premium-reference.css"

EXPECTED_BOARD_SHA256="409c9b776c498a30af87d14f61cbb815b8c5c17f9432bd176f0c5b0e6893aa4b"
EXPECTED_WORKSPACE_SHA256="28e06464e1c0414ffb251bf5f4b1dea7b66b2293e2593d740d5ab53c790e68eb"
EXPECTED_CSS_SHA256="7dbda600a92a0d08f543cce460880ce60aeb3e17052f6dfca9b4ef43e09ccaca"
V5G_RUNTIME='--tos-my-workspace-dark-select-v5g-runtime'
V5I_RUNTIME='--tos-task-details-dark-contrast-v5i-runtime'
V5J_RUNTIME='--tos-task-details-dark-visibility-v5j-runtime'
ROOT_HOOK='tos-task-details-modal'

DIST="$ROOT/frontend/dist"
LIVE_PARENT="/opt/apps/tamiyouz-front"
LIVE="$LIVE_PARENT/build"
STAMP="$(date +%Y%m%d-%H%M%S)"
STAGE="$LIVE_PARENT/build.phase03-v5j.new.$$"
BACKUP="$LIVE_PARENT/build.phase03-v5j.backup-$STAMP"

fail() {
  echo "PHASE03_TASKS_TASK_DETAILS_DARK_VISIBILITY_V5J=FAIL"
  echo "ERROR=$1" >&2
  exit "${2:-1}"
}

[ -d "$ROOT/.git" ] || fail "TOS repository not found" 2
[ -d "$PATCH_REPO_ROOT/.git" ] || fail "TOS-Patchs repository not found" 3
[ -f "$SOURCE_CSS" ] || fail "V5J CSS source missing" 4
[ -f "$ROOT/$BOARD_TARGET" ] || fail "ProfessionalTaskBoard.jsx missing" 5
[ -f "$ROOT/$WORKSPACE_TARGET" ] || fail "MyTaskWorkspace.jsx missing" 6
[ -f "$ROOT/$CSS_TARGET" ] || fail "Tasks stylesheet missing" 7
[ -d "$LIVE" ] || fail "Live frontend root missing" 8

git -C "$ROOT" diff --cached --quiet || fail "Staged changes exist; stop" 9

# Exact V5I reviewed state from the user's successful report.
[ "$(sha256sum "$ROOT/$BOARD_TARGET" | awk '{print $1}')" = "$EXPECTED_BOARD_SHA256" ] || fail "ProfessionalTaskBoard differs from reviewed V5I state" 10
[ "$(sha256sum "$ROOT/$WORKSPACE_TARGET" | awk '{print $1}')" = "$EXPECTED_WORKSPACE_SHA256" ] || fail "MyTaskWorkspace differs from reviewed V5I state" 11
[ "$(sha256sum "$ROOT/$CSS_TARGET" | awk '{print $1}')" = "$EXPECTED_CSS_SHA256" ] || fail "Tasks stylesheet differs from reviewed V5I state" 12

CHANGED_BEFORE="$(git -C "$ROOT" diff --name-only | sort)"
EXPECTED_CHANGED="$(printf '%s\n%s\n%s\n' "$BOARD_TARGET" "$WORKSPACE_TARGET" "$CSS_TARGET" | sort)"
[ "$CHANGED_BEFORE" = "$EXPECTED_CHANGED" ] || {
  echo "--- TRACKED CHANGES BEFORE V5J ---"
  printf '%s\n' "$CHANGED_BEFORE"
  fail "Unexpected tracked state before V5J" 13
}

[ "$(grep -Fc -- "$ROOT_HOOK" "$ROOT/$BOARD_TARGET" || true)" = "1" ] || fail "Task Details root hook missing" 14
[ "$(grep -Fc -- "$V5G_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "V5G runtime missing" 15
[ "$(grep -Fc -- "$V5I_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "V5I runtime missing" 16
[ "$(grep -Fc -- "$V5J_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "0" ] || fail "V5J already present unexpectedly" 17

SOURCE_REL="${SOURCE_CSS#$PATCH_REPO_ROOT/}"
[ "$(git -C "$PATCH_REPO_ROOT" hash-object "$SOURCE_CSS")" = "$(git -C "$PATCH_REPO_ROOT" rev-parse "HEAD:$SOURCE_REL")" ] || fail "V5J CSS source differs from TOS-Patchs HEAD" 18

printf '\n' >> "$ROOT/$CSS_TARGET"
cat "$SOURCE_CSS" >> "$ROOT/$CSS_TARGET"

[ "$(grep -Fc -- "$V5J_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "V5J runtime missing after append" 19
git -C "$ROOT" diff --check -- "$BOARD_TARGET" "$WORKSPACE_TARGET" "$CSS_TARGET"

cd "$ROOT/frontend"
npm run build
cd "$ROOT"

[ -f "$DIST/index.html" ] || fail "Built dist index missing" 20
grep -RFlq -- "$V5J_RUNTIME" "$DIST/assets" || fail "V5J runtime missing from dist assets" 21
grep -RFlq -- "$ROOT_HOOK" "$DIST/assets" || fail "Task Details root hook missing from dist assets" 22

rm -rf "$STAGE"
mkdir -p "$STAGE"
cp -a "$DIST/." "$STAGE/"
[ -f "$STAGE/index.html" ] || fail "Staged index missing" 23
grep -RFlq -- "$V5J_RUNTIME" "$STAGE/assets" || fail "V5J runtime missing from staged assets" 24

mv "$LIVE" "$BACKUP"
if ! mv "$STAGE" "$LIVE"; then
  mv "$BACKUP" "$LIVE" || true
  fail "Failed to activate V5J live build; rollback attempted" 25
fi
if ! grep -RFlq -- "$V5J_RUNTIME" "$LIVE/assets"; then
  rm -rf "$LIVE"
  mv "$BACKUP" "$LIVE" || true
  fail "Live V5J runtime missing; rolled back" 26
fi

CHANGED_AFTER="$(git -C "$ROOT" diff --name-only | sort)"
[ "$CHANGED_AFTER" = "$EXPECTED_CHANGED" ] || {
  echo "--- TRACKED CHANGES AFTER V5J ---"
  printf '%s\n' "$CHANGED_AFTER"
  fail "Unexpected tracked files after V5J" 27
}

git -C "$ROOT" diff --cached --quiet || fail "Unexpected staged changes after V5J" 28

BOARD_SHA="$(sha256sum "$ROOT/$BOARD_TARGET" | awk '{print $1}')"
WORKSPACE_SHA="$(sha256sum "$ROOT/$WORKSPACE_TARGET" | awk '{print $1}')"
CSS_SHA="$(sha256sum "$ROOT/$CSS_TARGET" | awk '{print $1}')"

echo "PHASE03_TASKS_TASK_DETAILS_DARK_VISIBILITY_V5J=PASS"
echo "SCREEN=Task_Details"
echo "FIX=Dark_native_controls_secondary_copy_and_save_cta_visibility"
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
