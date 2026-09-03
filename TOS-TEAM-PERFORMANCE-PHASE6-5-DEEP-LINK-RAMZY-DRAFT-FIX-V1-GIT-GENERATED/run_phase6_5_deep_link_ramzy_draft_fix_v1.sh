#!/usr/bin/env bash
set -euo pipefail

TOS=/var/www/TOS
PATCH_DIR=/var/www/TOS-Patchs/TOS-TEAM-PERFORMANCE-PHASE6-5-DEEP-LINK-RAMZY-DRAFT-FIX-V1-GIT-GENERATED
EXPECTED_HEAD=900859bf88a007ac1b413fda0df8d9e34a49fc50

normalize_status() {
  printf '%s\n' "$1" | sed '/^[[:space:]]*$/d' | sort
}

cd "$TOS"
HEAD_NOW="$(git rev-parse HEAD)"
if [[ "$HEAD_NOW" != "$EXPECTED_HEAD" ]]; then
  echo "PHASE6_5_FIX_ERROR=HEAD_MISMATCH"
  echo "EXPECTED_HEAD=$EXPECTED_HEAD"
  echo "ACTUAL_HEAD=$HEAD_NOW"
  exit 1
fi

EXPECTED_DIRTY_STATUS=$(cat <<'EOF'
 M frontend/src/App.jsx
 M frontend/src/components/RamzyAssistant.jsx
 M frontend/src/components/performance/TeamPerformanceHelpCenter.jsx
 M frontend/src/pages/TeamPerformanceDashboard.jsx
EOF
)
PRE_STATUS="$(git status --short)"
if [[ -n "$PRE_STATUS" ]] && [[ "$(normalize_status "$PRE_STATUS")" != "$(normalize_status "$EXPECTED_DIRTY_STATUS")" ]]; then
  echo "PHASE6_5_FIX_ERROR=UNEXPECTED_PRE_STATUS"
  printf '%s\n' "$PRE_STATUS"
  exit 1
fi

# Only require the broad Phase 6.5 state; exact anchors may already be old, new, or partially corrected.
grep -q 'tos:help-navigate' frontend/src/App.jsx || { echo "PHASE6_5_FIX_ERROR=PRE_APP_BRIDGE_MISSING"; exit 1; }
grep -q 'tos:ramzy-help' frontend/src/components/RamzyAssistant.jsx || { echo "PHASE6_5_FIX_ERROR=PRE_RAMZY_BRIDGE_MISSING"; exit 1; }
grep -q 'key: "performance-decline"' frontend/src/components/performance/TeamPerformanceHelpCenter.jsx || { echo "PHASE6_5_FIX_ERROR=PRE_HELP_WORKFLOWS_MISSING"; exit 1; }
grep -q 'key: "permissions"' frontend/src/components/performance/TeamPerformanceHelpCenter.jsx || { echo "PHASE6_5_FIX_ERROR=PRE_HELP_PERMISSIONS_MISSING"; exit 1; }

python3 "$PATCH_DIR/01_phase6_5_deep_link_ramzy_draft_fix.py"

if grep -Eq 'phase1-targets|phase4-workforce|phase4-reviews|phase4-skills|phase4-talent|phase4-recognition' frontend/src/components/performance/TeamPerformanceHelpCenter.jsx; then
  echo "PHASE6_5_FIX_ERROR=STALE_HELP_ANCHOR_FOUND"
  exit 1
fi
if grep -q 'الـDrill-down' frontend/src/components/performance/TeamPerformanceHelpCenter.jsx; then
  echo "PHASE6_5_FIX_ERROR=ARABIC_DRILLDOWN_LEAKAGE"
  exit 1
fi

grep -q 'anchor: "phase1-goals-disclosure", labelKey: "goals"' frontend/src/components/performance/TeamPerformanceHelpCenter.jsx
grep -q 'anchor: "team-performance-workforce", labelKey: "workforce"' frontend/src/components/performance/TeamPerformanceHelpCenter.jsx
grep -q 'anchor: "team-performance-reviews", labelKey: "reviews"' frontend/src/components/performance/TeamPerformanceHelpCenter.jsx
grep -q 'anchor: "team-performance-skills", labelKey: "skills"' frontend/src/components/performance/TeamPerformanceHelpCenter.jsx
grep -q 'anchor: "team-performance-talent", labelKey: "talent"' frontend/src/components/performance/TeamPerformanceHelpCenter.jsx
grep -q 'anchor: "team-performance-recognition", labelKey: "recognition"' frontend/src/components/performance/TeamPerformanceHelpCenter.jsx

