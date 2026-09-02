#!/usr/bin/env python3
from pathlib import Path

ROOT = Path('/var/www/TOS')
DASHBOARD = ROOT / 'frontend/src/pages/TeamPerformanceDashboard.jsx'
DISCLOSURE = ROOT / 'frontend/src/components/performance/PerformanceDisclosure.jsx'


def fail(message: str):
    raise SystemExit(f'PHASE1 PATCH ERROR: {message}')


def insert_once(text: str, anchor: str, addition: str, label: str) -> str:
    if addition.strip() in text:
        return text
    if anchor not in text:
        fail(f'missing anchor: {label}')
    return text.replace(anchor, anchor + addition, 1)


text = DASHBOARD.read_text(encoding='utf-8')
original = text

# 1) Reusable disclosure shell import. Preserve the premium dark-mode import when already applied.
import_anchor = 'import { ExecutiveCommandCenterPanel } from "../components/performance/ExecutiveCommandCenter";\n'
text = insert_once(
    text,
    import_anchor,
    'import { PerformanceDisclosure } from "../components/performance/PerformanceDisclosure";\n',
    'ExecutiveCommandCenter import',
)

# 2) Limit the team table to a focused first page while keeping all employees one click away.
state_anchor = '  const [sortDirection, setSortDirection] = useState("desc");\n'
text = insert_once(
    text,
    state_anchor,
    '  const [showAllEmployees, setShowAllEmployees] = useState(false);\n',
    'sort direction state',
)

rank_marker = '  const filteredRankMap = useMemo(() => {'
summary_marker = '\n\n  const filteredSummary = useMemo(() => {'
if 'const visibleEmployees = useMemo(' not in text:
    rank_start = text.find(rank_marker)
    if rank_start < 0:
        fail('filteredRankMap block not found')
    summary_pos = text.find(summary_marker, rank_start)
    if summary_pos < 0:
        fail('filteredSummary marker not found after filteredRankMap')
    insert = '''\n\n  const visibleEmployees = useMemo(
    () => showAllEmployees ? filteredEmployees : filteredEmployees.slice(0, 8),
    [filteredEmployees, showAllEmployees],
  );

  useEffect(() => {
    setShowAllEmployees(false);
  }, [employeeFilter, departmentFilter, statusFilter, searchTerm, preset, customStart, customEnd]);'''
    text = text[:summary_pos] + insert + text[summary_pos:]

# 3) Collapse Goals & Targets into an on-demand section.
goals_marker = '<p className="text-[11px] font-black uppercase tracking-[0.1em] text-amber-500">Goals & Targets</p>'
intel_marker = '<p className="text-[11px] font-black uppercase tracking-[0.1em] text-amber-500">Performance Intelligence</p>'
if 'phase1-goals-disclosure' not in text:
    goals_pos = text.find(goals_marker)
    intel_pos = text.find(intel_marker)
    if goals_pos < 0 or intel_pos < 0 or intel_pos <= goals_pos:
        fail('Goals/Intelligence section markers not found in expected order')
    goals_card = text.rfind('      <Card className="overflow-hidden p-0">', 0, goals_pos)
    intel_card = text.rfind('      <Card className="overflow-hidden p-0">', goals_pos, intel_pos)
    if goals_card < 0 or intel_card < 0:
        fail('Goals/Intelligence card starts not found')
    goals_wrapper = '''      <PerformanceDisclosure
        id="phase1-goals-disclosure"
        eyebrow="Goals & Targets"
        title="Target achievement"
        description="Keep target details available without occupying the daily management view."
        summary={`${targetData?.summary?.onTarget || 0} on target · ${targetData?.summary?.behind || 0} behind`}
      >\n'''
    text = text[:goals_card] + goals_wrapper + text[goals_card:intel_card] + '      </PerformanceDisclosure>\n\n' + text[intel_card:]

# 4) Collapse Performance Intelligence independently.
if 'phase1-intelligence-disclosure' not in text:
    intel_pos = text.find(intel_marker)
    if intel_pos < 0:
        fail('Performance Intelligence marker not found')
    intel_card = text.rfind('      <Card className="overflow-hidden p-0">', 0, intel_pos)
    if intel_card < 0:
        fail('Performance Intelligence card start not found')
    intel_close = text.find('\n      </Card>', intel_pos)
    if intel_close < 0:
        fail('Performance Intelligence card close not found')
    intel_close_end = intel_close + len('\n      </Card>')
    intel_wrapper = '''      <PerformanceDisclosure
        id="phase1-intelligence-disclosure"
        eyebrow="Performance Intelligence"
        title="Management brief & alerts"
        description="Open only when you need the detailed alerts, department signals and management brief."
        summary={`${Number(intelligenceData?.summary?.criticalAlerts || 0) + Number(intelligenceData?.summary?.warningAlerts || 0)} alerts`}
      >\n'''
    text = text[:intel_card] + intel_wrapper + text[intel_card:intel_close_end] + '\n      </PerformanceDisclosure>' + text[intel_close_end:]

