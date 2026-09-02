#!/usr/bin/env python3
from pathlib import Path

ROOT = Path('/var/www/TOS')
DASHBOARD = ROOT / 'frontend/src/pages/TeamPerformanceDashboard.jsx'
CONTROL = ROOT / 'frontend/src/components/performance/PerformancePeriodControl.jsx'


def fail(message: str):
    raise SystemExit(f'PHASE2 PATCH ERROR: {message}')


def insert_after(text: str, anchor: str, addition: str, label: str) -> str:
    if addition.strip() in text:
        return text
    if anchor not in text:
        fail(f'missing anchor: {label}')
    return text.replace(anchor, anchor + addition, 1)


text = DASHBOARD.read_text(encoding='utf-8')
original = text

# Preconditions: Phase 1 + premium dark must already be present locally.
for marker in [
    'PerformanceDisclosure',
    'phase1-goals-disclosure',
    'phase1-intelligence-disclosure',
    'phase1-deep-dive-disclosure',
    'phase1-show-all-employees',
    'teamPerformancePremiumDark.css',
]:
    if marker not in text:
        fail(f'expected Phase 1 / premium dark marker missing: {marker}')

# 1) Import the professional period control and comparison delta component.
import_anchor = 'import { PerformanceDisclosure } from "../components/performance/PerformanceDisclosure";\n'
text = insert_after(
    text,
    import_anchor,
    'import { ComparisonDelta, PerformancePeriodControl } from "../components/performance/PerformancePeriodControl";\n',
    'PerformanceDisclosure import',
)

# 2) Add Quarter to presets.
month_row = '  { key: "month", label: "Month" },\n'
if '{ key: "quarter", label: "Quarter" }' not in text:
    if month_row not in text:
        fail('month preset not found')
    text = text.replace(month_row, month_row + '  { key: "quarter", label: "Quarter" },\n', 1)

# 3) Add quarter date range support.
month_range = '''  } else if (preset === "month") {
    start = startOfDay(new Date(now.getFullYear(), now.getMonth(), 1));
    end = endOfDay(now);
  } else if (preset === "year") {'''
quarter_range = '''  } else if (preset === "month") {
    start = startOfDay(new Date(now.getFullYear(), now.getMonth(), 1));
    end = endOfDay(now);
  } else if (preset === "quarter") {
    const quarterStartMonth = Math.floor(now.getMonth() / 3) * 3;
    start = startOfDay(new Date(now.getFullYear(), quarterStartMonth, 1));
    end = endOfDay(now);
  } else if (preset === "year") {'''
if 'quarterStartMonth' not in text:
    if month_range not in text:
        fail('month/year date range anchor not found')
    text = text.replace(month_range, quarter_range, 1)

# 4) Add professional comparison range calculation.
helper_anchor = '''function getTeamDateRange(preset, customStart, customEnd) {
'''
helper_end = '''}\n\nfunction formatHours(value) {'''
if 'function getComparisonRange(' not in text:
    start_pos = text.find(helper_anchor)
    end_pos = text.find(helper_end, start_pos)
    if start_pos < 0 or end_pos < 0:
        fail('getTeamDateRange block boundaries not found')
    insert_pos = end_pos + 2
    helpers = r'''

function shiftCalendarDate(date, { months = 0, years = 0 } = {}) {
  const source = new Date(date);
  const targetYear = source.getFullYear() + years;
  const targetMonth = source.getMonth() + months;
  const targetDay = source.getDate();
  const first = new Date(targetYear, targetMonth, 1);
  const lastDay = new Date(first.getFullYear(), first.getMonth() + 1, 0).getDate();
  return new Date(first.getFullYear(), first.getMonth(), Math.min(targetDay, lastDay), source.getHours(), source.getMinutes(), source.getSeconds(), source.getMilliseconds());
}

function getComparisonRange(mode, selectedRange, customStart, customEnd) {
  if (mode === "off") return null;
  const currentStart = selectedRange?.start ? startOfDay(selectedRange.start) : null;
  const currentEnd = selectedRange?.end ? endOfDay(selectedRange.end) : null;
  if (!currentStart || !currentEnd || selectedRange?.invalid) return null;

  let start = null;
  let end = null;

  if (mode === "previous_period") {
    const dayMs = 86400000;
    const days = Math.max(1, Math.round((startOfDay(currentEnd) - currentStart) / dayMs) + 1);
    end = endOfDay(new Date(currentStart.getFullYear(), currentStart.getMonth(), currentStart.getDate() - 1));
    start = startOfDay(new Date(end.getFullYear(), end.getMonth(), end.getDate() - days + 1));
  } else if (mode === "previous_month") {
    start = startOfDay(shiftCalendarDate(currentStart, { months: -1 }));
    end = endOfDay(shiftCalendarDate(currentEnd, { months: -1 }));
  } else if (mode === "previous_year") {
    start = startOfDay(shiftCalendarDate(currentStart, { years: -1 }));
    end = endOfDay(shiftCalendarDate(currentEnd, { years: -1 }));
  } else if (mode === "custom") {
    start = parseDateInput(customStart, "start");
    end = parseDateInput(customEnd, "end");
  }

  return {
    start,
    end,
    invalid: Boolean(start && end && start > end),
  };
}
'''
    text = text[:insert_pos] + helpers + text[insert_pos:]

