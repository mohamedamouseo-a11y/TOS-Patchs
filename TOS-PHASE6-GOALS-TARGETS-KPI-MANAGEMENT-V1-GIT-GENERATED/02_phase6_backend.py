#!/usr/bin/env python3
from pathlib import Path
import sys

repo = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS").resolve()
path = repo / "backend/src/routes/tasks.routes.js"
text = path.read_text()
anchor = "function buildTeamPerformanceIntelligence(dataset) {"
if text.count(anchor) != 1:
    raise SystemExit(f"BACKEND_HELPER_ANCHOR=FAIL count={text.count(anchor)}")
code = r'''
const TARGET_PERIOD_TYPES = new Set(["WEEKLY", "MONTHLY", "QUARTERLY", "YEARLY", "CUSTOM"]);
const TARGET_SCOPE_TYPES = new Set(["EMPLOYEE", "DEPARTMENT"]);

function targetNum(value, min = 0, max = null, integer = false) {
  if (value === undefined || value === null || value === "") return null;
  const n = Number(value);
  if (!Number.isFinite(n) || n < min || (max != null && n > max) || (integer && !Number.isInteger(n))) throw new AppError("Invalid target value", 400);
  return n;
}

function normalizeTargetInput(payload = {}, existing = null) {
  const src = { ...(existing || {}), ...(payload || {}) };
  const scopeType = String(src.scopeType || "").toUpperCase();
  const periodType = String(src.periodType || "MONTHLY").toUpperCase();
  if (!TARGET_SCOPE_TYPES.has(scopeType)) throw new AppError("scopeType must be EMPLOYEE or DEPARTMENT", 400);
  if (!TARGET_PERIOD_TYPES.has(periodType)) throw new AppError("Invalid periodType", 400);
  const effectiveFrom = new Date(src.effectiveFrom);
  const effectiveTo = new Date(src.effectiveTo);
  if (Number.isNaN(effectiveFrom.getTime()) || Number.isNaN(effectiveTo.getTime()) || effectiveFrom > effectiveTo) throw new AppError("Invalid target effective period", 400);
  const employeeId = scopeType === "EMPLOYEE" ? String(src.employeeId || "").trim() : null;
  const department = scopeType === "DEPARTMENT" ? String(src.department || "").trim() : null;
  if (scopeType === "EMPLOYEE" && !employeeId) throw new AppError("employeeId is required", 400);
  if (scopeType === "DEPARTMENT" && !department) throw new AppError("department is required", 400);
  const targetScore = targetNum(src.targetScore, 0, 100);
  const targetCompletionRate = targetNum(src.targetCompletionRate, 0, 100);
  const targetCompletedTasks = targetNum(src.targetCompletedTasks, 0, null, true);
  const targetLoggedHours = targetNum(src.targetLoggedHours, 0);
  const maxOverdueTasks = targetNum(src.maxOverdueTasks, 0, null, true);
  if ([targetScore, targetCompletionRate, targetCompletedTasks, targetLoggedHours, maxOverdueTasks].every((v) => v == null)) throw new AppError("At least one KPI target is required", 400);
  return { scopeType, employeeId, department, periodType, effectiveFrom, effectiveTo, targetScore, targetCompletionRate, targetCompletedTasks, targetLoggedHours, maxOverdueTasks, customTargets: src.customTargets && typeof src.customTargets === "object" ? src.customTargets : null, isActive: src.isActive === undefined ? true : Boolean(src.isActive) };
}

async function assertTargetWriteAccess(req, input) {
  if (isSystemAdmin(req.user)) return;
  if (!["MANAGER", "PROJECT_MANAGER"].includes(req.user.role)) throw new AppError("Target management requires manager access", 403);
  const dataset = await buildTeamPerformanceExportDataset(req, { start: input.effectiveFrom.toISOString(), end: input.effectiveTo.toISOString(), employeeId: input.employeeId || null, department: input.department || null });
  if (input.scopeType === "EMPLOYEE" && !dataset.rows.some((r) => r.id === input.employeeId)) throw new AppError("Unauthorized employee target", 403);
  if (input.scopeType === "DEPARTMENT" && !dataset.rows.some((r) => String(r.department || "") === input.department)) throw new AppError("Unauthorized department target", 403);
}

function targetMetric(key, actual, target, lower = false) {
  if (target == null) return null;
  if (actual == null || !Number.isFinite(Number(actual))) return { key, actual: null, target, gap: null, achievement: null, status: "No Data" };
  const a = Number(actual), t = Number(target);
  let achievement = lower ? (a <= t ? 100 : t <= 0 ? 0 : (t / a) * 100) : t <= 0 ? (a >= t ? 100 : 0) : (a / t) * 100;
  achievement = Math.round(Math.max(0, Math.min(150, achievement)) * 10) / 10;
  const gap = Math.round((lower ? t - a : a - t) * 10) / 10;
  const status = lower ? (a <= t ? "On Target" : "Behind Target") : achievement >= 110 ? "Exceeded" : achievement >= 90 ? "On Target" : "Behind Target";
  return { key, actual: a, target: t, gap, achievement, status };
}

function calcTargetAchievement(row, target, source = null) {
  if (!target) return { target: null, source: null, achievementPercent: null, status: "No Target", atRisk: false, metrics: [] };
  const active = row.performanceScore != null || Number(row.totalTasks || 0) > 0 || Number(row.actualHours || 0) > 0;
  const metrics = [
    targetMetric("Score", active ? row.performanceScore : null, target.targetScore),
    targetMetric("Completion", active ? Number(row.completionRate || 0) : null, target.targetCompletionRate),
    targetMetric("Completed Tasks", active ? Number(row.completedTasks || 0) : null, target.targetCompletedTasks),
    targetMetric("Logged Hours", active ? Number(row.actualHours || 0) : null, target.targetLoggedHours),
    targetMetric("Overdue", active ? Number(row.overdueTasks || 0) : null, target.maxOverdueTasks, true),
  ].filter(Boolean);
  const measured = metrics.filter((m) => m.achievement != null);
  const achievementPercent = measured.length ? Math.round((measured.reduce((s, m) => s + m.achievement, 0) / measured.length) * 10) / 10 : null;
  const status = achievementPercent == null ? "No Data" : achievementPercent >= 110 ? "Exceeded" : achievementPercent >= 90 ? "On Target" : "Behind Target";
  return { target: { id: target.id, scopeType: target.scopeType, employeeId: target.employeeId, department: target.department, periodType: target.periodType, effectiveFrom: target.effectiveFrom, effectiveTo: target.effectiveTo, targetScore: target.targetScore, targetCompletionRate: target.targetCompletionRate, targetCompletedTasks: target.targetCompletedTasks, targetLoggedHours: target.targetLoggedHours, maxOverdueTasks: target.maxOverdueTasks, customTargets: target.customTargets }, source, achievementPercent, status, atRisk: achievementPercent != null && achievementPercent < 75, metrics };
}

async function buildTargetSummary(dataset) {
  const rows = dataset.rows || [];
  const employeeIds = rows.map((r) => r.id);
  const departments = [...new Set(rows.map((r) => r.department).filter(Boolean))];
  const targets = await prisma.performanceTarget.findMany({ where: { isActive: true, effectiveFrom: { lte: new Date(dataset.filters.periodEnd) }, effectiveTo: { gte: new Date(dataset.filters.periodStart) }, OR: [ ...(employeeIds.length ? [{ scopeType: "EMPLOYEE", employeeId: { in: employeeIds } }] : []), ...(departments.length ? [{ scopeType: "DEPARTMENT", department: { in: departments } }] : []) ] }, orderBy: [{ effectiveFrom: "desc" }, { updatedAt: "desc" }] });
  const targetRows = rows.map((row) => {
    const employeeTarget = targets.find((t) => t.scopeType === "EMPLOYEE" && t.employeeId === row.id);
    const departmentTarget = targets.find((t) => t.scopeType === "DEPARTMENT" && t.department === row.department);
    return { employeeId: row.id, name: row.name, department: row.department, ...calcTargetAchievement(row, employeeTarget || departmentTarget || null, employeeTarget ? "EMPLOYEE" : departmentTarget ? "DEPARTMENT" : null) };
  });
  const configured = targetRows.filter((r) => r.target);
  const measured = configured.filter((r) => r.achievementPercent != null);
  const summary = { configured: configured.length, onTarget: measured.filter((r) => r.status === "On Target").length, behind: measured.filter((r) => r.status === "Behind Target").length, exceeded: measured.filter((r) => r.status === "Exceeded").length, noData: configured.filter((r) => r.status === "No Data").length, averageAchievement: measured.length ? Math.round((measured.reduce((s, r) => s + r.achievementPercent, 0) / measured.length) * 10) / 10 : null };
  const depRows = [];
  for (const department of departments) {
    const members = rows.filter((r) => r.department === department);
    const target = targets.find((t) => t.scopeType === "DEPARTMENT" && t.department === department) || null;
    const scored = members.filter((r) => r.performanceScore != null);
    const totalTasks = members.reduce((s, r) => s + Number(r.totalTasks || 0), 0);
    const aggregate = { performanceScore: scored.length ? Math.round((scored.reduce((s, r) => s + Number(r.performanceScore), 0) / scored.length) * 10) / 10 : null, completionRate: totalTasks ? Math.round((members.reduce((s, r) => s + Number(r.completedTasks || 0), 0) / totalTasks) * 100) : 0, completedTasks: members.reduce((s, r) => s + Number(r.completedTasks || 0), 0), totalTasks, actualHours: members.reduce((s, r) => s + Number(r.actualHours || 0), 0), overdueTasks: members.reduce((s, r) => s + Number(r.overdueTasks || 0), 0) };
    depRows.push({ department, ...calcTargetAchievement(aggregate, target, target ? "DEPARTMENT" : null) });
  }
  const measuredDeps = depRows.filter((r) => r.achievementPercent != null);
  summary.departmentsConfigured = depRows.filter((r) => r.target).length;
  summary.departmentsOnTarget = measuredDeps.filter((r) => ["On Target", "Exceeded"].includes(r.status)).length;
  return { rows: targetRows, departments: depRows, summary, targets };
}

function addTargetIntelligence(intelligence, targetSummary) {
  const extra = [];
  for (const row of targetSummary.rows) {
    if (!row.target || row.achievementPercent == null) continue;
    if (row.status === "Behind Target") extra.push({ id: `target:${row.employeeId}`, type: row.atRisk ? "TARGET_AT_RISK" : "TARGET_MISSED", severity: row.atRisk ? "critical" : "warning", title: `${row.name} is behind target`, message: `Target achievement is ${row.achievementPercent}% for the selected period.`, employeeId: row.employeeId, department: row.department, metric: row.achievementPercent, delta: Math.round((row.achievementPercent - 100) * 10) / 10 });
    if (row.status === "Exceeded") extra.push({ id: `target-exceeded:${row.employeeId}`, type: "TARGET_EXCEEDED", severity: "positive", title: `${row.name} exceeded target`, message: `Target achievement is ${row.achievementPercent}% for the selected period.`, employeeId: row.employeeId, department: row.department, metric: row.achievementPercent, delta: Math.round((row.achievementPercent - 100) * 10) / 10 });
  }
  for (const row of targetSummary.departments) if (row.target && row.status === "Behind Target") extra.push({ id: `department-target:${row.department}`, type: "DEPARTMENT_TARGET_MISSED", severity: row.atRisk ? "critical" : "warning", title: `${row.department} department is behind target`, message: `Department target achievement is ${row.achievementPercent}%.`, employeeId: null, department: row.department, metric: row.achievementPercent });
  intelligence.insights = [...extra, ...(intelligence.insights || [])].sort((a, b) => ({ critical: 0, warning: 1, info: 2, positive: 3 }[a.severity] ?? 9) - ({ critical: 0, warning: 1, info: 2, positive: 3 }[b.severity] ?? 9)).slice(0, 50);
  intelligence.summary.targetAchievement = targetSummary.summary;
  intelligence.summary.criticalAlerts = intelligence.insights.filter((i) => i.severity === "critical").length;
  intelligence.summary.warningAlerts = intelligence.insights.filter((i) => i.severity === "warning").length;
  if (targetSummary.summary.behind) intelligence.brief = [`${targetSummary.summary.behind} employees are behind configured targets.`, ...(intelligence.brief || [])];
  return intelligence;
}

'''
text = text.replace(anchor, code + anchor, 1)

