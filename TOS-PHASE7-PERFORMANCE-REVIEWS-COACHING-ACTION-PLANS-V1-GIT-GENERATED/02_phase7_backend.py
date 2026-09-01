#!/usr/bin/env python3
from pathlib import Path
import sys

repo = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS").resolve()
path = repo / "backend/src/routes/tasks.routes.js"
text = path.read_text()

helper_anchor = "function buildTeamPerformanceIntelligence(dataset) {"
route_anchor = 'router.get("/reports/team-performance/targets/summary", asyncHandler(async (req, res) => {'
if text.count(helper_anchor) != 1:
    raise SystemExit(f"PHASE7_HELPER_ANCHOR=FAIL count={text.count(helper_anchor)}")
if text.count(route_anchor) != 1:
    raise SystemExit(f"PHASE7_ROUTE_ANCHOR=FAIL count={text.count(route_anchor)}")
if "const PERFORMANCE_REVIEW_STATUSES" in text or 'router.get("/reports/team-performance/reviews/summary"' in text:
    raise SystemExit("PHASE7_BACKEND_ALREADY_PRESENT=FAIL")

helpers = r'''
const PERFORMANCE_REVIEW_STATUSES = new Set(["DRAFT", "SHARED", "IN_PROGRESS", "COMPLETED"]);
const PERFORMANCE_REVIEW_TRIGGERS = new Set([
  "PERIODIC",
  "TARGET_MISSED",
  "TARGET_AT_RISK",
  "SCORE_DROP",
  "OVERDUE",
  "NO_ACTIVITY",
  "WORKLOAD_ISSUE",
  "MANAGER_INITIATED",
]);
const PERFORMANCE_ACTION_STATUSES = new Set(["OPEN", "IN_PROGRESS", "COMPLETED", "CANCELLED"]);
const PERFORMANCE_ACTION_PRIORITIES = new Set(["LOW", "MEDIUM", "HIGH", "URGENT"]);

function reviewText(value, max = 6000) {
  if (value === undefined) return undefined;
  if (value === null) return null;
  const text = String(value).trim();
  if (!text) return null;
  if (text.length > max) throw new AppError(`Review text exceeds ${max} characters`, 400);
  return text;
}

function reviewDate(value, label, required = false) {
  if (value === undefined || value === null || value === "") {
    if (required) throw new AppError(`${label} is required`, 400);
    return null;
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) throw new AppError(`Invalid ${label}`, 400);
  return date;
}

function reviewTrigger(value, fallback = "PERIODIC") {
  const trigger = String(value || fallback).trim().toUpperCase();
  if (!PERFORMANCE_REVIEW_TRIGGERS.has(trigger)) throw new AppError("Invalid review trigger", 400);
  return trigger;
}

async function getPerformanceReviewScope(req) {
  const targetScope = await getTargetAccessScope(req);
  const canManage = isSystemAdmin(req.user) || ["MANAGER", "PROJECT_MANAGER"].includes(req.user.role);
  return { ...targetScope, canManage };
}

async function getReviewVisibleEmployeeIds(req, { employeeId = null, department = null, requireManage = false } = {}) {
  const scope = await getPerformanceReviewScope(req);
  if (requireManage && !scope.canManage) throw new AppError("Performance review management requires manager access", 403);

  let ids = [...scope.userIds];
  if (employeeId) {
    if (!scope.userIds.has(employeeId)) throw new AppError("Unauthorized review employee", 403);
    ids = [employeeId];
  }

  if (department && ids.length) {
    const users = await prisma.user.findMany({
      where: { id: { in: ids }, role: { notIn: ["CLIENT", "FORMER_EMPLOYEE"] } },
      select: { id: true, department: true },
    });
    const key = String(department).trim().toLowerCase();
    ids = users.filter((user) => String(user.department || "").trim().toLowerCase() === key).map((user) => user.id);
  }

  return { ...scope, ids };
}

async function assertReviewEmployeeAccess(req, employeeId, requireManage = false) {
  const employee = await prisma.user.findUnique({
    where: { id: employeeId },
    select: { id: true, name: true, department: true, jobTitle: true, avatarUrl: true, role: true },
  });
  if (!employee) throw new AppError("Review employee not found", 404);
  if (["CLIENT", "FORMER_EMPLOYEE"].includes(employee.role)) throw new AppError("Employee is not eligible for performance reviews", 400);
  const scope = await getReviewVisibleEmployeeIds(req, { employeeId, requireManage });
  if (!scope.ids.includes(employeeId)) throw new AppError("Unauthorized review employee", 403);
  return { employee, scope };
}

function reviewActionInclude() {
  return {
    actions: {
      orderBy: [{ status: "asc" }, { dueDate: "asc" }, { createdAt: "asc" }],
    },
  };
}

async function attachReviewEmployees(reviews) {
  const ids = [...new Set((reviews || []).map((review) => review.employeeId).filter(Boolean))];
  const users = ids.length
    ? await prisma.user.findMany({
        where: { id: { in: ids } },
        select: { id: true, name: true, department: true, jobTitle: true, avatarUrl: true },
      })
    : [];
  const map = new Map(users.map((user) => [user.id, user]));
  return (reviews || []).map((review) => ({ ...review, employee: map.get(review.employeeId) || null }));
}

async function auditPerformanceReview(req, action, metadata = {}) {
  await prisma.workspaceAuditLog.create({
    data: {
      action,
      actorId: req.user.id,
      metadata: { ...metadata, occurredAt: new Date().toISOString() },
    },
  });
}

async function loadReviewForAccess(req, reviewId, { requireManage = false, includeActions = true } = {}) {
  const review = await prisma.performanceReview.findUnique({
    where: { id: reviewId },
    ...(includeActions ? { include: reviewActionInclude() } : {}),
  });
  if (!review) throw new AppError("Performance review not found", 404);
  const { scope } = await assertReviewEmployeeAccess(req, review.employeeId, requireManage);
  if (!scope.canManage && review.status === "DRAFT") throw new AppError("Performance review not found", 404);
  return { review, scope };
}

function normalizeReviewCreateInput(payload = {}) {
  const employeeId = String(payload.employeeId || "").trim();
  if (!employeeId) throw new AppError("employeeId is required", 400);
  const periodStart = reviewDate(payload.periodStart, "periodStart", true);
  const periodEnd = reviewDate(payload.periodEnd, "periodEnd", true);
  if (periodStart > periodEnd) throw new AppError("periodStart must be before or equal periodEnd", 400);
  const followUpAt = reviewDate(payload.followUpAt, "followUpAt", false);
  return {
    employeeId,
    periodStart,
    periodEnd,
    triggerType: reviewTrigger(payload.triggerType),
    triggerReference: reviewText(payload.triggerReference, 500),
    title: reviewText(payload.title, 300),
    strengths: reviewText(payload.strengths),
    improvementAreas: reviewText(payload.improvementAreas),
    managerNotes: reviewText(payload.managerNotes),
    followUpAt,
  };
}

async function createReviewSnapshot(req, input) {
  const dataset = await buildTeamPerformanceExportDataset(req, {
    start: input.periodStart.toISOString(),
    end: input.periodEnd.toISOString(),
    employeeId: input.employeeId,
  });
  const row = dataset.rows.find((item) => item.id === input.employeeId) || null;
  if (!row) throw new AppError("Employee is outside the accessible performance scope", 403);
  const targetSummary = await buildTargetSummary(dataset);
  const target = targetSummary.rows.find((item) => item.employeeId === input.employeeId) || null;
  return {
    snapshotScore: row.performanceScore == null ? null : Number(row.performanceScore),
    snapshotStatus: row.status || "No Activity",
    snapshotTargetAchievement: target?.achievementPercent == null ? null : Number(target.achievementPercent),
    snapshotTargetStatus: target?.status || "No Target",
    snapshotCompletedTasks: Number(row.completedTasks || 0),
    snapshotTotalTasks: Number(row.totalTasks || 0),
    snapshotOverdueTasks: Number(row.overdueTasks || 0),
    snapshotActualHours: Number(row.actualHours || 0),
  };
}

'''
text = text.replace(helper_anchor, helpers + helper_anchor, 1)

