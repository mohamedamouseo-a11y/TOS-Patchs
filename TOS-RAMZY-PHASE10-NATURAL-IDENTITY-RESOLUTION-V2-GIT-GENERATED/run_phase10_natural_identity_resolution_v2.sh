#!/usr/bin/env bash
set -euo pipefail

TOS_ROOT="/var/www/TOS"
PATCH_DIR="$(cd "$(dirname "$0")" && pwd)"
V1_GENERATOR="$PATCH_DIR/../TOS-RAMZY-PHASE10-NATURAL-IDENTITY-RESOLUTION-V1-GIT-GENERATED/01_phase10_natural_identity_resolution.py"
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
  echo "PHASE10_V2=FAIL"
  echo "REASON=$1"
  exit 1
}

cd "$TOS_ROOT"

CURRENT_HEAD="$(git rev-parse HEAD)"
if ! git merge-base --is-ancestor "$PHASE9_BASE" "$CURRENT_HEAD"; then
  fail "PHASE9_BASE_NOT_ANCESTOR_OF_CURRENT_HEAD"
fi

PRE_STATUS="$(git status --short)"
for file in "${TARGET_FILES[@]}"; do
  if printf '%s\n' "$PRE_STATUS" | grep -Fq " $file"; then
    fail "TARGET_FILE_ALREADY_DIRTY:$file"
  fi
done

if [[ ! -f "$V1_GENERATOR" ]]; then
  fail "PHASE10_V1_GENERATOR_NOT_FOUND"
fi

python3 "$V1_GENERATOR"
python3 "$PATCH_DIR/02_phase10_team_performance_identity_bridge.py"

echo "PATCH_APPLY=PASS"

npm --prefix backend run test:ramzy
echo "BACKEND_TESTS=PASS"

git diff --check -- "${TARGET_FILES[@]}"
echo "GIT_DIFF_CHECK=PASS"

# Required Phase 10 markers.
grep -q 'RAMZY_IDENTITY_NAME_MATCHING_V1' backend/src/agency-operator/services/identityNameMatching.service.js || fail "IDENTITY_MATCHER_MARKER_MISSING"
grep -q 'resolveEntityCandidates' backend/src/agency-operator/services/ramzyTeamPerformance.service.js || fail "TEAM_PERFORMANCE_SHARED_RESOLVER_MISSING"
grep -q 'already-authorized ACTIVE Team Performance dataset' backend/src/agency-operator/services/ramzyTeamPerformance.service.js || fail "TEAM_PERFORMANCE_RBAC_BOUNDARY_MARKER_MISSING"
if grep -q 'clean(row.name).startsWith(query)' backend/src/agency-operator/services/ramzyTeamPerformance.service.js; then
  fail "STALE_TEAM_PERFORMANCE_STARTSWITH_RESOLVER_PRESENT"
fi
if grep -q 'clean(row.name).includes(query)' backend/src/agency-operator/services/ramzyTeamPerformance.service.js; then
  fail "STALE_TEAM_PERFORMANCE_CONTAINS_RESOLVER_PRESENT"
fi

# Preserve unrelated dirty work exactly; this phase must add only its target-file changes.
POST_STATUS="$(git status --short)"
filter_non_targets() {
  local status="$1"
  printf '%s\n' "$status" | while IFS= read -r line; do
    [[ -z "$line" ]] && continue
    local path="${line:3}"
    local is_target=0
    for file in "${TARGET_FILES[@]}"; do
      if [[ "$path" == "$file" ]]; then is_target=1; break; fi
    done
    if [[ $is_target -eq 0 ]]; then printf '%s\n' "$line"; fi
  done | sort
}

if [[ "$(filter_non_targets "$PRE_STATUS")" != "$(filter_non_targets "$POST_STATUS")" ]]; then
  fail "UNRELATED_WORKTREE_CHANGED"
fi

for file in "${TARGET_FILES[@]}"; do
  if ! printf '%s\n' "$POST_STATUS" | grep -Fq " $file"; then
    fail "EXPECTED_PHASE10_FILE_NOT_CHANGED:$file"
  fi
done

echo "EXPECTED_CHANGED_FILES=PASS"

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

echo "HEALTH_HTTP=$(curl -ksS -o /dev/null -w '%{http_code}' https://tos.tamiyouz.com/health)"
echo "DASHBOARD_HTTP=$(curl -ksS -o /dev/null -w '%{http_code}' https://tos.tamiyouz.com/dashboard)"
echo "TEAM_PERFORMANCE_HTTP=$(curl -ksS -o /dev/null -w '%{http_code}' https://tos.tamiyouz.com/team-performance)"
echo "TASKS_HTTP=$(curl -ksS -o /dev/null -w '%{http_code}' https://tos.tamiyouz.com/tasks)"

for url in "/health" "/dashboard" "/team-performance" "/tasks"; do
  code="$(curl -ksS -o /dev/null -w '%{http_code}' "https://tos.tamiyouz.com${url}")"
  [[ "$code" == "200" ]] || fail "HTTP_SMOKE_FAILED:${url}:${code}"
done

echo "HTTP_SMOKE=PASS"
echo "NO_COMMIT_OR_PUSH=YES"
echo "PHASE10_V2=PASS"
echo "--- git status --short ---"
git status --short