# 5) Extend KPI card with comparison visual.
old_kpi_sig = 'function KpiCard({ icon: Icon, label, value, note = "", tone = "neutral" }) {'
new_kpi_sig = 'function KpiCard({ icon: Icon, label, value, note = "", tone = "neutral", comparison = null }) {'
if new_kpi_sig not in text:
    if old_kpi_sig not in text:
        fail('KpiCard signature not found')
    text = text.replace(old_kpi_sig, new_kpi_sig, 1)

old_note = '      {note ? <p className="mt-1 text-[11px] font-bold text-zinc-400">{note}</p> : null}\n    </div>\n  );\n}\n\nfunction ScorePopover'
new_note = '      {note ? <p className="mt-1 text-[11px] font-bold text-zinc-400">{note}</p> : null}\n      {comparison ? <div className="mt-2"><ComparisonDelta {...comparison} /></div> : null}\n    </div>\n  );\n}\n\nfunction ScorePopover'
if '<ComparisonDelta {...comparison}' not in text:
    if old_note not in text:
        fail('KpiCard note/body anchor not found')
    text = text.replace(old_note, new_note, 1)

# 6) Add comparison state.
custom_state_anchor = '  const [customEnd, setCustomEnd] = useState("");\n'
comparison_states = '''  const [compareMode, setCompareMode] = useState("previous_period");
  const [compareCustomStart, setCompareCustomStart] = useState("");
  const [compareCustomEnd, setCompareCustomEnd] = useState("");
'''
text = insert_after(text, custom_state_anchor, comparison_states, 'custom date state')

team_state_anchor = '  const [teamData, setTeamData] = useState(null);\n'
comparison_data_states = '''  const [comparisonData, setComparisonData] = useState(null);
  const [comparisonLoading, setComparisonLoading] = useState(false);
  const [comparisonError, setComparisonError] = useState("");
'''
text = insert_after(text, team_state_anchor, comparison_data_states, 'team data state')

# 7) Compute comparison range.
selected_anchor = '  const selectedRange = useMemo(() => getTeamDateRange(preset, customStart, customEnd), [preset, customStart, customEnd]);\n'
comparison_range_line = '  const comparisonRange = useMemo(() => getComparisonRange(compareMode, selectedRange, compareCustomStart, compareCustomEnd), [compareMode, selectedRange.start?.getTime?.(), selectedRange.end?.getTime?.(), selectedRange.invalid, compareCustomStart, compareCustomEnd]);\n'
text = insert_after(text, selected_anchor, comparison_range_line, 'selectedRange')

