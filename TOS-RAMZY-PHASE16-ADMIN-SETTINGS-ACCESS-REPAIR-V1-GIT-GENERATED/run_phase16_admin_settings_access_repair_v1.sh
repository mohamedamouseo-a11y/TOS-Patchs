#!/usr/bin/env bash
set -euo pipefail

TOS_ROOT="/var/www/TOS"
PATCH_DIR="$(cd "$(dirname "$0")" && pwd)"
GENERATOR="$PATCH_DIR/01_phase16_admin_settings_access_repair.py"
BASELINE="f7678ab1ab7b5b0261a9e3a3a78c43533999b66d"
DOMAIN="https://tos.tamiyouz.com"

TARGETS=(
  "backend/src/routes/agent.routes.js"
  "frontend/src/pages/SettingsPage.jsx"
  "frontend/src/components/RamzySettingsAdmin.jsx"
  "backend/src/agency-operator/tests/ramzyAdminSettingsAccessPhase16Repair.test.js"
)

fail() {
  echo "PASS/FAIL=FAIL"
  echo "RAMZY_ADMIN_SETTINGS_ACCESS=FAIL"
  echo "REASON=$1"
  exit 1
}

filtered_status() {
  python3 - "${TARGETS[@]}" <<'PY'
import subprocess, sys
excluded = set(sys.argv[1:])
raw = subprocess.check_output(["git", "status", "--short"], text=True)
for line in raw.splitlines():
    path = line[3:]
    if " -> " in path:
        path = path.split(" -> ", 1)[1]
    if path not in excluded:
        print(line)
PY
}

public_code() {
  local method="${1:-GET}"
  local path="${2:-/}"
  if [[ "$method" == "PATCH" ]]; then
    curl -ksS -X PATCH -H 'Content-Type: application/json' -d '{}' -o /dev/null -w '%{http_code}' "$DOMAIN$path" || true
  else
    curl -ksS -o /dev/null -w '%{http_code}' "$DOMAIN$path" || true
  fi
}

echo "RUNNING=RAMZY_PHASE16_ADMIN_SETTINGS_ACCESS_REPAIR_V1"
cd "$TOS_ROOT"
CURRENT_HEAD="$(git rev-parse HEAD)"
echo "CURRENT_TOS_HEAD=$CURRENT_HEAD"
git merge-base --is-ancestor "$BASELINE" "$CURRENT_HEAD" || fail "PHASE15_BASELINE_NOT_ANCESTOR"

# This repair is intentionally applied on top of the already-passing local Phase 16 work.
[[ -f backend/src/agency-operator/services/ramzyProductionHardening.service.js ]] || fail "PHASE16_LOCAL_HARDENING_NOT_APPLIED"
grep -q 'RAMZY_VOICE_ACTION_PRODUCTION_HARDENING_V1' backend/src/agency-operator/services/ramzyProductionHardening.service.js || fail "PHASE16_HARDENING_MARKER_MISSING"
grep -q 'publicRamzyApprovalView' backend/src/routes/agent.routes.js || fail "PHASE16_PUBLIC_APPROVAL_BOUNDARY_NOT_PRESENT"

[[ -z "$(git status --short -- frontend/src/pages/SettingsPage.jsx frontend/src/components/RamzySettingsAdmin.jsx)" ]] || fail "ADMIN_SETTINGS_FRONTEND_TARGETS_NOT_CLEAN"
[[ ! -e backend/src/agency-operator/tests/ramzyAdminSettingsAccessPhase16Repair.test.js ]] || fail "ADMIN_SETTINGS_TEST_ALREADY_EXISTS"
grep -q 'router.get("/settings", requireRole("SUPER_ADMIN")' backend/src/routes/agent.routes.js || fail "EXPECTED_SUPER_ADMIN_GET_GUARD_NOT_FOUND"
grep -q 'router.patch("/settings", requireRole("SUPER_ADMIN")' backend/src/routes/agent.routes.js || fail "EXPECTED_SUPER_ADMIN_PATCH_GUARD_NOT_FOUND"
grep -q 'ADMIN_SETTINGS_SECTION_KEYS = new Set(\["identity", "operations"\])' frontend/src/pages/SettingsPage.jsx || fail "EXPECTED_ADMIN_SECTION_BASELINE_NOT_FOUND"
grep -q 'if (user?.role !== "SUPER_ADMIN") return null;' frontend/src/components/RamzySettingsAdmin.jsx || fail "EXPECTED_RAMZY_COMPONENT_GUARD_NOT_FOUND"
echo "PRE_STATE=PHASE16_LOCAL_PASS_ADMIN_SETTINGS_LOCKED"

