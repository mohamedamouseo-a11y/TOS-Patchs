#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-/var/www/TOS}"
PATCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GENERATOR="$PATCH_DIR/generate_phase5_performance_intelligence_alerts_v1.py"

if [[ ! -d "$REPO/.git" ]]; then
  echo "REPO_CHECK=FAIL path=$REPO"
  exit 1
fi

if [[ ! -f "$GENERATOR" ]]; then
  echo "GENERATOR_CHECK=FAIL path=$GENERATOR"
  exit 1
fi

echo "REPO=$REPO"
echo "PATCH_DIR=$PATCH_DIR"
python3 "$GENERATOR" "$REPO"

cd "$REPO"

echo "--- PATCH TARGET STATUS ---"
git status --short -- \
  backend/src/routes/tasks.routes.js \
  frontend/src/lib/api.js \
  frontend/src/pages/TeamPerformanceDashboard.jsx

echo "--- INTELLIGENCE ROUTE CHECK ---"
grep -n 'reports/team-performance/intelligence' backend/src/routes/tasks.routes.js | head -5

echo "--- API WRAPPER CHECK ---"
grep -n 'teamPerformanceIntelligence' frontend/src/lib/api.js | head -5

echo "--- UI CHECK ---"
grep -n 'Management Brief & Alerts\|Live Management Alerts\|Department Performance' frontend/src/pages/TeamPerformanceDashboard.jsx | head -10

echo "PHASE5_PERFORMANCE_INTELLIGENCE_ALERTS_V1_RUNNER=PASS"
echo "NO_GIT_COMMIT_OR_PUSH_PERFORMED=YES"
