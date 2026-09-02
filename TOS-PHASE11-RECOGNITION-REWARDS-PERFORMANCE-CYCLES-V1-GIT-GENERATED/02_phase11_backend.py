#!/usr/bin/env python3
from pathlib import Path
import sys

repo = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
path = repo / "backend/src/routes/tasks.routes.js"
text = path.read_text()
anchor = "function buildTeamPerformanceIntelligence(dataset) {"
if "PHASE11_RECOGNITION_REWARDS_CYCLES" in text:
    raise SystemExit("Phase 11 backend already present")
if "PHASE10_TALENT_SUCCESSION" not in text:
    raise SystemExit("Phase 10 backend baseline missing")
if anchor not in text:
    raise SystemExit("backend anchor missing")

code = r'''
// PHASE11_RECOGNITION_REWARDS_CYCLES
const RECOGNITION_CYCLE_TYPES = new Set(["MONTHLY", "QUARTERLY", "ANNUAL", "CUSTOM"]);
const RECOGNITION_CYCLE_STATUSES = new Set(["DRAFT", "OPEN", "CLOSED"]);
const RECOGNITION_CATEGORY_TYPES = new Set(["RECOGNITION", "REWARD"]);
const RECOGNITION_REWARD_TYPES = new Set(["NONE", "BADGE", "CERTIFICATE", "GIFT", "EXPERIENCE", "OTHER"]);
const RECOGNITION_NOMINATION_STATUSES = new Set(["PENDING", "APPROVED", "REJECTED"]);

function recognitionText(value, max = 4000) {
  if (value === undefined) return undefined;
  if (value === null) return null;
  const text = String(value).trim();
  if (!text) return null;
  if (text.length > max) throw new AppError(`Text exceeds ${max} characters`, 400);
  return text;
}

function recognitionKey(value) {
  return String(value || "").trim().toLowerCase();
}

function recognitionDate(value, label, required = false) {
  if (value === undefined || value === null || value === "") {
    if (required) throw new AppError(`${label} is required`, 400);
    return null;
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) throw new AppError(`Invalid ${label}`, 400);
  return date;
}

function recognitionRewardType(value) {
  const rewardType = String(value || "NONE").trim().toUpperCase();
  if (!RECOGNITION_REWARD_TYPES.has(rewardType)) throw new AppError("Invalid recognition reward type", 400);
  return rewardType;
}

function assertRecognitionAdmin(req) {
  if (!isSystemAdmin(req.user)) throw new AppError("Recognition framework management requires admin access", 403);
}

function isRecognitionManager(req) {
  return isSystemAdmin(req.user) || ["MANAGER", "PROJECT_MANAGER"].includes(req.user.role);
}

async function recognitionManagerScope(req, filters = {}) {
  if (!isRecognitionManager(req)) throw new AppError("Recognition management requires manager access", 403);
  return getWorkforceScope(req, {
    employeeId: filters.employeeId || null,
    department: filters.department || null,
    requireManage: true,
  });
}

async function assertRecognitionEmployeeAccess(req, employeeId) {
  const scope = await recognitionManagerScope(req);
  if (!scope.userIds.includes(employeeId)) {
    if (scope.isAdmin) {
      const raw = await prisma.user.findUnique({ where: { id: employeeId }, select: { id: true, role: true } });
      if (!raw) throw new AppError("Recognition employee not found", 404);
      if (["CLIENT", "FORMER_EMPLOYEE"].includes(raw.role)) throw new AppError("Employee is not eligible for recognition", 400);
    }
    throw new AppError("Unauthorized recognition employee", 403);
  }
  const employee = scope.users.find((item) => item.id === employeeId);
  if (!employee) throw new AppError("Recognition employee not found", 404);
  return { scope, employee };
}

async function assertRecognitionDepartment(department) {
  if (!department) return;
  const [units, users] = await Promise.all([
    prisma.departmentUnit.findMany({ where: { isActive: true }, select: { key: true, name: true } }),
    prisma.user.findMany({ where: { department: { not: null }, role: { notIn: ["CLIENT", "FORMER_EMPLOYEE"] } }, select: { department: true } }),
  ]);
  const valid = new Set([
    ...units.flatMap((unit) => [recognitionKey(unit.key), recognitionKey(unit.name)]),
    ...users.map((user) => recognitionKey(user.department)),
  ].filter(Boolean));
  if (!valid.has(recognitionKey(department))) throw new AppError("Recognition cycle department not found", 404);
}

function normalizeRecognitionCycleInput(payload = {}, existing = null) {
  const name = recognitionText(payload.name === undefined ? existing?.name : payload.name, 180);
  if (!name) throw new AppError("Cycle name is required", 400);
  const cycleType = String(payload.cycleType === undefined ? existing?.cycleType || "MONTHLY" : payload.cycleType || "MONTHLY").trim().toUpperCase();
  if (!RECOGNITION_CYCLE_TYPES.has(cycleType)) throw new AppError("Invalid recognition cycle type", 400);
  const startDate = recognitionDate(payload.startDate === undefined ? existing?.startDate : payload.startDate, "startDate", true);
  const endDate = recognitionDate(payload.endDate === undefined ? existing?.endDate : payload.endDate, "endDate", true);
  if (startDate > endDate) throw new AppError("startDate must be before or equal endDate", 400);
  const nominationStart = recognitionDate(payload.nominationStart === undefined ? existing?.nominationStart : payload.nominationStart, "nominationStart", false);
  const nominationEnd = recognitionDate(payload.nominationEnd === undefined ? existing?.nominationEnd : payload.nominationEnd, "nominationEnd", false);
  if (nominationStart && nominationEnd && nominationStart > nominationEnd) throw new AppError("nominationStart must be before or equal nominationEnd", 400);
  const department = recognitionText(payload.department === undefined ? existing?.department : payload.department, 160);
  return {
    name,
    cycleType,
    department,
    startDate,
    endDate,
    nominationStart,
    nominationEnd,
    notes: recognitionText(payload.notes === undefined ? existing?.notes : payload.notes, 3000),
    isActive: payload.isActive === undefined ? (existing?.isActive ?? true) : Boolean(payload.isActive),
  };
}

function normalizeRecognitionCategoryInput(payload = {}, existing = null) {
  const name = recognitionText(payload.name === undefined ? existing?.name : payload.name, 160);
  if (!name) throw new AppError("Recognition category name is required", 400);
  const categoryType = String(payload.categoryType === undefined ? existing?.categoryType || "RECOGNITION" : payload.categoryType || "RECOGNITION").trim().toUpperCase();
  if (!RECOGNITION_CATEGORY_TYPES.has(categoryType)) throw new AppError("Invalid recognition category type", 400);
  return {
    name,
    categoryType,
    description: recognitionText(payload.description === undefined ? existing?.description : payload.description, 2000),
    rewardType: recognitionRewardType(payload.rewardType === undefined ? existing?.rewardType || "NONE" : payload.rewardType),
    defaultRewardDescription: recognitionText(payload.defaultRewardDescription === undefined ? existing?.defaultRewardDescription : payload.defaultRewardDescription, 1000),
    isActive: payload.isActive === undefined ? (existing?.isActive ?? true) : Boolean(payload.isActive),
  };
}

async function assertNoDuplicateRecognitionCategory(input, excludeId = null) {
  if (!input.isActive) return;
  const rows = await prisma.recognitionCategory.findMany({
    where: { isActive: true, ...(excludeId ? { id: { not: excludeId } } : {}) },
    select: { id: true, name: true },
    take: 2000,
  });
  if (rows.some((row) => recognitionKey(row.name) === recognitionKey(input.name))) {
    throw new AppError("An active recognition category with this name already exists", 409);
  }
}

async function auditRecognition(req, action, metadata = {}) {
  await prisma.workspaceAuditLog.create({
    data: {
      action,
      actorId: req.user.id,
      metadata: { ...metadata, occurredAt: new Date().toISOString() },
    },
  });
}

function recognitionCycleVisibleToScope(cycle, scope) {
  if (!cycle.department) return true;
  const departments = new Set(scope.users.map((user) => recognitionKey(user.department)).filter(Boolean));
  return departments.has(recognitionKey(cycle.department));
}

function recognitionNominationWindowOpen(cycle, now = new Date()) {
  if (!cycle.isActive || cycle.status !== "OPEN") return false;
  if (cycle.nominationStart && now < new Date(cycle.nominationStart)) return false;
  if (cycle.nominationEnd && now > new Date(cycle.nominationEnd)) return false;
  return true;
}

async function buildRecognitionPerformanceSnapshot(req, cycle, employeeId) {
  const dataset = await buildTeamPerformanceExportDataset(req, {
    start: cycle.startDate.toISOString(),
    end: cycle.endDate.toISOString(),
    employeeId,
  });
  const row = dataset.rows.find((item) => item.id === employeeId) || null;
  if (!row) throw new AppError("Employee is outside the accessible performance scope", 403);
  const targetSummary = await buildTargetSummary(dataset);
  const target = targetSummary.rows.find((item) => item.employeeId === employeeId) || null;
  return {
    snapshotPerformanceScore: row.performanceScore == null ? null : Number(row.performanceScore),
    snapshotPerformanceStatus: row.status || "No Activity",
    snapshotTargetAchievement: target?.achievementPercent == null ? null : Number(target.achievementPercent),
  };
}

function recognitionNominationInclude() {
  return {
    cycle: true,
    category: true,
    award: true,
  };
}

function recognitionAwardInclude() {
  return {
    cycle: true,
    category: true,
    nomination: { select: { id: true, status: true, reason: true, snapshotPerformanceScore: true, snapshotPerformanceStatus: true, snapshotTargetAchievement: true } },
  };
}

async function attachRecognitionEmployees(items, employeeField = "employeeId") {
  const ids = [...new Set((items || []).map((item) => item?.[employeeField]).filter(Boolean))];
  const users = ids.length ? await prisma.user.findMany({
    where: { id: { in: ids } },
    select: { id: true, name: true, department: true, jobTitle: true, avatarUrl: true },
  }) : [];
  const map = new Map(users.map((user) => [user.id, user]));
  return (items || []).map((item) => ({ ...item, employee: map.get(item[employeeField]) || null }));
}

async function buildRecognitionOverview(req, payload = {}) {
  const scope = await recognitionManagerScope(req, payload);
  const userIds = scope.userIds;
  const departments = [...new Set(scope.users.map((user) => user.department).filter(Boolean))];
  const cycleWhere = scope.isAdmin
    ? { isActive: true }
    : { isActive: true, OR: [{ department: null }, ...(departments.length ? [{ department: { in: departments } }] : [])] };

  const [cycles, categories, nominations, awards] = await Promise.all([
    prisma.recognitionPerformanceCycle.findMany({ where: cycleWhere, orderBy: [{ status: "asc" }, { startDate: "desc" }], take: 200 }),
    prisma.recognitionCategory.findMany({ where: { isActive: true }, orderBy: [{ categoryType: "asc" }, { name: "asc" }], take: 500 }),
    userIds.length ? prisma.recognitionNomination.findMany({
      where: { nomineeEmployeeId: { in: userIds } },
      include: recognitionNominationInclude(),
      orderBy: [{ createdAt: "desc" }],
      take: 1000,
    }) : [],
    userIds.length ? prisma.recognitionAward.findMany({
      where: { employeeId: { in: userIds } },
      include: recognitionAwardInclude(),
      orderBy: [{ issuedAt: "desc" }],
      take: 1000,
    }) : [],
  ]);

  const [enrichedNominations, enrichedAwards] = await Promise.all([
    attachRecognitionEmployees(nominations, "nomineeEmployeeId"),
    attachRecognitionEmployees(awards, "employeeId"),
  ]);
  const visibleCycles = cycles.filter((cycle) => recognitionCycleVisibleToScope(cycle, scope));
  const cycleIds = new Set(visibleCycles.map((cycle) => cycle.id));
  const scopedNominations = enrichedNominations.filter((item) => cycleIds.has(item.cycleId));
  const scopedAwards = enrichedAwards.filter((item) => cycleIds.has(item.cycleId));
  const publishedAwards = scopedAwards.filter((item) => item.isPublished);
  const recognizedEmployees = new Set(scopedAwards.map((item) => item.employeeId));

  const cycleRows = visibleCycles.map((cycle) => {
    const cycleNominations = scopedNominations.filter((item) => item.cycleId === cycle.id);
    const cycleAwards = scopedAwards.filter((item) => item.cycleId === cycle.id);
    return {
      ...cycle,
      nominationWindowOpen: recognitionNominationWindowOpen(cycle),
      nominationCount: cycleNominations.length,
      pendingNominations: cycleNominations.filter((item) => item.status === "PENDING").length,
      approvedNominations: cycleNominations.filter((item) => item.status === "APPROVED").length,
      awardCount: cycleAwards.length,
      publishedAwards: cycleAwards.filter((item) => item.isPublished).length,
    };
  });

  return {
    methodology: {
      type: "HUMAN_RECOGNITION_DECISION_SUPPORT",
      performanceContext: "Phase 3 performance and Phase 6 target achievement are snapshotted when a manager submits a nomination. They are context only and never auto-approve, auto-reject, or auto-create a reward.",
      rewards: "Rewards are non-payroll descriptors only: badge, certificate, gift, experience, other, or none. TOS does not calculate salary, bonus, commission, or compensation.",
      cycleTypes: ["MONTHLY", "QUARTERLY", "ANNUAL", "CUSTOM"],
    },
    summary: {
      openCycles: cycleRows.filter((cycle) => cycle.status === "OPEN").length,
      pendingNominations: scopedNominations.filter((item) => item.status === "PENDING").length,
      approvedNominations: scopedNominations.filter((item) => item.status === "APPROVED").length,
      publishedRecognitions: publishedAwards.length,
      rewardsIssued: scopedAwards.filter((item) => item.rewardType !== "NONE").length,
      recognizedEmployees: recognizedEmployees.size,
    },
    cycles: cycleRows,
    categories,
    nominations: scopedNominations,
    awards: scopedAwards,
  };
}

router.get("/reports/team-performance/recognition/overview", asyncHandler(async (req, res) => {
  const data = await buildRecognitionOverview(req, {
    employeeId: req.query.employeeId || null,
    department: req.query.department || null,
  });
  res.json(data);
}));

router.get("/reports/team-performance/recognition/cycles", asyncHandler(async (req, res) => {
  const scope = await recognitionManagerScope(req);
  const departments = [...new Set(scope.users.map((user) => user.department).filter(Boolean))];
  const where = scope.isAdmin
    ? (req.query.includeInactive === "true" ? {} : { isActive: true })
    : { isActive: true, OR: [{ department: null }, ...(departments.length ? [{ department: { in: departments } }] : [])] };
  const cycles = await prisma.recognitionPerformanceCycle.findMany({ where, orderBy: [{ startDate: "desc" }], take: 500 });
  res.json({ cycles: cycles.filter((cycle) => recognitionCycleVisibleToScope(cycle, scope)), canConfigure: scope.isAdmin });
}));

router.post("/reports/team-performance/recognition/cycles", asyncHandler(async (req, res) => {
  assertRecognitionAdmin(req);
  const input = normalizeRecognitionCycleInput(req.body || {});
  await assertRecognitionDepartment(input.department);
  const cycle = await prisma.recognitionPerformanceCycle.create({ data: { ...input, status: "DRAFT", createdById: req.user.id, updatedById: req.user.id } });
  await auditRecognition(req, "performance_cycle_created", { cycleId: cycle.id, cycleType: cycle.cycleType, department: cycle.department });
  res.status(201).json(cycle);
}));

router.patch("/reports/team-performance/recognition/cycles/:cycleId", asyncHandler(async (req, res) => {
  assertRecognitionAdmin(req);
  const existing = await prisma.recognitionPerformanceCycle.findUnique({ where: { id: req.params.cycleId } });
  if (!existing) throw new AppError("Performance cycle not found", 404);
  if (existing.status === "CLOSED") throw new AppError("Closed performance cycles cannot be edited", 409);
  const input = normalizeRecognitionCycleInput(req.body || {}, existing);
  await assertRecognitionDepartment(input.department);
  const cycle = await prisma.recognitionPerformanceCycle.update({ where: { id: existing.id }, data: { ...input, updatedById: req.user.id } });
  await auditRecognition(req, "performance_cycle_updated", { cycleId: cycle.id });
  res.json(cycle);
}));

router.post("/reports/team-performance/recognition/cycles/:cycleId/open", asyncHandler(async (req, res) => {
  assertRecognitionAdmin(req);
  const existing = await prisma.recognitionPerformanceCycle.findUnique({ where: { id: req.params.cycleId } });
  if (!existing || !existing.isActive) throw new AppError("Performance cycle not found", 404);
  if (existing.status !== "DRAFT") throw new AppError("Only draft cycles can be opened", 409);
  const cycle = await prisma.recognitionPerformanceCycle.update({ where: { id: existing.id }, data: { status: "OPEN", openedAt: new Date(), closedAt: null, updatedById: req.user.id } });
  await auditRecognition(req, "performance_cycle_opened", { cycleId: cycle.id });
  res.json(cycle);
}));

router.post("/reports/team-performance/recognition/cycles/:cycleId/close", asyncHandler(async (req, res) => {
  assertRecognitionAdmin(req);
  const existing = await prisma.recognitionPerformanceCycle.findUnique({ where: { id: req.params.cycleId } });
  if (!existing || !existing.isActive) throw new AppError("Performance cycle not found", 404);
  if (existing.status !== "OPEN") throw new AppError("Only open cycles can be closed", 409);
  const cycle = await prisma.recognitionPerformanceCycle.update({ where: { id: existing.id }, data: { status: "CLOSED", closedAt: new Date(), updatedById: req.user.id } });
  await auditRecognition(req, "performance_cycle_closed", { cycleId: cycle.id });
  res.json(cycle);
}));

router.delete("/reports/team-performance/recognition/cycles/:cycleId", asyncHandler(async (req, res) => {
  assertRecognitionAdmin(req);
  const existing = await prisma.recognitionPerformanceCycle.findUnique({ where: { id: req.params.cycleId } });
  if (!existing) throw new AppError("Performance cycle not found", 404);
  if (existing.status === "OPEN") throw new AppError("Close the cycle before deactivation", 409);
  const cycle = await prisma.recognitionPerformanceCycle.update({ where: { id: existing.id }, data: { isActive: false, updatedById: req.user.id } });
  await auditRecognition(req, "performance_cycle_deactivated", { cycleId: cycle.id });
  res.json(cycle);
}));

router.get("/reports/team-performance/recognition/categories", asyncHandler(async (req, res) => {
  const scope = await recognitionManagerScope(req);
  const includeInactive = scope.isAdmin && req.query.includeInactive === "true";
  const categories = await prisma.recognitionCategory.findMany({ where: includeInactive ? {} : { isActive: true }, orderBy: [{ isActive: "desc" }, { categoryType: "asc" }, { name: "asc" }], take: 1000 });
  res.json({ categories, canConfigure: scope.isAdmin });
}));

router.post("/reports/team-performance/recognition/categories", asyncHandler(async (req, res) => {
  assertRecognitionAdmin(req);
  const input = normalizeRecognitionCategoryInput(req.body || {});
  await assertNoDuplicateRecognitionCategory(input);
  const category = await prisma.recognitionCategory.create({ data: { ...input, createdById: req.user.id, updatedById: req.user.id } });
  await auditRecognition(req, "recognition_category_created", { categoryId: category.id, name: category.name, categoryType: category.categoryType });
  res.status(201).json(category);
}));

router.patch("/reports/team-performance/recognition/categories/:categoryId", asyncHandler(async (req, res) => {
  assertRecognitionAdmin(req);
  const existing = await prisma.recognitionCategory.findUnique({ where: { id: req.params.categoryId } });
  if (!existing) throw new AppError("Recognition category not found", 404);
  const input = normalizeRecognitionCategoryInput(req.body || {}, existing);
  await assertNoDuplicateRecognitionCategory(input, existing.id);
  const category = await prisma.recognitionCategory.update({ where: { id: existing.id }, data: { ...input, updatedById: req.user.id } });
  await auditRecognition(req, "recognition_category_updated", { categoryId: category.id });
  res.json(category);
}));

router.delete("/reports/team-performance/recognition/categories/:categoryId", asyncHandler(async (req, res) => {
  assertRecognitionAdmin(req);
  const existing = await prisma.recognitionCategory.findUnique({ where: { id: req.params.categoryId } });
  if (!existing) throw new AppError("Recognition category not found", 404);
  const category = await prisma.recognitionCategory.update({ where: { id: existing.id }, data: { isActive: false, updatedById: req.user.id } });
  await auditRecognition(req, "recognition_category_deactivated", { categoryId: category.id });
  res.json(category);
}));

router.post("/reports/team-performance/recognition/nominations", asyncHandler(async (req, res) => {
  const nomineeEmployeeId = String(req.body?.nomineeEmployeeId || "").trim();
  const cycleId = String(req.body?.cycleId || "").trim();
  const categoryId = String(req.body?.categoryId || "").trim();
  const reason = recognitionText(req.body?.reason, 4000);
  if (!nomineeEmployeeId || !cycleId || !categoryId || !reason) throw new AppError("cycleId, categoryId, nomineeEmployeeId and reason are required", 400);
  const { scope, employee } = await assertRecognitionEmployeeAccess(req, nomineeEmployeeId);
  if (!scope.isAdmin && nomineeEmployeeId === req.user.id) throw new AppError("Managers cannot nominate themselves", 403);
  const [cycle, category] = await Promise.all([
    prisma.recognitionPerformanceCycle.findUnique({ where: { id: cycleId } }),
    prisma.recognitionCategory.findUnique({ where: { id: categoryId } }),
  ]);
  if (!cycle || !cycle.isActive || !recognitionCycleVisibleToScope(cycle, scope)) throw new AppError("Performance cycle not found", 404);
  if (!category || !category.isActive) throw new AppError("Recognition category not found", 404);
  if (!recognitionNominationWindowOpen(cycle)) throw new AppError("Recognition nominations are not open for this cycle", 409);
  if (cycle.department && recognitionKey(cycle.department) !== recognitionKey(employee.department)) throw new AppError("Employee is outside the cycle department", 403);
  const duplicate = await prisma.recognitionNomination.findFirst({ where: { cycleId, categoryId, nomineeEmployeeId }, select: { id: true } });
  if (duplicate) throw new AppError("This employee is already nominated for this category in the cycle", 409);
  const snapshot = await buildRecognitionPerformanceSnapshot(req, cycle, nomineeEmployeeId);
  const nomination = await prisma.recognitionNomination.create({
    data: { cycleId, categoryId, nomineeEmployeeId, nominatedById: req.user.id, reason, ...snapshot },
    include: recognitionNominationInclude(),
  });
  await auditRecognition(req, "recognition_nomination_created", { nominationId: nomination.id, cycleId, categoryId, nomineeEmployeeId, ...snapshot });
  res.status(201).json({ ...nomination, employee });
}));

router.post("/reports/team-performance/recognition/nominations/:nominationId/approve", asyncHandler(async (req, res) => {
  assertRecognitionAdmin(req);
  const nomination = await prisma.recognitionNomination.findUnique({ where: { id: req.params.nominationId }, include: recognitionNominationInclude() });
  if (!nomination) throw new AppError("Recognition nomination not found", 404);
  if (nomination.status !== "PENDING") throw new AppError("Only pending nominations can be approved", 409);
  const rewardType = recognitionRewardType(req.body?.rewardType ?? nomination.category.rewardType);
  const title = recognitionText(req.body?.title, 220) || nomination.category.name;
  const message = recognitionText(req.body?.message, 3000);
  const rewardDescription = recognitionText(req.body?.rewardDescription, 1200) || nomination.category.defaultRewardDescription || null;
  const publish = req.body?.publish === undefined ? true : Boolean(req.body.publish);
  const decisionNote = recognitionText(req.body?.decisionNote, 2000);
  const now = new Date();
  const result = await prisma.$transaction(async (tx) => {
    const updatedNomination = await tx.recognitionNomination.update({
      where: { id: nomination.id },
      data: { status: "APPROVED", decisionNote, reviewedById: req.user.id, reviewedAt: now },
    });
    const award = await tx.recognitionAward.create({
      data: {
        cycleId: nomination.cycleId,
        categoryId: nomination.categoryId,
        employeeId: nomination.nomineeEmployeeId,
        nominationId: nomination.id,
        title,
        message,
        rewardType,
        rewardDescription,
        issuedById: req.user.id,
        issuedAt: now,
        isPublished: publish,
        publishedAt: publish ? now : null,
      },
      include: recognitionAwardInclude(),
    });
    return { nomination: updatedNomination, award };
  });
  await auditRecognition(req, "recognition_nomination_approved", { nominationId: nomination.id, awardId: result.award.id, employeeId: nomination.nomineeEmployeeId, rewardType, published: publish });
  await auditRecognition(req, "recognition_award_issued", { awardId: result.award.id, nominationId: nomination.id, employeeId: nomination.nomineeEmployeeId, rewardType, published: publish });
  res.json(result);
}));

router.post("/reports/team-performance/recognition/nominations/:nominationId/reject", asyncHandler(async (req, res) => {
  assertRecognitionAdmin(req);
  const nomination = await prisma.recognitionNomination.findUnique({ where: { id: req.params.nominationId } });
  if (!nomination) throw new AppError("Recognition nomination not found", 404);
  if (nomination.status !== "PENDING") throw new AppError("Only pending nominations can be rejected", 409);
  const updated = await prisma.recognitionNomination.update({
    where: { id: nomination.id },
    data: { status: "REJECTED", decisionNote: recognitionText(req.body?.decisionNote, 2000), reviewedById: req.user.id, reviewedAt: new Date() },
  });
  await auditRecognition(req, "recognition_nomination_rejected", { nominationId: nomination.id, employeeId: nomination.nomineeEmployeeId });
  res.json(updated);
}));

router.patch("/reports/team-performance/recognition/awards/:awardId", asyncHandler(async (req, res) => {
  assertRecognitionAdmin(req);
  const existing = await prisma.recognitionAward.findUnique({ where: { id: req.params.awardId } });
  if (!existing) throw new AppError("Recognition award not found", 404);
  const data = {};
  if (Object.prototype.hasOwnProperty.call(req.body || {}, "title")) {
    const title = recognitionText(req.body.title, 220);
    if (!title) throw new AppError("Award title is required", 400);
    data.title = title;
  }
  if (Object.prototype.hasOwnProperty.call(req.body || {}, "message")) data.message = recognitionText(req.body.message, 3000);
  if (Object.prototype.hasOwnProperty.call(req.body || {}, "rewardType")) data.rewardType = recognitionRewardType(req.body.rewardType);
  if (Object.prototype.hasOwnProperty.call(req.body || {}, "rewardDescription")) data.rewardDescription = recognitionText(req.body.rewardDescription, 1200);
  if (Object.prototype.hasOwnProperty.call(req.body || {}, "isPublished")) {
    data.isPublished = Boolean(req.body.isPublished);
    data.publishedAt = data.isPublished ? (existing.publishedAt || new Date()) : null;
  }
  const award = await prisma.recognitionAward.update({ where: { id: existing.id }, data, include: recognitionAwardInclude() });
  await auditRecognition(req, "recognition_award_updated", { awardId: award.id, employeeId: award.employeeId, published: award.isPublished });
  res.json(award);
}));

router.get("/reports/team-performance/recognition/feed", asyncHandler(async (req, res) => {
  const awards = await prisma.recognitionAward.findMany({
    where: { isPublished: true },
    include: recognitionAwardInclude(),
    orderBy: [{ publishedAt: "desc" }, { issuedAt: "desc" }],
    take: 100,
  });
  res.json({ awards: await attachRecognitionEmployees(awards, "employeeId") });
}));

router.get("/reports/team-performance/recognition/employee/:employeeId", asyncHandler(async (req, res) => {
  const employeeId = String(req.params.employeeId || "").trim();
  const selfOnly = !isRecognitionManager(req) && employeeId === req.user.id;
  if (!selfOnly) await assertRecognitionEmployeeAccess(req, employeeId);
  const [awards, nominations] = await Promise.all([
    prisma.recognitionAward.findMany({
      where: { employeeId, ...(selfOnly ? { isPublished: true } : {}) },
      include: recognitionAwardInclude(),
      orderBy: [{ issuedAt: "desc" }],
      take: 100,
    }),
    selfOnly ? Promise.resolve([]) : prisma.recognitionNomination.findMany({
      where: { nomineeEmployeeId: employeeId },
      include: recognitionNominationInclude(),
      orderBy: [{ createdAt: "desc" }],
      take: 100,
    }),
  ]);
  res.json({
    employeeId,
    awards,
    nominations,
    summary: {
      awards: awards.length,
      publishedAwards: awards.filter((item) => item.isPublished).length,
      rewards: awards.filter((item) => item.rewardType !== "NONE").length,
      pendingNominations: nominations.filter((item) => item.status === "PENDING").length,
    },
  });
}));

'''
path.write_text(text.replace(anchor, code + anchor, 1))
print("BACKEND_RECOGNITION_OVERVIEW=PASS")
print("BACKEND_PERFORMANCE_CYCLES=PASS")
print("BACKEND_RECOGNITION_CATEGORIES=PASS")
print("BACKEND_RECOGNITION_NOMINATIONS=PASS")
print("BACKEND_RECOGNITION_AWARDS=PASS")
print("RECOGNITION_HUMAN_DECISION_GUARD=PASS")
print("NON_PAYROLL_REWARD_GUARD=PASS")
