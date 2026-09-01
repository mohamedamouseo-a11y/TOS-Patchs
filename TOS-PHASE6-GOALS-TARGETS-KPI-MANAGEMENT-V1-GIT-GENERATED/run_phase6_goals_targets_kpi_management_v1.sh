#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-/var/www/TOS}"
BASELINE="9773ffa21fabe90c87823081984ebb6bb55999e1"
PATCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$REPO"

HEAD="$(git rev-parse HEAD)"
if [[ "$HEAD" != "$BASELINE" ]]; then
  echo "BASELINE_CHECK=FAIL expected=$BASELINE actual=$HEAD"
  exit 1
fi
echo "BASELINE_CHECK=PASS"

TARGET_STATUS="$(git status --porcelain -- backend/prisma/schema.prisma backend/src/routes/tasks.routes.js frontend/src/lib/api.js frontend/src/pages/TeamPerformanceDashboard.jsx backend/prisma/migrations/202609011600_phase6_performance_targets || true)"
if [[ -n "$TARGET_STATUS" ]]; then
  echo "$TARGET_STATUS"
  echo "TARGETS_CLEAN=FAIL"
  exit 1
fi
echo "TARGETS_CLEAN=PASS"

python3 "$PATCH_DIR/01_phase6_schema.py" "$REPO"
python3 "$PATCH_DIR/02_phase6_backend.py" "$REPO"
python3 "$PATCH_DIR/03_phase6_frontend.py" "$REPO"

npm --prefix backend run prisma:validate:wasm
echo "PRISMA_VALIDATE=PASS"

npm --prefix backend run prisma:deploy
echo "PRISMA_DEPLOY=PASS"

npm --prefix backend run prisma:generate
echo "PRISMA_GENERATE=PASS"

node --check backend/src/routes/tasks.routes.js
echo "BACKEND_SYNTAX=PASS"

if git diff "$BASELINE" -- backend/src/routes/tasks.routes.js | grep -E '^[+-].*function calculatePerformanceScore|^[+-].*eligibleOnTimeCompleted|^[+-].*onTimeCompleted / eligibleOnTimeCompleted' >/dev/null; then
  echo "PHASE3_SCORE_FORMULA_REGRESSION=FAIL"
  exit 1
fi
echo "PHASE3_SCORE_FORMULA_REGRESSION=PASS"

npm --prefix frontend run build
echo "FRONTEND_BUILD=PASS"

git diff --check
echo "GIT_DIFF_CHECK=PASS"

echo "PHASE6_GOALS_TARGETS_KPI_MANAGEMENT_V1_APPLIED=YES"
echo "NO_GIT_COMMIT_OR_PUSH_PERFORMED=YES"
echo "CURRENT_STATUS_BEGIN"
git status --short
echo "CURRENT_STATUS_END"
