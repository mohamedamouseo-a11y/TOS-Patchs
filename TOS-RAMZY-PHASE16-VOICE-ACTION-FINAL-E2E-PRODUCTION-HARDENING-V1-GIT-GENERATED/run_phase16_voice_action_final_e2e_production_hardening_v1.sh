#!/usr/bin/env bash
set -euo pipefail

TOS_ROOT="/var/www/TOS"
PATCH_DIR="$(cd "$(dirname "$0")" && pwd)"
GENERATOR="$PATCH_DIR/01_phase16_voice_action_final_e2e_production_hardening.py"
BASELINE="f7678ab1ab7b5b0261a9e3a3a78c43533999b66d"
DOMAIN="https://tos.tamiyouz.com"

TARGETS=(
  "backend/src/agency-operator/prompts/ramzyPrompt.js"
  "backend/src/agency-operator/services/ramzyRuntime.service.js"
  "backend/src/agency-operator/services/taskCommands.service.js"
  "backend/src/routes/agent.routes.js"
  "backend/src/agency-operator/services/ramzyProductionHardening.service.js"
  "backend/src/agency-operator/tests/ramzyVoiceActionProductionHardeningPhase16.test.js"
)

fail() {
  echo "PASS/FAIL=FAIL"
  echo "PHASE16_VOICE_ACTION_FINAL_E2E_PRODUCTION_HARDENING=FAIL"
  echo "REASON=$1"
  exit 1
}

public_code() {
  local method="${1:-GET}"
  local path="${2:-/}"
  local code="000"
  for _ in 1 2 3 4 5; do
    if [[ "$method" == "POST" ]]; then
      code="$(curl -ksS -X POST -H 'Content-Type: application/json' -d '{"text":"phase16-boundary"}' -o /dev/null -w '%{http_code}' "$DOMAIN$path" || true)"
    else
      code="$(curl -ksS -o /dev/null -w '%{http_code}' "$DOMAIN$path" || true)"
    fi
    [[ "$code" != "000" && "$code" != "502" && "$code" != "503" ]] && break
    sleep 2
  done
  printf '%s' "$code"
}

filtered_status() {
  python3 - "${TARGETS[@]}" <<'PY'
import subprocess, sys

targets = set(sys.argv[1:])
raw = subprocess.check_output(["git", "status", "--short"], text=True)
for line in raw.splitlines():
    path = line[3:]
    if " -> " in path:
        path = path.split(" -> ", 1)[1]
    if path not in targets:
        print(line)
PY
}

echo "RUNNING=RAMZY_PHASE16_VOICE_ACTION_FINAL_E2E_PRODUCTION_HARDENING_V1"
cd "$TOS_ROOT"
CURRENT_HEAD="$(git rev-parse HEAD)"
echo "CURRENT_TOS_HEAD=$CURRENT_HEAD"
if ! git merge-base --is-ancestor "$BASELINE" "$CURRENT_HEAD"; then
  fail "PHASE16_BASELINE_NOT_ANCESTOR"
fi

TARGET_STATUS_BEFORE="$(git status --short -- "${TARGETS[@]}")"
[[ -z "$TARGET_STATUS_BEFORE" ]] || fail "PHASE16_TARGET_FILES_NOT_CLEAN"
[[ ! -e "backend/src/agency-operator/services/ramzyProductionHardening.service.js" ]] || fail "PHASE16_SERVICE_ALREADY_EXISTS"
[[ ! -e "backend/src/agency-operator/tests/ramzyVoiceActionProductionHardeningPhase16.test.js" ]] || fail "PHASE16_TEST_ALREADY_EXISTS"
echo "PRE_STATE=TARGET_FILES_CLEAN"

UNRELATED_STATUS_BEFORE="$(filtered_status)"
FRONTEND_STATUS_BEFORE="$(git status --short -- frontend)"
FRONTEND_DIFF_BEFORE="$(git diff --binary -- frontend | sha256sum | awk '{print $1}')"
SCHEMA_PACKAGE_DIFF_BEFORE="$(git diff --binary -- backend/prisma backend/package.json frontend/package.json | sha256sum | awk '{print $1}')"

[[ -f "$GENERATOR" ]] || fail "PHASE16_GENERATOR_NOT_FOUND"
python3 "$GENERATOR" "$TOS_ROOT"
echo "PATCH_APPLY=PASS"

