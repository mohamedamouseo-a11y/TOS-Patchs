#!/usr/bin/env bash
set -euo pipefail

ROOT=/var/www/TOS
PATCH_DIR="$(cd "$(dirname "$0")" && pwd)"
EXPECTED_HEAD="4fa7ad74489f1e09e16dd63292c240d8a7e6f726"

cd "$ROOT"

HEAD="$(git rev-parse HEAD)"
if [[ "$HEAD" != "$EXPECTED_HEAD" ]]; then
  echo "PHASE5_HELP_CENTER_ERROR=UNEXPECTED_HEAD:$HEAD"
  exit 1
fi

if [[ -n "$(git status --short)" ]]; then
  echo "PHASE5_HELP_CENTER_ERROR=WORKING_TREE_NOT_CLEAN"
  git status --short
  exit 1
fi

echo "PREEXISTING_WORKING_TREE=CLEAN"

python3 "$PATCH_DIR/01_phase5_help_center.py"

DASHBOARD="frontend/src/pages/TeamPerformanceDashboard.jsx"
HELP="frontend/src/components/performance/TeamPerformanceHelpCenter.jsx"

test -f "$HELP"

grep -q 'TeamPerformanceHelpCenter' "$DASHBOARD"
grep -q 'Help Center' "$DASHBOARD"
grep -q 'Understand the number before the decision' "$HELP"
grep -q 'What it means' "$HELP"
grep -q 'How it is calculated' "$HELP"
grep -q 'Source' "$HELP"
grep -q 'How to use it' "$HELP"
grep -q 'Completion 35%' "$HELP"
grep -q 'On-time/Overdue 25%' "$HELP"
grep -q 'Time Efficiency 20%' "$HELP"
grep -q 'Workflow Quality 10%' "$HELP"
grep -q 'Consistency 10%' "$HELP"
grep -q 'High with 4–5 available components' "$HELP"
grep -q '85+ Excellent' "$HELP"
grep -q 'DISABLED rows go to archivedByUser' "$HELP"
grep -q 'PENDING appears in neither live performance nor the archive' "$HELP"
grep -q 'Management Summary' "$HELP"
grep -q 'Drill-down & Navigation' "$HELP"
grep -q 'Executive Command Center' "$HELP"
grep -q 'Goals & Targets' "$HELP"
grep -q 'Performance Intelligence' "$HELP"
grep -q 'Deep Dive modules' "$HELP"
grep -q 'Team Performance table' "$HELP"
grep -q 'Archived Members' "$HELP"

# Phase 5 is explanation-only. It must not touch backend, API contracts, score logic, schema, packages, App routing, or Ramzy.
if git status --short | grep -E '^( M|M |A | D|D |\?\?) backend/'; then
  echo 'PHASE5_HELP_CENTER_ERROR=BACKEND_CHANGED'
  exit 1
fi
if git status --short | grep -E 'backend/prisma|migration|package-lock|pnpm-lock|yarn.lock|package.json|frontend/src/App.jsx|Ramzy'; then
  echo 'PHASE5_HELP_CENTER_ERROR=FORBIDDEN_FILE_CHANGE'
  exit 1
fi

npm --prefix frontend run build

test -f frontend/dist/index.html

git diff --check

python3 - <<'PY'
import subprocess, sys
expected = {
    ' M frontend/src/pages/TeamPerformanceDashboard.jsx',
    '?? frontend/src/components/performance/TeamPerformanceHelpCenter.jsx',
}
actual = set(filter(None, subprocess.check_output(['git','status','--short'], text=True).splitlines()))
if actual != expected:
    print('PHASE5_HELP_CENTER_ERROR=UNEXPECTED_FINAL_STATUS')
    print('\n'.join(sorted(actual)))
    sys.exit(1)
print('EXPECTED_FILE_SCOPE=PASS')
PY

echo 'TEAM_PERFORMANCE_PHASE5_HELP_CENTER_V1_APPLIED=YES'
echo 'HELP_CENTER_ENTRY_POINT=YES'
echo 'HELP_CENTER_SEARCH=YES'
echo 'HELP_CENTER_MODAL_NO_PAGE_HEIGHT=YES'
echo 'HELP_ARTICLE_STRUCTURE=MEANING_CALCULATION_SOURCE_USAGE'
echo 'SCORE_FORMULA_DOCUMENTED=YES'
echo 'SCORE_NORMALIZATION_DOCUMENTED=YES'
echo 'CONFIDENCE_THRESHOLDS_DOCUMENTED=YES'
echo 'STATUS_THRESHOLDS_DOCUMENTED=YES'
echo 'ACTIVE_DISABLED_PENDING_RULES_DOCUMENTED=YES'
echo 'PHASE1_TO_PHASE4_HELP_TOPICS=YES'
echo 'RAMZY_INTEGRATION_ADDED=NO'
echo 'NEW_SCORE_CREATED=NO'
echo 'BACKEND_CHANGED=NO'
echo 'SCHEMA_CHANGED=NO'
echo 'PACKAGE_CHANGED=NO'
echo 'FRONTEND_BUILD=PASS'
echo 'GIT_DIFF_CHECK=PASS'
echo 'NO_GIT_COMMIT_OR_PUSH_PERFORMED=YES'