for id in team-performance-workforce team-performance-reviews team-performance-skills team-performance-talent team-performance-recognition; do
  grep -q "id=\"$id\"" frontend/src/pages/TeamPerformanceDashboard.jsx || {
    echo "PHASE6_5_FIX_ERROR=MISSING_TARGET_ID_$id"
    exit 1
  }
done

grep -q 'function scrollToSection' frontend/src/App.jsx
grep -q 'closest?.("details")' frontend/src/App.jsx
grep -q 'attempt >= 20' frontend/src/App.jsx
grep -q 'Use Help Center question' frontend/src/components/RamzyAssistant.jsx
grep -q 'استخدام سؤال مركز المساعدة' frontend/src/components/RamzyAssistant.jsx
grep -q 'helpSuggestion' frontend/src/components/RamzyAssistant.jsx

EXPECTED_FILES=$(cat <<'EOF'
frontend/src/App.jsx
frontend/src/components/RamzyAssistant.jsx
frontend/src/components/performance/TeamPerformanceHelpCenter.jsx
frontend/src/pages/TeamPerformanceDashboard.jsx
EOF
)
ACTUAL_FILES="$(git diff --name-only | sort)"
if [[ "$(normalize_status "$ACTUAL_FILES")" != "$(normalize_status "$EXPECTED_FILES")" ]]; then
  echo "PHASE6_5_FIX_ERROR=UNEXPECTED_CHANGED_FILES"
  printf '%s\n' "$ACTUAL_FILES"
  exit 1
fi

git diff --check
npm --prefix frontend run build

rm -rf /opt/apps/tamiyouz-front/build/*
cp -a /var/www/TOS/frontend/dist/. /opt/apps/tamiyouz-front/build/
pm2 reload tamiyouz-frontend
sleep 2

DASHBOARD_HTTP="$(curl -ks -o /dev/null -w '%{http_code}' https://tos.tamiyouz.com/dashboard || true)"
TEAM_PERFORMANCE_HTTP="$(curl -ks -o /dev/null -w '%{http_code}' https://tos.tamiyouz.com/team-performance || true)"
TASKS_HTTP="$(curl -ks -o /dev/null -w '%{http_code}' https://tos.tamiyouz.com/tasks || true)"

if ! diff -qr /var/www/TOS/frontend/dist /opt/apps/tamiyouz-front/build >/dev/null; then
  echo "PHASE6_5_FIX_ERROR=DIST_DEPLOY_MISMATCH"
  exit 1
fi

EXPECTED_POST_STATUS=$(cat <<'EOF'
 M frontend/src/App.jsx
 M frontend/src/components/RamzyAssistant.jsx
 M frontend/src/components/performance/TeamPerformanceHelpCenter.jsx
 M frontend/src/pages/TeamPerformanceDashboard.jsx
EOF
)
ACTUAL_POST_STATUS="$(git status --short)"
if [[ "$(normalize_status "$ACTUAL_POST_STATUS")" != "$(normalize_status "$EXPECTED_POST_STATUS")" ]]; then
  echo "PHASE6_5_FIX_ERROR=UNEXPECTED_POST_STATUS"
  printf '%s\n' "$ACTUAL_POST_STATUS"
  exit 1
fi

echo "PHASE_6_5_CORRECTION=PASS"
echo "BASELINE_HEAD=$HEAD_NOW"
echo "DEEP_LINK_TARGETS=PASS"
echo "CLOSED_DISCLOSURE_OPEN=PASS"
echo "CROSS_PAGE_SCROLL_RETRY=PASS"
echo "ARABIC_HELP_LEAKAGE_FIX=PASS"
echo "RAMZY_DRAFT_PRESERVED=PASS"
echo "RAMZY_HELP_SUGGESTION_RECOVERABLE=PASS"
echo "RAMZY_AUTO_SEND=MUST_BE_NO"
echo "FRONTEND_BUILD=PASS"
echo "DEPLOY=PASS"
echo "DASHBOARD_HTTP=$DASHBOARD_HTTP"
echo "TEAM_PERFORMANCE_HTTP=$TEAM_PERFORMANCE_HTTP"
echo "TASKS_HTTP=$TASKS_HTTP"
echo "DIST_VS_DEPLOYED_IDENTICAL=YES"
echo "BACKEND_CHANGED=MUST_BE_NO"
echo "RBAC_CHANGED=MUST_BE_NO"
echo "PERFORMANCE_LOGIC_CHANGED=MUST_BE_NO"
echo "GIT_DIFF_CHECK=PASS"
echo "NO_COMMIT_OR_PUSH=YES"
echo "FILES_CHANGED:"
git status --short
