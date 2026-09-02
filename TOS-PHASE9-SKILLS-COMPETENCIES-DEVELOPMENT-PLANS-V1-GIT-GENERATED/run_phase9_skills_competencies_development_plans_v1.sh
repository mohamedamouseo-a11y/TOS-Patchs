#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-/var/www/TOS}"
BASELINE="225230b9a79b839b8fc8ee60aa5f5869e8dba9b1"
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
  frontend/src/components/performance/SkillsDevelopment.jsx \
  backend/prisma/migrations/202609021130_phase9_skills_competencies_development || true)"
if [[ -n "$TARGET_STATUS" ]]; then
  echo "$TARGET_STATUS"
  echo "TARGETS_CLEAN=FAIL"
  exit 1
fi
echo "TARGETS_CLEAN=PASS"

grep -q 'model WorkforceCapacityPlan {' backend/prisma/schema.prisma
grep -q 'WorkforcePlanningPanel' frontend/src/pages/TeamPerformanceDashboard.jsx
grep -q 'RULE_BASED_OPERATIONAL_FORECAST' backend/src/routes/tasks.routes.js
echo "PHASE8_BASELINE_PRESENT=PASS"

python3 "$PATCH_DIR/01_phase9_schema.py" "$REPO"
python3 "$PATCH_DIR/02_phase9_backend.py" "$REPO"
python3 "$PATCH_DIR/03_phase9_api.py" "$REPO"
python3 "$PATCH_DIR/04_phase9_component.py" "$REPO"
python3 "$PATCH_DIR/05_phase9_dashboard.py" "$REPO"

npm --prefix backend run prisma:validate:wasm
echo "PRISMA_VALIDATE=PASS"

npm --prefix backend run prisma:deploy
echo "PRISMA_DEPLOY=PASS"

npm --prefix backend run prisma:generate
echo "PRISMA_GENERATE=PASS"

node --check backend/src/routes/tasks.routes.js
echo "BACKEND_SYNTAX=PASS"

grep -q 'model SkillDefinition {' backend/prisma/schema.prisma
grep -q 'model CompetencyRequirement {' backend/prisma/schema.prisma
grep -q 'model EmployeeSkillAssessment {' backend/prisma/schema.prisma
grep -q 'model EmployeeDevelopmentPlan {' backend/prisma/schema.prisma
grep -q 'model EmployeeDevelopmentAction {' backend/prisma/schema.prisma
echo "PRISMA_SKILLS_CONTRACT=PASS"

grep -q '/reports/team-performance/skills/matrix' backend/src/routes/tasks.routes.js
grep -q '/reports/team-performance/skills/catalog' backend/src/routes/tasks.routes.js
grep -q '/reports/team-performance/skills/requirements' backend/src/routes/tasks.routes.js
grep -q '/reports/team-performance/skills/assessments' backend/src/routes/tasks.routes.js
grep -q '/reports/team-performance/development-plans' backend/src/routes/tasks.routes.js
grep -q 'requirementPrecedence: \["EMPLOYEE", "JOB_TITLE", "DEPARTMENT"\]' backend/src/routes/tasks.routes.js
grep -q 'coverage: "Requirements met / effective required skills' backend/src/routes/tasks.routes.js
echo "BACKEND_SKILLS_CONTRACT=PASS"
echo "SKILL_REQUIREMENT_PRECEDENCE=PASS"
echo "SKILL_COVERAGE_SEPARATE_FROM_SCORE=PASS"

grep -q 'skillsMatrix:' frontend/src/lib/api.js
grep -q 'developmentPlans:' frontend/src/lib/api.js
grep -q 'SkillsDevelopmentPanel' frontend/src/pages/TeamPerformanceDashboard.jsx
grep -q 'EmployeeSkillsDevelopment' frontend/src/pages/TeamPerformanceDashboard.jsx
grep -q 'Skills Matrix & Development Plans' frontend/src/components/performance/SkillsDevelopment.jsx
echo "FRONTEND_SKILLS_INTEGRATION=PASS"

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

npm --prefix frontend run build
echo "FRONTEND_BUILD=PASS"

git diff --check
echo "GIT_DIFF_CHECK=PASS"

UNEXPECTED="$(git status --porcelain | awk '{print $2}' | grep -Ev '^(backend/prisma/schema\.prisma|backend/src/routes/tasks\.routes\.js|frontend/src/lib/api\.js|frontend/src/pages/TeamPerformanceDashboard\.jsx|frontend/src/components/performance/SkillsDevelopment\.jsx|backend/prisma/migrations/202609021130_phase9_skills_competencies_development/)$' || true)"
if [[ -n "$UNEXPECTED" ]]; then
  echo "$UNEXPECTED"
  echo "EXPECTED_FILE_SCOPE=FAIL"
  exit 1
fi
echo "EXPECTED_FILE_SCOPE=PASS"

echo "PHASE9_SKILLS_COMPETENCIES_DEVELOPMENT_PLANS_V1_APPLIED=YES"
echo "NO_GIT_COMMIT_OR_PUSH_PERFORMED=YES"
echo "CURRENT_STATUS_BEGIN"
git status --short
echo "CURRENT_STATUS_END"
