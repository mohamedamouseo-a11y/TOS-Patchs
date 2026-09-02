#!/usr/bin/env python3
from pathlib import Path
import sys

repo = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
path = repo / "backend/src/routes/tasks.routes.js"
text = path.read_text()
anchor = "function buildTeamPerformanceIntelligence(dataset) {"
if "PHASE12_EXECUTIVE_WORKFORCE_COMMAND_CENTER" in text:
    raise SystemExit("Phase 12 backend already present")
if "PHASE11_RECOGNITION_REWARDS_CYCLES" not in text:
    raise SystemExit("Phase 11 backend baseline missing")
if anchor not in text:
    raise SystemExit("backend anchor missing")

code = r'''
// PHASE12_EXECUTIVE_WORKFORCE_COMMAND_CENTER
function assertExecutiveCommandAccess(req) {
  if (!isSystemAdmin(req.user)) throw new AppError("Executive Workforce Command Center requires admin access", 403);
}

function executiveRound(value, digits = 1) {
  if (value == null || !Number.isFinite(Number(value))) return null;
  const factor = 10 ** digits;
  return Math.round(Number(value) * factor) / factor;
}

function executiveSeverityRank(value) {
  if (value === "critical") return 0;
  if (value === "warning") return 1;
  if (value === "info") return 2;
  return 3;
}

function executiveTargetBehind(status) {
  const value = String(status || "").trim().toUpperCase().replaceAll(" ", "_");
  return ["BEHIND", "AT_RISK", "BELOW_TARGET", "MISSED"].includes(value);
}

async function buildExecutiveReviewSignals(employeeIds) {
  if (!employeeIds.length) {
    return { reviews: [], openReviews: 0, overdueFollowUps: 0, overdueActions: 0, perEmployee: new Map() };
  }
  const reviews = await prisma.performanceReview.findMany({
    where: { employeeId: { in: employeeIds } },
    include: { actions: true },
    orderBy: [{ updatedAt: "desc" }],
    take: 3000,
  });
  const now = new Date();
  const perEmployee = new Map();
  let openReviews = 0;
  let overdueFollowUps = 0;
  let overdueActions = 0;
  for (const review of reviews) {
    const closed = review.status === "COMPLETED";
    if (!closed) openReviews += 1;
    const followUpOverdue = !closed && review.followUpAt && new Date(review.followUpAt) < now;
    if (followUpOverdue) overdueFollowUps += 1;
    const overdueActionCount = (review.actions || []).filter((action) => {
      return ["OPEN", "IN_PROGRESS"].includes(action.status) && action.dueDate && new Date(action.dueDate) < now;
    }).length;
    overdueActions += overdueActionCount;
    if (!perEmployee.has(review.employeeId)) perEmployee.set(review.employeeId, { openReviews: 0, overdueFollowUps: 0, overdueActions: 0 });
    const row = perEmployee.get(review.employeeId);
    if (!closed) row.openReviews += 1;
    if (followUpOverdue) row.overdueFollowUps += 1;
    row.overdueActions += overdueActionCount;
  }
  return { reviews, openReviews, overdueFollowUps, overdueActions, perEmployee };
}

async function buildExecutiveCommandCenter(req, payload = {}) {
  assertExecutiveCommandAccess(req);
  const start = parseDashboardDate(payload.start, "start");
  const end = parseDashboardDate(payload.end, "end");
  if (!start || !end) throw new AppError("start and end are required", 400);
  if (start > end) throw new AppError("start must be before or equal end", 400);
  const horizonDays = Number(payload.horizonDays || 14);
  if (!Number.isInteger(horizonDays) || horizonDays < 1 || horizonDays > 90) throw new AppError("horizonDays must be an integer between 1 and 90", 400);

  const filters = {
    start: start.toISOString(),
    end: end.toISOString(),
    employeeId: payload.employeeId || null,
    department: payload.department || null,
  };
  const dataset = await buildTeamPerformanceExportDataset(req, filters);
  const employeeIds = (dataset.rows || []).map((row) => row.id);
  const employeeMap = new Map((dataset.rows || []).map((row) => [row.id, row]));

  const [targetSummary, workforce, skillMatrix, talent, recognition, reviewSignals] = await Promise.all([
    buildTargetSummary(dataset),
    buildWorkforceForecast(req, { horizonDays, employeeId: filters.employeeId, department: filters.department }),
    buildSkillMatrix(req, { employeeId: filters.employeeId, department: filters.department }),
    buildTalentOverview(req, filters),
    buildRecognitionOverview(req, { employeeId: filters.employeeId, department: filters.department }),
    buildExecutiveReviewSignals(employeeIds),
  ]);
  const intelligence = buildTeamPerformanceIntelligence(dataset);

  const scored = (dataset.rows || []).filter((row) => row.performanceScore != null);
  const averagePerformanceScore = scored.length
    ? executiveRound(scored.reduce((sum, row) => sum + Number(row.performanceScore || 0), 0) / scored.length)
    : null;
  const atRiskEmployees = (dataset.rows || []).filter((row) => row.status === "At Risk").length;
  const needsAttentionEmployees = (dataset.rows || []).filter((row) => row.status === "Needs Attention").length;
  const noActivityEmployees = (dataset.rows || []).filter((row) => row.performanceScore == null).length;
  const criticalCapacityEmployees = (workforce.rows || []).filter((row) => row.capacityRisk === "CRITICAL").length;
  const highCapacityEmployees = (workforce.rows || []).filter((row) => row.capacityRisk === "HIGH").length;
  const targetBehindEmployees = (targetSummary.rows || []).filter((row) => executiveTargetBehind(row.status)).length;

  const priorities = [];
  const addPriority = (item) => priorities.push({
    id: item.id,
    severity: item.severity || "info",
    domain: item.domain,
    title: item.title,
    detail: item.detail || null,
    employeeId: item.employeeId || null,
    employeeName: item.employeeName || null,
    department: item.department || null,
    source: item.source || null,
    suggestedAction: item.suggestedAction || null,
  });

  for (const row of dataset.rows || []) {
    if (row.status === "At Risk") addPriority({ id: `performance-risk:${row.id}`, severity: "critical", domain: "Performance", title: `${row.name} is At Risk`, detail: `Performance Score ${row.performanceScore ?? "—"}; ${row.overdueTasks || 0} overdue tasks.`, employeeId: row.id, employeeName: row.name, department: row.department, source: "Phase 3", suggestedAction: "Review delivery blockers and coaching actions." });
    else if (row.status === "Needs Attention") addPriority({ id: `performance-attention:${row.id}`, severity: "warning", domain: "Performance", title: `${row.name} needs attention`, detail: `Performance Score ${row.performanceScore ?? "—"}.`, employeeId: row.id, employeeName: row.name, department: row.department, source: "Phase 3", suggestedAction: "Review recent performance trend and open actions." });
    else if (row.performanceScore == null) addPriority({ id: `performance-no-data:${row.id}`, severity: "info", domain: "Performance", title: `${row.name} has no meaningful activity`, detail: "No Activity remains unscored and unranked.", employeeId: row.id, employeeName: row.name, department: row.department, source: "Phase 3", suggestedAction: "Confirm workload, availability, or assignment context." });
  }

  for (const row of workforce.rows || []) {
    if (row.capacityRisk === "CRITICAL") addPriority({ id: `capacity-critical:${row.employeeId}`, severity: "critical", domain: "Capacity", title: `${row.name} has critical capacity risk`, detail: `${row.utilizationPercent ?? "—"}% planned utilization; ${row.overdueOpenTasks || 0} overdue open tasks.`, employeeId: row.employeeId, employeeName: row.name, department: row.department, source: "Phase 8", suggestedAction: "Review workload allocation before adding new work." });
    else if (row.capacityRisk === "HIGH") addPriority({ id: `capacity-high:${row.employeeId}`, severity: "warning", domain: "Capacity", title: `${row.name} has high capacity risk`, detail: `${row.utilizationPercent ?? "—"}% planned utilization.`, employeeId: row.employeeId, employeeName: row.name, department: row.department, source: "Phase 8", suggestedAction: "Review near-term demand and available reallocation options." });
  }

  for (const row of targetSummary.rows || []) {
    if (!executiveTargetBehind(row.status)) continue;
    const employee = employeeMap.get(row.employeeId);
    addPriority({ id: `target-behind:${row.employeeId}`, severity: "warning", domain: "Targets", title: `${employee?.name || "Employee"} is behind target`, detail: row.achievementPercent == null ? "Target configured but achievement is not available." : `${row.achievementPercent}% target achievement.`, employeeId: row.employeeId, employeeName: employee?.name || null, department: employee?.department || null, source: "Phase 6", suggestedAction: "Review target gaps and current delivery plan." });
  }

  for (const row of skillMatrix.rows || []) {
    const critical = (row.skills || []).filter((skill) => skill.status === "CRITICAL_GAP");
    if (!critical.length) continue;
    addPriority({ id: `skill-gap:${row.employeeId}`, severity: critical.length >= 2 ? "critical" : "warning", domain: "Skills", title: `${row.name} has ${critical.length} critical skill gap${critical.length === 1 ? "" : "s"}`, detail: critical.slice(0, 3).map((skill) => skill.name).join(", "), employeeId: row.employeeId, employeeName: row.name, department: row.department, source: "Phase 9", suggestedAction: "Review competency requirements and active development plan." });
  }

  for (const [employeeId, review] of reviewSignals.perEmployee.entries()) {
    if (!review.overdueFollowUps && !review.overdueActions) continue;
    const employee = employeeMap.get(employeeId);
    addPriority({ id: `review-overdue:${employeeId}`, severity: review.overdueActions >= 2 ? "critical" : "warning", domain: "Reviews", title: `${employee?.name || "Employee"} has overdue coaching follow-up`, detail: `${review.overdueFollowUps} overdue review follow-up(s); ${review.overdueActions} overdue action(s).`, employeeId, employeeName: employee?.name || null, department: employee?.department || null, source: "Phase 7", suggestedAction: "Close or reschedule overdue coaching commitments." });
  }

  for (const role of talent.successionRoles || []) {
    if (!["CRITICAL", "HIGH"].includes(role.criticality) || role.covered) continue;
    addPriority({ id: `succession-gap:${role.id}`, severity: role.criticality === "CRITICAL" ? "critical" : "warning", domain: "Succession", title: `Succession gap: ${role.title}`, detail: `${role.department || "Company"} · ${role.criticality} role has no active successor candidate.`, department: role.department, source: "Phase 10", suggestedAction: "Nominate and develop at least one viable successor." });
  }

  if (Number(recognition.summary?.pendingNominations || 0) > 0) {
    addPriority({ id: "recognition-pending", severity: "info", domain: "Recognition", title: `${recognition.summary.pendingNominations} recognition decision${recognition.summary.pendingNominations === 1 ? "" : "s"} pending`, detail: "Pending nominations require explicit Admin approval or rejection.", source: "Phase 11", suggestedAction: "Review pending nominations in the recognition cycle." });
  }

  priorities.sort((a, b) => {
    const severity = executiveSeverityRank(a.severity) - executiveSeverityRank(b.severity);
    if (severity !== 0) return severity;
    return String(a.title || "").localeCompare(String(b.title || ""));
  });

  const departmentMap = new Map();
  const ensureDepartment = (name) => {
    const department = name || "Unassigned";
    if (!departmentMap.has(department)) departmentMap.set(department, {
      department,
      employeeCount: 0,
      scoredEmployees: 0,
      scoreTotal: 0,
      atRisk: 0,
      needsAttention: 0,
      noActivity: 0,
      targetBehind: 0,
      capacityCriticalHigh: 0,
      criticalSkillGaps: 0,
      successionGaps: 0,
      overdueReviewActions: 0,
      pendingRecognition: 0,
    });
    return departmentMap.get(department);
  };

  for (const row of dataset.rows || []) {
    const item = ensureDepartment(row.department);
    item.employeeCount += 1;
    if (row.performanceScore != null) { item.scoredEmployees += 1; item.scoreTotal += Number(row.performanceScore || 0); }
    if (row.status === "At Risk") item.atRisk += 1;
    if (row.status === "Needs Attention") item.needsAttention += 1;
    if (row.performanceScore == null) item.noActivity += 1;
  }
  for (const row of targetSummary.rows || []) {
    if (!executiveTargetBehind(row.status)) continue;
    ensureDepartment(employeeMap.get(row.employeeId)?.department).targetBehind += 1;
  }
  for (const row of workforce.rows || []) {
    if (["CRITICAL", "HIGH"].includes(row.capacityRisk)) ensureDepartment(row.department).capacityCriticalHigh += 1;
  }
  for (const row of skillMatrix.rows || []) ensureDepartment(row.department).criticalSkillGaps += Number(row.criticalGaps || 0);
  for (const role of talent.successionRoles || []) {
    if (["CRITICAL", "HIGH"].includes(role.criticality) && !role.covered) ensureDepartment(role.department).successionGaps += 1;
  }
  for (const [employeeId, review] of reviewSignals.perEmployee.entries()) ensureDepartment(employeeMap.get(employeeId)?.department).overdueReviewActions += Number(review.overdueActions || 0);
  for (const nomination of recognition.nominations || []) {
    if (nomination.status === "PENDING") ensureDepartment(nomination.employee?.department).pendingRecognition += 1;
  }

  const departments = [...departmentMap.values()].map((item) => ({
    ...item,
    averagePerformanceScore: item.scoredEmployees ? executiveRound(item.scoreTotal / item.scoredEmployees) : null,
    attentionSignals: item.atRisk + item.needsAttention + item.targetBehind + item.capacityCriticalHigh + item.criticalSkillGaps + item.successionGaps + item.overdueReviewActions,
  })).sort((a, b) => b.attentionSignals - a.attentionSignals || String(a.department).localeCompare(String(b.department)));

  const criticalPriorities = priorities.filter((item) => item.severity === "critical").length;
  const warningPriorities = priorities.filter((item) => item.severity === "warning").length;
  const brief = [];
  const attentionEmployees = atRiskEmployees + needsAttentionEmployees;
  if (attentionEmployees) brief.push(`${attentionEmployees} employee${attentionEmployees === 1 ? "" : "s"} need performance attention in the selected period.`);
  if (criticalCapacityEmployees || highCapacityEmployees) brief.push(`${criticalCapacityEmployees} critical and ${highCapacityEmployees} high capacity-risk employee${criticalCapacityEmployees + highCapacityEmployees === 1 ? "" : "s"} are visible in the ${horizonDays}-day outlook.`);
  if (Number(skillMatrix.summary?.criticalGaps || 0)) brief.push(`${skillMatrix.summary.criticalGaps} critical competency gap${skillMatrix.summary.criticalGaps === 1 ? "" : "s"} require development follow-through.`);
  if (Number(talent.summary?.uncoveredCriticalRoles || 0)) brief.push(`${talent.summary.uncoveredCriticalRoles} critical/high succession role${talent.summary.uncoveredCriticalRoles === 1 ? "" : "s"} have no active successor candidate.`);
  if (reviewSignals.overdueFollowUps || reviewSignals.overdueActions) brief.push(`${reviewSignals.overdueFollowUps} overdue review follow-up(s) and ${reviewSignals.overdueActions} overdue coaching action(s) need closure.`);
  if (Number(recognition.summary?.pendingNominations || 0)) brief.push(`${recognition.summary.pendingNominations} recognition nomination${recognition.summary.pendingNominations === 1 ? "" : "s"} await a human decision.`);
  if (!brief.length) brief.push("No material cross-workforce management issue is currently surfaced by the selected signals.");

  return {
    generatedAt: new Date().toISOString(),
    period: { start: start.toISOString(), end: end.toISOString(), workforceHorizonDays: horizonDays },
    methodology: {
      type: "EXECUTIVE_CROSS_WORKFORCE_DECISION_SUPPORT",
      principle: "This command center aggregates existing Phase 3-11 signals. It creates no replacement performance score, talent score, risk score, or automated employment decision.",
      performance: "Phase 3 Performance Score remains authoritative and No Activity remains null/unranked.",
      priorityQueue: "Items are ordered only by transparent severity buckets (critical, warning, info), not by a hidden composite score.",
      employmentDecisions: "TOS does not automatically promote, demote, terminate, compensate, reassign, recognize, or succession-select employees from this view.",
    },
    summary: {
      employeeCount: (dataset.rows || []).length,
      averagePerformanceScore,
      atRiskEmployees,
      needsAttentionEmployees,
      noActivityEmployees,
      targetBehindEmployees,
      criticalCapacityEmployees,
      highCapacityEmployees,
      criticalSkillGaps: Number(skillMatrix.summary?.criticalGaps || 0),
      overallSkillCoveragePercent: skillMatrix.summary?.overallCoveragePercent ?? null,
      uncoveredCriticalRoles: Number(talent.summary?.uncoveredCriticalRoles || 0),
      readyNowCandidates: Number(talent.summary?.readyNowCandidates || 0),
      pendingRecognitionDecisions: Number(recognition.summary?.pendingNominations || 0),
      openReviews: reviewSignals.openReviews,
      overdueReviewFollowUps: reviewSignals.overdueFollowUps,
      overdueReviewActions: reviewSignals.overdueActions,
      criticalPriorities,
      warningPriorities,
    },
    brief,
    priorities: priorities.slice(0, 30),
    departments,
    domains: {
      performance: {
        averageScore: averagePerformanceScore,
        atRisk: atRiskEmployees,
        needsAttention: needsAttentionEmployees,
        noActivity: noActivityEmployees,
        criticalAlerts: Number(intelligence.summary?.criticalAlerts || 0),
        warningAlerts: Number(intelligence.summary?.warningAlerts || 0),
      },
      targets: {
        configured: Number(targetSummary.summary?.configured || 0),
        onTarget: Number(targetSummary.summary?.onTarget || 0),
        behind: Number(targetSummary.summary?.behind || targetBehindEmployees || 0),
        exceeded: Number(targetSummary.summary?.exceeded || 0),
        averageAchievement: targetSummary.summary?.averageAchievement ?? null,
      },
      reviews: {
        open: reviewSignals.openReviews,
        overdueFollowUps: reviewSignals.overdueFollowUps,
        overdueActions: reviewSignals.overdueActions,
      },
      workforce: {
        teamUtilizationPercent: workforce.summary?.teamUtilizationPercent ?? null,
        critical: Number(workforce.summary?.criticalEmployees || 0),
        high: Number(workforce.summary?.highRiskEmployees || 0),
        watch: Number(workforce.summary?.watchEmployees || 0),
        reallocationOpportunities: Number(workforce.summary?.reallocationOpportunities || 0),
      },
      skills: {
        coveragePercent: skillMatrix.summary?.overallCoveragePercent ?? null,
        criticalGaps: Number(skillMatrix.summary?.criticalGaps || 0),
        unassessedRequired: Number(skillMatrix.summary?.unassessedRequired || 0),
        activePlans: Number(skillMatrix.summary?.activeDevelopmentPlans || 0),
      },
      talent: {
        assessedEmployees: Number(talent.summary?.assessedEmployees || 0),
        highPotentialEmployees: Number(talent.summary?.highPotentialEmployees || 0),
        criticalRoles: Number(talent.summary?.criticalRoles || 0),
        uncoveredCriticalRoles: Number(talent.summary?.uncoveredCriticalRoles || 0),
        readyNowCandidates: Number(talent.summary?.readyNowCandidates || 0),
      },
      recognition: {
        openCycles: Number(recognition.summary?.openCycles || 0),
        pendingNominations: Number(recognition.summary?.pendingNominations || 0),
        publishedRecognitions: Number(recognition.summary?.publishedRecognitions || 0),
        rewardsIssued: Number(recognition.summary?.rewardsIssued || 0),
      },
    },
  };
}

router.get("/reports/team-performance/executive-command-center", asyncHandler(async (req, res) => {
  const data = await buildExecutiveCommandCenter(req, {
    start: req.query.start,
    end: req.query.end,
    horizonDays: req.query.horizonDays || 14,
    employeeId: req.query.employeeId || null,
    department: req.query.department || null,
  });
  res.json(data);
}));

'''

path.write_text(text.replace(anchor, code + anchor, 1))
print("BACKEND_EXECUTIVE_COMMAND_CENTER=PASS")
