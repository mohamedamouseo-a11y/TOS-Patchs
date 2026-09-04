#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/var/www/TOS}"
PATCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCH_REPO_ROOT="$(cd "$PATCH_DIR/.." && pwd)"
SOURCE_APPEND="$PATCH_DIR/tasks-projects-premium-reference-v2.append.css"

MAIN_TARGET="frontend/src/main.jsx"
TASKS_TARGET="frontend/src/components/ProfessionalTaskBoard.jsx"
CSS_TARGET="frontend/src/styles/tasks-projects-premium-reference.css"

EXPECTED_MAIN_HEAD_BLOB="725b57d3b7927b802dcedc26cca49c6a7f10ee55"
EXPECTED_TASKS_HEAD_BLOB="2a4fe1052b55e7f7f3d5da88c7eb0eb29fdb26d5"
EXPECTED_V1_CSS_SHA256="97e09d9c0c5e237fa60471ce207b478a6a5b08596d0b6f3a25b922b8ed6551ba"
IMPORT_LINE='import "./styles/tasks-projects-premium-reference.css";'
V1_RUNTIME='--tos-tasks-projects-reference-v1-runtime'
V2_RUNTIME='--tos-tasks-projects-reference-v2-runtime'

DIST="$ROOT/frontend/dist"
LIVE_PARENT="/opt/apps/tamiyouz-front"
LIVE="$LIVE_PARENT/build"
STAMP="$(date +%Y%m%d-%H%M%S)"
STAGE="$LIVE_PARENT/build.phase03-tasks-v2.new.$$"
BACKUP="$LIVE_PARENT/build.phase03-tasks-v2.backup-$STAMP"

fail() {
  echo "PHASE03_TASKS_PROJECTS_PREMIUM_REFERENCE_V2=FAIL"
  echo "ERROR=$1" >&2
  exit "${2:-1}"
}

[ -d "$ROOT/.git" ] || fail "TOS repository not found" 2
[ -d "$PATCH_REPO_ROOT/.git" ] || fail "TOS-Patchs repository not found" 3
[ -f "$SOURCE_APPEND" ] || fail "Missing V2 CSS source" 4
[ -f "$ROOT/$MAIN_TARGET" ] || fail "Missing main.jsx" 5
[ -f "$ROOT/$TASKS_TARGET" ] || fail "Missing ProfessionalTaskBoard.jsx" 6
[ -f "$ROOT/$CSS_TARGET" ] || fail "Missing tasks premium stylesheet" 7
[ -d "$LIVE" ] || fail "Live frontend root missing" 8

SOURCE_REL="${SOURCE_APPEND#$PATCH_REPO_ROOT/}"
[ "$(git -C "$PATCH_REPO_ROOT" hash-object "$SOURCE_APPEND")" = "$(git -C "$PATCH_REPO_ROOT" rev-parse "HEAD:$SOURCE_REL")" ] || fail "V2 patch source differs from TOS-Patchs HEAD" 9

