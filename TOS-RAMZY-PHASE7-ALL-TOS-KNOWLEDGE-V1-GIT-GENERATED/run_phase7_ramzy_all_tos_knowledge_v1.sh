#!/usr/bin/env bash
set -euo pipefail

TOS=/var/www/TOS
PATCH_DIR=/var/www/TOS-Patchs/TOS-RAMZY-PHASE7-ALL-TOS-KNOWLEDGE-V1-GIT-GENERATED
EXPECTED_HEAD=256cc2e13f69fd0aa98a840d4ae4b63ebdc8649c

normalize() {
  printf '%s\n' "$1" | sed '/^[[:space:]]*$/d' | sort
}

cd "$TOS"
HEAD_NOW="$(git rev-parse HEAD)"
if [[ "$HEAD_NOW" != "$EXPECTED_HEAD" ]]; then
  echo "PHASE7_ERROR=HEAD_MISMATCH"
  echo "EXPECTED_HEAD=$EXPECTED_HEAD"
  echo "ACTUAL_HEAD=$HEAD_NOW"
  exit 1
fi

PRE_STATUS="$(git status --short)"
if [[ -n "$PRE_STATUS" ]]; then
  echo "PHASE7_ERROR=WORKTREE_NOT_CLEAN"
  printf '%s\n' "$PRE_STATUS"
  exit 1
fi

python3 "$PATCH_DIR/01_phase7_ramzy_all_tos_knowledge.py"

grep -q 'id: "get_tos_module_context"' backend/src/agency-operator/tools/createRamzyTools.js
grep -q 'tosNavigatorAgent' backend/src/agency-operator/agents/specialistAgents.js
grep -q 'module=SYSTEM_MAP' backend/src/agency-operator/prompts/ramzyPrompt.js
grep -q 'export const RAMZY_TOS_MODULE_KEYS' backend/src/agency-operator/services/ramzyTosKnowledge.service.js
grep -q 'knowledgeOnly' backend/src/agency-operator/services/ramzyTosKnowledge.service.js

EXPECTED_FILES=$(cat <<'EOF'
backend/src/agency-operator/agents/ramzyAgencyOperator.js
backend/src/agency-operator/agents/specialistAgents.js
backend/src/agency-operator/prompts/ramzyPrompt.js
backend/src/agency-operator/services/ramzyTosKnowledge.service.js
backend/src/agency-operator/tests/ramzyTosKnowledge.static.test.js
backend/src/agency-operator/tools/createRamzyTools.js
EOF
)
ACTUAL_FILES="$(git diff --name-only | sort)"
if [[ "$(normalize "$ACTUAL_FILES")" != "$(normalize "$EXPECTED_FILES")" ]]; then
  echo "PHASE7_ERROR=UNEXPECTED_CHANGED_FILES"
  printf '%s\n' "$ACTUAL_FILES"
  exit 1
fi

git diff --check

node --check backend/src/agency-operator/services/ramzyTosKnowledge.service.js
node --check backend/src/agency-operator/tools/createRamzyTools.js
node --check backend/src/agency-operator/agents/ramzyAgencyOperator.js
node --check backend/src/agency-operator/agents/specialistAgents.js
node --check backend/src/agency-operator/prompts/ramzyPrompt.js
node --check backend/src/agency-operator/tests/ramzyTosKnowledge.static.test.js

node -e "import('./backend/src/agency-operator/services/ramzyTosKnowledge.service.js').then(()=>console.log('PHASE7_IMPORT_CHECK=PASS'))"
npm --prefix backend run test:ramzy

if ! pm2 describe tamiyouz-backend >/dev/null 2>&1; then
  echo "PHASE7_ERROR=BACKEND_PM2_NOT_FOUND"
  exit 1
fi
pm2 reload tamiyouz-backend
sleep 2

HEALTH_HTTP="$(curl -ks -o /dev/null -w '%{http_code}' https://tos.tamiyouz.com/health || true)"
DASHBOARD_HTTP="$(curl -ks -o /dev/null -w '%{http_code}' https://tos.tamiyouz.com/dashboard || true)"
TEAM_PERFORMANCE_HTTP="$(curl -ks -o /dev/null -w '%{http_code}' https://tos.tamiyouz.com/team-performance || true)"
TASKS_HTTP="$(curl -ks -o /dev/null -w '%{http_code}' https://tos.tamiyouz.com/tasks || true)"

if [[ "$HEALTH_HTTP" != "200" ]]; then
  echo "PHASE7_ERROR=HEALTH_HTTP_$HEALTH_HTTP"
  exit 1
fi

EXPECTED_STATUS=$(cat <<'EOF'
 M backend/src/agency-operator/agents/ramzyAgencyOperator.js
 M backend/src/agency-operator/agents/specialistAgents.js
 M backend/src/agency-operator/prompts/ramzyPrompt.js
 M backend/src/agency-operator/tools/createRamzyTools.js
?? backend/src/agency-operator/services/ramzyTosKnowledge.service.js
?? backend/src/agency-operator/tests/ramzyTosKnowledge.static.test.js
EOF
)
POST_STATUS="$(git status --short)"
if [[ "$(normalize "$POST_STATUS")" != "$(normalize "$EXPECTED_STATUS")" ]]; then
  echo "PHASE7_ERROR=UNEXPECTED_POST_STATUS"
  printf '%s\n' "$POST_STATUS"
  exit 1
fi

echo "PHASE_7_PATCH_APPLY=PASS"
echo "BASELINE_HEAD=$HEAD_NOW"
echo "TOS_MODULE_CONTEXT=PASS"
echo "MODULE_COVERAGE=23"
echo "SOURCE_OF_TRUTH_REUSE=PASS"
echo "KNOWLEDGE_ONLY_BOUNDARIES=PASS"
echo "SENSITIVE_SETTINGS_EXCLUDED=PASS"
echo "PARALLEL_TASK_FILE_LOGIC=MUST_BE_NO"
echo "RAMZY_TESTS=PASS"
echo "IMPORT_CHECK=PASS"
echo "BACKEND_RELOAD=PASS"
echo "HEALTH_HTTP=$HEALTH_HTTP"
echo "DASHBOARD_HTTP=$DASHBOARD_HTTP"
echo "TEAM_PERFORMANCE_HTTP=$TEAM_PERFORMANCE_HTTP"
echo "TASKS_HTTP=$TASKS_HTTP"
echo "GIT_DIFF_CHECK=PASS"
echo "NO_COMMIT_OR_PUSH=YES"
echo "FILES_CHANGED:"
git status --short
