#!/usr/bin/env python3
from pathlib import Path

ROOT = Path('/var/www/TOS')
ROUTE = ROOT / 'backend/src/routes/crmProjectsIntegration.routes.js'
MARKER = 'TOS_TCRM_PHASE4_STABLE_MANAGER_ID_V1'

if not ROUTE.exists():
    raise SystemExit('PHASE4_ERROR=MISSING_CRM_INTEGRATION_ROUTE')

route = ROUTE.read_text(encoding='utf-8')

already = (
    MARKER in route
    and 'projectManagerTosUserId' in route
    and 'changeType: "PROJECT_MANAGER_CHANGED"' in route
)
if already:
    print('PATCH_STATUS=ALREADY_APPLIED')
    print(f'PATCH_MARKER={MARKER}')
    raise SystemExit(0)

if MARKER in route or 'changeType: "PROJECT_MANAGER_CHANGED"' in route:
    raise SystemExit('PHASE4_ERROR=PARTIAL_STATE_DETECTED')

old_resolver = '''async function resolveProjectManagerFromPayload(payload, db = prisma) {
  const email = optionalPayloadText(
    payload,
    "projectManagerEmail",
    "project_manager_email",
    "pmEmail",
    "pm_email",
    "accountManagerEmail",
    "account_manager_email",
    "amEmail",
    "am_email",
    "assignedAccountManagerEmail",
    "assigned_account_manager_email",
    "assignedProjectManagerEmail",
    "assigned_project_manager_email"
  );
  const name = optionalPayloadText(
    payload,
    "projectManagerName",
    "project_manager_name",
    "pmName",
    "pm_name",
    "accountManagerName",
    "account_manager_name",
    "amName",
    "am_name",
    "assignedAccountManagerName",
    "assigned_account_manager_name",
    "assignedProjectManagerName",
    "assigned_project_manager_name"
  );
  return findActiveUserByEmailOrName(db, { email, name });
}
'''
new_resolver = '''// TOS_TCRM_PHASE4_STABLE_MANAGER_ID_V1
// TCRM Account Manager -> TOS Project Manager must use a TOS-issued User.id.
// Email/name are display fields only and are never identity keys for PM sync.
async function resolveProjectManagerFromPayload(payload, db = prisma) {
  const tosUserId = optionalPayloadText(
    payload,
    "projectManagerTosUserId",
    "project_manager_tos_user_id",
    "accountManagerTosUserId",
    "account_manager_tos_user_id"
  );
  if (!tosUserId) return null;

  const user = await db.user.findFirst({
    where: {
      id: tosUserId,
      status: "ACTIVE",
      role: { notIn: ["CLIENT", "FORMER_EMPLOYEE"] },
    },
    select: { id: true, name: true, email: true, role: true },
  }).catch(() => null);

  if (!user?.id) {
    throw new AppError("Stable TOS Project Manager identity is invalid or inactive", 400);
  }
  return user;
}
'''
if route.count(old_resolver) != 1:
    raise SystemExit(f'PHASE4_ERROR=MANAGER_RESOLVER_ANCHOR_COUNT_{route.count(old_resolver)}')
route = route.replace(old_resolver, new_resolver, 1)

old_apply = '''async function applyProjectManagerMapping(tx, projectId, manager, { preserveExistingRole = false } = {}) {
  if (!manager?.id) return;
  await tx.project.update({ where: { id: projectId }, data: { projectManagerId: manager.id } });
  const existing = await tx.projectMember.findUnique({
    where: { projectId_userId: { projectId, userId: manager.id } },
    select: { role: true },
  });
  if (!existing) {
    await tx.projectMember.create({ data: { projectId, userId: manager.id, role: "MANAGER" } });
  } else if (!preserveExistingRole && existing.role !== "OWNER") {
    await tx.projectMember.update({
      where: { projectId_userId: { projectId, userId: manager.id } },
      data: { role: "MANAGER" },
    });
  }
}
'''
new_apply = '''async function applyProjectManagerMapping(tx, projectId, manager, { preserveExistingRole = false } = {}) {
  if (!manager?.id) return;

  const project = await tx.project.findUnique({
    where: { id: projectId },
    select: { projectManagerId: true },
  });
  const previousProjectManagerId = project?.projectManagerId || null;

  if (previousProjectManagerId !== manager.id) {
    await tx.project.update({ where: { id: projectId }, data: { projectManagerId: manager.id } });
    await tx.projectActivity.create({
      data: {
        projectId,
        userId: null,
        type: "UPDATED",
        title: "TCRM Project Manager synced",
        message: "Project Manager changed from TCRM using a stable TOS user identity.",
        metadata: {
          source: "TCRM",
          syncVersion: "TOS_TCRM_PHASE4_STABLE_MANAGER_ID_V1",
          changeType: "PROJECT_MANAGER_CHANGED",
          previousProjectManagerId,
          nextProjectManagerId: manager.id,
          identityMethod: "TOS_USER_ID",
        },
      },
    });
  }

  const existing = await tx.projectMember.findUnique({
    where: { projectId_userId: { projectId, userId: manager.id } },
    select: { role: true },
  });
  if (!existing) {
    await tx.projectMember.create({ data: { projectId, userId: manager.id, role: "MANAGER" } });
  } else if (!preserveExistingRole && existing.role !== "OWNER") {
    await tx.projectMember.update({
      where: { projectId_userId: { projectId, userId: manager.id } },
      data: { role: "MANAGER" },
    });
  }
}
'''
if route.count(old_apply) != 1:
    raise SystemExit(f'PHASE4_ERROR=MANAGER_APPLY_ANCHOR_COUNT_{route.count(old_apply)}')
route = route.replace(old_apply, new_apply, 1)

ROUTE.write_text(route, encoding='utf-8')

print('PATCH_STATUS=APPLIED_TO_WORKTREE')
print(f'PATCH_MARKER={MARKER}')
print('FILES_CHANGED=backend/src/routes/crmProjectsIntegration.routes.js')
print('PM_IDENTITY=TOS_USER_ID_ONLY')
print('EMAIL_NAME_PM_MATCHING=DISABLED')
print('PM_CHANGE_HISTORY=PROJECT_ACTIVITY_UPDATED')
