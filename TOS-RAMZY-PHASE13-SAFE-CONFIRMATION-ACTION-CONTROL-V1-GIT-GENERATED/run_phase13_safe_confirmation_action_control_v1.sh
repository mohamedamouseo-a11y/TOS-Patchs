#!/usr/bin/env bash
set -euo pipefail

TOS_ROOT="/var/www/TOS"
PATCH_DIR="$(cd "$(dirname "$0")" && pwd)"
BASELINE="f8d892f2b596cf4f09863cfac7545aa279a7a6e7"
GENERATOR="$PATCH_DIR/01_phase13_safe_confirmation_action_control.py"
DOMAIN="https://tos.tamiyouz.com"

TARGET_FILES=(
  "backend/src/agency-operator/services/actionConfirmation.service.js"
  "backend/src/agency-operator/services/taskCommands.service.js"
  "backend/src/agency-operator/tools/createRamzyTools.js"
  "backend/src/agency-operator/services/ramzyRuntime.service.js"
  "backend/src/routes/agent.routes.js"
  "backend/src/agency-operator/prompts/ramzyPrompt.js"
  "backend/src/agency-operator/tests/ramzyActionConfirmationPhase13.static.test.js"
  "frontend/src/lib/api.js"
  "frontend/src/components/RamzyAssistant.jsx"
  "frontend/src/components/ramzyActionControlPhase13.css"
)

