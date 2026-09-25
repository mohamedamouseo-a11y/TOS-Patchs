#!/usr/bin/env bash
set -euo pipefail

PATCH="TOS-TWS-TSHEETS-CASUAL-P01-B01-SIDE-BY-SIDE-INTEGRATION-V1"
TOS="/var/www/TOS"
UPSTREAM="$TOS/vendor/tsheets-casual-upstream"
UPSTREAM_SHA="87a63902d94c85b3c50d3210055373a3d3bae991"
PATCH_URL="https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/main/TOS-TWS-TSHEETS-CASUAL-P01-B01-SIDE-BY-SIDE-INTEGRATION-V1"
PREVIEW_BASE="/tws-casual-runtime/"
LIVE_ROOT="/opt/apps/tamiyouz-front"
LIVE_BUILD="$LIVE_ROOT/build"
PM2_NAME="tamiyouz-frontend"
CREATED_LINKS=()
LIVE_BACKUP=""
LIVE_WAS_SYMLINK="NO"
OLD_LINK_TARGET=""

fail() {
  echo "PATCH=$PATCH"
  echo "PASS_FAIL=FAIL"
  echo "ERROR=$1"
  exit 1
}

cleanup_links() {
  local p
  for p in "${CREATED_LINKS[@]:-}"; do
    [ -L "$p" ] && rm -f "$p" || true
  done
  rmdir "$UPSTREAM/vendor/design-system/node_modules/@types" 2>/dev/null || true
  rmdir "$UPSTREAM/vendor/design-system/node_modules" 2>/dev/null || true
}

