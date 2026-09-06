#!/usr/bin/env bash
set -euo pipefail

TOS_ROOT="/var/www/TOS"
BASELINE="f22b0d94271477e2a58aa6d53e560b099c64356c"
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
  echo "PHASE12_CREATE_ASSIGNEE_VALIDATION_REPAIR=FAIL"
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

echo "RUNNING=RAMZY_PHASE12_CREATE_ASSIGNEE_VALIDATION_REPAIR"
cd "$TOS_ROOT"
CURRENT_HEAD="$(git rev-parse HEAD)"
echo "CURRENT_TOS_HEAD=$CURRENT_HEAD"
git merge-base --is-ancestor "$BASELINE" "$CURRENT_HEAD" || fail "PHASE12_BASELINE_NOT_ANCESTOR"

PRE_STATUS="$(git status --short)"

# Accept only the known Phase 12 applied state. The previous runner already applied
# the parser fix before its brittle source-text grep failed.
grep -q '"CREATE_TASK"' backend/src/agency-operator/services/semanticIntentResolver.service.js || fail "KNOWN_PHASE12_SEMANTIC_MARKER_MISSING"
grep -q 'assertAgentTaskCreateAccess' backend/src/agency-operator/policies/agentAccess.service.js || fail "KNOWN_PHASE12_ACCESS_MARKER_MISSING"
grep -q 'TASK_CREATE_GROUNDED_AND_AUTHORIZED' backend/src/agency-operator/services/actionGroundingValidation.service.js || fail "KNOWN_PHASE12_GROUNDING_MARKER_MISSING"
grep -q 'detectedIntent === "TASK_CREATE"' backend/src/agency-operator/services/ramzySystemIntelligence.service.js || fail "KNOWN_PHASE12_INTELLIGENCE_MARKER_MISSING"
grep -q 'actionType === "CREATE_TASK"' backend/src/agency-operator/services/taskCommands.service.js || fail "KNOWN_PHASE12_COMMAND_MARKER_MISSING"
grep -q '"CREATE_TASK"' backend/src/agency-operator/tools/createRamzyTools.js || fail "KNOWN_PHASE12_TOOL_MARKER_MISSING"
grep -q 'isCreateTaskApproval' backend/src/routes/agent.routes.js || fail "KNOWN_PHASE12_ROUTE_MARKER_MISSING"
grep -q 'Phase 12:' backend/src/agency-operator/prompts/ramzyPrompt.js || fail "KNOWN_PHASE12_PROMPT_MARKER_MISSING"
grep -q 'CREATE_TASK: { ar: "إنشاء مهمة", en: "Create task" }' frontend/src/components/RamzyAssistant.jsx || fail "KNOWN_PHASE12_FRONTEND_MARKER_MISSING"
[[ -f backend/src/agency-operator/tests/ramzyVoiceTaskActionsPhase12.static.test.js ]] || fail "KNOWN_PHASE12_TEST_MISSING"
grep -Fq 'اعمل تاسك مراجعة البنر ليوسف في مشروع Cuir' backend/src/agency-operator/tests/ramzyVoiceTaskActionsPhase12.static.test.js || fail "PARSER_FIX_TEST_MARKER_MISSING"

echo "PRE_STATE=KNOWN_PHASE12_PARSER_FIX_APPLIED"

# Behavioral validation. Do not grep escaped JavaScript regex source text.
node --input-type=module <<'NODE'
import { resolveSemanticIntent } from './backend/src/agency-operator/services/semanticIntentResolver.service.js';

const cases = [
  ['اعمل تاسك ليوسف', 'يوسف'],
  ['اعمل تاسك لـيوسف', 'يوسف'],
  ['اعمل تاسك ل يوسف', 'يوسف'],
  ['اعمل تاسك مراجعة البنر ليوسف في مشروع Cuir', 'يوسف'],
  ['create a task review banner for Youssef project Cuir', 'Youssef'],
];
for (const [message, expected] of cases) {
  const intent = resolveSemanticIntent({ message });
  const actual = String(intent?.slots?.assigneeQuery || '');
  if (intent?.intent !== 'TASK_CREATE' || intent?.operation !== 'CREATE_TASK' || actual !== expected) {
    console.error('PHASE12_BEHAVIOR_CASE_FAIL', JSON.stringify({ message, expected, actual, intent: intent?.intent, operation: intent?.operation }));
    process.exit(1);
  }
}
console.log('CREATE_ASSIGNEE_BEHAVIOR=PASS');
NODE

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

if git diff --name-only -- backend/prisma frontend/package.json backend/package.json | grep -q .; then
  fail "FORBIDDEN_SCHEMA_OR_PACKAGE_CHANGE"
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

echo "NO_SOURCE_CHANGE_THIS_RUN=YES"
echo "NO_COMMIT_OR_PUSH=YES"
echo "PHASE12_CREATE_ASSIGNEE_VALIDATION_REPAIR=PASS"
echo "PHASE12_VOICE_TASK_ACTIONS=PASS"
echo "--- git status --short ---"
git status --short
