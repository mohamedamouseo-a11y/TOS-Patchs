#!/usr/bin/env bash
set -euo pipefail

echo "RUNNING=V5H_FINALIZER"

ROOT="${1:-/var/www/TOS}"
WORKSPACE_TARGET="frontend/src/pages/MyTaskWorkspace.jsx"
CSS_TARGET="frontend/src/styles/tasks-projects-premium-reference.css"
BOARD_TARGET="frontend/src/components/ProfessionalTaskBoard.jsx"
ROOT_HOOK="tos-my-workspace"
V5_RUNTIME='--tos-tasks-flagship-v5-runtime'
V5D_RUNTIME='--tos-tasks-flagship-v5d-runtime'
V5G_RUNTIME='--tos-my-workspace-dark-select-v5g-runtime'

DIST="$ROOT/frontend/dist"
LIVE_PARENT="/opt/apps/tamiyouz-front"
LIVE="$LIVE_PARENT/build"
STAMP="$(date +%Y%m%d-%H%M%S)"
STAGE="$LIVE_PARENT/build.phase03-v5h.new.$$"
BACKUP="$LIVE_PARENT/build.phase03-v5h.backup-$STAMP"

fail() {
  echo "PHASE03_TASKS_MY_WORKSPACE_DARK_SELECT_VISIBILITY_V5H=FAIL"
  echo "ERROR=$1" >&2
  exit "${2:-1}"
}

[ -d "$ROOT/.git" ] || fail "TOS repository not found" 2
[ -f "$ROOT/$WORKSPACE_TARGET" ] || fail "MyTaskWorkspace.jsx missing" 3
[ -f "$ROOT/$CSS_TARGET" ] || fail "Tasks premium stylesheet missing" 4
[ -f "$ROOT/$BOARD_TARGET" ] || fail "ProfessionalTaskBoard.jsx missing" 5
[ -d "$LIVE" ] || fail "Live frontend root missing" 6

git -C "$ROOT" diff --cached --quiet || fail "Staged changes exist; stop" 7

