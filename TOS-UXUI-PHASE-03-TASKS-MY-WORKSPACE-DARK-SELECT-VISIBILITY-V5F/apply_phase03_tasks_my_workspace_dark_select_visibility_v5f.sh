#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/var/www/TOS}"
PATCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCH_REPO_ROOT="$(cd "$PATCH_DIR/.." && pwd)"
SOURCE_CSS="$PATCH_DIR/my-workspace-dark-select-visibility-v5f.css"

WORKSPACE_TARGET="frontend/src/pages/MyTaskWorkspace.jsx"
CSS_TARGET="frontend/src/styles/tasks-projects-premium-reference.css"
BOARD_TARGET="frontend/src/components/ProfessionalTaskBoard.jsx"
EXPECTED_WORKSPACE_HEAD_BLOB="7b5e0d1c4d62a439dbdfc3fa056a9a4eea4cbf0e"
ROOT_HOOK="tos-my-workspace"
V5_RUNTIME='--tos-tasks-flagship-v5-runtime'
V5D_RUNTIME='--tos-tasks-flagship-v5d-runtime'
V5F_RUNTIME='--tos-my-workspace-dark-select-v5f-runtime'

DIST="$ROOT/frontend/dist"
LIVE_PARENT="/opt/apps/tamiyouz-front"
LIVE="$LIVE_PARENT/build"
STAMP="$(date +%Y%m%d-%H%M%S)"
STAGE="$LIVE_PARENT/build.phase03-v5f.new.$$"
BACKUP="$LIVE_PARENT/build.phase03-v5f.backup-$STAMP"

fail() {
  echo "PHASE03_TASKS_MY_WORKSPACE_DARK_SELECT_VISIBILITY_V5F=FAIL"
  echo "ERROR=$1" >&2
  exit "${2:-1}"
}

[ -d "$ROOT/.git" ] || fail "TOS repository not found" 2
[ -d "$PATCH_REPO_ROOT/.git" ] || fail "TOS-Patchs repository not found" 3
[ -f "$SOURCE_CSS" ] || fail "V5F CSS source missing" 4
[ -f "$ROOT/$WORKSPACE_TARGET" ] || fail "MyTaskWorkspace.jsx missing" 5
[ -f "$ROOT/$CSS_TARGET" ] || fail "Tasks premium stylesheet missing" 6
[ -f "$ROOT/$BOARD_TARGET" ] || fail "ProfessionalTaskBoard.jsx missing" 7
[ -d "$LIVE" ] || fail "Live frontend root missing" 8

git -C "$ROOT" diff --cached --quiet || fail "Staged changes exist; stop" 9
[ "$(git -C "$ROOT" rev-parse "HEAD:$WORKSPACE_TARGET")" = "$EXPECTED_WORKSPACE_HEAD_BLOB" ] || fail "Committed MyTaskWorkspace baseline changed" 10

# V5D is the reviewed live baseline. Do not require a brittle full-file SHA;
# require its exact runtime markers and semantic board hooks instead.
[ "$(grep -Fc -- "$V5_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "V5 flagship runtime missing" 11
[ "$(grep -Fc -- "$V5D_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "V5D runtime missing" 12
[ "$(grep -Fc -- 'tos-task-kpi-deck' "$ROOT/$BOARD_TARGET" || true)" = "1" ] || fail "V5D KPI hook missing" 13
[ "$(grep -Fc -- 'tos-task-kanban-shell' "$ROOT/$BOARD_TARGET" || true)" = "1" ] || fail "V5D Kanban shell hook missing" 14
[ "$(grep -Fc -- 'tos-task-kanban-hero' "$ROOT/$BOARD_TARGET" || true)" = "1" ] || fail "V5D Kanban hero hook missing" 15

# Allow only the reviewed V5D tracked changes before V5F.
PRE_DIRTY="$(git -C "$ROOT" diff --name-only | sort)"
while IFS= read -r path; do
  [ -z "$path" ] && continue
  case "$path" in
    "$BOARD_TARGET"|"$CSS_TARGET") ;;
    *) fail "Unexpected pre-existing tracked change: $path" 16 ;;
  esac
done <<< "$PRE_DIRTY"

SOURCE_REL="${SOURCE_CSS#$PATCH_REPO_ROOT/}"
[ "$(git -C "$PATCH_REPO_ROOT" hash-object "$SOURCE_CSS")" = "$(git -C "$PATCH_REPO_ROOT" rev-parse "HEAD:$SOURCE_REL")" ] || fail "V5F CSS source differs from TOS-Patchs HEAD" 17

ROOT_COUNT="$(grep -Fc -- "$ROOT_HOOK" "$ROOT/$WORKSPACE_TARGET" || true)"
V5F_COUNT="$(grep -Fc -- "$V5F_RUNTIME" "$ROOT/$CSS_TARGET" || true)"

