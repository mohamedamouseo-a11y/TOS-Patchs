#!/usr/bin/env bash
set -euo pipefail

TOS=/var/www/TOS
PATCH_DIR=/var/www/TOS-Patchs/TOS-RAMZY-PHASE9-FINAL-POLISH-E2E-V1-GIT-GENERATED
EXPECTED_HEAD=1642787ecdb41015be37329a72d6485b79961abb
DEPLOY_DIR=/opt/apps/tamiyouz-front/build

normalize() {
  printf '%s\n' "$1" | sed '/^[[:space:]]*$/d' | sort
}

cd "$TOS"
HEAD_NOW="$(git rev-parse HEAD)"
if [[ "$HEAD_NOW" != "$EXPECTED_HEAD" ]]; then
  echo "PHASE9_ERROR=HEAD_MISMATCH"
  echo "EXPECTED_HEAD=$EXPECTED_HEAD"
  echo "ACTUAL_HEAD=$HEAD_NOW"
  exit 1
fi

PRE_STATUS="$(git status --short)"
if [[ -n "$PRE_STATUS" ]]; then
  echo "PHASE9_ERROR=WORKTREE_NOT_CLEAN"
  printf '%s\n' "$PRE_STATUS"
  exit 1
fi

python3 "$PATCH_DIR/01_phase9_ramzy_final_polish_e2e.py"

# Source-level final polish assertions.
! grep -q '— ID: ${item.id}' backend/src/agency-operator/services/ramzySystemIntelligence.service.js
! grep -q 'حدد الـID الصحيح الأول' backend/src/agency-operator/services/ramzySystemIntelligence.service.js
grep -q 'بدون أي معرف تقني' backend/src/agency-operator/services/ramzySystemIntelligence.service.js
grep -q 'What are my top priorities today?' frontend/src/components/RamzyAssistant.jsx
grep -q 'Evidence & access' frontend/src/components/RamzyAssistant.jsx
grep -q 'evidenceScopeLabel' frontend/src/components/RamzyAssistant.jsx
grep -q 'RAMZY_PHASE9_FINAL_POLISH_EVIDENCE' frontend/src/index.css
! grep -q 'payload.assigneeName || payload.assigneeId' frontend/src/components/RamzyAssistant.jsx
! grep -q 'المهمة: {approval.targetId}' frontend/src/components/RamzyAssistant.jsx

EXPECTED_STATUS=$(cat <<'EOF'
 M backend/src/agency-operator/services/ramzySystemIntelligence.service.js
 M frontend/src/components/RamzyAssistant.jsx
 M frontend/src/index.css
?? backend/src/agency-operator/tests/ramzyFinalPolishE2E.static.test.js
EOF
)
POST_STATUS="$(git status --short)"
if [[ "$(normalize "$POST_STATUS")" != "$(normalize "$EXPECTED_STATUS")" ]]; then
  echo "PHASE9_ERROR=UNEXPECTED_CHANGED_FILES"
  printf '%s\n' "$POST_STATUS"
  exit 1
fi

git diff --check
node --check backend/src/agency-operator/services/ramzySystemIntelligence.service.js
node --check backend/src/agency-operator/tests/ramzyFinalPolishE2E.static.test.js

npm --prefix backend run test:ramzy
npm --prefix frontend run build

if [[ ! -d frontend/dist ]]; then
  echo "PHASE9_ERROR=FRONTEND_DIST_MISSING"
  exit 1
fi
if [[ ! -d "$DEPLOY_DIR" ]]; then
  echo "PHASE9_ERROR=DEPLOY_DIR_MISSING"
  exit 1
fi

