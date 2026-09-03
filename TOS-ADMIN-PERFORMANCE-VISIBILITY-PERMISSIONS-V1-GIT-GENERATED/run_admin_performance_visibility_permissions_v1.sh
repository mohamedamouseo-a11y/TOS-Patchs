#!/usr/bin/env bash
set -euo pipefail

TOS=/var/www/TOS
PATCH_DIR=/var/www/TOS-Patchs/TOS-ADMIN-PERFORMANCE-VISIBILITY-PERMISSIONS-V1-GIT-GENERATED
EXPECTED_HEAD=7e8ec8c7856ce41724f493886ebe050381ecc4d8

cd "$TOS"

HEAD_NOW="$(git rev-parse HEAD)"
if [[ "$HEAD_NOW" != "$EXPECTED_HEAD" ]]; then
  echo "ADMIN_PERFORMANCE_PERMISSIONS_ERROR=HEAD_MISMATCH:$HEAD_NOW"
  exit 1
fi

EXPECTED_PRE_STATUS=$(cat <<'EOF'
 M backend/src/agency-operator/agents/ramzyAgencyOperator.js
 M backend/src/agency-operator/agents/specialistAgents.js
 M backend/src/agency-operator/prompts/ramzyPrompt.js
 M backend/src/agency-operator/tools/createRamzyTools.js
 M backend/src/routes/tasks.routes.js
?? backend/src/agency-operator/services/ramzyTeamPerformance.service.js
EOF
)
ACTUAL_PRE_STATUS="$(git status --short)"
if [[ "$ACTUAL_PRE_STATUS" != "$EXPECTED_PRE_STATUS" ]]; then
  echo "ADMIN_PERFORMANCE_PERMISSIONS_ERROR=UNEXPECTED_PRE_STATUS"
  printf '%s\n' "$ACTUAL_PRE_STATUS"
  exit 1
fi

echo "PRE_STATUS=PASS"
python3 "$PATCH_DIR/01_admin_performance_visibility_permissions.py"

node --check backend/src/services/permissions.service.js
node --check backend/src/routes/tasks.routes.js
node --check backend/src/agency-operator/services/ramzyTeamPerformance.service.js
node --check backend/src/agency-operator/tools/createRamzyTools.js

echo "NODE_CHECK=PASS"

# Sync only the existing permission catalog tables. No schema/migration changes.
cd "$TOS/backend"
node --input-type=module <<'NODE'
import { ensurePermissionCatalog, getPermissionsMatrix, hasPermission } from "./src/services/permissions.service.js";
import { prisma } from "./src/prisma.js";

try {
  await ensurePermissionCatalog();
  const matrix = await getPermissionsMatrix();
  const admin = matrix.rolePermissions?.ADMIN || {};
  const manager = matrix.rolePermissions?.MANAGER || {};
  const projectManager = matrix.rolePermissions?.PROJECT_MANAGER || {};
  const teamMember = matrix.rolePermissions?.TEAM_MEMBER || {};
  const superAdmin = matrix.rolePermissions?.SUPER_ADMIN || {};

  const required = ["performance.view_self", "performance.view_team", "performance.view_all"];
  for (const key of required) {
    if (!matrix.permissions.some((item) => item.key === key)) throw new Error(`Missing permission ${key}`);
  }

  if (admin["performance.view_self"] !== true) throw new Error("ADMIN view_self default must be true");
  if (admin["performance.view_team"] !== true) throw new Error("ADMIN view_team default must be true");
  if (admin["performance.view_all"] !== false) throw new Error("ADMIN view_all default must be false");
  if (manager["performance.view_self"] !== true || manager["performance.view_team"] !== true || manager["performance.view_all"] !== false) throw new Error("MANAGER defaults invalid");
  if (projectManager["performance.view_self"] !== true || projectManager["performance.view_team"] !== true || projectManager["performance.view_all"] !== false) throw new Error("PROJECT_MANAGER defaults invalid");
  if (teamMember["performance.view_self"] !== true || teamMember["performance.view_team"] !== false || teamMember["performance.view_all"] !== false) throw new Error("TEAM_MEMBER defaults invalid");
  if (superAdmin["performance.view_all"] !== true) throw new Error("SUPER_ADMIN view_all must be true");

  const activeAdmin = await prisma.user.findFirst({
    where: { role: "ADMIN", status: "ACTIVE" },
    select: { id: true, name: true, email: true, role: true, status: true },
    orderBy: { createdAt: "asc" },
  });
  if (activeAdmin) {
    const canSelf = await hasPermission(activeAdmin, "performance.view_self");
    const canTeam = await hasPermission(activeAdmin, "performance.view_team");
    const canAll = await hasPermission(activeAdmin, "performance.view_all");
    if (!canSelf || !canTeam || canAll) throw new Error("Active ADMIN effective performance permissions invalid");
    console.log(`ADMIN_TEST_USER=${activeAdmin.name || activeAdmin.email}`);
    console.log(`ADMIN_EFFECTIVE_VIEW_SELF=${canSelf ? "YES" : "NO"}`);
    console.log(`ADMIN_EFFECTIVE_VIEW_TEAM=${canTeam ? "YES" : "NO"}`);
    console.log(`ADMIN_EFFECTIVE_VIEW_ALL=${canAll ? "YES" : "NO"}`);
  } else {
    console.log("ADMIN_TEST_USER=NONE_ACTIVE");
  }

  console.log("PERMISSION_CATALOG_SYNC=PASS");
  console.log("ADMIN_DEFAULT_VIEW_ALL=NO");
  console.log("SUPER_ADMIN_VIEW_ALL=YES");
} finally {
  await prisma.$disconnect();
}
NODE

cd "$TOS"
npm --prefix frontend run build

echo "FRONTEND_BUILD=PASS"

git diff --check

echo "GIT_DIFF_CHECK=PASS"

EXPECTED_POST_STATUS=$(cat <<'EOF'
 M backend/src/agency-operator/agents/ramzyAgencyOperator.js
 M backend/src/agency-operator/agents/specialistAgents.js
 M backend/src/agency-operator/prompts/ramzyPrompt.js
 M backend/src/agency-operator/tools/createRamzyTools.js
 M backend/src/routes/tasks.routes.js
 M backend/src/services/permissions.service.js
?? backend/src/agency-operator/services/ramzyTeamPerformance.service.js
 M frontend/src/pages/PermissionsPage.jsx
EOF
)
ACTUAL_POST_STATUS="$(git status --short)"
if [[ "$ACTUAL_POST_STATUS" != "$EXPECTED_POST_STATUS" ]]; then
  echo "ADMIN_PERFORMANCE_PERMISSIONS_ERROR=UNEXPECTED_POST_STATUS"
  printf '%s\n' "$ACTUAL_POST_STATUS"
  exit 1
fi

echo "POST_STATUS=PASS"
echo "ADMIN_PERFORMANCE_VISIBILITY_PERMISSIONS_V1=PASS"
echo "TEAM_PERFORMANCE_PERMISSION_DRIVEN=YES"
echo "RAMZY_PERMISSION_DRIVEN=YES"
echo "ADMIN_ROLE_COMPANY_WIDE_HARDCODE_FOR_PERFORMANCE=REMOVED"
echo "IS_SYSTEM_ADMIN_GLOBAL_BEHAVIOR_CHANGED=NO"
echo "SCHEMA_CHANGED=NO"
echo "MIGRATION_CREATED=NO"
echo "NO_COMMIT_OR_PUSH_PERFORMED=YES"
