#!/usr/bin/env bash
set -euo pipefail

TOS_ROOT="/var/www/TOS"
PATCH_DIR="$(cd "$(dirname "$0")" && pwd)"
BASELINE="f22b0d94271477e2a58aa6d53e560b099c64356c"
GENERATOR="$PATCH_DIR/01_phase12_voice_task_actions.py"
DOMAIN="https://tos.tamiyouz.com"

TARGET_FILES=(
  "backend/src/agency-operator/services/semanticIntentResolver.service.js"
  "backend/src/agency-operator/policies/agentAccess.service.js"
  "backend/src/agency-operator/services/actionGroundingValidation.service.js"
  "backend/src/agency-operator/services/ramzySystemIntelligence.service.js"
  "backend/src/agency-operator/services/taskCommands.service.js"
  "backend/src/agency-operator/tools/createRamzyTools.js"
  "backend/src/routes/agent.routes.js"
  "backend/src/agency-operator/prompts/ramzyPrompt.js"
  "frontend/src/components/RamzyAssistant.jsx"
  "backend/src/agency-operator/tests/ramzyVoiceTaskActionsPhase12.static.test.js"
)

fail() {
  echo "PHASE12_VOICE_TASK_ACTIONS=FAIL"
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
  local method="$1"
  local path="$2"
  local body="${3:-}"
  local code="000"
  for _ in 1 2 3 4 5; do
    if [[ "$method" == "POST" ]]; then
      code="$(curl -ksS -o /dev/null -w '%{http_code}' -X POST -H 'Content-Type: application/json' --data "$body" "$DOMAIN$path" || true)"
    else
      code="$(curl -ksS -o /dev/null -w '%{http_code}' "$DOMAIN$path" || true)"
    fi
    [[ "$code" != "000" && "$code" != "502" && "$code" != "503" ]] && break
    sleep 2
  done
  printf '%s' "$code"
}

echo "RUNNING=RAMZY_PHASE12_VOICE_TASK_ACTIONS_V1"
cd "$TOS_ROOT"
CURRENT_HEAD="$(git rev-parse HEAD)"
echo "CURRENT_TOS_HEAD=$CURRENT_HEAD"
if ! git merge-base --is-ancestor "$BASELINE" "$CURRENT_HEAD"; then
  fail "PHASE12_BASELINE_NOT_ANCESTOR"
fi

PRE_STATUS="$(git status --short)"
while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  path="${line:3}"
  if is_target "$path"; then
    fail "PHASE12_TARGET_FILE_ALREADY_DIRTY:$path"
  fi
done <<< "$PRE_STATUS"
echo "PRE_STATE=TARGET_FILES_CLEAN"

[[ -f "$GENERATOR" ]] || fail "GENERATOR_NOT_FOUND"
python3 "$GENERATOR"
echo "PATCH_APPLY=PASS"

# Phase 12 contracts: CREATE_TASK joins the same approval/RBAC path used by typed actions.
grep -q '"CREATE_TASK"' backend/src/agency-operator/services/semanticIntentResolver.service.js || fail "CREATE_TASK_SEMANTIC_SUPPORT_MISSING"
grep -q 'assertAgentTaskCreateAccess' backend/src/agency-operator/policies/agentAccess.service.js || fail "CREATE_TASK_ACCESS_GUARD_MISSING"
grep -q 'TASK_CREATE_GROUNDED_AND_AUTHORIZED' backend/src/agency-operator/services/actionGroundingValidation.service.js || fail "CREATE_TASK_GROUNDING_MISSING"
grep -q 'projectResolution' backend/src/agency-operator/services/actionGroundingValidation.service.js || fail "CREATE_TASK_PROJECT_GROUNDING_MISSING"
grep -q 'detectedIntent === "TASK_CREATE"' backend/src/agency-operator/services/ramzySystemIntelligence.service.js || fail "CREATE_TASK_INTELLIGENCE_MISSING"
grep -q 'actionType === "CREATE_TASK"' backend/src/agency-operator/services/taskCommands.service.js || fail "CREATE_TASK_COMMAND_MISSING"
grep -q 'targetType = "PROJECT"' backend/src/agency-operator/services/taskCommands.service.js || fail "CREATE_TASK_PROJECT_APPROVAL_TARGET_MISSING"
grep -q 'ensureProjectDefaultWorkspaceBoard' backend/src/agency-operator/services/taskCommands.service.js || fail "CREATE_TASK_BOARD_SERVICE_REUSE_MISSING"
grep -q 'CREATE_TASK.*ADD_COMMENT' backend/src/agency-operator/tools/createRamzyTools.js || grep -q '"CREATE_TASK"' backend/src/agency-operator/tools/createRamzyTools.js || fail "CREATE_TASK_TOOL_SCHEMA_MISSING"
grep -q 'isCreateTaskApproval' backend/src/routes/agent.routes.js || fail "CREATE_TASK_APPROVAL_ROUTE_MISSING"
grep -q 'assertAgentTaskCreateAccess' backend/src/routes/agent.routes.js || fail "CREATE_TASK_DECISION_REAUTH_MISSING"
grep -q 'Phase 12:' backend/src/agency-operator/prompts/ramzyPrompt.js || fail "PHASE12_PROMPT_RULE_MISSING"
grep -q 'CREATE_TASK: { ar: "إنشاء مهمة", en: "Create task" }' frontend/src/components/RamzyAssistant.jsx || fail "CREATE_TASK_APPROVAL_UI_MISSING"

