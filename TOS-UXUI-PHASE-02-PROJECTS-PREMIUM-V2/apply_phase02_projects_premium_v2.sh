#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/var/www/TOS}"
PATCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_APPEND="$PATCH_DIR/projects-premium-v2.append.css"
MAIN_TARGET="frontend/src/main.jsx"
PROJECTS_TARGET="frontend/src/pages/ProjectsPage.jsx"
CSS_TARGET="frontend/src/styles/projects-github-reference.css"
EXPECTED_MAIN_HEAD_BLOB="10a76aae2e1c5a20ce84d28e304c565a96aef500"
EXPECTED_PROJECTS_HEAD_BLOB="1720111a2bab77133eac9f7c754ddd89a58fa179"
EXPECTED_V1_CSS_SHA256="fb68e974ee1fea621a2da0502da39f6de03e737a8dfef9c35ec03f4ef79506df"
IMPORT_LINE='import "./styles/projects-github-reference.css";'
V2_START='TOS_PHASE02_PROJECTS_PREMIUM_V2_START'
V2_END='TOS_PHASE02_PROJECTS_PREMIUM_V2_END'
DIST="$ROOT/frontend/dist"
LIVE_PARENT="/opt/apps/tamiyouz-front"
LIVE="$LIVE_PARENT/build"
STAMP="$(date +%Y%m%d-%H%M%S)"
STAGE="$LIVE_PARENT/build.phase02-premium-v2.new.$$"
BACKUP="$LIVE_PARENT/build.phase02-premium-v2.backup-$STAMP"

fail() {
  echo "PHASE02_PROJECTS_PREMIUM_V2=FAIL"
  echo "ERROR=$1" >&2
  exit "${2:-1}"
}

[ -d "$ROOT/.git" ] || fail "TOS repository not found" 2
[ -f "$SOURCE_APPEND" ] || fail "Missing premium V2 CSS source" 3
[ -f "$ROOT/$MAIN_TARGET" ] || fail "Missing main.jsx" 4
[ -f "$ROOT/$PROJECTS_TARGET" ] || fail "Missing ProjectsPage.jsx" 5
[ -f "$ROOT/$CSS_TARGET" ] || fail "Missing Phase 02 Projects stylesheet" 6
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
  fail "Expected exact Phase 02 V1 working-tree state only" 12
}

START_COUNT="$(grep -Fc "$V2_START" "$ROOT/$CSS_TARGET" || true)"
END_COUNT="$(grep -Fc "$V2_END" "$ROOT/$CSS_TARGET" || true)"
[ "$START_COUNT" = "$END_COUNT" ] || fail "Partial premium V2 marker state" 13
[ "$START_COUNT" -le 1 ] || fail "Duplicate premium V2 marker state" 14

if [ "$START_COUNT" = "0" ]; then
  CURRENT_SHA="$(sha256sum "$ROOT/$CSS_TARGET" | awk '{print $1}')"
  echo "CURRENT_CSS_SHA256=$CURRENT_SHA"
  [ "$CURRENT_SHA" = "$EXPECTED_V1_CSS_SHA256" ] || fail "Projects CSS is not exact V1 baseline" 15
  printf '\n' >> "$ROOT/$CSS_TARGET"
  cat "$SOURCE_APPEND" >> "$ROOT/$CSS_TARGET"
  PATCH_ACTION="APPLIED_PREMIUM_V2"
else
  PATCH_ACTION="VALIDATED_EXISTING_PREMIUM_V2"
fi

[ "$(grep -Fc "$V2_START" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "Premium V2 start marker missing" 16
[ "$(grep -Fc "$V2_END" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "Premium V2 end marker missing" 17

git -C "$ROOT" diff --check -- "$MAIN_TARGET" "$CSS_TARGET"

cd "$ROOT/frontend"
npm run build
cd "$ROOT"

[ -f "$DIST/index.html" ] || fail "Built dist index missing" 18
grep -RFlq 'TOS_PHASE02_PROJECTS_PREMIUM_V2_START' "$DIST/assets" || fail "Premium V2 marker missing from dist assets" 19

rm -rf "$STAGE"
mkdir -p "$STAGE"
cp -a "$DIST/." "$STAGE/"
[ -f "$STAGE/index.html" ] || fail "Staged index missing" 20

mv "$LIVE" "$BACKUP"
if ! mv "$STAGE" "$LIVE"; then
  mv "$BACKUP" "$LIVE" || true
  fail "Failed to activate premium V2 live build; rollback attempted" 21
fi

if ! grep -RFlq 'TOS_PHASE02_PROJECTS_PREMIUM_V2_START' "$LIVE/assets"; then
  rm -rf "$LIVE"
  mv "$BACKUP" "$LIVE" || true
  fail "Live premium V2 marker missing; rolled back" 22
fi

FINAL_STATUS="$(git -C "$ROOT" status --porcelain=v1 --untracked-files=all)"
FINAL_PATHS="$(printf '%s\n' "$FINAL_STATUS" | sed '/^$/d' | cut -c4- | sort -u)"
[ "$FINAL_PATHS" = "$EXPECTED_PATHS" ] || fail "Unexpected TOS files changed" 23

FINAL_SHA="$(sha256sum "$ROOT/$CSS_TARGET" | awk '{print $1}')"
echo "PHASE02_PROJECTS_PREMIUM_V2=PASS"
echo "SCREEN=Projects"
echo "PATCH_ACTION=$PATCH_ACTION"
echo "BUILD_RESULT=PASS"
echo "LIVE_DEPLOY=PASS"
echo "CHANGED_FILES=$MAIN_TARGET,$CSS_TARGET"
echo "CSS_SHA256=$FINAL_SHA"
echo "BUSINESS_LOGIC_CHANGED=NO"
echo "COMMIT_CREATED=NO"
echo "PUSH_PERFORMED=NO"
echo "READY_FOR_VISUAL_REVIEW=YES"
echo "--- GIT STATUS ---"
printf '%s\n' "$FINAL_STATUS"
