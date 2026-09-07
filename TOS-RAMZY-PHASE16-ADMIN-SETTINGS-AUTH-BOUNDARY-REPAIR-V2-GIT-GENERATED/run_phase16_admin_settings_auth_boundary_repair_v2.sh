#!/usr/bin/env bash
set -euo pipefail

TOS_ROOT="/var/www/TOS"
PATCH_DIR="$(cd "$(dirname "$0")" && pwd)"
VERIFIER="$PATCH_DIR/01_phase16_admin_settings_auth_boundary_repair.py"
BASELINE="f7678ab1ab7b5b0261a9e3a3a78c43533999b66d"
DOMAIN="https://tos.tamiyouz.com"
BACKEND_PORT="${TOS_BACKEND_PORT:-5006}"

fail() {
  echo "PASS/FAIL=FAIL"
  echo "RAMZY_ADMIN_SETTINGS_AUTH_BOUNDARY_REPAIR=FAIL"
  echo "REASON=$1"
  exit 1
}

http_code() {
  local method="$1"
  local url="$2"
  if [[ "$method" == "PATCH" ]]; then
    curl --http1.1 -ksS --connect-timeout 3 --max-time 8 -H 'Connection: close' -X PATCH -H 'Content-Type: application/json' -d '{}' -o /dev/null -w '%{http_code}' "$url" 2>/dev/null || true
  else
    curl --http1.1 -ksS --connect-timeout 3 --max-time 8 -H 'Connection: close' -o /dev/null -w '%{http_code}' "$url" 2>/dev/null || true
  fi
}

wait_for_code() {
  local method="$1"
  local url="$2"
  local expected="$3"
  local attempts="${4:-20}"
  local delay="${5:-2}"
  local code="000"
  for ((i=1; i<=attempts; i++)); do
    code="$(http_code "$method" "$url")"
    [[ "$code" == "$expected" ]] && { printf '%s' "$code"; return 0; }
    sleep "$delay"
  done
  printf '%s' "$code"
  return 1
}

tree_hash() {
  local dir="$1"
  if [[ ! -d "$dir" ]]; then printf 'MISSING'; return; fi
  (cd "$dir" && find . -type f -print0 | sort -z | xargs -0 sha256sum | sha256sum | awk '{print $1}')
}

echo "RUNNING=RAMZY_PHASE16_ADMIN_SETTINGS_AUTH_BOUNDARY_REPAIR_V2"
cd "$TOS_ROOT"
CURRENT_HEAD="$(git rev-parse HEAD)"
echo "CURRENT_TOS_HEAD=$CURRENT_HEAD"
git merge-base --is-ancestor "$BASELINE" "$CURRENT_HEAD" || fail "PHASE15_BASELINE_NOT_ANCESTOR"

STATUS_BEFORE="$(git status --short)"
DIFF_BEFORE="$(git diff --binary | sha256sum | awk '{print $1}')"
SCHEMA_PACKAGE_BEFORE="$(git diff --binary -- backend/prisma backend/package.json frontend/package.json | sha256sum | awk '{print $1}')"

[[ -f "$VERIFIER" ]] || fail "SOURCE_VERIFIER_NOT_FOUND"
python3 "$VERIFIER" "$TOS_ROOT" || fail "ADMIN_SETTINGS_SOURCE_STATE_INVALID"
echo "PRE_STATE=ADMIN_SETTINGS_PATCH_ALREADY_APPLIED_SOURCE_VALID"

# Focused acceptance: admin settings repair + Phase 16 production hardening.
TEST_LOG="$(mktemp)"
trap 'rm -f "$TEST_LOG"' EXIT
node --test \
  backend/src/agency-operator/tests/ramzyAdminSettingsAccessPhase16Repair.test.js \
  backend/src/agency-operator/tests/ramzyVoiceActionProductionHardeningPhase16.test.js \
  2>&1 | tee "$TEST_LOG"
TEST_COUNT="$(awk '/^# tests /{print $3}' "$TEST_LOG" | tail -1)"
PASS_COUNT="$(awk '/^# pass /{print $3}' "$TEST_LOG" | tail -1)"
[[ -n "$TEST_COUNT" && "$TEST_COUNT" == "$PASS_COUNT" ]] || fail "FOCUSED_TESTS_FAILED:${PASS_COUNT:-0}/${TEST_COUNT:-0}"
echo "FOCUSED_TESTS=PASS (${PASS_COUNT}/${TEST_COUNT})"

# The previous V1 run already built and deployed frontend successfully. This V2 must not rebuild or mutate it.
DIST_HASH="$(tree_hash frontend/dist)"
LIVE_HASH="$(tree_hash /opt/apps/tamiyouz-front/build)"
echo "FRONTEND_DIST_HASH=$DIST_HASH"
echo "FRONTEND_LIVE_HASH=$LIVE_HASH"
[[ "$DIST_HASH" != "MISSING" && "$DIST_HASH" == "$LIVE_HASH" ]] || fail "DEPLOYED_FRONTEND_NOT_MATCHING_CURRENT_DIST"
echo "FRONTEND_DEPLOYED_DIST_MATCH=PASS"

BACKEND_PM2=""
if pm2 describe tamiyouz-system >/dev/null 2>&1; then
  BACKEND_PM2="tamiyouz-system"
