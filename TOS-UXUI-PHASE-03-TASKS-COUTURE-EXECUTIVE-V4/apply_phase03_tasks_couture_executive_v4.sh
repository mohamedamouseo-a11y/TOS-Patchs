#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/var/www/TOS}"
PATCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCH_REPO_ROOT="$(cd "$PATCH_DIR/.." && pwd)"
SOURCE_APPEND="$PATCH_DIR/tasks-couture-executive-v4.append.css"

MAIN_TARGET="frontend/src/main.jsx"
TASKS_TARGET="frontend/src/components/ProfessionalTaskBoard.jsx"
CSS_TARGET="frontend/src/styles/tasks-projects-premium-reference.css"

EXPECTED_MAIN_HEAD_BLOB="725b57d3b7927b802dcedc26cca49c6a7f10ee55"
EXPECTED_TASKS_HEAD_BLOB="2a4fe1052b55e7f7f3d5da88c7eb0eb29fdb26d5"
EXPECTED_V3_CSS_SHA256="37ee3011f6e136c0f23a6cbbc4dce6e2ffc86e6a909b275c248a0c3f2875d4c5"
IMPORT_LINE='import "./styles/tasks-projects-premium-reference.css";'
V3_RUNTIME='--tos-tasks-active-board-v3-runtime'
V4_RUNTIME='--tos-tasks-couture-v4-runtime'

DIST="$ROOT/frontend/dist"
LIVE_PARENT="/opt/apps/tamiyouz-front"
LIVE="$LIVE_PARENT/build"
STAMP="$(date +%Y%m%d-%H%M%S)"
STAGE="$LIVE_PARENT/build.phase03-tasks-couture-v4.new.$$"
BACKUP="$LIVE_PARENT/build.phase03-tasks-couture-v4.backup-$STAMP"

fail() {
  echo "PHASE03_TASKS_COUTURE_EXECUTIVE_V4=FAIL"
  echo "ERROR=$1" >&2
  exit "${2:-1}"
}

[ -d "$ROOT/.git" ] || fail "TOS repository not found" 2
[ -d "$PATCH_REPO_ROOT/.git" ] || fail "TOS-Patchs repository not found" 3
[ -f "$SOURCE_APPEND" ] || fail "Missing V4 CSS source" 4
[ -f "$ROOT/$MAIN_TARGET" ] || fail "Missing main.jsx" 5
[ -f "$ROOT/$TASKS_TARGET" ] || fail "Missing ProfessionalTaskBoard.jsx" 6
[ -f "$ROOT/$CSS_TARGET" ] || fail "Missing Tasks premium stylesheet" 7
[ -d "$LIVE" ] || fail "Live frontend root missing" 8

SOURCE_REL="${SOURCE_APPEND#$PATCH_REPO_ROOT/}"
[ "$(git -C "$PATCH_REPO_ROOT" hash-object "$SOURCE_APPEND")" = "$(git -C "$PATCH_REPO_ROOT" rev-parse "HEAD:$SOURCE_REL")" ] || fail "V4 patch source differs from TOS-Patchs HEAD" 9