UNRELATED_STATUS_BEFORE="$(filtered_status)"
PHASE16_OTHER_DIFF_BEFORE="$(git diff --binary -- backend/src/agency-operator/prompts/ramzyPrompt.js backend/src/agency-operator/services/ramzyRuntime.service.js backend/src/agency-operator/services/taskCommands.service.js backend/src/agency-operator/services/ramzyProductionHardening.service.js backend/src/agency-operator/tests/ramzyVoiceActionProductionHardeningPhase16.test.js | sha256sum | awk '{print $1}')"
SCHEMA_PACKAGE_DIFF_BEFORE="$(git diff --binary -- backend/prisma backend/package.json frontend/package.json | sha256sum | awk '{print $1}')"

[[ -f "$GENERATOR" ]] || fail "GENERATOR_NOT_FOUND"
python3 "$GENERATOR" "$TOS_ROOT"
echo "PATCH_APPLY=PASS"

grep -q 'router.get("/settings", requireRole("SUPER_ADMIN", "ADMIN")' backend/src/routes/agent.routes.js || fail "ADMIN_SETTINGS_GET_NOT_OPEN"
grep -q 'router.patch("/settings", requireRole("SUPER_ADMIN", "ADMIN")' backend/src/routes/agent.routes.js || fail "ADMIN_SETTINGS_PATCH_NOT_OPEN"
grep -q 'router.get("/audit", requireRole("SUPER_ADMIN")' backend/src/routes/agent.routes.js || fail "AUDIT_BOUNDARY_WEAKENED"
grep -q 'ADMIN_SETTINGS_SECTION_KEYS = new Set(\["identity", "operations", "ramzy"\])' frontend/src/pages/SettingsPage.jsx || fail "ADMIN_RAMZY_NAV_NOT_OPEN"
grep -q '\["SUPER_ADMIN", "ADMIN"\].includes(user?.role)' frontend/src/components/RamzySettingsAdmin.jsx || fail "ADMIN_RAMZY_COMPONENT_NOT_OPEN"
grep -q 'user?.role === "SUPER_ADMIN" ? api.agent.audit' frontend/src/components/RamzySettingsAdmin.jsx || fail "AUDIT_UI_BOUNDARY_NOT_PRESERVED"
grep -q 'RAMZY_VOICE_ACTION_PRODUCTION_HARDENING_V1' backend/src/agency-operator/services/ramzyProductionHardening.service.js || fail "PHASE16_HARDENING_LOST"
grep -q 'assertRamzyToolInvocationScope' backend/src/agency-operator/tools/createRamzyTools.js || fail "RAMZY_RBAC_SCOPE_GUARD_LOST"
echo "CONTRACT_CHECKS=PASS"

git diff --check -- "${TARGETS[@]}"
echo "GIT_DIFF_CHECK=PASS"

node --test backend/src/agency-operator/tests/ramzyAdminSettingsAccessPhase16Repair.test.js
echo "ADMIN_SETTINGS_ACCESS_TEST=PASS"

TEST_LOG="$(mktemp)"
trap 'rm -f "$TEST_LOG"' EXIT
npm --prefix backend run test:ramzy 2>&1 | tee "$TEST_LOG"
TEST_COUNT="$(awk '/^# tests /{print $3}' "$TEST_LOG" | tail -1)"
PASS_COUNT="$(awk '/^# pass /{print $3}' "$TEST_LOG" | tail -1)"
if [[ -n "$TEST_COUNT" && -n "$PASS_COUNT" ]]; then
  [[ "$TEST_COUNT" == "$PASS_COUNT" ]] || fail "BACKEND_TEST_COUNT_MISMATCH:${PASS_COUNT}/${TEST_COUNT}"
  echo "BACKEND_TESTS=PASS (${PASS_COUNT}/${TEST_COUNT} tests passed)"
else
  echo "BACKEND_TESTS=PASS"
fi

npm --prefix frontend run build
echo "FRONTEND_BUILD=PASS"

