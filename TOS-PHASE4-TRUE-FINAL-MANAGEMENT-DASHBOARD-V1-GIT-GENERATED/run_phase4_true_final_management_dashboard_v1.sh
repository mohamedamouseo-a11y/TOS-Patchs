#!/usr/bin/env bash
set -euo pipefail

TOS_DIR="${1:-/var/www/TOS}"
BASELINE="c19ac5e54384c2a00f0b81be6ab5de01154c1a96"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$TOS_DIR"

HEAD="$(git rev-parse HEAD)"
if [[ "$HEAD" != "$BASELINE" ]]; then
  echo "BASELINE_CHECK=FAIL expected=$BASELINE actual=$HEAD"
  exit 1
fi
echo "BASELINE_CHECK=PASS"

for target in \
  backend/src/routes/tasks.routes.js \
  frontend/src/pages/TeamPerformanceDashboard.jsx \
  frontend/src/lib/api.js
do
  if ! git diff --quiet -- "$target" || ! git diff --cached --quiet -- "$target"; then
    echo "TARGET_DIRTY=FAIL $target"
    exit 1
  fi
done
echo "TARGETS_CLEAN=PASS"

python3 "$SCRIPT_DIR/generate_phase4_true_final_management_dashboard_v1.py" "$TOS_DIR"

node --check backend/src/routes/tasks.routes.js
echo "BACKEND_SYNTAX=PASS"

if grep -q 'completionRate - (overdue \* 5)' backend/src/routes/tasks.routes.js; then
  echo "FAKE_EXPORT_SCORE_FORMULA_REMOVED=FAIL"
  exit 1
fi
echo "FAKE_EXPORT_SCORE_FORMULA_REMOVED=PASS"

grep -q 'calculatePeriodMetrics(tasksByUser.get(item.id)' backend/src/routes/tasks.routes.js
echo "EXPORT_PHASE3_CALCULATOR=PASS"

grep -q 'exportTeamPerformance:' frontend/src/lib/api.js
grep -q 'teamPerformanceHistory:' frontend/src/lib/api.js
grep -q 'activities:' frontend/src/lib/api.js
echo "FRONTEND_API_WRAPPERS=PASS"

if grep -q 'ProjectTimeCard' frontend/src/pages/TeamPerformanceDashboard.jsx || grep -q 'selectedJobTitle' frontend/src/pages/TeamPerformanceDashboard.jsx; then
  echo "OLD_DASHBOARD_REMOVAL=FAIL"
  exit 1
fi
echo "OLD_DASHBOARD_REMOVAL=PASS"

npm --prefix frontend run build
echo "FRONTEND_BUILD=PASS"

git diff --check
echo "GIT_DIFF_CHECK=PASS"

echo "PHASE4_TRUE_FINAL_MANAGEMENT_DASHBOARD_V1_APPLIED=YES"
echo "NO_GIT_COMMIT_OR_PUSH_PERFORMED=YES"
echo "--- git status --short ---"
git status --short
