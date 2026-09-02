#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-/var/www/TOS}"
BASELINE="20aa559dfcf397aa8ea31453e2ea911b26ddb2b4"
PATCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$REPO"
HEAD="$(git rev-parse HEAD)"
if [[ "$HEAD" != "$BASELINE" ]]; then
  echo "BASELINE_CHECK=FAIL expected=$BASELINE actual=$HEAD"
  exit 1
fi
echo "BASELINE_CHECK=PASS"

TARGET_STATUS="$(git status --porcelain -- \
  backend/prisma/schema.prisma \
  backend/src/routes/tasks.routes.js \
  frontend/src/lib/api.js \
  frontend/src/pages/TeamPerformanceDashboard.jsx \
  frontend/src/components/performance/TalentSuccession.jsx \
  backend/prisma/migrations/202609021410_phase10_talent_matrix_succession_planning || true)"
if [[ -n "$TARGET_STATUS" ]]; then
  echo "$TARGET_STATUS"
  echo "TARGETS_CLEAN=FAIL"
  exit 1
fi
echo "TARGETS_CLEAN=PASS"

grep -q 'model SkillDefinition {' backend/prisma/schema.prisma
grep -q 'SkillsDevelopmentPanel' frontend/src/pages/TeamPerformanceDashboard.jsx
grep -q 'Skill Coverage' frontend/src/components/performance/SkillsDevelopment.jsx
echo "PHASE9_BASELINE_PRESENT=PASS"

python3 "$PATCH_DIR/01_phase10_schema.py" "$REPO"
python3 "$PATCH_DIR/02_phase10_backend.py" "$REPO"
python3 "$PATCH_DIR/03_phase10_api.py" "$REPO"
python3 "$PATCH_DIR/04_phase10_component.py" "$REPO"
python3 "$PATCH_DIR/05_phase10_dashboard.py" "$REPO"

npm --prefix backend run prisma:validate:wasm
echo "PRISMA_VALIDATE=PASS"

npm --prefix backend run prisma:deploy
echo "PRISMA_DEPLOY=PASS"

npm --prefix backend run prisma:generate
echo "PRISMA_GENERATE=PASS"

node --check backend/src/routes/tasks.routes.js
echo "BACKEND_SYNTAX=PASS"

grep -q 'model TalentAssessment {' backend/prisma/schema.prisma
grep -q 'model SuccessionRole {' backend/prisma/schema.prisma
grep -q 'model SuccessionCandidate {' backend/prisma/schema.prisma
echo "PRISMA_TALENT_CONTRACT=PASS"

grep -q '/reports/team-performance/talent/overview' backend/src/routes/tasks.routes.js
grep -q '/reports/team-performance/talent/assessments' backend/src/routes/tasks.routes.js
grep -q '/reports/team-performance/talent/succession-roles' backend/src/routes/tasks.routes.js
grep -q 'MANAGER_ASSESSED_TALENT_MATRIX' backend/src/routes/tasks.routes.js
grep -q 'Readiness is an explicit manager nomination field' backend/src/routes/tasks.routes.js
grep -q 'does not automatically promote, demote, terminate, compensate, or reassign employees' backend/src/routes/tasks.routes.js
echo "BACKEND_TALENT_CONTRACT=PASS"
echo "TALENT_HUMAN_DECISION_GUARD=PASS"

grep -q 'talentOverview:' frontend/src/lib/api.js
grep -q 'assessTalentPotential:' frontend/src/lib/api.js
grep -q 'successionRoles:' frontend/src/lib/api.js
grep -q 'TalentSuccessionPanel' frontend/src/pages/TeamPerformanceDashboard.jsx
grep -q 'EmployeeTalentSuccession' frontend/src/pages/TeamPerformanceDashboard.jsx
grep -q '9-Box Talent & Succession Bench' frontend/src/components/performance/TalentSuccession.jsx
grep -q 'Manager-only' frontend/src/components/performance/TalentSuccession.jsx
echo "FRONTEND_TALENT_INTEGRATION=PASS"

