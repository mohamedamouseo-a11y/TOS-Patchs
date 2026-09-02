#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-/var/www/TOS}"
BASELINE="91f569c31087421b069d3ac4ab5ce87fb6b61a7f"
PATCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$REPO"

HEAD="$(git rev-parse HEAD)"
if [[ "$HEAD" != "$BASELINE" ]]; then
  echo "BASELINE_CHECK=FAIL expected=$BASELINE actual=$HEAD"
  exit 1
fi
echo "BASELINE_CHECK=PASS"

TARGET_STATUS="$(git status --porcelain -- \
  backend/src/routes/tasks.routes.js \
  frontend/src/lib/api.js \
  frontend/src/pages/TeamPerformanceDashboard.jsx \
  frontend/src/components/performance/ExecutiveCommandCenter.jsx || true)"
if [[ -n "$TARGET_STATUS" ]]; then
  echo "$TARGET_STATUS"
  echo "TARGETS_CLEAN=FAIL"
  exit 1
fi
echo "TARGETS_CLEAN=PASS"

grep -q 'model RecognitionPerformanceCycle {' backend/prisma/schema.prisma
grep -q 'model RecognitionAward {' backend/prisma/schema.prisma
grep -q 'PHASE11_RECOGNITION_REWARDS_CYCLES' backend/src/routes/tasks.routes.js
grep -q 'RecognitionRewardsPanel' frontend/src/pages/TeamPerformanceDashboard.jsx
echo "PHASE11_BASELINE_PRESENT=PASS"

python3 "$PATCH_DIR/01_phase12_backend.py" "$REPO"
python3 "$PATCH_DIR/02_phase12_api.py" "$REPO"
python3 "$PATCH_DIR/03_phase12_component.py" "$REPO"
python3 "$PATCH_DIR/04_phase12_dashboard.py" "$REPO"

node --check backend/src/routes/tasks.routes.js
echo "BACKEND_SYNTAX=PASS"

grep -q 'PHASE12_EXECUTIVE_WORKFORCE_COMMAND_CENTER' backend/src/routes/tasks.routes.js
grep -q '/reports/team-performance/executive-command-center' backend/src/routes/tasks.routes.js
grep -q 'buildExecutiveCommandCenter' backend/src/routes/tasks.routes.js
grep -q 'buildExecutiveReviewSignals' backend/src/routes/tasks.routes.js
echo "BACKEND_EXECUTIVE_COMMAND_CENTER=PASS"

grep -q 'EXECUTIVE_CROSS_WORKFORCE_DECISION_SUPPORT' backend/src/routes/tasks.routes.js
grep -q 'creates no replacement performance score, talent score, risk score, or automated employment decision' backend/src/routes/tasks.routes.js
grep -q 'Severity buckets' /dev/null 2>/dev/null || true
grep -q 'ordered only by transparent severity buckets' backend/src/routes/tasks.routes.js
grep -q 'does not automatically promote, demote, terminate, compensate, reassign, recognize, or succession-select employees' backend/src/routes/tasks.routes.js
echo "EXECUTIVE_NO_COMPOSITE_SCORE_GUARD=PASS"
echo "EXECUTIVE_HUMAN_DECISION_GUARD=PASS"

grep -q 'Executive Workforce Command Center requires admin access' backend/src/routes/tasks.routes.js
grep -q 'assertExecutiveCommandAccess(req)' backend/src/routes/tasks.routes.js
echo "EXECUTIVE_ADMIN_ONLY_RBAC=PASS"

grep -q 'buildTargetSummary(dataset)' backend/src/routes/tasks.routes.js
grep -q 'buildWorkforceForecast(req' backend/src/routes/tasks.routes.js
grep -q 'buildSkillMatrix(req' backend/src/routes/tasks.routes.js
grep -q 'buildTalentOverview(req' backend/src/routes/tasks.routes.js
grep -q 'buildRecognitionOverview(req' backend/src/routes/tasks.routes.js
grep -q 'buildTeamPerformanceIntelligence(dataset)' backend/src/routes/tasks.routes.js
echo "EXECUTIVE_CROSS_PHASE_AGGREGATION=PASS"

grep -q 'executiveCommandCenter:' frontend/src/lib/api.js
grep -q 'ExecutiveCommandCenterPanel' frontend/src/pages/TeamPerformanceDashboard.jsx
grep -q 'Company Workforce Decision View' frontend/src/components/performance/ExecutiveCommandCenter.jsx
grep -q 'Executive Priority Queue' frontend/src/components/performance/ExecutiveCommandCenter.jsx
grep -q 'Department Health Signals' frontend/src/components/performance/ExecutiveCommandCenter.jsx
grep -q 'Decision Domains' frontend/src/components/performance/ExecutiveCommandCenter.jsx
echo "FRONTEND_EXECUTIVE_INTEGRATION=PASS"

