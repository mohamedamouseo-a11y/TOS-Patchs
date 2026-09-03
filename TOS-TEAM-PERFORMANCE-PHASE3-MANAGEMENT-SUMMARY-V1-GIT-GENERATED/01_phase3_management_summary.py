#!/usr/bin/env python3
from pathlib import Path

ROOT = Path('/var/www/TOS')
DASHBOARD = ROOT / 'frontend/src/pages/TeamPerformanceDashboard.jsx'
SUMMARY = ROOT / 'frontend/src/components/performance/ManagementSummary.jsx'


def fail(message: str):
    raise SystemExit(f'PHASE3 MANAGEMENT SUMMARY PATCH ERROR: {message}')


def insert_after(text: str, anchor: str, addition: str, label: str) -> str:
    if addition.strip() in text:
        return text
    if anchor not in text:
        fail(f'missing anchor: {label}')
    return text.replace(anchor, anchor + addition, 1)


text = DASHBOARD.read_text(encoding='utf-8')
original = text

# Preconditions: Phases 1-2, Executive Snapshot and archived members are already present.
for marker in [
    'ExecutiveCommandCenterPanel',
    'PerformancePeriodControl',
    'ArchivedPerformanceMembers',
    'phase1-goals-disclosure',
    'phase1-intelligence-disclosure',
    'phase1-deep-dive-disclosure',
]:
    if marker not in text:
        fail(f'expected existing Team Performance marker missing: {marker}')

# 1) Import the compact Phase 3 management summary.
import_anchor = 'import { ArchivedPerformanceMembers } from "../components/performance/ArchivedPerformanceMembers";\n'
text = insert_after(
    text,
    import_anchor,
    'import { ManagementSummary } from "../components/performance/ManagementSummary";\n',
    'ArchivedPerformanceMembers import',
)

# 2) Insert after the five core KPIs and before the Executive Command Center.
anchor = '''        <KpiCard icon={Clock3} label="Logged hours" value={formatHours(filteredSummary.hours)} note="Actual task hours" tone="neutral" comparison={compareMode !== "off" ? { current: filteredSummary.hours, previous: comparisonSummary.hours, unit: "h", label: "vs comparison", precision: 1 } : null} />\n      </div>\n\n      <ExecutiveCommandCenterPanel'''
replacement = '''        <KpiCard icon={Clock3} label="Logged hours" value={formatHours(filteredSummary.hours)} note="Actual task hours" tone="neutral" comparison={compareMode !== "off" ? { current: filteredSummary.hours, previous: comparisonSummary.hours, unit: "h", label: "vs comparison", precision: 1 } : null} />\n      </div>\n\n      <ManagementSummary\n        employees={filteredEmployees}\n        targetSummary={targetData?.summary || null}\n        periodLabel={periodLabel}\n        onOpenEmployee={openEmployee}\n      />\n\n      <ExecutiveCommandCenterPanel'''

if '<ManagementSummary' not in text:
    if anchor not in text:
        fail('five-KPI / Executive Command Center anchor missing')
    text = text.replace(anchor, replacement, 1)

if text == original:
    fail('dashboard was not changed')
DASHBOARD.write_text(text, encoding='utf-8')

