#!/usr/bin/env bash
set -euo pipefail

TOS=/var/www/TOS
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXPECTED_HEAD=4fa7ad74489f1e09e16dd63292c240d8a7e6f726

cd "$TOS"

HEAD_NOW="$(git rev-parse HEAD)"
if [[ "$HEAD_NOW" != "$EXPECTED_HEAD" ]]; then
  echo "PHASE5_GLOBAL_HELP_ERROR=UNEXPECTED_HEAD:$HEAD_NOW"
  exit 1
fi

python3 - <<'PY'
import subprocess, sys
expected = {
    ' M frontend/src/App.jsx',
    ' M frontend/src/components/layout/Topbar.jsx',
    ' M frontend/src/pages/TeamPerformanceDashboard.jsx',
    '?? frontend/src/components/performance/TeamPerformanceHelpCenter.jsx',
}
lines = {line for line in subprocess.check_output(['git','status','--short'], text=True).splitlines() if line.strip()}
if lines != expected:
    print('PHASE5_GLOBAL_HELP_ERROR=UNEXPECTED_PRE_STATUS')
    print('\n'.join(sorted(lines)))
    sys.exit(1)
print('PRE_STATUS=PASS')
PY

python3 "$HERE/01_phase5_global_help_icon.py"

# Static contract checks.
grep -Fq 'CircleHelp' frontend/src/components/layout/Topbar.jsx
grep -Fq 'tos:global-help' frontend/src/components/layout/Topbar.jsx
! grep -Fq 'onHelpClick' frontend/src/components/layout/Topbar.jsx
grep -Fq 'GlobalHelpCenterBridge' frontend/src/App.jsx
grep -Fq 'TeamPerformanceHelpCenter' frontend/src/App.jsx
! grep -Fq 'tos:team-performance-help' frontend/src/App.jsx
! grep -Fq 'TeamPerformanceHelpCenter' frontend/src/pages/TeamPerformanceDashboard.jsx

git diff --check
npm --prefix frontend run build
test -f frontend/dist/index.html

python3 - <<'PY'
import subprocess, sys
expected = {
    ' M frontend/src/App.jsx',
    ' M frontend/src/components/layout/Topbar.jsx',
    ' M frontend/src/pages/TeamPerformanceDashboard.jsx',
    '?? frontend/src/components/performance/TeamPerformanceHelpCenter.jsx',
}
lines = {line for line in subprocess.check_output(['git','status','--short'], text=True).splitlines() if line.strip()}
if lines != expected:
    print('PHASE5_GLOBAL_HELP_ERROR=UNEXPECTED_POST_STATUS')
    print('\n'.join(sorted(lines)))
    sys.exit(1)
print('POST_STATUS=PASS')
PY

echo 'PHASE5_GLOBAL_HELP_REFINEMENT=PASS'
echo 'HELP_ICON_ALL_PAGES=YES'
echo 'HELP_ICON_ALL_AUTHENTICATED_USERS=YES'
echo 'HELP_CENTER_GLOBAL_BRIDGE=YES'
echo 'TEAM_PERFORMANCE_HELP_CONTENT_PRESERVED=YES'
echo 'BACKEND_CHANGED=NO'
echo 'SCHEMA_CHANGED=NO'
echo 'PACKAGE_CHANGED=NO'
echo 'RAMZY_CHANGED=NO'
echo 'FRONTEND_BUILD=PASS'
echo 'GIT_DIFF_CHECK=PASS'
echo 'NO_COMMIT_OR_PUSH_PERFORMED=YES'
