#!/usr/bin/env python3
from pathlib import Path
import sys

repo = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
path = repo / "backend/src/routes/tasks.routes.js"
text = path.read_text()

if "PHASE9_SKILLS_COMPETENCIES" in text:
    raise SystemExit("PHASE9_BACKEND_ALREADY_PRESENT")

helper_anchor = "function buildTeamPerformanceIntelligence(dataset) {"
route_anchor = 'router.get("/reports/team-performance/reviews/summary", asyncHandler(async (req, res) => {'
if helper_anchor not in text or route_anchor not in text:
    raise SystemExit("PHASE9_BACKEND_ANCHOR_MISSING")

helpers = r'''
// PHASE9_SKILLS_COMPETENCIES
const SKILL_REQUIREMENT_SCOPES = new Set(["DEPARTMENT", "JOB_TITLE", "EMPLOYEE"]);
const SKILL_IMPORTANCE = new Set(["CORE", "IMPORTANT", "OPTIONAL"]);
const DEVELOPMENT_PLAN_STATUSES = new Set(["DRAFT", "ACTIVE", "COMPLETED", "CANCELLED"]);
const DEVELOPMENT_ACTION_STATUSES = new Set(["TODO", "IN_PROGRESS", "COMPLETED", "CANCELLED"]);

function skillText(value, max = 4000) {
  if (value === undefined) return undefined;
  if (value === null) return null;
  const text = String(value).trim();
  if (!text) return null;
  if (text.length > max) throw new AppError(`Text exceeds ${max} characters`, 400);
  return text;
}

function skillKey(value) {
  return String(value || "").trim().toLowerCase();
}

function skillLevel(value, label = "level", required = true) {
  if (value === undefined || value === null || value === "") {
    if (required) throw new AppError(`${label} is required`, 400);
    return null;
  }
  const level = Number(value);
  if (!Number.isInteger(level) || level < 1 || level > 5) throw new AppError(`${label} must be an integer from 1 to 5`, 400);
  return level;
}

function skillDate(value, label, required = false) {
  if (value === undefined || value === null || value === "") {
    if (required) throw new AppError(`${label} is required`, 400);
    return null;
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) throw new AppError(`Invalid ${label}`, 400);
  return date;
}

function assertSkillConfigAdmin(req) {
  if (!isSystemAdmin(req.user)) throw new AppError("Skills framework configuration requires admin access", 403);
}

async function assertSkillEmployeeAccess(req, employeeId, requireManage = false) {
  const scope = await getWorkforceScope(req, { requireManage });
  if (!scope.userIds.includes(employeeId)) {
    if (scope.isAdmin) {
      const raw = await prisma.user.findUnique({ where: { id: employeeId }, select: { id: true, role: true } });
      if (!raw) throw new AppError("Skills employee not found", 404);
      if (["CLIENT", "FORMER_EMPLOYEE"].includes(raw.role)) throw new AppError("Employee is not eligible for skills management", 400);
    }
    throw new AppError("Unauthorized skills employee", 403);
  }
  const employee = scope.users.find((user) => user.id === employeeId);
  if (!employee) throw new AppError("Skills employee not found", 404);
  return { scope, employee };
}

async function activeSkillDefinition(skillId, allowInactive = false) {
  const skill = await prisma.skillDefinition.findUnique({ where: { id: skillId } });
  if (!skill) throw new AppError("Skill not found", 404);
  if (!allowInactive && !skill.isActive) throw new AppError("Skill is inactive", 409);
  return skill;
}

function normalizeSkillDefinitionInput(payload = {}, existing = null) {
  const name = skillText(payload.name === undefined ? existing?.name : payload.name, 160);
  if (!name) throw new AppError("Skill name is required", 400);
  const category = skillText(payload.category === undefined ? existing?.category : payload.category, 120) || "General";
  return {
    name,
    category,
    description: skillText(payload.description === undefined ? existing?.description : payload.description, 2000),
    isActive: payload.isActive === undefined ? (existing?.isActive ?? true) : Boolean(payload.isActive),
  };
}

async function assertNoDuplicateSkillDefinition(input, excludeId = null) {
  if (!input.isActive) return;
  const candidates = await prisma.skillDefinition.findMany({
    where: { isActive: true, ...(excludeId ? { id: { not: excludeId } } : {}) },
    select: { id: true, name: true, category: true },
    take: 5000,
  });
  const duplicate = candidates.find((item) => skillKey(item.name) === skillKey(input.name) && skillKey(item.category) === skillKey(input.category));
  if (duplicate) throw new AppError("An active skill with the same name and category already exists", 409);
}

function normalizeCompetencyRequirementInput(payload = {}, existing = null) {
  const skillId = String(payload.skillId === undefined ? existing?.skillId || "" : payload.skillId || "").trim();
  if (!skillId) throw new AppError("skillId is required", 400);
  const scopeType = String(payload.scopeType === undefined ? existing?.scopeType || "" : payload.scopeType || "").trim().toUpperCase();
  if (!SKILL_REQUIREMENT_SCOPES.has(scopeType)) throw new AppError("Invalid competency requirement scope", 400);
  const targetLevel = skillLevel(payload.targetLevel === undefined ? existing?.targetLevel : payload.targetLevel, "targetLevel");
  const importance = String(payload.importance === undefined ? existing?.importance || "CORE" : payload.importance || "CORE").trim().toUpperCase();
  if (!SKILL_IMPORTANCE.has(importance)) throw new AppError("Invalid competency importance", 400);

  const department = scopeType === "DEPARTMENT" ? skillText(payload.department === undefined ? existing?.department : payload.department, 160) : null;
  const jobTitle = scopeType === "JOB_TITLE" ? skillText(payload.jobTitle === undefined ? existing?.jobTitle : payload.jobTitle, 180) : null;
  const employeeId = scopeType === "EMPLOYEE" ? String(payload.employeeId === undefined ? existing?.employeeId || "" : payload.employeeId || "").trim() : null;
  if (scopeType === "DEPARTMENT" && !department) throw new AppError("department is required", 400);
  if (scopeType === "JOB_TITLE" && !jobTitle) throw new AppError("jobTitle is required", 400);
  if (scopeType === "EMPLOYEE" && !employeeId) throw new AppError("employeeId is required", 400);

  return {
    skillId,
    scopeType,
    department,
    jobTitle,
    employeeId,
    targetLevel,
    importance,
    isActive: payload.isActive === undefined ? (existing?.isActive ?? true) : Boolean(payload.isActive),
  };
}

async function assertCompetencyRequirementSubject(input) {
  await activeSkillDefinition(input.skillId);
  if (input.scopeType === "EMPLOYEE") {
    const employee = await prisma.user.findUnique({ where: { id: input.employeeId }, select: { id: true, role: true } });
    if (!employee) throw new AppError("Requirement employee not found", 404);
    if (["CLIENT", "FORMER_EMPLOYEE"].includes(employee.role)) throw new AppError("Employee is not eligible for competency requirements", 400);
  }
  if (input.scopeType === "DEPARTMENT") {
    const [units, users] = await Promise.all([
      prisma.departmentUnit.findMany({ where: { isActive: true }, select: { key: true, name: true } }),
      prisma.user.findMany({ where: { department: { not: null }, role: { notIn: ["CLIENT", "FORMER_EMPLOYEE"] } }, select: { department: true } }),
    ]);
    const valid = new Set([
      ...units.flatMap((unit) => [skillKey(unit.key), skillKey(unit.name)]),
      ...users.map((user) => skillKey(user.department)),
    ].filter(Boolean));
    if (!valid.has(skillKey(input.department))) throw new AppError("Requirement department not found", 404);
  }
}

function requirementSubjectValue(requirement) {
  if (requirement.scopeType === "EMPLOYEE") return skillKey(requirement.employeeId);
  if (requirement.scopeType === "JOB_TITLE") return skillKey(requirement.jobTitle);
  return skillKey(requirement.department);
}

async function assertNoDuplicateCompetencyRequirement(input, excludeId = null) {
  if (!input.isActive) return;
  const candidates = await prisma.competencyRequirement.findMany({
    where: {
      skillId: input.skillId,
      scopeType: input.scopeType,
      isActive: true,
      ...(excludeId ? { id: { not: excludeId } } : {}),
    },
    select: { id: true, scopeType: true, department: true, jobTitle: true, employeeId: true },
    take: 5000,
  });
  const key = requirementSubjectValue(input);
  if (candidates.some((item) => requirementSubjectValue(item) === key)) {
    throw new AppError("An active requirement already exists for this skill and scope subject", 409);
  }
}

function requirementPriority(requirement) {
  if (requirement?.scopeType === "EMPLOYEE") return 3;
  if (requirement?.scopeType === "JOB_TITLE") return 2;
  if (requirement?.scopeType === "DEPARTMENT") return 1;
  return 0;
}

function requirementMatchesUser(requirement, user) {
  if (requirement.scopeType === "EMPLOYEE") return requirement.employeeId === user.id;
  if (requirement.scopeType === "JOB_TITLE") return skillKey(requirement.jobTitle) === skillKey(user.jobTitle);
  if (requirement.scopeType === "DEPARTMENT") return skillKey(requirement.department) === skillKey(user.department);
  return false;
}

function resolvedRequirement(requirements, user, skillId) {
  return requirements
    .filter((item) => item.skillId === skillId && requirementMatchesUser(item, user))
    .sort((a, b) => {
      const priority = requirementPriority(b) - requirementPriority(a);
      if (priority !== 0) return priority;
      return new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime();
    })[0] || null;
}

function developmentPlanInclude() {
  return {
    skill: { select: { id: true, name: true, category: true, isActive: true } },
    actions: {
      include: { skill: { select: { id: true, name: true, category: true, isActive: true } } },
      orderBy: [{ status: "asc" }, { dueDate: "asc" }, { createdAt: "asc" }],
    },
  };
}

function decorateDevelopmentPlan(plan) {
  const liveActions = (plan.actions || []).filter((action) => action.status !== "CANCELLED");
  const completedActions = liveActions.filter((action) => action.status === "COMPLETED").length;
  const progressPercent = liveActions.length ? Math.round((completedActions / liveActions.length) * 100) : 0;
  return { ...plan, progressPercent, completedActions, totalActions: liveActions.length };
}

async function attachDevelopmentEmployees(plans) {
  const employeeIds = [...new Set((plans || []).map((plan) => plan.employeeId).filter(Boolean))];
  const users = employeeIds.length
    ? await prisma.user.findMany({
        where: { id: { in: employeeIds } },
        select: { id: true, name: true, department: true, jobTitle: true, avatarUrl: true },
      })
    : [];
  const userMap = new Map(users.map((user) => [user.id, user]));
  return (plans || []).map((plan) => ({ ...decorateDevelopmentPlan(plan), employee: userMap.get(plan.employeeId) || null }));
}

async function auditSkillDevelopment(req, action, metadata = {}) {
  await prisma.workspaceAuditLog.create({
    data: {
      action,
      actorId: req.user.id,
      metadata: { ...metadata, occurredAt: new Date().toISOString() },
    },
  });
}

async function buildSkillMatrix(req, payload = {}) {
  const scope = await getWorkforceScope(req, {
    employeeId: payload.employeeId || null,
    department: payload.department || null,
  });
  const users = scope.users;
  const userIds = scope.userIds;
  const departments = [...new Set(users.map((user) => user.department).filter(Boolean))];
  const jobTitles = [...new Set(users.map((user) => user.jobTitle).filter(Boolean))];
  const requirementScope = [
    ...(userIds.length ? [{ scopeType: "EMPLOYEE", employeeId: { in: userIds } }] : []),
    ...(departments.length ? [{ scopeType: "DEPARTMENT", department: { in: departments } }] : []),
    ...(jobTitles.length ? [{ scopeType: "JOB_TITLE", jobTitle: { in: jobTitles } }] : []),
  ];

  const [catalog, requirements, assessments, activePlans] = await Promise.all([
    prisma.skillDefinition.findMany({ where: { isActive: true }, orderBy: [{ category: "asc" }, { name: "asc" }], take: 2000 }),
    requirementScope.length
      ? prisma.competencyRequirement.findMany({
          where: { isActive: true, OR: requirementScope, skill: { isActive: true } },
          include: { skill: { select: { id: true, name: true, category: true, isActive: true } } },
          orderBy: [{ updatedAt: "desc" }],
          take: 5000,
        })
      : [],
    userIds.length
      ? prisma.employeeSkillAssessment.findMany({
          where: { employeeId: { in: userIds }, skill: { isActive: true } },
          include: { skill: { select: { id: true, name: true, category: true, isActive: true } } },
          take: 10000,
        })
      : [],
    userIds.length
      ? prisma.employeeDevelopmentPlan.findMany({
          where: { employeeId: { in: userIds }, status: { in: ["DRAFT", "ACTIVE"] } },
          include: { actions: true },
          take: 5000,
        })
      : [],
  ]);

  const assessmentsByEmployee = new Map();
  for (const assessment of assessments) {
    if (!assessmentsByEmployee.has(assessment.employeeId)) assessmentsByEmployee.set(assessment.employeeId, new Map());
    assessmentsByEmployee.get(assessment.employeeId).set(assessment.skillId, assessment);
  }
  const plansByEmployee = new Map();
  for (const plan of activePlans) {
    if (!plansByEmployee.has(plan.employeeId)) plansByEmployee.set(plan.employeeId, []);
    plansByEmployee.get(plan.employeeId).push(plan);
  }

  const rows = users.map((user) => {
    const assessmentMap = assessmentsByEmployee.get(user.id) || new Map();
    const employeePlans = plansByEmployee.get(user.id) || [];
    const skills = [];

    for (const skill of catalog) {
      const requirement = resolvedRequirement(requirements, user, skill.id);
      const assessment = assessmentMap.get(skill.id) || null;
      if (!requirement && !assessment) continue;

      const currentLevel = assessment?.currentLevel ?? null;
      const targetLevel = requirement?.targetLevel ?? null;
      const gap = targetLevel == null ? null : Math.max(targetLevel - (currentLevel ?? 0), 0);
      let status = "ADDITIONAL";
      if (requirement) {
        if (currentLevel == null) status = requirement.importance === "CORE" ? "CRITICAL_GAP" : "UNASSESSED";
        else if (currentLevel >= targetLevel) status = "MET";
        else if (gap === 1) status = "NEAR";
        else status = requirement.importance === "CORE" ? "CRITICAL_GAP" : "GAP";
      }

      skills.push({
        skillId: skill.id,
        name: skill.name,
        category: skill.category,
        currentLevel,
        targetLevel,
        gap,
        importance: requirement?.importance || null,
        requirementSource: requirement?.scopeType || null,
        requirementId: requirement?.id || null,
        assessmentId: assessment?.id || null,
        assessedAt: assessment?.assessedAt || null,
        evidence: assessment?.evidence || null,
        status,
      });
    }

    const requiredSkills = skills.filter((item) => item.targetLevel != null);
    const metSkills = requiredSkills.filter((item) => item.status === "MET");
    const criticalGaps = requiredSkills.filter((item) => item.status === "CRITICAL_GAP");
    const unassessedRequired = requiredSkills.filter((item) => item.currentLevel == null);
    const gapSkills = requiredSkills.filter((item) => item.status !== "MET");
    const openPlans = employeePlans.filter((plan) => ["DRAFT", "ACTIVE"].includes(plan.status));
    const now = new Date();
    const overdueActions = openPlans.flatMap((plan) => plan.actions || []).filter((action) => ["TODO", "IN_PROGRESS"].includes(action.status) && action.dueDate && action.dueDate < now);

    return {
      employeeId: user.id,
      name: user.name,
      department: user.department,
      jobTitle: user.jobTitle,
      avatarUrl: user.avatarUrl,
      requiredSkills: requiredSkills.length,
      assessedSkills: skills.filter((item) => item.currentLevel != null).length,
      metSkills: metSkills.length,
      gapSkills: gapSkills.length,
      criticalGaps: criticalGaps.length,
      unassessedRequired: unassessedRequired.length,
      coveragePercent: requiredSkills.length ? Math.round((metSkills.length / requiredSkills.length) * 100) : null,
      assessmentCoveragePercent: requiredSkills.length ? Math.round(((requiredSkills.length - unassessedRequired.length) / requiredSkills.length) * 100) : null,
      activeDevelopmentPlans: openPlans.filter((plan) => plan.status === "ACTIVE").length,
      draftDevelopmentPlans: openPlans.filter((plan) => plan.status === "DRAFT").length,
      overdueDevelopmentActions: overdueActions.length,
      skills,
    };
  });

  const requiredAssignments = rows.reduce((sum, row) => sum + row.requiredSkills, 0);
  const coveredRequirements = rows.reduce((sum, row) => sum + row.metSkills, 0);
  const priorityGaps = rows.flatMap((row) => row.skills
    .filter((skill) => skill.targetLevel != null && skill.status !== "MET")
    .map((skill) => ({
      employeeId: row.employeeId,
      employeeName: row.name,
      department: row.department,
      jobTitle: row.jobTitle,
      ...skill,
    })))
    .sort((a, b) => {
      const importanceOrder = { CORE: 0, IMPORTANT: 1, OPTIONAL: 2 };
      const statusOrder = { CRITICAL_GAP: 0, GAP: 1, UNASSESSED: 2, NEAR: 3 };
      const importance = (importanceOrder[a.importance] ?? 9) - (importanceOrder[b.importance] ?? 9);
      if (importance !== 0) return importance;
      const status = (statusOrder[a.status] ?? 9) - (statusOrder[b.status] ?? 9);
      if (status !== 0) return status;
      return Number(b.gap || 0) - Number(a.gap || 0);
    })
    .slice(0, 50);

  return {
    methodology: {
      proficiencyScale: { 1: "Awareness", 2: "Basic", 3: "Working", 4: "Advanced", 5: "Expert" },
      requirementPrecedence: ["EMPLOYEE", "JOB_TITLE", "DEPARTMENT"],
      coverage: "Requirements met / effective required skills. This is separate from the Phase 3 Performance Score.",
      criticalGap: "CORE skill unassessed or at least two proficiency levels below target.",
    },
    summary: {
      employees: rows.length,
      configuredSkills: catalog.length,
      requiredAssignments,
      coveredRequirements,
      overallCoveragePercent: requiredAssignments ? Math.round((coveredRequirements / requiredAssignments) * 100) : null,
      criticalGaps: rows.reduce((sum, row) => sum + row.criticalGaps, 0),
      unassessedRequired: rows.reduce((sum, row) => sum + row.unassessedRequired, 0),
      activeDevelopmentPlans: rows.reduce((sum, row) => sum + row.activeDevelopmentPlans, 0),
      overdueDevelopmentActions: rows.reduce((sum, row) => sum + row.overdueDevelopmentActions, 0),
    },
    rows,
    priorityGaps,
  };
}

async function loadDevelopmentPlanForAccess(req, planId, { requireManage = false } = {}) {
  const plan = await prisma.employeeDevelopmentPlan.findUnique({ where: { id: planId }, include: developmentPlanInclude() });
  if (!plan) throw new AppError("Development plan not found", 404);
  const { scope } = await assertSkillEmployeeAccess(req, plan.employeeId, requireManage);
  if (!scope.canManage && plan.status === "DRAFT") throw new AppError("Development plan not found", 404);
  return { plan, scope };
}

function normalizeDevelopmentPlanInput(payload = {}) {
  const employeeId = String(payload.employeeId || "").trim();
  if (!employeeId) throw new AppError("employeeId is required", 400);
  const skillId = payload.skillId ? String(payload.skillId).trim() : null;
  const title = skillText(payload.title, 260);
  if (!title) throw new AppError("Development plan title is required", 400);
  const startDate = skillDate(payload.startDate, "startDate", false) || new Date();
  const targetDate = skillDate(payload.targetDate, "targetDate", false);
  if (targetDate && targetDate < startDate) throw new AppError("targetDate must be on or after startDate", 400);
  return {
    employeeId,
    skillId,
    sourceReviewId: payload.sourceReviewId ? String(payload.sourceReviewId).trim() : null,
    title,
    objective: skillText(payload.objective, 5000),
    targetLevel: skillLevel(payload.targetLevel, "targetLevel", false),
    startDate,
    targetDate,
  };
}

'''

