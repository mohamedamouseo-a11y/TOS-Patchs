#!/usr/bin/env bash
set -euo pipefail

TOS_ROOT="/var/www/TOS"
PATCH_DIR="$(cd "$(dirname "$0")" && pwd)"
BASELINE="046bf034e5fdf0f4667e96dfa4861b4440d6db70"
REPAIR="$PATCH_DIR/05_phase14_committed_partial_persistent_guard_fix.py"
DOMAIN="https://tos.tamiyouz.com"
TARGET="backend/src/agency-operator/services/ramzyMemory.service.js"
TEST="backend/src/agency-operator/tests/ramzyActionDraftPersistentMemoryPhase14.test.js"

fail() {
  echo "PASS/FAIL=FAIL"
  echo "PHASE14_CONVERSATIONAL_ACTION_MEMORY=FAIL"
  echo "REASON=$1"
  exit 1
}

public_code() {
  local path="$1"
  local code="000"
  for _ in 1 2 3 4 5; do
    code="$(curl -ksS -o /dev/null -w '%{http_code}' "$DOMAIN$path" || true)"
    [[ "$code" != "000" && "$code" != "502" && "$code" != "503" ]] && break
    sleep 2
  done
  printf '%s' "$code"
}

strip_target_status() {
  local status="$1"
  printf '%s\n' "$status" | while IFS= read -r line; do
    [[ -z "$line" ]] && continue
    local path="${line:3}"
    [[ "$path" == "$TARGET" ]] && continue
    printf '%s\n' "$line"
  done | sort
}

echo "RUNNING=RAMZY_PHASE14_COMMITTED_PARTIAL_PERSISTENT_GUARD_FIX"
cd "$TOS_ROOT"
CURRENT_HEAD="$(git rev-parse HEAD)"
echo "CURRENT_TOS_HEAD=$CURRENT_HEAD"
if ! git merge-base --is-ancestor "$BASELINE" "$CURRENT_HEAD"; then
  fail "PHASE14_COMMITTED_PARTIAL_BASELINE_NOT_ANCESTOR"
fi

PRE_STATUS="$(git status --short)"
if printf '%s\n' "$PRE_STATUS" | grep -Fq " $TARGET"; then
  fail "PHASE14_GUARD_TARGET_ALREADY_DIRTY"
fi

grep -q 'RAMZY_CONVERSATIONAL_ACTION_DRAFT_V1' backend/src/agency-operator/services/ramzyActionDraft.service.js || fail "PHASE14_DRAFT_SERVICE_MISSING"
grep -q 'Phase 14 task action commands are not promoted into long-term RamzyMemory' "$TEST" || fail "PHASE14_PERSISTENT_TEST_MISSING"
grep -q 'Space/end boundaries are Unicode-safe here.' "$TARGET" || fail "EXPECTED_COMMITTED_BROKEN_GUARD_STATE_NOT_FOUND"
grep -q 'looksLikeActionDraftMessage(message) || !isHighConfidenceMemory(message)' "$TARGET" || fail "PERSISTENT_SKIP_GUARD_MISSING"
echo "PRE_STATE=COMMITTED_PHASE14_PARTIAL_GUARD_BROKEN"

TEST_HASH_BEFORE="$(sha256sum "$TEST" | awk '{print $1}')"
FRONTEND_STATUS_BEFORE="$(git status --short -- frontend)"
FRONTEND_DIFF_BEFORE="$(git diff --binary -- frontend | sha256sum | awk '{print $1}')"
SCHEMA_PACKAGE_DIFF_BEFORE="$(git diff --binary -- backend/prisma backend/package.json frontend/package.json | sha256sum | awk '{print $1}')"

[[ -f "$REPAIR" ]] || fail "PHASE14_COMMITTED_GUARD_REPAIR_NOT_FOUND"
python3 "$REPAIR"
echo "PATCH_APPLY=PASS"

node --test "$TEST"
echo "PERSISTENT_MEMORY_REGRESSION_TEST=PASS"

npm --prefix backend run test:ramzy
echo "BACKEND_TESTS=PASS"

# Phase 14 contracts and previous safety invariants.
grep -q 'const startsWithVerb = (verbs)' "$TARGET" || fail "TOKEN_GUARD_VERB_DETECTOR_MISSING"
grep -q 'taskToken.test(value)' "$TARGET" || fail "TOKEN_GUARD_TASK_TOKEN_MISSING"
grep -q 'commentChecklistToken.test(value)' "$TARGET" || fail "TOKEN_GUARD_COMMENT_CHECKLIST_MISSING"
grep -q 'dueToken.test(value)' "$TARGET" || fail "TOKEN_GUARD_DUE_TOKEN_MISSING"
grep -q 'looksLikeActionDraftMessage(message) || !isHighConfidenceMemory(message)' "$TARGET" || fail "PERSISTENT_ACTION_SKIP_MISSING"
grep -q 'authorizationTrusted: false' backend/src/agency-operator/services/ramzyActionDraft.service.js || fail "MEMORY_AUTH_UNTRUSTED_MARKER_MISSING"
grep -q 'targetReferencesTrusted: false' backend/src/agency-operator/services/ramzyActionDraft.service.js || fail "MEMORY_TARGET_UNTRUSTED_MARKER_MISSING"
grep -q 'materializeConversationActionDraft' backend/src/agency-operator/services/ramzyActionDraft.service.js || fail "DRAFT_MATERIALIZATION_MISSING"
grep -q 'assertAgentTaskCreateAccess' backend/src/agency-operator/services/ramzyActionDraft.service.js || fail "DRAFT_CREATE_RBAC_RECHECK_MISSING"
grep -q 'assertAgentTaskActionAccess' backend/src/agency-operator/services/ramzyActionDraft.service.js || fail "DRAFT_TASK_RBAC_RECHECK_MISSING"
grep -q 'assertRamzyToolInvocationScope' backend/src/agency-operator/tools/createRamzyTools.js || fail "PHASE8_SCOPE_GUARD_MISSING"
grep -q 'RAMZY_ACTION_CONFIRMATION_V1' backend/src/agency-operator/services/actionConfirmation.service.js || fail "PHASE13_CONFIRMATION_POLICY_MISSING"
grep -q 'RAMZY_VOICE_IO_V1' backend/src/agency-operator/services/ramzyVoice.service.js || fail "PHASE11_VOICE_SERVICE_MISSING"
echo "CONTRACT_CHECKS=PASS"

