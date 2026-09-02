#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path('/var/www/TOS')
BACKEND = ROOT / 'backend/src/routes/tasks.routes.js'
DASHBOARD = ROOT / 'frontend/src/pages/TeamPerformanceDashboard.jsx'
CONTROL = ROOT / 'frontend/src/components/performance/PerformancePeriodControl.jsx'
ARCHIVED = ROOT / 'frontend/src/components/performance/ArchivedPerformanceMembers.jsx'


def fail(message: str):
    raise SystemExit(f'PHASE2 REFINEMENT PATCH ERROR: {message}')


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        fail(f'missing anchor: {label}')
    return text.replace(old, new, 1)


def section(text: str, start_marker: str, end_marker: str, label: str):
    start = text.find(start_marker)
    end = text.find(end_marker, start + len(start_marker))
    if start < 0 or end < 0:
        fail(f'cannot locate section: {label}')
    return start, end


# -----------------------------------------------------------------------------
# 1) BACKEND: Active-only live performance + archived disabled historical rows.
# -----------------------------------------------------------------------------
backend = BACKEND.read_text(encoding='utf-8')
backend_original = backend

route_start, route_end = section(
    backend,
    '// Phase 2+3: Team Performance Aggregation Endpoint',
    '// Phase 3: Performance History Endpoint',
    'team performance aggregation endpoint',
)
route = backend[route_start:route_end]

# Include account state in aggregation without changing the performance-status field.
route = replace_once(
    route,
    'id: true, name: true, email: true, role: true, department: true, jobTitle: true, avatarUrl: true',
    'id: true, name: true, email: true, role: true, status: true, disabledAt: true, department: true, jobTitle: true, avatarUrl: true',
    'team performance user select',
)

# Empty-range contract also exposes an empty archive collection.
route = replace_once(
    route,
    'return res.json({ users: [], summary: {}, byUser: [], filters: { start: null, end: null } });',
    'return res.json({ users: [], summary: {}, byUser: [], archivedByUser: [], filters: { start: null, end: null } });',
    'empty team performance response',
)

# Preserve user account state alongside calculated performance status.
route = replace_once(
    route,
    '      role: user.role,\n      department: user.department,',
    '      role: user.role,\n      accountStatus: user.status,\n      disabledAt: user.disabledAt,\n      department: user.department,',
    'byUser account status fields',
)

# Split live and archived cohorts BEFORE ranking/summary.
sort_marker = '  // Sort by score descending, then by name\n  byUser.sort((a, b) => {'
if 'const activeByUser = byUser.filter' not in route:
    if sort_marker not in route:
        fail('team performance sort marker missing')
    split = '''  // Live management reporting is ACTIVE-only. Disabled employees retain historical\n  // metrics in archivedByUser but never participate in live KPIs, ranking or comparison.\n  const activeByUser = byUser.filter((row) => row.accountStatus === "ACTIVE");\n  const archivedByUser = byUser.filter((row) => row.accountStatus === "DISABLED");\n\n  // Sort active rows by score descending, then by name\n  activeByUser.sort((a, b) => {'''
    route = route.replace(sort_marker, split, 1)

# All live rank/summary math must use activeByUser.
replacements = [
    ('  for (const user of byUser) {', '  for (const user of activeByUser) {', 'active ranking loop'),
    ('  const totalCompleted = byUser.reduce(', '  const totalCompleted = activeByUser.reduce(', 'completed summary'),
    ('  const totalTasks = byUser.reduce(', '  const totalTasks = activeByUser.reduce(', 'task summary'),
    ('  const totalOverdue = byUser.reduce(', '  const totalOverdue = activeByUser.reduce(', 'overdue summary'),
    ('  const totalHours = Math.round(byUser.reduce(', '  const totalHours = Math.round(activeByUser.reduce(', 'hours summary'),
    ('  const scoredUsers = byUser.filter(', '  const scoredUsers = activeByUser.filter(', 'score average'),
    ('  const topPerformer = byUser.find(', '  const topPerformer = activeByUser.find(', 'top performer'),
    ('  const needsAttentionCount = byUser.filter(', '  const needsAttentionCount = activeByUser.filter(', 'attention count'),
    ('      totalEmployees: byUser.length,', '      totalEmployees: activeByUser.length,\n      archivedEmployees: archivedByUser.length,', 'employee counts'),
    ('    byUser,\n    users: users.map(', '    byUser: activeByUser,\n    archivedByUser,\n    users: users.filter((u) => u.status === "ACTIVE").map(', 'active response cohort'),
]
for old, new, label in replacements:
    route = replace_once(route, old, new, label)