routes = r'''
router.get("/reports/team-performance/reviews/summary", asyncHandler(async (req, res) => {
  const { startDate, endDate } = parseTargetQueryRange(req.query.start, req.query.end);
  const access = await getReviewVisibleEmployeeIds(req, {
    employeeId: req.query.employeeId || null,
    department: req.query.department || null,
  });
  const where = {
    employeeId: { in: access.ids },
    periodStart: { lte: endDate },
    periodEnd: { gte: startDate },
    ...(!access.canManage ? { status: { not: "DRAFT" } } : {}),
  };
  const reviews = access.ids.length
    ? await prisma.performanceReview.findMany({
        where,
        include: reviewActionInclude(),
        orderBy: [{ followUpAt: "asc" }, { updatedAt: "desc" }],
        take: 500,
      })
    : [];

  const now = new Date();
  const actions = reviews.flatMap((review) => review.actions || []);
  const openActions = actions.filter((action) => ["OPEN", "IN_PROGRESS"].includes(action.status));
  const overdueActions = openActions.filter((action) => action.dueDate && action.dueDate < now);
  const dueReviews = reviews.filter((review) => review.status !== "COMPLETED" && review.followUpAt && review.followUpAt <= now);
  const followUpEmployees = new Set([
    ...dueReviews.map((review) => review.employeeId),
    ...reviews.filter((review) => (review.actions || []).some((action) => overdueActions.some((overdue) => overdue.id === action.id))).map((review) => review.employeeId),
  ]);

  res.json({
    period: { start: startDate.toISOString(), end: endDate.toISOString() },
    summary: {
      totalReviews: reviews.length,
      draft: reviews.filter((review) => review.status === "DRAFT").length,
      awaitingAcknowledgment: reviews.filter((review) => review.status === "SHARED" && !review.employeeAcknowledgedAt).length,
      inProgress: reviews.filter((review) => review.status === "IN_PROGRESS").length,
      completed: reviews.filter((review) => review.status === "COMPLETED").length,
      reviewsDue: dueReviews.length,
      openActionPlans: openActions.length,
      overdueActions: overdueActions.length,
      employeesNeedingFollowUp: followUpEmployees.size,
    },
  });
}));

router.get("/reports/team-performance/reviews", asyncHandler(async (req, res) => {
  const { startDate, endDate } = parseTargetQueryRange(req.query.start, req.query.end);
  const access = await getReviewVisibleEmployeeIds(req, {
    employeeId: req.query.employeeId || null,
    department: req.query.department || null,
  });
  const status = req.query.status ? String(req.query.status).trim().toUpperCase() : null;
  const triggerType = req.query.triggerType ? String(req.query.triggerType).trim().toUpperCase() : null;
  if (status && !PERFORMANCE_REVIEW_STATUSES.has(status)) throw new AppError("Invalid review status", 400);
  if (triggerType && !PERFORMANCE_REVIEW_TRIGGERS.has(triggerType)) throw new AppError("Invalid review trigger", 400);
  const limit = Math.min(200, Math.max(1, Number(req.query.limit || 100)));
  const where = {
    employeeId: { in: access.ids },
    periodStart: { lte: endDate },
    periodEnd: { gte: startDate },
    ...(status ? { status } : {}),
    ...(triggerType ? { triggerType } : {}),
    ...(!access.canManage ? { AND: [{ status: { not: "DRAFT" } }] } : {}),
  };
  const reviews = access.ids.length
    ? await prisma.performanceReview.findMany({
        where,
        include: reviewActionInclude(),
        orderBy: [{ updatedAt: "desc" }],
        take: limit,
      })
    : [];
  res.json({ reviews: await attachReviewEmployees(reviews) });
}));

router.get("/reports/team-performance/reviews/:reviewId", asyncHandler(async (req, res) => {
  const { review } = await loadReviewForAccess(req, req.params.reviewId, { includeActions: true });
  const [enriched] = await attachReviewEmployees([review]);
  res.json(enriched);
}));

router.post("/reports/team-performance/reviews", asyncHandler(async (req, res) => {
  const input = normalizeReviewCreateInput(req.body);
  const { employee } = await assertReviewEmployeeAccess(req, input.employeeId, true);
  const duplicate = await prisma.performanceReview.findFirst({
    where: {
      employeeId: input.employeeId,
      periodStart: input.periodStart,
      periodEnd: input.periodEnd,
      status: { not: "COMPLETED" },
    },
    select: { id: true },
  });
  if (duplicate) throw new AppError("An open review already exists for this employee and exact period", 409);
  const snapshot = await createReviewSnapshot(req, input);
  const review = await prisma.performanceReview.create({
    data: {
      ...input,
      ...snapshot,
      reviewerId: req.user.id,
      status: "DRAFT",
      createdById: req.user.id,
      updatedById: req.user.id,
    },
    include: reviewActionInclude(),
  });
  await auditPerformanceReview(req, "performance_review_created", {
    reviewId: review.id,
    employeeId: review.employeeId,
    employeeName: employee.name,
    periodStart: review.periodStart,
    periodEnd: review.periodEnd,
    triggerType: review.triggerType,
  });
  res.status(201).json({ ...review, employee });
}));

router.patch("/reports/team-performance/reviews/:reviewId", asyncHandler(async (req, res) => {
  const { review } = await loadReviewForAccess(req, req.params.reviewId, { requireManage: true, includeActions: false });
  if (review.status === "COMPLETED") throw new AppError("Completed reviews cannot be edited", 409);
  const data = { updatedById: req.user.id };
  if (Object.prototype.hasOwnProperty.call(req.body || {}, "title")) data.title = reviewText(req.body.title, 300);
  if (Object.prototype.hasOwnProperty.call(req.body || {}, "strengths")) data.strengths = reviewText(req.body.strengths);
  if (Object.prototype.hasOwnProperty.call(req.body || {}, "improvementAreas")) data.improvementAreas = reviewText(req.body.improvementAreas);
  if (Object.prototype.hasOwnProperty.call(req.body || {}, "managerNotes")) data.managerNotes = reviewText(req.body.managerNotes);
  if (Object.prototype.hasOwnProperty.call(req.body || {}, "triggerReference")) data.triggerReference = reviewText(req.body.triggerReference, 500);
  if (Object.prototype.hasOwnProperty.call(req.body || {}, "triggerType")) data.triggerType = reviewTrigger(req.body.triggerType, review.triggerType);
  if (Object.prototype.hasOwnProperty.call(req.body || {}, "followUpAt")) data.followUpAt = reviewDate(req.body.followUpAt, "followUpAt", false);
  const updated = await prisma.performanceReview.update({
    where: { id: review.id },
    data,
    include: reviewActionInclude(),
  });
  await auditPerformanceReview(req, "performance_review_updated", { reviewId: updated.id, employeeId: updated.employeeId });
  res.json(updated);
}));

router.post("/reports/team-performance/reviews/:reviewId/share", asyncHandler(async (req, res) => {
  const { review } = await loadReviewForAccess(req, req.params.reviewId, { requireManage: true, includeActions: false });
  if (review.status !== "DRAFT") throw new AppError("Only draft reviews can be shared", 409);
  const updated = await prisma.performanceReview.update({
    where: { id: review.id },
    data: { status: "SHARED", sharedAt: new Date(), updatedById: req.user.id },
    include: reviewActionInclude(),
  });
  await auditPerformanceReview(req, "performance_review_shared", { reviewId: updated.id, employeeId: updated.employeeId });
  res.json(updated);
}));

router.post("/reports/team-performance/reviews/:reviewId/acknowledge", asyncHandler(async (req, res) => {
  const { review } = await loadReviewForAccess(req, req.params.reviewId, { includeActions: false });
  if (review.employeeId !== req.user.id) throw new AppError("Only the reviewed employee can acknowledge this review", 403);
  if (!["SHARED", "IN_PROGRESS"].includes(review.status)) throw new AppError("This review is not ready for acknowledgment", 409);
  const comment = reviewText(req.body?.employeeComment, 4000);
  const updated = await prisma.performanceReview.update({
    where: { id: review.id },
    data: {
      employeeComment: comment,
      employeeAcknowledgedAt: new Date(),
      status: review.status === "SHARED" ? "IN_PROGRESS" : review.status,
      updatedById: req.user.id,
    },
    include: reviewActionInclude(),
  });
  await auditPerformanceReview(req, "performance_review_acknowledged", { reviewId: updated.id, employeeId: updated.employeeId });
  res.json(updated);
}));

router.post("/reports/team-performance/reviews/:reviewId/complete", asyncHandler(async (req, res) => {
  const { review } = await loadReviewForAccess(req, req.params.reviewId, { requireManage: true, includeActions: true });
  if (!["SHARED", "IN_PROGRESS"].includes(review.status)) throw new AppError("Review must be shared or in progress before completion", 409);
  const openActions = (review.actions || []).filter((action) => ["OPEN", "IN_PROGRESS"].includes(action.status));
  if (openActions.length) throw new AppError("Complete or cancel open action items before completing the review", 409);
  const updated = await prisma.performanceReview.update({
    where: { id: review.id },
    data: { status: "COMPLETED", completedAt: new Date(), updatedById: req.user.id },
    include: reviewActionInclude(),
  });
  await auditPerformanceReview(req, "performance_review_completed", { reviewId: updated.id, employeeId: updated.employeeId });
  res.json(updated);
}));

router.post("/reports/team-performance/reviews/:reviewId/actions", asyncHandler(async (req, res) => {
  const { review } = await loadReviewForAccess(req, req.params.reviewId, { requireManage: true, includeActions: false });
  if (review.status === "COMPLETED") throw new AppError("Cannot add actions to a completed review", 409);
  const title = reviewText(req.body?.title, 300);
  if (!title) throw new AppError("Action title is required", 400);
  const priority = String(req.body?.priority || "MEDIUM").trim().toUpperCase();
  if (!PERFORMANCE_ACTION_PRIORITIES.has(priority)) throw new AppError("Invalid action priority", 400);
  const dueDate = reviewDate(req.body?.dueDate, "dueDate", false);
  const action = await prisma.performanceActionItem.create({
    data: {
      reviewId: review.id,
      title,
      description: reviewText(req.body?.description, 4000),
      dueDate,
      priority,
      status: "OPEN",
      createdById: req.user.id,
      updatedById: req.user.id,
    },
  });
  await auditPerformanceReview(req, "performance_action_created", { reviewId: review.id, actionId: action.id, employeeId: review.employeeId });
  res.status(201).json(action);
}));

router.patch("/reports/team-performance/reviews/:reviewId/actions/:actionId", asyncHandler(async (req, res) => {
  const action = await prisma.performanceActionItem.findUnique({
    where: { id: req.params.actionId },
    include: { review: true },
  });
  if (!action || action.reviewId !== req.params.reviewId) throw new AppError("Performance action not found", 404);
  const access = await getReviewVisibleEmployeeIds(req, { employeeId: action.review.employeeId });
  if (!access.ids.includes(action.review.employeeId)) throw new AppError("Unauthorized performance action", 403);
  const isEmployee = req.user.id === action.review.employeeId && !access.canManage;
  if (!access.canManage && !isEmployee) throw new AppError("Unauthorized performance action", 403);
  if (action.review.status === "DRAFT" && isEmployee) throw new AppError("Performance action not found", 404);
  if (action.review.status === "COMPLETED") throw new AppError("Completed review actions cannot be edited", 409);

  const data = { updatedById: req.user.id };
  const requestedStatus = Object.prototype.hasOwnProperty.call(req.body || {}, "status")
    ? String(req.body.status || "").trim().toUpperCase()
    : null;
  if (requestedStatus) {
    if (!PERFORMANCE_ACTION_STATUSES.has(requestedStatus)) throw new AppError("Invalid action status", 400);
    if (isEmployee && requestedStatus === "CANCELLED") throw new AppError("Employees cannot cancel action items", 403);
    if (isEmployee && action.status === "COMPLETED" && requestedStatus !== "COMPLETED") throw new AppError("Employees cannot reopen completed action items", 403);
    data.status = requestedStatus;
    data.completedAt = requestedStatus === "COMPLETED" ? (action.completedAt || new Date()) : null;
  }
  if (!isEmployee) {
    if (Object.prototype.hasOwnProperty.call(req.body || {}, "title")) {
      const title = reviewText(req.body.title, 300);
      if (!title) throw new AppError("Action title is required", 400);
      data.title = title;
    }
    if (Object.prototype.hasOwnProperty.call(req.body || {}, "description")) data.description = reviewText(req.body.description, 4000);
    if (Object.prototype.hasOwnProperty.call(req.body || {}, "dueDate")) data.dueDate = reviewDate(req.body.dueDate, "dueDate", false);
    if (Object.prototype.hasOwnProperty.call(req.body || {}, "priority")) {
      const priority = String(req.body.priority || "").trim().toUpperCase();
      if (!PERFORMANCE_ACTION_PRIORITIES.has(priority)) throw new AppError("Invalid action priority", 400);
      data.priority = priority;
    }
  } else {
    const forbidden = ["title", "description", "dueDate", "priority"].some((key) => Object.prototype.hasOwnProperty.call(req.body || {}, key));
    if (forbidden) throw new AppError("Employees can only update action status", 403);
  }

  const updated = await prisma.performanceActionItem.update({ where: { id: action.id }, data });
  await auditPerformanceReview(req, "performance_action_updated", { reviewId: action.reviewId, actionId: updated.id, employeeId: action.review.employeeId, status: updated.status });
  res.json(updated);
}));

router.delete("/reports/team-performance/reviews/:reviewId/actions/:actionId", asyncHandler(async (req, res) => {
  const action = await prisma.performanceActionItem.findUnique({
    where: { id: req.params.actionId },
    include: { review: true },
  });
  if (!action || action.reviewId !== req.params.reviewId) throw new AppError("Performance action not found", 404);
  await assertReviewEmployeeAccess(req, action.review.employeeId, true);
  if (action.review.status === "COMPLETED") throw new AppError("Completed review actions cannot be cancelled", 409);
  const updated = await prisma.performanceActionItem.update({
    where: { id: action.id },
    data: { status: "CANCELLED", completedAt: null, updatedById: req.user.id },
  });
  await auditPerformanceReview(req, "performance_action_cancelled", { reviewId: action.reviewId, actionId: updated.id, employeeId: action.review.employeeId });
  res.json(updated);
}));

'''
text = text.replace(route_anchor, routes + route_anchor, 1)
path.write_text(text)

print("BACKEND_REVIEW_HELPERS=PASS")
print("BACKEND_REVIEW_CRUD=PASS")
print("BACKEND_ACTION_PLANS=PASS")
print("BACKEND_REVIEW_RBAC=PASS")
print("BACKEND_REVIEW_AUDIT=PASS")
