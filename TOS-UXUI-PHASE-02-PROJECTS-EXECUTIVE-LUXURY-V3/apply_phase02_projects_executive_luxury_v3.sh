#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/var/www/TOS}"
PATCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_APPEND="$PATCH_DIR/projects-executive-luxury-v3.append.css"
MAIN_TARGET="frontend/src/main.jsx"
PROJECTS_TARGET="frontend/src/pages/ProjectsPage.jsx"
CSS_TARGET="frontend/src/styles/projects-github-reference.css"
EXPECTED_MAIN_HEAD_BLOB="10a76aae2e1c5a20ce84d28e304c565a96aef500"
EXPECTED_PROJECTS_HEAD_BLOB="1720111a2bab77133eac9f7c754ddd89a58fa179"
IMPORT_LINE='import "./styles/projects-github-reference.css";'
V2_START='TOS_PHASE02_PROJECTS_PREMIUM_V2_START'
V2_END='TOS_PHASE02_PROJECTS_PREMIUM_V2_END'
V3_START='TOS_PHASE02_PROJECTS_EXECUTIVE_LUXURY_V3_START'
V3_END='TOS_PHASE02_PROJECTS_EXECUTIVE_LUXURY_V3_END'
DIST="$ROOT/frontend/dist"
LIVE_PARENT="/opt/apps/tamiyouz-front"
LIVE="$LIVE_PARENT/build"
STAMP="$(date +%Y%m%d-%H%M%S)"
STAGE="$LIVE_PARENT/build.phase02-exec-v3.new.$$"
BACKUP="$LIVE_PARENT/build.phase02-exec-v3.backup-$STAMP"

fail() {
  echo "PHASE02_PROJECTS_EXECUTIVE_LUXURY_V3=FAIL"
  echo "ERROR=$1" >&2
  exit "${2:-1}"
}

[ -d "$ROOT/.git" ] || fail "TOS repository not found" 2
[ -f "$SOURCE_APPEND" ] || fail "Missing V3 CSS source" 3
[ -f "$ROOT/$MAIN_TARGET" ] || fail "Missing main.jsx" 4
[ -f "$ROOT/$PROJECTS_TARGET" ] || fail "Missing ProjectsPage.jsx" 5
[ -f "$ROOT/$CSS_TARGET" ] || fail "Missing Projects stylesheet" 6
[ -d "$LIVE" ] || fail "Live frontend root missing" 7

git -C "$ROOT" diff --cached --quiet || fail "Staged changes exist; stop" 8
[ "$(git -C "$ROOT" rev-parse "HEAD:$MAIN_TARGET")" = "$EXPECTED_MAIN_HEAD_BLOB" ] || fail "Committed main.jsx baseline changed" 9
[ "$(git -C "$ROOT" rev-parse "HEAD:$PROJECTS_TARGET")" = "$EXPECTED_PROJECTS_HEAD_BLOB" ] || fail "Committed ProjectsPage.jsx baseline changed" 10
[ "$(grep -Fxc "$IMPORT_LINE" "$ROOT/$MAIN_TARGET" || true)" = "1" ] || fail "Projects CSS import missing or duplicated" 11
[ "$(grep -Fc "$V2_START" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "Premium V2 baseline marker missing" 12
[ "$(grep -Fc "$V2_END" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "Premium V2 end marker missing" 13

STATUS="$(git -C "$ROOT" status --porcelain=v1 --untracked-files=all)"
PATHS="$(printf '%s\n' "$STATUS" | sed '/^$/d' | cut -c4- | sort -u)"
EXPECTED_PATHS="$(printf '%s\n%s\n' "$MAIN_TARGET" "$CSS_TARGET" | sort)"
[ "$PATHS" = "$EXPECTED_PATHS" ] || {
  echo "--- PRE-EXISTING STATUS ---"
  printf '%s\n' "$STATUS"
  fail "Expected exact Phase 02 working-tree state only" 14
}

START_COUNT="$(grep -Fc "$V3_START" "$ROOT/$CSS_TARGET" || true)"
END_COUNT="$(grep -Fc "$V3_END" "$ROOT/$CSS_TARGET" || true)"
[ "$START_COUNT" = "$END_COUNT" ] || fail "Partial V3 marker state" 15
[ "$START_COUNT" -le 1 ] || fail "Duplicate V3 marker state" 16

if [ "$START_COUNT" = "0" ]; then
  printf '\n' >> "$ROOT/$CSS_TARGET"
  cat "$SOURCE_APPEND" >> "$ROOT/$CSS_TARGET"
  PATCH_ACTION="APPLIED_EXECUTIVE_LUXURY_V3"
else
  PATCH_ACTION="VALIDATED_EXISTING_EXECUTIVE_LUXURY_V3"
fi

[ "$(grep -Fc "$V3_START" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "V3 start marker missing" 17
[ "$(grep -Fc "$V3_END" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "V3 end marker missing" 18

git -C "$ROOT" diff --check -- "$MAIN_TARGET" "$CSS_TARGET"

cd "$ROOT/frontend"
npm run build
cd "$ROOT"

[ -f "$DIST/index.html" ] || fail "Built dist index missing" 19
grep -RFlq "$V3_START" "$DIST/assets" || fail "V3 marker missing from dist assets" 20

rm -rf "$STAGE"
mkdir -p "$STAGE"
cp -a "$DIST/." "$STAGE/"
[ -f "$STAGE/index.html" ] || fail "Staged index missing" 21

grep -RFlq "$V3_START" "$STAGE/assets" || fail "V3 marker missing from staged assets" 22

mv "$LIVE" "$BACKUP"
if ! mv "$STAGE" "$LIVE"; then
  mv "$BACKUP" "$LIVE" || true
  fail "Failed to activate V3 live build; rollback attempted" 23
fi

if ! grep -RFlq "$V3_START" "$LIVE/assets"; then
  rm -rf "$LIVE"
  mv "$BACKUP" "$LIVE" || true
  fail "Live V3 marker missing; rolled back" 24
fi

FINAL_STATUS="$(git -C "$ROOT" status --porcelain=v1 --untracked-files=all)"
FINAL_PATHS="$(printf '%s\n' "$FINAL_STATUS" | sed '/^$/d' | cut -c4- | sort -u)"
[ "$FINAL_PATHS" = "$EXPECTED_PATHS" ] || fail "Unexpected TOS files changed" 25

FINAL_SHA="$(sha256sum "$ROOT/$CSS_TARGET" | awk '{print $1}')"
echo "PHASE02_PROJECTS_EXECUTIVE_LUXURY_V3=PASS"
echo "SCREEN=Projects"
echo "PATCH_ACTION=$PATCH_ACTION"
echo "BUILD_RESULT=PASS"
echo "LIVE_DEPLOY=PASS"
echo "DARK_MODE_PRIORITY=YES"
echo "CHANGED_FILES=$MAIN_TARGET,$CSS_TARGET"
echo "CSS_SHA256=$FINAL_SHA"
echo "BUSINESS_LOGIC_CHANGED=NO"
echo "COMMIT_CREATED=NO"
echo "PUSH_PERFORMED=NO"
echo "READY_FOR_VISUAL_REVIEW=YES"
echo "--- GIT STATUS ---"
printf '%s\n' "$FINAL_STATUS"
