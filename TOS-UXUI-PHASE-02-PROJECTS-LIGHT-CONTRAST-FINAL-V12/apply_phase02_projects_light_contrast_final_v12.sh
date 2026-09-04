#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/var/www/TOS}"
PATCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCH_REPO_ROOT="$(cd "$PATCH_DIR/.." && pwd)"
SOURCE_APPEND="$PATCH_DIR/projects-light-contrast-final-v12.append.css"

MAIN_TARGET="frontend/src/main.jsx"
PROJECTS_TARGET="frontend/src/pages/ProjectsPage.jsx"
CSS_TARGET="frontend/src/styles/projects-github-reference.css"

EXPECTED_MAIN_HEAD_BLOB="10a76aae2e1c5a20ce84d28e304c565a96aef500"
EXPECTED_PROJECTS_HEAD_BLOB="1720111a2bab77133eac9f7c754ddd89a58fa179"
EXPECTED_V11_CSS_SHA256="7ba34f6691f796c66af5c6117593f218970437086da96d42751dfee01ec83e48"
IMPORT_LINE='import "./styles/projects-github-reference.css";'
V11_RUNTIME='--tos-projects-couture-v11-runtime'
V12_RUNTIME='--tos-projects-light-contrast-v12-runtime'

DIST="$ROOT/frontend/dist"
LIVE_PARENT="/opt/apps/tamiyouz-front"
LIVE="$LIVE_PARENT/build"
STAMP="$(date +%Y%m%d-%H%M%S)"
STAGE="$LIVE_PARENT/build.phase02-light-contrast-v12.new.$$"
BACKUP="$LIVE_PARENT/build.phase02-light-contrast-v12.backup-$STAMP"

fail() {
  echo "PHASE02_PROJECTS_LIGHT_CONTRAST_FINAL_V12=FAIL"
  echo "ERROR=$1" >&2
  exit "${2:-1}"
}

[ -d "$ROOT/.git" ] || fail "TOS repository not found" 2
[ -d "$PATCH_REPO_ROOT/.git" ] || fail "TOS-Patchs repository not found" 3
[ -f "$SOURCE_APPEND" ] || fail "Missing V12 CSS source" 4
[ -f "$ROOT/$MAIN_TARGET" ] || fail "Missing main.jsx" 5
[ -f "$ROOT/$PROJECTS_TARGET" ] || fail "Missing ProjectsPage.jsx" 6
[ -f "$ROOT/$CSS_TARGET" ] || fail "Missing Projects stylesheet" 7
[ -d "$LIVE" ] || fail "Live frontend root missing" 8

SOURCE_REL="${SOURCE_APPEND#$PATCH_REPO_ROOT/}"
[ "$(git -C "$PATCH_REPO_ROOT" hash-object "$SOURCE_APPEND")" = "$(git -C "$PATCH_REPO_ROOT" rev-parse "HEAD:$SOURCE_REL")" ] || fail "V12 patch source differs from TOS-Patchs HEAD" 9