SUMMARY.parent.mkdir(parents=True, exist_ok=True)
SUMMARY.write_text(r'''import { AlertTriangle, CheckCircle2, Clock3, Focus, UserRound } from "lucide-react";

function statusPriority(status) {
  if (status === "At Risk") return 0;
  if (status === "Needs Attention") return 1;
  return 2;
}

function employeeButton(employee, onOpenEmployee, suffix = "") {
  return (
    <button
      key={employee.id}
      type="button"
      onClick={() => onOpenEmployee?.(employee.id)}
      className="flex w-full items-center justify-between gap-2 rounded-xl border border-zinc-200/70 bg-white/70 px-2.5 py-2 text-left transition hover:border-amber-300 hover:bg-amber-50/70 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-400 dark:border-white/8 dark:bg-white/[0.025] dark:hover:border-amber-400/25 dark:hover:bg-amber-400/[0.045]"
    >
      <span className="min-w-0">
        <span className="block truncate text-[11px] font-black text-zinc-900 dark:text-white">{employee.name}</span>
        <span className="block truncate text-[9px] font-bold text-zinc-400">{employee.department || employee.jobTitle || "—"}</span>
      </span>
      <span className="shrink-0 text-[10px] font-black text-zinc-500 dark:text-zinc-300">{suffix}</span>
    </button>
  );
}

function EmptyLine({ children }) {
  return <div className="rounded-xl border border-dashed border-zinc-200 px-3 py-3 text-[10px] font-bold text-zinc-400 dark:border-white/10">{children}</div>;
}

export function ManagementSummary({ employees = [], targetSummary = null, periodLabel = "", onOpenEmployee }) {
  const live = (employees || []).filter((employee) => employee?.accountStatus !== "DISABLED");

  const strong = live
    .filter((employee) => employee.performanceScore != null && ["Excellent", "On Track"].includes(employee.status))
    .sort((a, b) => Number(b.performanceScore || 0) - Number(a.performanceScore || 0));

  const attention = live
    .filter((employee) => ["At Risk", "Needs Attention"].includes(employee.status))
    .sort((a, b) => {
      const statusDelta = statusPriority(a.status) - statusPriority(b.status);
      if (statusDelta) return statusDelta;
      const overdueDelta = Number(b.overdueTasks || 0) - Number(a.overdueTasks || 0);
      if (overdueDelta) return overdueDelta;
      return Number(a.performanceScore ?? 999) - Number(b.performanceScore ?? 999);
    });

  const overdue = live
    .filter((employee) => Number(employee.overdueTasks || 0) > 0)
    .sort((a, b) => Number(b.overdueTasks || 0) - Number(a.overdueTasks || 0));

  const atRiskCount = live.filter((employee) => employee.status === "At Risk").length;
  const needsAttentionCount = live.filter((employee) => employee.status === "Needs Attention").length;
  const noActivityCount = live.filter((employee) => employee.status === "No Activity" || employee.performanceScore == null).length;
  const overdueTotal = live.reduce((sum, employee) => sum + Number(employee.overdueTasks || 0), 0);
  const behindTargets = Number(targetSummary?.behind || 0);

  const focusSignals = [];
  if (atRiskCount > 0) focusSignals.push({ tone: "critical", label: `${atRiskCount} at risk` });
  if (overdueTotal > 0) focusSignals.push({ tone: "critical", label: `${overdueTotal} overdue tasks` });
  if (needsAttentionCount > 0) focusSignals.push({ tone: "warning", label: `${needsAttentionCount} need attention` });
  if (behindTargets > 0) focusSignals.push({ tone: "warning", label: `${behindTargets} behind target` });
  if (noActivityCount > 0) focusSignals.push({ tone: "neutral", label: `${noActivityCount} no activity` });
  if (!focusSignals.length) focusSignals.push({ tone: "positive", label: "No urgent management signal" });

  const toneClass = {
    critical: "border-red-200 bg-red-50/70 text-red-700 dark:border-red-400/20 dark:bg-red-400/[0.07] dark:text-red-300",
    warning: "border-amber-200 bg-amber-50/70 text-amber-700 dark:border-amber-400/20 dark:bg-amber-400/[0.07] dark:text-amber-300",
    neutral: "border-zinc-200 bg-zinc-50 text-zinc-600 dark:border-white/10 dark:bg-white/[0.035] dark:text-zinc-300",
    positive: "border-emerald-200 bg-emerald-50/70 text-emerald-700 dark:border-emerald-400/20 dark:bg-emerald-400/[0.07] dark:text-emerald-300",
  };

  return (
    <section id="phase3-management-summary" className="rounded-[24px] border border-zinc-200/80 bg-white/85 p-4 shadow-sm dark:border-white/10 dark:bg-white/[0.025]">
      <div className="flex flex-col gap-2 border-b border-zinc-100 pb-3 dark:border-white/10 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-[10px] font-black uppercase tracking-[0.12em] text-amber-500">Management Summary</p>
          <h2 className="mt-1 text-base font-black text-zinc-950 dark:text-white">What needs your attention</h2>
          <p className="mt-1 text-[10px] font-bold text-zinc-400">Fast read of the current filtered team. Click an employee to open the existing detailed drawer.</p>
        </div>
        <div className="text-left sm:text-right">
          <p className="text-[9px] font-black uppercase tracking-[0.08em] text-zinc-400">Selected period</p>
          <p className="mt-1 text-[10px] font-black text-zinc-600 dark:text-zinc-300">{periodLabel || "—"}</p>
        </div>
      </div>

      <div className="mt-3 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <article className="rounded-2xl border border-emerald-200/80 bg-emerald-50/45 p-3 dark:border-emerald-400/15 dark:bg-emerald-400/[0.045]">
          <div className="flex items-center justify-between gap-2"><div><p className="text-[9px] font-black uppercase tracking-[0.08em] text-emerald-600 dark:text-emerald-300">Doing well</p><p className="mt-1 text-xl font-black text-zinc-950 dark:text-white">{strong.length}</p></div><CheckCircle2 size={17} className="text-emerald-500" /></div>
          <div className="mt-2 space-y-1.5">{strong.slice(0, 3).map((employee) => employeeButton(employee, onOpenEmployee, employee.performanceScore ?? "—"))}{!strong.length ? <EmptyLine>No Excellent / On Track employee in this scope.</EmptyLine> : null}</div>
        </article>

        <article className="rounded-2xl border border-orange-200/80 bg-orange-50/45 p-3 dark:border-orange-400/15 dark:bg-orange-400/[0.045]">
          <div className="flex items-center justify-between gap-2"><div><p className="text-[9px] font-black uppercase tracking-[0.08em] text-orange-600 dark:text-orange-300">Needs attention</p><p className="mt-1 text-xl font-black text-zinc-950 dark:text-white">{attention.length}</p></div><UserRound size={17} className="text-orange-500" /></div>
          <div className="mt-2 space-y-1.5">{attention.slice(0, 3).map((employee) => employeeButton(employee, onOpenEmployee, employee.status))}{!attention.length ? <EmptyLine>No employee currently needs intervention.</EmptyLine> : null}</div>
        </article>

        <article className="rounded-2xl border border-red-200/80 bg-red-50/45 p-3 dark:border-red-400/15 dark:bg-red-400/[0.045]">
          <div className="flex items-center justify-between gap-2"><div><p className="text-[9px] font-black uppercase tracking-[0.08em] text-red-600 dark:text-red-300">Overdue pressure</p><p className="mt-1 text-xl font-black text-zinc-950 dark:text-white">{overdueTotal}</p></div><Clock3 size={17} className="text-red-500" /></div>
          <div className="mt-2 space-y-1.5">{overdue.slice(0, 3).map((employee) => employeeButton(employee, onOpenEmployee, `${employee.overdueTasks} overdue`))}{!overdue.length ? <EmptyLine>No overdue work in the selected scope.</EmptyLine> : null}</div>
        </article>

        <article className="rounded-2xl border border-zinc-200 bg-zinc-50/55 p-3 dark:border-white/10 dark:bg-white/[0.035]">
          <div className="flex items-center justify-between gap-2"><div><p className="text-[9px] font-black uppercase tracking-[0.08em] text-zinc-500 dark:text-zinc-300">Focus now</p><p className="mt-1 text-xl font-black text-zinc-950 dark:text-white">{focusSignals.filter((item) => item.tone !== "positive").length || "✓"}</p></div><Focus size={17} className="text-amber-500" /></div>
          <div className="mt-2 space-y-1.5">{focusSignals.slice(0, 3).map((signal) => <div key={signal.label} className={`rounded-xl border px-2.5 py-2 text-[10px] font-black ${toneClass[signal.tone] || toneClass.neutral}`}>{signal.label}</div>)}</div>
        </article>
      </div>

      <div className="mt-3 flex items-start gap-2 rounded-xl border border-zinc-200/70 bg-zinc-50/60 px-3 py-2 dark:border-white/8 dark:bg-white/[0.02]">
        <AlertTriangle size={13} className="mt-0.5 shrink-0 text-zinc-400" />
        <p className="text-[9px] font-bold leading-4 text-zinc-400">Rule-based summary of the existing filtered performance data. It does not create a new score or make an automated HR decision.</p>
      </div>
    </section>
  );
}

export default ManagementSummary;
''', encoding='utf-8')

print('TEAM_PERFORMANCE_PHASE3_MANAGEMENT_SUMMARY_V1_APPLIED=YES')
print('MANAGEMENT_SUMMARY_VISIBLE=YES')
print('DOING_WELL_SECTION=YES')
print('NEEDS_ATTENTION_SECTION=YES')
print('OVERDUE_PRESSURE_SECTION=YES')
print('FOCUS_NOW_SECTION=YES')
print('EMPLOYEE_DRAWER_LINKS_PRESERVED=YES')
print('NEW_SCORE_CREATED=NO')
print('AUTOMATED_HR_DECISION=NO')