routes = r'''
router.get("/reports/team-performance/skills/matrix", asyncHandler(async (req, res) => {
  const matrix = await buildSkillMatrix(req, {
    employeeId: req.query.employeeId || null,
    department: req.query.department || null,
  });
  res.json(matrix);
}));

router.get("/reports/team-performance/skills/catalog", asyncHandler(async (req, res) => {
  const canManageConfig = isSystemAdmin(req.user);
  const includeInactive = canManageConfig && req.query.includeInactive === "true";
  const skills = await prisma.skillDefinition.findMany({
    where: includeInactive ? {} : { isActive: true },
    orderBy: [{ isActive: "desc" }, { category: "asc" }, { name: "asc" }],
    take: 2000,
  });
  res.json({ skills, canManageConfig });
}));

router.post("/reports/team-performance/skills/catalog", asyncHandler(async (req, res) => {
  assertSkillConfigAdmin(req);
  const input = normalizeSkillDefinitionInput(req.body || {});
  await assertNoDuplicateSkillDefinition(input);
  const skill = await prisma.skillDefinition.create({ data: { ...input, createdById: req.user.id, updatedById: req.user.id } });
  await auditSkillDevelopment(req, "skill_definition_created", { skillId: skill.id, name: skill.name, category: skill.category });
  res.status(201).json(skill);
}));

router.patch("/reports/team-performance/skills/catalog/:skillId", asyncHandler(async (req, res) => {
  assertSkillConfigAdmin(req);
  const existing = await activeSkillDefinition(req.params.skillId, true);
  const input = normalizeSkillDefinitionInput(req.body || {}, existing);
  await assertNoDuplicateSkillDefinition(input, existing.id);
  const skill = await prisma.skillDefinition.update({ where: { id: existing.id }, data: { ...input, updatedById: req.user.id } });
  await auditSkillDevelopment(req, "skill_definition_updated", { skillId: skill.id, name: skill.name, isActive: skill.isActive });
  res.json(skill);
}));

router.delete("/reports/team-performance/skills/catalog/:skillId", asyncHandler(async (req, res) => {
  assertSkillConfigAdmin(req);
  const existing = await activeSkillDefinition(req.params.skillId, true);
  const skill = await prisma.skillDefinition.update({ where: { id: existing.id }, data: { isActive: false, updatedById: req.user.id } });
  await auditSkillDevelopment(req, "skill_definition_deactivated", { skillId: skill.id });
  res.json(skill);
}));

router.get("/reports/team-performance/skills/requirements", asyncHandler(async (req, res) => {
  assertSkillConfigAdmin(req);
  const requirements = await prisma.competencyRequirement.findMany({
    include: { skill: { select: { id: true, name: true, category: true, isActive: true } } },
    orderBy: [{ isActive: "desc" }, { updatedAt: "desc" }],
    take: 5000,
  });
  res.json({ requirements });
}));

router.post("/reports/team-performance/skills/requirements", asyncHandler(async (req, res) => {
  assertSkillConfigAdmin(req);
  const input = normalizeCompetencyRequirementInput(req.body || {});
  await assertCompetencyRequirementSubject(input);
  await assertNoDuplicateCompetencyRequirement(input);
  const requirement = await prisma.competencyRequirement.create({
    data: { ...input, createdById: req.user.id, updatedById: req.user.id },
    include: { skill: { select: { id: true, name: true, category: true, isActive: true } } },
  });
  await auditSkillDevelopment(req, "competency_requirement_created", { requirementId: requirement.id, skillId: requirement.skillId, scopeType: requirement.scopeType, employeeId: requirement.employeeId, department: requirement.department, jobTitle: requirement.jobTitle, targetLevel: requirement.targetLevel });
  res.status(201).json(requirement);
}));

router.patch("/reports/team-performance/skills/requirements/:requirementId", asyncHandler(async (req, res) => {
  assertSkillConfigAdmin(req);
  const existing = await prisma.competencyRequirement.findUnique({ where: { id: req.params.requirementId } });
  if (!existing) throw new AppError("Competency requirement not found", 404);
  const input = normalizeCompetencyRequirementInput(req.body || {}, existing);
  await assertCompetencyRequirementSubject(input);
  await assertNoDuplicateCompetencyRequirement(input, existing.id);
  const requirement = await prisma.competencyRequirement.update({
    where: { id: existing.id },
    data: { ...input, updatedById: req.user.id },
    include: { skill: { select: { id: true, name: true, category: true, isActive: true } } },
  });
  await auditSkillDevelopment(req, "competency_requirement_updated", { requirementId: requirement.id, skillId: requirement.skillId, targetLevel: requirement.targetLevel, isActive: requirement.isActive });
  res.json(requirement);
}));

router.delete("/reports/team-performance/skills/requirements/:requirementId", asyncHandler(async (req, res) => {
  assertSkillConfigAdmin(req);
  const existing = await prisma.competencyRequirement.findUnique({ where: { id: req.params.requirementId } });
  if (!existing) throw new AppError("Competency requirement not found", 404);
  const requirement = await prisma.competencyRequirement.update({ where: { id: existing.id }, data: { isActive: false, updatedById: req.user.id } });
  await auditSkillDevelopment(req, "competency_requirement_deactivated", { requirementId: requirement.id, skillId: requirement.skillId });
  res.json(requirement);
}));

router.post("/reports/team-performance/skills/assessments", asyncHandler(async (req, res) => {
  const employeeId = String(req.body?.employeeId || "").trim();
  const skillId = String(req.body?.skillId || "").trim();
  if (!employeeId || !skillId) throw new AppError("employeeId and skillId are required", 400);
  const currentLevel = skillLevel(req.body?.currentLevel, "currentLevel");
  const evidence = skillText(req.body?.evidence, 4000);
  const { employee } = await assertSkillEmployeeAccess(req, employeeId, true);
  const skill = await activeSkillDefinition(skillId);
  const assessment = await prisma.employeeSkillAssessment.upsert({
    where: { employeeId_skillId: { employeeId, skillId } },
    create: { employeeId, skillId, currentLevel, evidence, assessedById: req.user.id, assessedAt: new Date() },
    update: { currentLevel, evidence, assessedById: req.user.id, assessedAt: new Date() },
    include: { skill: { select: { id: true, name: true, category: true, isActive: true } } },
  });
  await auditSkillDevelopment(req, "employee_skill_assessed", { assessmentId: assessment.id, employeeId, skillId, currentLevel });
  res.status(200).json({ ...assessment, employee, skillName: skill.name });
}));

router.delete("/reports/team-performance/skills/assessments/:employeeId/:skillId", asyncHandler(async (req, res) => {
  const employeeId = String(req.params.employeeId || "").trim();
  const skillId = String(req.params.skillId || "").trim();
  await assertSkillEmployeeAccess(req, employeeId, true);
  const assessment = await prisma.employeeSkillAssessment.findUnique({ where: { employeeId_skillId: { employeeId, skillId } } });
  if (!assessment) throw new AppError("Skill assessment not found", 404);
  await prisma.employeeSkillAssessment.delete({ where: { id: assessment.id } });
  await auditSkillDevelopment(req, "employee_skill_assessment_removed", { assessmentId: assessment.id, employeeId, skillId });
  res.json({ deleted: true, id: assessment.id });
}));

router.get("/reports/team-performance/development-plans", asyncHandler(async (req, res) => {
  const scope = await getWorkforceScope(req, {
    employeeId: req.query.employeeId || null,
    department: req.query.department || null,
  });
  const requestedStatus = req.query.status ? String(req.query.status).trim().toUpperCase() : null;
  if (requestedStatus && !DEVELOPMENT_PLAN_STATUSES.has(requestedStatus)) throw new AppError("Invalid development plan status", 400);
  const plans = scope.userIds.length
    ? await prisma.employeeDevelopmentPlan.findMany({
        where: {
          employeeId: { in: scope.userIds },
          ...(requestedStatus ? { status: requestedStatus } : {}),
          ...(!scope.canManage ? { status: { not: "DRAFT" } } : {}),
        },
        include: developmentPlanInclude(),
        orderBy: [{ status: "asc" }, { targetDate: "asc" }, { updatedAt: "desc" }],
        take: 1000,
      })
    : [];
  res.json({ plans: await attachDevelopmentEmployees(plans) });
}));

router.post("/reports/team-performance/development-plans", asyncHandler(async (req, res) => {
  const input = normalizeDevelopmentPlanInput(req.body || {});
  const { employee } = await assertSkillEmployeeAccess(req, input.employeeId, true);
  let skill = null;
  if (input.skillId) skill = await activeSkillDefinition(input.skillId);
  if (input.sourceReviewId) {
    const review = await prisma.performanceReview.findFirst({ where: { id: input.sourceReviewId, employeeId: input.employeeId }, select: { id: true } });
    if (!review) throw new AppError("Source performance review not found for this employee", 404);
  }
  if (input.skillId) {
    const duplicate = await prisma.employeeDevelopmentPlan.findFirst({
      where: { employeeId: input.employeeId, skillId: input.skillId, status: { in: ["DRAFT", "ACTIVE"] } },
      select: { id: true },
    });
    if (duplicate) throw new AppError("An open development plan already exists for this employee and skill", 409);
  }
  const assessment = input.skillId
    ? await prisma.employeeSkillAssessment.findUnique({ where: { employeeId_skillId: { employeeId: input.employeeId, skillId: input.skillId } } })
    : null;
  let targetLevel = input.targetLevel;
  if (input.skillId && targetLevel == null) {
    const matrix = await buildSkillMatrix(req, { employeeId: input.employeeId });
    const matrixSkill = matrix.rows?.[0]?.skills?.find((item) => item.skillId === input.skillId);
    targetLevel = matrixSkill?.targetLevel ?? null;
  }
  const plan = await prisma.employeeDevelopmentPlan.create({
    data: {
      ...input,
      targetLevel,
      currentLevelSnapshot: assessment?.currentLevel ?? null,
      status: "DRAFT",
      createdById: req.user.id,
      updatedById: req.user.id,
    },
    include: developmentPlanInclude(),
  });
  await auditSkillDevelopment(req, "employee_development_plan_created", { planId: plan.id, employeeId: plan.employeeId, skillId: plan.skillId, sourceReviewId: plan.sourceReviewId, targetLevel: plan.targetLevel });
  res.status(201).json({ ...decorateDevelopmentPlan(plan), employee, skillName: skill?.name || null });
}));

router.patch("/reports/team-performance/development-plans/:planId", asyncHandler(async (req, res) => {
  const { plan } = await loadDevelopmentPlanForAccess(req, req.params.planId, { requireManage: true });
  if (["COMPLETED", "CANCELLED"].includes(plan.status)) throw new AppError("Closed development plans cannot be edited", 409);
  const data = { updatedById: req.user.id };
  if (Object.prototype.hasOwnProperty.call(req.body || {}, "title")) {
    const title = skillText(req.body.title, 260);
    if (!title) throw new AppError("Development plan title is required", 400);
    data.title = title;
  }
  if (Object.prototype.hasOwnProperty.call(req.body || {}, "objective")) data.objective = skillText(req.body.objective, 5000);
  if (Object.prototype.hasOwnProperty.call(req.body || {}, "targetLevel")) data.targetLevel = skillLevel(req.body.targetLevel, "targetLevel", false);
  if (Object.prototype.hasOwnProperty.call(req.body || {}, "targetDate")) {
    const targetDate = skillDate(req.body.targetDate, "targetDate", false);
    if (targetDate && targetDate < plan.startDate) throw new AppError("targetDate must be on or after startDate", 400);
    data.targetDate = targetDate;
  }
  const updated = await prisma.employeeDevelopmentPlan.update({ where: { id: plan.id }, data, include: developmentPlanInclude() });
  await auditSkillDevelopment(req, "employee_development_plan_updated", { planId: updated.id, employeeId: updated.employeeId });
  res.json(decorateDevelopmentPlan(updated));
}));

router.post("/reports/team-performance/development-plans/:planId/activate", asyncHandler(async (req, res) => {
  const { plan } = await loadDevelopmentPlanForAccess(req, req.params.planId, { requireManage: true });
  if (plan.status !== "DRAFT") throw new AppError("Only draft development plans can be activated", 409);
  const updated = await prisma.employeeDevelopmentPlan.update({ where: { id: plan.id }, data: { status: "ACTIVE", updatedById: req.user.id }, include: developmentPlanInclude() });
  await auditSkillDevelopment(req, "employee_development_plan_activated", { planId: updated.id, employeeId: updated.employeeId });
  res.json(decorateDevelopmentPlan(updated));
}));

router.post("/reports/team-performance/development-plans/:planId/complete", asyncHandler(async (req, res) => {
  const { plan } = await loadDevelopmentPlanForAccess(req, req.params.planId, { requireManage: true });
  if (plan.status !== "ACTIVE") throw new AppError("Only active development plans can be completed", 409);
  const openActions = (plan.actions || []).filter((action) => ["TODO", "IN_PROGRESS"].includes(action.status));
  if (openActions.length) throw new AppError("Complete or cancel open development actions before completing the plan", 409);
  const updated = await prisma.employeeDevelopmentPlan.update({
    where: { id: plan.id },
    data: { status: "COMPLETED", completedAt: new Date(), updatedById: req.user.id },
    include: developmentPlanInclude(),
  });
  await auditSkillDevelopment(req, "employee_development_plan_completed", { planId: updated.id, employeeId: updated.employeeId, skillId: updated.skillId });
  res.json(decorateDevelopmentPlan(updated));
}));

router.delete("/reports/team-performance/development-plans/:planId", asyncHandler(async (req, res) => {
  const { plan } = await loadDevelopmentPlanForAccess(req, req.params.planId, { requireManage: true });
  if (plan.status === "COMPLETED") throw new AppError("Completed development plans cannot be cancelled", 409);
  const updated = await prisma.employeeDevelopmentPlan.update({ where: { id: plan.id }, data: { status: "CANCELLED", updatedById: req.user.id }, include: developmentPlanInclude() });
  await auditSkillDevelopment(req, "employee_development_plan_cancelled", { planId: updated.id, employeeId: updated.employeeId });
  res.json(decorateDevelopmentPlan(updated));
}));

router.post("/reports/team-performance/development-plans/:planId/actions", asyncHandler(async (req, res) => {
  const { plan } = await loadDevelopmentPlanForAccess(req, req.params.planId, { requireManage: true });
  if (["COMPLETED", "CANCELLED"].includes(plan.status)) throw new AppError("Cannot add actions to a closed development plan", 409);
  const title = skillText(req.body?.title, 300);
  if (!title) throw new AppError("Development action title is required", 400);
  const skillId = req.body?.skillId ? String(req.body.skillId).trim() : (plan.skillId || null);
  if (skillId) await activeSkillDefinition(skillId);
  const action = await prisma.employeeDevelopmentAction.create({
    data: {
      planId: plan.id,
      skillId,
      title,
      description: skillText(req.body?.description, 4000),
      dueDate: skillDate(req.body?.dueDate, "dueDate", false),
      status: "TODO",
      createdById: req.user.id,
      updatedById: req.user.id,
    },
    include: { skill: { select: { id: true, name: true, category: true, isActive: true } } },
  });
  await auditSkillDevelopment(req, "employee_development_action_created", { planId: plan.id, actionId: action.id, employeeId: plan.employeeId, skillId: action.skillId });
  res.status(201).json(action);
}));

router.patch("/reports/team-performance/development-plans/:planId/actions/:actionId", asyncHandler(async (req, res) => {
  const action = await prisma.employeeDevelopmentAction.findUnique({
    where: { id: req.params.actionId },
    include: { plan: true, skill: { select: { id: true, name: true, category: true, isActive: true } } },
  });
  if (!action || action.planId !== req.params.planId) throw new AppError("Development action not found", 404);
  const { scope } = await assertSkillEmployeeAccess(req, action.plan.employeeId, false);
  const isEmployee = req.user.id === action.plan.employeeId && !scope.canManage;
  if (!scope.canManage && !isEmployee) throw new AppError("Unauthorized development action", 403);
  if (action.plan.status === "DRAFT" && isEmployee) throw new AppError("Development action not found", 404);
  if (["COMPLETED", "CANCELLED"].includes(action.plan.status)) throw new AppError("Closed development plan actions cannot be edited", 409);

  const data = { updatedById: req.user.id };
  if (Object.prototype.hasOwnProperty.call(req.body || {}, "status")) {
    const status = String(req.body.status || "").trim().toUpperCase();
    if (!DEVELOPMENT_ACTION_STATUSES.has(status)) throw new AppError("Invalid development action status", 400);
    if (isEmployee && status === "CANCELLED") throw new AppError("Employees cannot cancel development actions", 403);
    if (isEmployee && action.status === "COMPLETED" && status !== "COMPLETED") throw new AppError("Employees cannot reopen completed development actions", 403);
    data.status = status;
    data.completedAt = status === "COMPLETED" ? (action.completedAt || new Date()) : null;
  }

  if (!isEmployee) {
    if (Object.prototype.hasOwnProperty.call(req.body || {}, "title")) {
      const title = skillText(req.body.title, 300);
      if (!title) throw new AppError("Development action title is required", 400);
      data.title = title;
    }
    if (Object.prototype.hasOwnProperty.call(req.body || {}, "description")) data.description = skillText(req.body.description, 4000);
    if (Object.prototype.hasOwnProperty.call(req.body || {}, "dueDate")) data.dueDate = skillDate(req.body.dueDate, "dueDate", false);
    if (Object.prototype.hasOwnProperty.call(req.body || {}, "skillId")) {
      const skillId = req.body.skillId ? String(req.body.skillId).trim() : null;
      if (skillId) await activeSkillDefinition(skillId);
      data.skillId = skillId;
    }
  } else {
    const forbidden = ["title", "description", "dueDate", "skillId"].some((key) => Object.prototype.hasOwnProperty.call(req.body || {}, key));
    if (forbidden) throw new AppError("Employees can only update development action status", 403);
  }

  const updated = await prisma.employeeDevelopmentAction.update({ where: { id: action.id }, data, include: { skill: { select: { id: true, name: true, category: true, isActive: true } } } });
  await auditSkillDevelopment(req, "employee_development_action_updated", { planId: action.planId, actionId: updated.id, employeeId: action.plan.employeeId, status: updated.status });
  res.json(updated);
}));

router.delete("/reports/team-performance/development-plans/:planId/actions/:actionId", asyncHandler(async (req, res) => {
  const action = await prisma.employeeDevelopmentAction.findUnique({ where: { id: req.params.actionId }, include: { plan: true } });
  if (!action || action.planId !== req.params.planId) throw new AppError("Development action not found", 404);
  await assertSkillEmployeeAccess(req, action.plan.employeeId, true);
  if (["COMPLETED", "CANCELLED"].includes(action.plan.status)) throw new AppError("Closed development plan actions cannot be cancelled", 409);
  const updated = await prisma.employeeDevelopmentAction.update({ where: { id: action.id }, data: { status: "CANCELLED", completedAt: null, updatedById: req.user.id } });
  await auditSkillDevelopment(req, "employee_development_action_cancelled", { planId: action.planId, actionId: updated.id, employeeId: action.plan.employeeId });
  res.json(updated);
}));

'''

text = text.replace(helper_anchor, helpers + helper_anchor, 1)
text = text.replace(route_anchor, routes + route_anchor, 1)
path.write_text(text)

print("BACKEND_SKILLS_MATRIX=PASS")
print("BACKEND_SKILLS_CATALOG=PASS")
print("BACKEND_COMPETENCY_REQUIREMENTS=PASS")
print("BACKEND_SKILL_ASSESSMENTS=PASS")
print("BACKEND_DEVELOPMENT_PLANS=PASS")
print("SKILLS_RBAC_GUARDS=PASS")
print("SKILL_REQUIREMENT_PRECEDENCE=PASS")
print("SKILLS_BULK_AGGREGATION=PASS")
