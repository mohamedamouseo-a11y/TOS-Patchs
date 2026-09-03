#!/usr/bin/env python3
from pathlib import Path

ROOT = Path('/var/www/TOS')
PERMISSIONS = ROOT / 'backend/src/services/permissions.service.js'
TASKS = ROOT / 'backend/src/routes/tasks.routes.js'
PERMISSIONS_UI = ROOT / 'frontend/src/pages/PermissionsPage.jsx'

for path in (PERMISSIONS, TASKS, PERMISSIONS_UI):
    if not path.exists():
        raise SystemExit(f'ADMIN_PERFORMANCE_PERMISSIONS_ERROR=MISSING_{path.name}')


def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'ADMIN_PERFORMANCE_PERMISSIONS_ERROR={label}_COUNT_{count}')
    return text.replace(old, new, 1)


def replace_function(text, signature, next_anchor, replacement, label):
    start = text.find(signature)
    if start < 0:
        raise SystemExit(f'ADMIN_PERFORMANCE_PERMISSIONS_ERROR={label}_START_NOT_FOUND')
    end = text.find(next_anchor, start)
    if end < 0:
        raise SystemExit(f'ADMIN_PERFORMANCE_PERMISSIONS_ERROR={label}_END_NOT_FOUND')
    return text[:start] + replacement.rstrip() + '\n\n' + text[end:].lstrip('\n')

# -----------------------------------------------------------------------------
# 1) Dynamic permissions catalog: visibility is explicit, not ADMIN hardcode.
# -----------------------------------------------------------------------------
permissions = PERMISSIONS.read_text(encoding='utf-8')
if 'performance.view_all' in permissions:
    raise SystemExit('ADMIN_PERFORMANCE_PERMISSIONS_ERROR=PERMISSIONS_ALREADY_APPLIED')

reports_definition = '  { key: "reports.view", label: "مشاهدة التقارير", category: "Reports", description: "مشاهدة لوحات المتابعة والتقارير." },\n'
performance_definitions = reports_definition + '''  { key: "performance.view_self", label: "مشاهدة أدائك الشخصي", category: "Performance", description: "مشاهدة بيانات الأداء الخاصة بحساب المستخدم نفسه." },
  { key: "performance.view_team", label: "مشاهدة أداء الفريق", category: "Performance", description: "مشاهدة أداء أعضاء المشاريع الواقعة داخل نطاق المستخدم الحالي." },
  { key: "performance.view_all", label: "مشاهدة أداء كل الموظفين", category: "Performance", description: "مشاهدة أداء جميع الموظفين على مستوى الشركة. لا تُمنح للـ Admin افتراضيًا." },
'''
permissions = replace_once(permissions, reports_definition, performance_definitions, 'PERMISSION_DEFINITIONS')

permissions = replace_once(
    permissions,
    '    "reports.view",\n    "sla.policies.manage",\n  ],\n  MANAGER:',
    '    "reports.view",\n    "performance.view_self",\n    "performance.view_team",\n    "sla.policies.manage",\n  ],\n  MANAGER:',
    'ADMIN_DEFAULTS',
)
permissions = replace_once(
    permissions,
    '  MANAGER: ["projects.create", "tasks.manage", "design_queue.assign", "files.upload", "chat.use", "reports.view"],\n  PROJECT_MANAGER: ["projects.create", "tasks.manage", "design_queue.assign", "files.upload", "chat.use", "reports.view"],\n  TEAM_MEMBER: ["tasks.manage", "files.upload", "chat.use"],',
    '  MANAGER: ["projects.create", "tasks.manage", "design_queue.assign", "files.upload", "chat.use", "reports.view", "performance.view_self", "performance.view_team"],\n  PROJECT_MANAGER: ["projects.create", "tasks.manage", "design_queue.assign", "files.upload", "chat.use", "reports.view", "performance.view_self", "performance.view_team"],\n  TEAM_MEMBER: ["tasks.manage", "files.upload", "chat.use", "performance.view_self"],',
    'OTHER_ROLE_DEFAULTS',
)
PERMISSIONS.write_text(permissions, encoding='utf-8')

# -----------------------------------------------------------------------------
# 2) Team Performance read scope. SUPER_ADMIN remains absolute. Everyone else
#    follows performance.view_self / view_team / view_all from the permission DB.
# -----------------------------------------------------------------------------
tasks = TASKS.read_text(encoding='utf-8')
if 'resolveTeamPerformancePermissionScope' in tasks:
    raise SystemExit('ADMIN_PERFORMANCE_PERMISSIONS_ERROR=TASK_SCOPE_ALREADY_APPLIED')

