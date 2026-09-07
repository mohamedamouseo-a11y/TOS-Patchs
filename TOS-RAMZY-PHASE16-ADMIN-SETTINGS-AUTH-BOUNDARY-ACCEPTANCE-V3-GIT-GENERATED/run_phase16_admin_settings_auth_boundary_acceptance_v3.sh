#!/usr/bin/env bash
set -euo pipefail

TOS_ROOT="/var/www/TOS"
PATCH_DIR="$(cd "$(dirname "$0")" && pwd)"
VERIFY="$PATCH_DIR/01_phase16_admin_settings_auth_boundary_acceptance_v3.py"
BASELINE="f7678ab1ab7b5b0261a9e3a3a78c43533999b66d"
DOMAIN="https://tos.tamiyouz.com"
LOOPBACK="http://127.0.0.1:5006"
CSRF_TOKEN="a16a16a16a16a16a16a16a16a16a16a16a16a16a16a16a16a16a16a16a16a1"

fail() {
  echo "PASS/FAIL=FAIL"
  echo "RAMZY_ADMIN_SETTINGS_AUTH_BOUNDARY_ACCEPTANCE=FAIL"
  echo "REASON=$1"
  exit 1
}

code_get() {
  curl -ksS -o /dev/null -w '%{http_code}' "$1" || true
}

code_patch_no_csrf() {
  curl -ksS -X PATCH -H 'Content-Type: application/json' -d '{}' -o /dev/null -w '%{http_code}' "$1" || true
}

code_patch_with_csrf() {
  curl -ksS -X PATCH \
    -H 'Content-Type: application/json' \
    -H "x-csrf-token: $CSRF_TOKEN" \
    -H "Cookie: tamiyouz_csrf_token=$CSRF_TOKEN" \
    -d '{}' -o /dev/null -w '%{http_code}' "$1" || true
}

retry_code() {
  local mode="$1" url="$2" expected="$3" code="000"
  for _ in 1 2 3 4 5 6; do
    case "$mode" in
      GET) code="$(code_get "$url")" ;;
      PATCH_NO_CSRF) code="$(code_patch_no_csrf "$url")" ;;
      PATCH_WITH_CSRF) code="$(code_patch_with_csrf "$url")" ;;
      *) fail "UNKNOWN_HTTP_MODE:$mode" ;;
    esac
    [[ "$code" == "$expected" ]] && break
    sleep 2
  done
  printf '%s' "$code"
}

tree_hash() {
  local dir="$1"
  if [[ ! -d "$dir" ]]; then printf 'MISSING'; return; fi
  (cd "$dir" && find . -type f -print0 | sort -z | xargs -0 sha256sum | sha256sum | awk '{print $1}')
}

echo "RUNNING=RAMZY_PHASE16_ADMIN_SETTINGS_AUTH_BOUNDARY_ACCEPTANCE_V3"
cd "$TOS_ROOT"
CURRENT_HEAD="$(git rev-parse HEAD)"
echo "CURRENT_TOS_HEAD=$CURRENT_HEAD"
git merge-base --is-ancestor "$BASELINE" "$CURRENT_HEAD" || fail "PHASE15_BASELINE_NOT_ANCESTOR"

PRE_STATUS="$(git status --short)"
PRE_DIFF_HASH="$(git diff --binary | sha256sum | awk '{print $1}')"

[[ -f "$VERIFY" ]] || fail "V3_SOURCE_VERIFIER_NOT_FOUND"
python3 "$VERIFY" "$TOS_ROOT"
echo "PRE_STATE=ADMIN_SETTINGS_PATCH_APPLIED_CSRF_PREAUTH_CONFIRMED"

node --test \
  backend/src/agency-operator/tests/ramzyAdminSettingsAccessPhase16Repair.test.js \
  backend/src/agency-operator/tests/ramzyVoiceActionProductionHardeningPhase16.test.js

echo "FOCUSED_TESTS=PASS (15/15 expected)"

DIST_HASH="$(tree_hash frontend/dist)"
LIVE_HASH="$(tree_hash /opt/apps/tamiyouz-front/build)"
echo "FRONTEND_DIST_HASH=$DIST_HASH"
echo "FRONTEND_LIVE_HASH=$LIVE_HASH"
[[ "$DIST_HASH" != "MISSING" && "$DIST_HASH" == "$LIVE_HASH" ]] || fail "FRONTEND_DEPLOYED_DIST_MISMATCH"
echo "FRONTEND_DEPLOYED_DIST_MATCH=PASS"

if pm2 describe tamiyouz-system >/dev/null 2>&1; then
  pm2 describe tamiyouz-system | grep -qi online || fail "BACKEND_PM2_NOT_ONLINE"
elif pm2 describe tamiyouz-backend >/dev/null 2>&1; then
  pm2 describe tamiyouz-backend | grep -qi online || fail "BACKEND_PM2_NOT_ONLINE"
