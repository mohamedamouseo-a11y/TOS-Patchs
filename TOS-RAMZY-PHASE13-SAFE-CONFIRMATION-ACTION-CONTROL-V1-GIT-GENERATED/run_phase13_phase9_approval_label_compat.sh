#!/usr/bin/env bash
set -euo pipefail

TOS_ROOT="/var/www/TOS"
PATCH_DIR="$(cd "$(dirname "$0")" && pwd)"
BASELINE="f8d892f2b596cf4f09863cfac7545aa279a7a6e7"
FIXER="$PATCH_DIR/03_phase13_phase9_approval_label_compat.py"
DOMAIN="https://tos.tamiyouz.com"
COMPAT_TEST="backend/src/agency-operator/tests/ramzyFinalPolishE2E.static.test.js"

fail() {
  echo "PHASE13_SAFE_CONFIRMATION_ACTION_CONTROL=FAIL"
  echo "REASON=$1"
  exit 1
}

without_compat_status() {
  printf '%s\n' "$1" | while IFS= read -r line; do
    [[ -z "$line" ]] && continue
    path="${line:3}"
    [[ "$path" == "$COMPAT_TEST" ]] && continue
    printf '%s\n' "$line"
  done | sort
}

public_code() {
  local method="$1" path="$2" body="${3:-}"
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

echo "RUNNING=RAMZY_PHASE13_PHASE9_APPROVAL_LABEL_COMPAT"
cd "$TOS_ROOT"
CURRENT_HEAD="$(git rev-parse HEAD)"
echo "CURRENT_TOS_HEAD=$CURRENT_HEAD"
git merge-base --is-ancestor "$BASELINE" "$CURRENT_HEAD" || fail "PHASE13_BASELINE_NOT_ANCESTOR"

# Require the known Phase 13 applied state from the previous run.
grep -q 'RAMZY_ACTION_CONFIRMATION_V1' backend/src/agency-operator/services/actionConfirmation.service.js || fail "PHASE13_CONFIRMATION_SERVICE_MISSING"
grep -q 'revisePendingTaskActionProposal' backend/src/agency-operator/services/taskCommands.service.js || fail "PHASE13_REVISION_SERVICE_MISSING"
grep -q 'executeLowRiskTaskActionApproval' backend/src/agency-operator/tools/createRamzyTools.js || fail "PHASE13_LOW_RISK_BRIDGE_MISSING"
grep -q 'hasWaitingApproval' backend/src/agency-operator/services/ramzyRuntime.service.js || fail "PHASE13_RUNTIME_STATUS_GUARD_MISSING"
grep -q 'router.post("/approvals/:approvalId/revise"' backend/src/routes/agent.routes.js || fail "PHASE13_REVISION_ROUTE_MISSING"
grep -q 'Phase 13:' backend/src/agency-operator/prompts/ramzyPrompt.js || fail "PHASE13_PROMPT_MISSING"
grep -q 'RevisionEditor' frontend/src/components/RamzyAssistant.jsx || fail "PHASE13_REVISION_UI_MISSING"
grep -q 'ramzy-confirmation-risk' frontend/src/components/RamzyAssistant.jsx || fail "PHASE13_RISK_UI_MISSING"
grep -q 'reviseApproval:' frontend/src/lib/api.js || fail "PHASE13_FRONTEND_API_MISSING"
echo "PRE_STATE=KNOWN_PHASE13_APPLIED_PHASE9_COMPAT_FAIL"

PRE_STATUS="$(git status --short)"
[[ -f "$FIXER" ]] || fail "COMPAT_FIXER_NOT_FOUND"
python3 "$FIXER"
echo "PATCH_APPLY=PASS"

grep -Fq 'assert.match(assistant, /Approve|Confirm & execute/);' "$COMPAT_TEST" || fail "PHASE9_APPROVAL_LABEL_COMPAT_MISSING"
# Preserve both the old Phase 9 English concept and the new Phase 13 wording.
grep -Fq 'Confirm & execute' frontend/src/components/RamzyAssistant.jsx || fail "PHASE13_CONFIRM_EXECUTE_LABEL_MISSING"
grep -Fq 'Reject' frontend/src/components/RamzyAssistant.jsx || fail "PHASE9_REJECT_LABEL_MISSING"
grep -Fq 'Evidence & access' frontend/src/components/RamzyAssistant.jsx || fail "PHASE9_EVIDENCE_LABEL_MISSING"
grep -q 'الصوت لا يمنح أي صلاحية إضافية' backend/src/agency-operator/prompts/ramzyPrompt.js || fail "VOICE_NO_PERMISSION_RULE_MISSING"
grep -q 'assertRamzyToolInvocationScope' backend/src/agency-operator/tools/createRamzyTools.js || fail "PHASE8_SCOPE_GUARD_MISSING"
echo "CONTRACT_CHECKS=PASS"

npm --prefix backend run test:ramzy
echo "BACKEND_TESTS=PASS"

npm --prefix frontend run build
echo "FRONTEND_BUILD=PASS"

git diff --check -- \
  backend/src/agency-operator/services/actionConfirmation.service.js \
  backend/src/agency-operator/services/taskCommands.service.js \
  backend/src/agency-operator/tools/createRamzyTools.js \
  backend/src/agency-operator/services/ramzyRuntime.service.js \
  backend/src/routes/agent.routes.js \
  backend/src/agency-operator/prompts/ramzyPrompt.js \
  backend/src/agency-operator/tests/ramzyActionConfirmationPhase13.static.test.js \
  "$COMPAT_TEST" \
  frontend/src/lib/api.js \
  frontend/src/components/RamzyAssistant.jsx \
  frontend/src/components/ramzyActionControlPhase13.css
echo "GIT_DIFF_CHECK=PASS"

POST_STATUS="$(git status --short)"
if [[ "$(without_compat_status "$PRE_STATUS")" != "$(without_compat_status "$POST_STATUS")" ]]; then
  fail "UNRELATED_WORKTREE_CHANGED"
fi
echo "UNRELATED_WORK_PRESERVED=YES"

if git diff --name-only -- backend/prisma backend/package.json frontend/package.json | grep -q .; then
  fail "FORBIDDEN_SCHEMA_MIGRATION_OR_PACKAGE_CHANGE"
fi
echo "NO_SCHEMA_MIGRATION_PACKAGE_CHANGE=YES"

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

for url in /health /dashboard /team-performance /tasks; do
  code="000"
  for _ in 1 2 3 4 5; do
    code="$(curl -ksS -o /dev/null -w '%{http_code}' "$DOMAIN$url" || true)"
    [[ "$code" == "200" ]] && break
    sleep 2
  done
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

echo "NO_COMMIT_OR_PUSH=YES"
echo "PHASE13_SAFE_CONFIRMATION_ACTION_CONTROL=PASS"
echo "--- git status --short ---"
git status --short
