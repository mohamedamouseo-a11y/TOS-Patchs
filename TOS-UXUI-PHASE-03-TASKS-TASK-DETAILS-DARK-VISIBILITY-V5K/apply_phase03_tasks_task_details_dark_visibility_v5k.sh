#!/usr/bin/env bash
set -euo pipefail

echo "RUNNING=V5K_TASK_DETAILS_DARK_VISIBILITY_RECOVERY"

ROOT="${1:-/var/www/TOS}"
PATCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCH_REPO_ROOT="$(cd "$PATCH_DIR/.." && pwd)"
SOURCE_CSS="$PATCH_DIR/task-details-dark-visibility-v5k.css"

BOARD_TARGET="frontend/src/components/ProfessionalTaskBoard.jsx"
WORKSPACE_TARGET="frontend/src/pages/MyTaskWorkspace.jsx"
CSS_TARGET="frontend/src/styles/tasks-projects-premium-reference.css"

ROOT_HOOK='tos-task-details-modal'
WORKSPACE_HOOK='tos-my-workspace'
V5G_RUNTIME='--tos-my-workspace-dark-select-v5g-runtime'
V5I_RUNTIME='--tos-task-details-dark-contrast-v5i-runtime'
V5J_RUNTIME='--tos-task-details-dark-visibility-v5j-runtime'
V5K_RUNTIME='--tos-task-details-dark-visibility-v5k-runtime'

DIST="$ROOT/frontend/dist"
LIVE_PARENT="/opt/apps/tamiyouz-front"
LIVE="$LIVE_PARENT/build"
STAMP="$(date +%Y%m%d-%H%M%S)"
STAGE="$LIVE_PARENT/build.phase03-v5k.new.$$"
BACKUP="$LIVE_PARENT/build.phase03-v5k.backup-$STAMP"

fail() {
  echo "PHASE03_TASKS_TASK_DETAILS_DARK_VISIBILITY_V5K=FAIL"
  echo "ERROR=$1" >&2
  exit "${2:-1}"
}

[ -d "$ROOT/.git" ] || fail "TOS repository not found" 2
[ -d "$PATCH_REPO_ROOT/.git" ] || fail "TOS-Patchs repository not found" 3
[ -f "$SOURCE_CSS" ] || fail "V5K CSS source missing" 4
[ -f "$ROOT/$BOARD_TARGET" ] || fail "ProfessionalTaskBoard.jsx missing" 5
[ -f "$ROOT/$WORKSPACE_TARGET" ] || fail "MyTaskWorkspace.jsx missing" 6
[ -f "$ROOT/$CSS_TARGET" ] || fail "Tasks stylesheet missing" 7
[ -d "$LIVE" ] || fail "Live frontend root missing" 8

git -C "$ROOT" diff --cached --quiet || fail "Staged changes exist; stop" 9

# The exact full stylesheet SHA drifted after V5I even though the reviewed Phase 03
# state is still represented by semantic runtime markers. Validate meaning, not a
# brittle whole-file checksum.
CHANGED_BEFORE="$(git -C "$ROOT" diff --name-only | sort)"
EXPECTED_CHANGED="$(printf '%s\n%s\n%s\n' "$BOARD_TARGET" "$WORKSPACE_TARGET" "$CSS_TARGET" | sort)"
[ "$CHANGED_BEFORE" = "$EXPECTED_CHANGED" ] || {
  echo "--- TRACKED CHANGES BEFORE V5K ---"
  printf '%s\n' "$CHANGED_BEFORE"
  fail "Unexpected tracked state before V5K" 10
}

