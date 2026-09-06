#!/usr/bin/env bash
set -euo pipefail

TOS_ROOT="/var/www/TOS"
PATCH_DIR="$(cd "$(dirname "$0")" && pwd)"
BASELINE="c177b43a2472adbbdf41e3f55683542dc4cef4c5"
REPAIR="$PATCH_DIR/04_phase14_persistent_guard_token_fix.py"
DOMAIN="https://tos.tamiyouz.com"

PHASE14_TARGET_FILES=(
  "backend/src/agency-operator/services/ramzyActionDraft.service.js"
  "backend/src/agency-operator/tests/ramzyConversationalActionMemoryPhase14.test.js"
  "backend/src/agency-operator/tests/ramzyActionDraftPersistentMemoryPhase14.test.js"
  "backend/src/agency-operator/services/contextResolution.service.js"
  "backend/src/agency-operator/services/ramzyMemory.service.js"
  "backend/src/agency-operator/services/ramzySystemIntelligence.service.js"
  "backend/src/agency-operator/tools/createRamzyTools.js"
  "backend/src/agency-operator/services/ramzyRuntime.service.js"
  "backend/src/agency-operator/prompts/ramzyPrompt.js"
)

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

echo "RUNNING=RAMZY_PHASE14_PERSISTENT_GUARD_TOKEN_FIX"
cd "$TOS_ROOT"
CURRENT_HEAD="$(git rev-parse HEAD)"
echo "CURRENT_TOS_HEAD=$CURRENT_HEAD"
if ! git merge-base --is-ancestor "$BASELINE" "$CURRENT_HEAD"; then
  fail "PHASE14_BASELINE_NOT_ANCESTOR"
fi

PRE_STATUS="$(git status --short)"
for file in "${PHASE14_TARGET_FILES[@]}"; do
  if ! printf '%s\n' "$PRE_STATUS" | grep -Fq " $file"; then
    fail "KNOWN_PHASE14_PARTIAL_FILE_NOT_DIRTY:$file"
  fi
done

grep -q 'RAMZY_CONVERSATIONAL_ACTION_DRAFT_V1' backend/src/agency-operator/services/ramzyActionDraft.service.js || fail "PHASE14_DRAFT_SERVICE_MISSING"
grep -q 'Space/end boundaries are Unicode-safe here.' backend/src/agency-operator/services/ramzyMemory.service.js || fail "EXPECTED_BROKEN_GUARD_STATE_NOT_FOUND"
grep -q 'Phase 14 task action commands are not promoted into long-term RamzyMemory' backend/src/agency-operator/tests/ramzyActionDraftPersistentMemoryPhase14.test.js || fail "PHASE14_PERSISTENT_TEST_MISSING"
echo "PRE_STATE=KNOWN_PHASE14_APPLIED_TOKEN_BOUNDARY_FAIL"

FRONTEND_STATUS_BEFORE="$(git status --short -- frontend)"
FRONTEND_DIFF_BEFORE="$(git diff --binary -- frontend | sha256sum | awk '{print $1}')"
SCHEMA_PACKAGE_DIFF_BEFORE="$(git diff --binary -- backend/prisma backend/package.json frontend/package.json | sha256sum | awk '{print $1}')"

[[ -f "$REPAIR" ]] || fail "PHASE14_TOKEN_FIX_NOT_FOUND"
python3 "$REPAIR"
echo "PATCH_APPLY=PASS"

# Behavioral check before the suite: direct action commands must be blocked from long-term memory,
# while genuine workflow preferences remain eligible for normal memory classification.
node --input-type=module <<'NODE'
import { __testables } from './backend/src/agency-operator/services/ramzyMemory.service.js';
const yes = [
  'عايز اعمل تاسك ليوسف',
  'create task for Youssef',
  'اسند التاسك ليوسف',
  'ضيف comment على التاسك',
  'غير موعد التاسك لبكرة',
];
for (const sample of yes) {
  if (__testables.looksLikeActionDraftMessage(sample) !== true) {
    console.error(`TOKEN_GUARD_EXPECTED_TRUE_FAILED=${sample}`);
    process.exit(21);
  }
}
const no = [
  'دائمًا لما أقول اعمل تاسك اسألني عن المشروع الأول',
  'أفضل أن تكون كل المهام المهمة High',
];
for (const sample of no) {
  if (__testables.looksLikeActionDraftMessage(sample) !== false) {
    console.error(`TOKEN_GUARD_EXPECTED_FALSE_FAILED=${sample}`);
    process.exit(22);
  }
}
console.log('PERSISTENT_GUARD_BEHAVIOR=PASS');
NODE

