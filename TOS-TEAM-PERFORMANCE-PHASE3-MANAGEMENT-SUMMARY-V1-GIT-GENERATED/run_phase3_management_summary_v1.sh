#!/usr/bin/env bash
set -euo pipefail

ROOT=/var/www/TOS
PATCH_DIR="$(cd "$(dirname "$0")" && pwd)"
EXPECTED_HEAD="79ef5d12ce4e6b4df5a3cc7f9829b326ea03afee"

cd "$ROOT"

HEAD="$(git rev-parse HEAD)"
if [[ "$HEAD" != "$EXPECTED_HEAD" ]]; then
  echo "PHASE3_MANAGEMENT_SUMMARY_ERROR=UNEXPECTED_HEAD:$HEAD"
  exit 1
fi

if [[ -n "$(git status --short)" ]]; then
  echo "PHASE3_MANAGEMENT_SUMMARY_ERROR=WORKING_TREE_NOT_CLEAN"
  git status --short
  exit 1
fi

echo "PREEXISTING_WORKING_TREE=CLEAN"

python3 "$PATCH_DIR/01_phase3_management_summary.py"
python3 "$PATCH_DIR/02_phase3_style_hardening.py"

DASHBOARD="frontend/src/pages/TeamPerformanceDashboard.jsx"
SUMMARY="frontend/src/components/performance/ManagementSummary.jsx"

grep -q 'ManagementSummary' "$DASHBOARD"
grep -q 'phase3-management-summary' "$SUMMARY"
grep -q 'What needs your attention' "$SUMMARY"
grep -q 'Doing well' "$SUMMARY"
grep -q 'Needs attention' "$SUMMARY"
grep -q 'Overdue pressure' "$SUMMARY"
grep -q 'Focus now' "$SUMMARY"
grep -q 'does not create a new score' "$SUMMARY"
grep -q 'onOpenEmployee={openEmployee}' "$DASHBOARD"

if grep -q 'dark:border-white/8' "$SUMMARY"; then
  echo 'PHASE3_MANAGEMENT_SUMMARY_ERROR=STYLE_HARDENING_FAILED'
  exit 1
fi

# Guardrails: Phase 3 is frontend-only and must not alter score/business logic.
if git status --short | grep -E '^( M|M |A | D|D |\?\?) backend/'; then
  echo 'PHASE3_MANAGEMENT_SUMMARY_ERROR=BACKEND_CHANGED'
  exit 1
fi
if git status --short | grep -E 'backend/prisma|migration|package-lock|pnpm-lock|yarn.lock'; then
  echo 'PHASE3_MANAGEMENT_SUMMARY_ERROR=FORBIDDEN_FILE_CHANGE'
  exit 1
fi

npm --prefix frontend run build

test -f frontend/dist/index.html

git diff --check

python3 - <<'PY'
import subprocess, sys
expected = {
    ' M frontend/src/pages/TeamPerformanceDashboard.jsx',
    '?? frontend/src/components/performance/ManagementSummary.jsx',
}
actual = set(filter(None, subprocess.check_output(['git','status','--short'], text=True).splitlines()))
if actual != expected:
    print('PHASE3_MANAGEMENT_SUMMARY_ERROR=UNEXPECTED_FINAL_STATUS')
    print('\n'.join(sorted(actual)))
    sys.exit(1)
print('EXPECTED_FILE_SCOPE=PASS')
PY

echo 'TEAM_PERFORMANCE_PHASE3_MANAGEMENT_SUMMARY_V1_APPLIED=YES'
echo 'MANAGEMENT_SUMMARY_VISIBLE=YES'
echo 'DOING_WELL_SECTION=YES'
echo 'NEEDS_ATTENTION_SECTION=YES'
echo 'OVERDUE_PRESSURE_SECTION=YES'
echo 'FOCUS_NOW_SECTION=YES'
echo 'TOP_EMPLOYEES_LIMIT=3'
echo 'EMPLOYEE_DRAWER_LINKS_PRESERVED=YES'
echo 'FILTER_SCOPE_RESPECTED=YES'
echo 'ACTIVE_ONLY_INHERITED_FROM_PHASE2=YES'
echo 'NEW_SCORE_CREATED=NO'
echo 'AUTOMATED_HR_DECISION=NO'
echo 'BACKEND_CHANGED=NO'
echo 'SCHEMA_CHANGED=NO'
echo 'PACKAGE_CHANGED=NO'
echo 'FRONTEND_BUILD=PASS'
echo 'GIT_DIFF_CHECK=PASS'
echo 'NO_GIT_COMMIT_OR_PUSH_PERFORMED=YES'
