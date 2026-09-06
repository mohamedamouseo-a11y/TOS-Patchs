#!/usr/bin/env bash
set -euo pipefail

TOS_ROOT="/var/www/TOS"
PATCH_DIR="$(cd "$(dirname "$0")" && pwd)"
BASELINE="c177b43a2472adbbdf41e3f55683542dc4cef4c5"
GENERATOR="$PATCH_DIR/01_phase14_conversational_action_memory.py"
DOMAIN="https://tos.tamiyouz.com"

TARGET_FILES=(
  "backend/src/agency-operator/services/ramzyActionDraft.service.js"
  "backend/src/agency-operator/tests/ramzyConversationalActionMemoryPhase14.test.js"
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

echo "RUNNING=RAMZY_PHASE14_CONVERSATIONAL_ACTION_MEMORY_V1"
cd "$TOS_ROOT"
CURRENT_HEAD="$(git rev-parse HEAD)"
echo "CURRENT_TOS_HEAD=$CURRENT_HEAD"
if ! git merge-base --is-ancestor "$BASELINE" "$CURRENT_HEAD"; then
  fail "PHASE14_BASELINE_NOT_ANCESTOR"
fi

PRE_STATUS="$(git status --short)"
while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  path="${line:3}"
  if is_target "$path"; then fail "PHASE14_TARGET_FILE_ALREADY_DIRTY:$path"; fi
done <<< "$PRE_STATUS"
for new_file in \
  backend/src/agency-operator/services/ramzyActionDraft.service.js \
  backend/src/agency-operator/tests/ramzyConversationalActionMemoryPhase14.test.js; do
  [[ ! -e "$new_file" ]] || fail "PHASE14_NEW_FILE_ALREADY_EXISTS:$new_file"
done
echo "PRE_STATE=TARGET_FILES_CLEAN"

[[ -f "$GENERATOR" ]] || fail "PHASE14_GENERATOR_NOT_FOUND"
python3 "$GENERATOR"
echo "PATCH_APPLY=PASS"

# Phase 14 memory boundaries.
grep -q 'RAMZY_CONVERSATIONAL_ACTION_DRAFT_V1' backend/src/agency-operator/services/ramzyActionDraft.service.js || fail "ACTION_DRAFT_VERSION_MISSING"
grep -q 'scope: "CONVERSATION_ONLY"' backend/src/agency-operator/services/ramzyActionDraft.service.js || fail "ACTION_DRAFT_SCOPE_MISSING"
grep -q 'authorizationTrusted: false' backend/src/agency-operator/services/ramzyActionDraft.service.js || fail "MEMORY_AUTH_UNTRUSTED_MARKER_MISSING"
grep -q 'targetReferencesTrusted: false' backend/src/agency-operator/services/ramzyActionDraft.service.js || fail "MEMORY_TARGET_UNTRUSTED_MARKER_MISSING"
grep -q 'ACTION_DRAFT_TTL_MS' backend/src/agency-operator/services/ramzyActionDraft.service.js || fail "ACTION_DRAFT_EXPIRY_MISSING"

# Revalidation must happen when writing target refs and again before proposal materialization.
grep -q 'assertAgentTaskCreateAccess' backend/src/agency-operator/services/ramzyActionDraft.service.js || fail "DRAFT_CREATE_RBAC_RECHECK_MISSING"
grep -q 'assertAgentTaskActionAccess' backend/src/agency-operator/services/ramzyActionDraft.service.js || fail "DRAFT_TASK_RBAC_RECHECK_MISSING"
grep -q 'assertAssigneeInProject' backend/src/agency-operator/services/ramzyActionDraft.service.js || fail "DRAFT_ASSIGNEE_PROJECT_RECHECK_MISSING"
grep -q 'canActorAssignTargetUser' backend/src/agency-operator/services/ramzyActionDraft.service.js || fail "DRAFT_ASSIGNMENT_RBAC_RECHECK_MISSING"
grep -q 'materializeConversationActionDraft' backend/src/agency-operator/services/ramzyActionDraft.service.js || fail "DRAFT_MATERIALIZATION_MISSING"

# Conversation continuity and provider-safe draft view.
grep -q 'actionDraft: previous.actionDraft' backend/src/agency-operator/services/contextResolution.service.js || fail "CONTEXT_DRAFT_PRESERVATION_MISSING"
grep -q 'CONVERSATIONAL_ACTION_DRAFT' backend/src/agency-operator/services/contextResolution.service.js || fail "CONTEXT_CONFIG_DRAFT_MISSING"
grep -q 'conversation_action_draft' backend/src/agency-operator/services/ramzyMemory.service.js || fail "MEMORY_PROMPT_DRAFT_MISSING"
grep -q 'publicActionDraftView' backend/src/agency-operator/services/ramzySystemIntelligence.service.js || fail "INTELLIGENCE_PUBLIC_DRAFT_VIEW_MISSING"
grep -q 'safePromptActiveContext' backend/src/agency-operator/services/ramzySystemIntelligence.service.js || fail "INTELLIGENCE_PRIVATE_DRAFT_FILTER_MISSING"

# Tool chain: draft -> fresh materialization -> existing Phase 13 approval path.
for tool in get_task_action_draft update_task_action_draft discard_task_action_draft propose_task_action_draft; do
  grep -q "$tool" backend/src/agency-operator/tools/createRamzyTools.js || fail "PHASE14_TOOL_MISSING:$tool"
done
grep -q 'materializeConversationActionDraft' backend/src/agency-operator/tools/createRamzyTools.js || fail "DRAFT_TOOL_MATERIALIZATION_BRIDGE_MISSING"
grep -q 'createTaskActionProposal' backend/src/agency-operator/tools/createRamzyTools.js || fail "PHASE13_PROPOSAL_REUSE_MISSING"
grep -q 'discardConversationActionDraft' backend/src/agency-operator/tools/createRamzyTools.js || fail "DRAFT_CLEAR_AFTER_PROPOSAL_MISSING"
grep -q 'executeLowRiskTaskActionApproval' backend/src/agency-operator/tools/createRamzyTools.js || fail "PHASE13_LOW_RISK_POLICY_REUSE_MISSING"
grep -q 'update_task_action_draft' backend/src/agency-operator/services/ramzyRuntime.service.js || fail "DRAFT_FALLBACK_SIDE_EFFECT_GUARD_MISSING"
grep -q 'propose_task_action_draft' backend/src/agency-operator/services/ramzyRuntime.service.js || fail "DRAFT_PROPOSAL_SIDE_EFFECT_GUARD_MISSING"

# Prompt and earlier security invariants.
grep -q 'Phase 14:' backend/src/agency-operator/prompts/ramzyPrompt.js || fail "PHASE14_PROMPT_MISSING"
grep -q 'Conversational Action Memory' backend/src/agency-operator/prompts/ramzyPrompt.js || fail "PHASE14_PROMPT_NAME_MISSING"
grep -q 'لا تثق في المسودة كصلاحية' backend/src/agency-operator/prompts/ramzyPrompt.js || fail "PHASE14_MEMORY_NOT_AUTH_RULE_MISSING"
grep -q 'assertRamzyToolInvocationScope' backend/src/agency-operator/tools/createRamzyTools.js || fail "PHASE8_TOOL_SCOPE_GUARD_MISSING"
grep -q 'RAMZY_ACTION_CONFIRMATION_V1' backend/src/agency-operator/services/actionConfirmation.service.js || fail "PHASE13_CONFIRMATION_POLICY_MISSING"
grep -q 'TASK_CREATE_GROUNDED_AND_AUTHORIZED' backend/src/agency-operator/services/actionGroundingValidation.service.js || fail "PHASE12_ACTION_GROUNDING_MISSING"
grep -q 'RAMZY_VOICE_IO_V1' backend/src/agency-operator/services/ramzyVoice.service.js || fail "PHASE11_VOICE_SERVICE_MISSING"
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
    fail "EXPECTED_PHASE14_FILE_NOT_CHANGED:$file"
  fi
done
echo "EXPECTED_CHANGED_FILES=PASS"
echo "UNRELATED_WORK_PRESERVED=YES"

if git diff --name-only -- backend/prisma backend/package.json frontend/package.json | grep -q .; then
  fail "FORBIDDEN_SCHEMA_MIGRATION_OR_PACKAGE_CHANGE"
fi
echo "NO_SCHEMA_MIGRATION_PACKAGE_CHANGE=YES"
echo "FRONTEND_SOURCE_CHANGE_BY_PHASE14=NO"

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

echo "NO_COMMIT_OR_PUSH=YES"
echo "PHASE14_CONVERSATIONAL_ACTION_MEMORY=PASS"
echo "PASS/FAIL=PASS"
echo "--- git status --short ---"
git status --short
