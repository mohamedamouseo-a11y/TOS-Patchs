#!/usr/bin/env bash
set -euo pipefail

TOS_ROOT="/var/www/TOS"
PATCH_DIR="$(cd "$(dirname "$0")" && pwd)"
BASELINE="ccda1f7e378c1ef8d1045a55aaca3b6376ce6369"
GENERATOR="$PATCH_DIR/01_phase15_multi_step_voice_operations.py"
DOMAIN="https://tos.tamiyouz.com"

TARGET_FILES=(
  "backend/src/agency-operator/services/ramzyMultiStepOperations.service.js"
  "backend/src/agency-operator/tests/ramzyMultiStepVoiceOperationsPhase15.static.test.js"
  "backend/src/agency-operator/tools/createRamzyTools.js"
  "backend/src/agency-operator/services/ramzyRuntime.service.js"
  "backend/src/agency-operator/prompts/ramzyPrompt.js"
  "backend/src/routes/agent.routes.js"
  "frontend/src/components/RamzyAssistant.jsx"
)

fail() {
  echo "PASS/FAIL=FAIL"
  echo "PHASE15_MULTI_STEP_VOICE_OPERATIONS=FAIL"
  echo "REASON=$1"
  exit 1
}

is_target() {
  local path="$1"
  for file in "${TARGET_FILES[@]}"; do
    [[ "$path" == "$file" ]] && return 0
  done
  return 1
}

