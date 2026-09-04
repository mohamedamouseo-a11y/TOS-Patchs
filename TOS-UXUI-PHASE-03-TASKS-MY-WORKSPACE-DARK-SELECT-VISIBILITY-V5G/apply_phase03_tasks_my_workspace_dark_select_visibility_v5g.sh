#!/usr/bin/env bash
set -euo pipefail

echo "RUNNING=V5G_CONSOLIDATED"

ROOT="${1:-/var/www/TOS}"
PATCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCH_REPO_ROOT="$(cd "$PATCH_DIR/.." && pwd)"
V5D_SCRIPT="$PATCH_REPO_ROOT/TOS-UXUI-PHASE-03-TASKS-FLAGSHIP-SIGNATURE-V5D/apply_phase03_tasks_flagship_signature_v5d.sh"
SOURCE_CSS="$PATCH_DIR/my-workspace-dark-select-visibility-v5g.css"

WORKSPACE_TARGET="frontend/src/pages/MyTaskWorkspace.jsx"
CSS_TARGET="frontend/src/styles/tasks-projects-premium-reference.css"
BOARD_TARGET="frontend/src/components/ProfessionalTaskBoard.jsx"
EXPECTED_WORKSPACE_HEAD_BLOB="7b5e0d1c4d62a439dbdfc3fa056a9a4eea4cbf0e"
ROOT_HOOK="tos-my-workspace"
V5_RUNTIME='--tos-tasks-flagship-v5-runtime'
V5D_RUNTIME='--tos-tasks-flagship-v5d-runtime'
V5G_RUNTIME='--tos-my-workspace-dark-select-v5g-runtime'

DIST="$ROOT/frontend/dist"
LIVE_PARENT="/opt/apps/tamiyouz-front"
LIVE="$LIVE_PARENT/build"
STAMP="$(date +%Y%m%d-%H%M%S)"
STAGE="$LIVE_PARENT/build.phase03-v5g.new.$$"
BACKUP="$LIVE_PARENT/build.phase03-v5g.backup-$STAMP"

fail() {
  echo "PHASE03_TASKS_MY_WORKSPACE_DARK_SELECT_VISIBILITY_V5G=FAIL"
  echo "ERROR=$1" >&2
  exit "${2:-1}"
}

[ -d "$ROOT/.git" ] || fail "TOS repository not found" 2
[ -d "$PATCH_REPO_ROOT/.git" ] || fail "TOS-Patchs repository not found" 3
[ -f "$V5D_SCRIPT" ] || fail "V5D script missing" 4
[ -f "$SOURCE_CSS" ] || fail "V5G CSS source missing" 5
[ -f "$ROOT/$WORKSPACE_TARGET" ] || fail "MyTaskWorkspace.jsx missing" 6
[ -f "$ROOT/$CSS_TARGET" ] || fail "Tasks premium stylesheet missing" 7
[ -f "$ROOT/$BOARD_TARGET" ] || fail "ProfessionalTaskBoard.jsx missing" 8
[ -d "$LIVE" ] || fail "Live frontend root missing" 9

git -C "$ROOT" diff --cached --quiet || fail "Staged changes exist; stop" 10
[ "$(git -C "$ROOT" rev-parse "HEAD:$WORKSPACE_TARGET")" = "$EXPECTED_WORKSPACE_HEAD_BLOB" ] || fail "Committed MyTaskWorkspace baseline changed" 11

# Restore the reviewed V5D source state if the previous runner/session left TOS clean.
V5D_COUNT="$(grep -Fc -- "$V5D_RUNTIME" "$ROOT/$CSS_TARGET" || true)"
if [ "$V5D_COUNT" = "0" ]; then
  PRE_TRACKED="$(git -C "$ROOT" diff --name-only | sed '/^$/d')"
  [ -z "$PRE_TRACKED" ] || fail "V5D missing but tracked working tree is not clean" 12
  echo "V5D_STATE=ABSENT_REAPPLYING"
  bash "$V5D_SCRIPT" "$ROOT"
elif [ "$V5D_COUNT" = "1" ]; then
  echo "V5D_STATE=PRESENT"
else
  fail "Duplicate V5D runtime sentinel" 13
fi

[ "$(grep -Fc -- "$V5_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "V5 flagship runtime missing after V5D normalization" 14
[ "$(grep -Fc -- "$V5D_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "V5D runtime missing after normalization" 15
[ "$(grep -Fc -- 'tos-task-kpi-deck' "$ROOT/$BOARD_TARGET" || true)" = "1" ] || fail "V5D KPI hook missing" 16
[ "$(grep -Fc -- 'tos-task-kanban-shell' "$ROOT/$BOARD_TARGET" || true)" = "1" ] || fail "V5D Kanban shell hook missing" 17
[ "$(grep -Fc -- 'tos-task-kanban-hero' "$ROOT/$BOARD_TARGET" || true)" = "1" ] || fail "V5D Kanban hero hook missing" 18

# Only reviewed V5D tracked changes may exist before the My Workspace fix.
PRE_DIRTY="$(git -C "$ROOT" diff --name-only | sort)"
while IFS= read -r path; do
  [ -z "$path" ] && continue
  case "$path" in
    "$BOARD_TARGET"|"$CSS_TARGET") ;;
    *) fail "Unexpected tracked change before V5G: $path" 19 ;;
  esac
