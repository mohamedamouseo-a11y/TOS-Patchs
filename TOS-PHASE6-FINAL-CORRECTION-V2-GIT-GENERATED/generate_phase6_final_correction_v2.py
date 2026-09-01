#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys

BASELINE = "9773ffa21fabe90c87823081984ebb6bb55999e1"
repo = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS").resolve()
path = repo / "backend/src/routes/tasks.routes.js"


def run(*args):
    return subprocess.check_output(args, cwd=repo, text=True).strip()


def replace_block(text, start_marker, end_marker, replacement, label):
    start = text.find(start_marker)
    if start < 0:
        raise SystemExit(f"{label}=FAIL missing start marker")
    end = text.find(end_marker, start)
    if end < 0:
        raise SystemExit(f"{label}=FAIL missing end marker")
    return text[:start] + replacement.rstrip() + "\n\n" + text[end:]


head = run("git", "rev-parse", "HEAD")
if head != BASELINE:
    raise SystemExit(f"BASELINE_CHECK=FAIL expected={BASELINE} actual={head}")
print("BASELINE_CHECK=PASS")

text = path.read_text()
required_markers = [
    'const TARGET_PERIOD_TYPES = new Set(["WEEKLY", "MONTHLY", "QUARTERLY", "YEARLY", "CUSTOM"]);',
    'async function assertTargetWriteAccess(req, input) {',
    'router.get("/reports/team-performance/targets/summary"',
    'router.post("/reports/team-performance/targets/bulk"',
    'function addTargetIntelligence(intelligence, targetSummary) {',
]
for marker in required_markers:
    if marker not in text:
        raise SystemExit(f"PHASE6_V1_WORKTREE_CHECK=FAIL missing={marker}")

migration = repo / "backend/prisma/migrations/202609011600_phase6_performance_targets/migration.sql"
schema = (repo / "backend/prisma/schema.prisma").read_text()
if not migration.exists() or "model PerformanceTarget" not in schema:
    raise SystemExit("PHASE6_V1_WORKTREE_CHECK=FAIL migration/model missing")
print("PHASE6_V1_WORKTREE_CHECK=PASS")