helper_anchor = '// Phase 2+3: Team Performance Aggregation Endpoint\n'
if helper_anchor not in tasks:
    raise SystemExit('ADMIN_PERFORMANCE_PERMISSIONS_ERROR=TEAM_PERFORMANCE_ANCHOR_NOT_FOUND')

helper = r'''// PERFORMANCE_PERMISSION_SCOPE_V1
async function resolveTeamPerformancePermissionScope(req) {
  const role = String(req.user?.role || "").toUpperCase();
  const isSuperAdmin = role === "SUPER_ADMIN";
  const canViewAll = isSuperAdmin || await hasPermission(req.user, "performance.view_all");
  const canViewTeam = canViewAll || await hasPermission(req.user, "performance.view_team");
  const canViewSelf = canViewTeam || await hasPermission(req.user, "performance.view_self");

  if (!canViewSelf) throw new AppError("Team Performance access is not allowed", 403);

  if (canViewAll) {
    const [projects, users] = await Promise.all([
      prisma.project.findMany({ where: { archivedAt: null }, select: { id: true } }),
      prisma.user.findMany({ where: { role: { notIn: ["CLIENT", "FORMER_EMPLOYEE"] } }, select: { id: true } }),
    ]);
    return {
      level: "ALL",
      canViewAll: true,
      canViewTeam: true,
      canViewSelf: true,
      projectIds: projects.map((project) => project.id),
      userIds: users.map((user) => user.id),
      userProjectMap: new Map(),
    };
  }

  const projects = await prisma.project.findMany({
    where: { archivedAt: null, members: { some: { userId: req.user.id } } },
    select: { id: true, members: { select: { userId: true } } },
  });
  const projectIds = projects.map((project) => project.id);
  const userProjectMap = new Map();
  for (const project of projects) {
    for (const member of project.members || []) {
      if (!userProjectMap.has(member.userId)) userProjectMap.set(member.userId, []);
      userProjectMap.get(member.userId).push(project.id);
    }
  }

  const userIds = canViewTeam
    ? [...new Set([req.user.id, ...projects.flatMap((project) => (project.members || []).map((member) => member.userId))])]
    : [req.user.id];

  return {
    level: canViewTeam ? "TEAM" : "SELF",
    canViewAll: false,
    canViewTeam: Boolean(canViewTeam),
    canViewSelf: true,
    projectIds,
    userIds,
    userProjectMap,
  };
}

'''
tasks = tasks.replace(helper_anchor, helper + helper_anchor, 1)

# Main Team Performance route scope.
route_anchor = 'router.get("/reports/team-performance", asyncHandler(async (req, res) => {'
route_start = tasks.find(route_anchor)
if route_start < 0:
    raise SystemExit('ADMIN_PERFORMANCE_PERMISSIONS_ERROR=MAIN_ROUTE_NOT_FOUND')
old_scope_start = tasks.find('  const isAdmin = isSystemAdmin(req.user);', route_start)
old_scope_end = tasks.find('\n\n  // Fetch all users in scope', old_scope_start)
if old_scope_start < 0 or old_scope_end < 0:
    raise SystemExit('ADMIN_PERFORMANCE_PERMISSIONS_ERROR=MAIN_SCOPE_NOT_FOUND')
main_scope = '''  const performanceScope = await resolveTeamPerformancePermissionScope(req);
  const accessibleProjectIds = performanceScope.projectIds;
  const accessibleUserIds = performanceScope.userIds;
  const userProjectMap = performanceScope.userProjectMap;'''
tasks = tasks[:old_scope_start] + main_scope + tasks[old_scope_end:]

# Export dataset scope. Phase 6 may already have exported this function; do not
# touch the declaration, only replace the old role-hardcoded scope block.
export_marker = 'buildTeamPerformanceExportDataset(req, payload = {})'
export_pos = tasks.find(export_marker)
if export_pos < 0:
    raise SystemExit('ADMIN_PERFORMANCE_PERMISSIONS_ERROR=EXPORT_DATASET_NOT_FOUND')
export_scope_start = tasks.find('  const isAdmin = isSystemAdmin(req.user);', export_pos)
export_scope_end = tasks.find('\n\n  let scopedProjectIds = accessibleProjectIds;', export_scope_start)
if export_scope_start < 0 or export_scope_end < 0:
    raise SystemExit('ADMIN_PERFORMANCE_PERMISSIONS_ERROR=EXPORT_SCOPE_NOT_FOUND')
export_scope = '''  const performanceScope = await resolveTeamPerformancePermissionScope(req);
  const accessibleProjectIds = performanceScope.projectIds;
  const accessibleUserIds = performanceScope.userIds;'''
tasks = tasks[:export_scope_start] + export_scope + tasks[export_scope_end:]

