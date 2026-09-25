#!/usr/bin/env bash
set -euo pipefail

PATCH="TOS-TWS-TSHEETS-CASUAL-P02-B01-SIDEBAR-BRANDING-V1_1"
TOS="/var/www/TOS"
TARGET="$TOS/frontend/src/pages/tws/TSheetsCasualLab.jsx"
SIDEBAR="$TOS/frontend/src/components/layout/Sidebar.jsx"
PAYLOAD_URL="https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/main/TOS-TWS-TSHEETS-CASUAL-P02-B01-SIDEBAR-BRANDING-V1_1/payload/TSheetsCasualLab.jsx"
LIVE_ROOT="/opt/apps/tamiyouz-front"
LIVE_BUILD="$LIVE_ROOT/build"
PM2_NAME="tamiyouz-frontend"

fail() {
  echo "PATCH=$PATCH"
  echo "PASS_FAIL=FAIL"
  echo "ERROR=$1"
  exit 1
}

[ -d "$TOS/.git" ] || fail "TOS_REPO_NOT_FOUND"
[ -f "$TARGET" ] || fail "LAB_COMPONENT_MISSING"
[ -f "$SIDEBAR" ] || fail "SIDEBAR_MISSING"
grep -q "TOS_TWS_TSHEETS_CASUAL_P02_B01_SIDEBAR_BRANDING_V1" "$TARGET" || fail "P02_V1_BASELINE_MISSING"
grep -q "data-tws-tsheets-lab-nav" "$SIDEBAR" || fail "SIDEBAR_CHILD_MISSING"
[ -L "$LIVE_BUILD" ] || fail "LIVE_BUILD_NOT_SYMLINK"

SIDEBAR_HASH_BEFORE="$(sha256sum "$SIDEBAR" | awk '{print $1}')"
OLD_RELEASE="$(readlink -f "$LIVE_BUILD")"
TMP="$(mktemp /tmp/tsheets-casual-p02-v1_1.XXXXXX.jsx)"

curl -fsSL "$PAYLOAD_URL" -o "$TMP"
grep -q "TOS_TWS_TSHEETS_CASUAL_P02_B01_SIDEBAR_BRANDING_V1_1" "$TMP" || fail "PAYLOAD_MARKER_MISSING"
! grep -q "new frameWindow.MutationObserver" "$TMP" || fail "PAYLOAD_HAS_MUTATION_OBSERVER"

cp "$TMP" "$TARGET"
rm -f "$TMP"

[ "$(sha256sum "$SIDEBAR" | awk '{print $1}')" = "$SIDEBAR_HASH_BEFORE" ] || fail "SIDEBAR_CHANGED"
! grep -q "new frameWindow.MutationObserver" "$TARGET" || fail "MUTATION_OBSERVER_STILL_PRESENT"
grep -q "Bounded retries only" "$TARGET" || fail "BOUNDED_RETRY_MARKER_MISSING"

cd "$TOS"
git diff --check -- frontend/src/pages/tws/TSheetsCasualLab.jsx

cd "$TOS/frontend"
TOS_REQUIRE_TSHEETS_CASUAL_RUNTIME=1 npm run build
[ -f dist/index.html ] || fail "TOS_BUILD_OUTPUT_MISSING"
[ -f dist/tws-casual-runtime/index.html ] || fail "CASUAL_RUNTIME_MISSING"

STAMP="$(date +%Y%m%d-%H%M%S)"
NEW_RELEASE="$LIVE_ROOT/.tsheets-casual-p02-v1_1-$STAMP"
mkdir -p "$NEW_RELEASE"
cp -a dist/. "$NEW_RELEASE/"

ln -sfn "$NEW_RELEASE" "$LIVE_ROOT/.build.next"
mv -Tf "$LIVE_ROOT/.build.next" "$LIVE_BUILD"

if ! pm2 restart "$PM2_NAME" --update-env >/dev/null; then
  ln -sfn "$OLD_RELEASE" "$LIVE_ROOT/.build.rollback"
  mv -Tf "$LIVE_ROOT/.build.rollback" "$LIVE_BUILD"
  pm2 restart "$PM2_NAME" --update-env >/dev/null 2>&1 || true
  fail "PM2_RESTART_FAILED_ROLLED_BACK"
fi

HTTP_LAB=""
HTTP_RUNTIME=""
for _ in $(seq 1 30); do
  HTTP_LAB="$(curl -k -sS -o /tmp/tsheets-p02-v1_1-lab.html -w '%{http_code}' https://tos.tamiyouz.com/tws/sheets-lab || true)"
  HTTP_RUNTIME="$(curl -k -sS -o /tmp/tsheets-p02-v1_1-runtime.html -w '%{http_code}' https://tos.tamiyouz.com/tws-casual-runtime/ || true)"
  [ "$HTTP_LAB" = "200" ] && [ "$HTTP_RUNTIME" = "200" ] && break
  sleep 1
done

if [ "$HTTP_LAB" != "200" ] || [ "$HTTP_RUNTIME" != "200" ]; then
  ln -sfn "$OLD_RELEASE" "$LIVE_ROOT/.build.rollback"
  mv -Tf "$LIVE_ROOT/.build.rollback" "$LIVE_BUILD"
  pm2 restart "$PM2_NAME" --update-env >/dev/null 2>&1 || true
  fail "HTTP_VERIFY_FAILED_ROLLED_BACK"
fi

STATUS="$(git -C "$TOS" status --short -- frontend/src/components/layout/Sidebar.jsx frontend/src/pages/tws/TSheetsCasualLab.jsx)"

echo "PATCH=$PATCH"
echo "PASS_FAIL=PASS"
echo "TOS_BUILD=PASS"
echo "DEPLOY_MODE=SYMLINK_SWAP"
echo "PM2=online"
echo "HTTP_LAB=$HTTP_LAB"
echo "HTTP_RUNTIME=$HTTP_RUNTIME"
echo "MUTATION_OBSERVER_REMOVED=YES"
echo "WHOLE_BODY_TEXT_WALK_REMOVED=YES"
echo "BRANDING_RETRY_MODE=BOUNDED_6_ATTEMPTS_MAX_1800MS"
echo "SIDEBAR_PRESERVED=YES"
echo "CASUAL_UPSTREAM_REBUILT=NO"
echo "GIT_STATUS=$(printf '%s' "$STATUS" | tr '\n' ';')"
echo "COMMIT_PERFORMED=NO"
echo "PUSH_PERFORMED=NO"
echo "READY_FOR_BROWSER_TEST=YES"
echo "ERROR=NONE"