helpers = r'''function targetDepartmentKey(value) {
  return String(value || "").trim().toLowerCase();
}

function parseTargetQueryRange(start, end) {
  if (!start || !end) throw new AppError("start and end are required", 400);
  const startDate = new Date(start);
  const endDate = new Date(end);
  if (Number.isNaN(startDate.getTime()) || Number.isNaN(endDate.getTime())) throw new AppError("Invalid target date range", 400);
  if (startDate > endDate) throw new AppError("start must be before or equal end", 400);
  return { startDate, endDate };
}

async function getTargetAccessScope(req) {
  const isAdmin = isSystemAdmin(req.user);
  const isManager = req.user.role === "MANAGER" || req.user.role === "PROJECT_MANAGER";
  let users = [];
  let departmentUnits = [];

  if (isAdmin) {
    [users, departmentUnits] = await Promise.all([
      prisma.user.findMany({
        where: { role: { notIn: ["CLIENT", "FORMER_EMPLOYEE"] } },
        select: { id: true, department: true },
      }),
      prisma.departmentUnit.findMany({
        where: { isActive: true },
        select: { name: true, key: true },
      }),
    ]);
  } else if (isManager) {
    const projects = await prisma.project.findMany({
      where: { archivedAt: null, members: { some: { userId: req.user.id } } },
      select: { members: { select: { userId: true } } },
    });
    const candidateIds = [...new Set(projects.flatMap((project) => project.members.map((member) => member.userId)))];
    users = candidateIds.length
      ? await prisma.user.findMany({
          where: { id: { in: candidateIds }, role: { notIn: ["CLIENT", "FORMER_EMPLOYEE"] } },
          select: { id: true, department: true },
        })
      : [];
  } else {
    const own = await prisma.user.findUnique({
      where: { id: req.user.id },
      select: { id: true, department: true, role: true },
    });
    if (own && !["CLIENT", "FORMER_EMPLOYEE"].includes(own.role)) users = [own];
  }

  const userIds = new Set(users.map((user) => user.id));
  const departmentValues = new Set(users.map((user) => String(user.department || "").trim()).filter(Boolean));
  if (isAdmin) {
    for (const unit of departmentUnits) {
      if (unit.name) departmentValues.add(String(unit.name).trim());
      if (unit.key) departmentValues.add(String(unit.key).trim());
    }
  }
  const departmentKeys = new Set([...departmentValues].map(targetDepartmentKey).filter(Boolean));

  return {
    isAdmin,
    isManager,
    userIds,
    departmentValues: [...departmentValues],
    departmentKeys,
  };
}

async function assertTargetSubjectExists(input) {
  if (input.scopeType === "EMPLOYEE") {
    const employee = await prisma.user.findUnique({
      where: { id: input.employeeId },
      select: { id: true, role: true, department: true },
    });
    if (!employee) throw new AppError("Target employee not found", 404);
    if (["CLIENT", "FORMER_EMPLOYEE"].includes(employee.role)) throw new AppError("Target employee is not eligible for performance targets", 400);
    return employee;
  }

  const department = String(input.department || "").trim();
  const [unit, employee] = await Promise.all([
    prisma.departmentUnit.findFirst({
      where: {
        isActive: true,
        OR: [{ name: department }, { key: department }],
      },
      select: { id: true, name: true, key: true },
    }),
    prisma.user.findFirst({
      where: { department, role: { notIn: ["CLIENT", "FORMER_EMPLOYEE"] } },
      select: { id: true, department: true },
    }),
  ]);
  if (!unit && !employee) throw new AppError("Target department not found", 404);
  return unit || employee;
}

async function assertTargetWriteAccess(req, input) {
  const isAdmin = isSystemAdmin(req.user);
  const isManager = req.user.role === "MANAGER" || req.user.role === "PROJECT_MANAGER";
  if (!isAdmin && !isManager) throw new AppError("Target management requires manager access", 403);

  await assertTargetSubjectExists(input);
  if (isAdmin) return;

  const scope = await getTargetAccessScope(req);
  if (input.scopeType === "EMPLOYEE" && !scope.userIds.has(input.employeeId)) {
    throw new AppError("Unauthorized employee target", 403);
  }
  if (input.scopeType === "DEPARTMENT" && !scope.departmentKeys.has(targetDepartmentKey(input.department))) {
    throw new AppError("Unauthorized department target", 403);
  }
}

async function assertBulkEmployeeTargetWriteAccess(req, employeeIds) {
  const isAdmin = isSystemAdmin(req.user);
  const isManager = req.user.role === "MANAGER" || req.user.role === "PROJECT_MANAGER";
  if (!isAdmin && !isManager) throw new AppError("Target management requires manager access", 403);

  const employees = await prisma.user.findMany({
    where: { id: { in: employeeIds }, role: { notIn: ["CLIENT", "FORMER_EMPLOYEE"] } },
    select: { id: true },
  });
  const found = new Set(employees.map((employee) => employee.id));
  const missing = employeeIds.filter((id) => !found.has(id));
  if (missing.length) throw new AppError(`Target employee not found: ${missing.join(", ")}`, 404);

  if (isAdmin) return;
  const scope = await getTargetAccessScope(req);
  const unauthorized = employeeIds.filter((id) => !scope.userIds.has(id));
  if (unauthorized.length) throw new AppError("Unauthorized employee target", 403);
}

async function assertNoExactActiveTarget(input, excludeId = null) {
  if (!input.isActive) return;
  const subjectWhere = input.scopeType === "EMPLOYEE"
    ? { employeeId: input.employeeId }
    : { department: input.department };
  const duplicate = await prisma.performanceTarget.findFirst({
    where: {
      isActive: true,
      scopeType: input.scopeType,
      periodType: input.periodType,
      effectiveFrom: input.effectiveFrom,
      effectiveTo: input.effectiveTo,
      ...subjectWhere,
      ...(excludeId ? { id: { not: excludeId } } : {}),
    },
    select: { id: true },
  });
  if (duplicate) throw new AppError("An active target already exists for this subject and exact period", 409);
}
'''

text = replace_block(
    text,
    "async function assertTargetWriteAccess(req, input) {",
    "function targetMetric(key, actual, target, lower = false) {",
    helpers,
    "TARGET_ACCESS_HARDENING",
)
print("TARGET_ACCESS_HARDENING=PASS")

old_map = '''  const targets = await prisma.performanceTarget.findMany({ where: { isActive: true, effectiveFrom: { lte: new Date(dataset.filters.periodEnd) }, effectiveTo: { gte: new Date(dataset.filters.periodStart) }, OR: [ ...(employeeIds.length ? [{ scopeType: "EMPLOYEE", employeeId: { in: employeeIds } }] : []), ...(departments.length ? [{ scopeType: "DEPARTMENT", department: { in: departments } }] : []) ] }, orderBy: [{ effectiveFrom: "desc" }, { updatedAt: "desc" }] });
  const targetRows = rows.map((row) => {
    const employeeTarget = targets.find((t) => t.scopeType === "EMPLOYEE" && t.employeeId === row.id);
    const departmentTarget = targets.find((t) => t.scopeType === "DEPARTMENT" && t.department === row.department);
    return { employeeId: row.id, name: row.name, department: row.department, ...calcTargetAchievement(row, employeeTarget || departmentTarget || null, employeeTarget ? "EMPLOYEE" : departmentTarget ? "DEPARTMENT" : null) };
  });'''
