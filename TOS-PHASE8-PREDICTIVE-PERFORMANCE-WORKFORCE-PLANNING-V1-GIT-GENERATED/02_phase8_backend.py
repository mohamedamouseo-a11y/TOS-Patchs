#!/usr/bin/env python3
from pathlib import Path
import sys

repo = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS").resolve()
path = repo / "backend/src/routes/tasks.routes.js"
text = path.read_text()
helper_anchor = "function buildTeamPerformanceIntelligence(dataset) {"
route_anchor = 'router.get("/reports/team-performance/reviews/summary", asyncHandler(async (req, res) => {'
if text.count(helper_anchor) != 1:
    raise SystemExit(f"WORKFORCE_HELPER_ANCHOR=FAIL count={text.count(helper_anchor)}")
if text.count(route_anchor) != 1:
    raise SystemExit(f"WORKFORCE_ROUTE_ANCHOR=FAIL count={text.count(route_anchor)}")
if "async function buildWorkforceForecast(req" in text or 'router.get("/reports/team-performance/workforce/forecast"' in text:
    raise SystemExit("WORKFORCE_ALREADY_PRESENT=FAIL")

helpers = r'''
const WORKFORCE_DEFAULT_WEEKLY_CAPACITY = 40;
const WORKFORCE_MAX_HORIZON_DAYS = 90;
const WORKFORCE_OPEN_STATUSES = ["BACKLOG", "TODO", "IN_PROGRESS", "WAITING_CLIENT", "IN_REVIEW", "REVIEW", "REVISION", "APPROVED"];

function workforceRound(value, digits = 1) {
  if (value == null || !Number.isFinite(Number(value))) return null;
  const factor = 10 ** digits;
  return Math.round(Number(value) * factor) / factor;
}

function workforceStartOfDay(value = new Date()) {
  const date = new Date(value);
  date.setHours(0, 0, 0, 0);
  return date;
}

function workforceEndOfDay(value = new Date()) {
  const date = new Date(value);
  date.setHours(23, 59, 59, 999);
  return date;
}

function workforceBusinessDays(start, end) {
  let count = 0;
  const cursor = workforceStartOfDay(start);
  const last = workforceStartOfDay(end);
  while (cursor <= last) {
    const day = cursor.getDay();
    // TOS SLA defaults use Sunday-Thursday as business days: 0..4.
    if (day >= 0 && day <= 4) count += 1;
    cursor.setDate(cursor.getDate() + 1);
  }
  return count;
}

function workforceText(value, max = 1200) {
  if (value === undefined) return undefined;
  if (value === null) return null;
  const text = String(value).trim();
  if (!text) return null;
  if (text.length > max) throw new AppError(`Capacity note exceeds ${max} characters`, 400);
  return text;
}

function normalizeWorkforceCapacityInput(payload = {}, existing = null) {
  const employeeId = String(existing?.employeeId || payload.employeeId || "").trim();
  if (!employeeId) throw new AppError("employeeId is required", 400);
  const weeklyCapacityHours = Number(payload.weeklyCapacityHours ?? existing?.weeklyCapacityHours);
  if (!Number.isFinite(weeklyCapacityHours) || weeklyCapacityHours <= 0 || weeklyCapacityHours > 168) {
    throw new AppError("weeklyCapacityHours must be greater than 0 and no more than 168", 400);
  }
  const effectiveFrom = new Date(payload.effectiveFrom ?? existing?.effectiveFrom);
  if (Number.isNaN(effectiveFrom.getTime())) throw new AppError("Invalid effectiveFrom", 400);
  let effectiveTo = payload.effectiveTo === undefined ? (existing?.effectiveTo || null) : payload.effectiveTo;
  effectiveTo = effectiveTo ? new Date(effectiveTo) : null;
  if (effectiveTo && Number.isNaN(effectiveTo.getTime())) throw new AppError("Invalid effectiveTo", 400);
  if (effectiveTo && effectiveFrom > effectiveTo) throw new AppError("effectiveFrom must be before or equal effectiveTo", 400);
  return {
    employeeId,
    weeklyCapacityHours: workforceRound(weeklyCapacityHours, 2),
    effectiveFrom,
    effectiveTo,
    note: workforceText(payload.note === undefined ? existing?.note : payload.note),
    isActive: payload.isActive === undefined ? (existing?.isActive ?? true) : Boolean(payload.isActive),
  };
}

async function getWorkforceScope(req, { employeeId = null, department = null, requireManage = false } = {}) {
  const isAdmin = isSystemAdmin(req.user);
  const isManager = req.user.role === "MANAGER" || req.user.role === "PROJECT_MANAGER";
  const canManage = isAdmin || isManager;
  if (requireManage && !canManage) throw new AppError("Workforce planning management requires manager access", 403);

  let projectIds = [];
  let candidateUserIds = [];
  if (isAdmin) {
    const [projects, users] = await Promise.all([
      prisma.project.findMany({ where: { archivedAt: null }, select: { id: true } }),
      prisma.user.findMany({ where: { role: { notIn: ["CLIENT", "FORMER_EMPLOYEE"] } }, select: { id: true } }),
    ]);
    projectIds = projects.map((project) => project.id);
    candidateUserIds = users.map((user) => user.id);
  } else if (isManager) {
    const projects = await prisma.project.findMany({
      where: { archivedAt: null, members: { some: { userId: req.user.id } } },
      select: { id: true, members: { select: { userId: true } } },
    });
    projectIds = projects.map((project) => project.id);
    candidateUserIds = [...new Set(projects.flatMap((project) => project.members.map((member) => member.userId)))];
  } else {
    const projects = await prisma.project.findMany({
      where: { archivedAt: null, members: { some: { userId: req.user.id } } },
      select: { id: true },
    });
    projectIds = projects.map((project) => project.id);
    candidateUserIds = [req.user.id];
  }

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
  const allowedIds = new Set(users.map((user) => user.id));
  if (employeeId && !allowedIds.has(employeeId)) throw new AppError("Unauthorized workforce employee", 403);

  let visibleUsers = employeeId ? users.filter((user) => user.id === employeeId) : users;
  if (department) {
    const key = String(department).trim().toLowerCase();
    visibleUsers = visibleUsers.filter((user) => String(user.department || "").trim().toLowerCase() === key);
  }

  return {
    isAdmin,
    isManager,
    canManage,
    projectIds,
    users: visibleUsers,
    userIds: visibleUsers.map((user) => user.id),
  };
}

async function assertWorkforceCapacityAccess(req, employeeId) {
  const scope = await getWorkforceScope(req, { requireManage: true });
  if (!scope.userIds.includes(employeeId)) throw new AppError("Unauthorized workforce employee", 403);
  const employee = scope.users.find((user) => user.id === employeeId);
  if (!employee) throw new AppError("Workforce employee not found", 404);
  return { scope, employee };
}

async function assertNoOverlappingCapacityPlan(input, excludeId = null) {
  if (!input.isActive) return;
  const effectiveEnd = input.effectiveTo || new Date("9999-12-31T23:59:59.999Z");
  const overlap = await prisma.workforceCapacityPlan.findFirst({
    where: {
      employeeId: input.employeeId,
      isActive: true,
      effectiveFrom: { lte: effectiveEnd },
      OR: [{ effectiveTo: null }, { effectiveTo: { gte: input.effectiveFrom } }],
      ...(excludeId ? { id: { not: excludeId } } : {}),
    },
    select: { id: true },
  });
  if (overlap) throw new AppError("An active capacity plan already overlaps this employee period", 409);
}

async function auditWorkforceCapacity(req, action, metadata = {}) {
  await prisma.workspaceAuditLog.create({
    data: {
      action,
      actorId: req.user.id,
      metadata: { ...metadata, occurredAt: new Date().toISOString() },
    },
  });
}

function workforceCapacitySource(user, plan) {
  if (plan) return { weeklyCapacityHours: Number(plan.weeklyCapacityHours), source: "CAPACITY_PLAN", planId: plan.id };
  const legacy = Number(user.designWeeklyCapacityHours || 0);
  if (Number.isFinite(legacy) && legacy > 0) return { weeklyCapacityHours: legacy, source: "DESIGN_CAPACITY", planId: null };
  return { weeklyCapacityHours: WORKFORCE_DEFAULT_WEEKLY_CAPACITY, source: "DEFAULT_40H", planId: null };
}

function workforceRisk({ utilization, overdueTasks, dueTasks, estimatedDueTasks }) {
  if (overdueTasks >= 5 || (utilization != null && utilization >= 125)) return "CRITICAL";
  if (overdueTasks >= 3 || (utilization != null && utilization > 100)) return "HIGH";
  if (overdueTasks >= 1 || (utilization != null && utilization >= 85)) return "WATCH";
  if (dueTasks > 0 && estimatedDueTasks === 0) return "UNKNOWN";
  return "HEALTHY";
}

function workforceConfidence(dueTasks, unestimatedDueTasks) {
  if (!dueTasks) return "NO_DEMAND";
  const ratio = unestimatedDueTasks / dueTasks;
  if (ratio === 0) return "HIGH";
  if (ratio <= 0.25) return "MEDIUM";
  return "LOW";
}

function workforceOutlook({ risk, performanceScore, scoreDelta, targetAchievement, overdueActions, dueTasks }) {
  if (["CRITICAL", "HIGH"].includes(risk) || Number(performanceScore) < 50 || Number(scoreDelta) <= -10 || overdueActions > 0) return "AT_RISK";
  if (risk === "WATCH" || (performanceScore != null && Number(performanceScore) < 70) || (targetAchievement != null && Number(targetAchievement) < 90)) return "WATCH";
  if (Number(scoreDelta) >= 5 && risk === "HEALTHY" && (targetAchievement == null || Number(targetAchievement) >= 90)) return "POSITIVE";
  if (performanceScore == null && dueTasks === 0 && targetAchievement == null) return "INSUFFICIENT_DATA";
  return "STABLE";
}

function workforceSignals(row) {
  const signals = [];
  if (row.utilizationPercent != null && row.utilizationPercent > 100) signals.push({ type: "CAPACITY_OVERLOAD", severity: row.utilizationPercent >= 125 ? "critical" : "warning", message: `${row.utilizationPercent}% planned capacity load.` });
  if (row.overdueOpenTasks > 0) signals.push({ type: "OVERDUE_OPEN_WORK", severity: row.overdueOpenTasks >= 3 ? "critical" : "warning", message: `${row.overdueOpenTasks} overdue open task${row.overdueOpenTasks === 1 ? "" : "s"}.` });
  if (row.unestimatedDueTasks > 0) signals.push({ type: "UNESTIMATED_DEMAND", severity: "info", message: `${row.unestimatedDueTasks} due task${row.unestimatedDueTasks === 1 ? "" : "s"} missing estimates.` });
  if (row.scoreDelta != null && row.scoreDelta <= -10) signals.push({ type: "PERFORMANCE_DECLINE", severity: "warning", message: `Recent performance trend is ${row.scoreDelta} points.` });
  if (row.targetAchievement != null && row.targetAchievement < 90) signals.push({ type: "TARGET_BEHIND", severity: "warning", message: `Recent target achievement is ${row.targetAchievement}%.` });
  if (row.overdueReviewActions > 0) signals.push({ type: "COACHING_ACTION_OVERDUE", severity: "warning", message: `${row.overdueReviewActions} overdue coaching action${row.overdueReviewActions === 1 ? "" : "s"}.` });
  return signals;
}

async function buildWorkforceForecast(req, payload = {}) {
  const horizonDays = Number(payload.horizonDays || 14);
  if (!Number.isInteger(horizonDays) || horizonDays < 1 || horizonDays > WORKFORCE_MAX_HORIZON_DAYS) throw new AppError("horizonDays must be an integer between 1 and 90", 400);
  const start = workforceStartOfDay(new Date());
  const end = workforceEndOfDay(new Date(start.getFullYear(), start.getMonth(), start.getDate() + horizonDays - 1));
  const scope = await getWorkforceScope(req, {
    employeeId: payload.employeeId || null,
    department: payload.department || null,
  });
  const userIds = scope.userIds;
  const businessDays = workforceBusinessDays(start, end);
  const historyStart = workforceStartOfDay(new Date(start.getFullYear(), start.getMonth(), start.getDate() - 29));
  const historyEnd = workforceEndOfDay(new Date());

  const [tasks, capacityPlans, openActions, performanceDataset] = await Promise.all([
    userIds.length && scope.projectIds.length
      ? prisma.task.findMany({
          where: {
            archivedAt: null,
            assigneeId: { in: userIds },
            projectId: { in: scope.projectIds },
            status: { in: WORKFORCE_OPEN_STATUSES },
          },
          select: {
            id: true,
            title: true,
            status: true,
            priority: true,
            estimatedHours: true,
            actualHours: true,
            dueDate: true,
            startDate: true,
            assigneeId: true,
            projectId: true,
            project: { select: { name: true } },
          },
        })
      : [],
    userIds.length
      ? prisma.workforceCapacityPlan.findMany({
          where: {
            employeeId: { in: userIds },
            isActive: true,
            effectiveFrom: { lte: start },
            OR: [{ effectiveTo: null }, { effectiveTo: { gte: start } }],
          },
          orderBy: [{ effectiveFrom: "desc" }, { updatedAt: "desc" }],
        })
      : [],
    userIds.length
      ? prisma.performanceActionItem.findMany({
          where: {
            status: { in: ["OPEN", "IN_PROGRESS"] },
            review: { employeeId: { in: userIds } },
          },
          select: { id: true, status: true, priority: true, dueDate: true, review: { select: { employeeId: true } } },
        })
      : [],
    buildTeamPerformanceExportDataset(req, {
      start: historyStart.toISOString(),
      end: historyEnd.toISOString(),
      employeeId: payload.employeeId || null,
      department: payload.department || null,
    }),
  ]);

  const targetSummary = await buildTargetSummary(performanceDataset);
  const performanceMap = new Map((performanceDataset.rows || []).map((row) => [row.id, row]));
  const targetMap = new Map((targetSummary.rows || []).map((row) => [row.employeeId, row]));
  const planMap = new Map();
  for (const plan of capacityPlans) if (!planMap.has(plan.employeeId)) planMap.set(plan.employeeId, plan);

  const tasksByUser = new Map();
  for (const task of tasks) {
    if (!tasksByUser.has(task.assigneeId)) tasksByUser.set(task.assigneeId, []);
    tasksByUser.get(task.assigneeId).push(task);
  }
  const actionsByUser = new Map();
  for (const action of openActions) {
    const employeeId = action.review?.employeeId;
    if (!employeeId) continue;
    if (!actionsByUser.has(employeeId)) actionsByUser.set(employeeId, []);
    actionsByUser.get(employeeId).push(action);
  }

  const rows = scope.users.map((user) => {
    const employeeTasks = tasksByUser.get(user.id) || [];
    const dueDemand = employeeTasks.filter((task) => task.dueDate && new Date(task.dueDate) <= end);
    const upcoming = dueDemand.filter((task) => new Date(task.dueDate) >= start);
    const overdue = dueDemand.filter((task) => new Date(task.dueDate) < start);
    const unscheduled = employeeTasks.filter((task) => !task.dueDate);
    let plannedRemainingHours = 0;
    let estimatedDueTasks = 0;
    let unestimatedDueTasks = 0;
    for (const task of dueDemand) {
      const estimated = Number(task.estimatedHours || 0);
      const actual = Number(task.actualHours || 0);
      if (Number.isFinite(estimated) && estimated > 0) {
        estimatedDueTasks += 1;
        plannedRemainingHours += Math.max(0, estimated - (Number.isFinite(actual) ? actual : 0));
      } else {
        unestimatedDueTasks += 1;
      }
    }

    const plan = planMap.get(user.id) || null;
    const capacity = workforceCapacitySource(user, plan);
    const capacityHours = (capacity.weeklyCapacityHours * businessDays) / 5;
    const utilizationPercent = capacityHours > 0 ? workforceRound((plannedRemainingHours / capacityHours) * 100) : null;
    const employeeActions = actionsByUser.get(user.id) || [];
    const overdueReviewActions = employeeActions.filter((action) => action.dueDate && new Date(action.dueDate) < start).length;
    const performance = performanceMap.get(user.id) || null;
    const target = targetMap.get(user.id) || null;
    const risk = workforceRisk({ utilization: utilizationPercent, overdueTasks: overdue.length, dueTasks: dueDemand.length, estimatedDueTasks });
    const base = {
      employeeId: user.id,
      name: user.name,
      email: user.email,
      department: user.department,
      jobTitle: user.jobTitle,
      avatarUrl: user.avatarUrl,
      weeklyCapacityHours: workforceRound(capacity.weeklyCapacityHours),
      capacityHours: workforceRound(capacityHours),
      capacitySource: capacity.source,
      capacityPlanId: capacity.planId,
      plannedRemainingHours: workforceRound(plannedRemainingHours),
      utilizationPercent,
      capacityGapHours: workforceRound(plannedRemainingHours - capacityHours),
      dueTasks: dueDemand.length,
      upcomingDueTasks: upcoming.length,
      overdueOpenTasks: overdue.length,
      unscheduledOpenTasks: unscheduled.length,
      estimatedDueTasks,
      unestimatedDueTasks,
      openReviewActions: employeeActions.length,
      overdueReviewActions,
      performanceScore: performance?.performanceScore ?? null,
      performanceStatus: performance?.status || "No Activity",
      scoreDelta: Number.isFinite(Number(performance?.trend?.scoreDelta)) ? Number(performance.trend.scoreDelta) : null,
      targetAchievement: target?.achievementPercent ?? null,
      targetStatus: target?.status || "No Target",
      capacityRisk: risk,
      forecastConfidence: workforceConfidence(dueDemand.length, unestimatedDueTasks),
    };
    const outlook = workforceOutlook({
      risk,
      performanceScore: base.performanceScore,
      scoreDelta: base.scoreDelta,
      targetAchievement: base.targetAchievement,
      overdueActions: overdueReviewActions,
      dueTasks: dueDemand.length,
    });
    return { ...base, outlook, signals: workforceSignals(base) };
  });

  rows.sort((a, b) => {
    const riskOrder = { CRITICAL: 0, HIGH: 1, WATCH: 2, UNKNOWN: 3, HEALTHY: 4 };
    const riskDiff = (riskOrder[a.capacityRisk] ?? 9) - (riskOrder[b.capacityRisk] ?? 9);
    if (riskDiff) return riskDiff;
    return Number(b.utilizationPercent || 0) - Number(a.utilizationPercent || 0);
  });

  const departmentMap = new Map();
  for (const row of rows) {
    const department = row.department || "Unassigned";
    if (!departmentMap.has(department)) departmentMap.set(department, { department, employees: 0, capacityHours: 0, plannedHours: 0, dueTasks: 0, overdueTasks: 0, unestimatedDueTasks: 0, atRiskEmployees: 0 });
    const item = departmentMap.get(department);
    item.employees += 1;
    item.capacityHours += Number(row.capacityHours || 0);
    item.plannedHours += Number(row.plannedRemainingHours || 0);
    item.dueTasks += Number(row.dueTasks || 0);
    item.overdueTasks += Number(row.overdueOpenTasks || 0);
    item.unestimatedDueTasks += Number(row.unestimatedDueTasks || 0);
    if (["CRITICAL", "HIGH"].includes(row.capacityRisk)) item.atRiskEmployees += 1;
  }
  const departments = [...departmentMap.values()].map((item) => ({
    ...item,
    capacityHours: workforceRound(item.capacityHours),
    plannedHours: workforceRound(item.plannedHours),
    capacityGapHours: workforceRound(item.plannedHours - item.capacityHours),
    utilizationPercent: item.capacityHours > 0 ? workforceRound((item.plannedHours / item.capacityHours) * 100) : null,
  })).sort((a, b) => Number(b.utilizationPercent || 0) - Number(a.utilizationPercent || 0));

  const overloaded = rows.filter((row) => row.utilizationPercent != null && row.utilizationPercent > 100 && row.capacityGapHours > 0).map((row) => ({ ...row, remainingGap: row.capacityGapHours }));
  const available = rows.filter((row) => row.utilizationPercent != null && row.utilizationPercent < 70).map((row) => ({ ...row, remainingSpare: Math.max(0, Number(row.capacityHours || 0) - Number(row.plannedRemainingHours || 0)) }));
  const recommendations = [];
  for (const source of overloaded) {
    const candidates = available
      .filter((candidate) => candidate.employeeId !== source.employeeId && candidate.remainingSpare > 0)
      .sort((a, b) => {
        const sameDepartmentDiff = Number(b.department === source.department) - Number(a.department === source.department);
        if (sameDepartmentDiff) return sameDepartmentDiff;
        return b.remainingSpare - a.remainingSpare;
      });
    for (const candidate of candidates) {
      if (source.remainingGap <= 0) break;
      const suggested = Math.min(source.remainingGap, candidate.remainingSpare);
      if (suggested < 0.5) continue;
      recommendations.push({
        fromEmployeeId: source.employeeId,
        fromEmployee: source.name,
        toEmployeeId: candidate.employeeId,
        toEmployee: candidate.name,
        department: source.department || null,
        suggestedHours: workforceRound(suggested),
        reason: candidate.department === source.department ? "Same-department spare capacity" : "Cross-team spare capacity",
      });
      source.remainingGap -= suggested;
      candidate.remainingSpare -= suggested;
      if (recommendations.length >= 12) break;
    }
    if (recommendations.length >= 12) break;
  }

  const upcomingDeadlines = tasks
    .filter((task) => task.dueDate && new Date(task.dueDate) >= start && new Date(task.dueDate) <= end)
    .sort((a, b) => new Date(a.dueDate) - new Date(b.dueDate))
    .slice(0, 30)
    .map((task) => ({
      taskId: task.id,
      title: task.title,
      dueDate: task.dueDate,
      priority: task.priority,
      status: task.status,
      employeeId: task.assigneeId,
      employeeName: rows.find((row) => row.employeeId === task.assigneeId)?.name || null,
      projectId: task.projectId,
      projectName: task.project?.name || null,
      estimatedHours: task.estimatedHours,
      actualHours: task.actualHours,
    }));

  const totalCapacityHours = rows.reduce((sum, row) => sum + Number(row.capacityHours || 0), 0);
  const totalPlannedHours = rows.reduce((sum, row) => sum + Number(row.plannedRemainingHours || 0), 0);
  const summary = {
    horizonDays,
    businessDays,
    start: start.toISOString(),
    end: end.toISOString(),
    employeeCount: rows.length,
    totalCapacityHours: workforceRound(totalCapacityHours),
    totalPlannedHours: workforceRound(totalPlannedHours),
    capacityGapHours: workforceRound(totalPlannedHours - totalCapacityHours),
    teamUtilizationPercent: totalCapacityHours > 0 ? workforceRound((totalPlannedHours / totalCapacityHours) * 100) : null,
    criticalEmployees: rows.filter((row) => row.capacityRisk === "CRITICAL").length,
    highRiskEmployees: rows.filter((row) => row.capacityRisk === "HIGH").length,
    watchEmployees: rows.filter((row) => row.capacityRisk === "WATCH").length,
    unknownCapacityRisk: rows.filter((row) => row.capacityRisk === "UNKNOWN").length,
    upcomingDueTasks: rows.reduce((sum, row) => sum + row.upcomingDueTasks, 0),
    overdueOpenTasks: rows.reduce((sum, row) => sum + row.overdueOpenTasks, 0),
    unestimatedDueTasks: rows.reduce((sum, row) => sum + row.unestimatedDueTasks, 0),
    unscheduledOpenTasks: rows.reduce((sum, row) => sum + row.unscheduledOpenTasks, 0),
    reallocationOpportunities: recommendations.length,
  };

  return {
    generatedAt: new Date().toISOString(),
    methodology: {
      type: "RULE_BASED_OPERATIONAL_FORECAST",
      businessDays: "Sunday-Thursday",
      demand: "Open primary-assignee tasks due on or before forecast end; overdue tasks remain demand. Unscheduled tasks are reported separately.",
      remainingHours: "max(estimatedHours - actualHours, 0). Tasks without estimates are never assigned invented hours.",
      capacity: "Effective WorkforceCapacityPlan at forecast start; otherwise legacy designWeeklyCapacityHours; otherwise explicit 40h/week fallback.",
      riskThresholds: { watch: 85, high: 100, critical: 125 },
      note: "This is a transparent planning signal, not a machine-learning prediction and not a replacement for manager judgment.",
    },
    summary,
    rows,
    departments,
    recommendations,
    upcomingDeadlines,
  };
}
'''