# 8) Fetch comparison using the existing team-performance API; no backend change needed.
main_effect_end = '''  }, [selectedRange.start?.getTime(), selectedRange.end?.getTime(), selectedRange.invalid, refreshNonce, realtimeRefreshVersion]);

  useEffect(() => {
    if (!selectedRange.start || !selectedRange.end || selectedRange.invalid) return;
    let ignore = false;
    async function loadIntelligence() {'''
if 'async function loadComparison()' not in text:
    if main_effect_end not in text:
        fail('main team-performance effect boundary not found')
    comparison_effect = '''  }, [selectedRange.start?.getTime(), selectedRange.end?.getTime(), selectedRange.invalid, refreshNonce, realtimeRefreshVersion]);

  useEffect(() => {
    if (compareMode === "off") {
      setComparisonData(null);
      setComparisonError("");
      setComparisonLoading(false);
      return;
    }
    if (!comparisonRange?.start || !comparisonRange?.end || comparisonRange?.invalid) {
      setComparisonData(null);
      return;
    }
    let ignore = false;
    async function loadComparison() {
      setComparisonLoading(true);
      setComparisonError("");
      try {
        const data = await api.tasks.teamPerformance({
          start: comparisonRange.start.toISOString(),
          end: comparisonRange.end.toISOString(),
        });
        if (!ignore) setComparisonData(data);
      } catch (err) {
        if (!ignore) {
          setComparisonData(null);
          setComparisonError(getErrorMessage(err, "Unable to load comparison period."));
        }
      } finally {
        if (!ignore) setComparisonLoading(false);
      }
    }
    loadComparison();
    return () => { ignore = true; };
  }, [compareMode, comparisonRange?.start?.getTime?.(), comparisonRange?.end?.getTime?.(), comparisonRange?.invalid, refreshNonce, realtimeRefreshVersion]);

  useEffect(() => {
    if (!selectedRange.start || !selectedRange.end || selectedRange.invalid) return;
    let ignore = false;
    async function loadIntelligence() {'''
    text = text.replace(main_effect_end, comparison_effect, 1)

# 9) Build apples-to-apples comparison summary using the current filtered employee cohort.
selected_employee_anchor = '  const selectedEmployee = allEmployees.find((employee) => employee.id === selectedEmployeeId) || null;\n'
if 'const comparisonByEmployee = useMemo(' not in text:
    if selected_employee_anchor not in text:
        fail('selected employee anchor not found')
    comparison_block = '''  const comparisonByEmployee = useMemo(
    () => new Map((comparisonData?.byUser || []).map((employee) => [employee.id, employee])),
    [comparisonData],
  );

  const comparisonFilteredEmployees = useMemo(() => {
    const currentIds = new Set(filteredEmployees.map((employee) => employee.id));
    return (comparisonData?.byUser || []).filter((employee) => currentIds.has(employee.id));
  }, [comparisonData, filteredEmployees]);

  const comparisonSummary = useMemo(() => {
    const scored = comparisonFilteredEmployees.filter((employee) => employee.performanceScore != null);
    const avgScore = scored.length ? Math.round((scored.reduce((sum, employee) => sum + Number(employee.performanceScore || 0), 0) / scored.length) * 10) / 10 : null;
    const completed = comparisonFilteredEmployees.reduce((sum, employee) => sum + Number(employee.completedTasks || 0), 0);
    const total = comparisonFilteredEmployees.reduce((sum, employee) => sum + Number(employee.totalTasks || 0), 0);
    const overdue = comparisonFilteredEmployees.reduce((sum, employee) => sum + Number(employee.overdueTasks || 0), 0);
    const hours = comparisonFilteredEmployees.reduce((sum, employee) => sum + Number(employee.actualHours || 0), 0);
    return { avgScore, completed, total, overdue, hours, completionRate: total ? Math.round((completed / total) * 100) : 0 };
  }, [comparisonFilteredEmployees]);

  const topPerformerComparisonScore = filteredSummary.top ? comparisonByEmployee.get(filteredSummary.top.id)?.performanceScore ?? null : null;

'''
    text = text.replace(selected_employee_anchor, comparison_block + selected_employee_anchor, 1)