cleanup() {
  cleanup_links
  if [ -f "$UPSTREAM/scripts/swap-fork-pkgs.mjs" ]; then
    node "$UPSTREAM/scripts/swap-fork-pkgs.mjs" --restore >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

[ -d "$TOS/.git" ] || fail "TOS_REPO_NOT_FOUND"
[ -d "$UPSTREAM/.git" ] || fail "P00_SOURCE_NOT_FOUND"
[ "$(git -C "$UPSTREAM" rev-parse HEAD)" = "$UPSTREAM_SHA" ] || fail "UPSTREAM_SHA_MISMATCH"
command -v curl >/dev/null 2>&1 || fail "CURL_NOT_FOUND"
command -v pm2 >/dev/null 2>&1 || fail "PM2_NOT_FOUND"
pm2 describe "$PM2_NAME" >/dev/null 2>&1 || fail "PM2_FRONTEND_NOT_FOUND"
[ -d "$LIVE_BUILD" ] || [ -L "$LIVE_BUILD" ] || fail "LIVE_BUILD_NOT_FOUND"

TMPDIR="$(mktemp -d /tmp/tsheets-casual-p01-b01.XXXXXX)"
trap 'cleanup; rm -rf "$TMPDIR"' EXIT

curl -fsSL "$PATCH_URL/apply.py" -o "$TMPDIR/apply.py"
curl -fsSL "$PATCH_URL/payload/TSheetsCasualLab.jsx" -o "$TMPDIR/TSheetsCasualLab.jsx"
curl -fsSL "$PATCH_URL/payload/syncTsheetsCasualRuntime.mjs" -o "$TMPDIR/syncTsheetsCasualRuntime.mjs"

python3 "$TMPDIR/apply.py"

mkdir -p "$TOS/frontend/src/pages/tws" "$TOS/frontend/scripts"
if [ -e "$TOS/frontend/src/pages/tws/TSheetsCasualLab.jsx" ] && ! grep -q "TOS_TWS_TSHEETS_CASUAL_P01_B01_SIDE_BY_SIDE_INTEGRATION_V1" "$TOS/frontend/src/pages/tws/TSheetsCasualLab.jsx"; then
  fail "UNEXPECTED_EXISTING_LAB_COMPONENT"
fi
if [ -e "$TOS/frontend/scripts/syncTsheetsCasualRuntime.mjs" ] && ! grep -q "TSheets Casual runtime not found" "$TOS/frontend/scripts/syncTsheetsCasualRuntime.mjs"; then
  fail "UNEXPECTED_EXISTING_RUNTIME_SYNC_SCRIPT"
fi
cp "$TMPDIR/TSheetsCasualLab.jsx" "$TOS/frontend/src/pages/tws/TSheetsCasualLab.jsx"
cp "$TMPDIR/syncTsheetsCasualRuntime.mjs" "$TOS/frontend/scripts/syncTsheetsCasualRuntime.mjs"

cd "$UPSTREAM"
corepack enable >/dev/null 2>&1 || true
corepack prepare pnpm@10.33.4 --activate >/dev/null
[ -d "$UPSTREAM/packages/sdk/dist" ] || fail "P00_SDK_BUILD_MISSING"
[ -f "$UPSTREAM/vendor/univer-revamp/packages/core/lib/es/index.js" ] || fail "P00_UNIVER_BUILD_MISSING"

node "$UPSTREAM/scripts/swap-fork-pkgs.mjs"

WEB_NM="$UPSTREAM/apps/web/node_modules"
for required in "$WEB_NM/react" "$WEB_NM/react-dom" "$WEB_NM/@types/react" "$WEB_NM/@types/react-dom"; do
  [ -e "$required" ] || fail "EXPECTED_WEB_PEER_MISSING:$required"
done

DS_NM="$UPSTREAM/vendor/design-system/node_modules"
mkdir -p "$DS_NM/@types"

link_peer() {
  local source="$1"
  local dest="$2"
  [ ! -e "$dest" ] && [ ! -L "$dest" ] || fail "TEMP_PEER_ALREADY_EXISTS:$dest"
  ln -s "$source" "$dest"
  CREATED_LINKS+=("$dest")
}

link_peer "$WEB_NM/react" "$DS_NM/react"
link_peer "$WEB_NM/react-dom" "$DS_NM/react-dom"
link_peer "$WEB_NM/@types/react" "$DS_NM/@types/react"
link_peer "$WEB_NM/@types/react-dom" "$DS_NM/@types/react-dom"

PAGES_BASE="$PREVIEW_BASE" NODE_OPTIONS=--max-old-space-size=4096 pnpm --filter @sheet/web build
grep -q "$PREVIEW_BASE" "$UPSTREAM/apps/web/dist/index.html" || fail "UPSTREAM_BASE_PATH_NOT_APPLIED"

cleanup_links
node "$UPSTREAM/scripts/swap-fork-pkgs.mjs" --restore
[ -z "$(git -C "$UPSTREAM" status --porcelain=v1 --untracked-files=no)" ] || fail "UPSTREAM_TRACKED_SOURCE_DIRTY"

cd "$TOS/frontend"
TOS_REQUIRE_TSHEETS_CASUAL_RUNTIME=1 npm run build
[ -f "$TOS/frontend/dist/index.html" ] || fail "TOS_DIST_INDEX_MISSING"
[ -f "$TOS/frontend/dist/tws-casual-runtime/index.html" ] || fail "CASUAL_RUNTIME_NOT_SYNCED_TO_TOS_DIST"

STAMP="$(date +%Y%m%d-%H%M%S)"
NEW_RELEASE="$LIVE_ROOT/.tsheets-casual-p01-$STAMP"
mkdir -p "$NEW_RELEASE"
cp -a "$TOS/frontend/dist/." "$NEW_RELEASE/"

rollback_live() {
  set +e
  if [ "$LIVE_WAS_SYMLINK" = "YES" ] && [ -n "$OLD_LINK_TARGET" ]; then
    ln -sfn "$OLD_LINK_TARGET" "$LIVE_ROOT/.build.rollback"
    mv -Tf "$LIVE_ROOT/.build.rollback" "$LIVE_BUILD"
  elif [ -n "$LIVE_BACKUP" ] && [ -d "$LIVE_BACKUP" ]; then
    rm -rf "$LIVE_BUILD"
    mv "$LIVE_BACKUP" "$LIVE_BUILD"
  fi
  pm2 restart "$PM2_NAME" --update-env >/dev/null 2>&1 || true
}

if [ -L "$LIVE_BUILD" ]; then
  LIVE_WAS_SYMLINK="YES"
  OLD_LINK_TARGET="$(readlink -f "$LIVE_BUILD")"
  ln -sfn "$NEW_RELEASE" "$LIVE_ROOT/.build.next"
  mv -Tf "$LIVE_ROOT/.build.next" "$LIVE_BUILD"
  DEPLOY_MODE="SYMLINK_SWAP"
else
  LIVE_BACKUP="$LIVE_ROOT/.build.prev-$STAMP"
  mv "$LIVE_BUILD" "$LIVE_BACKUP"
  if ! mv "$NEW_RELEASE" "$LIVE_BUILD"; then
    mv "$LIVE_BACKUP" "$LIVE_BUILD" || true
    fail "ATOMIC_SWAP_FAILED"
  fi
  DEPLOY_MODE="DIRECTORY_SWAP"
fi

if ! pm2 restart "$PM2_NAME" --update-env >/dev/null; then
  rollback_live
  fail "PM2_RESTART_FAILED_ROLLED_BACK"
fi

HTTP_MAIN=""
HTTP_RUNTIME=""
for _ in $(seq 1 30); do
  HTTP_MAIN="$(curl -k -sS -o /tmp/tsheets-p01-main.html -w '%{http_code}' https://tos.tamiyouz.com/tws/sheets-lab || true)"
  HTTP_RUNTIME="$(curl -k -sS -o /tmp/tsheets-p01-runtime.html -w '%{http_code}' https://tos.tamiyouz.com/tws-casual-runtime/ || true)"
  [ "$HTTP_MAIN" = "200" ] && [ "$HTTP_RUNTIME" = "200" ] && break
  sleep 1
done

if [ "$HTTP_MAIN" != "200" ] || [ "$HTTP_RUNTIME" != "200" ]; then
  rollback_live
  fail "HTTP_VERIFY_FAILED_MAIN_${HTTP_MAIN}_RUNTIME_${HTTP_RUNTIME}_ROLLED_BACK"
fi

grep -qi '<!doctype html' /tmp/tsheets-p01-runtime.html || { rollback_live; fail "RUNTIME_HTML_INVALID_ROLLED_BACK"; }

if [ "$LIVE_WAS_SYMLINK" = "YES" ]; then
  DEPLOY_REF="$NEW_RELEASE"
else
  DEPLOY_REF="$LIVE_BUILD"
fi

echo "PATCH=$PATCH"
echo "PHASE=P01"
echo "BATCH=B01"
echo "VERSION=V1"
echo "PASS_FAIL=PASS"
echo "ROUTE=/tws/sheets-lab"
echo "RUNTIME_PATH=/tws-casual-runtime/"
echo "UPSTREAM_BASE_BUILD=PASS"
echo "TOS_BUILD=PASS"
echo "RUNTIME_SYNC=PASS"
echo "DEPLOY_MODE=$DEPLOY_MODE"
echo "DEPLOY_REF=$DEPLOY_REF"
echo "PM2=online"
echo "HTTP_ROUTE=$HTTP_MAIN"
echo "HTTP_RUNTIME=$HTTP_RUNTIME"
echo "OLD_TSHEETS_PRESERVED=YES"
echo "SIDEBAR_CHANGED=NO"
echo "BRANDING_CHANGED=NO"
echo "BACKEND_CHANGED=NO"
echo "DATABASE_CHANGED=NO"
echo "COMMIT_PERFORMED=NO"
echo "PUSH_PERFORMED=NO"
echo "READY_FOR_BROWSER_TEST=YES"
echo "NEXT=P02-B01-TWS-SIDEBAR-AND-BRANDING-V1"
echo "ERROR=NONE"