done <<< "$PRE_DIRTY"

SOURCE_REL="${SOURCE_CSS#$PATCH_REPO_ROOT/}"
[ "$(git -C "$PATCH_REPO_ROOT" hash-object "$SOURCE_CSS")" = "$(git -C "$PATCH_REPO_ROOT" rev-parse "HEAD:$SOURCE_REL")" ] || fail "V5G CSS source differs from TOS-Patchs HEAD" 20

ROOT_COUNT="$(grep -Fc -- "$ROOT_HOOK" "$ROOT/$WORKSPACE_TARGET" || true)"
V5G_COUNT="$(grep -Fc -- "$V5G_RUNTIME" "$ROOT/$CSS_TARGET" || true)"

if [ "$ROOT_COUNT" = "0" ]; then
  [ "$(git -C "$ROOT" hash-object "$WORKSPACE_TARGET")" = "$EXPECTED_WORKSPACE_HEAD_BLOB" ] || fail "MyTaskWorkspace worktree differs from reviewed baseline" 21
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
path.write_text(text.replace(old, new, 1))
PY
elif [ "$ROOT_COUNT" != "1" ]; then
  fail "My Workspace root hook duplicated" 22
fi

if [ "$V5G_COUNT" = "0" ]; then
  printf '\n' >> "$ROOT/$CSS_TARGET"
  cat "$SOURCE_CSS" >> "$ROOT/$CSS_TARGET"
elif [ "$V5G_COUNT" != "1" ]; then
  fail "V5G runtime duplicated" 23
fi

[ "$(grep -Fc -- "$ROOT_HOOK" "$ROOT/$WORKSPACE_TARGET" || true)" = "1" ] || fail "My Workspace root hook missing" 24
[ "$(grep -Fc -- "$V5G_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "V5G runtime missing" 25

git -C "$ROOT" diff --check -- "$WORKSPACE_TARGET" "$CSS_TARGET" "$BOARD_TARGET"

cd "$ROOT/frontend"
npm run build
cd "$ROOT"

[ -f "$DIST/index.html" ] || fail "Built dist index missing" 26
grep -RFlq -- "$V5G_RUNTIME" "$DIST/assets" || fail "V5G runtime missing from dist assets" 27
grep -RFlq -- "$ROOT_HOOK" "$DIST/assets" || fail "My Workspace hook missing from dist assets" 28
if ! grep -RFlq -- 'color-scheme:dark' "$DIST/assets" && ! grep -RFlq -- 'color-scheme: dark' "$DIST/assets"; then
  fail "Dark native select color-scheme missing from dist assets" 29
fi

rm -rf "$STAGE"
mkdir -p "$STAGE"
cp -a "$DIST/." "$STAGE/"
[ -f "$STAGE/index.html" ] || fail "Staged index missing" 30
grep -RFlq -- "$V5G_RUNTIME" "$STAGE/assets" || fail "V5G runtime missing from staged assets" 31

mv "$LIVE" "$BACKUP"
if ! mv "$STAGE" "$LIVE"; then
  mv "$BACKUP" "$LIVE" || true
  fail "Failed to activate V5G build; rollback attempted" 32
fi
if ! grep -RFlq -- "$V5G_RUNTIME" "$LIVE/assets"; then
  rm -rf "$LIVE"
  mv "$BACKUP" "$LIVE" || true
  fail "Live V5G runtime missing; rolled back" 33
fi

TRACKED_CHANGED="$(git -C "$ROOT" diff --name-only | sort)"
EXPECTED_CHANGED="$(printf '%s\n%s\n%s\n' "$BOARD_TARGET" "$CSS_TARGET" "$WORKSPACE_TARGET" | sort)"
[ "$TRACKED_CHANGED" = "$EXPECTED_CHANGED" ] || {
  echo "--- TRACKED CHANGES ---"
  printf '%s\n' "$TRACKED_CHANGED"
  fail "Unexpected tracked files after V5G" 34
}

git -C "$ROOT" diff --cached --quiet || fail "Unexpected staged changes after V5G" 35

WORKSPACE_SHA="$(sha256sum "$ROOT/$WORKSPACE_TARGET" | awk '{print $1}')"
CSS_SHA="$(sha256sum "$ROOT/$CSS_TARGET" | awk '{print $1}')"
echo "PHASE03_TASKS_MY_WORKSPACE_DARK_SELECT_VISIBILITY_V5G=PASS"
echo "SCREEN=My_Workspace"
echo "FIX=Dark_native_select_popup_visibility"
echo "SELECT_SCOPE=All_native_selects_under_My_Workspace"
echo "V5D_BASELINE=NORMALIZED"
echo "LIGHT_MODE_CHANGED=NO"
echo "BUSINESS_LOGIC_CHANGED=NO"
echo "BUILD_RESULT=PASS"
echo "LIVE_DEPLOY=PASS"
echo "MY_WORKSPACE_SHA256=$WORKSPACE_SHA"
echo "TASKS_CSS_SHA256=$CSS_SHA"
echo "NO_COMMIT_OR_PUSH=YES"
echo "--- GIT STATUS ---"
git -C "$ROOT" status --short
