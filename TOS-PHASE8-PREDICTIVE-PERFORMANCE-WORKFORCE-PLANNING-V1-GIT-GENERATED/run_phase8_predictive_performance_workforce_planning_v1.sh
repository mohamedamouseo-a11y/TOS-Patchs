#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-/var/www/TOS}"
BASELINE="125b92e5779294cb23d057d5017e8b1b288d8c7b"
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
  frontend/src/components/performance/WorkforcePlanning.jsx \
  backend/prisma/migrations/202609020120_phase8_workforce_capacity_plans || true)"
if [[ -n "$TARGET_STATUS" ]]; then
  echo "$TARGET_STATUS"
  echo "TARGETS_CLEAN=FAIL"
  exit 1
fi
echo "TARGETS_CLEAN=PASS"

# Phase 7 must already exist in the baseline.
grep -q 'model PerformanceReview {' backend/prisma/schema.prisma
grep -q 'performance_review_created' backend/src/routes/tasks.routes.js
grep -q 'PerformanceReviewsPanel' frontend/src/pages/TeamPerformanceDashboard.jsx
echo "PHASE7_BASELINE_PRESENT=PASS"

python3 "$PATCH_DIR/01_phase8_schema.py" "$REPO"
python3 "$PATCH_DIR/02_phase8_backend.py" "$REPO"
python3 "$PATCH_DIR/02b_phase8_backend_hardening.py" "$REPO"
python3 "$PATCH_DIR/03_phase8_api.py" "$REPO"
python3 "$PATCH_DIR/04_phase8_component.py" "$REPO"
python3 "$PATCH_DIR/05_phase8_dashboard.py" "$REPO"

npm --prefix backend run prisma:validate:wasm
echo "PRISMA_VALIDATE=PASS"

npm --prefix backend run prisma:deploy
echo "PRISMA_DEPLOY=PASS"

npm --prefix backend run prisma:generate
echo "PRISMA_GENERATE=PASS"

node --check backend/src/routes/tasks.routes.js
echo "BACKEND_SYNTAX=PASS"

grep -q 'model WorkforceCapacityPlan {' backend/prisma/schema.prisma
grep -q '/reports/team-performance/workforce/forecast' backend/src/routes/tasks.routes.js
grep -q '/reports/team-performance/workforce/capacity-plans' backend/src/routes/tasks.routes.js
grep -q 'RULE_BASED_OPERATIONAL_FORECAST' backend/src/routes/tasks.routes.js
grep -q 'assertNoOverlappingCapacityPlan' backend/src/routes/tasks.routes.js
grep -q 'performanceScore != null && Number(performanceScore) < 50' backend/src/routes/tasks.routes.js
grep -q 'Workforce employee not found' backend/src/routes/tasks.routes.js
grep -q 'tasksByUser' backend/src/routes/tasks.routes.js
grep -q 'actionsByUser' backend/src/routes/tasks.routes.js
echo "BACKEND_WORKFORCE_CONTRACT=PASS"
echo "WORKFORCE_CAPACITY_OVERLAP_GUARD=PASS"
echo "WORKFORCE_ACCESS_HARDENING=PASS"
echo "NO_ACTIVITY_OUTLOOK_HARDENING=PASS"
echo "WORKFORCE_BULK_AGGREGATION=PASS"

grep -q 'workforceForecast:' frontend/src/lib/api.js
grep -q 'workforceCapacityPlans:' frontend/src/lib/api.js
grep -q 'WorkforcePlanningPanel' frontend/src/pages/TeamPerformanceDashboard.jsx
grep -q 'EmployeeWorkforceOutlook' frontend/src/pages/TeamPerformanceDashboard.jsx
grep -q 'Predictive Performance & Workforce Planning' frontend/src/components/performance/WorkforcePlanning.jsx
echo "FRONTEND_WORKFORCE_INTEGRATION=PASS"

if git diff "$BASELINE" -- backend/src/routes/tasks.routes.js | grep -E '^-.*(eligibleOnTimeCompleted|function calculatePeriodMetrics|calculatePerformanceScore)' >/dev/null; then
  echo "PHASE3_SCORE_FORMULA_REGRESSION=FAIL"
  exit 1
fi
echo "PHASE3_SCORE_FORMULA_REGRESSION=PASS"

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

npm --prefix frontend run build
echo "FRONTEND_BUILD=PASS"

git diff --check
echo "GIT_DIFF_CHECK=PASS"

UNEXPECTED="$(git status --porcelain | awk '{print $2}' | grep -Ev '^(backend/prisma/schema\.prisma|backend/src/routes/tasks\.routes\.js|frontend/src/lib/api\.js|frontend/src/pages/TeamPerformanceDashboard\.jsx|frontend/src/components/performance/WorkforcePlanning\.jsx|backend/prisma/migrations/202609020120_phase8_workforce_capacity_plans/)$' || true)"
if [[ -n "$UNEXPECTED" ]]; then
  echo "$UNEXPECTED"
  echo "EXPECTED_FILE_SCOPE=FAIL"
  exit 1
fi
echo "EXPECTED_FILE_SCOPE=PASS"

echo "PHASE8_PREDICTIVE_PERFORMANCE_WORKFORCE_PLANNING_V1_APPLIED=YES"
echo "NO_GIT_COMMIT_OR_PUSH_PERFORMED=YES"
echo "CURRENT_STATUS_BEGIN"
git status --short
echo "CURRENT_STATUS_END"