# 10) Professional period control replaces the old quick-button-only block, preserving filters below it.
card_anchor = '''      <Card className="p-4">
        <div className="flex flex-col gap-3">
'''
filter_grid = '          <div className="grid gap-2 md:grid-cols-2 xl:grid-cols-[1fr_1fr_1.2fr_auto_auto]">'
if '<PerformancePeriodControl' not in text:
    card_pos = text.find(card_anchor)
    grid_pos = text.find(filter_grid, card_pos)
    if card_pos < 0 or grid_pos < 0:
        fail('period/filter card anchors not found')
    body_start = card_pos + len(card_anchor)
    period_control = '''          <PerformancePeriodControl
            presets={TEAM_PRESETS}
            preset={preset}
            setPreset={setPreset}
            customStart={customStart}
            setCustomStart={setCustomStart}
            customEnd={customEnd}
            setCustomEnd={setCustomEnd}
            selectedRange={selectedRange}
            compareMode={compareMode}
            setCompareMode={setCompareMode}
            compareCustomStart={compareCustomStart}
            setCompareCustomStart={setCompareCustomStart}
            compareCustomEnd={compareCustomEnd}
            setCompareCustomEnd={setCompareCustomEnd}
            comparisonRange={comparisonRange}
            comparisonLoading={comparisonLoading}
          />

'''
    text = text[:body_start] + period_control + text[grid_pos:]

# 11) Comparison validation/error notices.
invalid_notice = '      {selectedRange.invalid ? <Notice type="error">Custom start date must be before the end date.</Notice> : null}\n'
comparison_notices = '''      {comparisonRange?.invalid ? <Notice type="error">Comparison start date must be before the comparison end date.</Notice> : null}
      {comparisonError ? <Notice type="error">{comparisonError}</Notice> : null}
'''
text = insert_after(text, invalid_notice, comparison_notices, 'selected range invalid notice')

# 12) Add comparison deltas to the five core management KPIs.
old_kpis = '''        <KpiCard icon={BarChart3} label="Average score" value={filteredSummary.avgScore ?? "—"} note={`${filteredEmployees.filter((employee) => employee.performanceScore != null).length} scored employees`} tone="gold" />
        <KpiCard icon={UserRound} label="Top performer" value={filteredSummary.top?.name || "—"} note={filteredSummary.top ? `Score ${filteredSummary.top.performanceScore}` : "No scored employees"} tone="green" />
        <KpiCard icon={CheckCircle2} label="Completed tasks" value={`${filteredSummary.completed}/${filteredSummary.total}`} note={`${filteredSummary.completionRate}% completion`} tone="green" />
        <KpiCard icon={AlertCircle} label="Overdue tasks" value={filteredSummary.overdue} note="Within selected team scope" tone="red" />
        <KpiCard icon={Clock3} label="Logged hours" value={formatHours(filteredSummary.hours)} note="Actual task hours" tone="neutral" />'''
new_kpis = '''        <KpiCard icon={BarChart3} label="Average score" value={filteredSummary.avgScore ?? "—"} note={`${filteredEmployees.filter((employee) => employee.performanceScore != null).length} scored employees`} tone="gold" comparison={compareMode !== "off" ? { current: filteredSummary.avgScore, previous: comparisonSummary.avgScore, unit: "pts", label: "vs comparison" } : null} />
        <KpiCard icon={UserRound} label="Top performer" value={filteredSummary.top?.name || "—"} note={filteredSummary.top ? `Score ${filteredSummary.top.performanceScore}` : "No scored employees"} tone="green" comparison={compareMode !== "off" && filteredSummary.top ? { current: filteredSummary.top.performanceScore, previous: topPerformerComparisonScore, unit: "pts", label: "same employee vs comparison" } : null} />
        <KpiCard icon={CheckCircle2} label="Completed tasks" value={`${filteredSummary.completed}/${filteredSummary.total}`} note={`${filteredSummary.completionRate}% completion`} tone="green" comparison={compareMode !== "off" ? { current: filteredSummary.completionRate, previous: comparisonSummary.completionRate, unit: "pp", label: "completion rate" } : null} />
        <KpiCard icon={AlertCircle} label="Overdue tasks" value={filteredSummary.overdue} note="Within selected team scope" tone="red" comparison={compareMode !== "off" ? { current: filteredSummary.overdue, previous: comparisonSummary.overdue, unit: "", label: "vs comparison", inverse: true } : null} />
        <KpiCard icon={Clock3} label="Logged hours" value={formatHours(filteredSummary.hours)} note="Actual task hours" tone="neutral" comparison={compareMode !== "off" ? { current: filteredSummary.hours, previous: comparisonSummary.hours, unit: "h", label: "vs comparison", precision: 1 } : null} />'''