# Archived rows are historical only and never have a live rank.
rank_end = '''  for (const user of activeByUser) {\n    if (user.performanceScore !== null) {\n      user.rank = rank++;\n    } else {\n      user.rank = null;\n    }\n  }\n'''
if 'archivedByUser.forEach((user) => { user.rank = null; });' not in route:
    if rank_end not in route:
        fail('active ranking block missing')
    route = route.replace(rank_end, rank_end + '  archivedByUser.forEach((user) => { user.rank = null; });\n', 1)

backend = backend[:route_start] + route + backend[route_end:]

# Advanced live modules must also use ACTIVE users only.
# Export dataset powers Intelligence, Targets summary, Executive Command Center and exports.
export_start, export_end = section(
    backend,
    'async function buildTeamPerformanceExportDataset(req, payload = {}) {',
    'function teamPerformanceExportFilename(',
    'team performance export dataset',
)
export_block = backend[export_start:export_end]
export_block = replace_once(
    export_block,
    '      role: { notIn: ["CLIENT", "FORMER_EMPLOYEE"] },',
    '      status: "ACTIVE",\n      role: { notIn: ["CLIENT", "FORMER_EMPLOYEE"] },',
    'export dataset active users',
)
backend = backend[:export_start] + export_block + backend[export_end:]

# Targets + Reviews share the target access scope. Keep disabled/pending employees out.
target_start, target_end = section(
    backend,
    'async function getTargetAccessScope(req) {',
    'async function assertTargetSubjectExists(',
    'target access scope',
)
target_block = backend[target_start:target_end]
if 'status: "ACTIVE"' not in target_block:
    target_block = target_block.replace(
        'role: { notIn: ["CLIENT", "FORMER_EMPLOYEE"] }',
        'status: "ACTIVE", role: { notIn: ["CLIENT", "FORMER_EMPLOYEE"] }',
    )
backend = backend[:target_start] + target_block + backend[target_end:]

# Workforce scope also powers Skills, Talent and Recognition management views.
workforce_start, workforce_end = section(
    backend,
    'async function getWorkforceScope(req, { employeeId = null, department = null, requireManage = false } = {}) {',
    'async function assertWorkforceCapacityAccess(',
    'workforce access scope',
)
workforce_block = backend[workforce_start:workforce_end]
if 'PHASE2_ACTIVE_WORKFORCE_SCOPE' not in workforce_block:
    allowed_anchor = '  const allowedIds = new Set(users.map((user) => user.id));'
    if allowed_anchor not in workforce_block:
        fail('workforce allowedIds anchor missing')
    active_filter = '''  // PHASE2_ACTIVE_WORKFORCE_SCOPE: disabled/pending users are historical, not live workforce.\n  const activeUsers = users.filter((user) => user.status === "ACTIVE");\n  const allowedIds = new Set(activeUsers.map((user) => user.id));'''
    workforce_block = workforce_block.replace(allowed_anchor, active_filter, 1)
    workforce_block = workforce_block.replace(
        'let visibleUsers = employeeId ? users.filter((user) => user.id === employeeId) : users;',
        'let visibleUsers = employeeId ? activeUsers.filter((user) => user.id === employeeId) : activeUsers;',
        1,
    )
backend = backend[:workforce_start] + workforce_block + backend[workforce_end:]

if backend == backend_original:
    fail('backend was not changed')
BACKEND.write_text(backend, encoding='utf-8')


# -----------------------------------------------------------------------------
# 2) FRONTEND: replace Phase 2 period control with synced preset/manual dates.
# -----------------------------------------------------------------------------
if not CONTROL.exists():
    fail('PerformancePeriodControl.jsx missing; Phase 2 must already be applied')

