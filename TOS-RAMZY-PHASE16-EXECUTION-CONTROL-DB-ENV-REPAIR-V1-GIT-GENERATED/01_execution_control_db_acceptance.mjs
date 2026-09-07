import path from "node:path";
import { pathToFileURL } from "node:url";

const backendRoot = process.env.TOS_BACKEND_ROOT || "/var/www/TOS/backend";
const importFromBackend = (relative) => import(pathToFileURL(path.join(backendRoot, relative)).href);

const { prisma } = await importFromBackend("src/prisma.js");
const { ensurePermissionCatalog } = await importFromBackend("src/services/permissions.service.js");
const { resolveRamzyExecutionControl } = await importFromBackend("src/agency-operator/services/ramzyExecutionControl.service.js");

try {
  await ensurePermissionCatalog();

  const permission = await prisma.permission.findUnique({
    where: { key: "ramzy.execute_actions" },
    select: { id: true, key: true },
  });
  if (!permission) throw new Error("ramzy.execute_actions catalog row missing");

  // Initial rollout contract: ADMIN execution is enabled by default. Do not alter
  // non-admin roles here; their catalog defaults / later dashboard choices remain authoritative.
  await prisma.rolePermission.upsert({
    where: { role_permissionId: { role: "ADMIN", permissionId: permission.id } },
    update: { enabled: true },
    create: { role: "ADMIN", permissionId: permission.id, enabled: true },
  });

  const roleRows = await prisma.rolePermission.findMany({
    where: { permissionId: permission.id, role: { in: ["ADMIN", "MANAGER", "PROJECT_MANAGER", "TEAM_MEMBER"] } },
    select: { role: true, enabled: true },
  });
  const byRole = Object.fromEntries(roleRows.map((row) => [row.role, Boolean(row.enabled)]));
  if (byRole.ADMIN !== true) throw new Error("ADMIN ramzy.execute_actions is not enabled");

  const current = await prisma.agentSettings.findUnique({
    where: { id: "main" },
    select: { id: true, readOnlyMode: true, approvalActionsEnabled: true },
  });

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
    console.log("EMERGENCY_LOCK_AFTER=OFF_BY_SOURCE_DEFAULT");
    console.log("APPROVAL_ACTIONS_AFTER=ENV_OR_DEFAULT_ON");
  }

  const admin = await prisma.user.findFirst({
    where: { role: "ADMIN", status: "ACTIVE" },
    select: { id: true, role: true },
  });
  if (!admin) throw new Error("No ACTIVE ADMIN available for execution-control verification");

  const control = await resolveRamzyExecutionControl(admin);
  console.log(`ADMIN_EXECUTION_PERMISSION=${control.permissionGranted ? "PASS" : "FAIL"}`);
  console.log(`ADMIN_EXECUTION_STATE=${control.state}`);
  console.log(`ADMIN_CAN_EXECUTE_AFTER_APPROVAL=${control.canExecute ? "YES" : "NO"}`);
  if (!control.permissionGranted || control.emergencyLocked || !control.approvalActionsEnabled || !control.canExecute) {
    throw new Error(`ADMIN execution control not enabled: ${control.state}`);
  }

  console.log(`MANAGER_EXECUTION_DEFAULT=${byRole.MANAGER === true ? "ENABLED" : "DISABLED"}`);
  console.log(`PROJECT_MANAGER_EXECUTION_DEFAULT=${byRole.PROJECT_MANAGER === true ? "ENABLED" : "DISABLED"}`);
  console.log(`TEAM_MEMBER_EXECUTION_DEFAULT=${byRole.TEAM_MEMBER === true ? "ENABLED" : "DISABLED"}`);
  console.log("PERMISSION_CATALOG_SYNC=PASS");
  console.log("DATABASE_EXECUTION_CONTROL_STATE=PASS");
} finally {
  await prisma.$disconnect();
}