if 'same employee vs comparison' not in text:
    if old_kpis not in text:
        fail('five KPI block not found')
    text = text.replace(old_kpis, new_kpis, 1)

# 13) Team table comparison follows the chosen period instead of an unrelated fixed trend.
old_header = '<th className="px-3 py-3 text-right font-black">Trend</th>'
new_header = '<th className="px-3 py-3 text-right font-black">{compareMode === "off" ? "Trend" : "Compare"}</th>'
if new_header not in text:
    if old_header not in text:
        fail('team table Trend header not found')
    text = text.replace(old_header, new_header, 1)

old_cell = '<td className="px-3 py-3 text-right"><TrendValue trend={employee.trend} /></td>'
new_cell = '<td className="px-3 py-3 text-right">{compareMode === "off" ? <TrendValue trend={employee.trend} /> : <ComparisonDelta current={employee.performanceScore} previous={comparisonByEmployee.get(employee.id)?.performanceScore} unit="pts" compact label="" />}</td>'
if new_cell not in text:
    if old_cell not in text:
        fail('desktop Trend cell not found')
    text = text.replace(old_cell, new_cell, 1)

old_mobile = '<div><p className="text-zinc-400">Trend</p><TrendValue trend={employee.trend} /></div>'
new_mobile = '<div><p className="text-zinc-400">{compareMode === "off" ? "Trend" : "Compare"}</p>{compareMode === "off" ? <TrendValue trend={employee.trend} /> : <ComparisonDelta current={employee.performanceScore} previous={comparisonByEmployee.get(employee.id)?.performanceScore} unit="pts" compact label="" />}</div>'
if new_mobile not in text:
    if old_mobile not in text:
        fail('mobile Trend cell not found')
    text = text.replace(old_mobile, new_mobile, 1)

# 14) Quarter maps correctly in target management metadata.
old_period_type = 'periodType: preset === "week" ? "WEEKLY" : preset === "year" ? "YEARLY" : preset === "custom" ? "CUSTOM" : "MONTHLY"'
new_period_type = 'periodType: preset === "week" ? "WEEKLY" : preset === "quarter" ? "QUARTERLY" : preset === "year" ? "YEARLY" : preset === "custom" ? "CUSTOM" : "MONTHLY"'
if new_period_type not in text:
    if old_period_type not in text:
        fail('target manager periodType mapping not found')
    text = text.replace(old_period_type, new_period_type, 1)

if text == original:
    fail('dashboard was not changed')
DASHBOARD.write_text(text, encoding='utf-8')

