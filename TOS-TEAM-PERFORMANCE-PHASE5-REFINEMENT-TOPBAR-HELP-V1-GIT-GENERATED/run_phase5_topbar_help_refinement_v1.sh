#!/usr/bin/env bash
set -euo pipefail

ROOT=/var/www/TOS
EXPECTED_HEAD=4fa7ad74489f1e09e16dd63292c240d8a7e6f726
PATCH_DIR=/var/www/TOS-Patchs/TOS-TEAM-PERFORMANCE-PHASE5-REFINEMENT-TOPBAR-HELP-V1-GIT-GENERATED

cd "$ROOT"

HEAD="$(git rev-parse HEAD)"
if [[ "$HEAD" != "$EXPECTED_HEAD" ]]; then
  echo "PHASE5_TOPBAR_HELP_ERROR=BASELINE_MISMATCH"
  echo "ACTUAL_HEAD=$HEAD"
  echo "EXPECTED_HEAD=$EXPECTED_HEAD"
  exit 1
fi

EXPECTED_STATUS=$' M frontend/src/pages/TeamPerformanceDashboard.jsx\n?? frontend/src/components/performance/TeamPerformanceHelpCenter.jsx'
ACTUAL_STATUS="$(git status --short)"
if [[ "$ACTUAL_STATUS" != "$EXPECTED_STATUS" ]]; then
  echo "PHASE5_TOPBAR_HELP_ERROR=UNEXPECTED_PRE_APPLY_STATUS"
  echo "EXPECTED_STATUS_BEGIN"
  printf '%s\n' "$EXPECTED_STATUS"
  echo "EXPECTED_STATUS_END"
  echo "ACTUAL_STATUS_BEGIN"
  printf '%s\n' "$ACTUAL_STATUS"
  echo "ACTUAL_STATUS_END"
  exit 1
fi

python3 "$PATCH_DIR/01_phase5_topbar_help_refinement.py"

# Static contract checks
grep -q 'CircleHelp' frontend/src/components/layout/Topbar.jsx
grep -q 'onHelpClick' frontend/src/components/layout/Topbar.jsx
grep -q 'Open Help Center' frontend/src/components/layout/Topbar.jsx
grep -q 'tos:team-performance-help' frontend/src/App.jsx
grep -q 'active === "teamPerformance"' frontend/src/App.jsx
grep -q 'tos:team-performance-help' frontend/src/pages/TeamPerformanceDashboard.jsx
grep -q 'TeamPerformanceHelpCenter' frontend/src/pages/TeamPerformanceDashboard.jsx

# The old page-level Help Center button must be gone.
if grep -q '<CircleHelp size={15} /> Help Center' frontend/src/pages/TeamPerformanceDashboard.jsx; then
  echo 'PHASE5_TOPBAR_HELP_ERROR=PAGE_LEVEL_HELP_BUTTON_STILL_PRESENT'
  exit 1
fi

# The Help Center itself must remain intact.
grep -q 'How Team Performance works' frontend/src/components/performance/TeamPerformanceHelpCenter.jsx
grep -q 'Performance Score' frontend/src/components/performance/TeamPerformanceHelpCenter.jsx
grep -q 'Completion 35%' frontend/src/components/performance/TeamPerformanceHelpCenter.jsx
grep -q 'Archived Members' frontend/src/components/performance/TeamPerformanceHelpCenter.jsx

npm --prefix frontend run build

git diff --check

EXPECTED_FINAL=$' M frontend/src/App.jsx\n M frontend/src/components/layout/Topbar.jsx\n M frontend/src/pages/TeamPerformanceDashboard.jsx\n?? frontend/src/components/performance/TeamPerformanceHelpCenter.jsx'
FINAL_STATUS="$(git status --short)"
if [[ "$FINAL_STATUS" != "$EXPECTED_FINAL" ]]; then
  echo "PHASE5_TOPBAR_HELP_ERROR=UNEXPECTED_FINAL_STATUS"
  echo "EXPECTED_FINAL_BEGIN"
  printf '%s\n' "$EXPECTED_FINAL"
  echo "EXPECTED_FINAL_END"
  echo "ACTUAL_FINAL_BEGIN"
  printf '%s\n' "$FINAL_STATUS"
  echo "ACTUAL_FINAL_END"
  exit 1
fi

echo 'PHASE5_TOPBAR_HELP_REFINEMENT=PASS'
echo 'TOPBAR_HELP_ICON=PASS'
echo 'HELP_ICON_CONTEXT=TEAM_PERFORMANCE_ONLY'
echo 'PAGE_LEVEL_HELP_BUTTON_REMOVED=PASS'
echo 'HELP_CENTER_REUSED=PASS'
echo 'FRONTEND_BUILD=PASS'
echo 'GIT_DIFF_CHECK=PASS'
echo 'BACKEND_CHANGED=NO'
echo 'SCHEMA_CHANGED=NO'
echo 'PACKAGE_CHANGED=NO'
echo 'RAMZY_CHANGED=NO'
echo 'NO_COMMIT_OR_PUSH_PERFORMED=YES'
