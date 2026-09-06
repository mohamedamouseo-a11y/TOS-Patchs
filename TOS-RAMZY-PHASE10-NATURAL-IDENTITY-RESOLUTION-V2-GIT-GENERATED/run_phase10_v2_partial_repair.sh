#!/usr/bin/env bash
set -euo pipefail

TOS_ROOT="/var/www/TOS"
PATCH_DIR="$(cd "$(dirname "$0")" && pwd)"
REPAIR="$PATCH_DIR/04_phase10_partial_state_repair.py"
BRIDGE="$PATCH_DIR/02_phase10_team_performance_identity_bridge.py"
PHASE9_BASE="ee59c7c8e47aadc4c489b17948649208ce2b041c"

TARGET_FILES=(
  "backend/src/agency-operator/prompts/ramzyPrompt.js"
  "backend/src/agency-operator/services/entityAlias.service.js"
  "backend/src/agency-operator/services/entityResolution.service.js"
  "backend/src/agency-operator/services/identityNameMatching.service.js"
  "backend/src/agency-operator/services/ramzySystemIntelligence.service.js"
  "backend/src/agency-operator/services/ramzyTeamPerformance.service.js"
  "backend/src/agency-operator/tests/ramzyIdentityResolutionPhase10.test.js"
  "backend/src/agency-operator/tests/ramzyTeamPerformanceIdentityPhase10.test.js"
)

fail() {
  echo "PHASE10_V2_REPAIR=FAIL"
  echo "REASON=$1"
  exit 1
}

is_target() {
  local path="$1"
  for file in "${TARGET_FILES[@]}"; do
    [[ "$path" == "$file" ]] && return 0
  done
  return 1
}

cd "$TOS_ROOT"
CURRENT_HEAD="$(git rev-parse HEAD)"
echo "RUNNING=RAMZY_PHASE10_V2_PARTIAL_REPAIR"
echo "CURRENT_TOS_HEAD=$CURRENT_HEAD"

git merge-base --is-ancestor "$PHASE9_BASE" "$CURRENT_HEAD" || fail "PHASE9_BASE_NOT_ANCESTOR"

PRE_STATUS="$(git status --short)"

# This runner is recovery-only: prior failed attempts must have established the
# Phase 10 foundation. No reset/checkout/clean is ever performed on TOS.
[[ -f backend/src/agency-operator/services/identityNameMatching.service.js ]] || fail "IDENTITY_MATCHER_PARTIAL_MISSING"
grep -q 'RAMZY_IDENTITY_NAME_MATCHING_V1' backend/src/agency-operator/services/identityNameMatching.service.js || fail "IDENTITY_MATCHER_PARTIAL_INVALID"
grep -q 'RAMZY_ENTITY_RESOLUTION_V2' backend/src/agency-operator/services/entityResolution.service.js || fail "ENTITY_RESOLUTION_PARTIAL_MISSING"
grep -q 'RAMZY_ALIAS_LEARNING_V2' backend/src/agency-operator/services/entityAlias.service.js || fail "ENTITY_ALIAS_PARTIAL_MISSING"

echo "PRE_STATE=KNOWN_PHASE10_PARTIAL"

[[ -f "$REPAIR" ]] || fail "REPAIR_GENERATOR_NOT_FOUND"
[[ -f "$BRIDGE" ]] || fail "TEAM_PERFORMANCE_BRIDGE_NOT_FOUND"

python3 "$REPAIR"
python3 "$BRIDGE"
echo "PATCH_APPLY=PASS"

# Contract checks before running the full suite.
grep -q 'scoreIdentityNameMatch' backend/src/agency-operator/services/entityResolution.service.js || fail "IDENTITY_MATCHER_NOT_WIRED"
grep -q 'aliasConfidence' backend/src/agency-operator/services/ramzySystemIntelligence.service.js || fail "ALIAS_CONFIDENCE_NOT_WIRED"
! grep -q 'aliasField: "aliasMatch"' backend/src/agency-operator/services/ramzySystemIntelligence.service.js || fail "STALE_ALIAS_FIELD_PRESENT"
grep -q 'resolveEntityCandidates' backend/src/agency-operator/services/ramzyTeamPerformance.service.js || fail "TEAM_PERFORMANCE_SHARED_RESOLVER_MISSING"
grep -q 'already-authorized ACTIVE Team Performance dataset' backend/src/agency-operator/services/ramzyTeamPerformance.service.js || fail "TEAM_PERFORMANCE_RBAC_BOUNDARY_MISSING"
! grep -q 'clean(row.name).startsWith(query)' backend/src/agency-operator/services/ramzyTeamPerformance.service.js || fail "STALE_TEAM_PERFORMANCE_STARTSWITH_PRESENT"
! grep -q 'clean(row.name).includes(query)' backend/src/agency-operator/services/ramzyTeamPerformance.service.js || fail "STALE_TEAM_PERFORMANCE_CONTAINS_PRESENT"
grep -q 'Phase 10:' backend/src/agency-operator/prompts/ramzyPrompt.js || fail "PHASE10_PROMPT_MISSING"

echo "CONTRACT_CHECKS=PASS"

npm --prefix backend run test:ramzy
echo "BACKEND_TESTS=PASS"

git diff --check -- "${TARGET_FILES[@]}"
echo "GIT_DIFF_CHECK=PASS"

POST_STATUS="$(git status --short)"

# Preserve unrelated in-progress work exactly. We compare non-target status lines
# before/after and never reset them.
filter_non_targets() {
  local status="$1"
  printf '%s\n' "$status" | while IFS= read -r line; do
    [[ -z "$line" ]] && continue
    local path="${line:3}"
    if ! is_target "$path"; then printf '%s\n' "$line"; fi
  done | sort
}

[[ "$(filter_non_targets "$PRE_STATUS")" == "$(filter_non_targets "$POST_STATUS")" ]] || fail "UNRELATED_WORKTREE_CHANGED"
echo "UNRELATED_WORK_PRESERVED=YES"

BACKEND_PM2=""
if pm2 describe tamiyouz-system >/dev/null 2>&1; then
  BACKEND_PM2="tamiyouz-system"
elif pm2 describe tamiyouz-backend >/dev/null 2>&1; then
  BACKEND_PM2="tamiyouz-backend"
else
  fail "BACKEND_PM2_NOT_FOUND"
fi

pm2 reload "$BACKEND_PM2"
sleep 2
pm2 describe "$BACKEND_PM2" | grep -qi 'online' || fail "BACKEND_PM2_NOT_ONLINE"
echo "BACKEND_RELOAD=PASS"

for url in "/health" "/dashboard" "/team-performance" "/tasks"; do
  code="$(curl -ksS -o /dev/null -w '%{http_code}' "https://tos.tamiyouz.com${url}")"
  echo "HTTP_${url//\//_}=$code"
  [[ "$code" == "200" ]] || fail "HTTP_SMOKE_FAILED:${url}:${code}"
done

echo "HTTP_SMOKE=PASS"
echo "NO_COMMIT_OR_PUSH=YES"
echo "PHASE10_V2_REPAIR=PASS"
echo "--- git status --short ---"
git status --short