git diff --check -- "$TARGET"
echo "GIT_DIFF_CHECK=PASS"

TEST_HASH_AFTER="$(sha256sum "$TEST" | awk '{print $1}')"
[[ "$TEST_HASH_BEFORE" == "$TEST_HASH_AFTER" ]] || fail "REGRESSION_TEST_CHANGED"

POST_STATUS="$(git status --short)"
printf '%s\n' "$POST_STATUS" | grep -Fq " $TARGET" || fail "PHASE14_GUARD_TARGET_NOT_CHANGED"
if [[ "$(strip_target_status "$PRE_STATUS")" != "$(strip_target_status "$POST_STATUS")" ]]; then
  fail "UNRELATED_WORKTREE_CHANGED"
fi

FRONTEND_STATUS_AFTER="$(git status --short -- frontend)"
FRONTEND_DIFF_AFTER="$(git diff --binary -- frontend | sha256sum | awk '{print $1}')"
SCHEMA_PACKAGE_DIFF_AFTER="$(git diff --binary -- backend/prisma backend/package.json frontend/package.json | sha256sum | awk '{print $1}')"
[[ "$FRONTEND_STATUS_BEFORE" == "$FRONTEND_STATUS_AFTER" && "$FRONTEND_DIFF_BEFORE" == "$FRONTEND_DIFF_AFTER" ]] || fail "TEAM_PERFORMANCE_V3_2_CHANGED"
[[ "$SCHEMA_PACKAGE_DIFF_BEFORE" == "$SCHEMA_PACKAGE_DIFF_AFTER" ]] || fail "SCHEMA_OR_PACKAGE_DIFF_CHANGED"
echo "UNRELATED_WORK_PRESERVED=YES"
echo "TEAM_PERFORMANCE_V3_2_PRESERVED=YES"
echo "REGRESSION_TEST_UNCHANGED=YES"
echo "NO_SCHEMA_MIGRATION_PACKAGE_CHANGE_THIS_RUN=YES"

BACKEND_PM2=""
if pm2 describe tamiyouz-system >/dev/null 2>&1; then
  BACKEND_PM2="tamiyouz-system"
elif pm2 describe tamiyouz-backend >/dev/null 2>&1; then
  BACKEND_PM2="tamiyouz-backend"
else
  fail "BACKEND_PM2_NOT_FOUND"
fi
pm2 reload "$BACKEND_PM2"
sleep 4
pm2 describe "$BACKEND_PM2" | grep -qi 'online' || fail "BACKEND_PM2_NOT_ONLINE"
echo "BACKEND_RELOAD=PASS"

for url in "/health" "/dashboard" "/team-performance" "/tasks"; do
  code="000"
  for _ in 1 2 3 4 5; do
    code="$(curl -ksS -o /dev/null -w '%{http_code}' "$DOMAIN$url" || true)"
    [[ "$code" == "200" ]] && break
    sleep 2
  done
  echo "HTTP_${url//\//_}=$code"
  [[ "$code" == "200" ]] || fail "HTTP_SMOKE_FAILED:${url}:${code}"
done
echo "HTTP_SMOKE=PASS"

AGENT_AUTH="$(public_code /api/agent/status)"
VOICE_AUTH="$(public_code /api/agent/voice/status)"
echo "AGENT_STATUS_UNAUTH_HTTP=$AGENT_AUTH"
echo "VOICE_STATUS_UNAUTH_HTTP=$VOICE_AUTH"
[[ "$AGENT_AUTH" == "401" ]] || fail "AGENT_AUTH_BOUNDARY_FAILED:$AGENT_AUTH"
[[ "$VOICE_AUTH" == "401" ]] || fail "VOICE_AUTH_BOUNDARY_FAILED:$VOICE_AUTH"
echo "AUTH_BOUNDARY_E2E=PASS"

echo "NO_FRONTEND_DEPLOY_THIS_RUN=YES"
echo "NO_COMMIT_OR_PUSH=YES"
echo "PHASE14_CONVERSATIONAL_ACTION_MEMORY=PASS"
echo "PASS/FAIL=PASS"
echo "--- git status --short ---"
git status --short