UNRELATED_STATUS_AFTER="$(filtered_status)"
PHASE16_OTHER_DIFF_AFTER="$(git diff --binary -- backend/src/agency-operator/prompts/ramzyPrompt.js backend/src/agency-operator/services/ramzyRuntime.service.js backend/src/agency-operator/services/taskCommands.service.js backend/src/agency-operator/services/ramzyProductionHardening.service.js backend/src/agency-operator/tests/ramzyVoiceActionProductionHardeningPhase16.test.js | sha256sum | awk '{print $1}')"
SCHEMA_PACKAGE_DIFF_AFTER="$(git diff --binary -- backend/prisma backend/package.json frontend/package.json | sha256sum | awk '{print $1}')"
[[ "$UNRELATED_STATUS_BEFORE" == "$UNRELATED_STATUS_AFTER" ]] || fail "UNRELATED_WORKTREE_CHANGED"
[[ "$PHASE16_OTHER_DIFF_BEFORE" == "$PHASE16_OTHER_DIFF_AFTER" ]] || fail "PHASE16_OTHER_FILES_CHANGED"
[[ "$SCHEMA_PACKAGE_DIFF_BEFORE" == "$SCHEMA_PACKAGE_DIFF_AFTER" ]] || fail "SCHEMA_OR_PACKAGE_CHANGED"
echo "PHASE16_LOCAL_WORK_PRESERVED=YES"
echo "UNRELATED_WORK_PRESERVED=YES"

rm -rf /opt/apps/tamiyouz-front/build/*
cp -a frontend/dist/. /opt/apps/tamiyouz-front/build/
pm2 reload tamiyouz-frontend
sleep 3
pm2 describe tamiyouz-frontend | grep -qi online || fail "FRONTEND_PM2_NOT_ONLINE"
echo "FRONTEND_DEPLOY=PASS"

BACKEND_PM2=""
if pm2 describe tamiyouz-system >/dev/null 2>&1; then
  BACKEND_PM2="tamiyouz-system"
elif pm2 describe tamiyouz-backend >/dev/null 2>&1; then
  BACKEND_PM2="tamiyouz-backend"
else
  fail "BACKEND_PM2_NOT_FOUND"
fi
pm2 reload "$BACKEND_PM2"
sleep 4
pm2 describe "$BACKEND_PM2" | grep -qi online || fail "BACKEND_PM2_NOT_ONLINE"
echo "BACKEND_RELOAD=PASS"

for url in /health /dashboard /team-performance /tasks; do
  code="$(curl -ksS -o /dev/null -w '%{http_code}' "$DOMAIN$url" || true)"
  echo "HTTP_${url//\//_}=$code"
  [[ "$code" == "200" ]] || fail "HTTP_SMOKE_FAILED:${url}:${code}"
done
echo "HTTP_SMOKE=PASS"

SETTINGS_GET_UNAUTH="$(public_code GET /api/agent/settings)"
SETTINGS_PATCH_UNAUTH="$(public_code PATCH /api/agent/settings)"
echo "RAMZY_SETTINGS_GET_UNAUTH_HTTP=$SETTINGS_GET_UNAUTH"
echo "RAMZY_SETTINGS_PATCH_UNAUTH_HTTP=$SETTINGS_PATCH_UNAUTH"
[[ "$SETTINGS_GET_UNAUTH" == "401" ]] || fail "SETTINGS_GET_AUTH_BOUNDARY_FAILED:$SETTINGS_GET_UNAUTH"
[[ "$SETTINGS_PATCH_UNAUTH" == "401" ]] || fail "SETTINGS_PATCH_AUTH_BOUNDARY_FAILED:$SETTINGS_PATCH_UNAUTH"
echo "AUTH_BOUNDARY_E2E=PASS"

echo "ADMIN_RAMZY_SETTINGS_ACCESS=PASS"
echo "SUPER_ADMIN_RAMZY_SETTINGS_ACCESS=PASS"
echo "SUPER_ADMIN_AUDIT_ONLY=PRESERVED"
echo "RAMZY_EXECUTION_RBAC=UNCHANGED"
echo "NO_COMMIT_OR_PUSH=YES"
echo "RAMZY_ADMIN_SETTINGS_ACCESS=PASS"
echo "PASS/FAIL=PASS"
echo "--- git status --short ---"
git status --short
