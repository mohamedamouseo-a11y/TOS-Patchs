#!/usr/bin/env python3
from pathlib import Path

ROOT = Path('/var/www/TOS')
TARGET = ROOT / 'frontend/src/components/performance/ExecutiveCommandCenter.jsx'

text = TARGET.read_text(encoding='utf-8')
original = text


def replace_once(old: str, new: str, label: str):
    global text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'ERROR: {label}: expected exactly 1 match, found {count}')
    text = text.replace(old, new, 1)

replace_once(
    '  const [localRefresh, setLocalRefresh] = useState(0);\n',
    '  const [localRefresh, setLocalRefresh] = useState(0);\n  const [detailsOpen, setDetailsOpen] = useState(false);\n',
    'details state',
)

replace_once(
    '  const topPriorities = useMemo(() => (data?.priorities || []).slice(0, 10), [data]);\n',
    '  const topPriorities = useMemo(() => (data?.priorities || []).slice(0, detailsOpen ? 10 : 3), [data, detailsOpen]);\n',
    'priority limit',
)

replace_once(
    '          <button type="button" onClick={() => setLocalRefresh((value) => value + 1)} className="rounded-xl border border-zinc-200 p-2 text-zinc-500 dark:border-white/10" aria-label="Refresh executive command center"><RefreshCw size={16} className={loading ? "animate-spin" : ""} /></button>\n',
    '          <button type="button" onClick={() => setLocalRefresh((value) => value + 1)} className="rounded-xl border border-zinc-200 p-2 text-zinc-500 dark:border-white/10" aria-label="Refresh executive command center"><RefreshCw size={16} className={loading ? "animate-spin" : ""} /></button>\n          <button type="button" onClick={() => setDetailsOpen((value) => !value)} aria-expanded={detailsOpen} className="rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-[10px] font-black text-amber-700 transition hover:bg-amber-100 dark:border-amber-400/20 dark:bg-amber-400/10 dark:text-amber-300 dark:hover:bg-amber-400/15">{detailsOpen ? "Hide executive details" : "View executive details"}</button>\n',
    'details toggle',
)

replace_once(
    '                {(data.brief || []).map((line, index) => (\n',
    '                {(data.brief || []).slice(0, detailsOpen ? 6 : 2).map((line, index) => (\n',
    'brief limit',
)

replace_once(
    '              <div className="mt-3 grid grid-cols-2 gap-2">\n                <div className="rounded-xl bg-zinc-50 p-2.5 dark:bg-white/[0.03]"><p className="text-[10px] font-black text-zinc-400">Pending recognition</p><p className="mt-1 text-lg font-black">{summary.pendingRecognitionDecisions || 0}</p></div>\n                <div className="rounded-xl bg-zinc-50 p-2.5 dark:bg-white/[0.03]"><p className="text-[10px] font-black text-zinc-400">Overdue coaching</p><p className="mt-1 text-lg font-black">{Number(summary.overdueReviewFollowUps || 0) + Number(summary.overdueReviewActions || 0)}</p></div>\n              </div>\n',
    '              {detailsOpen ? (\n                <div className="mt-3 grid grid-cols-2 gap-2">\n                  <div className="rounded-xl bg-zinc-50 p-2.5 dark:bg-white/[0.03]"><p className="text-[10px] font-black text-zinc-400">Pending recognition</p><p className="mt-1 text-lg font-black">{summary.pendingRecognitionDecisions || 0}</p></div>\n                  <div className="rounded-xl bg-zinc-50 p-2.5 dark:bg-white/[0.03]"><p className="text-[10px] font-black text-zinc-400">Overdue coaching</p><p className="mt-1 text-lg font-black">{Number(summary.overdueReviewFollowUps || 0) + Number(summary.overdueReviewActions || 0)}</p></div>\n                </div>\n              ) : null}\n',
    'secondary brief metrics',
)

replace_once(
    '                <Badge>{data.priorities?.length || 0} signals</Badge>\n',
    '                <Badge>{detailsOpen ? `${data.priorities?.length || 0} signals` : `Top ${Math.min(3, data.priorities?.length || 0)} of ${data.priorities?.length || 0}`}</Badge>\n',
    'priority badge',
)

replace_once(
    '                <div className="grid gap-2 md:grid-cols-2">\n                  {topPriorities.map((item) => (\n',
    '                <div className={`grid gap-2 ${detailsOpen ? "md:grid-cols-2" : "md:grid-cols-3"}`}>\n                  {topPriorities.map((item) => (\n',
    'priority grid',
)

replace_once(
    '          <div className="border-t border-zinc-100 p-4 dark:border-white/10">\n            <div className="mb-3"><h3 className="text-sm font-black text-zinc-950 dark:text-white">Decision Domains</h3>',
    '          <div className={`border-t border-zinc-100 p-4 dark:border-white/10 ${detailsOpen ? "" : "hidden"}`}>\n            <div className="mb-3"><h3 className="text-sm font-black text-zinc-950 dark:text-white">Decision Domains</h3>',
    'decision domains visibility',
)

replace_once(
    '          <div className="border-t border-zinc-100 p-4 dark:border-white/10">\n            <div className="mb-3 flex items-center justify-between gap-2"><div><h3 className="text-sm font-black text-zinc-950 dark:text-white">Department Health Signals</h3>',
    '          <div className={`border-t border-zinc-100 p-4 dark:border-white/10 ${detailsOpen ? "" : "hidden"}`}>\n            <div className="mb-3 flex items-center justify-between gap-2"><div><h3 className="text-sm font-black text-zinc-950 dark:text-white">Department Health Signals</h3>',
    'department health visibility',
)

if text == original:
    raise SystemExit('ERROR: no changes produced')

TARGET.write_text(text, encoding='utf-8')
print('PHASE1_EXECUTIVE_SNAPSHOT_REFINEMENT_GENERATOR_APPLIED=YES')
