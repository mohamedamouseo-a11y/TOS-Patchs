#!/usr/bin/env bash
set -euo pipefail

TOS_ROOT="/var/www/TOS"
PATCH_DIR="$(cd "$(dirname "$0")" && pwd)"
GENERATOR="$PATCH_DIR/01_ramzy_execution_control_v1.py"
BASELINE="f6b6f60b57d702e62ed488eca7265bfcde0ca601"
DOMAIN="https://tos.tamiyouz.com"

TARGETS=(
  "backend/src/services/permissions.service.js"
  "backend/src/agency-operator/services/agentSettings.service.js"
  "backend/src/agency-operator/services/ramzyExecutionControl.service.js"
  "backend/src/agency-operator/services/taskCommands.service.js"
  "backend/src/routes/agent.routes.js"
  "backend/src/agency-operator/tests/ramzyExecutionControlPhase16.test.js"
  "frontend/src/components/RamzySettingsAdmin.jsx"
  "frontend/src/components/RamzyAssistant.jsx"
  "frontend/src/components/ramzyExecutionControlV1.css"
  "frontend/src/pages/PermissionsPage.jsx"
)

fail() {
  echo "PASS/FAIL=FAIL"
  echo "RAMZY_EXECUTION_CONTROL_V1=FAIL"
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

echo "RUNNING=RAMZY_PHASE16_EXECUTION_CONTROL_V1"
cd "$TOS_ROOT"
CURRENT_HEAD="$(git rev-parse HEAD)"
echo "CURRENT_TOS_HEAD=$CURRENT_HEAD"
git merge-base --is-ancestor "$BASELINE" "$CURRENT_HEAD" || fail "BASELINE_NOT_ANCESTOR"

# The pushed Phase 16 / Admin Settings baseline must already be present.
grep -q 'RAMZY_VOICE_ACTION_PRODUCTION_HARDENING_V1' backend/src/agency-operator/services/ramzyProductionHardening.service.js || fail "PHASE16_HARDENING_MISSING"
grep -q 'requireRole("SUPER_ADMIN", "ADMIN")' backend/src/routes/agent.routes.js || fail "ADMIN_RAMZY_SETTINGS_REPAIR_MISSING"
grep -q 'ramzyFlagshipV2_3FinalLightLuxe.css' frontend/src/components/RamzyAssistant.jsx || fail "RAMZY_V2_3_BASELINE_MISSING"

# Do not overwrite local changes to files this patch owns. Unrelated work is allowed and preserved.
for target in "${TARGETS[@]}"; do
  if [[ -e "$target" ]]; then
    [[ -z "$(git status --short -- "$target")" ]] || fail "TARGET_NOT_CLEAN:$target"
  fi
done
[[ ! -e backend/src/agency-operator/services/ramzyExecutionControl.service.js ]] || fail "EXECUTION_SERVICE_ALREADY_EXISTS"
[[ ! -e backend/src/agency-operator/tests/ramzyExecutionControlPhase16.test.js ]] || fail "EXECUTION_TEST_ALREADY_EXISTS"
[[ ! -e frontend/src/components/ramzyExecutionControlV1.css ]] || fail "EXECUTION_CSS_ALREADY_EXISTS"

echo "PRE_STATE=PHASE16_PUSHED_RAMZY_EXECUTION_PERMISSION_NOT_INSTALLED"
UNRELATED_BEFORE="$(filtered_status)"
SCHEMA_PACKAGE_BEFORE="$(git diff --binary -- backend/prisma backend/package.json frontend/package.json | sha256sum | awk '{print $1}')"

[[ -f "$GENERATOR" ]] || fail "GENERATOR_NOT_FOUND"
python3 "$GENERATOR" "$TOS_ROOT"
echo "PATCH_APPLY=PASS"

# Source contracts.
grep -q 'key: "ramzy.execute_actions"' backend/src/services/permissions.service.js || fail "PERMISSION_DEFINITION_MISSING"
grep -q 'RAMZY_EXECUTION_CONTROL_V1' backend/src/agency-operator/services/ramzyExecutionControl.service.js || fail "EXECUTION_CONTROL_MARKER_MISSING"
grep -q 'assertRamzyActionExecutionAllowed(req.user, { settings })' backend/src/routes/agent.routes.js || fail "ROUTE_EXECUTION_GATE_MISSING"
grep -q 'assertRamzyActionExecutionAllowed(user, { settings })' backend/src/agency-operator/services/taskCommands.service.js || fail "TASK_EXECUTION_GATE_MISSING"
grep -q 'delete input.readOnlyMode' backend/src/routes/agent.routes.js || fail "ADMIN_EMERGENCY_LOCK_BOUNDARY_MISSING"
grep -q 'status.executionControl' frontend/src/components/RamzyAssistant.jsx || fail "RAMZY_EXECUTION_STATUS_MISSING"
grep -q 'تشغيل إجراءات رمزي' frontend/src/pages/PermissionsPage.jsx || fail "PERMISSIONS_UI_LABEL_MISSING"
grep -q 'RAMZY_EMERGENCY_LOCK' backend/src/agency-operator/services/agentSettings.service.js || fail "EMERGENCY_LOCK_ENV_ALIAS_MISSING"
grep -q 'assertRamzyToolInvocationScope' backend/src/agency-operator/tools/createRamzyTools.js || fail "PHASE8_RBAC_SCOPE_GUARD_LOST"
grep -q 'actionExecutionFromVoice: false' backend/src/agency-operator/services/ramzyVoice.service.js || fail "VOICE_PERMISSION_GUARD_LOST"
echo "CONTRACT_CHECKS=PASS"

git diff --check -- "${TARGETS[@]}"
echo "GIT_DIFF_CHECK=PASS"

node --test backend/src/agency-operator/tests/ramzyExecutionControlPhase16.test.js
echo "FOCUSED_EXECUTION_CONTROL_TEST=PASS"

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

UNRELATED_AFTER="$(filtered_status)"
SCHEMA_PACKAGE_AFTER="$(git diff --binary -- backend/prisma backend/package.json frontend/package.json | sha256sum | awk '{print $1}')"
[[ "$UNRELATED_BEFORE" == "$UNRELATED_AFTER" ]] || fail "UNRELATED_WORKTREE_CHANGED"
[[ "$SCHEMA_PACKAGE_BEFORE" == "$SCHEMA_PACKAGE_AFTER" ]] || fail "SCHEMA_OR_PACKAGE_CHANGED"
echo "NO_PRISMA_OR_PACKAGE_CHANGE=YES"
echo "UNRELATED_WORK_PRESERVED=YES"

# Sync the existing dynamic permission catalog. No schema migration is required.
# This transition intentionally unlocks the legacy global read-only flag and enables
# approval actions once; execution remains limited to ramzy.execute_actions + normal TOS RBAC.
node --input-type=module <<'NODE'
import { prisma } from "./backend/src/prisma.js";
import { ensurePermissionCatalog } from "./backend/src/services/permissions.service.js";
import { resolveRamzyExecutionControl } from "./backend/src/agency-operator/services/ramzyExecutionControl.service.js";

try {
  await ensurePermissionCatalog();
  const permission = await prisma.permission.findUnique({ where: { key: "ramzy.execute_actions" }, select: { id: true, key: true } });
  if (!permission) throw new Error("ramzy.execute_actions catalog row missing");

  const adminRole = await prisma.rolePermission.findUnique({
    where: { role_permissionId: { role: "ADMIN", permissionId: permission.id } },
    select: { enabled: true },
  });
  const managerRole = await prisma.rolePermission.findUnique({
    where: { role_permissionId: { role: "MANAGER", permissionId: permission.id } },
    select: { enabled: true },
  });
  const pmRole = await prisma.rolePermission.findUnique({
    where: { role_permissionId: { role: "PROJECT_MANAGER", permissionId: permission.id } },
    select: { enabled: true },
  });
  const memberRole = await prisma.rolePermission.findUnique({
    where: { role_permissionId: { role: "TEAM_MEMBER", permissionId: permission.id } },
    select: { enabled: true },
  });
  if (adminRole?.enabled !== true) throw new Error("ADMIN ramzy.execute_actions default is not enabled");
  if (managerRole?.enabled === true || pmRole?.enabled === true || memberRole?.enabled === true) {
    throw new Error("Non-admin execution permission unexpectedly enabled by default");
  }

  const current = await prisma.agentSettings.findUnique({ where: { id: "main" }, select: { id: true, readOnlyMode: true, approvalActionsEnabled: true } });
  if (current) {
    await prisma.agentSettings.update({
      where: { id: "main" },
      data: { readOnlyMode: false, approvalActionsEnabled: true },
    });
    console.log(`LEGACY_EXECUTION_STATE_BEFORE=readOnly:${Boolean(current.readOnlyMode)},approvals:${Boolean(current.approvalActionsEnabled)}`);
    console.log("EMERGENCY_LOCK_AFTER=OFF");
    console.log("APPROVAL_ACTIONS_AFTER=ON");
  } else {
    console.log("AGENT_SETTINGS_ROW=ENV_FALLBACK");
    console.log("EMERGENCY_LOCK_AFTER=OFF_BY_NEW_DEFAULT");
    console.log("APPROVAL_ACTIONS_AFTER=ENV_OR_DEFAULT_ON");
  }

  const admin = await prisma.user.findFirst({ where: { role: "ADMIN", status: "ACTIVE" }, select: { id: true, role: true } });
  if (!admin) throw new Error("No ACTIVE ADMIN available for execution-control verification");
  const control = await resolveRamzyExecutionControl(admin);
  console.log(`ADMIN_EXECUTION_PERMISSION=${control.permissionGranted ? "PASS" : "FAIL"}`);
  console.log(`ADMIN_EXECUTION_STATE=${control.state}`);
  console.log(`ADMIN_CAN_EXECUTE_AFTER_APPROVAL=${control.canExecute ? "YES" : "NO"}`);
  if (!control.permissionGranted || control.emergencyLocked || !control.approvalActionsEnabled || !control.canExecute) {
    throw new Error(`ADMIN execution control not enabled: ${control.state}`);
  }
  console.log("PERMISSION_CATALOG_SYNC=PASS");
  console.log("LEGACY_READ_ONLY_TO_EMERGENCY_LOCK_TRANSITION=PASS");
} finally {
  await prisma.$disconnect();
}
NODE

echo "DATABASE_EXECUTION_CONTROL_STATE=PASS"

# Deploy frontend build.
rm -rf /opt/apps/tamiyouz-front/build/*
cp -a frontend/dist/. /opt/apps/tamiyouz-front/build/
pm2 reload tamiyouz-frontend
sleep 3
pm2 describe tamiyouz-frontend | grep -qi online || fail "FRONTEND_PM2_NOT_ONLINE"
echo "FRONTEND_DEPLOY=PASS"

# Reload only the existing backend process.
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

# Preserve the already-established auth/CSRF boundary semantics.
GET_UNAUTH="$(public_code GET /api/agent/settings)"
PATCH_NO_CSRF="$(public_code PATCH /api/agent/settings)"
echo "RAMZY_SETTINGS_GET_UNAUTH_HTTP=$GET_UNAUTH"
echo "RAMZY_SETTINGS_PATCH_NO_CSRF_HTTP=$PATCH_NO_CSRF"
[[ "$GET_UNAUTH" == "401" ]] || fail "SETTINGS_GET_AUTH_BOUNDARY_FAILED:$GET_UNAUTH"
[[ "$PATCH_NO_CSRF" == "403" ]] || fail "SETTINGS_PATCH_CSRF_BOUNDARY_FAILED:$PATCH_NO_CSRF"
echo "AUTH_CSRF_BOUNDARY=PASS"

echo "RAMZY_EXECUTION_PERMISSION=ramzy.execute_actions"
echo "ADMIN_DEFAULT_EXECUTION=ENABLED"
echo "MANAGER_DEFAULT_EXECUTION=DISABLED"
echo "PROJECT_MANAGER_DEFAULT_EXECUTION=DISABLED"
echo "TEAM_MEMBER_DEFAULT_EXECUTION=DISABLED"
echo "EMERGENCY_LOCK=SUPER_ADMIN_ONLY"
echo "APPROVAL_CONFIRMATION=REQUIRED_BY_EXISTING_POLICY"
echo "TOS_RBAC_RECHECK_AT_EXECUTION=YES"
echo "VOICE_INDEPENDENT_PERMISSION=NO"
echo "NO_COMMIT_OR_PUSH=YES"
echo "RAMZY_EXECUTION_CONTROL_V1=PASS"
echo "PASS/FAIL=PASS"
echo "--- git status --short ---"
git status --short