control_content = r'''import { CalendarDays, Minus, TrendingDown, TrendingUp } from "lucide-react";

const COMPARE_OPTIONS = [
  { value: "previous_period", label: "Previous period" },
  { value: "previous_month", label: "Previous month" },
  { value: "previous_year", label: "Previous year" },
  { value: "custom", label: "Custom comparison" },
  { value: "off", label: "No comparison" },
];

function toInputDate(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  const shifted = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
  return shifted.toISOString().slice(0, 10);
}

function formatDate(value) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat("en-GB", { day: "2-digit", month: "short", year: "numeric" }).format(date);
}

function formatRange(range) {
  if (!range?.start || !range?.end || range?.invalid) return "Choose a valid period";
  return `${formatDate(range.start)} — ${formatDate(range.end)}`;
}

export function ComparisonDelta({ current, previous, unit = "", label = "vs comparison", inverse = false }) {
  if (current == null || previous == null || !Number.isFinite(Number(current)) || !Number.isFinite(Number(previous))) {
    return <span className="text-[10px] font-black text-zinc-500">—</span>;
  }
  const raw = Math.round((Number(current) - Number(previous)) * 10) / 10;
  const good = inverse ? raw < 0 : raw > 0;
  const bad = inverse ? raw > 0 : raw < 0;
  const className = good ? "text-emerald-500" : bad ? "text-red-400" : "text-zinc-400";
  const Icon = raw > 0 ? TrendingUp : raw < 0 ? TrendingDown : Minus;
  const sign = raw > 0 ? "+" : "";
  return <span className={`inline-flex items-center gap-1 text-[10px] font-black ${className}`}><Icon size={11} />{sign}{raw}{unit ? ` ${unit}` : ""} <span className="font-bold text-zinc-500">{label}</span></span>;
}

export function PerformancePeriodControl({
  presets,
  preset,
  setPreset,
  customStart,
  setCustomStart,
  customEnd,
  setCustomEnd,
  selectedRange,
  compareMode,
  setCompareMode,
  compareCustomStart,
  setCompareCustomStart,
  compareCustomEnd,
  setCompareCustomEnd,
  comparisonRange,
  comparisonLoading = false,
}) {
  const currentStartValue = preset === "custom" ? customStart : toInputDate(selectedRange?.start);
  const currentEndValue = preset === "custom" ? customEnd : toInputDate(selectedRange?.end);

  function switchToCustom(nextStart, nextEnd) {
    const fallbackStart = toInputDate(selectedRange?.start);
    const fallbackEnd = toInputDate(selectedRange?.end);
    setCustomStart(nextStart ?? customStart || fallbackStart);
    setCustomEnd(nextEnd ?? customEnd || fallbackEnd);
    setPreset("custom");
  }

  function onCurrentStart(value) {
    switchToCustom(value, preset === "custom" ? customEnd : toInputDate(selectedRange?.end));
  }

  function onCurrentEnd(value) {
    switchToCustom(preset === "custom" ? customStart : toInputDate(selectedRange?.start), value);
  }

  return (
    <section className="rounded-2xl border border-zinc-200/80 bg-zinc-50/70 p-3 dark:border-white/10 dark:bg-white/[0.025]">
      <div className="grid gap-3 xl:grid-cols-[1.2fr_.42fr_.42fr_.5fr] xl:items-end">
        <div>
          <div className="flex items-center gap-2">
            <span className="grid h-8 w-8 place-items-center rounded-xl bg-amber-500/10 text-amber-500"><CalendarDays size={16} /></span>
            <div><p className="text-[10px] font-black uppercase tracking-[0.12em] text-amber-500">Reporting Period</p><p className="text-[11px] font-bold text-zinc-400">Choose a valid period</p></div>
          </div>
          <div className="mt-2 flex flex-wrap gap-1.5">
            {presets.map((item) => {
              const active = preset === item.key;
              return <button key={item.key} type="button" onClick={() => setPreset(item.key)} className={`rounded-xl border px-3 py-2 text-[10px] font-black transition ${active ? "border-amber-400 bg-amber-400 text-zinc-950 shadow-[0_6px_18px_rgba(217,164,65,.18)]" : "border-zinc-200 bg-white text-zinc-500 hover:border-amber-300 dark:border-white/10 dark:bg-white/[0.025] dark:text-zinc-300 dark:hover:border-amber-400/30"}`} aria-pressed={active}>{item.label}</button>;
            })}
          </div>
        </div>

        <label className="block"><span className="mb-1 block text-[9px] font-black uppercase tracking-[0.1em] text-zinc-500">From</span><input type="date" value={currentStartValue} onChange={(e) => onCurrentStart(e.target.value)} className="min-h-10 w-full rounded-xl border border-zinc-200 bg-white px-3 text-xs font-bold text-zinc-800 outline-none focus:border-amber-400 dark:border-white/10 dark:bg-zinc-900 dark:text-white" /></label>
        <label className="block"><span className="mb-1 block text-[9px] font-black uppercase tracking-[0.1em] text-zinc-500">To</span><input type="date" value={currentEndValue} onChange={(e) => onCurrentEnd(e.target.value)} className="min-h-10 w-full rounded-xl border border-zinc-200 bg-white px-3 text-xs font-bold text-zinc-800 outline-none focus:border-amber-400 dark:border-white/10 dark:bg-zinc-900 dark:text-white" /></label>
        <label className="block"><span className="mb-1 block text-[9px] font-black uppercase tracking-[0.1em] text-zinc-500">Compare with</span><select value={compareMode} onChange={(e) => setCompareMode(e.target.value)} className="min-h-10 w-full rounded-xl border border-zinc-200 bg-white px-3 text-xs font-black text-zinc-800 outline-none focus:border-amber-400 dark:border-white/10 dark:bg-zinc-900 dark:text-white">{COMPARE_OPTIONS.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}</select></label>
      </div>

      {compareMode === "custom" ? <div className="mt-3 grid gap-2 border-t border-zinc-200/70 pt-3 sm:grid-cols-2 xl:max-w-xl dark:border-white/10"><label><span className="mb-1 block text-[9px] font-black uppercase tracking-[0.1em] text-zinc-500">Comparison From</span><input type="date" value={compareCustomStart} onChange={(e) => setCompareCustomStart(e.target.value)} className="min-h-10 w-full rounded-xl border border-zinc-200 bg-white px-3 text-xs font-bold dark:border-white/10 dark:bg-zinc-900 dark:text-white" /></label><label><span className="mb-1 block text-[9px] font-black uppercase tracking-[0.1em] text-zinc-500">Comparison To</span><input type="date" value={compareCustomEnd} onChange={(e) => setCompareCustomEnd(e.target.value)} className="min-h-10 w-full rounded-xl border border-zinc-200 bg-white px-3 text-xs font-bold dark:border-white/10 dark:bg-zinc-900 dark:text-white" /></label></div> : null}

      <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 border-t border-zinc-200/60 pt-2 text-[10px] font-bold dark:border-white/10">
        <span className="text-zinc-500">Current: <strong className="text-zinc-700 dark:text-zinc-200">{formatRange(selectedRange)}</strong></span>
        <span className="text-zinc-500">Compare: <strong className="text-zinc-700 dark:text-zinc-200">{compareMode === "off" ? "Off" : formatRange(comparisonRange)}</strong></span>
        {comparisonLoading ? <span className="text-amber-500">Loading comparison…</span> : null}
      </div>
    </section>
  );
}

export default PerformancePeriodControl;
'''
CONTROL.write_text(control_content, encoding='utf-8')


