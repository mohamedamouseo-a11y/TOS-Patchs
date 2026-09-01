#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-/var/www/TOS}"
BASELINE="230559f2ba936466ea6b0246c2a7f2108138e9a5"
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
  frontend/src/components/performance/PerformanceReviews.jsx \
  backend/prisma/migrations/202609020030_phase7_performance_reviews || true)"
if [[ -n "$TARGET_STATUS" ]]; then
  echo "$TARGET_STATUS"
  echo "TARGETS_CLEAN=FAIL"
  exit 1
fi
echo "TARGETS_CLEAN=PASS"

python3 "$PATCH_DIR/01_phase7_schema.py" "$REPO"
python3 "$PATCH_DIR/02_phase7_backend.py" "$REPO"
python3 "$PATCH_DIR/03_phase7_api.py" "$REPO"
python3 "$PATCH_DIR/04_phase7_component.py" "$REPO"
python3 "$PATCH_DIR/05_phase7_dashboard.py" "$REPO"

if ! grep -q 'model PerformanceReview {' backend/prisma/schema.prisma || ! grep -q 'model PerformanceActionItem {' backend/prisma/schema.prisma; then
  echo "PRISMA_REVIEW_MODELS=FAIL"
  exit 1
fi
echo "PRISMA_REVIEW_MODELS=PASS"

if [[ ! -f backend/prisma/migrations/202609020030_phase7_performance_reviews/migration.sql ]]; then
  echo "PRISMA_REVIEW_MIGRATION=FAIL"
  exit 1
fi
echo "PRISMA_REVIEW_MIGRATION=PASS"

npm --prefix backend run prisma:validate:wasm
echo "PRISMA_VALIDATE=PASS"

npm --prefix backend run prisma:deploy
echo "PRISMA_DEPLOY=PASS"

npm --prefix backend run prisma:generate
echo "PRISMA_GENERATE=PASS"

node --check backend/src/routes/tasks.routes.js
echo "BACKEND_SYNTAX=PASS"

for marker in \
  '/reports/team-performance/reviews/summary' \
  'performance_review_created' \
  'performance_review_shared' \
  'performance_review_acknowledged' \
  'performance_review_completed' \
  'performance_action_created' \
  'performance_action_updated'; do
  if ! grep -q "$marker" backend/src/routes/tasks.routes.js; then
    echo "BACKEND_REVIEW_CONTRACT=FAIL missing=$marker"
    exit 1
  fi
done
echo "BACKEND_REVIEW_CONTRACT=PASS"

if ! grep -q 'status === "DRAFT"' backend/src/routes/tasks.routes.js || ! grep -q 'Performance review management requires manager access' backend/src/routes/tasks.routes.js; then
  echo "REVIEW_RBAC_GUARDS=FAIL"
  exit 1
fi
echo "REVIEW_RBAC_GUARDS=PASS"

if ! grep -q 'PerformanceTarget' backend/prisma/schema.prisma || ! grep -q 'TARGET_SCOPE_TYPES' backend/src/routes/tasks.routes.js || ! grep -q 'addTargetIntelligence' backend/src/routes/tasks.routes.js; then
  echo "PHASE6_TARGET_REGRESSION=FAIL"
  exit 1
fi
echo "PHASE6_TARGET_REGRESSION=PASS"

if git diff "$BASELINE" -- backend/src/routes/tasks.routes.js | grep -E '^[+-].*function calculatePerformanceScore|^[+-].*eligibleOnTimeCompleted|^[+-].*onTimeCompleted / eligibleOnTimeCompleted|^[+-].*Completion.*35|^[+-].*On-Time.*25' >/dev/null; then
  echo "PHASE3_SCORE_FORMULA_REGRESSION=FAIL"
  exit 1
fi
echo "PHASE3_SCORE_FORMULA_REGRESSION=PASS"

for marker in \
  'performanceReviewSummary:' \
  'createPerformanceReview:' \
  'acknowledgePerformanceReview:' \
  'createPerformanceAction:'; do
  if ! grep -q "$marker" frontend/src/lib/api.js; then
    echo "FRONTEND_REVIEW_API=FAIL missing=$marker"
    exit 1
  fi
done
echo "FRONTEND_REVIEW_API=PASS"

if [[ ! -f frontend/src/components/performance/PerformanceReviews.jsx ]]; then
  echo "FRONTEND_REVIEW_COMPONENT=FAIL"
  exit 1
fi
if ! grep -q 'PerformanceReviewsPanel' frontend/src/pages/TeamPerformanceDashboard.jsx || ! grep -q 'EmployeeReviewsSection' frontend/src/pages/TeamPerformanceDashboard.jsx; then
  echo "FRONTEND_REVIEW_INTEGRATION=FAIL"
  exit 1
fi
echo "FRONTEND_REVIEW_INTEGRATION=PASS"

npm --prefix frontend run build
echo "FRONTEND_BUILD=PASS"

git diff --check
echo "GIT_DIFF_CHECK=PASS"

echo "PHASE7_PERFORMANCE_REVIEWS_COACHING_ACTION_PLANS_V1_APPLIED=YES"
echo "NO_GIT_COMMIT_OR_PUSH_PERFORMED=YES"
echo "CURRENT_STATUS_BEGIN"
git status --short
echo "CURRENT_STATUS_END"