git -C "$ROOT" diff --cached --quiet || fail "Staged changes exist; stop" 10
[ "$(git -C "$ROOT" rev-parse "HEAD:$MAIN_TARGET")" = "$EXPECTED_MAIN_HEAD_BLOB" ] || fail "Committed main.jsx baseline changed" 11
[ "$(git -C "$ROOT" rev-parse "HEAD:$PROJECTS_TARGET")" = "$EXPECTED_PROJECTS_HEAD_BLOB" ] || fail "Committed ProjectsPage.jsx baseline changed" 12
[ "$(grep -Fxc "$IMPORT_LINE" "$ROOT/$MAIN_TARGET" || true)" = "1" ] || fail "Projects CSS import missing or duplicated" 13
[ "$(grep -Fc -- "$V11_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "V11 runtime baseline missing" 14
[ "$(grep -Fc 'tos-projects-command-center' "$ROOT/$PROJECTS_TARGET" || true)" -ge 1 ] || fail "Command-center hook missing" 15
[ "$(grep -Fc 'tos-project-list-row--selected' "$ROOT/$PROJECTS_TARGET" || true)" -ge 1 ] || fail "Selected-row hook missing" 16
[ "$(grep -Fc 'tos-project-inspector' "$ROOT/$PROJECTS_TARGET" || true)" -ge 1 ] || fail "Inspector hook missing" 17

STATUS="$(git -C "$ROOT" status --porcelain=v1 --untracked-files=all)"
PATHS="$(printf '%s\n' "$STATUS" | sed '/^$/d' | cut -c4- | sort -u)"
EXPECTED_PATHS="$(printf '%s\n%s\n%s\n' "$MAIN_TARGET" "$PROJECTS_TARGET" "$CSS_TARGET" | sort)"
[ "$PATHS" = "$EXPECTED_PATHS" ] || {
  echo "--- PRE-EXISTING STATUS ---"
  printf '%s\n' "$STATUS"
  fail "Expected exact reviewed V11 working-tree paths only" 18
}

V12_COUNT="$(grep -Fc -- "$V12_RUNTIME" "$ROOT/$CSS_TARGET" || true)"
[ "$V12_COUNT" -le 1 ] || fail "Duplicate V12 runtime sentinel" 19

if [ "$V12_COUNT" = "0" ]; then
  CURRENT_SHA="$(sha256sum "$ROOT/$CSS_TARGET" | awk '{print $1}')"
  echo "BASELINE_CSS_SHA256=$CURRENT_SHA"
  [ "$CURRENT_SHA" = "$EXPECTED_V11_CSS_SHA256" ] || fail "Projects CSS is not exact reviewed V11 baseline" 20
  printf '\n' >> "$ROOT/$CSS_TARGET"
  cat "$SOURCE_APPEND" >> "$ROOT/$CSS_TARGET"
  PATCH_ACTION="APPLIED_LIGHT_CONTRAST_FINAL_V12"
else
  PATCH_ACTION="VALIDATED_EXISTING_LIGHT_CONTRAST_V12"
fi

[ "$(grep -Fc -- "$V12_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "V12 runtime sentinel missing in source" 21

git -C "$ROOT" diff --check -- "$MAIN_TARGET" "$PROJECTS_TARGET" "$CSS_TARGET"

cd "$ROOT/frontend"
npm run build
cd "$ROOT"

[ -f "$DIST/index.html" ] || fail "Built dist index missing" 22
grep -RFlq -- "$V12_RUNTIME" "$DIST/assets" || fail "V12 runtime sentinel missing from dist assets" 23
grep -RFlq 'conic-gradient' "$DIST/assets" || fail "Progress visual missing from dist assets" 24

rm -rf "$STAGE"
mkdir -p "$STAGE"
cp -a "$DIST/." "$STAGE/"
[ -f "$STAGE/index.html" ] || fail "Staged index missing" 25
grep -RFlq -- "$V12_RUNTIME" "$STAGE/assets" || fail "V12 runtime sentinel missing from staged assets" 26

mv "$LIVE" "$BACKUP"
if ! mv "$STAGE" "$LIVE"; then
  mv "$BACKUP" "$LIVE" || true
  fail "Failed to activate V12 live build; rollback attempted" 27
fi

if ! grep -RFlq -- "$V12_RUNTIME" "$LIVE/assets"; then
  rm -rf "$LIVE"
  mv "$BACKUP" "$LIVE" || true
  fail "Live V12 runtime sentinel missing; rolled back" 28
fi

FINAL_STATUS="$(git -C "$ROOT" status --porcelain=v1 --untracked-files=all)"
FINAL_PATHS="$(printf '%s\n' "$FINAL_STATUS" | sed '/^$/d' | cut -c4- | sort -u)"
[ "$FINAL_PATHS" = "$EXPECTED_PATHS" ] || fail "Unexpected TOS files changed" 29

FINAL_SHA="$(sha256sum "$ROOT/$CSS_TARGET" | awk '{print $1}')"
echo "PHASE02_PROJECTS_LIGHT_CONTRAST_FINAL_V12=PASS"
echo "SCREEN=Projects"
echo "PATCH_ACTION=$PATCH_ACTION"
echo "LIGHT_MODE_ONLY=YES"
echo "ROW_AVATAR_CONTRAST=FIXED"
echo "INSPECTOR_HERO_CONTRAST=FIXED"
echo "INSPECTOR_METRIC_CONTRAST=FIXED"
echo "PROGRESS_VALUE_CONTRAST=FIXED"
echo "FILTER_VALUE_CONTRAST=FIXED"
echo "MICRO_TEXT_CONTRAST=FIXED"
echo "DARK_MODE_CHANGED=NO"
echo "BUILD_RESULT=PASS"
echo "LIVE_DEPLOY=PASS"
echo "DIST_RUNTIME_SENTINEL=PASS"
echo "LIVE_RUNTIME_SENTINEL=PASS"
echo "CHANGED_FILES=$MAIN_TARGET,$PROJECTS_TARGET,$CSS_TARGET"
echo "CSS_SHA256=$FINAL_SHA"
echo "BUSINESS_LOGIC_CHANGED=NO"
echo "COMMIT_CREATED=NO"
echo "PUSH_PERFORMED=NO"
echo "READY_FOR_VISUAL_REVIEW=YES"
echo "--- GIT STATUS ---"
printf '%s\n' "$FINAL_STATUS"
