#!/usr/bin/env python3
from pathlib import Path
import sys

repo = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
path = repo / "backend/src/routes/tasks.routes.js"
text = path.read_text()

if "// PHASE10_TALENT_SUCCESSION" in text:
    print("BACKEND_TALENT_SUCCESSION=PASS already-present")
    raise SystemExit(0)

helper_anchor = "function buildTeamPerformanceIntelligence(dataset) {"
if helper_anchor not in text:
    raise SystemExit("Phase 10 backend helper anchor not found")

helpers = r'''
// PHASE10_TALENT_SUCCESSION
const TALENT_POTENTIAL_LEVELS = new Set(["LOW", "MEDIUM", "HIGH"]);
const SUCCESSION_READINESS = new Set(["READY_NOW", "READY_1_2_YEARS", "READY_3_PLUS_YEARS", "DEVELOPING"]);
const SUCCESSION_CRITICALITY = new Set(["NORMAL", "HIGH", "CRITICAL"]);

function talentText(value, max = 4000) {
  if (value === undefined) return undefined;
  if (value === null) return null;
  const text = String(value).trim();
  if (!text) return null;
  if (text.length > max) throw new AppError(`Talent text exceeds ${max} characters`, 400);
  return text;
}

function talentPotential(value) {
  const normalized = String(value || "").trim().toUpperCase();
  if (!TALENT_POTENTIAL_LEVELS.has(normalized)) throw new AppError("potentialLevel must be LOW, MEDIUM, or HIGH", 400);
  return normalized;
}

function successionReadiness(value, fallback = "DEVELOPING") {
  const normalized = String(value || fallback).trim().toUpperCase();
  if (!SUCCESSION_READINESS.has(normalized)) throw new AppError("Invalid succession readiness", 400);
  return normalized;
}

function successionCriticality(value, fallback = "NORMAL") {
  const normalized = String(value || fallback).trim().toUpperCase();
  if (!SUCCESSION_CRITICALITY.has(normalized)) throw new AppError("Invalid succession role criticality", 400);
  return normalized;
}

function successionPriority(value, fallback = 3) {
  const priority = Number(value ?? fallback);
  if (!Number.isInteger(priority) || priority < 1 || priority > 5) throw new AppError("Succession priority must be an integer from 1 to 5", 400);
  return priority;
}

function assertTalentViewer(req) {
  const role = String(req.user?.role || "").toUpperCase();
  const isAdmin = isSystemAdmin(req.user);
  const isManager = role === "MANAGER" || role === "PROJECT_MANAGER";
  if (!isAdmin && !isManager) throw new AppError("Talent and succession planning requires manager access", 403);
  return { isAdmin, isManager };
}

function assertTalentAdmin(req) {
  if (!isSystemAdmin(req.user)) throw new AppError("Succession role configuration requires admin access", 403);
}

async function getTalentScope(req, payload = {}) {
  assertTalentViewer(req);
  return getWorkforceScope(req, {
    employeeId: payload.employeeId || null,
    department: payload.department || null,
    requireManage: true,
  });
}

async function assertTalentEmployeeAccess(req, employeeId) {
  return assertSkillEmployeeAccess(req, employeeId, true);
}

function talentPerformanceBand(score) {
  if (score == null || !Number.isFinite(Number(score))) return "NO_DATA";
  const value = Number(score);
  if (value >= 85) return "HIGH";
  if (value >= 70) return "MEDIUM";
  return "LOW";
}

function talentBoxKey(potentialLevel, performanceBand) {
  if (!TALENT_POTENTIAL_LEVELS.has(potentialLevel) || !["LOW", "MEDIUM", "HIGH"].includes(performanceBand)) return null;
  return `${potentialLevel}_${performanceBand}`;
}

function talentBoxLabel(potentialLevel, performanceBand) {
  const labels = {
    HIGH_HIGH: "Future Leader",
    HIGH_MEDIUM: "Emerging Talent",
    HIGH_LOW: "Untapped Potential",
    MEDIUM_HIGH: "High Performer",
    MEDIUM_MEDIUM: "Core Talent",
    MEDIUM_LOW: "Development Focus",
    LOW_HIGH: "Expert Contributor",
    LOW_MEDIUM: "Solid Contributor",
    LOW_LOW: "Performance Support",
  };
  return labels[talentBoxKey(potentialLevel, performanceBand)] || "Unclassified";
}

async function validateSuccessionDepartment(department) {
  if (!department) return;
  const [units, users] = await Promise.all([
    prisma.departmentUnit.findMany({ where: { isActive: true }, select: { key: true, name: true } }),
    prisma.user.findMany({ where: { department: { not: null }, role: { notIn: ["CLIENT", "FORMER_EMPLOYEE"] } }, select: { department: true } }),
  ]);
  const valid = new Set([
    ...units.flatMap((unit) => [skillKey(unit.key), skillKey(unit.name)]),
    ...users.map((user) => skillKey(user.department)),
  ].filter(Boolean));
  if (!valid.has(skillKey(department))) throw new AppError("Succession role department not found", 404);
}

async function normalizeSuccessionRoleInput(payload = {}, existing = null) {
  const title = talentText(payload.title === undefined ? existing?.title : payload.title, 200);
  if (!title) throw new AppError("Succession role title is required", 400);
  const department = talentText(payload.department === undefined ? existing?.department : payload.department, 160);
  const criticality = successionCriticality(payload.criticality === undefined ? existing?.criticality : payload.criticality, existing?.criticality || "NORMAL");
  const incumbentEmployeeId = payload.incumbentEmployeeId === undefined
    ? (existing?.incumbentEmployeeId || null)
    : (String(payload.incumbentEmployeeId || "").trim() || null);
  await validateSuccessionDepartment(department);
  if (incumbentEmployeeId) {
    const incumbent = await prisma.user.findUnique({ where: { id: incumbentEmployeeId }, select: { id: true, role: true } });
    if (!incumbent) throw new AppError("Succession incumbent employee not found", 404);
    if (["CLIENT", "FORMER_EMPLOYEE"].includes(incumbent.role)) throw new AppError("Incumbent is not eligible for succession planning", 400);
  }
  return {
    title,
    department,
    criticality,
    incumbentEmployeeId,
    description: talentText(payload.description === undefined ? existing?.description : payload.description, 3000),
    isActive: payload.isActive === undefined ? (existing?.isActive ?? true) : Boolean(payload.isActive),
  };
}

async function assertNoDuplicateSuccessionRole(input, excludeId = null) {
  if (!input.isActive) return;
  const roles = await prisma.successionRole.findMany({
    where: { isActive: true, ...(excludeId ? { id: { not: excludeId } } : {}) },
    select: { id: true, title: true, department: true },
    take: 2000,
  });
  const duplicate = roles.some((role) => skillKey(role.title) === skillKey(input.title) && skillKey(role.department) === skillKey(input.department));
  if (duplicate) throw new AppError("An active succession role already exists for this title and department", 409);
}

async function loadSuccessionRoleForAccess(req, roleId, { requireAdmin = false, allowInactive = false } = {}) {
  if (requireAdmin) assertTalentAdmin(req);
  else assertTalentViewer(req);
  const role = await prisma.successionRole.findUnique({ where: { id: roleId } });
  if (!role) throw new AppError("Succession role not found", 404);
  if (!allowInactive && !role.isActive) throw new AppError("Succession role is inactive", 409);
  if (!isSystemAdmin(req.user)) {
    const scope = await getTalentScope(req, {});
    const visibleDepartments = new Set(scope.users.map((user) => skillKey(user.department)).filter(Boolean));
    if (!role.department || !visibleDepartments.has(skillKey(role.department))) throw new AppError("Unauthorized succession role", 403);
  }
  return role;
}

async function normalizeSuccessionCandidateInput(req, role, payload = {}, existing = null) {
  const employeeId = String(existing?.employeeId || payload.employeeId || "").trim();
  if (!employeeId) throw new AppError("employeeId is required", 400);
  await assertTalentEmployeeAccess(req, employeeId);
  const readiness = successionReadiness(payload.readiness === undefined ? existing?.readiness : payload.readiness, existing?.readiness || "DEVELOPING");
  const priority = successionPriority(payload.priority === undefined ? existing?.priority : payload.priority, existing?.priority || 3);
  const developmentPlanId = payload.developmentPlanId === undefined
    ? (existing?.developmentPlanId || null)
    : (String(payload.developmentPlanId || "").trim() || null);
  if (developmentPlanId) {
    const plan = await prisma.employeeDevelopmentPlan.findUnique({ where: { id: developmentPlanId }, select: { id: true, employeeId: true, status: true } });
    if (!plan || plan.employeeId !== employeeId || plan.status === "CANCELLED") throw new AppError("Development plan not found for this succession candidate", 404);
  }
  if (role.incumbentEmployeeId && role.incumbentEmployeeId === employeeId) throw new AppError("The current incumbent cannot be nominated as their own successor", 409);
  return {
    employeeId,
    readiness,
    priority,
    rationale: talentText(payload.rationale === undefined ? existing?.rationale : payload.rationale, 3000),
    developmentPlanId,
    isActive: payload.isActive === undefined ? (existing?.isActive ?? true) : Boolean(payload.isActive),
  };
}

async function auditTalentSuccession(req, action, metadata = {}) {
  await prisma.workspaceAuditLog.create({
    data: {
      action,
      actorId: req.user.id,
      metadata: { ...metadata, occurredAt: new Date().toISOString() },
    },
  });
}

async function buildTalentOverview(req, payload = {}) {
  const scope = await getTalentScope(req, payload);
  const userIds = scope.userIds;
  const departments = [...new Set(scope.users.map((user) => user.department).filter(Boolean))];
  const datasetPromise = buildTeamPerformanceExportDataset(req, {
    start: payload.start,
    end: payload.end,
    employeeId: payload.employeeId || null,
    department: payload.department || null,
  });
  const skillMatrixPromise = buildSkillMatrix(req, {
    employeeId: payload.employeeId || null,
    department: payload.department || null,
  });
  const assessmentsPromise = userIds.length
    ? prisma.talentAssessment.findMany({ where: { employeeId: { in: userIds }, isActive: true }, orderBy: [{ assessedAt: "desc" }] })
    : [];
  const roleWhere = scope.isAdmin
    ? {
        isActive: true,
        ...(payload.department ? { department: String(payload.department).trim() } : {}),
      }
    : {
        isActive: true,
        department: { in: departments.length ? departments : ["__NO_VISIBLE_DEPARTMENT__"] },
      };
  const rolesPromise = prisma.successionRole.findMany({
    where: roleWhere,
    include: {
      candidates: {
        where: { isActive: true, ...(userIds.length ? { employeeId: { in: userIds } } : { employeeId: "__NO_VISIBLE_EMPLOYEE__" }) },
        orderBy: [{ priority: "asc" }, { updatedAt: "desc" }],
      },
    },
    orderBy: [{ criticality: "desc" }, { department: "asc" }, { title: "asc" }],
    take: 1000,
  });

  const [dataset, skillMatrix, assessments, roles] = await Promise.all([datasetPromise, skillMatrixPromise, assessmentsPromise, rolesPromise]);
  const assessmentMap = new Map(assessments.map((item) => [item.employeeId, item]));
  const performanceMap = new Map((dataset.rows || []).map((row) => [row.id, row]));
  const skillMap = new Map((skillMatrix.rows || []).map((row) => [row.employeeId, row]));

  const involvedIds = new Set(userIds);
  if (scope.isAdmin) {
    for (const role of roles) {
      if (role.incumbentEmployeeId) involvedIds.add(role.incumbentEmployeeId);
      for (const candidate of role.candidates || []) involvedIds.add(candidate.employeeId);
    }
  }
  const involvedUsers = involvedIds.size
    ? await prisma.user.findMany({
        where: { id: { in: [...involvedIds] } },
        select: { id: true, name: true, department: true, jobTitle: true, avatarUrl: true, role: true },
      })
    : [];
  const userMap = new Map(involvedUsers.map((user) => [user.id, user]));

  const candidateRolesByEmployee = new Map();
  for (const role of roles) {
    for (const candidate of role.candidates || []) {
      if (!candidateRolesByEmployee.has(candidate.employeeId)) candidateRolesByEmployee.set(candidate.employeeId, []);
      candidateRolesByEmployee.get(candidate.employeeId).push({
        candidateId: candidate.id,
        roleId: role.id,
        roleTitle: role.title,
        roleDepartment: role.department,
        criticality: role.criticality,
        readiness: candidate.readiness,
        priority: candidate.priority,
        rationale: candidate.rationale,
        developmentPlanId: candidate.developmentPlanId,
      });
    }
  }

  const rows = scope.users.map((user) => {
    const performance = performanceMap.get(user.id) || null;
    const assessment = assessmentMap.get(user.id) || null;
    const skills = skillMap.get(user.id) || null;
    const performanceScore = performance?.performanceScore == null ? null : Number(performance.performanceScore);
    const performanceBand = talentPerformanceBand(performanceScore);
    const potentialLevel = assessment?.potentialLevel || null;
    const boxKey = potentialLevel ? talentBoxKey(potentialLevel, performanceBand) : null;
    return {
      employeeId: user.id,
      name: user.name,
      department: user.department,
      jobTitle: user.jobTitle,
      avatarUrl: user.avatarUrl,
      performanceScore,
      performanceStatus: performance?.status || "No Activity",
      performanceBand,
      potentialLevel,
      talentBox: boxKey,
      talentBoxLabel: boxKey ? talentBoxLabel(potentialLevel, performanceBand) : "Unclassified",
      potentialEvidence: assessment?.evidence || null,
      potentialManagerNote: assessment?.managerNote || null,
      potentialAssessedAt: assessment?.assessedAt || null,
      skillCoveragePercent: skills?.coveragePercent ?? null,
      criticalSkillGaps: Number(skills?.criticalGaps || 0),
      activeDevelopmentPlans: Number(skills?.activeDevelopmentPlans || 0),
      successionNominations: candidateRolesByEmployee.get(user.id) || [],
    };
  });

  const potentialOrder = ["HIGH", "MEDIUM", "LOW"];
  const performanceOrder = ["LOW", "MEDIUM", "HIGH"];
  const matrix = [];
  for (const potential of potentialOrder) {
    for (const performance of performanceOrder) {
      const employees = rows.filter((row) => row.potentialLevel === potential && row.performanceBand === performance);
      matrix.push({
        key: talentBoxKey(potential, performance),
        potential,
        performance,
        label: talentBoxLabel(potential, performance),
        employeeCount: employees.length,
        employees: employees.map((row) => ({ employeeId: row.employeeId, name: row.name, department: row.department, jobTitle: row.jobTitle, performanceScore: row.performanceScore })),
      });
    }
  }

  const enrichedRoles = roles.map((role) => {
    const candidates = (role.candidates || []).map((candidate) => ({
      ...candidate,
      employee: userMap.get(candidate.employeeId) || null,
    }));
    return {
      ...role,
      incumbent: role.incumbentEmployeeId ? (userMap.get(role.incumbentEmployeeId) || null) : null,
      candidates,
      benchDepth: candidates.length,
      readyNowCount: candidates.filter((candidate) => candidate.readiness === "READY_NOW").length,
      covered: candidates.length > 0,
      readyNowCovered: candidates.some((candidate) => candidate.readiness === "READY_NOW"),
    };
  });

  const criticalRoles = enrichedRoles.filter((role) => ["CRITICAL", "HIGH"].includes(role.criticality));
  const coveredCriticalRoles = criticalRoles.filter((role) => role.covered);
  const readyNowCandidates = enrichedRoles.reduce((sum, role) => sum + role.readyNowCount, 0);
  const assessedEmployees = rows.filter((row) => row.potentialLevel).length;
  const classifiedEmployees = rows.filter((row) => row.talentBox).length;

  return {
    generatedAt: new Date().toISOString(),
    methodology: {
      type: "MANAGER_ASSESSED_TALENT_MATRIX",
      performanceAxis: "Uses the existing Phase 3 Performance Score only: HIGH >=85, MEDIUM 70-84, LOW <70. No Activity stays unclassified.",
      potentialAxis: "Potential is explicitly assessed by an authorized manager/admin as LOW, MEDIUM, or HIGH. TOS does not infer potential from personal or sensitive attributes.",
      successionReadiness: "Readiness is an explicit manager nomination field. It is never auto-calculated from the 9-box, skills, or performance score.",
      decisionUse: "Decision-support only. The matrix does not automatically promote, demote, terminate, compensate, or reassign employees.",
    },
    period: { start: dataset.filters?.periodStart || null, end: dataset.filters?.periodEnd || null },
    summary: {
      employeeCount: rows.length,
      assessedEmployees,
      unassessedPotential: rows.length - assessedEmployees,
      classifiedEmployees,
      highPotentialEmployees: rows.filter((row) => row.potentialLevel === "HIGH").length,
      criticalRoles: criticalRoles.length,
      coveredCriticalRoles: coveredCriticalRoles.length,
      uncoveredCriticalRoles: criticalRoles.length - coveredCriticalRoles.length,
      readyNowCandidates,
      successionRoles: enrichedRoles.length,
    },
    matrix,
    rows,
    successionRoles: enrichedRoles,
  };
}

'''
text = text.replace(helper_anchor, helpers + helper_anchor, 1)