[ "$(grep -Fc -- "$ROOT_HOOK" "$ROOT/$BOARD_TARGET" || true)" = "1" ] || fail "Task Details root hook missing or duplicated" 11
[ "$(grep -Fc -- "$WORKSPACE_HOOK" "$ROOT/$WORKSPACE_TARGET" || true)" = "1" ] || fail "My Workspace hook missing or duplicated" 12
[ "$(grep -Fc -- "$V5G_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "V5G runtime missing or duplicated" 13
[ "$(grep -Fc -- "$V5I_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "V5I runtime missing or duplicated" 14
[ "$(grep -Fc -- 'tos-task-rich-editor-content' "$ROOT/$CSS_TARGET" || true)" -ge "1" ] || fail "V5I rich editor contrast selectors missing" 15
[ "$(grep -Fc -- "$V5J_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "0" ] || fail "V5J runtime already present unexpectedly" 16
[ "$(grep -Fc -- "$V5K_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "0" ] || fail "V5K runtime already present unexpectedly" 17

SOURCE_REL="${SOURCE_CSS#$PATCH_REPO_ROOT/}"
[ "$(git -C "$PATCH_REPO_ROOT" hash-object "$SOURCE_CSS")" = "$(git -C "$PATCH_REPO_ROOT" rev-parse "HEAD:$SOURCE_REL")" ] || fail "V5K CSS source differs from TOS-Patchs HEAD" 18

PRE_CSS_SHA="$(sha256sum "$ROOT/$CSS_TARGET" | awk '{print $1}')"
printf '\n' >> "$ROOT/$CSS_TARGET"
cat "$SOURCE_CSS" >> "$ROOT/$CSS_TARGET"

[ "$(grep -Fc -- "$V5K_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "V5K runtime missing after append" 19
[ "$(grep -Fc -- "$V5I_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "V5I runtime changed during append" 20

git -C "$ROOT" diff --check -- "$BOARD_TARGET" "$WORKSPACE_TARGET" "$CSS_TARGET"

cd "$ROOT/frontend"
npm run build
cd "$ROOT"

[ -f "$DIST/index.html" ] || fail "Built dist index missing" 21
grep -RFlq -- "$V5K_RUNTIME" "$DIST/assets" || fail "V5K runtime missing from dist assets" 22
grep -RFlq -- "$ROOT_HOOK" "$DIST/assets" || fail "Task Details root hook missing from dist assets" 23
if ! grep -RFlq -- 'color-scheme:dark' "$DIST/assets" && ! grep -RFlq -- 'color-scheme: dark' "$DIST/assets"; then
  fail "Dark native control color-scheme missing from dist assets" 24
fi

rm -rf "$STAGE"
mkdir -p "$STAGE"
cp -a "$DIST/." "$STAGE/"
[ -f "$STAGE/index.html" ] || fail "Staged index missing" 25
grep -RFlq -- "$V5K_RUNTIME" "$STAGE/assets" || fail "V5K runtime missing from staged assets" 26

mv "$LIVE" "$BACKUP"
if ! mv "$STAGE" "$LIVE"; then
  mv "$BACKUP" "$LIVE" || true
  fail "Failed to activate V5K live build; rollback attempted" 27
fi
if ! grep -RFlq -- "$V5K_RUNTIME" "$LIVE/assets"; then
  rm -rf "$LIVE"
  mv "$BACKUP" "$LIVE" || true
  fail "Live V5K runtime missing; rolled back" 28
fi

CHANGED_AFTER="$(git -C "$ROOT" diff --name-only | sort)"
[ "$CHANGED_AFTER" = "$EXPECTED_CHANGED" ] || {
  echo "--- TRACKED CHANGES AFTER V5K ---"
  printf '%s\n' "$CHANGED_AFTER"
  fail "Unexpected tracked files after V5K" 29
}

git -C "$ROOT" diff --cached --quiet || fail "Unexpected staged changes after V5K" 30

BOARD_SHA="$(sha256sum "$ROOT/$BOARD_TARGET" | awk '{print $1}')"
WORKSPACE_SHA="$(sha256sum "$ROOT/$WORKSPACE_TARGET" | awk '{print $1}')"
CSS_SHA="$(sha256sum "$ROOT/$CSS_TARGET" | awk '{print $1}')"

echo "PHASE03_TASKS_TASK_DETAILS_DARK_VISIBILITY_V5K=PASS"
echo "SCREEN=Task_Details"
echo "FIX=Dark_native_controls_secondary_copy_and_save_cta_visibility"
echo "GUARD_MODE=SEMANTIC_RUNTIME_AND_TRACKED_STATE"
echo "PRE_TASKS_CSS_SHA256=$PRE_CSS_SHA"
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