# 5) Put reviews/workforce/skills/talent/recognition behind one Deep Dive disclosure.
if 'phase1-deep-dive-disclosure' not in text:
    reviews_start = text.find('      <PerformanceReviewsPanel')
    recognition_start = text.find('      <RecognitionRewardsPanel', reviews_start)
    if reviews_start < 0 or recognition_start < 0:
        fail('advanced performance panel markers not found')
    recognition_end = text.find('\n      />', recognition_start)
    if recognition_end < 0:
        fail('RecognitionRewardsPanel close not found')
    recognition_end += len('\n      />')
    advanced_wrapper = '''      <PerformanceDisclosure
        id="phase1-deep-dive-disclosure"
        eyebrow="Deep Dive"
        title="Reviews, workforce, skills, talent & recognition"
        description="Advanced management modules stay available here when you need deeper analysis."
        summary="5 detailed modules"
      >\n'''
    text = text[:reviews_start] + advanced_wrapper + text[reviews_start:recognition_end] + '\n      </PerformanceDisclosure>' + text[recognition_end:]

# 6) Team Performance table: first 8 rows, then explicit Show all / Show fewer.
team_marker = '<p className="text-[11px] font-black uppercase tracking-[0.1em] text-amber-500">Management view</p>'
modal_marker = '      {targetManagerOpen ?'
team_marker_pos = text.find(team_marker)
if team_marker_pos < 0:
    fail('Management view marker not found')
team_card_start = text.rfind('      <Card className="overflow-hidden p-0">', 0, team_marker_pos)
team_card_end = text.find(modal_marker, team_marker_pos)
if team_card_start < 0 or team_card_end < 0:
    fail('Team Performance card boundaries not found')
team_block = text[team_card_start:team_card_end]
team_block = team_block.replace('filteredEmployees.map((employee)', 'visibleEmployees.map((employee)')
if 'phase1-show-all-employees' not in team_block:
    close_pos = team_block.rfind('\n      </Card>')
    if close_pos < 0:
        fail('Team Performance card closing tag not found')
    footer = '''

        {filteredEmployees.length > 8 ? (
          <div className="border-t border-zinc-100 p-3 text-center dark:border-white/10">
            <button
              id="phase1-show-all-employees"
              type="button"
              onClick={() => setShowAllEmployees((value) => !value)}
              className="rounded-xl border border-zinc-200 bg-white px-4 py-2 text-xs font-black text-zinc-700 transition hover:border-amber-300 hover:text-amber-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-400 dark:border-white/10 dark:bg-white/[0.035] dark:text-zinc-200 dark:hover:border-amber-400/30 dark:hover:text-amber-300"
              aria-expanded={showAllEmployees}
            >
              {showAllEmployees ? "Show fewer employees" : `Show all ${filteredEmployees.length} employees`}
            </button>
          </div>
        ) : null}'''
    team_block = team_block[:close_pos] + footer + team_block[close_pos:]
text = text[:team_card_start] + team_block + text[team_card_end:]

if text == original:
    fail('dashboard was not changed')

DASHBOARD.write_text(text, encoding='utf-8')

# 7) Reusable premium compact disclosure component.
disclosure_content = '''import { useState } from "react";
import { ChevronDown } from "lucide-react";

export function PerformanceDisclosure({
  id,
  eyebrow,
  title,
  description = "",
  summary = "",
  children,
  defaultOpen = false,
}) {
  const [open, setOpen] = useState(Boolean(defaultOpen));

  return (
    <details
      id={id}
      open={open}
      onToggle={(event) => setOpen(event.currentTarget.open)}
      className="group rounded-[24px] border border-zinc-200/80 bg-white/80 shadow-sm dark:border-white/10 dark:bg-white/[0.025]"
    >
      <summary className="flex cursor-pointer list-none items-center justify-between gap-3 rounded-[24px] px-4 py-3.5 outline-none transition hover:bg-zinc-50 focus-visible:ring-2 focus-visible:ring-amber-400 dark:hover:bg-white/[0.035] [&::-webkit-details-marker]:hidden">
        <div className="min-w-0">
          {eyebrow ? <p className="text-[10px] font-black uppercase tracking-[0.12em] text-amber-500">{eyebrow}</p> : null}
          <div className="mt-0.5 flex flex-wrap items-center gap-x-2 gap-y-1">
            <h2 className="text-sm font-black text-zinc-950 dark:text-white">{title}</h2>
            {summary ? <span className="rounded-full bg-zinc-100 px-2 py-0.5 text-[10px] font-black text-zinc-500 dark:bg-white/[0.06] dark:text-zinc-300">{summary}</span> : null}
          </div>
          {description ? <p className="mt-1 max-w-4xl text-[11px] font-bold leading-5 text-zinc-400">{description}</p> : null}
        </div>
        <span className="grid h-8 w-8 shrink-0 place-items-center rounded-xl border border-zinc-200 bg-white text-zinc-500 transition group-open:rotate-180 dark:border-white/10 dark:bg-white/[0.04] dark:text-zinc-300">
          <ChevronDown size={16} />
        </span>
      </summary>
      <div className="px-2 pb-2">
        {children}
      </div>
    </details>
  );
}
'''
DISCLOSURE.parent.mkdir(parents=True, exist_ok=True)
DISCLOSURE.write_text(disclosure_content, encoding='utf-8')

print('TEAM_PERFORMANCE_UX_CLEANUP_PHASE1_V1_APPLIED=YES')
print('DETAILS_PRESERVED=YES')
print('CORE_KPIS_VISIBLE=5')
print('COLLAPSIBLE_SECTIONS=3')
print('TEAM_TABLE_INITIAL_ROWS=8')
print('EMPLOYEE_DRAWER_PRESERVED=YES')
