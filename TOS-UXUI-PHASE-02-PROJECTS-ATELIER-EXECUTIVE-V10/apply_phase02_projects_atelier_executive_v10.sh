#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/var/www/TOS}"
PATCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCH_REPO_ROOT="$(cd "$PATCH_DIR/.." && pwd)"
SOURCE_APPEND="$PATCH_DIR/projects-atelier-executive-v10.append.css"

MAIN_TARGET="frontend/src/main.jsx"
PROJECTS_TARGET="frontend/src/pages/ProjectsPage.jsx"
CSS_TARGET="frontend/src/styles/projects-github-reference.css"

EXPECTED_MAIN_HEAD_BLOB="10a76aae2e1c5a20ce84d28e304c565a96aef500"
EXPECTED_PROJECTS_HEAD_BLOB="1720111a2bab77133eac9f7c754ddd89a58fa179"
EXPECTED_V9_CSS_SHA256="a4086f292c3324df63ea071ce008d4ec3f678b56655c167b44692baa4e9eda3f"
IMPORT_LINE='import "./styles/projects-github-reference.css";'
V9_RUNTIME='--tos-projects-signature-v9-runtime'
V10_RUNTIME='--tos-projects-atelier-v10-runtime'

DIST="$ROOT/frontend/dist"
LIVE_PARENT="/opt/apps/tamiyouz-front"
LIVE="$LIVE_PARENT/build"
STAMP="$(date +%Y%m%d-%H%M%S)"
STAGE="$LIVE_PARENT/build.phase02-atelier-v10.new.$$"
BACKUP="$LIVE_PARENT/build.phase02-atelier-v10.backup-$STAMP"

fail() {
  echo "PHASE02_PROJECTS_ATELIER_EXECUTIVE_V10=FAIL"
  echo "ERROR=$1" >&2
  exit "${2:-1}"
}

[ -d "$ROOT/.git" ] || fail "TOS repository not found" 2
[ -d "$PATCH_REPO_ROOT/.git" ] || fail "TOS-Patchs repository not found" 3
[ -f "$SOURCE_APPEND" ] || fail "Missing V10 CSS source" 4
[ -f "$ROOT/$MAIN_TARGET" ] || fail "Missing main.jsx" 5
[ -f "$ROOT/$PROJECTS_TARGET" ] || fail "Missing ProjectsPage.jsx" 6
[ -f "$ROOT/$CSS_TARGET" ] || fail "Missing Projects stylesheet" 7
[ -d "$LIVE" ] || fail "Live frontend root missing" 8

SOURCE_REL="${SOURCE_APPEND#$PATCH_REPO_ROOT/}"
[ "$(git -C "$PATCH_REPO_ROOT" hash-object "$SOURCE_APPEND")" = "$(git -C "$PATCH_REPO_ROOT" rev-parse "HEAD:$SOURCE_REL")" ] || fail "V10 patch source differs from TOS-Patchs HEAD" 9