# V5G must already be present exactly once. This script is a finalizer, not another applier.
[ "$(grep -Fc -- "$ROOT_HOOK" "$ROOT/$WORKSPACE_TARGET" || true)" = "1" ] || fail "My Workspace V5G root hook missing or duplicated" 8
[ "$(grep -Fc -- "$V5_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "V5 flagship runtime missing" 9
[ "$(grep -Fc -- "$V5D_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "V5D runtime missing" 10
[ "$(grep -Fc -- "$V5G_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "V5G runtime missing or duplicated" 11

# Require the actual dark-select visibility rules that were reviewed for Windows/Chrome native menus.
grep -Fq 'html.dark .tos-my-workspace select {' "$ROOT/$CSS_TARGET" || fail "V5G select rule missing" 12
grep -Fq 'color-scheme: dark !important;' "$ROOT/$CSS_TARGET" || fail "Dark color-scheme rule missing" 13
grep -Fq 'html.dark .tos-my-workspace select option,' "$ROOT/$CSS_TARGET" || fail "Dark option rule missing" 14
grep -Fq 'background-color: #171b20 !important;' "$ROOT/$CSS_TARGET" || fail "Dark option background rule missing" 15

# Flagship board semantics may be committed already or still modified; presence is what matters.
[ "$(grep -Fc -- 'tos-task-kpi-deck' "$ROOT/$BOARD_TARGET" || true)" = "1" ] || fail "V5D KPI hook missing" 16
[ "$(grep -Fc -- 'tos-task-kanban-shell' "$ROOT/$BOARD_TARGET" || true)" = "1" ] || fail "V5D Kanban shell hook missing" 17
[ "$(grep -Fc -- 'tos-task-kanban-hero' "$ROOT/$BOARD_TARGET" || true)" = "1" ] || fail "V5D Kanban hero hook missing" 18

TRACKED_CHANGED="$(git -C "$ROOT" diff --name-only | sort)"
# My Workspace + Tasks CSS must be modified from HEAD. Board is optional because its V5D hooks may already exist in HEAD.
printf '%s\n' "$TRACKED_CHANGED" | grep -Fxq "$WORKSPACE_TARGET" || fail "MyTaskWorkspace.jsx is not modified as expected" 19
printf '%s\n' "$TRACKED_CHANGED" | grep -Fxq "$CSS_TARGET" || fail "Tasks premium stylesheet is not modified as expected" 20
while IFS= read -r path; do
  [ -z "$path" ] && continue
  case "$path" in
    "$WORKSPACE_TARGET"|"$CSS_TARGET"|"$BOARD_TARGET") ;;
    *) fail "Unexpected tracked file after V5G: $path" 21 ;;
  esac
done <<< "$TRACKED_CHANGED"

git -C "$ROOT" diff --check -- "$WORKSPACE_TARGET" "$CSS_TARGET" "$BOARD_TARGET"

cd "$ROOT/frontend"
npm run build
cd "$ROOT"

[ -f "$DIST/index.html" ] || fail "Built dist index missing" 22
grep -RFlq -- "$V5G_RUNTIME" "$DIST/assets" || fail "V5G runtime missing from dist assets" 23
grep -RFlq -- "$ROOT_HOOK" "$DIST/assets" || fail "My Workspace hook missing from dist assets" 24
if ! grep -RFlq -- 'color-scheme:dark' "$DIST/assets" && ! grep -RFlq -- 'color-scheme: dark' "$DIST/assets"; then
  fail "Dark native select color-scheme missing from dist assets" 25
fi

rm -rf "$STAGE"
mkdir -p "$STAGE"
cp -a "$DIST/." "$STAGE/"
[ -f "$STAGE/index.html" ] || fail "Staged index missing" 26
grep -RFlq -- "$V5G_RUNTIME" "$STAGE/assets" || fail "V5G runtime missing from staged assets" 27

mv "$LIVE" "$BACKUP"
if ! mv "$STAGE" "$LIVE"; then
  mv "$BACKUP" "$LIVE" || true
  fail "Failed to activate V5H live build; rollback attempted" 28
fi
if ! grep -RFlq -- "$V5G_RUNTIME" "$LIVE/assets"; then
  rm -rf "$LIVE"
  mv "$BACKUP" "$LIVE" || true
  fail "Live V5G runtime missing; rolled back" 29
fi

FINAL_CHANGED="$(git -C "$ROOT" diff --name-only | sort)"
[ "$FINAL_CHANGED" = "$TRACKED_CHANGED" ] || fail "Tracked file set changed during V5H finalization" 30
git -C "$ROOT" diff --cached --quiet || fail "Unexpected staged changes after V5H" 31

WORKSPACE_SHA="$(sha256sum "$ROOT/$WORKSPACE_TARGET" | awk '{print $1}')"
CSS_SHA="$(sha256sum "$ROOT/$CSS_TARGET" | awk '{print $1}')"
BOARD_SHA="$(sha256sum "$ROOT/$BOARD_TARGET" | awk '{print $1}')"

echo "PHASE03_TASKS_MY_WORKSPACE_DARK_SELECT_VISIBILITY_V5H=PASS"
echo "SCREEN=My_Workspace"
echo "FIX=Dark_native_select_popup_visibility"
echo "RECOVERY=V5G_POST_DEPLOY_FINALIZER"
echo "BOARD_FILE_DIRTY_OPTIONAL=YES"
echo "BUSINESS_LOGIC_CHANGED=NO"
echo "BUILD_RESULT=PASS"
echo "LIVE_DEPLOY=PASS"
echo "MY_WORKSPACE_SHA256=$WORKSPACE_SHA"
echo "TASKS_CSS_SHA256=$CSS_SHA"
echo "BOARD_SHA256=$BOARD_SHA"
echo "NO_COMMIT_OR_PUSH=YES"
echo "--- GIT STATUS ---"
git -C "$ROOT" status --short