filter_non_targets() {
  local status="$1"
  printf '%s\n' "$status" | while IFS= read -r line; do
    [[ -z "$line" ]] && continue
    local path="${line:3}"
    if ! is_target "$path"; then printf '%s\n' "$line"; fi
  done | sort
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

dir_hash() {
  local dir="$1"
  (cd "$dir" && find . -type f -print0 | sort -z | xargs -0 sha256sum) | sha256sum | awk '{print $1}'
}

echo "RUNNING=RAMZY_PHASE15_MULTI_STEP_VOICE_OPERATIONS_V1"
cd "$TOS_ROOT"
CURRENT_HEAD="$(git rev-parse HEAD)"
echo "CURRENT_TOS_HEAD=$CURRENT_HEAD"
if ! git merge-base --is-ancestor "$BASELINE" "$CURRENT_HEAD"; then
  fail "PHASE15_BASELINE_NOT_ANCESTOR"
fi

PRE_STATUS="$(git status --short)"
while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  path="${line:3}"
  if is_target "$path"; then fail "PHASE15_TARGET_FILE_ALREADY_DIRTY:$path"; fi
done <<< "$PRE_STATUS"
for new_file in \
  backend/src/agency-operator/services/ramzyMultiStepOperations.service.js \
  backend/src/agency-operator/tests/ramzyMultiStepVoiceOperationsPhase15.static.test.js; do
  [[ ! -e "$new_file" ]] || fail "PHASE15_NEW_FILE_ALREADY_EXISTS:$new_file"
done
echo "PRE_STATE=TARGET_FILES_CLEAN"

[[ -f "$GENERATOR" ]] || fail "PHASE15_GENERATOR_NOT_FOUND"
python3 "$GENERATOR"
echo "PATCH_APPLY=PASS"

# Phase 15 contracts.
grep -q 'RAMZY_MULTI_STEP_OPERATIONS_V1' backend/src/agency-operator/services/ramzyMultiStepOperations.service.js || fail "MULTI_STEP_VERSION_MISSING"
grep -q 'MULTI_STEP_TASK_OPERATION' backend/src/agency-operator/services/ramzyMultiStepOperations.service.js || fail "MULTI_STEP_ACTION_MISSING"
grep -q 'MAX_STEPS = 5' backend/src/agency-operator/services/ramzyMultiStepOperations.service.js || fail "MULTI_STEP_BOUND_MISSING"
grep -q 'alwaysExplicitConfirmation: true' backend/src/agency-operator/services/ramzyMultiStepOperations.service.js || fail "MULTI_STEP_CONFIRMATION_MISSING"
grep -q 'directExecutionEnabled: false' backend/src/agency-operator/services/ramzyMultiStepOperations.service.js || fail "MULTI_STEP_DIRECT_DISABLE_MISSING"
grep -q 'SEQUENTIAL_NO_ROLLBACK' backend/src/agency-operator/services/ramzyMultiStepOperations.service.js || fail "MULTI_STEP_EXECUTION_MODE_MISSING"
grep -q 'PARTIAL_SUCCESS' backend/src/agency-operator/services/ramzyMultiStepOperations.service.js || fail "PARTIAL_SUCCESS_MISSING"
grep -q 'status: "SKIPPED"' backend/src/agency-operator/services/ramzyMultiStepOperations.service.js || fail "DEPENDENCY_SKIP_MISSING"
grep -q 'executeApprovedTaskAction' backend/src/agency-operator/services/ramzyMultiStepOperations.service.js || fail "EXISTING_TASK_SERVICE_REUSE_MISSING"
grep -q 'assertAgentTaskCreateAccess' backend/src/agency-operator/services/ramzyMultiStepOperations.service.js || fail "CREATE_RBAC_RECHECK_MISSING"
grep -q 'assertAgentTaskActionAccess' backend/src/agency-operator/services/ramzyMultiStepOperations.service.js || fail "TASK_RBAC_RECHECK_MISSING"
grep -q 'assertAssigneeInProject' backend/src/agency-operator/services/ramzyMultiStepOperations.service.js || fail "ASSIGNEE_PROJECT_RECHECK_MISSING"
grep -q 'canActorAssignTargetUser' backend/src/agency-operator/services/ramzyMultiStepOperations.service.js || fail "ASSIGNEE_RBAC_RECHECK_MISSING"

# Approval route must reauthorize before claim and distinguish all-failed from partial success.
grep -q 'assertMultiStepApprovalStillAuthorized' backend/src/routes/agent.routes.js || fail "ROUTE_MULTI_STEP_PRECLAIM_RBAC_MISSING"
grep -q 'executeApprovedMultiStepOperation' backend/src/routes/agent.routes.js || fail "ROUTE_MULTI_STEP_EXECUTOR_MISSING"
grep -q 'targetType === "CONVERSATION"' backend/src/routes/agent.routes.js || fail "ROUTE_MULTI_STEP_TARGET_MISSING"
grep -q 'result?.outcome === "FAILED"' backend/src/routes/agent.routes.js || fail "ROUTE_ALL_FAILED_STATUS_MISSING"

# Tool/runtime/prompt/frontend.
grep -q 'propose_multi_step_task_operation' backend/src/agency-operator/tools/createRamzyTools.js || fail "MULTI_STEP_TOOL_MISSING"
grep -q 'createMultiStepTaskOperationProposal' backend/src/agency-operator/tools/createRamzyTools.js || fail "MULTI_STEP_TOOL_SERVICE_BRIDGE_MISSING"
grep -q 'propose_multi_step_task_operation' backend/src/agency-operator/services/ramzyRuntime.service.js || fail "MULTI_STEP_SIDE_EFFECT_GUARD_MISSING"
grep -q 'Phase 15:' backend/src/agency-operator/prompts/ramzyPrompt.js || fail "PHASE15_PROMPT_MISSING"
grep -q 'Multi-Step Voice Operations' backend/src/agency-operator/prompts/ramzyPrompt.js || fail "PHASE15_PROMPT_NAME_MISSING"
grep -q 'PARTIAL_SUCCESS' backend/src/agency-operator/prompts/ramzyPrompt.js || fail "PHASE15_PARTIAL_REPORTING_RULE_MISSING"
grep -q 'MULTI_STEP_TASK_OPERATION' frontend/src/components/RamzyAssistant.jsx || fail "FRONTEND_MULTI_STEP_LABEL_MISSING"
grep -q 'publicSteps' frontend/src/components/RamzyAssistant.jsx || fail "FRONTEND_SAFE_PLAN_MISSING"
grep -q 'multiStepExecution' frontend/src/components/RamzyAssistant.jsx || fail "FRONTEND_RESULT_SUMMARY_MISSING"

# Previous safety boundaries must remain.
grep -q 'assertRamzyToolInvocationScope' backend/src/agency-operator/tools/createRamzyTools.js || fail "PHASE8_TOOL_SCOPE_GUARD_MISSING"
grep -q 'RAMZY_ACTION_CONFIRMATION_V1' backend/src/agency-operator/services/actionConfirmation.service.js || fail "PHASE13_CONFIRMATION_POLICY_MISSING"
grep -q 'RAMZY_CONVERSATIONAL_ACTION_DRAFT_V1' backend/src/agency-operator/services/ramzyActionDraft.service.js || fail "PHASE14_DRAFT_MEMORY_MISSING"
grep -q 'looksLikeActionDraftMessage(message) || !isHighConfidenceMemory(message)' backend/src/agency-operator/services/ramzyMemory.service.js || fail "PHASE14_PERSISTENT_MEMORY_GUARD_MISSING"
grep -q 'RAMZY_VOICE_IO_V1' backend/src/agency-operator/services/ramzyVoice.service.js || fail "PHASE11_VOICE_SERVICE_MISSING"
grep -q 'actionExecutionFromVoice: false' backend/src/agency-operator/services/ramzyVoice.service.js || fail "VOICE_DIRECT_EXECUTION_GUARD_MISSING"
echo "CONTRACT_CHECKS=PASS"

npm --prefix backend run test:ramzy
echo "BACKEND_TESTS=PASS"

git diff --check -- "${TARGET_FILES[@]}"
echo "GIT_DIFF_CHECK=PASS"

POST_STATUS="$(git status --short)"
if [[ "$(filter_non_targets "$PRE_STATUS")" != "$(filter_non_targets "$POST_STATUS")" ]]; then
  fail "UNRELATED_WORKTREE_CHANGED"
fi
for file in "${TARGET_FILES[@]}"; do
  if ! printf '%s\n' "$POST_STATUS" | grep -Fq " $file"; then
    fail "EXPECTED_PHASE15_FILE_NOT_CHANGED:$file"
  fi
done
echo "EXPECTED_CHANGED_FILES=PASS"
echo "UNRELATED_WORK_PRESERVED=YES"

if git diff --name-only -- backend/prisma backend/package.json frontend/package.json | grep -q .; then
  fail "FORBIDDEN_SCHEMA_MIGRATION_OR_PACKAGE_CHANGE"
fi
echo "NO_SCHEMA_MIGRATION_PACKAGE_CHANGE=YES"

npm --prefix frontend run build
echo "FRONTEND_BUILD=PASS"

rm -rf /opt/apps/tamiyouz-front/build/*
cp -a /var/www/TOS/frontend/dist/. /opt/apps/tamiyouz-front/build/
pm2 reload tamiyouz-frontend >/dev/null
sleep 2
pm2 describe tamiyouz-frontend | grep -qi 'online' || fail "FRONTEND_PM2_NOT_ONLINE"
echo "FRONTEND_DEPLOY=PASS"

SOURCE_DIST_HASH="$(dir_hash /var/www/TOS/frontend/dist)"
LIVE_DIST_HASH="$(dir_hash /opt/apps/tamiyouz-front/build)"
echo "SOURCE_DIST_SHA256=$SOURCE_DIST_HASH"
echo "LIVE_DIST_SHA256=$LIVE_DIST_HASH"
[[ "$SOURCE_DIST_HASH" == "$LIVE_DIST_HASH" ]] || fail "DEPLOYED_DIST_MISMATCH"
echo "DEPLOYED_DIST_MATCH=PASS"

BACKEND_PM2=""
if pm2 describe tamiyouz-system >/dev/null 2>&1; then
  BACKEND_PM2="tamiyouz-system"
elif pm2 describe tamiyouz-backend >/dev/null 2>&1; then
  BACKEND_PM2="tamiyouz-backend"
else
  fail "BACKEND_PM2_NOT_FOUND"
fi
pm2 reload "$BACKEND_PM2" >/dev/null
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

echo "NO_COMMIT_OR_PUSH=YES"
echo "PHASE15_MULTI_STEP_VOICE_OPERATIONS=PASS"
echo "PASS/FAIL=PASS"
echo "--- git status --short ---"
git status --short