# Targets use the exact same visible users/departments as the Team Performance
# scope. Full department catalog is only exposed when view_all is allowed.
new_target_scope = r'''async function getTargetAccessScope(req) {
  const performanceScope = await resolveTeamPerformancePermissionScope(req);
  const users = performanceScope.userIds.length
    ? await prisma.user.findMany({
        where: {
          id: { in: performanceScope.userIds },
          status: "ACTIVE",
          role: { notIn: ["CLIENT", "FORMER_EMPLOYEE"] },
        },
        select: { id: true, department: true },
      })
    : [];
  const departmentUnits = performanceScope.canViewAll
    ? await prisma.departmentUnit.findMany({ where: { isActive: true }, select: { name: true, key: true } })
    : [];

  const userIds = new Set(users.map((user) => user.id));
  const departmentValues = new Set(users.map((user) => String(user.department || "").trim()).filter(Boolean));
  if (performanceScope.canViewAll) {
    for (const unit of departmentUnits) {
      if (unit.name) departmentValues.add(String(unit.name).trim());
      if (unit.key) departmentValues.add(String(unit.key).trim());
    }
  }
  const departmentKeys = new Set([...departmentValues].map(targetDepartmentKey).filter(Boolean));

  return {
    isAdmin: performanceScope.canViewAll,
    isManager: performanceScope.canViewTeam && !performanceScope.canViewAll,
    permissionLevel: performanceScope.level,
    userIds,
    departmentValues: [...departmentValues],
    departmentKeys,
  };
}'''
tasks = replace_function(tasks, 'async function getTargetAccessScope(req) {', 'async function assertTargetSubjectExists', new_target_scope, 'TARGET_SCOPE')

# ADMIN can still manage targets by its existing role authority, but without
# view_all it cannot write outside the visible permission scope.
old = '''async function assertTargetWriteAccess(req, input) {
  const isAdmin = isSystemAdmin(req.user);
  const isManager = req.user.role === "MANAGER" || req.user.role === "PROJECT_MANAGER";
  if (!isAdmin && !isManager) throw new AppError("Target management requires manager access", 403);

  await assertTargetSubjectExists(input);
  if (isAdmin) return;

  const scope = await getTargetAccessScope(req);'''
new = '''async function assertTargetWriteAccess(req, input) {
  const canManage = isSystemAdmin(req.user) || req.user.role === "MANAGER" || req.user.role === "PROJECT_MANAGER";
  if (!canManage) throw new AppError("Target management requires manager access", 403);

  await assertTargetSubjectExists(input);
  const scope = await getTargetAccessScope(req);
  if (scope.isAdmin) return;'''
tasks = replace_once(tasks, old, new, 'TARGET_WRITE_SCOPE')

old = '''async function assertBulkEmployeeTargetWriteAccess(req, employeeIds) {
  const isAdmin = isSystemAdmin(req.user);
  const isManager = req.user.role === "MANAGER" || req.user.role === "PROJECT_MANAGER";
  if (!isAdmin && !isManager) throw new AppError("Target management requires manager access", 403);

  const employees = await prisma.user.findMany({'''
new = '''async function assertBulkEmployeeTargetWriteAccess(req, employeeIds) {
  const canManage = isSystemAdmin(req.user) || req.user.role === "MANAGER" || req.user.role === "PROJECT_MANAGER";
  if (!canManage) throw new AppError("Target management requires manager access", 403);

  const employees = await prisma.user.findMany({'''
tasks = replace_once(tasks, old, new, 'BULK_TARGET_WRITE_HEADER')
tasks = replace_once(
    tasks,
    '''  if (isAdmin) return;
  const scope = await getTargetAccessScope(req);
  const unauthorized = employeeIds.filter((id) => !scope.userIds.has(id));''',
    '''  const scope = await getTargetAccessScope(req);
  if (scope.isAdmin) return;
  const unauthorized = employeeIds.filter((id) => !scope.userIds.has(id));''',
    'BULK_TARGET_WRITE_SCOPE',
)

