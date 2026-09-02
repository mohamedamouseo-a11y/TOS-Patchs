#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-/var/www/TOS}"
BASELINE="7cefa3ef82cad91a90b184fc1f8e4e12ec670a47"
PATCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MIGRATION_DIR="backend/prisma/migrations/202609021430_phase11_recognition_rewards_performance_cycles"

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
  frontend/src/components/performance/RecognitionRewards.jsx \
  "$MIGRATION_DIR" || true)"
if [[ -n "$TARGET_STATUS" ]]; then
  echo "$TARGET_STATUS"
  echo "TARGETS_CLEAN=FAIL"
  exit 1
fi
echo "TARGETS_CLEAN=PASS"

grep -q 'model TalentAssessment {' backend/prisma/schema.prisma
grep -q 'model SuccessionRole {' backend/prisma/schema.prisma
grep -q 'TalentSuccessionPanel' frontend/src/pages/TeamPerformanceDashboard.jsx
grep -q 'PHASE10_TALENT_SUCCESSION' backend/src/routes/tasks.routes.js
echo "PHASE10_BASELINE_PRESENT=PASS"

python3 "$PATCH_DIR/01_phase11_schema.py" "$REPO"
python3 "$PATCH_DIR/02_phase11_backend.py" "$REPO"
python3 "$PATCH_DIR/02b_phase11_date_boundary_hardening.py" "$REPO"
python3 "$PATCH_DIR/03_phase11_api.py" "$REPO"
python3 "$PATCH_DIR/04_phase11_component.py" "$REPO"
python3 "$PATCH_DIR/05_phase11_dashboard.py" "$REPO"

npm --prefix backend run prisma:validate:wasm
echo "PRISMA_VALIDATE=PASS"

npm --prefix backend run prisma:deploy
echo "PRISMA_DEPLOY=PASS"

npm --prefix backend run prisma:generate
echo "PRISMA_GENERATE=PASS"

node --check backend/src/routes/tasks.routes.js
echo "BACKEND_SYNTAX=PASS"

grep -q 'model RecognitionPerformanceCycle {' backend/prisma/schema.prisma
grep -q 'model RecognitionCategory {' backend/prisma/schema.prisma
grep -q 'model RecognitionNomination {' backend/prisma/schema.prisma
grep -q 'model RecognitionAward {' backend/prisma/schema.prisma
test -f "$MIGRATION_DIR/migration.sql"
echo "PRISMA_RECOGNITION_CONTRACT=PASS"
echo "PRISMA_RECOGNITION_MIGRATION=PASS"

grep -q '/reports/team-performance/recognition/overview' backend/src/routes/tasks.routes.js
grep -q '/reports/team-performance/recognition/cycles' backend/src/routes/tasks.routes.js
grep -q '/reports/team-performance/recognition/categories' backend/src/routes/tasks.routes.js
grep -q '/reports/team-performance/recognition/nominations' backend/src/routes/tasks.routes.js
grep -q '/reports/team-performance/recognition/feed' backend/src/routes/tasks.routes.js
grep -q '/reports/team-performance/recognition/employee/:employeeId' backend/src/routes/tasks.routes.js
echo "BACKEND_RECOGNITION_CONTRACT=PASS"

grep -q 'HUMAN_RECOGNITION_DECISION_SUPPORT' backend/src/routes/tasks.routes.js
grep -q 'never auto-approve, auto-reject, or auto-create a reward' backend/src/routes/tasks.routes.js
grep -q 'does not calculate salary, bonus, commission, or compensation' backend/src/routes/tasks.routes.js
grep -q 'RECOGNITION_REWARD_TYPES = new Set(\["NONE", "BADGE", "CERTIFICATE", "GIFT", "EXPERIENCE", "OTHER"\])' backend/src/routes/tasks.routes.js
echo "RECOGNITION_HUMAN_DECISION_GUARD=PASS"
echo "NON_PAYROLL_REWARD_GUARD=PASS"

grep -q 'snapshotPerformanceScore' backend/src/routes/tasks.routes.js
grep -q 'snapshotTargetAchievement' backend/src/routes/tasks.routes.js
grep -q 'buildRecognitionPerformanceSnapshot' backend/src/routes/tasks.routes.js
echo "PERFORMANCE_CONTEXT_SNAPSHOT=PASS"

grep -q 'function recognitionBoundaryDate' backend/src/routes/tasks.routes.js
grep -q 'date.setUTCHours(23, 59, 59, 999)' backend/src/routes/tasks.routes.js
echo "RECOGNITION_DATE_BOUNDARY_HARDENING=PASS"

grep -q 'recognitionOverview:' frontend/src/lib/api.js
grep -q 'createRecognitionCycle:' frontend/src/lib/api.js
grep -q 'createRecognitionNomination:' frontend/src/lib/api.js
grep -q 'approveRecognitionNomination:' frontend/src/lib/api.js
grep -q 'RecognitionRewardsPanel' frontend/src/pages/TeamPerformanceDashboard.jsx
grep -q 'EmployeeRecognitionRewards' frontend/src/pages/TeamPerformanceDashboard.jsx
grep -q 'Recognition, Rewards & Performance Cycles' frontend/src/components/performance/RecognitionRewards.jsx
echo "FRONTEND_RECOGNITION_INTEGRATION=PASS"

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

npm --prefix frontend run build
echo "FRONTEND_BUILD=PASS"

git diff --check
echo "GIT_DIFF_CHECK=PASS"

if git status --porcelain -- backend/package.json backend/package-lock.json | grep -q .; then
  git status --short -- backend/package.json backend/package-lock.json
  echo "PACKAGE_SCOPE_CLEAN=FAIL"
  exit 1
fi
echo "PACKAGE_SCOPE_CLEAN=PASS"

UNEXPECTED="$(git status --porcelain | awk '{print $2}' | grep -Ev '^(backend/prisma/schema\.prisma|backend/src/routes/tasks\.routes\.js|frontend/src/lib/api\.js|frontend/src/pages/TeamPerformanceDashboard\.jsx|frontend/src/components/performance/RecognitionRewards\.jsx|backend/prisma/migrations/202609021430_phase11_recognition_rewards_performance_cycles/)$' || true)"
if [[ -n "$UNEXPECTED" ]]; then
  echo "$UNEXPECTED"
  echo "EXPECTED_FILE_SCOPE=FAIL"
  exit 1
fi
echo "EXPECTED_FILE_SCOPE=PASS"

echo "PHASE11_RECOGNITION_REWARDS_PERFORMANCE_CYCLES_V1_APPLIED=YES"
echo "FINAL_E2E_QA=DEFERRED_BY_PLAN"
echo "NO_GIT_COMMIT_OR_PUSH_PERFORMED=YES"
echo "CURRENT_STATUS_BEGIN"
git status --short
echo "CURRENT_STATUS_END"
