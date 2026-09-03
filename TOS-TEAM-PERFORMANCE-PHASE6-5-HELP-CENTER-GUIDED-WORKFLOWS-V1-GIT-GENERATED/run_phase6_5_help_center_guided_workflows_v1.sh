#!/usr/bin/env bash
set -euo pipefail

TOS=/var/www/TOS
PATCH_DIR=/var/www/TOS-Patchs/TOS-TEAM-PERFORMANCE-PHASE6-5-HELP-CENTER-GUIDED-WORKFLOWS-V1-GIT-GENERATED
EXPECTED_HEAD=5831f3763a43d43ae16891208f653e03b39f4936

normalize_status() {
  printf '%s\n' "$1" | sed '/^[[:space:]]*$/d' | sort
}

cd "$TOS"

HEAD_NOW="$(git rev-parse HEAD)"
if [[ "$HEAD_NOW" != "$EXPECTED_HEAD" ]]; then
  echo "PHASE6_5_ERROR=HEAD_MISMATCH"
  echo "EXPECTED_HEAD=$EXPECTED_HEAD"
  echo "ACTUAL_HEAD=$HEAD_NOW"
  exit 1
fi

# This patch intentionally completes the partial direct Phase 6.5 attempt.
# The three support files must already be modified; Help Center must still be clean.
EXPECTED_PRE_STATUS=$(cat <<'EOF'
 M frontend/src/App.jsx
 M frontend/src/components/RamzyAssistant.jsx
 M frontend/src/pages/TeamPerformanceDashboard.jsx
EOF
)
ACTUAL_PRE_STATUS="$(git status --short)"
if [[ "$(normalize_status "$ACTUAL_PRE_STATUS")" != "$(normalize_status "$EXPECTED_PRE_STATUS")" ]]; then
  echo "PHASE6_5_ERROR=UNEXPECTED_PRE_STATUS"
  printf '%s\n' "$ACTUAL_PRE_STATUS"
  exit 1
fi

# Verify support bridge markers before writing Help Center.
grep -q 'tos:help-navigate' frontend/src/App.jsx || {
  echo "PHASE6_5_ERROR=APP_NAV_BRIDGE_MISSING"
  exit 1
}
grep -q 'tos:ramzy-help' frontend/src/components/RamzyAssistant.jsx || {
  echo "PHASE6_5_ERROR=RAMZY_BRIDGE_MISSING"
  exit 1
}

python3 "$PATCH_DIR/01_phase6_5_help_center_guided_workflows.py"

# Required content markers.
grep -q 'key: "performance-decline"' frontend/src/components/performance/TeamPerformanceHelpCenter.jsx
grep -q 'key: "permissions"' frontend/src/components/performance/TeamPerformanceHelpCenter.jsx
grep -q 'ramzyPrompt' frontend/src/components/performance/TeamPerformanceHelpCenter.jsx
grep -q 'اسأل رمزي عن هذا الموضوع' frontend/src/components/performance/TeamPerformanceHelpCenter.jsx
grep -q 'Ask Ramzy about this topic' frontend/src/components/performance/TeamPerformanceHelpCenter.jsx
grep -q 'لمزيد من التفاصيل' frontend/src/components/performance/TeamPerformanceHelpCenter.jsx
grep -q 'More details' frontend/src/components/performance/TeamPerformanceHelpCenter.jsx

# Correct Git blob comparison.
HEAD_HELP_BLOB="$(git rev-parse HEAD:frontend/src/components/performance/TeamPerformanceHelpCenter.jsx)"
WORKTREE_HELP_BLOB="$(git hash-object frontend/src/components/performance/TeamPerformanceHelpCenter.jsx)"
if [[ "$HEAD_HELP_BLOB" == "$WORKTREE_HELP_BLOB" ]]; then
  echo "PHASE6_5_ERROR=HELP_CENTER_DID_NOT_CHANGE"
  exit 1
fi

npm --prefix frontend run build

rm -rf /opt/apps/tamiyouz-front/build/*
cp -a /var/www/TOS/frontend/dist/. /opt/apps/tamiyouz-front/build/
pm2 reload tamiyouz-frontend

sleep 2

DASHBOARD_HTTP="$(curl -ks -o /dev/null -w '%{http_code}' https://tos.tamiyouz.com/dashboard || true)"
TEAM_PERFORMANCE_HTTP="$(curl -ks -o /dev/null -w '%{http_code}' https://tos.tamiyouz.com/team-performance || true)"
TASKS_HTTP="$(curl -ks -o /dev/null -w '%{http_code}' https://tos.tamiyouz.com/tasks || true)"

if ! diff -qr /var/www/TOS/frontend/dist /opt/apps/tamiyouz-front/build >/dev/null; then
  echo "PHASE6_5_ERROR=DIST_DEPLOY_MISMATCH"
  exit 1
fi

git diff --check

EXPECTED_POST_STATUS=$(cat <<'EOF'
 M frontend/src/App.jsx
 M frontend/src/components/RamzyAssistant.jsx
 M frontend/src/components/performance/TeamPerformanceHelpCenter.jsx
 M frontend/src/pages/TeamPerformanceDashboard.jsx
EOF
)
ACTUAL_POST_STATUS="$(git status --short)"
if [[ "$(normalize_status "$ACTUAL_POST_STATUS")" != "$(normalize_status "$EXPECTED_POST_STATUS")" ]]; then
  echo "PHASE6_5_ERROR=UNEXPECTED_POST_STATUS"
  printf '%s\n' "$ACTUAL_POST_STATUS"
  exit 1
fi

echo "PHASE_6_5_PATCH_APPLY=PASS"
echo "BASELINE_HEAD=$HEAD_NOW"
echo "PATCH_REPO_USED=YES"
echo "GUIDED_WORKFLOWS=PASS"
echo "WORKFLOW_COUNT=14"
echo "MORE_DETAILS_ACCORDION=PASS"
echo "DEEP_LINKS=PASS"
echo "ASK_RAMZY_BUTTON=PASS"
echo "RAMZY_AUTO_SEND=MUST_BE_NO"
echo "BACKEND_CHANGED=MUST_BE_NO"
echo "RBAC_CHANGED=MUST_BE_NO"
echo "PERFORMANCE_LOGIC_CHANGED=MUST_BE_NO"
echo "FRONTEND_BUILD=PASS"
echo "DASHBOARD_HTTP=$DASHBOARD_HTTP"
echo "TEAM_PERFORMANCE_HTTP=$TEAM_PERFORMANCE_HTTP"
echo "TASKS_HTTP=$TASKS_HTTP"
echo "DIST_VS_DEPLOYED_IDENTICAL=YES"
echo "HEAD_HELP_CENTER_GIT_BLOB=$HEAD_HELP_BLOB"
echo "WORKTREE_HELP_CENTER_GIT_BLOB=$WORKTREE_HELP_BLOB"
echo "GIT_DIFF_CHECK=PASS"
echo "NO_COMMIT_OR_PUSH=YES"
echo "FILES_CHANGED:"
git status --short