route_anchor = 'router.get("/reports/team-performance/workforce/forecast", asyncHandler(async (req, res) => {'
if route_anchor not in text:
    raise SystemExit("Phase 10 route anchor not found")

routes = r'''
router.get("/reports/team-performance/talent/overview", asyncHandler(async (req, res) => {
  const overview = await buildTalentOverview(req, {
    start: req.query.start,
    end: req.query.end,
    employeeId: req.query.employeeId || null,
    department: req.query.department || null,
  });
  res.json(overview);
}));

router.post("/reports/team-performance/talent/assessments", asyncHandler(async (req, res) => {
  assertTalentViewer(req);
  const employeeId = String(req.body?.employeeId || "").trim();
  if (!employeeId) throw new AppError("employeeId is required", 400);
  const { employee } = await assertTalentEmployeeAccess(req, employeeId);
  const potentialLevel = talentPotential(req.body?.potentialLevel);
  const existing = await prisma.talentAssessment.findUnique({ where: { employeeId } });
  const data = {
    potentialLevel,
    evidence: talentText(req.body?.evidence, 3000),
    managerNote: talentText(req.body?.managerNote, 3000),
    isActive: true,
    assessedById: req.user.id,
    assessedAt: new Date(),
    updatedById: req.user.id,
  };
  const assessment = existing
    ? await prisma.talentAssessment.update({ where: { employeeId }, data })
    : await prisma.talentAssessment.create({ data: { employeeId, ...data } });
  await auditTalentSuccession(req, existing ? "talent_assessment_updated" : "talent_assessment_created", {
    assessmentId: assessment.id,
    employeeId,
    employeeName: employee.name,
    potentialLevel,
  });
  res.status(existing ? 200 : 201).json({ ...assessment, employee });
}));

router.delete("/reports/team-performance/talent/assessments/:employeeId", asyncHandler(async (req, res) => {
  assertTalentViewer(req);
  await assertTalentEmployeeAccess(req, req.params.employeeId);
  const existing = await prisma.talentAssessment.findUnique({ where: { employeeId: req.params.employeeId } });
  if (!existing) throw new AppError("Talent assessment not found", 404);
  const assessment = await prisma.talentAssessment.update({ where: { id: existing.id }, data: { isActive: false, updatedById: req.user.id } });
  await auditTalentSuccession(req, "talent_assessment_deactivated", { assessmentId: assessment.id, employeeId: assessment.employeeId });
  res.json(assessment);
}));

router.get("/reports/team-performance/talent/succession-roles", asyncHandler(async (req, res) => {
  const scope = await getTalentScope(req, { department: req.query.department || null });
  const includeInactive = scope.isAdmin && req.query.includeInactive === "true";
  const departments = [...new Set(scope.users.map((user) => user.department).filter(Boolean))];
  const where = scope.isAdmin
    ? {
        ...(includeInactive ? {} : { isActive: true }),
        ...(req.query.department ? { department: String(req.query.department).trim() } : {}),
      }
    : {
        isActive: true,
        department: { in: departments.length ? departments : ["__NO_VISIBLE_DEPARTMENT__"] },
      };
  const roles = await prisma.successionRole.findMany({
    where,
    include: {
      candidates: {
        where: scope.isAdmin ? {} : { employeeId: { in: scope.userIds } },
        orderBy: [{ isActive: "desc" }, { priority: "asc" }, { updatedAt: "desc" }],
      },
    },
    orderBy: [{ isActive: "desc" }, { criticality: "desc" }, { department: "asc" }, { title: "asc" }],
    take: 1000,
  });
  const ids = new Set();
  for (const role of roles) {
    if (role.incumbentEmployeeId) ids.add(role.incumbentEmployeeId);
    for (const candidate of role.candidates || []) ids.add(candidate.employeeId);
  }
  const users = ids.size
    ? await prisma.user.findMany({ where: { id: { in: [...ids] } }, select: { id: true, name: true, department: true, jobTitle: true, avatarUrl: true } })
    : [];
  const userMap = new Map(users.map((user) => [user.id, user]));
  res.json({
    canConfigureRoles: scope.isAdmin,
    roles: roles.map((role) => ({
      ...role,
      incumbent: role.incumbentEmployeeId ? (userMap.get(role.incumbentEmployeeId) || null) : null,
      candidates: (role.candidates || []).map((candidate) => ({ ...candidate, employee: userMap.get(candidate.employeeId) || null })),
    })),
  });
}));

router.post("/reports/team-performance/talent/succession-roles", asyncHandler(async (req, res) => {
  assertTalentAdmin(req);
  const input = await normalizeSuccessionRoleInput(req.body || {});
  await assertNoDuplicateSuccessionRole(input);
  const role = await prisma.successionRole.create({ data: { ...input, createdById: req.user.id, updatedById: req.user.id } });
  await auditTalentSuccession(req, "succession_role_created", { roleId: role.id, title: role.title, department: role.department, criticality: role.criticality });
  res.status(201).json(role);
}));

router.patch("/reports/team-performance/talent/succession-roles/:roleId", asyncHandler(async (req, res) => {
  const existing = await loadSuccessionRoleForAccess(req, req.params.roleId, { requireAdmin: true, allowInactive: true });
  const input = await normalizeSuccessionRoleInput(req.body || {}, existing);
  await assertNoDuplicateSuccessionRole(input, existing.id);
  const role = await prisma.successionRole.update({ where: { id: existing.id }, data: { ...input, updatedById: req.user.id } });
  await auditTalentSuccession(req, "succession_role_updated", { roleId: role.id, title: role.title, isActive: role.isActive });
  res.json(role);
}));

router.delete("/reports/team-performance/talent/succession-roles/:roleId", asyncHandler(async (req, res) => {
  const existing = await loadSuccessionRoleForAccess(req, req.params.roleId, { requireAdmin: true, allowInactive: true });
  const role = await prisma.successionRole.update({ where: { id: existing.id }, data: { isActive: false, updatedById: req.user.id } });
  await prisma.successionCandidate.updateMany({ where: { roleId: role.id, isActive: true }, data: { isActive: false, updatedById: req.user.id } });
  await auditTalentSuccession(req, "succession_role_deactivated", { roleId: role.id });
  res.json(role);
}));

router.post("/reports/team-performance/talent/succession-roles/:roleId/candidates", asyncHandler(async (req, res) => {
  const role = await loadSuccessionRoleForAccess(req, req.params.roleId);
  const employeeId = String(req.body?.employeeId || "").trim();
  const existing = employeeId
    ? await prisma.successionCandidate.findUnique({ where: { roleId_employeeId: { roleId: role.id, employeeId } } })
    : null;
  const input = await normalizeSuccessionCandidateInput(req, role, req.body || {}, existing);
  const data = { ...input, isActive: true, updatedById: req.user.id };
  const candidate = existing
    ? await prisma.successionCandidate.update({ where: { id: existing.id }, data })
    : await prisma.successionCandidate.create({ data: { roleId: role.id, ...data, nominatedById: req.user.id } });
  await auditTalentSuccession(req, existing ? "succession_candidate_updated" : "succession_candidate_nominated", {
    roleId: role.id,
    candidateId: candidate.id,
    employeeId: candidate.employeeId,
    readiness: candidate.readiness,
  });
  res.status(existing ? 200 : 201).json(candidate);
}));

router.patch("/reports/team-performance/talent/succession-roles/:roleId/candidates/:candidateId", asyncHandler(async (req, res) => {
  const role = await loadSuccessionRoleForAccess(req, req.params.roleId);
  const existing = await prisma.successionCandidate.findUnique({ where: { id: req.params.candidateId } });
  if (!existing || existing.roleId !== role.id) throw new AppError("Succession candidate not found", 404);
  const input = await normalizeSuccessionCandidateInput(req, role, req.body || {}, existing);
  const candidate = await prisma.successionCandidate.update({ where: { id: existing.id }, data: { ...input, updatedById: req.user.id } });
  await auditTalentSuccession(req, "succession_candidate_updated", { roleId: role.id, candidateId: candidate.id, employeeId: candidate.employeeId, readiness: candidate.readiness });
  res.json(candidate);
}));

router.delete("/reports/team-performance/talent/succession-roles/:roleId/candidates/:candidateId", asyncHandler(async (req, res) => {
  const role = await loadSuccessionRoleForAccess(req, req.params.roleId);
  const existing = await prisma.successionCandidate.findUnique({ where: { id: req.params.candidateId } });
  if (!existing || existing.roleId !== role.id) throw new AppError("Succession candidate not found", 404);
  await assertTalentEmployeeAccess(req, existing.employeeId);
  const candidate = await prisma.successionCandidate.update({ where: { id: existing.id }, data: { isActive: false, updatedById: req.user.id } });
  await auditTalentSuccession(req, "succession_candidate_deactivated", { roleId: role.id, candidateId: candidate.id, employeeId: candidate.employeeId });
  res.json(candidate);
}));

'''
text = text.replace(route_anchor, routes + route_anchor, 1)
path.write_text(text)
print("BACKEND_TALENT_OVERVIEW=PASS")
print("BACKEND_TALENT_ASSESSMENTS=PASS")
print("BACKEND_SUCCESSION_ROLES=PASS")
print("BACKEND_SUCCESSION_CANDIDATES=PASS")
print("TALENT_DECISION_SUPPORT_GUARD=PASS")
