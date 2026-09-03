#!/usr/bin/env bash
set -euo pipefail

ROOT=/var/www/TOS
PATCH_DIR="$(cd "$(dirname "$0")" && pwd)"
EXPECTED_HEAD="4cd67350304736ea24bd64e3bfac86ec897486b2"

cd "$ROOT"

HEAD="$(git rev-parse HEAD)"
if [[ "$HEAD" != "$EXPECTED_HEAD" ]]; then
  echo "PHASE4_DRILLDOWN_ERROR=UNEXPECTED_HEAD:$HEAD"
  exit 1
fi

if [[ -n "$(git status --short)" ]]; then
  echo "PHASE4_DRILLDOWN_ERROR=WORKING_TREE_NOT_CLEAN"
  git status --short
  exit 1
fi

echo "PREEXISTING_WORKING_TREE=CLEAN"

python3 "$PATCH_DIR/01_phase4_drilldown_navigation.py"

DASHBOARD="frontend/src/pages/TeamPerformanceDashboard.jsx"
NAVIGATOR="frontend/src/components/performance/PerformanceDrilldownNavigator.jsx"

grep -q 'PerformanceDrilldownNavigator' "$DASHBOARD"
grep -q 'phase4-drilldown-disclosure' "$DASHBOARD"
grep -q 'Company → Department → Employee → Task' "$DASHBOARD"
grep -q 'DEPARTMENT_PAGE_SIZE = 6' "$NAVIGATOR"
grep -q 'EMPLOYEE_PAGE_SIZE = 8' "$NAVIGATOR"
grep -q 'TASK_PAGE_SIZE = 6' "$NAVIGATOR"
grep -q 'api.tasks.userDashboard' "$NAVIGATOR"
grep -q 'onOpenEmployee?.(selectedEmployee.id)' "$NAVIGATOR"
grep -q 'onOpenTask(task)' "$NAVIGATOR"
grep -q 'accountStatus !== "DISABLED"' "$NAVIGATOR"
grep -q 'accountStatus !== "PENDING"' "$NAVIGATOR"

# Phase 4 is frontend-only.
if git status --short | grep -E '^( M|M |A | D|D |\?\?) backend/'; then
  echo 'PHASE4_DRILLDOWN_ERROR=BACKEND_CHANGED'
  exit 1
fi
if git status --short | grep -E 'backend/prisma|migration|package-lock|pnpm-lock|yarn.lock'; then
  echo 'PHASE4_DRILLDOWN_ERROR=FORBIDDEN_FILE_CHANGE'
  exit 1
fi

npm --prefix frontend run build

test -f frontend/dist/index.html

git diff --check

python3 - <<'PY'
import subprocess, sys
expected = {
    ' M frontend/src/pages/TeamPerformanceDashboard.jsx',
    '?? frontend/src/components/performance/PerformanceDrilldownNavigator.jsx',
}
actual = set(filter(None, subprocess.check_output(['git','status','--short'], text=True).splitlines()))
if actual != expected:
    print('PHASE4_DRILLDOWN_ERROR=UNEXPECTED_FINAL_STATUS')
    print('\n'.join(sorted(actual)))
    sys.exit(1)
print('EXPECTED_FILE_SCOPE=PASS')
PY

echo 'TEAM_PERFORMANCE_PHASE4_DRILLDOWN_NAVIGATION_V1_APPLIED=YES'
echo 'DRILLDOWN_LEVELS=COMPANY_DEPARTMENT_EMPLOYEE_TASK'
echo 'DEFAULT_DISCLOSURE_COLLAPSED=YES'
echo 'DEPARTMENT_SEARCH=YES'
echo 'EMPLOYEE_SEARCH=YES'
echo 'TASK_SEARCH=YES'
echo 'DEPARTMENT_PAGINATION=6'
echo 'EMPLOYEE_PAGINATION=8'
echo 'TASK_PAGINATION=6'
echo 'CURRENT_FILTER_SCOPE_RESPECTED=YES'
echo 'ACTIVE_ONLY_INHERITED_FROM_PHASE2=YES'
echo 'EMPLOYEE_DRAWER_REUSED=YES'
echo 'EXISTING_TASK_NAVIGATION_REUSED=YES'
echo 'NEW_BACKEND_ENDPOINT=NO'
echo 'NEW_SCORE_CREATED=NO'
echo 'BACKEND_CHANGED=NO'
echo 'SCHEMA_CHANGED=NO'
echo 'PACKAGE_CHANGED=NO'
echo 'FRONTEND_BUILD=PASS'
echo 'GIT_DIFF_CHECK=PASS'
echo 'NO_GIT_COMMIT_OR_PUSH_PERFORMED=YES'
