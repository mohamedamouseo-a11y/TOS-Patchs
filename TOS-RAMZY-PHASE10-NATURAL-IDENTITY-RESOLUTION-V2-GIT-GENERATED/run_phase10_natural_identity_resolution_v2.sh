#!/usr/bin/env bash
set -euo pipefail

TOS_ROOT="/var/www/TOS"
PATCH_DIR="$(cd "$(dirname "$0")" && pwd)"
RESILIENT_GENERATOR="$PATCH_DIR/03_phase10_resilient_identity_finalize.py"
BRIDGE_GENERATOR="$PATCH_DIR/02_phase10_team_performance_identity_bridge.py"
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

is_target_file() {
  local path="$1"
  for file in "${TARGET_FILES[@]}"; do
    [[ "$path" == "$file" ]] && return 0
  done
  return 1
}

known_partial_phase10_target() {
  local path="$1"
  case "$path" in
    backend/src/agency-operator/services/identityNameMatching.service.js)
      [[ -f "$path" ]] && grep -q 'RAMZY_IDENTITY_NAME_MATCHING_V1' "$path"
      ;;
    backend/src/agency-operator/services/entityResolution.service.js)
      grep -q 'RAMZY_ENTITY_RESOLUTION_V2' "$path" && grep -q 'scoreIdentityNameMatch' "$path"
      ;;
    backend/src/agency-operator/services/entityAlias.service.js)
      grep -q 'RAMZY_ALIAS_LEARNING_V2' "$path" && grep -q 'resolutionScore' "$path"
      ;;
    backend/src/agency-operator/services/ramzySystemIntelligence.service.js)
      grep -q 'aliasConfidence' "$path"
      ;;
    backend/src/agency-operator/prompts/ramzyPrompt.js)
      grep -q 'Phase 10:' "$path"
      ;;
    backend/src/agency-operator/services/ramzyTeamPerformance.service.js)
      grep -q 'Phase 10: Team Performance' "$path"
      ;;
    backend/src/agency-operator/tests/ramzyIdentityResolutionPhase10.test.js)
      grep -q 'Phase 10 resolves common Arabic-English' "$path"
      ;;
    backend/src/agency-operator/tests/ramzyTeamPerformanceIdentityPhase10.test.js)
      grep -q 'Phase 10 Team Performance uses shared multilingual identity resolution' "$path"
      ;;
    *) return 1 ;;
  esac
}

cd "$TOS_ROOT"

CURRENT_HEAD="$(git rev-parse HEAD)"
echo "CURRENT_TOS_HEAD=$CURRENT_HEAD"
if ! git merge-base --is-ancestor "$PHASE9_BASE" "$CURRENT_HEAD"; then
  fail "PHASE9_BASE_NOT_ANCESTOR_OF_CURRENT_HEAD"
fi

PRE_STATUS="$(git status --short)"

# A previous V2 attempt may have stopped after the first few Phase 10 files were
# written. Accept only target-file dirtiness that contains known Phase 10 markers.
# Never reset/clean TOS and never accept unrelated target-file edits silently.
while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  path="${line:3}"
  if is_target_file "$path"; then
    if ! known_partial_phase10_target "$path"; then
      fail "TARGET_FILE_DIRTY_NOT_RECOGNIZED_AS_PHASE10_PARTIAL:$path"
    fi
  fi
done <<< "$PRE_STATUS"

echo "PRE_STATE=ACCEPTED_CLEAN_OR_KNOWN_PHASE10_PARTIAL"

[[ -f "$RESILIENT_GENERATOR" ]] || fail "RESILIENT_GENERATOR_NOT_FOUND"
[[ -f "$BRIDGE_GENERATOR" ]] || fail "TEAM_PERFORMANCE_BRIDGE_GENERATOR_NOT_FOUND"

python3 "$RESILIENT_GENERATOR"
python3 "$BRIDGE_GENERATOR"
echo "PATCH_APPLY=PASS"

npm --prefix backend run test:ramzy
echo "BACKEND_TESTS=PASS"

git diff --check -- "${TARGET_FILES[@]}"
echo "GIT_DIFF_CHECK=PASS"

# Required Phase 10 markers and regression guards.
grep -q 'RAMZY_IDENTITY_NAME_MATCHING_V1' backend/src/agency-operator/services/identityNameMatching.service.js || fail "IDENTITY_MATCHER_MARKER_MISSING"
grep -q 'RAMZY_ENTITY_RESOLUTION_V2' backend/src/agency-operator/services/entityResolution.service.js || fail "ENTITY_RESOLUTION_V2_MISSING"
grep -q 'RAMZY_ALIAS_LEARNING_V2' backend/src/agency-operator/services/entityAlias.service.js || fail "ALIAS_V2_MISSING"
grep -q 'aliasConfidence' backend/src/agency-operator/services/ramzySystemIntelligence.service.js || fail "SYSTEM_INTELLIGENCE_ALIAS_CONFIDENCE_MISSING"
grep -q 'resolveEntityCandidates' backend/src/agency-operator/services/ramzyTeamPerformance.service.js || fail "TEAM_PERFORMANCE_SHARED_RESOLVER_MISSING"
grep -q 'already-authorized ACTIVE Team Performance dataset' backend/src/agency-operator/services/ramzyTeamPerformance.service.js || fail "TEAM_PERFORMANCE_RBAC_BOUNDARY_MARKER_MISSING"
grep -q 'Phase 10:' backend/src/agency-operator/prompts/ramzyPrompt.js || fail "RAMZY_PHASE10_PROMPT_RULE_MISSING"
if grep -q 'clean(row.name).startsWith(query)' backend/src/agency-operator/services/ramzyTeamPerformance.service.js; then
  fail "STALE_TEAM_PERFORMANCE_STARTSWITH_RESOLVER_PRESENT"
fi
if grep -q 'clean(row.name).includes(query)' backend/src/agency-operator/services/ramzyTeamPerformance.service.js; then
  fail "STALE_TEAM_PERFORMANCE_CONTAINS_RESOLVER_PRESENT"
fi
if grep -q 'aliasField: "aliasMatch"' backend/src/agency-operator/services/ramzySystemIntelligence.service.js; then
  fail "STALE_SYSTEM_INTELLIGENCE_ALIAS_MATCH_PRESENT"
fi

# Preserve unrelated dirty work exactly; Phase 10 may only add/change target files.
POST_STATUS="$(git status --short)"
filter_non_targets() {
  local status="$1"
  printf '%s\n' "$status" | while IFS= read -r line; do
    [[ -z "$line" ]] && continue
    local path="${line:3}"
    if ! is_target_file "$path"; then printf '%s\n' "$line"; fi
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

for url in "/health" "/dashboard" "/team-performance" "/tasks"; do
  code="$(curl -ksS -o /dev/null -w '%{http_code}' "https://tos.tamiyouz.com${url}")"
  echo "HTTP_${url//\//_}=$code"
  [[ "$code" == "200" ]] || fail "HTTP_SMOKE_FAILED:${url}:${code}"
done

echo "HTTP_SMOKE=PASS"
echo "NO_COMMIT_OR_PUSH=YES"
echo "PHASE10_V2=PASS"
echo "--- git status --short ---"
git status --short