new_map = '''  const targetScope = [
    ...(employeeIds.length ? [{ scopeType: "EMPLOYEE", employeeId: { in: employeeIds } }] : []),
    ...(departments.length ? [{ scopeType: "DEPARTMENT", department: { in: departments } }] : []),
  ];
  const targets = targetScope.length
    ? await prisma.performanceTarget.findMany({
        where: {
          isActive: true,
          effectiveFrom: { lte: new Date(dataset.filters.periodEnd) },
          effectiveTo: { gte: new Date(dataset.filters.periodStart) },
          OR: targetScope,
        },
        orderBy: [{ effectiveFrom: "desc" }, { updatedAt: "desc" }],
      })
    : [];
  const employeeTargetMap = new Map();
  const departmentTargetMap = new Map();
  for (const target of targets) {
    if (target.scopeType === "EMPLOYEE" && target.employeeId && !employeeTargetMap.has(target.employeeId)) employeeTargetMap.set(target.employeeId, target);
    if (target.scopeType === "DEPARTMENT" && target.department && !departmentTargetMap.has(target.department)) departmentTargetMap.set(target.department, target);
  }
  const targetRows = rows.map((row) => {
    const employeeTarget = employeeTargetMap.get(row.id) || null;
    const departmentTarget = departmentTargetMap.get(row.department) || null;
    return { employeeId: row.id, name: row.name, department: row.department, ...calcTargetAchievement(row, employeeTarget || departmentTarget || null, employeeTarget ? "EMPLOYEE" : departmentTarget ? "DEPARTMENT" : null) };
  });'''
if text.count(old_map) != 1:
    raise SystemExit(f"TARGET_SUMMARY_MAP_HARDENING=FAIL anchor_count={text.count(old_map)}")
text = text.replace(old_map, new_map, 1)
text = text.replace('const target = targets.find((t) => t.scopeType === "DEPARTMENT" && t.department === department) || null;', 'const target = departmentTargetMap.get(department) || null;', 1)
print("TARGET_SUMMARY_MAP_HARDENING=PASS")

get_targets = r'''router.get("/reports/team-performance/targets", asyncHandler(async (req, res) => {
  const { startDate, endDate } = parseTargetQueryRange(req.query.start, req.query.end);
  const scope = await getTargetAccessScope(req);
  const targetScope = [
    ...(scope.userIds.size ? [{ scopeType: "EMPLOYEE", employeeId: { in: [...scope.userIds] } }] : []),
    ...(scope.departmentValues.length ? [{ scopeType: "DEPARTMENT", department: { in: scope.departmentValues } }] : []),
  ];
  const targets = targetScope.length
    ? await prisma.performanceTarget.findMany({
        where: {
          effectiveFrom: { lte: endDate },
          effectiveTo: { gte: startDate },
          OR: targetScope,
        },
        orderBy: [{ isActive: "desc" }, { effectiveFrom: "desc" }, { updatedAt: "desc" }],
        take: 1000,
      })
    : [];
  res.json({ targets });
}));'''
text = replace_block(
    text,
    'router.get("/reports/team-performance/targets", asyncHandler(async (req, res) => {',
    'router.post("/reports/team-performance/targets", asyncHandler(async (req, res) => {',
    get_targets,
    "TARGET_LIST_LIGHTWEIGHT_SCOPE",
)
print("TARGET_LIST_LIGHTWEIGHT_SCOPE=PASS")

post_target = r'''router.post("/reports/team-performance/targets", asyncHandler(async (req, res) => {
  const input = normalizeTargetInput(req.body);
  await assertTargetWriteAccess(req, input);
  await assertNoExactActiveTarget(input);
  const target = await prisma.performanceTarget.create({ data: { ...input, createdById: req.user.id, updatedById: req.user.id } });
  await prisma.workspaceAuditLog.create({ data: { action: "performance_target_created", actorId: req.user.id, metadata: { targetId: target.id, scopeType: target.scopeType, employeeId: target.employeeId, department: target.department, periodType: target.periodType, effectiveFrom: target.effectiveFrom, effectiveTo: target.effectiveTo } } });
  res.status(201).json(target);
}));'''
text = replace_block(
    text,
    'router.post("/reports/team-performance/targets", asyncHandler(async (req, res) => {',
    'router.post("/reports/team-performance/targets/bulk", asyncHandler(async (req, res) => {',
    post_target,
    "TARGET_CREATE_VALIDATION",
)

