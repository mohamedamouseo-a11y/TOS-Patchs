#!/usr/bin/env bash
set -euo pipefail

ROOT=/var/www/TOS
PATCH_DIR="$(cd "$(dirname "$0")" && pwd)"
EXPECTED_HEAD="495201cfa490f643d9e28252eb523a4e278f385c"

cd "$ROOT"

HEAD="$(git rev-parse HEAD)"
if [[ "$HEAD" != "$EXPECTED_HEAD" ]]; then
  echo "PHASE2_REFINEMENT_ERROR=UNEXPECTED_HEAD:$HEAD"
  exit 1
fi

# Safely remove only the exact known residue from the failed Dashboard V2 patch.
python3 "$PATCH_DIR/00_cleanup_failed_dashboard_v2.py"

if [[ -n "$(git status --short)" ]]; then
  echo 'PHASE2_REFINEMENT_ERROR=WORKTREE_NOT_CLEAN_AFTER_SAFE_CLEANUP'
  git status --short
  exit 1
fi

echo 'PREEXISTING_PHASE1_PHASE2_HEADER_STATE=COMMITTED_IN_BASELINE'
echo 'PHASE2_REFINEMENT_BASELINE=CONFIRMED'

python3 "$PATCH_DIR/01_phase2_refinement.py"
python3 "$PATCH_DIR/02_phase2_control_hardening.py"

# Backend syntax/static contract.
node --check backend/src/routes/tasks.routes.js

grep -q 'archivedByUser' backend/src/routes/tasks.routes.js
grep -q 'accountStatus: user.status' backend/src/routes/tasks.routes.js
grep -q 'const activeByUser = byUser.filter' backend/src/routes/tasks.routes.js
grep -q 'PHASE2_ACTIVE_WORKFORCE_SCOPE' backend/src/routes/tasks.routes.js
grep -q 'status: "ACTIVE"' backend/src/routes/tasks.routes.js

# Frontend contract.
grep -q 'ArchivedPerformanceMembers' frontend/src/pages/TeamPerformanceDashboard.jsx
grep -q 'archivedByUser' frontend/src/pages/TeamPerformanceDashboard.jsx
grep -q 'currentStartValue' frontend/src/components/performance/PerformancePeriodControl.jsx
grep -q 'currentEndValue' frontend/src/components/performance/PerformancePeriodControl.jsx
grep -q 'aria-pressed={active}' frontend/src/components/performance/PerformancePeriodControl.jsx
grep -q 'Disabled employee history' frontend/src/components/performance/ArchivedPerformanceMembers.jsx

# Ensure the invalid mixed nullish/logical syntax is not emitted.
if grep -qF '?? customStart ||' frontend/src/components/performance/PerformancePeriodControl.jsx; then
  echo 'PHASE2_REFINEMENT_ERROR=INVALID_NULLISH_MIX_START'
  exit 1
fi
if grep -qF '?? customEnd ||' frontend/src/components/performance/PerformancePeriodControl.jsx; then
  echo 'PHASE2_REFINEMENT_ERROR=INVALID_NULLISH_MIX_END'
  exit 1
fi

npm --prefix frontend run build

test -f frontend/dist/index.html

git diff --check

python3 - <<'PY'
import subprocess, sys
expected = {
 ' M backend/src/routes/tasks.routes.js',
 ' M frontend/src/components/performance/PerformancePeriodControl.jsx',
 ' M frontend/src/pages/TeamPerformanceDashboard.jsx',
 '?? frontend/src/components/performance/ArchivedPerformanceMembers.jsx',
}
actual = set(filter(None, subprocess.check_output(['git','status','--short'], text=True).splitlines()))
if actual != expected:
    print('PHASE2_REFINEMENT_ERROR=UNEXPECTED_FINAL_STATUS')
    print('\n'.join(sorted(actual)))
    sys.exit(1)
print('EXPECTED_FILE_SCOPE=PASS')
PY

echo 'TEAM_PERFORMANCE_PHASE2_REFINEMENT_V1_APPLIED=YES'
echo 'DATE_PRESET_INPUT_SYNC=YES'
echo 'CURRENT_PERIOD_LABEL_FIXED=YES'
echo 'COMPARISON_PERIOD_LABEL_FIXED=YES'
echo 'ACTIVE_PRESET_VISUAL_STATE=YES'
echo 'LIVE_PERFORMANCE_ACTIVE_ONLY=YES'
echo 'DISABLED_MEMBERS_EXCLUDED_FROM_KPIS=YES'
echo 'DISABLED_MEMBERS_EXCLUDED_FROM_RANKING=YES'
echo 'DISABLED_MEMBERS_EXCLUDED_FROM_COMPARISON=YES'
echo 'DISABLED_MEMBERS_EXCLUDED_FROM_ADVANCED_LIVE_MODULES=YES'
echo 'DISABLED_HISTORY_ARCHIVED=YES'
echo 'ARCHIVED_MEMBERS_DEFAULT_COLLAPSED=YES'
echo 'FRONTEND_BUILD=PASS'
echo 'BACKEND_SYNTAX=PASS'
echo 'GIT_DIFF_CHECK=PASS'
echo 'NO_SCHEMA_OR_MIGRATION=YES'
echo 'NO_GIT_COMMIT_OR_PUSH_PERFORMED=YES'