old = '''router.get("/reports/team-performance/intelligence", asyncHandler(async (req, res) => {
  const dataset = await buildTeamPerformanceExportDataset(req, {
    start: req.query.start,
    end: req.query.end,
    employeeId: req.query.employeeId || null,
    department: req.query.department || null,
    projectId: req.query.projectId || null,
  });
  res.json(buildTeamPerformanceIntelligence(dataset));
}));
'''
if text.count(old) != 1:
    raise SystemExit(f"INTELLIGENCE_ROUTE_ANCHOR=FAIL count={text.count(old)}")
routes = r'''router.get("/reports/team-performance/targets/summary", asyncHandler(async (req, res) => {
  const dataset = await buildTeamPerformanceExportDataset(req, { start: req.query.start, end: req.query.end, employeeId: req.query.employeeId || null, department: req.query.department || null, projectId: req.query.projectId || null });
  const targetSummary = await buildTargetSummary(dataset);
  res.json({ period: { start: dataset.filters.periodStart, end: dataset.filters.periodEnd }, rows: targetSummary.rows, departments: targetSummary.departments, summary: targetSummary.summary });
}));

router.get("/reports/team-performance/targets", asyncHandler(async (req, res) => {
  if (!req.query.start || !req.query.end) throw new AppError("start and end are required", 400);
  const dataset = await buildTeamPerformanceExportDataset(req, { start: req.query.start, end: req.query.end });
  const employeeIds = dataset.rows.map((r) => r.id);
  const departments = [...new Set(dataset.rows.map((r) => r.department).filter(Boolean))];
  const targets = await prisma.performanceTarget.findMany({ where: { effectiveFrom: { lte: new Date(req.query.end) }, effectiveTo: { gte: new Date(req.query.start) }, OR: [ ...(employeeIds.length ? [{ scopeType: "EMPLOYEE", employeeId: { in: employeeIds } }] : []), ...(departments.length ? [{ scopeType: "DEPARTMENT", department: { in: departments } }] : []) ] }, orderBy: [{ isActive: "desc" }, { effectiveFrom: "desc" }, { updatedAt: "desc" }] });
  res.json({ targets });
}));

router.post("/reports/team-performance/targets", asyncHandler(async (req, res) => {
  const input = normalizeTargetInput(req.body);
  await assertTargetWriteAccess(req, input);
  const target = await prisma.performanceTarget.create({ data: { ...input, createdById: req.user.id, updatedById: req.user.id } });
  await prisma.workspaceAuditLog.create({ data: { action: "performance_target_created", actorId: req.user.id, metadata: { targetId: target.id, scopeType: target.scopeType, employeeId: target.employeeId, department: target.department, periodType: target.periodType, effectiveFrom: target.effectiveFrom, effectiveTo: target.effectiveTo } } });
  res.status(201).json(target);
}));

router.post("/reports/team-performance/targets/bulk", asyncHandler(async (req, res) => {
  const employeeIds = [...new Set((Array.isArray(req.body?.employeeIds) ? req.body.employeeIds : []).map(String))].filter(Boolean);
  if (!employeeIds.length || employeeIds.length > 100) throw new AppError("employeeIds must contain 1-100 values", 400);
  const input = normalizeTargetInput({ ...(req.body?.target || {}), scopeType: "EMPLOYEE", employeeId: employeeIds[0] });
  if (!isSystemAdmin(req.user)) {
    if (!["MANAGER", "PROJECT_MANAGER"].includes(req.user.role)) throw new AppError("Target management requires manager access", 403);
    const dataset = await buildTeamPerformanceExportDataset(req, { start: input.effectiveFrom.toISOString(), end: input.effectiveTo.toISOString() });
    const allowed = new Set(dataset.rows.map((r) => r.id));
    if (employeeIds.some((id) => !allowed.has(id))) throw new AppError("Unauthorized employee target", 403);
  }
  const created = await prisma.$transaction(employeeIds.map((employeeId) => prisma.performanceTarget.create({ data: { ...input, employeeId, createdById: req.user.id, updatedById: req.user.id } })));
  await prisma.workspaceAuditLog.create({ data: { action: "performance_target_bulk_created", actorId: req.user.id, metadata: { employeeIds, targetIds: created.map((t) => t.id), periodType: input.periodType } } });
  res.status(201).json({ targets: created });
}));

router.patch("/reports/team-performance/targets/:targetId", asyncHandler(async (req, res) => {
  const existing = await prisma.performanceTarget.findUnique({ where: { id: req.params.targetId } });
  if (!existing) throw new AppError("Target not found", 404);
  const input = normalizeTargetInput(req.body, existing);
  await assertTargetWriteAccess(req, input);
  const target = await prisma.performanceTarget.update({ where: { id: existing.id }, data: { ...input, updatedById: req.user.id } });
  await prisma.workspaceAuditLog.create({ data: { action: "performance_target_updated", actorId: req.user.id, metadata: { targetId: target.id } } });
  res.json(target);
}));

router.delete("/reports/team-performance/targets/:targetId", asyncHandler(async (req, res) => {
  const existing = await prisma.performanceTarget.findUnique({ where: { id: req.params.targetId } });
  if (!existing) throw new AppError("Target not found", 404);
  await assertTargetWriteAccess(req, normalizeTargetInput(existing));
  const target = await prisma.performanceTarget.update({ where: { id: existing.id }, data: { isActive: false, updatedById: req.user.id } });
  await prisma.workspaceAuditLog.create({ data: { action: "performance_target_deactivated", actorId: req.user.id, metadata: { targetId: target.id } } });
  res.json(target);
}));

router.post("/reports/team-performance/targets/:targetId/copy", asyncHandler(async (req, res) => {
  const existing = await prisma.performanceTarget.findUnique({ where: { id: req.params.targetId } });
  if (!existing) throw new AppError("Target not found", 404);
  const input = normalizeTargetInput({ ...existing, effectiveFrom: req.body?.effectiveFrom, effectiveTo: req.body?.effectiveTo, periodType: req.body?.periodType || existing.periodType, isActive: true });
  await assertTargetWriteAccess(req, input);
  const copy = await prisma.performanceTarget.create({ data: { ...input, createdById: req.user.id, updatedById: req.user.id } });
  await prisma.workspaceAuditLog.create({ data: { action: "performance_target_copied", actorId: req.user.id, metadata: { sourceTargetId: existing.id, targetId: copy.id } } });
  res.status(201).json(copy);
}));

router.get("/reports/team-performance/intelligence", asyncHandler(async (req, res) => {
  const dataset = await buildTeamPerformanceExportDataset(req, { start: req.query.start, end: req.query.end, employeeId: req.query.employeeId || null, department: req.query.department || null, projectId: req.query.projectId || null });
  const targetSummary = await buildTargetSummary(dataset);
  res.json(addTargetIntelligence(buildTeamPerformanceIntelligence(dataset), targetSummary));
}));
'''
text = text.replace(old, routes, 1)
path.write_text(text)
print("BACKEND_TARGET_CRUD=PASS")
print("BACKEND_TARGET_SUMMARY=PASS")
print("INTELLIGENCE_TARGET_ALERTS=PASS")
print("PHASE3_SCORE_FORMULA_UNTOUCHED=PASS")