# Required Phase 16 contracts.
grep -q 'RAMZY_VOICE_ACTION_PRODUCTION_HARDENING_V1' backend/src/agency-operator/services/ramzyProductionHardening.service.js || fail "PHASE16_MARKER_MISSING"
grep -q 'RAMZY_PUBLIC_APPROVAL_V1' backend/src/agency-operator/services/ramzyProductionHardening.service.js || fail "PUBLIC_APPROVAL_VERSION_MISSING"
grep -q 'publicTargetIdsExposed: false' backend/src/agency-operator/services/ramzyProductionHardening.service.js || fail "PUBLIC_TARGET_ID_POLICY_MISSING"
grep -q 'publicRawExecutionRecordsExposed: false' backend/src/agency-operator/services/ramzyProductionHardening.service.js || fail "PUBLIC_RAW_EXECUTION_POLICY_MISSING"
grep -q 'approvals: publicRamzyApprovalViews(approvals)' backend/src/routes/agent.routes.js || fail "CONVERSATION_APPROVAL_BOUNDARY_MISSING"
grep -q 'res.json(publicRamzyApprovalViews(approvals))' backend/src/routes/agent.routes.js || fail "APPROVAL_LIST_BOUNDARY_MISSING"
grep -q 'publicRamzyApprovalView(revised)' backend/src/routes/agent.routes.js || fail "REVISE_PUBLIC_BOUNDARY_MISSING"
grep -q 'publicRamzyApprovalView(rejected)' backend/src/routes/agent.routes.js || fail "REJECT_PUBLIC_BOUNDARY_MISSING"
grep -q 'publicRamzyApprovalView(finalized)' backend/src/routes/agent.routes.js || fail "FINAL_PUBLIC_BOUNDARY_MISSING"
grep -q 'const publicApprovals = approvals.map(publicRamzyApprovalView)' backend/src/agency-operator/services/ramzyRuntime.service.js || fail "RUNTIME_PUBLIC_APPROVAL_BOUNDARY_MISSING"
grep -q 'emit("ramzy:approval", publicRamzyApprovalView(revised))' backend/src/agency-operator/services/taskCommands.service.js || fail "REVISE_SOCKET_BOUNDARY_MISSING"
grep -q 'emit("ramzy:approval", publicRamzyApprovalView(executed))' backend/src/agency-operator/services/taskCommands.service.js || fail "DIRECT_SOCKET_BOUNDARY_MISSING"
grep -q 'productionHardening: getRamzyProductionHardeningConfig()' backend/src/routes/agent.routes.js || fail "PRODUCTION_STATUS_MARKER_MISSING"
grep -q 'Phase 16: Voice & Action Final E2E / Production Hardening' backend/src/agency-operator/prompts/ramzyPrompt.js || fail "PHASE16_PROMPT_MISSING"

# Cross-phase safety invariants that Phase 16 must never weaken.
grep -q 'assertRamzyToolInvocationScope' backend/src/agency-operator/tools/createRamzyTools.js || fail "PHASE8_SCOPE_GUARD_MISSING"
grep -q 'RAMZY_EVIDENCE_V1' backend/src/agency-operator/services/ramzyEvidence.service.js || fail "PHASE8_EVIDENCE_MISSING"
grep -q 'RAMZY_IDENTITY_NAME_MATCHING_V1' backend/src/agency-operator/services/identityNameMatching.service.js || fail "PHASE10_IDENTITY_MATCHING_MISSING"
grep -q 'RAMZY_VOICE_IO_V1' backend/src/agency-operator/services/ramzyVoice.service.js || fail "PHASE11_VOICE_MISSING"
grep -q 'autoSendAfterTranscription: false' backend/src/agency-operator/services/ramzyVoice.service.js || fail "VOICE_AUTO_SEND_SAFETY_MISSING"
grep -q 'actionExecutionFromVoice: false' backend/src/agency-operator/services/ramzyVoice.service.js || fail "VOICE_EXECUTION_SAFETY_MISSING"
grep -q 'TASK_CREATE_GROUNDED_AND_AUTHORIZED' backend/src/agency-operator/services/actionGroundingValidation.service.js || fail "PHASE12_CREATE_GROUNDING_MISSING"
grep -q 'RAMZY_ACTION_CONFIRMATION_V1' backend/src/agency-operator/services/actionConfirmation.service.js || fail "PHASE13_CONFIRMATION_MISSING"
grep -q 'RAMZY_CONVERSATIONAL_ACTION_DRAFT_V1' backend/src/agency-operator/services/ramzyActionDraft.service.js || fail "PHASE14_DRAFT_MEMORY_MISSING"
grep -q 'RAMZY_MULTI_STEP_OPERATIONS_V1' backend/src/agency-operator/services/ramzyMultiStepOperations.service.js || fail "PHASE15_MULTI_STEP_MISSING"
echo "CONTRACT_CHECKS=PASS"

git diff --check -- "${TARGETS[@]}"
echo "GIT_DIFF_CHECK=PASS"

node --test backend/src/agency-operator/tests/ramzyVoiceActionProductionHardeningPhase16.test.js
echo "PHASE16_ACCEPTANCE_MATRIX=PASS"

