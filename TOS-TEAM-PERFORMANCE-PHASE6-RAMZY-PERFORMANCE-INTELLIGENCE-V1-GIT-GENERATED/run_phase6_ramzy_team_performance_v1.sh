#!/usr/bin/env bash
set -euo pipefail

TOS=/var/www/TOS
PATCH_DIR=/var/www/TOS-Patchs/TOS-TEAM-PERFORMANCE-PHASE6-RAMZY-PERFORMANCE-INTELLIGENCE-V1-GIT-GENERATED
EXPECTED_HEAD=7e8ec8c7856ce41724f493886ebe050381ecc4d8

cd "$TOS"
HEAD_NOW="$(git rev-parse HEAD)"
if [ "$HEAD_NOW" != "$EXPECTED_HEAD" ]; then
  echo "PHASE6_RAMZY_PERFORMANCE_ERROR=HEAD_MISMATCH"
  echo "EXPECTED=$EXPECTED_HEAD"
  echo "ACTUAL=$HEAD_NOW"
  exit 1
fi

if [ -n "$(git status --short)" ]; then
  echo "PHASE6_RAMZY_PERFORMANCE_ERROR=WORKTREE_NOT_CLEAN"
  git status --short
  exit 1
fi

python3 "$PATCH_DIR/01_phase6_ramzy_team_performance.py"
python3 "$PATCH_DIR/02_phase6_ramzy_team_performance_fix.py"

node --check backend/src/routes/tasks.routes.js
node --check backend/src/agency-operator/services/ramzyTeamPerformance.service.js
node --check backend/src/agency-operator/tools/createRamzyTools.js
node --check backend/src/agency-operator/agents/ramzyAgencyOperator.js
node --check backend/src/agency-operator/agents/specialistAgents.js
node --check backend/src/agency-operator/prompts/ramzyPrompt.js

node --input-type=module - <<'NODE'
import { getRamzyTeamPerformance } from './backend/src/agency-operator/services/ramzyTeamPerformance.service.js';
const result = await getRamzyTeamPerformance({ user: { id: 'phase6-static-smoke' }, mode: 'METHODOLOGY' });
if (result?.methodology?.weights?.completion !== 35) throw new Error('completion weight mismatch');
if (result?.methodology?.weights?.onTimeOverdue !== 25) throw new Error('on-time weight mismatch');
if (result?.methodology?.weights?.timeEfficiency !== 20) throw new Error('efficiency weight mismatch');
if (result?.methodology?.weights?.workflowQuality !== 10) throw new Error('workflow weight mismatch');
if (result?.methodology?.weights?.consistency !== 10) throw new Error('consistency weight mismatch');
if (result?.readOnly !== true) throw new Error('read-only contract missing');
console.log('RAMZY_TEAM_PERFORMANCE_METHODOLOGY_SMOKE=PASS');
NODE

grep -q 'id: "get_team_performance"' backend/src/agency-operator/tools/createRamzyTools.js
grep -q 'getTeamPerformanceTool: tools.getTeamPerformanceTool' backend/src/agency-operator/agents/ramzyAgencyOperator.js
grep -q 'export async function buildTeamPerformanceExportDataset' backend/src/routes/tasks.routes.js
grep -q 'export async function buildWorkforceForecast' backend/src/routes/tasks.routes.js
grep -q 'Employee Not Visible' backend/src/agency-operator/prompts/ramzyPrompt.js
grep -q 'ACTIVE-only' backend/src/agency-operator/prompts/ramzyPrompt.js

git diff --check

STATUS="$(git status --short)"
EXPECTED_STATUS=$(cat <<'EOF'
 M backend/src/agency-operator/agents/ramzyAgencyOperator.js
 M backend/src/agency-operator/agents/specialistAgents.js
 M backend/src/agency-operator/prompts/ramzyPrompt.js
 M backend/src/agency-operator/tools/createRamzyTools.js
 M backend/src/routes/tasks.routes.js
?? backend/src/agency-operator/services/ramzyTeamPerformance.service.js
EOF
)

if [ "$STATUS" != "$EXPECTED_STATUS" ]; then
  echo "PHASE6_RAMZY_PERFORMANCE_ERROR=UNEXPECTED_GIT_STATUS"
  printf '%s\n' "$STATUS"
  exit 1
fi

echo "TEAM_PERFORMANCE_PHASE6_RAMZY_V1_APPLIED=YES"
echo "RAMZY_TEAM_PERFORMANCE_TOOL=YES"
echo "RAMZY_SERVER_SIDE_DATASET_REUSED=YES"
echo "RAMZY_WORKFORCE_FORECAST_REUSED=YES"
echo "RAMZY_RBAC_REUSES_TEAM_PERFORMANCE_SCOPE=YES"
echo "RAMZY_METHOD_SCORE_WEIGHTS=35_25_20_10_10"
echo "NEW_SCORE_CREATED=NO"
echo "NEW_API_ENDPOINT=NO"
echo "SCHEMA_CHANGED=NO"
echo "MIGRATION_CREATED=NO"
echo "FRONTEND_CHANGED=NO"
echo "NODE_CHECK=PASS"
echo "RAMZY_METHODOLOGY_SMOKE=PASS"
echo "GIT_DIFF_CHECK=PASS"
echo "NO_COMMIT_OR_PUSH_PERFORMED=YES"
