#!/usr/bin/env bash
set -euo pipefail

TOS=/var/www/TOS
PATCH_DIR=/var/www/TOS-Patchs/TOS-RAMZY-PHASE10-NATURAL-IDENTITY-RESOLUTION-V1-GIT-GENERATED
EXPECTED_HEAD=ee59c7c8e47aadc4c489b17948649208ce2b041c

normalize() {
  printf '%s\n' "$1" | sed '/^[[:space:]]*$/d' | sort
}

cd "$TOS"
HEAD_NOW="$(git rev-parse HEAD)"
if [[ "$HEAD_NOW" != "$EXPECTED_HEAD" ]]; then
  echo "PHASE10_ERROR=HEAD_MISMATCH"
  echo "EXPECTED_HEAD=$EXPECTED_HEAD"
  echo "ACTUAL_HEAD=$HEAD_NOW"
  exit 1
fi

PRE_STATUS="$(git status --short)"
if [[ -n "$PRE_STATUS" ]]; then
  echo "PHASE10_ERROR=WORKTREE_NOT_CLEAN"
  printf '%s\n' "$PRE_STATUS"
  exit 1
fi

python3 "$PATCH_DIR/01_phase10_natural_identity_resolution.py"

grep -q 'RAMZY_IDENTITY_NAME_MATCHING_V1' backend/src/agency-operator/services/identityNameMatching.service.js
grep -q 'COMPACT_NAME' backend/src/agency-operator/services/identityNameMatching.service.js
grep -q 'TOKEN_COVERAGE' backend/src/agency-operator/services/identityNameMatching.service.js
grep -q 'RAMZY_ENTITY_RESOLUTION_V2' backend/src/agency-operator/services/entityResolution.service.js
grep -q 'spellingAwareLookup: true' backend/src/agency-operator/services/entityAlias.service.js
grep -q 'fuzzyAliasAutoResolve: false' backend/src/agency-operator/services/entityAlias.service.js
grep -q 'aliasConfidence' backend/src/agency-operator/services/ramzySystemIntelligence.service.js
grep -q 'Speech-to-Text' backend/src/agency-operator/prompts/ramzyPrompt.js
grep -q 'يوسف' backend/src/agency-operator/tests/ramzyIdentityResolutionPhase10.test.js
grep -q 'Abdelrahman' backend/src/agency-operator/tests/ramzyIdentityResolutionPhase10.test.js

EXPECTED_STATUS=$(cat <<'EOF'
 M backend/src/agency-operator/prompts/ramzyPrompt.js
 M backend/src/agency-operator/services/entityAlias.service.js
 M backend/src/agency-operator/services/entityResolution.service.js
 M backend/src/agency-operator/services/ramzySystemIntelligence.service.js
?? backend/src/agency-operator/services/identityNameMatching.service.js
?? backend/src/agency-operator/tests/ramzyIdentityResolutionPhase10.test.js
EOF
)
POST_STATUS="$(git status --short)"
if [[ "$(normalize "$POST_STATUS")" != "$(normalize "$EXPECTED_STATUS")" ]]; then
  echo "PHASE10_ERROR=UNEXPECTED_CHANGED_FILES"
  printf '%s\n' "$POST_STATUS"
  exit 1
fi

if git status --short | grep -Eq '(^| )(backend/prisma/|package(-lock)?\.json|backend/package(-lock)?\.json|frontend/package(-lock)?\.json)'; then
  echo "PHASE10_ERROR=FORBIDDEN_SCHEMA_OR_PACKAGE_CHANGE"
  exit 1
fi

git diff --check

node --check backend/src/agency-operator/services/identityNameMatching.service.js
node --check backend/src/agency-operator/services/entityResolution.service.js
node --check backend/src/agency-operator/services/entityAlias.service.js
node --check backend/src/agency-operator/services/ramzySystemIntelligence.service.js
node --check backend/src/agency-operator/prompts/ramzyPrompt.js
node --check backend/src/agency-operator/tests/ramzyIdentityResolutionPhase10.test.js

node --test backend/src/agency-operator/tests/ramzyIdentityResolutionPhase10.test.js
npm --prefix backend run test:ramzy

BACKEND_PM2=""
if pm2 describe tamiyouz-system >/dev/null 2>&1; then
  BACKEND_PM2=tamiyouz-system
elif pm2 describe tamiyouz-backend >/dev/null 2>&1; then
  BACKEND_PM2=tamiyouz-backend
else
  echo "PHASE10_ERROR=BACKEND_PM2_NOT_FOUND"
  exit 1
fi

pm2 reload "$BACKEND_PM2"
sleep 2

HEALTH_HTTP="$(curl -ks -o /dev/null -w '%{http_code}' https://tos.tamiyouz.com/health || true)"
DASHBOARD_HTTP="$(curl -ks -o /dev/null -w '%{http_code}' https://tos.tamiyouz.com/dashboard || true)"
TEAM_PERFORMANCE_HTTP="$(curl -ks -o /dev/null -w '%{http_code}' https://tos.tamiyouz.com/team-performance || true)"
TASKS_HTTP="$(curl -ks -o /dev/null -w '%{http_code}' https://tos.tamiyouz.com/tasks || true)"

if [[ "$HEALTH_HTTP" != "200" || "$DASHBOARD_HTTP" != "200" || "$TEAM_PERFORMANCE_HTTP" != "200" || "$TASKS_HTTP" != "200" ]]; then
  echo "PHASE10_ERROR=SMOKE_FAILED"
  echo "HEALTH_HTTP=$HEALTH_HTTP"
  echo "DASHBOARD_HTTP=$DASHBOARD_HTTP"
  echo "TEAM_PERFORMANCE_HTTP=$TEAM_PERFORMANCE_HTTP"
  echo "TASKS_HTTP=$TASKS_HTTP"
  exit 1
fi

FINAL_STATUS="$(git status --short)"
if [[ "$(normalize "$FINAL_STATUS")" != "$(normalize "$EXPECTED_STATUS")" ]]; then
  echo "PHASE10_ERROR=UNEXPECTED_FINAL_STATUS"
  printf '%s\n' "$FINAL_STATUS"
  exit 1
fi

echo "PHASE_10_PATCH_APPLY=PASS"
echo "BASELINE_HEAD=$HEAD_NOW"
echo "IDENTITY_NAME_MATCHING=PASS"
echo "AR_EN_TRANSLITERATION=PASS"
echo "COMPOUND_NAME_SPACING=PASS"
echo "MULTIWORD_FALSE_MATCH_GUARD=PASS"
echo "SPELLING_AWARE_ALIASES=PASS"
echo "FUZZY_ALIAS_AUTO_RESOLVE=NO"
echo "RBAC_SCOPE_PRESERVED=PASS"
echo "PROVIDER_IDENTITY_OVERRIDE=NO"
echo "RAMZY_TESTS=PASS"
echo "BACKEND_RELOAD=PASS"
echo "BACKEND_PM2=$BACKEND_PM2"
echo "HEALTH_HTTP=$HEALTH_HTTP"
echo "DASHBOARD_HTTP=$DASHBOARD_HTTP"
echo "TEAM_PERFORMANCE_HTTP=$TEAM_PERFORMANCE_HTTP"
echo "TASKS_HTTP=$TASKS_HTTP"
echo "GIT_DIFF_CHECK=PASS"
echo "NO_COMMIT_OR_PUSH=YES"
echo "FILES_CHANGED:"
git status --short
