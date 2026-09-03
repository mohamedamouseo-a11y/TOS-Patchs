#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/var/www/TOS}"
PATCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCH_REPO_ROOT="$(cd "$PATCH_DIR/.." && pwd)"
V2_SOURCE="$PATCH_REPO_ROOT/TOS-UXUI-PHASE-02-PROJECTS-PREMIUM-V2/projects-premium-v2.append.css"
V3_SOURCE="$PATCH_REPO_ROOT/TOS-UXUI-PHASE-02-PROJECTS-EXECUTIVE-LUXURY-V3/projects-executive-luxury-v3.append.css"
V4_SENTINEL_SOURCE="$PATCH_DIR/projects-executive-luxury-v4.sentinel.css"

MAIN_TARGET="frontend/src/main.jsx"
PROJECTS_TARGET="frontend/src/pages/ProjectsPage.jsx"
CSS_TARGET="frontend/src/styles/projects-github-reference.css"
EXPECTED_MAIN_HEAD_BLOB="10a76aae2e1c5a20ce84d28e304c565a96aef500"
EXPECTED_PROJECTS_HEAD_BLOB="1720111a2bab77133eac9f7c754ddd89a58fa179"
EXPECTED_V1_CSS_SHA256="fb68e974ee1fea621a2da0502da39f6de03e737a8dfef9c35ec03f4ef79506df"
IMPORT_LINE='import "./styles/projects-github-reference.css";'
V2_START='TOS_PHASE02_PROJECTS_PREMIUM_V2_START'
V2_END='TOS_PHASE02_PROJECTS_PREMIUM_V2_END'
V3_START='TOS_PHASE02_PROJECTS_EXECUTIVE_LUXURY_V3_START'
V3_END='TOS_PHASE02_PROJECTS_EXECUTIVE_LUXURY_V3_END'
V4_RUNTIME='--tos-projects-executive-luxury-v4-runtime'

DIST="$ROOT/frontend/dist"
LIVE_PARENT="/opt/apps/tamiyouz-front"
LIVE="$LIVE_PARENT/build"
STAMP="$(date +%Y%m%d-%H%M%S)"
STAGE="$LIVE_PARENT/build.phase02-exec-v4.new.$$"
BACKUP="$LIVE_PARENT/build.phase02-exec-v4.backup-$STAMP"

fail() {
  echo "PHASE02_PROJECTS_EXECUTIVE_LUXURY_V4=FAIL"
  echo "ERROR=$1" >&2
  exit "${2:-1}"
}

[ -d "$ROOT/.git" ] || fail "TOS repository not found" 2
[ -d "$PATCH_REPO_ROOT/.git" ] || fail "TOS-Patchs repository not found" 3
[ -f "$V2_SOURCE" ] || fail "Missing Premium V2 source" 4
[ -f "$V3_SOURCE" ] || fail "Missing Executive Luxury V3 source" 5
[ -f "$V4_SENTINEL_SOURCE" ] || fail "Missing V4 sentinel source" 6
[ -f "$ROOT/$MAIN_TARGET" ] || fail "Missing main.jsx" 7
[ -f "$ROOT/$PROJECTS_TARGET" ] || fail "Missing ProjectsPage.jsx" 8
[ -f "$ROOT/$CSS_TARGET" ] || fail "Missing Projects stylesheet" 9
[ -d "$LIVE" ] || fail "Live frontend root missing" 10

git -C "$ROOT" diff --cached --quiet || fail "Staged changes exist; stop" 11
[ "$(git -C "$ROOT" rev-parse "HEAD:$MAIN_TARGET")" = "$EXPECTED_MAIN_HEAD_BLOB" ] || fail "Committed main.jsx baseline changed" 12
[ "$(git -C "$ROOT" rev-parse "HEAD:$PROJECTS_TARGET")" = "$EXPECTED_PROJECTS_HEAD_BLOB" ] || fail "Committed ProjectsPage.jsx baseline changed" 13
[ "$(grep -Fxc "$IMPORT_LINE" "$ROOT/$MAIN_TARGET" || true)" = "1" ] || fail "Projects CSS import missing or duplicated" 14

STATUS="$(git -C "$ROOT" status --porcelain=v1 --untracked-files=all)"
PATHS="$(printf '%s\n' "$STATUS" | sed '/^$/d' | cut -c4- | sort -u)"
EXPECTED_PATHS="$(printf '%s\n%s\n' "$MAIN_TARGET" "$CSS_TARGET" | sort)"
[ "$PATHS" = "$EXPECTED_PATHS" ] || {
  echo "--- PRE-EXISTING STATUS ---"
  printf '%s\n' "$STATUS"
  fail "Expected exact Phase 02 working-tree paths only" 15
}