node --test backend/src/agency-operator/tests/ramzyActionDraftPersistentMemoryPhase14.test.js
echo "PERSISTENT_MEMORY_REGRESSION_TEST=PASS"

npm --prefix backend run test:ramzy
echo "BACKEND_TESTS=PASS"

# Phase 14 safety contracts.
grep -q 'const startsWithVerb = (verbs)' backend/src/agency-operator/services/ramzyMemory.service.js || fail "TOKEN_VERB_DETECTOR_MISSING"
grep -q 'taskToken.test(value)' backend/src/agency-operator/services/ramzyMemory.service.js || fail "TASK_TOKEN_DETECTOR_MISSING"
grep -q 'looksLikeActionDraftMessage(message) || !isHighConfidenceMemory(message)' backend/src/agency-operator/services/ramzyMemory.service.js || fail "PERSISTENT_ACTION_SKIP_MISSING"
grep -q 'authorizationTrusted: false' backend/src/agency-operator/services/ramzyActionDraft.service.js || fail "MEMORY_AUTH_UNTRUSTED_MARKER_MISSING"
grep -q 'targetReferencesTrusted: false' backend/src/agency-operator/services/ramzyActionDraft.service.js || fail "MEMORY_TARGET_UNTRUSTED_MARKER_MISSING"
grep -q 'materializeConversationActionDraft' backend/src/agency-operator/services/ramzyActionDraft.service.js || fail "DRAFT_MATERIALIZATION_MISSING"
grep -q 'assertAgentTaskCreateAccess' backend/src/agency-operator/services/ramzyActionDraft.service.js || fail "DRAFT_CREATE_RBAC_RECHECK_MISSING"
grep -q 'assertAgentTaskActionAccess' backend/src/agency-operator/services/ramzyActionDraft.service.js || fail "DRAFT_TASK_RBAC_RECHECK_MISSING"
grep -q 'assertRamzyToolInvocationScope' backend/src/agency-operator/tools/createRamzyTools.js || fail "PHASE8_SCOPE_GUARD_MISSING"
grep -q 'RAMZY_ACTION_CONFIRMATION_V1' backend/src/agency-operator/services/actionConfirmation.service.js || fail "PHASE13_CONFIRMATION_POLICY_MISSING"
grep -q 'RAMZY_VOICE_IO_V1' backend/src/agency-operator/services/ramzyVoice.service.js || fail "PHASE11_VOICE_SERVICE_MISSING"
echo "CONTRACT_CHECKS=PASS"

git diff --check -- "${PHASE14_TARGET_FILES[@]}"
echo "GIT_DIFF_CHECK=PASS"

POST_STATUS="$(git status --short)"
if [[ "$PRE_STATUS" != "$POST_STATUS" ]]; then
  fail "WORKTREE_STATUS_SHAPE_CHANGED"
fi

FRONTEND_STATUS_AFTER="$(git status --short -- frontend)"
FRONTEND_DIFF_AFTER="$(git diff --binary -- frontend | sha256sum | awk '{print $1}')"
SCHEMA_PACKAGE_DIFF_AFTER="$(git diff --binary -- backend/prisma backend/package.json frontend/package.json | sha256sum | awk '{print $1}')"
if [[ "$FRONTEND_STATUS_BEFORE" != "$FRONTEND_STATUS_AFTER" || "$FRONTEND_DIFF_BEFORE" != "$FRONTEND_DIFF_AFTER" ]]; then
  fail "UNRELATED_FRONTEND_V3_2_CHANGED"
fi
if [[ "$SCHEMA_PACKAGE_DIFF_BEFORE" != "$SCHEMA_PACKAGE_DIFF_AFTER" ]]; then
  fail "SCHEMA_OR_PACKAGE_DIFF_CHANGED"
fi
echo "UNRELATED_WORK_PRESERVED=YES"
echo "TEAM_PERFORMANCE_V3_2_LOCAL_WORK_PRESERVED=YES"
echo "FRONTEND_SOURCE_CHANGE_THIS_RUN=NO"
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