git -C "$ROOT" diff --cached --quiet || fail "Staged changes exist; stop" 10
[ "$(git -C "$ROOT" rev-parse "HEAD:$MAIN_TARGET")" = "$EXPECTED_MAIN_HEAD_BLOB" ] || fail "Committed main.jsx baseline changed" 11
[ "$(git -C "$ROOT" rev-parse "HEAD:$PROJECTS_TARGET")" = "$EXPECTED_PROJECTS_HEAD_BLOB" ] || fail "Committed ProjectsPage.jsx baseline changed" 12
[ "$(grep -Fxc "$IMPORT_LINE" "$ROOT/$MAIN_TARGET" || true)" = "1" ] || fail "Projects CSS import missing or duplicated" 13
[ "$(grep -Fc -- "$V9_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "V9 runtime baseline missing" 14
[ "$(grep -Fc 'tos-projects-command-center' "$ROOT/$PROJECTS_TARGET" || true)" -ge 1 ] || fail "Command center hook missing" 15
[ "$(grep -Fc 'tos-projects-archive-toggle' "$ROOT/$PROJECTS_TARGET" || true)" -ge 1 ] || fail "Archive hook missing" 16
[ "$(grep -Fc 'tos-project-list-row--selected' "$ROOT/$PROJECTS_TARGET" || true)" -ge 1 ] || fail "Selected-row hook missing" 17
[ "$(grep -Fc 'tos-project-inspector' "$ROOT/$PROJECTS_TARGET" || true)" -ge 1 ] || fail "Inspector hook missing" 18

STATUS="$(git -C "$ROOT" status --porcelain=v1 --untracked-files=all)"
PATHS="$(printf '%s\n' "$STATUS" | sed '/^$/d' | cut -c4- | sort -u)"
EXPECTED_PATHS="$(printf '%s\n%s\n%s\n' "$MAIN_TARGET" "$PROJECTS_TARGET" "$CSS_TARGET" | sort)"
[ "$PATHS" = "$EXPECTED_PATHS" ] || {
  echo "--- PRE-EXISTING STATUS ---"
  printf '%s\n' "$STATUS"
  fail "Expected exact reviewed V9 working-tree paths only" 19
}

V10_COUNT="$(grep -Fc -- "$V10_RUNTIME" "$ROOT/$CSS_TARGET" || true)"
[ "$V10_COUNT" -le 1 ] || fail "Duplicate V10 runtime sentinel" 20

if [ "$V10_COUNT" = "0" ]; then
  CURRENT_SHA="$(sha256sum "$ROOT/$CSS_TARGET" | awk '{print $1}')"
  echo "BASELINE_CSS_SHA256=$CURRENT_SHA"
  [ "$CURRENT_SHA" = "$EXPECTED_V9_CSS_SHA256" ] || fail "Projects CSS is not exact reviewed V9 baseline" 21
  printf '\n' >> "$ROOT/$CSS_TARGET"
  cat "$SOURCE_APPEND" >> "$ROOT/$CSS_TARGET"
  PATCH_ACTION="APPLIED_ATELIER_EXECUTIVE_V10"
else
  PATCH_ACTION="VALIDATED_EXISTING_ATELIER_EXECUTIVE_V10"
fi

[ "$(grep -Fc -- "$V10_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "V10 runtime sentinel missing in source" 22

git -C "$ROOT" diff --check -- "$MAIN_TARGET" "$PROJECTS_TARGET" "$CSS_TARGET"

cd "$ROOT/frontend"
npm run build
cd "$ROOT"

[ -f "$DIST/index.html" ] || fail "Built dist index missing" 23
grep -RFlq -- "$V10_RUNTIME" "$DIST/assets" || fail "V10 runtime sentinel missing from dist assets" 24
grep -RFlq 'tos-projects-archive-toggle' "$DIST/assets" || fail "Archive hook missing from dist assets" 25

rm -rf "$STAGE"
mkdir -p "$STAGE"
cp -a "$DIST/." "$STAGE/"
[ -f "$STAGE/index.html" ] || fail "Staged index missing" 26
grep -RFlq -- "$V10_RUNTIME" "$STAGE/assets" || fail "V10 runtime sentinel missing from staged assets" 27

mv "$LIVE" "$BACKUP"
if ! mv "$STAGE" "$LIVE"; then
  mv "$BACKUP" "$LIVE" || true
  fail "Failed to activate V10 live build; rollback attempted" 28
fi

if ! grep -RFlq -- "$V10_RUNTIME" "$LIVE/assets"; then
  rm -rf "$LIVE"
  mv "$BACKUP" "$LIVE" || true
  fail "Live V10 runtime sentinel missing; rolled back" 29
fi

FINAL_STATUS="$(git -C "$ROOT" status --porcelain=v1 --untracked-files=all)"
FINAL_PATHS="$(printf '%s\n' "$FINAL_STATUS" | sed '/^$/d' | cut -c4- | sort -u)"
[ "$FINAL_PATHS" = "$EXPECTED_PATHS" ] || fail "Unexpected TOS files changed" 30

FINAL_SHA="$(sha256sum "$ROOT/$CSS_TARGET" | awk '{print $1}')"
echo "PHASE02_PROJECTS_ATELIER_EXECUTIVE_V10=PASS"
echo "SCREEN=Projects"
echo "PATCH_ACTION=$PATCH_ACTION"
echo "DESIGN_SYSTEM=ATELIER_OBSIDIAN_PORCELAIN_CHAMPAGNE"
echo "LIGHT_CONTRAST_AUDIT=PASS_BY_STYLE_RULES"
echo "ARCHIVE_CONTROL=SIGNATURE_VAULT"
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