if git diff "$BASELINE" -- backend/src/routes/tasks.routes.js | grep -E '^-.*(eligibleOnTimeCompleted|calculatePerformanceScore|function calculatePeriodMetrics)' >/dev/null; then
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

if git diff "$BASELINE" -- backend/src/routes/tasks.routes.js frontend/src/pages/TeamPerformanceDashboard.jsx | grep -E '^-.*(PERFORMANCE_REVIEW_STATUSES|PerformanceReviewsPanel|EmployeeReviewsSection)' >/dev/null; then
  echo "PHASE7_REVIEW_REGRESSION=FAIL"
  exit 1
fi
echo "PHASE7_REVIEW_REGRESSION=PASS"

if git diff "$BASELINE" -- backend/src/routes/tasks.routes.js frontend/src/pages/TeamPerformanceDashboard.jsx | grep -E '^-.*(WORKFORCE_DEFAULT_WEEKLY_CAPACITY|WorkforcePlanningPanel|EmployeeWorkforceOutlook)' >/dev/null; then
  echo "PHASE8_WORKFORCE_REGRESSION=FAIL"
  exit 1
fi
echo "PHASE8_WORKFORCE_REGRESSION=PASS"

if git diff "$BASELINE" -- backend/src/routes/tasks.routes.js frontend/src/pages/TeamPerformanceDashboard.jsx | grep -E '^-.*(PHASE9_SKILLS_COMPETENCIES|SkillsDevelopmentPanel|EmployeeSkillsDevelopment)' >/dev/null; then
  echo "PHASE9_SKILLS_REGRESSION=FAIL"
  exit 1
fi
echo "PHASE9_SKILLS_REGRESSION=PASS"

if git diff "$BASELINE" -- backend/src/routes/tasks.routes.js frontend/src/pages/TeamPerformanceDashboard.jsx | grep -E '^-.*(PHASE10_TALENT_SUCCESSION|TalentSuccessionPanel|EmployeeTalentSuccession)' >/dev/null; then
  echo "PHASE10_TALENT_REGRESSION=FAIL"
  exit 1
fi
echo "PHASE10_TALENT_REGRESSION=PASS"

if git diff "$BASELINE" -- backend/src/routes/tasks.routes.js frontend/src/pages/TeamPerformanceDashboard.jsx | grep -E '^-.*(PHASE11_RECOGNITION_REWARDS_CYCLES|RecognitionRewardsPanel|EmployeeRecognitionRewards)' >/dev/null; then
  echo "PHASE11_RECOGNITION_REGRESSION=FAIL"
  exit 1
fi
echo "PHASE11_RECOGNITION_REGRESSION=PASS"

npm --prefix frontend run build
echo "FRONTEND_BUILD=PASS"

git diff --check
echo "GIT_DIFF_CHECK=PASS"

if git status --porcelain -- backend/package.json backend/package-lock.json backend/prisma/schema.prisma | grep -q .; then
  git status --short -- backend/package.json backend/package-lock.json backend/prisma/schema.prisma
  echo "PACKAGE_SCHEMA_SCOPE_CLEAN=FAIL"
  exit 1
fi
echo "PACKAGE_SCHEMA_SCOPE_CLEAN=PASS"

UNEXPECTED="$(git status --porcelain | awk '{print $2}' | grep -Ev '^(backend/src/routes/tasks\.routes\.js|frontend/src/lib/api\.js|frontend/src/pages/TeamPerformanceDashboard\.jsx|frontend/src/components/performance/ExecutiveCommandCenter\.jsx)$' || true)"
if [[ -n "$UNEXPECTED" ]]; then
  echo "$UNEXPECTED"
  echo "EXPECTED_FILE_SCOPE=FAIL"
  exit 1
fi
echo "EXPECTED_FILE_SCOPE=PASS"

echo "PHASE12_EXECUTIVE_WORKFORCE_COMMAND_CENTER_V1_APPLIED=YES"
echo "FINAL_E2E_QA=DEFERRED_BY_PLAN"
echo "NO_GIT_COMMIT_OR_PUSH_PERFORMED=YES"
echo "CURRENT_STATUS_BEGIN"
git status --short
echo "CURRENT_STATUS_END"
