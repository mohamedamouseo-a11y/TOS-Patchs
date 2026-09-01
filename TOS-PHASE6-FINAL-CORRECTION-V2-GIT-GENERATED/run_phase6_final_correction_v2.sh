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

if ! grep -q 'model PerformanceTarget' backend/prisma/schema.prisma; then
  echo "PHASE6_V1_WORKTREE_CHECK=FAIL PerformanceTarget model missing"
  exit 1
fi
if [[ ! -f backend/prisma/migrations/202609011600_phase6_performance_targets/migration.sql ]]; then
  echo "PHASE6_V1_WORKTREE_CHECK=FAIL migration missing"
  exit 1
fi
if ! grep -q 'router.post("/reports/team-performance/targets/bulk"' backend/src/routes/tasks.routes.js; then
  echo "PHASE6_V1_WORKTREE_CHECK=FAIL target routes missing"
  exit 1
fi
echo "PHASE6_V1_WORKTREE_CHECK=PASS"

python3 "$PATCH_DIR/generate_phase6_final_correction_v2.py" "$REPO"

node --check backend/src/routes/tasks.routes.js
echo "BACKEND_SYNTAX=PASS"

npm --prefix backend run prisma:validate:wasm
echo "PRISMA_VALIDATE=PASS"

npm --prefix backend run prisma:deploy
echo "PRISMA_DEPLOY=PASS"

npm --prefix backend run prisma:generate
echo "PRISMA_GENERATE=PASS"

if ! grep -q 'Target employee not found' backend/src/routes/tasks.routes.js; then
  echo "INVALID_EMPLOYEE_VALIDATION=FAIL"
  exit 1
fi
echo "INVALID_EMPLOYEE_VALIDATION=PASS"

if ! grep -q 'Unauthorized employee target' backend/src/routes/tasks.routes.js; then
  echo "MANAGER_SCOPE_ENFORCEMENT=FAIL"
  exit 1
fi
echo "MANAGER_SCOPE_ENFORCEMENT=PASS"

if ! grep -q 'An active target already exists for this subject and exact period' backend/src/routes/tasks.routes.js; then
  echo "EXACT_DUPLICATE_GUARD=FAIL"
  exit 1
fi
echo "EXACT_DUPLICATE_GUARD=PASS"

if ! grep -q 'async function getTargetAccessScope(req)' backend/src/routes/tasks.routes.js; then
  echo "LIGHTWEIGHT_TARGET_SCOPE=FAIL"
  exit 1
fi
echo "LIGHTWEIGHT_TARGET_SCOPE=PASS"

if git diff "$BASELINE" -- backend/src/routes/tasks.routes.js | grep -E '^[+-].*function calculatePerformanceScore|^[+-].*eligibleOnTimeCompleted|^[+-].*onTimeCompleted / eligibleOnTimeCompleted' >/dev/null; then
  echo "PHASE3_SCORE_FORMULA_REGRESSION=FAIL"
  exit 1
fi
echo "PHASE3_SCORE_FORMULA_REGRESSION=PASS"

npm --prefix frontend run build
echo "FRONTEND_BUILD=PASS"

git diff --check
echo "GIT_DIFF_CHECK=PASS"

echo "PHASE6_FINAL_CORRECTION_V2_APPLIED=YES"
echo "NO_GIT_COMMIT_OR_PUSH_PERFORMED=YES"
echo "CURRENT_STATUS_BEGIN"
git status --short
echo "CURRENT_STATUS_END"
