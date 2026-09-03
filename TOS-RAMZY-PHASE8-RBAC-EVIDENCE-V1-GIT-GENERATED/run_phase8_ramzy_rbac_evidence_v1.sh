#!/usr/bin/env bash
set -euo pipefail

TOS=/var/www/TOS
PATCH_DIR=/var/www/TOS-Patchs/TOS-RAMZY-PHASE8-RBAC-EVIDENCE-V1-GIT-GENERATED
EXPECTED_HEAD=db3d6a21184bb670d5252771c3ef3a5059ecca52

normalize() {
  printf '%s\n' "$1" | sed '/^[[:space:]]*$/d' | sort
}

status_files() {
  git status --short | sed 's/^...//' | sort
}

cd "$TOS"
HEAD_NOW="$(git rev-parse HEAD)"
if [[ "$HEAD_NOW" != "$EXPECTED_HEAD" ]]; then
  echo "PHASE8_ERROR=HEAD_MISMATCH"
  echo "EXPECTED_HEAD=$EXPECTED_HEAD"
  echo "ACTUAL_HEAD=$HEAD_NOW"
  exit 1
fi

PRE_STATUS="$(git status --short)"
if [[ -n "$PRE_STATUS" ]]; then
  echo "PHASE8_ERROR=WORKTREE_NOT_CLEAN"
  printf '%s\n' "$PRE_STATUS"
  exit 1
fi

python3 "$PATCH_DIR/01_phase8_ramzy_rbac_evidence.py"

grep -q 'assertRamzyToolInvocationScope' backend/src/agency-operator/policies/agentPolicy.service.js
grep -q 'await assertRamzyToolInvocationScope' backend/src/agency-operator/tools/createRamzyTools.js
grep -q 'ramzyVisibleUserWhere' backend/src/agency-operator/services/ramzySystemIntelligence.service.js
grep -q 'RAMZY_EVIDENCE_V1' backend/src/agency-operator/services/ramzyEvidence.service.js
grep -q 'safeBuildEvidence' backend/src/agency-operator/services/ramzyRuntime.service.js
grep -q 'الأدلة ونطاق الصلاحية' frontend/src/components/RamzyAssistant.jsx

EXPECTED_FILES=$(cat <<'EOF'
backend/src/agency-operator/policies/agentPolicy.service.js
backend/src/agency-operator/prompts/ramzyPrompt.js
backend/src/agency-operator/services/ramzyEvidence.service.js
backend/src/agency-operator/services/ramzyRuntime.service.js
backend/src/agency-operator/services/ramzySystemIntelligence.service.js
backend/src/agency-operator/tests/ramzyRbacEvidence.static.test.js
backend/src/agency-operator/tools/createRamzyTools.js
frontend/src/components/RamzyAssistant.jsx
EOF
)

ACTUAL_FILES="$(status_files)"
if [[ "$(normalize "$ACTUAL_FILES")" != "$(normalize "$EXPECTED_FILES")" ]]; then
  echo "PHASE8_ERROR=UNEXPECTED_CHANGED_FILES"
  printf '%s\n' "$ACTUAL_FILES"
  exit 1
fi

git diff --check

node --check backend/src/agency-operator/policies/agentPolicy.service.js
node --check backend/src/agency-operator/prompts/ramzyPrompt.js
node --check backend/src/agency-operator/services/ramzyEvidence.service.js
node --check backend/src/agency-operator/services/ramzyRuntime.service.js
node --check backend/src/agency-operator/services/ramzySystemIntelligence.service.js
node --check backend/src/agency-operator/tests/ramzyRbacEvidence.static.test.js
node --check backend/src/agency-operator/tools/createRamzyTools.js

node -e "import('./backend/src/agency-operator/services/ramzyEvidence.service.js').then(()=>console.log('PHASE8_EVIDENCE_IMPORT=PASS'))"
npm --prefix backend run test:ramzy
npm --prefix frontend run build