elif pm2 describe tamiyouz-backend >/dev/null 2>&1; then
  BACKEND_PM2="tamiyouz-backend"
else
  fail "BACKEND_PM2_NOT_FOUND"
fi
pm2 reload "$BACKEND_PM2"
echo "BACKEND_RELOAD=PASS"

# Critical difference from V1: prove the backend itself is ready before testing nginx/public auth boundaries.
LOOPBACK_SETTINGS_GET="$(wait_for_code GET "http://127.0.0.1:${BACKEND_PORT}/api/agent/settings" 401 20 2 || true)"
echo "LOOPBACK_RAMZY_SETTINGS_GET_UNAUTH_HTTP=$LOOPBACK_SETTINGS_GET"
if [[ "$LOOPBACK_SETTINGS_GET" != "401" ]]; then
  echo "PM2_STATUS_BEGIN"
  pm2 describe "$BACKEND_PM2" || true
  echo "PM2_STATUS_END"
  fail "BACKEND_AGENT_ROUTE_NOT_READY_OR_AUTH_BROKEN:$LOOPBACK_SETTINGS_GET"
fi
echo "BACKEND_AGENT_ROUTE_READY=PASS"

LOOPBACK_SETTINGS_PATCH="$(wait_for_code PATCH "http://127.0.0.1:${BACKEND_PORT}/api/agent/settings" 401 5 1 || true)"
echo "LOOPBACK_RAMZY_SETTINGS_PATCH_UNAUTH_HTTP=$LOOPBACK_SETTINGS_PATCH"
[[ "$LOOPBACK_SETTINGS_PATCH" == "401" ]] || fail "LOOPBACK_SETTINGS_PATCH_AUTH_BOUNDARY_FAILED:$LOOPBACK_SETTINGS_PATCH"

PUBLIC_AGENT_STATUS="$(wait_for_code GET "$DOMAIN/api/agent/status" 401 20 2 || true)"
PUBLIC_SETTINGS_GET="$(wait_for_code GET "$DOMAIN/api/agent/settings" 401 20 2 || true)"
PUBLIC_SETTINGS_PATCH="$(wait_for_code PATCH "$DOMAIN/api/agent/settings" 401 20 2 || true)"
echo "AGENT_STATUS_UNAUTH_HTTP=$PUBLIC_AGENT_STATUS"
echo "RAMZY_SETTINGS_GET_UNAUTH_HTTP=$PUBLIC_SETTINGS_GET"
echo "RAMZY_SETTINGS_PATCH_UNAUTH_HTTP=$PUBLIC_SETTINGS_PATCH"
[[ "$PUBLIC_AGENT_STATUS" == "401" ]] || fail "PUBLIC_AGENT_AUTH_BOUNDARY_FAILED:$PUBLIC_AGENT_STATUS"
[[ "$PUBLIC_SETTINGS_GET" == "401" ]] || fail "PUBLIC_SETTINGS_GET_AUTH_BOUNDARY_FAILED:$PUBLIC_SETTINGS_GET"
[[ "$PUBLIC_SETTINGS_PATCH" == "401" ]] || fail "PUBLIC_SETTINGS_PATCH_AUTH_BOUNDARY_FAILED:$PUBLIC_SETTINGS_PATCH"
echo "AUTH_BOUNDARY_E2E=PASS"

# Public frontend smoke only after backend readiness has been established.
for path in /dashboard /settings /tasks; do
  code="$(wait_for_code GET "$DOMAIN$path" 200 5 1 || true)"
  echo "HTTP_${path//\//_}=$code"
  [[ "$code" == "200" ]] || fail "FRONTEND_SMOKE_FAILED:$path:$code"
done
echo "HTTP_SMOKE=PASS"

STATUS_AFTER="$(git status --short)"
DIFF_AFTER="$(git diff --binary | sha256sum | awk '{print $1}')"
SCHEMA_PACKAGE_AFTER="$(git diff --binary -- backend/prisma backend/package.json frontend/package.json | sha256sum | awk '{print $1}')"
[[ "$STATUS_BEFORE" == "$STATUS_AFTER" ]] || fail "WORKTREE_STATUS_CHANGED_BY_V2"
[[ "$DIFF_BEFORE" == "$DIFF_AFTER" ]] || fail "SOURCE_DIFF_CHANGED_BY_V2"
[[ "$SCHEMA_PACKAGE_BEFORE" == "$SCHEMA_PACKAGE_AFTER" ]] || fail "SCHEMA_OR_PACKAGE_CHANGED"

echo "SOURCE_CHANGES_THIS_RUN=NO"
echo "PHASE16_LOCAL_WORK_PRESERVED=YES"
echo "UNRELATED_WORK_PRESERVED=YES"
echo "ADMIN_RAMZY_SETTINGS_ACCESS=PASS"
echo "SUPER_ADMIN_RAMZY_SETTINGS_ACCESS=PASS"
echo "SUPER_ADMIN_AUDIT_ONLY=PRESERVED"
echo "RAMZY_EXECUTION_RBAC=UNCHANGED"
echo "NO_FRONTEND_REBUILD_OR_DEPLOY_THIS_RUN=YES"
echo "NO_COMMIT_OR_PUSH=YES"
echo "RAMZY_ADMIN_SETTINGS_AUTH_BOUNDARY_REPAIR=PASS"
echo "PASS/FAIL=PASS"
echo "--- git status --short ---"
git status --short