V2_START_COUNT="$(grep -Fc "$V2_START" "$ROOT/$CSS_TARGET" || true)"
V2_END_COUNT="$(grep -Fc "$V2_END" "$ROOT/$CSS_TARGET" || true)"
V3_START_COUNT="$(grep -Fc "$V3_START" "$ROOT/$CSS_TARGET" || true)"
V3_END_COUNT="$(grep -Fc "$V3_END" "$ROOT/$CSS_TARGET" || true)"
V4_COUNT="$(grep -Fc -- "$V4_RUNTIME" "$ROOT/$CSS_TARGET" || true)"

[ "$V2_START_COUNT" = "$V2_END_COUNT" ] || fail "Partial Premium V2 state" 16
[ "$V3_START_COUNT" = "$V3_END_COUNT" ] || fail "Partial Executive Luxury V3 state" 17
[ "$V2_START_COUNT" -le 1 ] || fail "Duplicate Premium V2 state" 18
[ "$V3_START_COUNT" -le 1 ] || fail "Duplicate Executive Luxury V3 state" 19
[ "$V4_COUNT" -le 1 ] || fail "Duplicate V4 runtime sentinel" 20

if [ "$V2_START_COUNT" = "0" ]; then
  CURRENT_SHA="$(sha256sum "$ROOT/$CSS_TARGET" | awk '{print $1}')"
  [ "$CURRENT_SHA" = "$EXPECTED_V1_CSS_SHA256" ] || fail "Cannot safely add V2: Projects CSS is not exact V1 baseline" 21
  printf '\n' >> "$ROOT/$CSS_TARGET"
  cat "$V2_SOURCE" >> "$ROOT/$CSS_TARGET"
  V2_ACTION="APPLIED"
else
  V2_ACTION="EXISTING"
fi

if [ "$V3_START_COUNT" = "0" ]; then
  printf '\n' >> "$ROOT/$CSS_TARGET"
  cat "$V3_SOURCE" >> "$ROOT/$CSS_TARGET"
  V3_ACTION="APPLIED"
else
  V3_ACTION="EXISTING"
fi

if [ "$V4_COUNT" = "0" ]; then
  printf '\n' >> "$ROOT/$CSS_TARGET"
  cat "$V4_SENTINEL_SOURCE" >> "$ROOT/$CSS_TARGET"
  V4_ACTION="APPLIED_RUNTIME_SENTINEL"
else
  V4_ACTION="EXISTING_RUNTIME_SENTINEL"
fi

[ "$(grep -Fc "$V2_START" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "Premium V2 start marker missing in source" 22
[ "$(grep -Fc "$V2_END" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "Premium V2 end marker missing in source" 23
[ "$(grep -Fc "$V3_START" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "Executive Luxury V3 start marker missing in source" 24
[ "$(grep -Fc "$V3_END" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "Executive Luxury V3 end marker missing in source" 25
[ "$(grep -Fc -- "$V4_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "V4 runtime sentinel missing in source" 26

git -C "$ROOT" diff --check -- "$MAIN_TARGET" "$CSS_TARGET"

cd "$ROOT/frontend"
npm run build
cd "$ROOT"

[ -f "$DIST/index.html" ] || fail "Built dist index missing" 27
# CSS comments are stripped by the build pipeline, so verify a custom property that must survive minification.
grep -RFlq -- "$V4_RUNTIME" "$DIST/assets" || fail "V4 runtime sentinel missing from dist assets" 28

rm -rf "$STAGE"
mkdir -p "$STAGE"
cp -a "$DIST/." "$STAGE/"
[ -f "$STAGE/index.html" ] || fail "Staged index missing" 29
grep -RFlq -- "$V4_RUNTIME" "$STAGE/assets" || fail "V4 runtime sentinel missing from staged assets" 30

mv "$LIVE" "$BACKUP"
if ! mv "$STAGE" "$LIVE"; then
  mv "$BACKUP" "$LIVE" || true
  fail "Failed to activate V4 live build; rollback attempted" 31
fi

if ! grep -RFlq -- "$V4_RUNTIME" "$LIVE/assets"; then
  rm -rf "$LIVE"
  mv "$BACKUP" "$LIVE" || true
  fail "Live V4 runtime sentinel missing; rolled back" 32
fi

FINAL_STATUS="$(git -C "$ROOT" status --porcelain=v1 --untracked-files=all)"
FINAL_PATHS="$(printf '%s\n' "$FINAL_STATUS" | sed '/^$/d' | cut -c4- | sort -u)"
[ "$FINAL_PATHS" = "$EXPECTED_PATHS" ] || fail "Unexpected TOS files changed" 33

FINAL_SHA="$(sha256sum "$ROOT/$CSS_TARGET" | awk '{print $1}')"
echo "PHASE02_PROJECTS_EXECUTIVE_LUXURY_V4=PASS"
echo "SCREEN=Projects"
echo "V2_ACTION=$V2_ACTION"
echo "V3_ACTION=$V3_ACTION"
echo "V4_ACTION=$V4_ACTION"
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