bulk_target = r'''router.post("/reports/team-performance/targets/bulk", asyncHandler(async (req, res) => {
  const employeeIds = [...new Set((Array.isArray(req.body?.employeeIds) ? req.body.employeeIds : []).map(String))].filter(Boolean);
  if (!employeeIds.length || employeeIds.length > 100) throw new AppError("employeeIds must contain 1-100 values", 400);
  const input = normalizeTargetInput({ ...(req.body?.target || {}), scopeType: "EMPLOYEE", employeeId: employeeIds[0] });
  await assertBulkEmployeeTargetWriteAccess(req, employeeIds);

  const duplicates = input.isActive
    ? await prisma.performanceTarget.findMany({
        where: {
          isActive: true,
          scopeType: "EMPLOYEE",
          employeeId: { in: employeeIds },
          periodType: input.periodType,
          effectiveFrom: input.effectiveFrom,
          effectiveTo: input.effectiveTo,
        },
        select: { employeeId: true },
      })
    : [];
  if (duplicates.length) {
    const duplicateIds = [...new Set(duplicates.map((item) => item.employeeId).filter(Boolean))];
    throw new AppError(`Active target already exists for exact period: ${duplicateIds.join(", ")}`, 409);
  }

  const created = await prisma.$transaction(employeeIds.map((employeeId) => prisma.performanceTarget.create({ data: { ...input, employeeId, createdById: req.user.id, updatedById: req.user.id } })));
  await prisma.workspaceAuditLog.create({ data: { action: "performance_target_bulk_created", actorId: req.user.id, metadata: { employeeIds, targetIds: created.map((t) => t.id), periodType: input.periodType } } });
  res.status(201).json({ targets: created });
}));'''
text = replace_block(
    text,
    'router.post("/reports/team-performance/targets/bulk", asyncHandler(async (req, res) => {',
    'router.patch("/reports/team-performance/targets/:targetId", asyncHandler(async (req, res) => {',
    bulk_target,
    "TARGET_BULK_VALIDATION",
)

patch_target = r'''router.patch("/reports/team-performance/targets/:targetId", asyncHandler(async (req, res) => {
  const existing = await prisma.performanceTarget.findUnique({ where: { id: req.params.targetId } });
  if (!existing) throw new AppError("Target not found", 404);
  const input = normalizeTargetInput(req.body, existing);
  await assertTargetWriteAccess(req, input);
  await assertNoExactActiveTarget(input, existing.id);
  const target = await prisma.performanceTarget.update({ where: { id: existing.id }, data: { ...input, updatedById: req.user.id } });
  await prisma.workspaceAuditLog.create({ data: { action: "performance_target_updated", actorId: req.user.id, metadata: { targetId: target.id } } });
  res.json(target);
}));'''
text = replace_block(
    text,
    'router.patch("/reports/team-performance/targets/:targetId", asyncHandler(async (req, res) => {',
    'router.delete("/reports/team-performance/targets/:targetId", asyncHandler(async (req, res) => {',
    patch_target,
    "TARGET_UPDATE_DUPLICATE_GUARD",
)

copy_target = r'''router.post("/reports/team-performance/targets/:targetId/copy", asyncHandler(async (req, res) => {
  const existing = await prisma.performanceTarget.findUnique({ where: { id: req.params.targetId } });
  if (!existing) throw new AppError("Target not found", 404);
  const input = normalizeTargetInput({ ...existing, effectiveFrom: req.body?.effectiveFrom, effectiveTo: req.body?.effectiveTo, periodType: req.body?.periodType || existing.periodType, isActive: true });
  await assertTargetWriteAccess(req, input);
  await assertNoExactActiveTarget(input);
  const copy = await prisma.performanceTarget.create({ data: { ...input, createdById: req.user.id, updatedById: req.user.id } });
  await prisma.workspaceAuditLog.create({ data: { action: "performance_target_copied", actorId: req.user.id, metadata: { sourceTargetId: existing.id, targetId: copy.id } } });
  res.status(201).json(copy);
}));'''
text = replace_block(
    text,
    'router.post("/reports/team-performance/targets/:targetId/copy", asyncHandler(async (req, res) => {',
    'router.get("/reports/team-performance/intelligence", asyncHandler(async (req, res) => {',
    copy_target,
    "TARGET_COPY_DUPLICATE_GUARD",
)

path.write_text(text)

checks = {
    "INVALID_EMPLOYEE_VALIDATION": 'throw new AppError("Target employee not found", 404)',
    "MANAGER_SCOPE_ENFORCEMENT": 'throw new AppError("Unauthorized employee target", 403)',
    "EXACT_DUPLICATE_GUARD": 'An active target already exists for this subject and exact period',
    "LIGHTWEIGHT_TARGET_SCOPE": 'async function getTargetAccessScope(req)',
    "BULK_NO_N_PLUS_ONE": 'async function assertBulkEmployeeTargetWriteAccess(req, employeeIds)',
}
final_text = path.read_text()
for label, marker in checks.items():
    if marker not in final_text:
        raise SystemExit(f"{label}=FAIL")
    print(f"{label}=PASS")

print("PHASE6_FINAL_CORRECTION_V2_GENERATED=YES")