# -----------------------------------------------------------------------------
# 3) FRONTEND: Archived Members parking area + active-only dashboard semantics.
# -----------------------------------------------------------------------------
dashboard = DASHBOARD.read_text(encoding='utf-8')
dashboard_original = dashboard

for marker in ['PerformancePeriodControl', 'phase1-show-all-employees', 'ExecutiveCommandCenterPanel', 'teamPerformancePremiumDark.css']:
    if marker not in dashboard:
        fail(f'expected current frontend marker missing: {marker}')

period_import = 'import { ComparisonDelta, PerformancePeriodControl } from "../components/performance/PerformancePeriodControl";\n'
if 'ArchivedPerformanceMembers' not in dashboard:
    if period_import not in dashboard:
        fail('PerformancePeriodControl import anchor missing')
    dashboard = dashboard.replace(period_import, period_import + 'import { ArchivedPerformanceMembers } from "../components/performance/ArchivedPerformanceMembers";\n', 1)

all_employees = '  const allEmployees = teamData?.byUser || [];\n'
if 'const archivedEmployees = teamData?.archivedByUser || [];' not in dashboard:
    if all_employees not in dashboard:
        fail('allEmployees anchor missing')
    dashboard = dashboard.replace(all_employees, all_employees + '  const archivedEmployees = teamData?.archivedByUser || [];\n', 1)

# Insert the parked archive after the live Team Performance card and before target manager modal.
modal_marker = '      {targetManagerOpen ?'
if '<ArchivedPerformanceMembers' not in dashboard:
    modal_pos = dashboard.find(modal_marker)
    if modal_pos < 0:
        fail('target manager modal marker missing')
    archive_render = '''      <ArchivedPerformanceMembers rows={archivedEmployees} period={selectedRange} />\n\n'''
    dashboard = dashboard[:modal_pos] + archive_render + dashboard[modal_pos:]

if dashboard == dashboard_original:
    fail('dashboard was not changed')
DASHBOARD.write_text(dashboard, encoding='utf-8')

