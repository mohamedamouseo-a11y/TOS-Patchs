#!/usr/bin/env bash
set -euo pipefail

PATCH="TOS-TWS-TSHEETS-CASUAL-P00-B02-BASELINE-INSTALL-BUILD-SMOKE-V1_1"
TOS="/var/www/TOS"
TARGET="$TOS/vendor/tsheets-casual-upstream"
UPSTREAM_SHA="87a63902d94c85b3c50d3210055373a3d3bae991"
PREVIEW_PORT="4173"
PREVIEW_PID=""
CREATED_LINKS=()

emit_fail() {
  local err="$1"
  echo "PATCH=$PATCH"
  echo "PHASE=P00"
  echo "BATCH=B02"
  echo "VERSION=V1_1"
  echo "PASS_FAIL=FAIL"
  echo "ERROR=$err"
  exit 1
}

cleanup_links() {
  local p
  for p in "${CREATED_LINKS[@]:-}"; do
    [ -L "$p" ] && rm -f "$p" || true
  done
  rmdir "$TARGET/vendor/design-system/node_modules/@types" 2>/dev/null || true
  rmdir "$TARGET/vendor/design-system/node_modules" 2>/dev/null || true
}

cleanup() {
  if [ -n "$PREVIEW_PID" ] && kill -0 "$PREVIEW_PID" 2>/dev/null; then
    kill "$PREVIEW_PID" 2>/dev/null || true
    wait "$PREVIEW_PID" 2>/dev/null || true
  fi
  cleanup_links
  if [ -f "$TARGET/scripts/swap-fork-pkgs.mjs" ]; then
    node "$TARGET/scripts/swap-fork-pkgs.mjs" --restore >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

[ -d "$TOS/.git" ] || emit_fail "TOS_REPO_NOT_FOUND"
[ -d "$TARGET/.git" ] || emit_fail "P00_B01_SOURCE_NOT_FOUND"
[ "$(git -C "$TARGET" rev-parse HEAD)" = "$UPSTREAM_SHA" ] || emit_fail "UPSTREAM_SHA_MISMATCH"

command -v node >/dev/null 2>&1 || emit_fail "NODE_NOT_FOUND"
command -v corepack >/dev/null 2>&1 || emit_fail "COREPACK_NOT_FOUND"
corepack enable >/dev/null 2>&1 || true
corepack prepare pnpm@10.33.4 --activate >/dev/null
[ "$(pnpm --version)" = "10.33.4" ] || emit_fail "PNPM_VERSION_MISMATCH"

TRACKED_BEFORE="$(git -C "$TOS" diff --no-ext-diff --binary HEAD -- . ':!vendor/tsheets-casual-upstream' | sha256sum | awk '{print $1}')"
STAGED_BEFORE="$(git -C "$TOS" diff --cached --no-ext-diff --binary HEAD -- . ':!vendor/tsheets-casual-upstream' | sha256sum | awk '{print $1}')"

cd "$TARGET"

# Previous V1 already completed workspace installation. Re-check from lockfile;
# pnpm reuses the existing store/node_modules and should be quick.
if ! pnpm install --frozen-lockfile --prefer-offline; then
  emit_fail "WORKSPACE_INSTALL_FAILED"
fi

# Reuse the expensive Univer fork build from V1 if its built artifacts exist.
FORK_CORE="$TARGET/vendor/univer-revamp/packages/core/lib/es/index.js"
FORK_SHEETS="$TARGET/vendor/univer-revamp/packages/sheets/lib/es/index.js"
if [ -f "$FORK_CORE" ] && [ -f "$FORK_SHEETS" ]; then
  node "$TARGET/scripts/swap-fork-pkgs.mjs"
  FORK_PREP="REUSED_EXISTING_BUILD"
else
  if ! "$TARGET/scripts/setup-fork.sh"; then
    emit_fail "UPSTREAM_FORK_PREP_FAILED"
  fi
  FORK_PREP="REBUILT"
fi

# The design-system is a link: peer package. Because this checkout is nested
# under /var/www/TOS, TypeScript can otherwise walk upward and resolve TOS's
# @types/react@19. Wire the peer package temporarily to the web app's own
# React 18 + React 18 type packages. Nothing tracked is changed.
WEB_NM="$TARGET/apps/web/node_modules"
for required in   "$WEB_NM/react"   "$WEB_NM/react-dom"   "$WEB_NM/@types/react"   "$WEB_NM/@types/react-dom"
do
  [ -e "$required" ] || emit_fail "EXPECTED_WEB_PEER_MISSING:$required"
done

WEB_REACT_TYPES_VERSION="$(node -p "require('$WEB_NM/@types/react/package.json').version")"
case "$WEB_REACT_TYPES_VERSION" in
  18.*) ;;
  *) emit_fail "EXPECTED_REACT18_TYPES_GOT:$WEB_REACT_TYPES_VERSION" ;;
esac

TOS_REACT_TYPES_VERSION="NONE"
if [ -f "$TOS/node_modules/@types/react/package.json" ]; then
  TOS_REACT_TYPES_VERSION="$(node -p "require('$TOS/node_modules/@types/react/package.json').version")"
fi

DS_NM="$TARGET/vendor/design-system/node_modules"
mkdir -p "$DS_NM/@types"

link_peer() {
  local source="$1"
  local dest="$2"
  if [ -e "$dest" ] || [ -L "$dest" ]; then
    emit_fail "DESIGN_SYSTEM_PEER_PATH_ALREADY_EXISTS:$dest"
  fi
  ln -s "$source" "$dest"
  CREATED_LINKS+=("$dest")
}