if git diff "$BASELINE" -- backend/src/routes/tasks.routes.js | grep -E '^-.*(eligibleOnTimeCompleted|function calculatePeriodMetrics|calculatePerformanceScore)' >/dev/null; then
  echo "PHASE3_SCORE_FORMULA_REGRESSION=FAIL"
  exit 1
fi
echo "PHASE3_SCORE_FORMULA_REGRESSION=PASS"

if git diff "$BASELINE" -- backend/src/routes/tasks.routes.js | grep -E '^-.*(function buildTeamPerformanceIntelligence|TOP_IMPROVER|WORKLOAD_IMBALANCE)' >/dev/null; then
  echo "PHASE5_INTELLIGENCE_REGRESSION=FAIL"
  exit 1
fi
echo "PHASE5_INTELLIGENCE_REGRESSION=PASS"

if git diff "$BASELINE" -- backend/src/routes/tasks.routes.js | grep -E '^-.*(TARGET_SCOPE_TYPES|function calcTargetAchievement|function buildTargetSummary)' >/dev/null; then
  echo "PHASE6_TARGET_REGRESSION=FAIL"
  exit 1
fi
echo "PHASE6_TARGET_REGRESSION=PASS"

if git diff "$BASELINE" -- backend/src/routes/tasks.routes.js frontend/src/pages/TeamPerformanceDashboard.jsx | grep -E '^-.*(PERFORMANCE_REVIEW_STATUSES|performance_review_created|PerformanceReviewsPanel|EmployeeReviewsSection)' >/dev/null; then
  echo "PHASE7_REVIEW_REGRESSION=FAIL"
  exit 1
fi
echo "PHASE7_REVIEW_REGRESSION=PASS"

if git diff "$BASELINE" -- backend/src/routes/tasks.routes.js frontend/src/pages/TeamPerformanceDashboard.jsx | grep -E '^-.*(WORKFORCE_DEFAULT_WEEKLY_CAPACITY|RULE_BASED_OPERATIONAL_FORECAST|WorkforcePlanningPanel|EmployeeWorkforceOutlook)' >/dev/null; then
  echo "PHASE8_WORKFORCE_REGRESSION=FAIL"
  exit 1
fi
echo "PHASE8_WORKFORCE_REGRESSION=PASS"

if git diff "$BASELINE" -- backend/src/routes/tasks.routes.js frontend/src/pages/TeamPerformanceDashboard.jsx | grep -E '^-.*(SKILL_REQUIREMENT_SCOPES|buildSkillMatrix|SkillsDevelopmentPanel|EmployeeSkillsDevelopment)' >/dev/null; then
  echo "PHASE9_SKILLS_REGRESSION=FAIL"
  exit 1
fi
echo "PHASE9_SKILLS_REGRESSION=PASS"

npm --prefix frontend run build
echo "FRONTEND_BUILD=PASS"

git diff --check
echo "GIT_DIFF_CHECK=PASS"

UNEXPECTED="$(git status --porcelain | awk '{print $2}' | grep -Ev '^(backend/prisma/schema\.prisma|backend/src/routes/tasks\.routes\.js|frontend/src/lib/api\.js|frontend/src/pages/TeamPerformanceDashboard\.jsx|frontend/src/components/performance/TalentSuccession\.jsx|backend/prisma/migrations/202609021410_phase10_talent_matrix_succession_planning/)$' || true)"
if [[ -n "$UNEXPECTED" ]]; then
  echo "$UNEXPECTED"
  echo "EXPECTED_FILE_SCOPE=FAIL"
  exit 1
fi
echo "EXPECTED_FILE_SCOPE=PASS"

echo "PHASE10_TALENT_MATRIX_SUCCESSION_PLANNING_V1_APPLIED=YES"
echo "NO_GIT_COMMIT_OR_PUSH_PERFORMED=YES"
echo "CURRENT_STATUS_BEGIN"
git status --short
echo "CURRENT_STATUS_END"