# Workforce is the read scope used by Workforce, Skills, Talent, Recognition and
# Executive modules. Make its isAdmin mean permission-level ALL, not role ADMIN.
new_workforce_scope = r'''async function getWorkforceScope(req, { employeeId = null, department = null, requireManage = false } = {}) {
  const performanceScope = await resolveTeamPerformancePermissionScope(req);
  const isAdmin = performanceScope.canViewAll;
  const isManager = performanceScope.canViewTeam && !performanceScope.canViewAll;
  const canManage = isSystemAdmin(req.user) || req.user.role === "MANAGER" || req.user.role === "PROJECT_MANAGER";
  if (requireManage && !canManage) throw new AppError("Workforce planning management requires manager access", 403);

  const projectIds = performanceScope.projectIds;
  const candidateUserIds = performanceScope.userIds;
  const users = candidateUserIds.length
    ? await prisma.user.findMany({
        where: { id: { in: candidateUserIds }, role: { notIn: ["CLIENT", "FORMER_EMPLOYEE"] } },
        select: {
          id: true,
          name: true,
          email: true,
          role: true,
          department: true,
          jobTitle: true,
          avatarUrl: true,
          designWeeklyCapacityHours: true,
          status: true,
        },
        orderBy: [{ department: "asc" }, { name: "asc" }],
      })
    : [];
  // PHASE2_ACTIVE_WORKFORCE_SCOPE: disabled/pending users are historical, not live workforce.
  const activeUsers = users.filter((user) => user.status === "ACTIVE");
  const allowedIds = new Set(activeUsers.map((user) => user.id));
  if (employeeId && !allowedIds.has(employeeId)) throw new AppError("Unauthorized workforce employee", 403);

  let visibleUsers = employeeId ? activeUsers.filter((user) => user.id === employeeId) : activeUsers;
  if (department) {
    const key = String(department).trim().toLowerCase();
    visibleUsers = visibleUsers.filter((user) => String(user.department || "").trim().toLowerCase() === key);
  }

  return {
    isAdmin,
    isManager,
    canManage,
    permissionLevel: performanceScope.level,
    projectIds,
    users: visibleUsers,
    userIds: visibleUsers.map((user) => user.id),
  };
}'''
tasks = replace_function(tasks, 'async function getWorkforceScope(req, { employeeId = null, department = null, requireManage = false } = {}) {', 'async function assertWorkforceCapacityAccess', new_workforce_scope, 'WORKFORCE_SCOPE')

# Talent role visibility must not use role ADMIN as a bypass. It follows the
# permission-scoped workforce users/departments unless view_all is enabled.
new_succession_loader = r'''async function loadSuccessionRoleForAccess(req, roleId, { requireAdmin = false, allowInactive = false } = {}) {
  if (requireAdmin) assertTalentAdmin(req);
  else assertTalentViewer(req);
  const role = await prisma.successionRole.findUnique({ where: { id: roleId } });
  if (!role) throw new AppError("Succession role not found", 404);
  if (!allowInactive && !role.isActive) throw new AppError("Succession role is inactive", 409);

  const scope = await getTalentScope(req, {});
  if (!scope.isAdmin) {
    const visibleDepartments = new Set(scope.users.map((user) => skillKey(user.department)).filter(Boolean));
    if (!role.department || !visibleDepartments.has(skillKey(role.department))) throw new AppError("Unauthorized succession role", 403);
  }
  return role;
}'''
tasks = replace_function(tasks, 'async function loadSuccessionRoleForAccess(req, roleId, { requireAdmin = false, allowInactive = false } = {}) {', 'async function normalizeSuccessionCandidateInput', new_succession_loader, 'SUCCESSION_SCOPE')

TASKS.write_text(tasks, encoding='utf-8')

# -----------------------------------------------------------------------------
# 3) Permissions Matrix localization for the new explicit controls.
# -----------------------------------------------------------------------------
ui = PERMISSIONS_UI.read_text(encoding='utf-8')
if 'View all employee performance' in ui:
    raise SystemExit('ADMIN_PERFORMANCE_PERMISSIONS_ERROR=UI_ALREADY_APPLIED')
ui_anchor = '  "مشاهدة التقارير": "View reports",\n'
ui_insert = ui_anchor + '''  "مشاهدة أدائك الشخصي": "View own performance",
  "مشاهدة أداء الفريق": "View team performance",
  "مشاهدة أداء كل الموظفين": "View all employee performance",
'''
ui = replace_once(ui, ui_anchor, ui_insert, 'PERMISSIONS_UI_LABELS')
PERMISSIONS_UI.write_text(ui, encoding='utf-8')

print('ADMIN_PERFORMANCE_VISIBILITY_PERMISSIONS_V1_APPLIED=YES')
print('PERMISSION_VIEW_SELF=YES')
print('PERMISSION_VIEW_TEAM=YES')
print('PERMISSION_VIEW_ALL=YES')
print('ADMIN_DEFAULT_VIEW_ALL=NO')
print('SUPER_ADMIN_VIEW_ALL=ALWAYS')
print('TEAM_PERFORMANCE_ROLE_HARDCODE_REMOVED=YES')
print('RAMZY_INHERITS_PERMISSION_SCOPE=YES')
print('SCHEMA_CHANGED=NO')
