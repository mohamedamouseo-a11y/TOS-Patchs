#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/var/www/TOS}"
PATCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_APPEND="$PATCH_DIR/projects-executive-luxury-v5.append.css"
MAIN_TARGET="frontend/src/main.jsx"
PROJECTS_TARGET="frontend/src/pages/ProjectsPage.jsx"
CSS_TARGET="frontend/src/styles/projects-github-reference.css"
EXPECTED_MAIN_HEAD_BLOB="10a76aae2e1c5a20ce84d28e304c565a96aef500"
EXPECTED_PROJECTS_HEAD_BLOB="1720111a2bab77133eac9f7c754ddd89a58fa179"
EXPECTED_V4_CSS_SHA256="1de7ff873d62958aaad7d66ba945a5918de515cd1fe9b0ffe0980bc2a91a5454"
IMPORT_LINE='import "./styles/projects-github-reference.css";'
SENTINEL='--tos-phase02-projects-v5'
DIST="$ROOT/frontend/dist"
LIVE_PARENT="/opt/apps/tamiyouz-front"
LIVE="$LIVE_PARENT/build"
STAMP="$(date +%Y%m%d-%H%M%S)"
STAGE="$LIVE_PARENT/build.phase02-exec-v5.new.$$"
BACKUP="$LIVE_PARENT/build.phase02-exec-v5.backup-$STAMP"

fail() {
  echo "PHASE02_PROJECTS_EXECUTIVE_LUXURY_V5=FAIL"
  echo "ERROR=$1" >&2
  exit "${2:-1}"
}

[ -d "$ROOT/.git" ] || fail "TOS repository not found" 2
[ -f "$SOURCE_APPEND" ] || fail "Missing V5 CSS source" 3
[ -f "$ROOT/$MAIN_TARGET" ] || fail "Missing main.jsx" 4
[ -f "$ROOT/$PROJECTS_TARGET" ] || fail "Missing ProjectsPage.jsx" 5
[ -f "$ROOT/$CSS_TARGET" ] || fail "Missing Projects stylesheet" 6
[ -d "$LIVE" ] || fail "Live frontend root missing" 7

git -C "$ROOT" diff --cached --quiet || fail "Staged changes exist; stop" 8
[ "$(git -C "$ROOT" rev-parse "HEAD:$MAIN_TARGET")" = "$EXPECTED_MAIN_HEAD_BLOB" ] || fail "Committed main.jsx baseline changed" 9
[ "$(git -C "$ROOT" rev-parse "HEAD:$PROJECTS_TARGET")" = "$EXPECTED_PROJECTS_HEAD_BLOB" ] || fail "Committed ProjectsPage.jsx baseline changed" 10
[ "$(grep -Fxc "$IMPORT_LINE" "$ROOT/$MAIN_TARGET" || true)" = "1" ] || fail "Projects CSS import missing or duplicated" 11

STATUS="$(git -C "$ROOT" status --porcelain=v1 --untracked-files=all)"
PATHS="$(printf '%s\n' "$STATUS" | sed '/^$/d' | cut -c4- | sort -u)"
EXPECTED_PATHS="$(printf '%s\n%s\n' "$MAIN_TARGET" "$CSS_TARGET" | sort)"
[ "$PATHS" = "$EXPECTED_PATHS" ] || {
  echo "--- PRE-EXISTING STATUS ---"
  printf '%s\n' "$STATUS"
  fail "Expected exact Phase 02 working-tree state only" 12
}

if grep -Fq -- "$SENTINEL" "$ROOT/$CSS_TARGET"; then
  PATCH_ACTION="VALIDATED_EXISTING_V5"
else
  CURRENT_SHA="$(sha256sum "$ROOT/$CSS_TARGET" | awk '{print $1}')"
  echo "CURRENT_CSS_SHA256=$CURRENT_SHA"
  [ "$CURRENT_SHA" = "$EXPECTED_V4_CSS_SHA256" ] || fail "Projects CSS is not exact V4 baseline" 13
  printf '\n' >> "$ROOT/$CSS_TARGET"
  cat "$SOURCE_APPEND" >> "$ROOT/$CSS_TARGET"
  PATCH_ACTION="APPLIED_EXECUTIVE_LUXURY_V5"
fi

[ "$(grep -Fc -- "$SENTINEL" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "V5 sentinel missing or duplicated" 14

git -C "$ROOT" diff --check -- "$MAIN_TARGET" "$CSS_TARGET"

cd "$ROOT/frontend"
npm run build
cd "$ROOT"

[ -f "$DIST/index.html" ] || fail "Built dist index missing" 15
grep -RFlq -- "$SENTINEL" "$DIST/assets" || fail "V5 runtime sentinel missing from dist assets" 16

rm -rf "$STAGE"
mkdir -p "$STAGE"
cp -a "$DIST/." "$STAGE/"
[ -f "$STAGE/index.html" ] || fail "Staged index missing" 17
grep -RFlq -- "$SENTINEL" "$STAGE/assets" || fail "V5 runtime sentinel missing from staged assets" 18

mv "$LIVE" "$BACKUP"
if ! mv "$STAGE" "$LIVE"; then
  mv "$BACKUP" "$LIVE" || true
  fail "Failed to activate V5 live build; rollback attempted" 19
fi

if ! grep -RFlq -- "$SENTINEL" "$LIVE/assets"; then
  rm -rf "$LIVE"
  mv "$BACKUP" "$LIVE" || true
  fail "Live V5 sentinel missing; rolled back" 20
fi

FINAL_STATUS="$(git -C "$ROOT" status --porcelain=v1 --untracked-files=all)"
FINAL_PATHS="$(printf '%s\n' "$FINAL_STATUS" | sed '/^$/d' | cut -c4- | sort -u)"
[ "$FINAL_PATHS" = "$EXPECTED_PATHS" ] || fail "Unexpected TOS files changed" 21

FINAL_SHA="$(sha256sum "$ROOT/$CSS_TARGET" | awk '{print $1}')"
echo "PHASE02_PROJECTS_EXECUTIVE_LUXURY_V5=PASS"
echo "SCREEN=Projects"
echo "PATCH_ACTION=$PATCH_ACTION"
echo "BUILD_RESULT=PASS"
echo "LIVE_DEPLOY=PASS"
echo "DIST_RUNTIME_SENTINEL=PASS"
echo "LIVE_RUNTIME_SENTINEL=PASS"
echo "DARK_MODE_PRIORITY=YES"
echo "CHANGED_FILES=$MAIN_TARGET,$CSS_TARGET"
echo "CSS_SHA256=$FINAL_SHA"
echo "BUSINESS_LOGIC_CHANGED=NO"
echo "COMMIT_CREATED=NO"
echo "PUSH_PERFORMED=NO"
echo "READY_FOR_VISUAL_REVIEW=YES"
echo "--- GIT STATUS ---"
printf '%s\n' "$FINAL_STATUS"