archived_content = r'''import { Archive, ChevronDown } from "lucide-react";

function formatDate(value) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat("en-GB", { day: "2-digit", month: "short", year: "numeric" }).format(date);
}

function formatHours(value) {
  const hours = Number(value || 0);
  if (!Number.isFinite(hours) || hours <= 0) return "0h";
  return `${Math.round(hours * 10) / 10}h`;
}

export function ArchivedPerformanceMembers({ rows = [], period = null }) {
  if (!rows.length) return null;
  return (
    <details className="group rounded-[24px] border border-zinc-200/80 bg-white/70 shadow-sm dark:border-white/10 dark:bg-white/[0.018]">
      <summary className="flex cursor-pointer list-none items-center justify-between gap-3 rounded-[24px] px-4 py-3.5 outline-none hover:bg-zinc-50 focus-visible:ring-2 focus-visible:ring-amber-400 dark:hover:bg-white/[0.03] [&::-webkit-details-marker]:hidden">
        <div className="flex min-w-0 items-center gap-3">
          <span className="grid h-9 w-9 shrink-0 place-items-center rounded-xl border border-zinc-200 bg-zinc-100 text-zinc-500 dark:border-white/10 dark:bg-white/[0.05] dark:text-zinc-400"><Archive size={16} /></span>
          <div className="min-w-0"><p className="text-[10px] font-black uppercase tracking-[0.12em] text-zinc-500">Archived Members</p><div className="mt-0.5 flex flex-wrap items-center gap-2"><h2 className="text-sm font-black text-zinc-900 dark:text-white">Disabled employee history</h2><span className="rounded-full bg-zinc-100 px-2 py-0.5 text-[10px] font-black text-zinc-500 dark:bg-white/[0.06]">{rows.length} archived</span></div><p className="mt-1 text-[11px] font-bold text-zinc-400">Excluded from live KPIs, ranking, comparison and management signals. Historical results remain available here for the selected period.</p></div>
        </div>
        <ChevronDown size={17} className="shrink-0 text-zinc-500 transition group-open:rotate-180" />
      </summary>
      <div className="border-t border-zinc-200/70 p-4 dark:border-white/10">
        <p className="mb-3 text-[10px] font-bold text-zinc-500">Period: {formatDate(period?.start)} — {formatDate(period?.end)}</p>
        <div className="overflow-x-auto rounded-2xl border border-zinc-200/70 dark:border-white/10">
          <table className="w-full min-w-[760px] text-[11px]">
            <thead className="bg-zinc-50 text-zinc-500 dark:bg-white/[0.03]"><tr><th className="px-3 py-2.5 text-left">Employee</th><th className="px-3 py-2.5 text-left">Department</th><th className="px-3 py-2.5 text-right">Score</th><th className="px-3 py-2.5 text-right">Completed</th><th className="px-3 py-2.5 text-right">Hours</th><th className="px-3 py-2.5 text-right">Overdue</th><th className="px-3 py-2.5 text-right">Disabled</th></tr></thead>
            <tbody className="divide-y divide-zinc-100 dark:divide-white/10">{rows.map((row) => <tr key={row.id} className="text-zinc-600 dark:text-zinc-300"><td className="px-3 py-2.5"><p className="font-black text-zinc-900 dark:text-white">{row.name}</p><p className="text-[9px] font-bold text-zinc-500">Archived · no live rank</p></td><td className="px-3 py-2.5">{row.department || "—"}</td><td className="px-3 py-2.5 text-right font-black">{row.performanceScore ?? "—"}</td><td className="px-3 py-2.5 text-right font-black">{row.completedTasks || 0}/{row.totalTasks || 0}</td><td className="px-3 py-2.5 text-right">{formatHours(row.actualHours)}</td><td className="px-3 py-2.5 text-right">{row.overdueTasks || 0}</td><td className="px-3 py-2.5 text-right">{formatDate(row.disabledAt)}</td></tr>)}</tbody>
          </table>
        </div>
      </div>
    </details>
  );
}

export default ArchivedPerformanceMembers;
'''
ARCHIVED.parent.mkdir(parents=True, exist_ok=True)
ARCHIVED.write_text(archived_content, encoding='utf-8')

print('TEAM_PERFORMANCE_PHASE2_REFINEMENT_V1_APPLIED=YES')
print('DATE_PRESET_INPUT_SYNC=YES')
print('CURRENT_PERIOD_LABEL_FIXED=YES')
print('COMPARISON_PERIOD_LABEL_FIXED=YES')
print('ACTIVE_PRESET_VISUAL_STATE=YES')
print('LIVE_PERFORMANCE_ACTIVE_ONLY=YES')
print('DISABLED_MEMBERS_EXCLUDED_FROM_KPIS=YES')
print('DISABLED_MEMBERS_EXCLUDED_FROM_RANKING=YES')
print('DISABLED_MEMBERS_EXCLUDED_FROM_COMPARISON=YES')
print('DISABLED_MEMBERS_EXCLUDED_FROM_ADVANCED_LIVE_MODULES=YES')
print('DISABLED_HISTORY_ARCHIVED=YES')
print('ARCHIVED_MEMBERS_DEFAULT_COLLAPSED=YES')
print('NO_SCHEMA_OR_MIGRATION=YES')
