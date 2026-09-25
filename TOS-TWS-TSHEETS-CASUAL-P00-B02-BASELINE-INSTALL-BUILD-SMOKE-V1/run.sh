#!/usr/bin/env bash
set -euo pipefail

PATCH="TOS-TWS-TSHEETS-CASUAL-P00-B02-BASELINE-INSTALL-BUILD-SMOKE-V1"
TOS="/var/www/TOS"
TARGET="$TOS/vendor/tsheets-casual-upstream"
UPSTREAM_SHA="87a63902d94c85b3c50d3210055373a3d3bae991"
PREVIEW_PORT="4173"
PREVIEW_PID=""

fail() {
  echo "PATCH=$PATCH"
  echo "PASS_FAIL=FAIL"
  echo "ERROR=$1"
  exit 1
}

cleanup() {
  if [ -n "$PREVIEW_PID" ] && kill -0 "$PREVIEW_PID" 2>/dev/null; then
    kill "$PREVIEW_PID" 2>/dev/null || true
    wait "$PREVIEW_PID" 2>/dev/null || true
  fi
  if [ -f "$TARGET/scripts/swap-fork-pkgs.mjs" ]; then
    node "$TARGET/scripts/swap-fork-pkgs.mjs" --restore >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

[ -d "$TOS/.git" ] || fail "TOS_REPO_NOT_FOUND"
[ -d "$TARGET/.git" ] || fail "P00_B01_SOURCE_NOT_FOUND"

HEAD_SHA="$(git -C "$TARGET" rev-parse HEAD)"
[ "$HEAD_SHA" = "$UPSTREAM_SHA" ] || fail "UPSTREAM_SHA_MISMATCH:$HEAD_SHA"

SUBMODULE_STATUS="$(git -C "$TARGET" submodule status --recursive)"
if printf '%s\n' "$SUBMODULE_STATUS" | grep -Eq '^[+-]'; then fail "SUBMODULE_PIN_MISMATCH"; fi
if printf '%s\n' "$SUBMODULE_STATUS" | grep -Eq '^-' ; then fail "SUBMODULE_NOT_INITIALIZED"; fi

command -v node >/dev/null 2>&1 || fail "NODE_NOT_FOUND"
command -v corepack >/dev/null 2>&1 || fail "COREPACK_NOT_FOUND"
NODE_VERSION="$(node -p 'process.versions.node')"
node -e 'const [a,b]=process.versions.node.split(".").map(Number); if(a<18 || (a===18 && b<17)) process.exit(1)' || fail "NODE_TOO_OLD:$NODE_VERSION"

TRACKED_BEFORE="$(git -C "$TOS" diff --no-ext-diff --binary HEAD -- . ':!vendor/tsheets-casual-upstream' | sha256sum | awk '{print $1}')"
STAGED_BEFORE="$(git -C "$TOS" diff --cached --no-ext-diff --binary HEAD -- . ':!vendor/tsheets-casual-upstream' | sha256sum | awk '{print $1}')"

cd "$TARGET"

corepack enable >/dev/null 2>&1 || true
corepack prepare pnpm@10.33.4 --activate
PNPM_VERSION="$(pnpm --version)"
[ "$PNPM_VERSION" = "10.33.4" ] || fail "PNPM_VERSION_MISMATCH:$PNPM_VERSION"

START_TS="$(date +%s)"

# Upstream-required preparation: install/build the pinned Univer fork once,
# then switch its package exports to consumable lib/ outputs.
./scripts/setup-fork.sh

# Install the Casual Sheets workspace exactly from its lockfile.
pnpm install --frozen-lockfile

# Build the published SDK first, then the reference web app.
pnpm --filter @casualoffice/sheets build
NODE_OPTIONS=--max-old-space-size=4096 pnpm --filter @sheet/web build

[ -f "$TARGET/apps/web/dist/index.html" ] || fail "WEB_DIST_INDEX_MISSING"

# Temporary localhost-only smoke server; this is NOT a TOS deployment.
(
  cd "$TARGET"
  exec pnpm --filter @sheet/web exec vite preview --host 127.0.0.1 --port "$PREVIEW_PORT" --strictPort
) >/tmp/tsheets-casual-p00-b02-preview.log 2>&1 &
PREVIEW_PID="$!"

HTTP_CODE=""
for _ in $(seq 1 30); do
  if ! kill -0 "$PREVIEW_PID" 2>/dev/null; then
    cat /tmp/tsheets-casual-p00-b02-preview.log >&2 || true
    fail "PREVIEW_EXITED_EARLY"
  fi
  if command -v curl >/dev/null 2>&1; then
    HTTP_CODE="$(curl -sS -o /tmp/tsheets-casual-p00-b02.html -w '%{http_code}' "http://127.0.0.1:$PREVIEW_PORT/" || true)"
  elif command -v wget >/dev/null 2>&1; then
    if wget -q -O /tmp/tsheets-casual-p00-b02.html "http://127.0.0.1:$PREVIEW_PORT/"; then HTTP_CODE="200"; else HTTP_CODE="000"; fi
  else
    fail "NO_HTTP_CLIENT"
  fi
  [ "$HTTP_CODE" = "200" ] && break
  sleep 1
done
[ "$HTTP_CODE" = "200" ] || fail "LOCAL_SMOKE_HTTP_$HTTP_CODE"

grep -qi '<!doctype html' /tmp/tsheets-casual-p00-b02.html || fail "LOCAL_SMOKE_HTML_INVALID"

# Stop preview before final integrity checks.
kill "$PREVIEW_PID" 2>/dev/null || true
wait "$PREVIEW_PID" 2>/dev/null || true
PREVIEW_PID=""

# Restore the fork package manifests so the upstream tracked source returns clean.
node "$TARGET/scripts/swap-fork-pkgs.mjs" --restore

UPSTREAM_TRACKED_DIRTY="$(git -C "$TARGET" status --porcelain=v1 --untracked-files=no)"
[ -z "$UPSTREAM_TRACKED_DIRTY" ] || fail "UPSTREAM_TRACKED_SOURCE_DIRTY_AFTER_BUILD"

TRACKED_AFTER="$(git -C "$TOS" diff --no-ext-diff --binary HEAD -- . ':!vendor/tsheets-casual-upstream' | sha256sum | awk '{print $1}')"
STAGED_AFTER="$(git -C "$TOS" diff --cached --no-ext-diff --binary HEAD -- . ':!vendor/tsheets-casual-upstream' | sha256sum | awk '{print $1}')"
[ "$TRACKED_BEFORE" = "$TRACKED_AFTER" ] || fail "TOS_TRACKED_DIFF_CHANGED"
[ "$STAGED_BEFORE" = "$STAGED_AFTER" ] || fail "TOS_STAGED_DIFF_CHANGED"

END_TS="$(date +%s)"
ELAPSED="$((END_TS-START_TS))"
DIST_SIZE="$(du -sh "$TARGET/apps/web/dist" | awk '{print $1}')"
SOURCE_TOTAL_SIZE="$(du -sh "$TARGET" | awk '{print $1}')"

echo "PATCH=$PATCH"
echo "PHASE=P00"
echo "BATCH=B02"
echo "VERSION=V1"
echo "PASS_FAIL=PASS"
echo "UPSTREAM_SHA=$HEAD_SHA"
echo "TARGET=$TARGET"
echo "NODE_VERSION=$NODE_VERSION"
echo "PNPM_VERSION=$PNPM_VERSION"
echo "UPSTREAM_PREP=PASS"
echo "WORKSPACE_INSTALL=PASS"
echo "SDK_BUILD=PASS"
echo "WEB_BUILD=PASS"
echo "LOCAL_SMOKE_HTTP=$HTTP_CODE"
echo "LOCAL_SMOKE_HTML=PASS"
echo "DIST_SIZE=$DIST_SIZE"
echo "SOURCE_TOTAL_SIZE=$SOURCE_TOTAL_SIZE"
echo "ELAPSED_SECONDS=$ELAPSED"
echo "UPSTREAM_TRACKED_SOURCE_CLEAN=YES"
echo "TOS_TRACKED_SOURCE_CHANGED=NO"
echo "TOS_LIVE_CHANGED=NO"
echo "DATABASE_CHANGED=NO"
echo "PM2_CHANGED=NO"
echo "NGINX_CHANGED=NO"
echo "COMMIT_PERFORMED=NO"
echo "PUSH_PERFORMED=NO"
echo "NEXT=P01-B01-SIDE-BY-SIDE-INTEGRATION-V1"
echo "ERROR=NONE"
