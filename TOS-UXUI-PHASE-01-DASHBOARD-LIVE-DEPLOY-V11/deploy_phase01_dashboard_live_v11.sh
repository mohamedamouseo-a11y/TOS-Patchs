#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/var/www/TOS}"
DIST="$ROOT/frontend/dist"
LIVE_PARENT="/opt/apps/tamiyouz-front"
LIVE="$LIVE_PARENT/build"
STAMP="$(date +%Y%m%d-%H%M%S)"
STAGE="$LIVE_PARENT/build.phase01-v11.new.$$"
BACKUP="$LIVE_PARENT/build.phase01-v11.backup-$STAMP"

fail() {
  echo "PHASE01_DASHBOARD_LIVE_DEPLOY_V11=FAIL"
  echo "ERROR=$1" >&2
  exit "${2:-1}"
}

[ -d "$ROOT/.git" ] || fail "TOS repository not found at $ROOT" 2
[ -d "$ROOT/frontend" ] || fail "Frontend directory missing" 3
[ -d "$LIVE_PARENT" ] || fail "Live frontend parent missing: $LIVE_PARENT" 4
[ -d "$LIVE" ] || fail "Live build root missing: $LIVE" 5
[ -f "$LIVE/index.html" ] || fail "Live build index.html missing" 6

# V9 working-tree state must be present; do not reset/stash it.
git -C "$ROOT" diff --cached --quiet || fail "Staged changes exist; stop" 7
STATUS="$(git -C "$ROOT" status --porcelain=v1 --untracked-files=all)"
for p in \
  "frontend/src/main.jsx" \
  "frontend/src/pages/Dashboard.jsx" \
  "frontend/src/pages/tws/TwsRecentFilesWidget.jsx" \
  "frontend/src/styles/dashboard-github-reference.css"; do
  printf '%s\n' "$STATUS" | grep -Fq "$p" || fail "Expected Phase 01 working-tree file missing from status: $p" 8
done

# Build the current Phase 01 source.
cd "$ROOT/frontend"
npm run build
cd "$ROOT"

[ -f "$DIST/index.html" ] || fail "Vite dist index.html missing after build" 9

grep -RFlq 'tos-dashboard-dark-card' "$DIST/assets" || fail "Dashboard V9 marker missing from dist assets" 10
grep -RFlq '#1d2b36' "$DIST/assets" || fail "Dashboard dark color marker missing from dist assets" 11

rm -rf "$STAGE"
mkdir -p "$STAGE"
cp -a "$DIST/." "$STAGE/"
[ -f "$STAGE/index.html" ] || fail "Staged live index missing" 12
grep -RFlq 'tos-dashboard-dark-card' "$STAGE/assets" || fail "Dashboard marker missing from staged live assets" 13

# Safe directory swap with rollback.
mv "$LIVE" "$BACKUP"
if ! mv "$STAGE" "$LIVE"; then
  mv "$BACKUP" "$LIVE" || true
  fail "Failed to activate staged live build; rollback attempted" 14
fi

# Verify activated live root.
[ -f "$LIVE/index.html" ] || {
  rm -rf "$LIVE"
  mv "$BACKUP" "$LIVE" || true
  fail "Activated live build missing index.html; rolled back" 15
}
if ! grep -RFlq 'tos-dashboard-dark-card' "$LIVE/assets"; then
  rm -rf "$LIVE"
  mv "$BACKUP" "$LIVE" || true
  fail "Activated live build missing Dashboard marker; rolled back" 16
fi
if ! grep -RFlq '#1d2b36' "$LIVE/assets"; then
  rm -rf "$LIVE"
  mv "$BACKUP" "$LIVE" || true
  fail "Activated live build missing dark color marker; rolled back" 17
fi

DIST_ASSETS="$(grep -oE '/assets/[^\" ]+' "$DIST/index.html" | tr '\n' ',' || true)"
LIVE_ASSETS="$(grep -oE '/assets/[^\" ]+' "$LIVE/index.html" | tr '\n' ',' || true)"
[ "$DIST_ASSETS" = "$LIVE_ASSETS" ] || fail "Live index assets do not match freshly built dist" 18

FINAL_STATUS="$(git -C "$ROOT" status --porcelain=v1 --untracked-files=all)"
[ "$FINAL_STATUS" = "$STATUS" ] || fail "TOS git working tree changed during live deployment" 19

echo "PHASE01_DASHBOARD_LIVE_DEPLOY_V11=PASS"
echo "BUILD_RESULT=PASS"
echo "SOURCE_DIST=$DIST"
echo "LIVE_ROOT=$LIVE"
echo "BACKUP_ROOT=$BACKUP"
echo "LIVE_MARKER=PASS:tos-dashboard-dark-card"
echo "LIVE_DARK_COLOR=PASS:#1d2b36"
echo "DIST_INDEX_ASSETS=$DIST_ASSETS"
echo "LIVE_INDEX_ASSETS=$LIVE_ASSETS"
echo "TOS_GIT_STATUS_UNCHANGED=YES"
echo "COMMIT_CREATED=NO"
echo "PUSH_PERFORMED=NO"
echo "READY_FOR_VISUAL_REVIEW=YES"
echo "--- GIT STATUS ---"
printf '%s\n' "$FINAL_STATUS"