# 15) Professional period/filter UI and compact delta visualization.
control_content = r'''import { CalendarDays, ChevronDown, Minus, TrendingDown, TrendingUp } from "lucide-react";

const COMPARE_OPTIONS = [
  { value: "previous_period", label: "Previous period" },
  { value: "previous_month", label: "Previous month" },
  { value: "previous_year", label: "Previous year" },
  { value: "custom", label: "Custom comparison" },
  { value: "off", label: "No comparison" },
];

function inputDate(date) {
  if (!date) return "";
  const value = new Date(date);
  return new Date(value.getTime() - value.getTimezoneOffset() * 60000).toISOString().slice(0, 10);
}

function shortDate(date) {
  if (!date) return "—";
  return new Intl.DateTimeFormat("en-GB", { day: "2-digit", month: "short", year: "numeric" }).format(new Date(date));
}

function rangeLabel(range) {
  if (!range?.start || !range?.end || range?.invalid) return "Choose a valid period";
  return `${shortDate(range.start)} — ${shortDate(range.end)}`;
}

export function ComparisonDelta({ current, previous, unit = "", label = "vs comparison", inverse = false, precision = 1, compact = false }) {
  const currentNumber = Number(current);
  const previousNumber = Number(previous);
  if (!Number.isFinite(currentNumber) || !Number.isFinite(previousNumber)) {
    return <span className={`${compact ? "text-[10px]" : "text-[11px]"} font-black text-zinc-400`}>—</span>;
  }
  const raw = currentNumber - previousNumber;
  const factor = 10 ** Math.max(0, precision);
  const delta = Math.round(raw * factor) / factor;
  const improved = inverse ? delta < 0 : delta > 0;
  const worsened = inverse ? delta > 0 : delta < 0;
  const tone = improved ? "text-emerald-600 dark:text-emerald-400" : worsened ? "text-red-600 dark:text-red-400" : "text-zinc-400";
  const Icon = delta > 0 ? TrendingUp : delta < 0 ? TrendingDown : Minus;
  const suffix = unit ? ` ${unit}` : "";
  return (
    <span className={`inline-flex items-center gap-1 ${compact ? "text-[10px]" : "text-[11px]"} font-black ${tone}`} title={label || undefined}>
      <Icon size={compact ? 11 : 12} />
      {delta > 0 ? "+" : ""}{delta}{suffix}
      {label ? <span className="font-bold text-zinc-400">{label}</span> : null}
    </span>
  );
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
  function setPrimaryStart(value) {
    if (preset !== "custom") {
      setCustomEnd(customEnd || inputDate(selectedRange?.end));
      setPreset("custom");
    }
    setCustomStart(value);
  }

  function setPrimaryEnd(value) {
    if (preset !== "custom") {
      setCustomStart(customStart || inputDate(selectedRange?.start));
      setPreset("custom");
    }
    setCustomEnd(value);
  }

  const currentStart = preset === "custom" ? customStart : inputDate(selectedRange?.start);
  const currentEnd = preset === "custom" ? customEnd : inputDate(selectedRange?.end);

  return (
    <section id="phase2-professional-period-control" className="rounded-2xl border border-zinc-200/80 bg-zinc-50/70 p-3.5 dark:border-white/10 dark:bg-white/[0.025]">
      <div className="flex flex-col gap-3 xl:flex-row xl:items-start xl:justify-between">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <span className="grid h-8 w-8 shrink-0 place-items-center rounded-xl bg-amber-50 text-amber-600 dark:bg-amber-400/10 dark:text-amber-300"><CalendarDays size={15} /></span>
            <div>
              <p className="text-[10px] font-black uppercase tracking-[0.12em] text-amber-500">Reporting period</p>
              <p className="mt-0.5 text-xs font-black text-zinc-800 dark:text-zinc-100">{rangeLabel(selectedRange)}</p>
            </div>
          </div>
          <div className="mt-3 flex flex-wrap gap-1.5">
            {presets.map((item) => (
              <button
                key={item.key}
                type="button"
                onClick={() => setPreset(item.key)}
                className={`rounded-lg border px-2.5 py-1.5 text-[10px] font-black transition ${preset === item.key ? "border-amber-300 bg-amber-50 text-amber-700 dark:border-amber-400/30 dark:bg-amber-400/10 dark:text-amber-200" : "border-zinc-200 bg-white text-zinc-500 hover:border-amber-300 dark:border-white/10 dark:bg-white/[0.025] dark:text-zinc-300"}`}
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>

        <div className="grid min-w-0 flex-1 gap-2 sm:grid-cols-2 xl:max-w-3xl xl:grid-cols-[1fr_1fr_1.15fr]">
          <label className="text-[10px] font-black uppercase tracking-[0.08em] text-zinc-400">
            From
            <input type="date" value={currentStart} onChange={(event) => setPrimaryStart(event.target.value)} className="mt-1.5 min-h-10 w-full rounded-xl border border-zinc-200 bg-white px-3 text-xs font-bold text-zinc-800 outline-none focus:border-amber-400 dark:border-white/10 dark:bg-zinc-900 dark:text-white" />
          </label>
          <label className="text-[10px] font-black uppercase tracking-[0.08em] text-zinc-400">
            To
            <input type="date" value={currentEnd} onChange={(event) => setPrimaryEnd(event.target.value)} className="mt-1.5 min-h-10 w-full rounded-xl border border-zinc-200 bg-white px-3 text-xs font-bold text-zinc-800 outline-none focus:border-amber-400 dark:border-white/10 dark:bg-zinc-900 dark:text-white" />
          </label>
          <label className="text-[10px] font-black uppercase tracking-[0.08em] text-zinc-400">
            Compare with
            <span className="relative mt-1.5 block">
              <select value={compareMode} onChange={(event) => setCompareMode(event.target.value)} className="min-h-10 w-full appearance-none rounded-xl border border-zinc-200 bg-white px-3 pr-9 text-xs font-black text-zinc-800 outline-none focus:border-amber-400 dark:border-white/10 dark:bg-zinc-900 dark:text-white">
                {COMPARE_OPTIONS.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
              </select>
              <ChevronDown size={14} className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-zinc-400" />
            </span>
          </label>
        </div>
      </div>

      {compareMode === "custom" ? (
        <div className="mt-3 grid gap-2 border-t border-zinc-200/70 pt-3 dark:border-white/10 sm:grid-cols-2 xl:max-w-xl">
          <label className="text-[10px] font-black uppercase tracking-[0.08em] text-zinc-400">Comparison from<input type="date" value={compareCustomStart} onChange={(event) => setCompareCustomStart(event.target.value)} className="mt-1.5 min-h-10 w-full rounded-xl border border-zinc-200 bg-white px-3 text-xs font-bold outline-none focus:border-amber-400 dark:border-white/10 dark:bg-zinc-900 dark:text-white" /></label>
          <label className="text-[10px] font-black uppercase tracking-[0.08em] text-zinc-400">Comparison to<input type="date" value={compareCustomEnd} onChange={(event) => setCompareCustomEnd(event.target.value)} className="mt-1.5 min-h-10 w-full rounded-xl border border-zinc-200 bg-white px-3 text-xs font-bold outline-none focus:border-amber-400 dark:border-white/10 dark:bg-zinc-900 dark:text-white" /></label>
        </div>
      ) : null}

      <div className="mt-3 flex flex-wrap items-center gap-2 text-[10px] font-bold text-zinc-400">
        <span className="rounded-full border border-zinc-200 bg-white px-2.5 py-1 dark:border-white/10 dark:bg-white/[0.025]">Current: {rangeLabel(selectedRange)}</span>
        {compareMode !== "off" ? <span className="rounded-full border border-amber-200 bg-amber-50 px-2.5 py-1 text-amber-700 dark:border-amber-400/20 dark:bg-amber-400/[0.07] dark:text-amber-300">Compare: {rangeLabel(comparisonRange)}{comparisonLoading ? " · loading…" : ""}</span> : <span>No comparison selected</span>}
      </div>
    </section>
  );
}

export default PerformancePeriodControl;
'''
CONTROL.parent.mkdir(parents=True, exist_ok=True)
CONTROL.write_text(control_content, encoding='utf-8')

print('TEAM_PERFORMANCE_PHASE2_PROFESSIONAL_DATE_COMPARE_V1_APPLIED=YES')
print('DATE_RANGE_CONTROL=PROFESSIONAL')
print('QUARTER_PRESET=YES')
print('COMPARE_PREVIOUS_PERIOD=YES')
print('COMPARE_PREVIOUS_MONTH=YES')
print('COMPARE_PREVIOUS_YEAR=YES')
print('COMPARE_CUSTOM=YES')
print('COMPARE_OFF=YES')
print('CORE_KPI_COMPARISON=YES')
print('EMPLOYEE_SCORE_COMPARISON=YES')
print('BACKEND_CHANGE_REQUIRED=NO')