if [ "$ROOT_COUNT" = "0" ] && [ "$V5F_COUNT" = "0" ]; then
  [ "$(git -C "$ROOT" hash-object "$WORKSPACE_TARGET")" = "$EXPECTED_WORKSPACE_HEAD_BLOB" ] || fail "MyTaskWorkspace worktree differs from reviewed baseline" 18

  python3 - "$ROOT/$WORKSPACE_TARGET" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text()
old = '<div className="mx-auto w-full max-w-[1580px]" dir={isAr ? "rtl" : "ltr"}>'
new = '<div className="tos-my-workspace mx-auto w-full max-w-[1580px]" dir={isAr ? "rtl" : "ltr"}>'
count = text.count(old)
if count != 1:
    raise SystemExit(f"My Workspace root anchor count={count}")
text = text.replace(old, new, 1)
path.write_text(text)
PY

  printf '\n' >> "$ROOT/$CSS_TARGET"
  cat "$SOURCE_CSS" >> "$ROOT/$CSS_TARGET"
  PATCH_ACTION="APPLIED"
elif [ "$ROOT_COUNT" = "1" ] && [ "$V5F_COUNT" = "1" ]; then
  PATCH_ACTION="VALIDATED_EXISTING"
else
  fail "Partial V5F state detected" 19
fi

[ "$(grep -Fc -- "$ROOT_HOOK" "$ROOT/$WORKSPACE_TARGET" || true)" = "1" ] || fail "My Workspace semantic hook missing or duplicated" 20
[ "$(grep -Fc -- "$V5F_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "V5F runtime missing or duplicated" 21

git -C "$ROOT" diff --check -- "$WORKSPACE_TARGET" "$CSS_TARGET"

cd "$ROOT/frontend"
npm run build
cd "$ROOT"

[ -f "$DIST/index.html" ] || fail "Built dist index missing" 22
grep -RFlq -- "$V5F_RUNTIME" "$DIST/assets" || fail "V5F runtime missing from dist assets" 23
grep -RFlq -- "$ROOT_HOOK" "$DIST/assets" || fail "My Workspace semantic hook missing from dist assets" 24
if ! grep -RFlq -- 'color-scheme:dark' "$DIST/assets" && ! grep -RFlq -- 'color-scheme: dark' "$DIST/assets"; then
  fail "Dark native select color-scheme missing from dist assets" 25
fi

rm -rf "$STAGE"
mkdir -p "$STAGE"
cp -a "$DIST/." "$STAGE/"
[ -f "$STAGE/index.html" ] || fail "Staged index missing" 26
grep -RFlq -- "$V5F_RUNTIME" "$STAGE/assets" || fail "V5F runtime missing from staged assets" 27

mv "$LIVE" "$BACKUP"
if ! mv "$STAGE" "$LIVE"; then
  mv "$BACKUP" "$LIVE" || true
  fail "Failed to activate V5F build; rollback attempted" 28
fi
if ! grep -RFlq -- "$V5F_RUNTIME" "$LIVE/assets"; then
  rm -rf "$LIVE"
  mv "$BACKUP" "$LIVE" || true
  fail "Live V5F runtime missing; rolled back" 29
fi

TRACKED_CHANGED="$(git -C "$ROOT" diff --name-only | sort)"
while IFS= read -r path; do
  [ -z "$path" ] && continue
  case "$path" in
    "$BOARD_TARGET"|"$CSS_TARGET"|"$WORKSPACE_TARGET") ;;
    *) fail "Unexpected tracked file after V5F: $path" 30 ;;
  esac
done <<< "$TRACKED_CHANGED"

git -C "$ROOT" diff --cached --quiet || fail "Unexpected staged changes after patch" 31

WORKSPACE_SHA="$(sha256sum "$ROOT/$WORKSPACE_TARGET" | awk '{print $1}')"
CSS_SHA="$(sha256sum "$ROOT/$CSS_TARGET" | awk '{print $1}')"
echo "PHASE03_TASKS_MY_WORKSPACE_DARK_SELECT_VISIBILITY_V5F=PASS"
echo "SCREEN=My_Workspace"
echo "FIX=Dark_native_select_popup_visibility"
echo "PATCH_ACTION=$PATCH_ACTION"
echo "SELECT_SCOPE=All_My_Workspace_native_selects"
echo "LIGHT_MODE_CHANGED=NO"
echo "BUSINESS_LOGIC_CHANGED=NO"
echo "BUILD_RESULT=PASS"
echo "LIVE_DEPLOY=PASS"
echo "MY_WORKSPACE_SHA256=$WORKSPACE_SHA"
echo "TASKS_CSS_SHA256=$CSS_SHA"
echo "NO_COMMIT_OR_PUSH=YES"
echo "--- GIT STATUS ---"
git -C "$ROOT" status --short