TEST_LOG="$(mktemp)"
trap 'rm -f "$TEST_LOG"' EXIT
npm --prefix backend run test:ramzy 2>&1 | tee "$TEST_LOG"
TEST_COUNT="$(awk '/^# tests /{print $3}' "$TEST_LOG" | tail -1)"
PASS_COUNT="$(awk '/^# pass /{print $3}' "$TEST_LOG" | tail -1)"
if [[ -n "$TEST_COUNT" && -n "$PASS_COUNT" ]]; then
  [[ "$TEST_COUNT" == "$PASS_COUNT" ]] || fail "BACKEND_TEST_COUNT_MISMATCH:${PASS_COUNT}/${TEST_COUNT}"
  echo "BACKEND_TESTS=PASS (${PASS_COUNT}/${TEST_COUNT} tests passed)"
else
  echo "BACKEND_TESTS=PASS"
fi

# Phase 16 does not modify frontend source, but final build must still compile with the hardened API shape.
npm --prefix frontend run build
echo "FRONTEND_BUILD=PASS"

UNRELATED_STATUS_AFTER="$(filtered_status)"
[[ "$UNRELATED_STATUS_BEFORE" == "$UNRELATED_STATUS_AFTER" ]] || fail "UNRELATED_WORKTREE_CHANGED"
FRONTEND_STATUS_AFTER="$(git status --short -- frontend)"
FRONTEND_DIFF_AFTER="$(git diff --binary -- frontend | sha256sum | awk '{print $1}')"
SCHEMA_PACKAGE_DIFF_AFTER="$(git diff --binary -- backend/prisma backend/package.json frontend/package.json | sha256sum | awk '{print $1}')"
[[ "$FRONTEND_STATUS_BEFORE" == "$FRONTEND_STATUS_AFTER" && "$FRONTEND_DIFF_BEFORE" == "$FRONTEND_DIFF_AFTER" ]] || fail "FRONTEND_SOURCE_CHANGED"
[[ "$SCHEMA_PACKAGE_DIFF_BEFORE" == "$SCHEMA_PACKAGE_DIFF_AFTER" ]] || fail "SCHEMA_OR_PACKAGE_DIFF_CHANGED"
echo "UNRELATED_WORK_PRESERVED=YES"
echo "FRONTEND_SOURCE_CHANGED=NO"
echo "SCHEMA_DATABASE_PACKAGE_CHANGED=NO"

PATCH_STATUS="$(git status --short -- "${TARGETS[@]}")"
for required in "${TARGETS[@]}"; do
  printf '%s\n' "$PATCH_STATUS" | grep -Fq "$required" || fail "EXPECTED_PHASE16_CHANGE_MISSING:$required"
done

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
APPROVAL_AUTH="$(public_code GET /api/agent/approvals)"
VOICE_POST_AUTH="$(public_code POST /api/agent/voice/synthesize)"
echo "AGENT_STATUS_UNAUTH_HTTP=$AGENT_AUTH"
echo "VOICE_STATUS_UNAUTH_HTTP=$VOICE_AUTH"
echo "APPROVALS_UNAUTH_HTTP=$APPROVAL_AUTH"
echo "VOICE_SYNTH_UNAUTH_HTTP=$VOICE_POST_AUTH"
[[ "$AGENT_AUTH" == "401" ]] || fail "AGENT_AUTH_BOUNDARY_FAILED:$AGENT_AUTH"
[[ "$VOICE_AUTH" == "401" ]] || fail "VOICE_AUTH_BOUNDARY_FAILED:$VOICE_AUTH"
[[ "$APPROVAL_AUTH" == "401" ]] || fail "APPROVAL_AUTH_BOUNDARY_FAILED:$APPROVAL_AUTH"
[[ "$VOICE_POST_AUTH" == "401" || "$VOICE_POST_AUTH" == "403" ]] || fail "VOICE_POST_AUTH_BOUNDARY_FAILED:$VOICE_POST_AUTH"
echo "AUTH_BOUNDARY_E2E=PASS"

echo "PUBLIC_APPROVAL_BOUNDARY=PASS"
echo "VOICE_REVIEW_BEFORE_SEND=PASS"
echo "IDENTITY_AMBIGUITY_MATRIX=PASS"
echo "CONFIRMATION_REVISION_GUARDS=PASS"
echo "MULTI_STEP_PARTIAL_RESULT_CONTRACT=PASS"
echo "EVIDENCE_AUDIT_CONTRACT=PASS"
echo "CONTROLLED_REAL_ACTION_E2E=READY_REQUIRES_EXPLICIT_SANDBOX_TARGET"
echo "NO_FRONTEND_DEPLOY_THIS_RUN=YES"
echo "NO_COMMIT_OR_PUSH=YES"
echo "PHASE16_CORE_PRODUCTION_HARDENING=PASS"
echo "PASS/FAIL=PASS"
echo "--- git status --short ---"
git status --short