git -C "$ROOT" diff --cached --quiet || fail "Staged changes exist; stop" 10
[ "$(git -C "$ROOT" rev-parse "HEAD:$MAIN_TARGET")" = "$EXPECTED_MAIN_HEAD_BLOB" ] || fail "Committed main.jsx baseline changed" 11
[ "$(git -C "$ROOT" rev-parse "HEAD:$TASKS_TARGET")" = "$EXPECTED_TASKS_HEAD_BLOB" ] || fail "Committed ProfessionalTaskBoard baseline changed" 12
[ "$(grep -Fxc "$IMPORT_LINE" "$ROOT/$MAIN_TARGET" || true)" = "1" ] || fail "Tasks premium CSS import missing or duplicated" 13
[ "$(grep -Fc -- "$V1_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "V1 runtime baseline missing" 14

grep -Fq 'tos-tasks-entry-v6' "$ROOT/$TASKS_TARGET" || fail "Tasks gateway root missing" 15
grep -Fq 'tos-tasks-system-theme-v15' "$ROOT/$TASKS_TARGET" || fail "Active task-board root missing" 16

STATUS="$(git -C "$ROOT" status --porcelain=v1 --untracked-files=all)"
PATHS="$(printf '%s\n' "$STATUS" | sed '/^$/d' | cut -c4- | sort -u)"
EXPECTED_PATHS="$(printf '%s\n%s\n' "$MAIN_TARGET" "$CSS_TARGET" | sort)"
[ "$PATHS" = "$EXPECTED_PATHS" ] || {
  echo "--- PRE-EXISTING STATUS ---"
  printf '%s\n' "$STATUS"
  fail "Expected exact reviewed V1 working-tree paths only" 17
}

V2_COUNT="$(grep -Fc -- "$V2_RUNTIME" "$ROOT/$CSS_TARGET" || true)"
[ "$V2_COUNT" -le 1 ] || fail "Duplicate V2 runtime sentinel" 18

if [ "$V2_COUNT" = "0" ]; then
  CURRENT_SHA="$(sha256sum "$ROOT/$CSS_TARGET" | awk '{print $1}')"
  echo "BASELINE_CSS_SHA256=$CURRENT_SHA"
  [ "$CURRENT_SHA" = "$EXPECTED_V1_CSS_SHA256" ] || fail "Tasks CSS is not exact reviewed V1 baseline" 19
  printf '\n' >> "$ROOT/$CSS_TARGET"
  cat "$SOURCE_APPEND" >> "$ROOT/$CSS_TARGET"
  PATCH_ACTION="APPLIED_SCREENSHOT_REFINEMENT_V2"
else
  PATCH_ACTION="VALIDATED_EXISTING_V2"
fi

[ "$(grep -Fc -- "$V2_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "V2 runtime sentinel missing in source" 20

git -C "$ROOT" diff --check -- "$MAIN_TARGET" "$CSS_TARGET"

cd "$ROOT/frontend"
npm run build
cd "$ROOT"

[ -f "$DIST/index.html" ] || fail "Built dist index missing" 21
grep -RFlq -- "$V2_RUNTIME" "$DIST/assets" || fail "V2 runtime sentinel missing from dist assets" 22
grep -RFlq 'tos-tasks-entry-v6' "$DIST/assets" || fail "Tasks gateway marker missing from dist" 23
grep -RFlq 'tos-tasks-system-theme-v15' "$DIST/assets" || fail "Active board marker missing from dist" 24

rm -rf "$STAGE"
mkdir -p "$STAGE"
cp -a "$DIST/." "$STAGE/"
[ -f "$STAGE/index.html" ] || fail "Staged index missing" 25
grep -RFlq -- "$V2_RUNTIME" "$STAGE/assets" || fail "V2 runtime sentinel missing from staged assets" 26

mv "$LIVE" "$BACKUP"
if ! mv "$STAGE" "$LIVE"; then
  mv "$BACKUP" "$LIVE" || true
  fail "Failed to activate V2 live build; rollback attempted" 27
fi

if ! grep -RFlq -- "$V2_RUNTIME" "$LIVE/assets"; then
  rm -rf "$LIVE"
  mv "$BACKUP" "$LIVE" || true
  fail "Live V2 runtime sentinel missing; rolled back" 28
fi

FINAL_STATUS="$(git -C "$ROOT" status --porcelain=v1 --untracked-files=all)"
FINAL_PATHS="$(printf '%s\n' "$FINAL_STATUS" | sed '/^$/d' | cut -c4- | sort -u)"
[ "$FINAL_PATHS" = "$EXPECTED_PATHS" ] || fail "Unexpected TOS files changed" 29

FINAL_SHA="$(sha256sum "$ROOT/$CSS_TARGET" | awk '{print $1}')"
echo "PHASE03_TASKS_PROJECTS_PREMIUM_REFERENCE_V2=PASS"
echo "SCREEN=Tasks"
echo "REFERENCE=Phase_02_Projects_Premium"
echo "PATCH_ACTION=$PATCH_ACTION"
echo "DARK_ROWS=MUDDY_FILL_REMOVED"
echo "DARK_METRIC_RINGS=CONTRAST_FIXED"
echo "DARK_TABS=CONTRAST_FIXED"
echo "LIGHT_SELECTED_STATE=POLISHED"
echo "ACTIVE_BOARD_MATERIAL=RETAINED"
echo "BUILD_RESULT=PASS"
echo "LIVE_DEPLOY=PASS"
echo "DIST_RUNTIME_SENTINEL=PASS"
echo "LIVE_RUNTIME_SENTINEL=PASS"
echo "CHANGED_FILES=$MAIN_TARGET,$CSS_TARGET"
echo "CSS_SHA256=$FINAL_SHA"
echo "BUSINESS_LOGIC_CHANGED=NO"
echo "COMMIT_CREATED=NO"
echo "PUSH_PERFORMED=NO"
echo "READY_FOR_VISUAL_REVIEW=YES"
echo "--- GIT STATUS ---"
printf '%s\n' "$FINAL_STATUS"
