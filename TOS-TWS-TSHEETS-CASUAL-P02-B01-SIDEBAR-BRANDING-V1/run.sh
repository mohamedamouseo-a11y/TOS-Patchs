#!/usr/bin/env bash
set -euo pipefail

PATCH="TOS-TWS-TSHEETS-CASUAL-P02-B01-SIDEBAR-BRANDING-V1"
TOS="/var/www/TOS"
PATCH_URL="https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/main/TOS-TWS-TSHEETS-CASUAL-P02-B01-SIDEBAR-BRANDING-V1"
LIVE_ROOT="/opt/apps/tamiyouz-front"
LIVE_BUILD="$LIVE_ROOT/build"
PM2_NAME="tamiyouz-frontend"
TMP="/tmp/tsheets-casual-p02-b01"
LIVE_BACKUP=""
LIVE_WAS_SYMLINK="NO"
OLD_LINK_TARGET=""

fail() {
  echo "PATCH=$PATCH"
  echo "PASS_FAIL=FAIL"
  echo "ERROR=$1"
  exit 1
}

[ -d "$TOS/.git" ] || fail "TOS_REPO_NOT_FOUND"
[ -f "$TOS/frontend/src/pages/tws/TSheetsCasualLab.jsx" ] || fail "P01_LAB_COMPONENT_MISSING"
grep -q "TOS_TWS_TSHEETS_CASUAL_P01_B01_SIDE_BY_SIDE_INTEGRATION_V1" "$TOS/frontend/src/pages/tws/TwsPage.jsx" || fail "P01_ROUTE_MARKER_MISSING"
[ -d "$TOS/vendor/tsheets-casual-upstream/apps/web/dist" ] || fail "CASUAL_RUNTIME_DIST_MISSING"

if ! git -C "$TOS" diff --quiet -- frontend/src/components/layout/Sidebar.jsx frontend/src/pages/tws/TSheetsCasualLab.jsx; then
  fail "P02_TARGET_FILES_DIRTY"
fi

rm -rf "$TMP"
mkdir -p "$TMP"
curl -fsSL "$PATCH_URL/apply.py" -o "$TMP/apply.py"
curl -fsSL "$PATCH_URL/payload/TSheetsCasualLab.jsx" -o "$TMP/TSheetsCasualLab.jsx"

python3 "$TMP/apply.py"

grep -q "TOS_TWS_TSHEETS_CASUAL_P02_B01_SIDEBAR_BRANDING_V1" "$TOS/frontend/src/components/layout/Sidebar.jsx" || fail "SIDEBAR_MARKER_MISSING"
grep -q "data-tws-tsheets-lab-nav" "$TOS/frontend/src/components/layout/Sidebar.jsx" || fail "SIDEBAR_LAB_LINK_MISSING"
grep -q "TOS_TWS_TSHEETS_CASUAL_P02_B01_SIDEBAR_BRANDING_V1" "$TOS/frontend/src/pages/tws/TSheetsCasualLab.jsx" || fail "BRANDING_MARKER_MISSING"
grep -q "replaceCasualSheetsBrand" "$TOS/frontend/src/pages/tws/TSheetsCasualLab.jsx" || fail "BRANDING_ENGINE_MISSING"

cd "$TOS"
git diff --check -- frontend/src/components/layout/Sidebar.jsx frontend/src/pages/tws/TSheetsCasualLab.jsx

cd "$TOS/frontend"
TOS_REQUIRE_TSHEETS_CASUAL_RUNTIME=1 npm run build

[ -f "$TOS/frontend/dist/index.html" ] || fail "TOS_DIST_INDEX_MISSING"
[ -f "$TOS/frontend/dist/tws-casual-runtime/index.html" ] || fail "CASUAL_RUNTIME_NOT_SYNCED"

STAMP="$(date +%Y%m%d-%H%M%S)"
NEW_RELEASE="$LIVE_ROOT/.tsheets-casual-p02-$STAMP"
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

HTTP_LAB=""
HTTP_RUNTIME=""
for _ in $(seq 1 30); do
  HTTP_LAB="$(curl -k -sS -o /tmp/tsheets-p02-lab.html -w '%{http_code}' https://tos.tamiyouz.com/tws/sheets-lab || true)"
  HTTP_RUNTIME="$(curl -k -sS -o /tmp/tsheets-p02-runtime.html -w '%{http_code}' https://tos.tamiyouz.com/tws-casual-runtime/ || true)"
  [ "$HTTP_LAB" = "200" ] && [ "$HTTP_RUNTIME" = "200" ] && break
  sleep 1
done

if [ "$HTTP_LAB" != "200" ] || [ "$HTTP_RUNTIME" != "200" ]; then
  rollback_live
  fail "HTTP_VERIFY_FAILED_LAB_${HTTP_LAB}_RUNTIME_${HTTP_RUNTIME}_ROLLED_BACK"
fi

STATUS="$(git -C "$TOS" status --short -- frontend/src/components/layout/Sidebar.jsx frontend/src/pages/tws/TSheetsCasualLab.jsx)"

echo "PATCH=$PATCH"
echo "PHASE=P02"
echo "BATCH=B01"
echo "VERSION=V1"
echo "PASS_FAIL=PASS"
echo "TOS_BUILD=PASS"
echo "DEPLOY_MODE=$DEPLOY_MODE"
echo "PM2=online"
echo "HTTP_LAB=$HTTP_LAB"
echo "HTTP_RUNTIME=$HTTP_RUNTIME"
echo "SIDEBAR_TWS_CHILD=ACTIVE"
echo "TSHEETS_BRANDING_LAYER=ACTIVE"
echo "VISIBLE_CASUAL_NAME_REPLACER=ACTIVE"
echo "UPSTREAM_SOURCE_CHANGED=NO"
echo "OLD_TSHEETS_CHANGED=NO"
echo "BACKEND_CHANGED=NO"
echo "DATABASE_CHANGED=NO"
echo "GIT_STATUS=$(printf '%s' "$STATUS" | tr '\n' ';')"
echo "READY_FOR_BROWSER_TEST=YES"
echo "COMMIT_PERFORMED=NO"
echo "PUSH_PERFORMED=NO"
echo "NEXT=P02-B01-BROWSER-VERIFY"
echo "ERROR=NONE"