fail() {
  echo "PHASE13_SAFE_CONFIRMATION_ACTION_CONTROL=FAIL"
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

echo "RUNNING=RAMZY_PHASE13_SAFE_CONFIRMATION_ACTION_CONTROL_V1"
cd "$TOS_ROOT"
CURRENT_HEAD="$(git rev-parse HEAD)"
echo "CURRENT_TOS_HEAD=$CURRENT_HEAD"
if ! git merge-base --is-ancestor "$BASELINE" "$CURRENT_HEAD"; then
  fail "PHASE13_BASELINE_NOT_ANCESTOR"
fi

PRE_STATUS="$(git status --short)"
while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  path="${line:3}"
  if is_target "$path"; then
    fail "PHASE13_TARGET_FILE_ALREADY_DIRTY:$path"
  fi
done <<< "$PRE_STATUS"
echo "PRE_STATE=TARGET_FILES_CLEAN"

for new_file in \
  backend/src/agency-operator/services/actionConfirmation.service.js \
  backend/src/agency-operator/tests/ramzyActionConfirmationPhase13.static.test.js \
  frontend/src/components/ramzyActionControlPhase13.css; do
  [[ ! -e "$new_file" ]] || fail "PHASE13_NEW_FILE_ALREADY_EXISTS:$new_file"
done

[[ -f "$GENERATOR" ]] || fail "PHASE13_GENERATOR_NOT_FOUND"
python3 "$GENERATOR"
echo "PATCH_APPLY=PASS"

# Core Phase 13 policy contracts.
grep -q 'RAMZY_ACTION_CONFIRMATION_V1' backend/src/agency-operator/services/actionConfirmation.service.js || fail "CONFIRMATION_POLICY_VERSION_MISSING"
grep -q 'CREATE_TASK: Object.freeze({ riskLevel: "HIGH"' backend/src/agency-operator/services/actionConfirmation.service.js || fail "CREATE_TASK_HIGH_RISK_MISSING"
grep -q 'CHANGE_ASSIGNEE: Object.freeze({ riskLevel: "HIGH"' backend/src/agency-operator/services/actionConfirmation.service.js || fail "ASSIGNEE_HIGH_RISK_MISSING"
grep -q 'CHANGE_DUE_DATE: Object.freeze({ riskLevel: "MEDIUM"' backend/src/agency-operator/services/actionConfirmation.service.js || fail "DUE_DATE_MEDIUM_RISK_MISSING"
grep -q 'ADD_CHECKLIST: Object.freeze({ riskLevel: "MEDIUM"' backend/src/agency-operator/services/actionConfirmation.service.js || fail "CHECKLIST_MEDIUM_RISK_MISSING"
grep -q 'ADD_COMMENT: Object.freeze({ riskLevel: "LOW"' backend/src/agency-operator/services/actionConfirmation.service.js || fail "COMMENT_LOW_RISK_MISSING"
grep -q 'RAMZY_LOW_RISK_DIRECT_ACTIONS' backend/src/agency-operator/services/actionConfirmation.service.js || fail "LOW_RISK_DIRECT_OPT_IN_MISSING"
grep -q 'profile.riskLevel === "LOW"' backend/src/agency-operator/services/actionConfirmation.service.js || fail "DIRECT_LOW_RISK_ONLY_GUARD_MISSING"
grep -q 'assertLowRiskDirectActionAllowed' backend/src/agency-operator/services/taskCommands.service.js || fail "DIRECT_SERVER_GUARD_MISSING"

# Revise-draft contracts: no project/assignee retargeting in generic revision.
grep -q 'revisePendingTaskActionProposal' backend/src/agency-operator/services/taskCommands.service.js || fail "REVISION_SERVICE_MISSING"
grep -q 'getActionRevisionFields' backend/src/agency-operator/services/taskCommands.service.js || fail "REVISION_FIELD_POLICY_MISSING"
grep -q 'revise_task_action_proposal' backend/src/agency-operator/tools/createRamzyTools.js || fail "REVISION_TOOL_MISSING"
grep -q 'router.post("/approvals/:approvalId/revise"' backend/src/routes/agent.routes.js || fail "REVISION_ROUTE_MISSING"
grep -q 'reviseApproval:' frontend/src/lib/api.js || fail "REVISION_FRONTEND_API_MISSING"
grep -q 'RevisionEditor' frontend/src/components/RamzyAssistant.jsx || fail "REVISION_UI_MISSING"
grep -q 'ramzy-confirmation-risk' frontend/src/components/RamzyAssistant.jsx || fail "RISK_UI_MISSING"

# Direct action must be opt-in and run status must not get stuck on already executed approvals.
grep -q 'executeLowRiskTaskActionApproval' backend/src/agency-operator/tools/createRamzyTools.js || fail "LOW_RISK_DIRECT_TOOL_BRIDGE_MISSING"
grep -q 'String(output?.status || "").toUpperCase() === "PENDING"' backend/src/agency-operator/tools/createRamzyTools.js || fail "TOOL_WAITING_STATUS_GUARD_MISSING"
grep -q 'hasWaitingApproval' backend/src/agency-operator/services/ramzyRuntime.service.js || fail "RUNTIME_WAITING_STATUS_GUARD_MISSING"
grep -q 'revise_task_action_proposal' backend/src/agency-operator/services/ramzyRuntime.service.js || fail "REVISION_FALLBACK_SIDE_EFFECT_GUARD_MISSING"

# Prompt and previous phase protections remain explicit.
grep -q 'Phase 13:' backend/src/agency-operator/prompts/ramzyPrompt.js || fail "PHASE13_PROMPT_RULE_MISSING"
grep -q 'Risk Policy:' backend/src/agency-operator/prompts/ramzyPrompt.js || fail "PHASE13_RISK_PROMPT_MISSING"
grep -q 'الصوت لا يمنح أي صلاحية إضافية' backend/src/agency-operator/prompts/ramzyPrompt.js || fail "VOICE_NO_PERMISSION_RULE_MISSING"
grep -q 'assertRamzyToolInvocationScope' backend/src/agency-operator/tools/createRamzyTools.js || fail "PHASE8_TOOL_SCOPE_GUARD_MISSING"
grep -q 'TASK_CREATE_GROUNDED_AND_AUTHORIZED' backend/src/agency-operator/services/actionGroundingValidation.service.js || fail "PHASE12_CREATE_GROUNDING_MISSING"
grep -q 'RAMZY_VOICE_IO_V1' backend/src/agency-operator/services/ramzyVoice.service.js || fail "PHASE11_VOICE_SERVICE_MISSING"
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
    fail "EXPECTED_PHASE13_FILE_NOT_CHANGED:$file"
  fi
done
echo "EXPECTED_CHANGED_FILES=PASS"
echo "UNRELATED_WORK_PRESERVED=YES"

if git diff --name-only -- backend/prisma backend/package.json frontend/package.json | grep -q .; then
  fail "FORBIDDEN_SCHEMA_MIGRATION_OR_PACKAGE_CHANGE"
fi
echo "NO_SCHEMA_MIGRATION_PACKAGE_CHANGE=YES"

# Frontend deploy.
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

AGENT_AUTH="$(public_code GET /api/agent/status)"
VOICE_AUTH="$(public_code GET /api/agent/voice/status)"
REVISE_AUTH="$(public_code POST /api/agent/approvals/fake/revise '{"revision":{"body":"test"}}')"
echo "AGENT_STATUS_UNAUTH_HTTP=$AGENT_AUTH"
echo "VOICE_STATUS_UNAUTH_HTTP=$VOICE_AUTH"
echo "APPROVAL_REVISE_UNAUTH_HTTP=$REVISE_AUTH"
[[ "$AGENT_AUTH" == "401" ]] || fail "AGENT_AUTH_BOUNDARY_FAILED:$AGENT_AUTH"
[[ "$VOICE_AUTH" == "401" ]] || fail "VOICE_AUTH_BOUNDARY_FAILED:$VOICE_AUTH"
[[ "$REVISE_AUTH" == "401" || "$REVISE_AUTH" == "403" ]] || fail "REVISION_AUTH_CSRF_BOUNDARY_FAILED:$REVISE_AUTH"
echo "AUTH_BOUNDARY_E2E=PASS"

if ! diff -qr /var/www/TOS/frontend/dist /opt/apps/tamiyouz-front/build >/dev/null; then
  fail "DEPLOYED_DIST_MISMATCH"
fi
echo "DEPLOYED_DIST_MATCH=PASS"

if [[ "${RAMZY_LOW_RISK_DIRECT_ACTIONS:-}" =~ ^(1|true|TRUE|yes|YES|on|ON)$ ]]; then
  echo "LOW_RISK_DIRECT_SERVER_OPT_IN=ENABLED"
else
  echo "LOW_RISK_DIRECT_SERVER_OPT_IN=DISABLED_SAFE_DEFAULT"
fi

echo "NO_COMMIT_OR_PUSH=YES"
echo "PHASE13_SAFE_CONFIRMATION_ACTION_CONTROL=PASS"
echo "--- git status --short ---"
git status --short