git -C "$ROOT" diff --cached --quiet || fail "Staged changes exist; stop" 10
[ "$(git -C "$ROOT" rev-parse "HEAD:$MAIN_TARGET")" = "$EXPECTED_MAIN_HEAD_BLOB" ] || fail "Committed main.jsx baseline changed" 11
[ "$(git -C "$ROOT" rev-parse "HEAD:$TASKS_TARGET")" = "$EXPECTED_TASKS_HEAD_BLOB" ] || fail "Committed ProfessionalTaskBoard baseline changed" 12
[ "$(grep -Fxc "$IMPORT_LINE" "$ROOT/$MAIN_TARGET" || true)" = "1" ] || fail "Tasks premium CSS import missing or duplicated" 13
[ "$(grep -Fc -- "$V3_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "V3 runtime baseline missing" 14
grep -Fq 'tos-modern-board-column' "$ROOT/$TASKS_TARGET" || fail "Modern board column hook missing" 15
grep -Fq 'tos-modern-task-card' "$ROOT/frontend/src/features/tasks/taskBoardParts.jsx" || fail "Modern task-card hook missing" 16
grep -Fq 'tos-management-card' "$ROOT/$TASKS_TARGET" || fail "Workspace tools hook missing" 17

STATUS="$(git -C "$ROOT" status --porcelain=v1 --untracked-files=all)"
PATHS="$(printf '%s\n' "$STATUS" | sed '/^$/d' | cut -c4- | sort -u)"
EXPECTED_PATHS="$(printf '%s\n%s\n' "$MAIN_TARGET" "$CSS_TARGET" | sort)"
[ "$PATHS" = "$EXPECTED_PATHS" ] || {
  echo "--- PRE-EXISTING STATUS ---"
  printf '%s\n' "$STATUS"
  fail "Expected exact reviewed V3 working-tree paths only" 18
}

V4_COUNT="$(grep -Fc -- "$V4_RUNTIME" "$ROOT/$CSS_TARGET" || true)"
[ "$V4_COUNT" -le 1 ] || fail "Duplicate V4 runtime sentinel" 19

if [ "$V4_COUNT" = "0" ]; then
  CURRENT_SHA="$(sha256sum "$ROOT/$CSS_TARGET" | awk '{print $1}')"
  echo "BASELINE_CSS_SHA256=$CURRENT_SHA"
  [ "$CURRENT_SHA" = "$EXPECTED_V3_CSS_SHA256" ] || fail "Tasks CSS is not exact reviewed V3 baseline" 20
  printf '\n' >> "$ROOT/$CSS_TARGET"
  cat "$SOURCE_APPEND" >> "$ROOT/$CSS_TARGET"
  PATCH_ACTION="APPLIED_COUTURE_EXECUTIVE_V4"
else
  PATCH_ACTION="VALIDATED_EXISTING_COUTURE_EXECUTIVE_V4"
fi

[ "$(grep -Fc -- "$V4_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "V4 runtime sentinel missing in source" 21

git -C "$ROOT" diff --check -- "$MAIN_TARGET" "$CSS_TARGET"

cd "$ROOT/frontend"
npm run build
cd "$ROOT"

[ -f "$DIST/index.html" ] || fail "Built dist index missing" 22
grep -RFlq -- "$V4_RUNTIME" "$DIST/assets" || fail "V4 runtime sentinel missing from dist assets" 23
grep -RFlq 'tos-modern-board-column' "$DIST/assets" || fail "Board column marker missing from dist assets" 24
grep -RFlq 'tos-modern-task-card' "$DIST/assets" || fail "Task card marker missing from dist assets" 25

rm -rf "$STAGE"
mkdir -p "$STAGE"
cp -a "$DIST/." "$STAGE/"
[ -f "$STAGE/index.html" ] || fail "Staged index missing" 26
grep -RFlq -- "$V4_RUNTIME" "$STAGE/assets" || fail "V4 runtime sentinel missing from staged assets" 27

mv "$LIVE" "$BACKUP"
if ! mv "$STAGE" "$LIVE"; then
  mv "$BACKUP" "$LIVE" || true
  fail "Failed to activate V4 live build; rollback attempted" 28
fi

if ! grep -RFlq -- "$V4_RUNTIME" "$LIVE/assets"; then
  rm -rf "$LIVE"
  mv "$BACKUP" "$LIVE" || true
  fail "Live V4 runtime sentinel missing; rolled back" 29
fi

FINAL_STATUS="$(git -C "$ROOT" status --porcelain=v1 --untracked-files=all)"
FINAL_PATHS="$(printf '%s\n' "$FINAL_STATUS" | sed '/^$/d' | cut -c4- | sort -u)"
[ "$FINAL_PATHS" = "$EXPECTED_PATHS" ] || fail "Unexpected TOS files changed" 30

FINAL_SHA="$(sha256sum "$ROOT/$CSS_TARGET" | awk '{print $1}')"
echo "PHASE03_TASKS_COUTURE_EXECUTIVE_V4=PASS"
echo "SCREEN=Tasks"
echo "STATE=Active_Task_Board"
echo "REFERENCE=Phase_02_Projects_Premium"
echo "PATCH_ACTION=$PATCH_ACTION"
echo "VISUAL_LEVEL=COUTURE_EXECUTIVE"
echo "DARK_MODE=OBSIDIAN_BLACK_TITANIUM"
echo "LIGHT_MODE=PORCELAIN_IVORY_CHAMPAGNE"
echo "TASK_CARDS=RAISED_EXECUTIVE"
echo "BOARD_COLUMNS=LAYERED_PREMIUM"
echo "WORKSPACE_TOOLS=COMMAND_DECK"
echo "BUSINESS_LOGIC_CHANGED=NO"
echo "BUILD_RESULT=PASS"
echo "LIVE_DEPLOY=PASS"
echo "DIST_RUNTIME_SENTINEL=PASS"
echo "LIVE_RUNTIME_SENTINEL=PASS"
echo "CHANGED_FILES=$MAIN_TARGET,$CSS_TARGET"
echo "CSS_SHA256=$FINAL_SHA"
echo "COMMIT_CREATED=NO"
echo "PUSH_PERFORMED=NO"
echo "READY_FOR_VISUAL_REVIEW=YES"
echo "--- GIT STATUS ---"
printf '%s\n' "$FINAL_STATUS"