link_peer "$WEB_NM/react" "$DS_NM/react"
link_peer "$WEB_NM/react-dom" "$DS_NM/react-dom"
link_peer "$WEB_NM/@types/react" "$DS_NM/@types/react"
link_peer "$WEB_NM/@types/react-dom" "$DS_NM/@types/react-dom"

START_TS="$(date +%s)"

# SDK was already built in V1, but rebuild is cheap and verifies its baseline.
if ! pnpm --filter @casualoffice/sheets build; then
  emit_fail "SDK_BUILD_FAILED"
fi

if ! NODE_OPTIONS=--max-old-space-size=4096 pnpm --filter @sheet/web build; then
  emit_fail "WEB_BUILD_FAILED_AFTER_REACT_TYPES_ISOLATION"
fi

[ -f "$TARGET/apps/web/dist/index.html" ] || emit_fail "WEB_DIST_INDEX_MISSING"

(
  cd "$TARGET"
  exec pnpm --filter @sheet/web exec vite preview --host 127.0.0.1 --port "$PREVIEW_PORT" --strictPort
) >/tmp/tsheets-casual-p00-b02-v1_1-preview.log 2>&1 &
PREVIEW_PID="$!"

HTTP_CODE=""
for _ in $(seq 1 30); do
  if ! kill -0 "$PREVIEW_PID" 2>/dev/null; then
    tail -n 80 /tmp/tsheets-casual-p00-b02-v1_1-preview.log >&2 || true
    emit_fail "PREVIEW_EXITED_EARLY"
  fi
  HTTP_CODE="$(curl -sS -o /tmp/tsheets-casual-p00-b02-v1_1.html -w '%{http_code}' "http://127.0.0.1:$PREVIEW_PORT/" || true)"
  [ "$HTTP_CODE" = "200" ] && break
  sleep 1
done
[ "$HTTP_CODE" = "200" ] || emit_fail "LOCAL_SMOKE_HTTP_$HTTP_CODE"
grep -qi '<!doctype html' /tmp/tsheets-casual-p00-b02-v1_1.html || emit_fail "LOCAL_SMOKE_HTML_INVALID"

kill "$PREVIEW_PID" 2>/dev/null || true
wait "$PREVIEW_PID" 2>/dev/null || true
PREVIEW_PID=""

# Remove isolation links and restore temporary fork package-manifest swaps
# before checking source integrity.
cleanup_links
node "$TARGET/scripts/swap-fork-pkgs.mjs" --restore

UPSTREAM_TRACKED_DIRTY="$(git -C "$TARGET" status --porcelain=v1 --untracked-files=no)"
[ -z "$UPSTREAM_TRACKED_DIRTY" ] || emit_fail "UPSTREAM_TRACKED_SOURCE_DIRTY_AFTER_BUILD"

TRACKED_AFTER="$(git -C "$TOS" diff --no-ext-diff --binary HEAD -- . ':!vendor/tsheets-casual-upstream' | sha256sum | awk '{print $1}')"
STAGED_AFTER="$(git -C "$TOS" diff --cached --no-ext-diff --binary HEAD -- . ':!vendor/tsheets-casual-upstream' | sha256sum | awk '{print $1}')"
[ "$TRACKED_BEFORE" = "$TRACKED_AFTER" ] || emit_fail "TOS_TRACKED_DIFF_CHANGED"
[ "$STAGED_BEFORE" = "$STAGED_AFTER" ] || emit_fail "TOS_STAGED_DIFF_CHANGED"

END_TS="$(date +%s)"
DIST_SIZE="$(du -sh "$TARGET/apps/web/dist" | awk '{print $1}')"

echo "PATCH=$PATCH"
echo "PHASE=P00"
echo "BATCH=B02"
echo "VERSION=V1_1"
echo "PASS_FAIL=PASS"
echo "UPSTREAM_SHA=$UPSTREAM_SHA"
echo "TARGET=$TARGET"
echo "WORKSPACE_INSTALL=PASS_REUSED"
echo "FORK_PREP=$FORK_PREP"
echo "REACT_TYPES_ISOLATION=PASS"
echo "WEB_REACT_TYPES_VERSION=$WEB_REACT_TYPES_VERSION"
echo "TOS_REACT_TYPES_VERSION=$TOS_REACT_TYPES_VERSION"
echo "SDK_BUILD=PASS"
echo "WEB_BUILD=PASS"
echo "LOCAL_SMOKE_HTTP=$HTTP_CODE"
echo "LOCAL_SMOKE_HTML=PASS"
echo "DIST_SIZE=$DIST_SIZE"
echo "ELAPSED_SECONDS=$((END_TS-START_TS))"
echo "UPSTREAM_TRACKED_SOURCE_CLEAN=YES"
echo "TOS_TRACKED_SOURCE_CHANGED=NO"
echo "TOS_LIVE_CHANGED=NO"
echo "DATABASE_CHANGED=NO"
echo "PM2_CHANGED=NO"
echo "NGINX_CHANGED=NO"
echo "COMMIT_PERFORMED=NO"
echo "PUSH_PERFORMED=NO"
echo "SUPERSEDES=P00-B02-V1"
echo "NEXT=P01-B01-SIDE-BY-SIDE-INTEGRATION-V1"
echo "ERROR=NONE"