else
  fail "BACKEND_PM2_NOT_FOUND"
fi
echo "BACKEND_PM2=ONLINE"

HEALTH_CODE="$(retry_code GET "$DOMAIN/health" 200)"
echo "HTTP_HEALTH=$HEALTH_CODE"
[[ "$HEALTH_CODE" == "200" ]] || fail "HEALTH_FAILED:$HEALTH_CODE"

# Layer 1: safe GET reaches Ramzy router auth and must be unauthenticated.
LB_GET="$(retry_code GET "$LOOPBACK/api/agent/settings" 401)"
echo "LOOPBACK_SETTINGS_GET_UNAUTH_HTTP=$LB_GET"
[[ "$LB_GET" == "401" ]] || fail "LOOPBACK_GET_AUTH_BOUNDARY_FAILED:$LB_GET"

# Layer 2: unsafe PATCH is intentionally rejected by global CSRF before auth.
LB_PATCH_CSRF="$(retry_code PATCH_NO_CSRF "$LOOPBACK/api/agent/settings" 403)"
echo "LOOPBACK_SETTINGS_PATCH_NO_CSRF_HTTP=$LB_PATCH_CSRF"
[[ "$LB_PATCH_CSRF" == "403" ]] || fail "LOOPBACK_CSRF_BOUNDARY_FAILED:$LB_PATCH_CSRF"
echo "LOOPBACK_CSRF_PREAUTH_BOUNDARY=PASS"

# Layer 3: provide a valid double-submit CSRF pair but no auth. The request must
# pass CSRF and then be rejected by agent auth with 401.
LB_PATCH_AUTH="$(retry_code PATCH_WITH_CSRF "$LOOPBACK/api/agent/settings" 401)"
echo "LOOPBACK_SETTINGS_PATCH_VALID_CSRF_UNAUTH_HTTP=$LB_PATCH_AUTH"
[[ "$LB_PATCH_AUTH" == "401" ]] || fail "LOOPBACK_PATCH_AUTH_BOUNDARY_FAILED:$LB_PATCH_AUTH"
echo "LOOPBACK_PATCH_AUTH_AFTER_CSRF=PASS"

PUB_GET="$(retry_code GET "$DOMAIN/api/agent/settings" 401)"
PUB_PATCH_CSRF="$(retry_code PATCH_NO_CSRF "$DOMAIN/api/agent/settings" 403)"
PUB_PATCH_AUTH="$(retry_code PATCH_WITH_CSRF "$DOMAIN/api/agent/settings" 401)"
echo "PUBLIC_SETTINGS_GET_UNAUTH_HTTP=$PUB_GET"
echo "PUBLIC_SETTINGS_PATCH_NO_CSRF_HTTP=$PUB_PATCH_CSRF"
echo "PUBLIC_SETTINGS_PATCH_VALID_CSRF_UNAUTH_HTTP=$PUB_PATCH_AUTH"
[[ "$PUB_GET" == "401" ]] || fail "PUBLIC_GET_AUTH_BOUNDARY_FAILED:$PUB_GET"
[[ "$PUB_PATCH_CSRF" == "403" ]] || fail "PUBLIC_CSRF_BOUNDARY_FAILED:$PUB_PATCH_CSRF"
[[ "$PUB_PATCH_AUTH" == "401" ]] || fail "PUBLIC_PATCH_AUTH_BOUNDARY_FAILED:$PUB_PATCH_AUTH"
echo "PUBLIC_AUTH_AND_CSRF_BOUNDARIES=PASS"

POST_STATUS="$(git status --short)"
POST_DIFF_HASH="$(git diff --binary | sha256sum | awk '{print $1}')"
[[ "$PRE_STATUS" == "$POST_STATUS" ]] || fail "WORKTREE_STATUS_CHANGED"
[[ "$PRE_DIFF_HASH" == "$POST_DIFF_HASH" ]] || fail "SOURCE_DIFF_CHANGED"
echo "SOURCE_CHANGES_THIS_RUN=NO"
echo "LOCAL_PHASE16_WORK_PRESERVED=YES"
echo "ADMIN_RAMZY_SETTINGS_ACCESS=PASS"
echo "SUPER_ADMIN_AUDIT_ONLY=PRESERVED"
echo "RAMZY_EXECUTION_RBAC=UNCHANGED"
echo "CSRF_BOUNDARY=PASS"
echo "AUTH_BOUNDARY=PASS"
echo "NO_DEPLOY_THIS_RUN=YES"
echo "NO_COMMIT_OR_PUSH=YES"
echo "RAMZY_ADMIN_SETTINGS_AUTH_BOUNDARY_ACCEPTANCE=PASS"
echo "PASS/FAIL=PASS"
echo "--- git status --short ---"
git status --short
