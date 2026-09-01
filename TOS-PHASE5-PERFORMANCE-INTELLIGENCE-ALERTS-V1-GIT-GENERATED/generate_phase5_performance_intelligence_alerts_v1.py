#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys

BASELINE = "d17484fa0b54b127ff7fab00d933973f63b233df"
TARGETS = [
    "backend/src/routes/tasks.routes.js",
    "frontend/src/lib/api.js",
    "frontend/src/pages/TeamPerformanceDashboard.jsx",
]

repo = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS").resolve()


def run(*args):
    return subprocess.check_output(args, cwd=repo, text=True).strip()


def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly 1 anchor, found {count}")
    return text.replace(old, new, 1)


head = run("git", "rev-parse", "HEAD")
if head != BASELINE:
    raise SystemExit(f"BASELINE_CHECK=FAIL expected={BASELINE} actual={head}")
print("BASELINE_CHECK=PASS")

status = run("git", "status", "--porcelain", "--", *TARGETS)
if status:
    print(status)
    raise SystemExit("TARGETS_CLEAN=FAIL")
print("TARGETS_CLEAN=PASS")

# -----------------------------------------------------------------------------
# Backend: deterministic intelligence built from the Phase 3/4 export dataset.
# No additional per-employee queries and no new score formula.
# -----------------------------------------------------------------------------
backend_path = repo / "backend/src/routes/tasks.routes.js"
backend = backend_path.read_text()
backend_anchor = "function teamPerformanceExportFilename(extension, startDate, endDate) {"
backend_insert = r'''function buildTeamPerformanceIntelligence(dataset) {
  const rows = Array.isArray(dataset?.rows) ? dataset.rows : [];
  const insights = [];
  const severityOrder = { critical: 0, warning: 1, info: 2, positive: 3 };
  const addInsight = (item) => insights.push({
    id: item.id,
    type: item.type,
    severity: item.severity || "info",
    title: item.title,
    message: item.message,
    employeeId: item.employeeId || null,
    department: item.department || null,
    metric: item.metric ?? null,
    delta: item.delta ?? null,
  });

  const scoredRows = rows.filter((row) => row.performanceScore != null);
  const noActivityRows = rows.filter((row) => row.performanceScore == null || row.status === "No Activity");
  const atRiskRows = rows.filter((row) => row.performanceScore != null && row.performanceScore < 50);
  const needsAttentionRows = rows.filter((row) => row.performanceScore != null && row.performanceScore >= 50 && row.performanceScore < 70);
  const overdueRows = rows.filter((row) => Number(row.overdueTasks || 0) > 0);

  const improvingRows = rows
    .filter((row) => Number.isFinite(Number(row.trend?.scoreDelta)) && Number(row.trend.scoreDelta) > 0)
    .sort((a, b) => Number(b.trend.scoreDelta) - Number(a.trend.scoreDelta));
  const decliningRows = rows
    .filter((row) => Number.isFinite(Number(row.trend?.scoreDelta)) && Number(row.trend.scoreDelta) < 0)
    .sort((a, b) => Number(a.trend.scoreDelta) - Number(b.trend.scoreDelta));

  const topImprover = improvingRows[0] || null;
  const biggestDrop = decliningRows[0] || null;

  for (const row of rows) {
    const delta = Number(row.trend?.scoreDelta);
    const overdue = Number(row.overdueTasks || 0);

    if (row.performanceScore != null && row.performanceScore < 50) {
      addInsight({
        id: `at-risk:${row.id}`,
        type: "AT_RISK",
        severity: "critical",
        title: `${row.name} is at risk`,
        message: `Performance score is ${row.performanceScore}. Review blockers, overdue work and workload before the next check-in.`,
        employeeId: row.id,
        department: row.department,
        metric: row.performanceScore,
      });
    } else if (row.performanceScore != null && row.performanceScore < 70) {
      addInsight({
        id: `needs-attention:${row.id}`,
        type: "NEEDS_ATTENTION",
        severity: "warning",
        title: `${row.name} needs attention`,
        message: `Performance score is ${row.performanceScore}. Focus the next review on delivery, due dates and workflow quality.`,
        employeeId: row.id,
        department: row.department,
        metric: row.performanceScore,
      });
    }

    if (Number.isFinite(delta) && delta <= -10) {
      addInsight({
        id: `score-drop:${row.id}`,
        type: "SCORE_DROP",
        severity: delta <= -20 ? "critical" : "warning",
        title: `${row.name} dropped ${Math.abs(delta)} points`,
        message: `Current score ${row.performanceScore ?? "—"} versus previous ${row.previous?.performanceScore ?? "—"}.`,
        employeeId: row.id,
        department: row.department,
        metric: row.performanceScore,
        delta,
      });
    }

    if (overdue >= 3) {
      addInsight({
        id: `overdue:${row.id}`,
        type: "OVERDUE_CONCENTRATION",
        severity: overdue >= 5 ? "critical" : "warning",
        title: `${row.name} has ${overdue} overdue tasks`,
        message: `Overdue work is concentrated on this employee in the selected period.`,
        employeeId: row.id,
        department: row.department,
        metric: overdue,
      });
    }

    if (row.performanceScore == null || row.status === "No Activity") {
      const wasPreviouslyActive = row.previous?.performanceScore != null;
      addInsight({
        id: `no-activity:${row.id}`,
        type: "NO_ACTIVITY",
        severity: wasPreviouslyActive ? "warning" : "info",
        title: `${row.name} has no performance activity`,
        message: wasPreviouslyActive
          ? `This employee had a previous score of ${row.previous.performanceScore} but has no meaningful activity in the selected period.`
          : "No meaningful task/activity data was recorded for the selected period.",
        employeeId: row.id,
        department: row.department,
      });
    }
  }

  if (topImprover && Number(topImprover.trend?.scoreDelta || 0) >= 5) {
    addInsight({
      id: `top-improver:${topImprover.id}`,
      type: "TOP_IMPROVER",
      severity: "positive",
      title: `${topImprover.name} is the top improver`,
      message: `Performance improved by ${topImprover.trend.scoreDelta} points versus the previous equal period.`,
      employeeId: topImprover.id,
      department: topImprover.department,
      metric: topImprover.performanceScore,
      delta: topImprover.trend.scoreDelta,
    });
  }

  const departmentMap = new Map();
  for (const row of rows) {
    const department = row.department || "Unassigned";
    if (!departmentMap.has(department)) {
      departmentMap.set(department, {
        department,
        employeeCount: 0,
        scoredEmployees: 0,
        scoreTotal: 0,
        completedTasks: 0,
        totalTasks: 0,
        overdueTasks: 0,
        actualHours: 0,
      });
    }
    const item = departmentMap.get(department);
    item.employeeCount += 1;
    if (row.performanceScore != null) {
      item.scoredEmployees += 1;
      item.scoreTotal += Number(row.performanceScore || 0);
    }
    item.completedTasks += Number(row.completedTasks || 0);
    item.totalTasks += Number(row.totalTasks || 0);
    item.overdueTasks += Number(row.overdueTasks || 0);
    item.actualHours += Number(row.actualHours || 0);
  }

  const departments = [...departmentMap.values()].map((item) => {
    const averageScore = item.scoredEmployees
      ? Math.round((item.scoreTotal / item.scoredEmployees) * 10) / 10
      : null;
    const completionRate = item.totalTasks
      ? Math.round((item.completedTasks / item.totalTasks) * 100)
      : 0;
    let status = "No Activity";
    if (averageScore != null) {
      if (averageScore >= 85) status = "Excellent";
      else if (averageScore >= 70) status = "On Track";
      else if (averageScore >= 50) status = "Needs Attention";
      else status = "At Risk";
    }
    return {
      department: item.department,
      employeeCount: item.employeeCount,
      scoredEmployees: item.scoredEmployees,
      averageScore,
      completionRate,
      completedTasks: item.completedTasks,
      totalTasks: item.totalTasks,
      overdueTasks: item.overdueTasks,
      actualHours: Math.round(item.actualHours * 10) / 10,
      status,
    };
  }).sort((a, b) => {
    if (a.averageScore == null && b.averageScore == null) return a.department.localeCompare(b.department);
    if (a.averageScore == null) return 1;
    if (b.averageScore == null) return -1;
    return b.averageScore - a.averageScore;
  });

  for (const department of departments) {
    if (department.averageScore != null && department.averageScore < 70) {
      addInsight({
        id: `department-score:${department.department}`,
        type: "DEPARTMENT_PERFORMANCE",
        severity: department.averageScore < 50 ? "critical" : "warning",
        title: `${department.department} department needs attention`,
        message: `Average score ${department.averageScore}, completion ${department.completionRate}%, overdue ${department.overdueTasks}.`,
        department: department.department,
        metric: department.averageScore,
      });
    } else if (department.overdueTasks >= 5) {
      addInsight({
        id: `department-overdue:${department.department}`,
        type: "DEPARTMENT_OVERDUE",
        severity: "warning",
        title: `${department.department} has ${department.overdueTasks} overdue tasks`,
        message: `Overdue work is concentrated in this department for the selected period.`,
        department: department.department,
        metric: department.overdueTasks,
      });
    }
  }

  const activeWorkload = rows.filter((row) => Number(row.totalTasks || 0) > 0 || Number(row.actualHours || 0) > 0);
  const useHours = activeWorkload.reduce((sum, row) => sum + Number(row.actualHours || 0), 0) > 0;
  const workloadValues = activeWorkload.map((row) => ({
    row,
    value: useHours ? Number(row.actualHours || 0) : Number(row.totalTasks || 0),
  }));
  const avgWorkload = workloadValues.length
    ? workloadValues.reduce((sum, item) => sum + item.value, 0) / workloadValues.length
    : 0;
  const maxWorkload = workloadValues.sort((a, b) => b.value - a.value)[0] || null;
  const imbalanceRatio = avgWorkload > 0 && maxWorkload ? maxWorkload.value / avgWorkload : 0;
  const workloadImbalanced = workloadValues.length >= 3 && imbalanceRatio >= 1.75;

  if (workloadImbalanced && maxWorkload) {
    addInsight({
      id: `workload:${maxWorkload.row.id}`,
      type: "WORKLOAD_IMBALANCE",
      severity: imbalanceRatio >= 2.25 ? "critical" : "warning",
      title: `Workload is concentrated on ${maxWorkload.row.name}`,
      message: useHours
        ? `${Math.round(maxWorkload.value * 10) / 10}h versus a team average of ${Math.round(avgWorkload * 10) / 10}h.`
        : `${maxWorkload.value} tasks versus a team average of ${Math.round(avgWorkload * 10) / 10} tasks.`,
      employeeId: maxWorkload.row.id,
      department: maxWorkload.row.department,
      metric: Math.round(imbalanceRatio * 100) / 100,
    });
  }

  insights.sort((a, b) => {
    const severityDiff = (severityOrder[a.severity] ?? 9) - (severityOrder[b.severity] ?? 9);
    if (severityDiff !== 0) return severityDiff;
    return String(a.title || "").localeCompare(String(b.title || ""));
  });

  const criticalCount = insights.filter((item) => item.severity === "critical").length;
  const warningCount = insights.filter((item) => item.severity === "warning").length;
  const totalOverdue = rows.reduce((sum, row) => sum + Number(row.overdueTasks || 0), 0);

  const brief = [];
  if (topImprover) brief.push(`${topImprover.name} improved by ${topImprover.trend.scoreDelta} points.`);
  if (biggestDrop) brief.push(`${biggestDrop.name} declined by ${Math.abs(biggestDrop.trend.scoreDelta)} points.`);
  if (totalOverdue > 0) brief.push(`${totalOverdue} overdue tasks require management attention.`);
  if (noActivityRows.length > 0) brief.push(`${noActivityRows.length} employees have no meaningful activity in this period.`);
  if (workloadImbalanced && maxWorkload) brief.push(`Workload concentration detected around ${maxWorkload.row.name}.`);
  if (!brief.length) brief.push("No material performance risks were detected for this period.");

  return {
    generatedAt: new Date().toISOString(),
    period: {
      start: dataset?.filters?.periodStart || null,
      end: dataset?.filters?.periodEnd || null,
    },
    summary: {
      topImprover: topImprover ? {
        id: topImprover.id,
        name: topImprover.name,
        score: topImprover.performanceScore,
        delta: topImprover.trend?.scoreDelta ?? null,
      } : null,
      biggestDrop: biggestDrop ? {
        id: biggestDrop.id,
        name: biggestDrop.name,
        score: biggestDrop.performanceScore,
        delta: biggestDrop.trend?.scoreDelta ?? null,
      } : null,
      atRiskCount: atRiskRows.length,
      needsAttentionCount: needsAttentionRows.length,
      noActivityCount: noActivityRows.length,
      overdueEmployeesCount: overdueRows.length,
      totalOverdue,
      criticalAlerts: criticalCount,
      warningAlerts: warningCount,
      workloadBalance: {
        status: workloadImbalanced ? "Imbalanced" : "Balanced",
        metric: useHours ? "hours" : "tasks",
        average: Math.round(avgWorkload * 10) / 10,
        max: maxWorkload ? Math.round(maxWorkload.value * 10) / 10 : 0,
        maxEmployee: maxWorkload?.row?.name || null,
        ratio: Math.round(imbalanceRatio * 100) / 100,
      },
    },
    brief,
    insights: insights.slice(0, 40),
    departments,
  };
}

router.get("/reports/team-performance/intelligence", asyncHandler(async (req, res) => {
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
backend = replace_once(backend, backend_anchor, backend_insert + backend_anchor, "BACKEND_INTELLIGENCE_ANCHOR")
backend_path.write_text(backend)
print("BACKEND_INTELLIGENCE_ROUTE=PASS")

# -----------------------------------------------------------------------------
# API wrapper
# -----------------------------------------------------------------------------
api_path = repo / "frontend/src/lib/api.js"
api = api_path.read_text()
api_anchor = '    teamPerformance: (params = {}) => request(`/api/tasks/reports/team-performance${queryString(params)}`),\n'
api_new = api_anchor + '    teamPerformanceIntelligence: (params = {}) => request(`/api/tasks/reports/team-performance/intelligence${queryString(params)}`),\n'
api = replace_once(api, api_anchor, api_new, "API_INTELLIGENCE_ANCHOR")
api_path.write_text(api)
print("FRONTEND_API_WRAPPER=PASS")

# -----------------------------------------------------------------------------
# Frontend state + fetch + Intelligence UI
# -----------------------------------------------------------------------------
front_path = repo / "frontend/src/pages/TeamPerformanceDashboard.jsx"
front = front_path.read_text()

state_anchor = '  const [toast, setToast] = useState(null);\n'
state_new = state_anchor + '''\n  const [intelligenceData, setIntelligenceData] = useState(null);\n  const [intelligenceLoading, setIntelligenceLoading] = useState(false);\n  const [intelligenceError, setIntelligenceError] = useState(\"\");\n'''
front = replace_once(front, state_anchor, state_new, "FRONTEND_INTELLIGENCE_STATE")

employees_anchor = '  const allEmployees = teamData?.byUser || [];\n'
effect = r'''  useEffect(() => {
    if (!selectedRange.start || !selectedRange.end || selectedRange.invalid) return;
    let ignore = false;
    async function loadIntelligence() {
      setIntelligenceLoading(true);
      setIntelligenceError("");
      try {
        const data = await api.tasks.teamPerformanceIntelligence({
          start: selectedRange.start.toISOString(),
          end: selectedRange.end.toISOString(),
          employeeId: employeeFilter !== "all" ? employeeFilter : "",
          department: departmentFilter !== "all" ? departmentFilter : "",
        });
        if (!ignore) setIntelligenceData(data);
      } catch (err) {
        if (!ignore) {
          setIntelligenceData(null);
          setIntelligenceError(getErrorMessage(err, "Unable to load performance intelligence."));
        }
      } finally {
        if (!ignore) setIntelligenceLoading(false);
      }
    }
    loadIntelligence();
    return () => { ignore = true; };
  }, [
    selectedRange.start?.getTime(),
    selectedRange.end?.getTime(),
    selectedRange.invalid,
    employeeFilter,
    departmentFilter,
    refreshNonce,
    realtimeRefreshVersion,
  ]);

'''
front = replace_once(front, employees_anchor, effect + employees_anchor, "FRONTEND_INTELLIGENCE_EFFECT")

team_card_anchor = '      <Card className="overflow-hidden p-0">\n'
intelligence_ui = r'''      <Card className="overflow-hidden p-0">
        <div className="flex flex-col gap-2 border-b border-zinc-100 p-4 dark:border-white/10 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-[11px] font-black uppercase tracking-[0.1em] text-amber-500">Performance Intelligence</p>
            <h2 className="mt-1 text-base font-black text-zinc-950 dark:text-white">Management Brief & Alerts</h2>
            <p className="mt-1 text-[11px] font-bold text-zinc-400">Rule-based insights from the same Phase 3 performance data — no separate score formula.</p>
          </div>
          <div className="flex items-center gap-2">
            {intelligenceData ? <Badge tone={Number(intelligenceData.summary?.criticalAlerts || 0) > 0 ? "danger" : Number(intelligenceData.summary?.warningAlerts || 0) > 0 ? "warning" : "success"}>{Number(intelligenceData.summary?.criticalAlerts || 0) + Number(intelligenceData.summary?.warningAlerts || 0)} alerts</Badge> : null}
            {intelligenceLoading ? <span className="text-[11px] font-black text-zinc-400">Analysing…</span> : null}
          </div>
        </div>

        {intelligenceError ? <div className="p-4"><Notice type="error">{intelligenceError}</Notice></div> : null}
        {intelligenceLoading && !intelligenceData ? (
          <div className="grid gap-3 p-4 sm:grid-cols-2 xl:grid-cols-4">{[1, 2, 3, 4].map((item) => <div key={item} className="h-24 animate-pulse rounded-2xl bg-zinc-100 dark:bg-white/[0.05]" />)}</div>
        ) : intelligenceData ? (
          <>
            <div className="grid gap-3 p-4 sm:grid-cols-2 xl:grid-cols-4">
              <div className="rounded-2xl border border-emerald-100 bg-emerald-50/70 p-3 dark:border-emerald-400/15 dark:bg-emerald-400/[0.06]">
                <p className="text-[10px] font-black uppercase tracking-[0.08em] text-emerald-600 dark:text-emerald-300">Top Improver</p>
                <p className="mt-2 truncate text-sm font-black text-zinc-950 dark:text-white">{intelligenceData.summary?.topImprover?.name || "—"}</p>
                <p className="mt-1 text-xs font-black text-emerald-600 dark:text-emerald-300">{intelligenceData.summary?.topImprover?.delta != null ? `+${intelligenceData.summary.topImprover.delta} points` : "No positive trend"}</p>
              </div>
              <div className="rounded-2xl border border-red-100 bg-red-50/70 p-3 dark:border-red-400/15 dark:bg-red-400/[0.06]">
                <p className="text-[10px] font-black uppercase tracking-[0.08em] text-red-600 dark:text-red-300">Biggest Drop</p>
                <p className="mt-2 truncate text-sm font-black text-zinc-950 dark:text-white">{intelligenceData.summary?.biggestDrop?.name || "—"}</p>
                <p className="mt-1 text-xs font-black text-red-600 dark:text-red-300">{intelligenceData.summary?.biggestDrop?.delta != null ? `${intelligenceData.summary.biggestDrop.delta} points` : "No negative trend"}</p>
              </div>
              <div className="rounded-2xl border border-orange-100 bg-orange-50/70 p-3 dark:border-orange-400/15 dark:bg-orange-400/[0.06]">
                <p className="text-[10px] font-black uppercase tracking-[0.08em] text-orange-600 dark:text-orange-300">Attention</p>
                <p className="mt-2 text-2xl font-black text-zinc-950 dark:text-white">{Number(intelligenceData.summary?.atRiskCount || 0) + Number(intelligenceData.summary?.needsAttentionCount || 0)}</p>
                <p className="mt-1 text-xs font-bold text-zinc-500 dark:text-zinc-400">{intelligenceData.summary?.totalOverdue || 0} overdue · {intelligenceData.summary?.noActivityCount || 0} no activity</p>
              </div>
              <div className="rounded-2xl border border-zinc-200 bg-zinc-50/70 p-3 dark:border-white/10 dark:bg-white/[0.035]">
                <p className="text-[10px] font-black uppercase tracking-[0.08em] text-zinc-500">Workload Balance</p>
                <p className="mt-2 text-sm font-black text-zinc-950 dark:text-white">{intelligenceData.summary?.workloadBalance?.status || "—"}</p>
                <p className="mt-1 text-xs font-bold text-zinc-500 dark:text-zinc-400">{intelligenceData.summary?.workloadBalance?.maxEmployee ? `${intelligenceData.summary.workloadBalance.maxEmployee} · ${intelligenceData.summary.workloadBalance.max}${intelligenceData.summary.workloadBalance.metric === "hours" ? "h" : " tasks"}` : "No active workload"}</p>
              </div>
            </div>

            <div className="grid gap-4 border-t border-zinc-100 p-4 dark:border-white/10 xl:grid-cols-[1.25fr_.75fr]">
              <section>
                <div className="mb-3 flex items-center justify-between gap-2">
                  <h3 className="text-sm font-black text-zinc-950 dark:text-white">Live Management Alerts</h3>
                  <span className="text-[10px] font-bold text-zinc-400">Critical first</span>
                </div>
                {intelligenceData.insights?.length ? (
                  <div className="grid gap-2 md:grid-cols-2">
                    {intelligenceData.insights.slice(0, 8).map((insight) => {
                      const tone = insight.severity === "critical"
                        ? "border-red-200 bg-red-50/70 dark:border-red-400/20 dark:bg-red-400/[0.06]"
                        : insight.severity === "warning"
                          ? "border-orange-200 bg-orange-50/70 dark:border-orange-400/20 dark:bg-orange-400/[0.06]"
                          : insight.severity === "positive"
                            ? "border-emerald-200 bg-emerald-50/70 dark:border-emerald-400/20 dark:bg-emerald-400/[0.06]"
                            : "border-zinc-200 bg-zinc-50 dark:border-white/10 dark:bg-white/[0.03]";
                      return (
                        <button key={insight.id} type="button" onClick={() => insight.employeeId ? openEmployee(insight.employeeId) : undefined} disabled={!insight.employeeId} className={`rounded-2xl border p-3 text-left transition ${tone} ${insight.employeeId ? "hover:-translate-y-0.5 hover:shadow-sm" : "cursor-default"}`}>
                          <div className="flex items-start gap-2">
                            <AlertCircle size={15} className={insight.severity === "critical" ? "mt-0.5 shrink-0 text-red-600" : insight.severity === "warning" ? "mt-0.5 shrink-0 text-orange-600" : insight.severity === "positive" ? "mt-0.5 shrink-0 text-emerald-600" : "mt-0.5 shrink-0 text-zinc-400"} />
                            <div className="min-w-0">
                              <p className="text-xs font-black text-zinc-950 dark:text-white">{insight.title}</p>
                              <p className="mt-1 text-[11px] leading-5 text-zinc-500 dark:text-zinc-400">{insight.message}</p>
                            </div>
                          </div>
                        </button>
                      );
                    })}
                  </div>
                ) : <div className="rounded-2xl border border-dashed border-zinc-200 p-5 text-center text-xs font-bold text-zinc-400 dark:border-white/10">No material alerts for this period.</div>}

                <div className="mt-4 rounded-2xl border border-zinc-100 bg-zinc-50/60 p-3 dark:border-white/10 dark:bg-white/[0.025]">
                  <p className="text-[10px] font-black uppercase tracking-[0.08em] text-zinc-400">Management Brief</p>
                  <div className="mt-2 space-y-1.5">
                    {(intelligenceData.brief || []).map((line, index) => <p key={`${line}-${index}`} className="text-xs font-bold text-zinc-700 dark:text-zinc-300">• {line}</p>)}
                  </div>
                </div>
              </section>

              <section>
                <div className="mb-3 flex items-center justify-between gap-2">
                  <h3 className="text-sm font-black text-zinc-950 dark:text-white">Department Performance</h3>
                  <span className="text-[10px] font-bold text-zinc-400">Same selected period</span>
                </div>
                <div className="space-y-2">
                  {(intelligenceData.departments || []).slice(0, 8).map((department) => (
                    <div key={department.department} className="rounded-xl border border-zinc-100 p-3 dark:border-white/10">
                      <div className="flex items-center justify-between gap-2">
                        <div className="min-w-0"><p className="truncate text-xs font-black text-zinc-950 dark:text-white">{department.department}</p><p className="mt-0.5 text-[10px] font-bold text-zinc-400">{department.completedTasks}/{department.totalTasks} completed · {department.overdueTasks} overdue</p></div>
                        <div className="text-right"><p className={`text-lg font-black ${scoreTextClass(department.averageScore)}`}>{department.averageScore ?? "—"}</p><p className="text-[9px] font-black text-zinc-400">{department.status}</p></div>
                      </div>
                      <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-zinc-100 dark:bg-white/10"><div className="h-full rounded-full bg-amber-400" style={{ width: `${Math.min(100, Math.max(0, Number(department.completionRate || 0)))}%` }} /></div>
                    </div>
                  ))}
                </div>
              </section>
            </div>
          </>
        ) : null}
      </Card>

'''
front = replace_once(front, team_card_anchor, intelligence_ui + team_card_anchor, "FRONTEND_INTELLIGENCE_UI")
front_path.write_text(front)
print("FRONTEND_INTELLIGENCE_UI=PASS")

# Static regression guards
backend_final = backend_path.read_text()
front_final = front_path.read_text()
api_final = api_path.read_text()
required_backend = [
    'router.get("/reports/team-performance/intelligence"',
    'buildTeamPerformanceExportDataset(req',
    'buildTeamPerformanceIntelligence(dataset)',
    'WORKLOAD_IMBALANCE',
    'DEPARTMENT_PERFORMANCE',
    'TOP_IMPROVER',
]
for marker in required_backend:
    if marker not in backend_final:
        raise SystemExit(f"STATIC_BACKEND_CHECK=FAIL missing={marker}")
if 'teamPerformanceIntelligence:' not in api_final:
    raise SystemExit("STATIC_API_CHECK=FAIL")
for marker in ["Management Brief & Alerts", "Department Performance", "Live Management Alerts", "intelligenceData"]:
    if marker not in front_final:
        raise SystemExit(f"STATIC_FRONTEND_CHECK=FAIL missing={marker}")

# Guard against new score formula in the intelligence helper: the new endpoint must
# consume the existing Phase 3/4 dataset and never calculate performanceScore itself.
inserted_backend = backend_insert
if "calculatePerformanceScore(" in inserted_backend or "performanceScore =" in inserted_backend:
    raise SystemExit("SCORE_FORMULA_REGRESSION=FAIL")
print("SCORE_FORMULA_REGRESSION=PASS")

subprocess.check_call(["node", "--check", str(backend_path)], cwd=repo)
print("BACKEND_SYNTAX=PASS")
subprocess.check_call(["npm", "run", "build"], cwd=repo / "frontend")
print("FRONTEND_BUILD=PASS")
subprocess.check_call(["git", "diff", "--check"], cwd=repo)
print("GIT_DIFF_CHECK=PASS")
print("PHASE5_PERFORMANCE_INTELLIGENCE_ALERTS_V1_APPLIED=YES")
print("NO_GIT_COMMIT_OR_PUSH_PERFORMED=YES")