rm -rf /opt/apps/tamiyouz-front/build/*
cp -a /var/www/TOS/frontend/dist/. /opt/apps/tamiyouz-front/build/
pm2 reload tamiyouz-frontend

if ! pm2 describe tamiyouz-backend >/dev/null 2>&1; then
  echo "PHASE8_ERROR=BACKEND_PM2_NOT_FOUND"
  exit 1
fi
pm2 reload tamiyouz-backend
sleep 2

HEALTH_HTTP="$(curl -ks -o /dev/null -w '%{http_code}' https://tos.tamiyouz.com/health || true)"
DASHBOARD_HTTP="$(curl -ks -o /dev/null -w '%{http_code}' https://tos.tamiyouz.com/dashboard || true)"
TEAM_PERFORMANCE_HTTP="$(curl -ks -o /dev/null -w '%{http_code}' https://tos.tamiyouz.com/team-performance || true)"
TASKS_HTTP="$(curl -ks -o /dev/null -w '%{http_code}' https://tos.tamiyouz.com/tasks || true)"

if [[ "$HEALTH_HTTP" != "200" || "$DASHBOARD_HTTP" != "200" || "$TEAM_PERFORMANCE_HTTP" != "200" || "$TASKS_HTTP" != "200" ]]; then
  echo "PHASE8_ERROR=SMOKE_FAILED"
  echo "HEALTH_HTTP=$HEALTH_HTTP"
  echo "DASHBOARD_HTTP=$DASHBOARD_HTTP"
  echo "TEAM_PERFORMANCE_HTTP=$TEAM_PERFORMANCE_HTTP"
  echo "TASKS_HTTP=$TASKS_HTTP"
  exit 1
fi

if ! diff -qr /var/www/TOS/frontend/dist /opt/apps/tamiyouz-front/build >/dev/null; then
  echo "PHASE8_ERROR=FRONTEND_DEPLOY_MISMATCH"
  exit 1
fi

EXPECTED_STATUS=$(cat <<'EOF'
 M backend/src/agency-operator/policies/agentPolicy.service.js
 M backend/src/agency-operator/prompts/ramzyPrompt.js
 M backend/src/agency-operator/services/ramzyRuntime.service.js
 M backend/src/agency-operator/services/ramzySystemIntelligence.service.js
 M backend/src/agency-operator/tools/createRamzyTools.js
 M frontend/src/components/RamzyAssistant.jsx
?? backend/src/agency-operator/services/ramzyEvidence.service.js
?? backend/src/agency-operator/tests/ramzyRbacEvidence.static.test.js
EOF
)
POST_STATUS="$(git status --short)"
if [[ "$(normalize "$POST_STATUS")" != "$(normalize "$EXPECTED_STATUS")" ]]; then
  echo "PHASE8_ERROR=UNEXPECTED_POST_STATUS"
  printf '%s\n' "$POST_STATUS"
  exit 1
fi

echo "PHASE_8_PATCH_APPLY=PASS"
echo "BASELINE_HEAD=$HEAD_NOW"
echo "TOOL_SCOPE_PREFLIGHT=PASS"
echo "USER_LOOKUP_RBAC=PASS"
echo "EXPLICIT_PROJECT_SCOPE=PASS"
echo "EVIDENCE_MANIFEST=PASS"
echo "USER_VISIBLE_EVIDENCE=PASS"
echo "INTERNAL_APPROVAL_TASK_ID_HIDDEN=PASS"
echo "RAMZY_TESTS=PASS"
echo "FRONTEND_BUILD=PASS"
echo "FRONTEND_DEPLOY=PASS"
echo "BACKEND_RELOAD=PASS"
echo "HEALTH_HTTP=$HEALTH_HTTP"
echo "DASHBOARD_HTTP=$DASHBOARD_HTTP"
echo "TEAM_PERFORMANCE_HTTP=$TEAM_PERFORMANCE_HTTP"
echo "TASKS_HTTP=$TASKS_HTTP"
echo "GIT_DIFF_CHECK=PASS"
echo "NO_COMMIT_OR_PUSH=YES"
echo "FILES_CHANGED:"
git status --short
