#!/usr/bin/env bash
set -euo pipefail

PATCH="TOS-TWS-TSHEETS-CASUAL-P00-B01-UPSTREAM-SOURCE-BASELINE-V1_1"
UPSTREAM_URL="https://github.com/CasualOffice/sheets.git"
UPSTREAM_SHA="87a63902d94c85b3c50d3210055373a3d3bae991"
TOS="/var/www/TOS"
TARGET="$TOS/vendor/tsheets-casual-upstream"

fail() {
  echo "PATCH=$PATCH"
  echo "PASS_FAIL=FAIL"
  echo "ERROR=$1"
  exit 1
}

command -v git >/dev/null 2>&1 || fail "GIT_NOT_FOUND"
[ -d "$TOS/.git" ] || fail "TOS_REPO_NOT_FOUND:$TOS"

TRACKED_BEFORE="$(git -C "$TOS" diff --no-ext-diff --binary HEAD -- . ':!vendor/tsheets-casual-upstream' | sha256sum | awk '{print $1}')"
STAGED_BEFORE="$(git -C "$TOS" diff --cached --no-ext-diff --binary HEAD -- . ':!vendor/tsheets-casual-upstream' | sha256sum | awk '{print $1}')"

if [ -e "$TARGET" ] && [ ! -d "$TARGET/.git" ]; then
  fail "TARGET_EXISTS_NOT_GIT:$TARGET"
fi

if [ ! -d "$TARGET/.git" ]; then
  mkdir -p "$(dirname "$TARGET")"
  git clone --filter=blob:none --no-checkout "$UPSTREAM_URL" "$TARGET"
  CLONE_ACTION="CLONED"
else
  CLONE_ACTION="ALREADY_PRESENT"
fi

ORIGIN="$(git -C "$TARGET" remote get-url origin 2>/dev/null || true)"
case "$ORIGIN" in
  https://github.com/CasualOffice/sheets.git|git@github.com:CasualOffice/sheets.git)
    ;;
  *)
    fail "UNEXPECTED_ORIGIN:$ORIGIN"
    ;;
esac

git -C "$TARGET" fetch --no-tags origin "$UPSTREAM_SHA"
git -C "$TARGET" checkout --detach "$UPSTREAM_SHA"

# Upstream submodules use git@github.com URLs. Rewrite to HTTPS for this command
# only so the server does not need GitHub SSH credentials.
git -C "$TARGET" -c url."https://github.com/".insteadOf=git@github.com:   submodule update --init --recursive --depth 1

HEAD_SHA="$(git -C "$TARGET" rev-parse HEAD)"
[ "$HEAD_SHA" = "$UPSTREAM_SHA" ] || fail "SHA_MISMATCH:$HEAD_SHA"

SUBMODULE_STATUS="$(git -C "$TARGET" submodule status --recursive)"
if printf '%s\n' "$SUBMODULE_STATUS" | grep -Eq '^[+-]'; then
  fail "SUBMODULE_PIN_MISMATCH"
fi
if printf '%s\n' "$SUBMODULE_STATUS" | grep -Eq '^-' ; then
  fail "SUBMODULE_NOT_INITIALIZED"
fi

TRACKED_DIRTY="$(git -C "$TARGET" status --porcelain=v1 --untracked-files=no)"
[ -z "$TRACKED_DIRTY" ] || fail "UPSTREAM_TRACKED_DIRTY"

TRACKED_AFTER="$(git -C "$TOS" diff --no-ext-diff --binary HEAD -- . ':!vendor/tsheets-casual-upstream' | sha256sum | awk '{print $1}')"
STAGED_AFTER="$(git -C "$TOS" diff --cached --no-ext-diff --binary HEAD -- . ':!vendor/tsheets-casual-upstream' | sha256sum | awk '{print $1}')"
[ "$TRACKED_BEFORE" = "$TRACKED_AFTER" ] || fail "TOS_TRACKED_DIFF_CHANGED"
[ "$STAGED_BEFORE" = "$STAGED_AFTER" ] || fail "TOS_STAGED_DIFF_CHANGED"

SOURCE_SIZE="$(du -sh "$TARGET" | awk '{print $1}')"
SUBMODULE_COUNT="$(git -C "$TARGET" submodule status --recursive | wc -l | tr -d ' ')"

echo "PATCH=$PATCH"
echo "PHASE=P00"
echo "BATCH=B01"
echo "VERSION=V1_1"
echo "PASS_FAIL=PASS"
echo "CLONE_ACTION=$CLONE_ACTION"
echo "UPSTREAM=CasualOffice/sheets"
echo "UPSTREAM_SHA=$HEAD_SHA"
echo "TARGET=$TARGET"
echo "SOURCE_SIZE=$SOURCE_SIZE"
echo "SUBMODULES_INITIALIZED=$SUBMODULE_COUNT"
echo "UPSTREAM_SOURCE_MODIFIED=NO"
echo "DEPENDENCIES_INSTALLED=NO"
echo "BUILD_RUN=NO"
echo "TOS_TRACKED_SOURCE_CHANGED=NO"
echo "TOS_UNTRACKED_VENDOR_ADDED=YES"
echo "TOS_LIVE_CHANGED=NO"
echo "DATABASE_CHANGED=NO"
echo "PM2_CHANGED=NO"
echo "NGINX_CHANGED=NO"
echo "SUPERSEDES=P00-B01-V1"
echo "NEXT=P00-B02-BASELINE-INSTALL-BUILD-SMOKE-V1"
echo "ERROR=NONE"