rm -rf "$DEPLOY_DIR"/*
cp -a frontend/dist/. "$DEPLOY_DIR"/

if pm2 describe tamiyouz-system >/dev/null 2>&1; then
  BACKEND_PM2=tamiyouz-system
elif pm2 describe tamiyouz-backend >/dev/null 2>&1; then
  BACKEND_PM2=tamiyouz-backend
else
  echo "PHASE9_ERROR=BACKEND_PM2_NOT_FOUND"
  exit 1
fi

if ! pm2 describe tamiyouz-frontend >/dev/null 2>&1; then
  echo "PHASE9_ERROR=FRONTEND_PM2_NOT_FOUND"
  exit 1
fi

pm2 reload "$BACKEND_PM2"
pm2 reload tamiyouz-frontend
sleep 3

BACKEND_STATUS="$(pm2 jlist | node -e 'let d="";process.stdin.on("data",c=>d+=c);process.stdin.on("end",()=>{const a=JSON.parse(d);const n=process.argv[1];const p=a.find(x=>x.name===n);process.stdout.write(p?.pm2_env?.status||"missing")})' "$BACKEND_PM2")"
FRONTEND_STATUS="$(pm2 jlist | node -e 'let d="";process.stdin.on("data",c=>d+=c);process.stdin.on("end",()=>{const a=JSON.parse(d);const n=process.argv[1];const p=a.find(x=>x.name===n);process.stdout.write(p?.pm2_env?.status||"missing")})' tamiyouz-frontend)"
if [[ "$BACKEND_STATUS" != "online" || "$FRONTEND_STATUS" != "online" ]]; then
  echo "PHASE9_ERROR=PM2_NOT_ONLINE"
  echo "BACKEND_PM2=$BACKEND_PM2:$BACKEND_STATUS"
  echo "FRONTEND_PM2=tamiyouz-frontend:$FRONTEND_STATUS"
  exit 1
fi

HEALTH_HTTP="$(curl -ks -o /dev/null -w '%{http_code}' https://tos.tamiyouz.com/health || true)"
DASHBOARD_HTTP="$(curl -ks -o /dev/null -w '%{http_code}' https://tos.tamiyouz.com/dashboard || true)"
TEAM_PERFORMANCE_HTTP="$(curl -ks -o /dev/null -w '%{http_code}' https://tos.tamiyouz.com/team-performance || true)"
TASKS_HTTP="$(curl -ks -o /dev/null -w '%{http_code}' https://tos.tamiyouz.com/tasks || true)"
AGENT_STATUS_HTTP="$(curl -ks -o /tmp/phase9-agent-status.json -w '%{http_code}' https://tos.tamiyouz.com/api/agent/status || true)"
AGENT_AUDIT_HTTP="$(curl -ks -o /tmp/phase9-agent-audit.json -w '%{http_code}' https://tos.tamiyouz.com/api/agent/audit || true)"

for pair in "HEALTH_HTTP:$HEALTH_HTTP" "DASHBOARD_HTTP:$DASHBOARD_HTTP" "TEAM_PERFORMANCE_HTTP:$TEAM_PERFORMANCE_HTTP" "TASKS_HTTP:$TASKS_HTTP"; do
  NAME="${pair%%:*}"
  CODE="${pair##*:}"
  if [[ "$CODE" != "200" ]]; then
    echo "PHASE9_ERROR=${NAME}_${CODE}"
    exit 1
  fi
done

if [[ "$AGENT_STATUS_HTTP" != "401" && "$AGENT_STATUS_HTTP" != "403" ]]; then
  echo "PHASE9_ERROR=AGENT_STATUS_AUTH_BOUNDARY_$AGENT_STATUS_HTTP"
  exit 1
fi
if [[ "$AGENT_AUDIT_HTTP" != "401" && "$AGENT_AUDIT_HTTP" != "403" ]]; then
  echo "PHASE9_ERROR=AGENT_AUDIT_AUTH_BOUNDARY_$AGENT_AUDIT_HTTP"
  exit 1
fi

if ! diff -qr frontend/dist "$DEPLOY_DIR" >/tmp/phase9-dist-diff.txt; then
  echo "PHASE9_ERROR=DEPLOYED_DIST_MISMATCH"
  cat /tmp/phase9-dist-diff.txt
  exit 1
fi

# Ensure Phase 7-8 contracts survived Phase 9.
grep -q 'id: "get_tos_module_context"' backend/src/agency-operator/tools/createRamzyTools.js
grep -q 'await assertRamzyToolInvocationScope' backend/src/agency-operator/tools/createRamzyTools.js
grep -q 'RAMZY_EVIDENCE_V1' backend/src/agency-operator/services/ramzyEvidence.service.js
grep -q 'SERVER_SIDE_RBAC' backend/src/agency-operator/services/ramzyEvidence.service.js

echo "PHASE_9_PATCH_APPLY=PASS"
echo "BASELINE_HEAD=$HEAD_NOW"
echo "FINAL_ID_LEAK_GUARDS=PASS"
echo "AR_EN_POLISH=PASS"
echo "EVIDENCE_UI_POLISH=PASS"
echo "RBAC_CONTRACT=PASS"
echo "EVIDENCE_CONTRACT=PASS"
echo "BACKEND_TESTS=PASS"
echo "FRONTEND_BUILD=PASS"
echo "DEPLOY=PASS"
echo "BACKEND_PM2=$BACKEND_PM2:$BACKEND_STATUS"
echo "FRONTEND_PM2=tamiyouz-frontend:$FRONTEND_STATUS"
echo "HEALTH_HTTP=$HEALTH_HTTP"
echo "DASHBOARD_HTTP=$DASHBOARD_HTTP"
echo "TEAM_PERFORMANCE_HTTP=$TEAM_PERFORMANCE_HTTP"
echo "TASKS_HTTP=$TASKS_HTTP"
echo "AGENT_STATUS_UNAUTH_HTTP=$AGENT_STATUS_HTTP"
echo "AGENT_AUDIT_UNAUTH_HTTP=$AGENT_AUDIT_HTTP"
echo "AUTH_BOUNDARY_E2E=PASS"
echo "DEPLOYED_DIST_MATCH=PASS"
echo "GIT_DIFF_CHECK=PASS"
echo "NO_COMMIT_OR_PUSH=YES"
echo "FILES_CHANGED:"
git status --short