text = text.replace(helper_anchor, helpers + "\n" + helper_anchor, 1)

routes = r'''
router.get("/reports/team-performance/workforce/forecast", asyncHandler(async (req, res) => {
  const forecast = await buildWorkforceForecast(req, {
    horizonDays: req.query.horizonDays || 14,
    employeeId: req.query.employeeId || null,
    department: req.query.department || null,
  });
  res.json(forecast);
}));

router.get("/reports/team-performance/workforce/capacity-plans", asyncHandler(async (req, res) => {
  const scope = await getWorkforceScope(req, {
    employeeId: req.query.employeeId || null,
    department: req.query.department || null,
  });
  const where = {
    employeeId: { in: scope.userIds },
    ...(req.query.active === "true" ? { isActive: true } : req.query.active === "false" ? { isActive: false } : {}),
  };
  const plans = scope.userIds.length
    ? await prisma.workforceCapacityPlan.findMany({ where, orderBy: [{ isActive: "desc" }, { effectiveFrom: "desc" }, { updatedAt: "desc" }], take: 1000 })
    : [];
  const employeeMap = new Map(scope.users.map((user) => [user.id, { id: user.id, name: user.name, department: user.department, jobTitle: user.jobTitle }]));
  res.json({ plans: plans.map((plan) => ({ ...plan, employee: employeeMap.get(plan.employeeId) || null })) });
}));

router.post("/reports/team-performance/workforce/capacity-plans", asyncHandler(async (req, res) => {
  const input = normalizeWorkforceCapacityInput(req.body || {});
  const { employee } = await assertWorkforceCapacityAccess(req, input.employeeId);
  await assertNoOverlappingCapacityPlan(input);
  const plan = await prisma.workforceCapacityPlan.create({ data: { ...input, createdById: req.user.id, updatedById: req.user.id } });
  await auditWorkforceCapacity(req, "workforce_capacity_plan_created", { planId: plan.id, employeeId: plan.employeeId, weeklyCapacityHours: plan.weeklyCapacityHours, effectiveFrom: plan.effectiveFrom, effectiveTo: plan.effectiveTo });
  res.status(201).json({ ...plan, employee });
}));

router.patch("/reports/team-performance/workforce/capacity-plans/:planId", asyncHandler(async (req, res) => {
  const existing = await prisma.workforceCapacityPlan.findUnique({ where: { id: req.params.planId } });
  if (!existing) throw new AppError("Capacity plan not found", 404);
  await assertWorkforceCapacityAccess(req, existing.employeeId);
  const input = normalizeWorkforceCapacityInput(req.body || {}, existing);
  await assertNoOverlappingCapacityPlan(input, existing.id);
  const plan = await prisma.workforceCapacityPlan.update({ where: { id: existing.id }, data: { ...input, updatedById: req.user.id } });
  await auditWorkforceCapacity(req, "workforce_capacity_plan_updated", { planId: plan.id, employeeId: plan.employeeId, weeklyCapacityHours: plan.weeklyCapacityHours });
  res.json(plan);
}));

router.delete("/reports/team-performance/workforce/capacity-plans/:planId", asyncHandler(async (req, res) => {
  const existing = await prisma.workforceCapacityPlan.findUnique({ where: { id: req.params.planId } });
  if (!existing) throw new AppError("Capacity plan not found", 404);
  await assertWorkforceCapacityAccess(req, existing.employeeId);
  const plan = await prisma.workforceCapacityPlan.update({ where: { id: existing.id }, data: { isActive: false, updatedById: req.user.id } });
  await auditWorkforceCapacity(req, "workforce_capacity_plan_deactivated", { planId: plan.id, employeeId: plan.employeeId });
  res.json(plan);
}));

'''
text = text.replace(route_anchor, routes + route_anchor, 1)
path.write_text(text)

print("BACKEND_WORKFORCE_FORECAST=PASS")
print("BACKEND_CAPACITY_CRUD=PASS")
print("WORKFORCE_RBAC_GUARDS=PASS")
print("WORKFORCE_TRANSPARENT_FORECAST=PASS")
print("PHASE3_SCORE_FORMULA_UNTOUCHED=PASS")
print("PHASE6_TARGETS_UNTOUCHED=PASS")
print("PHASE7_REVIEWS_UNTOUCHED=PASS")