# Phase 11 must remain intact: voice is only an input/output transport and never an RBAC bypass.
grep -q 'RAMZY_VOICE_IO_V1' backend/src/agency-operator/services/ramzyVoice.service.js || fail "PHASE11_VOICE_SERVICE_MISSING"
grep -q 'actionExecutionFromVoice: false' backend/src/agency-operator/services/ramzyVoice.service.js || fail "VOICE_DIRECT_EXECUTION_GUARD_MISSING"
grep -q 'providerSecretsExposedToBrowser: false' backend/src/agency-operator/services/ramzyVoice.service.js || fail "VOICE_SECRET_GUARD_MISSING"

echo "CONTRACT_CHECKS=PASS"

npm --prefix backend run test:ramzy
echo "BACKEND_TESTS=PASS"

npm --prefix frontend run build
echo "FRONTEND_BUILD=PASS"

git diff --check -- "${TARGET_FILES[@]}"
echo "GIT_DIFF_CHECK=PASS"

POST_STATUS="$(git status --short)"
if [[ "$(filter_non_targets "$PRE_STATUS")" != "$(filter_non_targets "$POST_STATUS")" ]]; then
  fail "UNRELATED_WORKTREE_CHANGED"
fi
for file in "${TARGET_FILES[@]}"; do
  if ! printf '%s\n' "$POST_STATUS" | grep -Fq " $file"; then
    fail "EXPECTED_PHASE12_FILE_NOT_CHANGED:$file"
  fi
done
echo "EXPECTED_CHANGED_FILES=PASS"
echo "UNRELATED_WORK_PRESERVED=YES"

# Phase 12 must not touch schema, migrations, packages, performance scoring or default permission grants.
if git diff --name-only -- backend/prisma frontend/package.json backend/package.json | grep -q .; then
  fail "FORBIDDEN_SCHEMA_OR_PACKAGE_CHANGE"
fi
echo "NO_SCHEMA_MIGRATION_PACKAGE_CHANGE=YES"

# Deploy frontend because Ramzy approval UI changed.
rm -rf /opt/apps/tamiyouz-front/build/*
cp -a /var/www/TOS/frontend/dist/. /opt/apps/tamiyouz-front/build/
pm2 reload tamiyouz-frontend
sleep 2
pm2 describe tamiyouz-frontend | grep -qi 'online' || fail "FRONTEND_PM2_NOT_ONLINE"
echo "FRONTEND_DEPLOY=PASS"

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

# Public auth/CSRF boundary only; never assume a localhost port.
AGENT_AUTH="$(public_code GET /api/agent/status)"
VOICE_AUTH="$(public_code GET /api/agent/voice/status)"
VOICE_TTS_AUTH="$(public_code POST /api/agent/voice/synthesize '{"text":"hello"}')"
echo "AGENT_STATUS_UNAUTH_HTTP=$AGENT_AUTH"
echo "VOICE_STATUS_UNAUTH_HTTP=$VOICE_AUTH"
echo "VOICE_SYNTHESIZE_UNAUTH_HTTP=$VOICE_TTS_AUTH"
[[ "$AGENT_AUTH" == "401" ]] || fail "AGENT_AUTH_BOUNDARY_FAILED:$AGENT_AUTH"
[[ "$VOICE_AUTH" == "401" ]] || fail "VOICE_STATUS_AUTH_BOUNDARY_FAILED:$VOICE_AUTH"
[[ "$VOICE_TTS_AUTH" == "401" || "$VOICE_TTS_AUTH" == "403" ]] || fail "VOICE_SYNTHESIZE_AUTH_CSRF_BOUNDARY_FAILED:$VOICE_TTS_AUTH"
echo "AUTH_BOUNDARY_E2E=PASS"

if ! diff -qr /var/www/TOS/frontend/dist /opt/apps/tamiyouz-front/build >/dev/null; then
  fail "DEPLOYED_DIST_MISMATCH"
fi
echo "DEPLOYED_DIST_MATCH=PASS"

echo "NO_COMMIT_OR_PUSH=YES"
echo "PHASE12_VOICE_TASK_ACTIONS=PASS"
echo "--- git status --short ---"
git status --short
