#!/usr/bin/env python3
from pathlib import Path

TARGET = Path("frontend/src/components/GithubAdvancedAdmin.jsx")

if not TARGET.exists():
    raise SystemExit(f"BLOCKED: target not found: {TARGET}")

text = TARGET.read_text(encoding="utf-8")
original = text
original_lines = len(text.splitlines())

start_marker = '  if (!backendVersionMismatch) {\n    return ('
end_marker = '\n  return (\n    <div className="space-y-5">'
start = text.find(start_marker)
end = text.find(end_marker, start + 1)
if start < 0 or end < 0:
    raise SystemExit("BLOCKED: premium GitHub UI branch not found")

segment = text[start:end]

required = [
    'xl:grid-cols-[248px_minmax(0,1fr)]',
    '#F3CC72',
    '#0A1018',
    'dark:!text-[#FFF4DA]',
    'id="github-overview"',
    'id="github-workflow"',
    'id="github-changes"',
    'id="github-connection"',
    'id="github-console"',
]
for anchor in required:
    if anchor not in segment:
        raise SystemExit(f"BLOCKED: expected V6 marker missing: {anchor}")

if 'xl:grid-cols-[260px_minmax(0,1fr)]' in segment and 'min-h-[154px]' in segment and 'break-all font-mono' in segment:
    print("PATCH_APPLIED=ALREADY")
    print("STRUCTURE_PRESERVED=YES")
    print("LOGIC_PRESERVED=YES")
    raise SystemExit(0)


def replace_required(scope, old, new, label):
    if old not in scope:
        raise SystemExit(f"BLOCKED: missing V7 anchor [{label}]: {old[:180]}")
    return scope.replace(old, new)

# 1) Main frame + hero sizing / responsive containment.
segment = replace_required(
    segment,
    'className="grid gap-6 text-[#2E2417] dark:text-[#F8F2E7] xl:grid-cols-[248px_minmax(0,1fr)]"',
    'className="grid min-w-0 gap-6 text-[#2E2417] dark:text-[#F8F2E7] xl:grid-cols-[260px_minmax(0,1fr)] 2xl:grid-cols-[272px_minmax(0,1fr)]"',
    'main-grid',
)
segment = replace_required(
    segment,
    'className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between"',
    'className="flex min-w-0 flex-col gap-5 lg:flex-row lg:items-center lg:justify-between lg:gap-8"',
    'hero-inner',
)
segment = replace_required(
    segment,
    'className="min-w-[272px] rounded-[18px] border border-[#D9AE5B]/36 bg-white/88 px-4 py-3 text-xs font-black text-[#44331D] shadow-[0_12px_34px_rgba(185,133,46,0.14)] backdrop-blur-md dark:border-[#D9AE5B]/24 dark:bg-[linear-gradient(180deg,rgba(217,174,91,0.10),rgba(217,174,91,0.055))] dark:!text-[#F8E8BF]"',
    'className="min-w-0 max-w-full rounded-[18px] border border-[#D9AE5B]/36 bg-white/88 px-4 py-3 text-[11px] font-black leading-4 text-[#44331D] shadow-[0_12px_34px_rgba(185,133,46,0.14)] backdrop-blur-md dark:border-[#D9AE5B]/24 dark:bg-[linear-gradient(180deg,rgba(217,174,91,0.10),rgba(217,174,91,0.055))] dark:!text-[#F8E8BF] sm:min-w-[260px] sm:max-w-[380px] sm:text-xs"',
    'repo-pill',
)

# 2) Top cards: equal heights, safe text widths, readable metadata.
segment = replace_required(
    segment,
    '<section className="grid gap-4 lg:grid-cols-3">',
    '<section className="grid min-w-0 items-stretch gap-4 xl:grid-cols-3">',
    'top-cards-grid',
)
segment = segment.replace(
    'rounded-[30px] border border-[#E8D7B1] bg-[linear-gradient(180deg,rgba(255,255,255,0.99),rgba(255,252,246,0.96))] p-5.5 shadow-[0_20px_62px_rgba(80,55,16,0.095)] ring-1 ring-white/80 transition-all duration-200 hover:-translate-y-0.5 hover:border-[#D9AE5B]/48 hover:shadow-[0_28px_80px_rgba(80,55,16,0.14)] dark:border-[#D9AE5B]/18 dark:bg-[linear-gradient(180deg,#0E151F_0%,#080D14_100%)] dark:shadow-[0_20px_58px_rgba(0,0,0,0.30)] dark:ring-white/[0.045] dark:hover:border-[#E0B75D]/32',
    'min-w-0 overflow-hidden rounded-[30px] border border-[#E8D7B1] bg-[linear-gradient(180deg,rgba(255,255,255,0.99),rgba(255,252,246,0.96))] p-[22px] shadow-[0_20px_62px_rgba(80,55,16,0.095)] ring-1 ring-white/80 transition-all duration-200 hover:-translate-y-0.5 hover:border-[#D9AE5B]/48 hover:shadow-[0_28px_80px_rgba(80,55,16,0.14)] dark:border-[#D9AE5B]/18 dark:bg-[linear-gradient(180deg,#0E151F_0%,#080D14_100%)] dark:shadow-[0_20px_58px_rgba(0,0,0,0.30)] dark:ring-white/[0.045] dark:hover:border-[#E0B75D]/32'
)
segment = segment.replace(
    'className="mt-5 space-y-3 text-xs"',
    'className="mt-4 min-w-0 space-y-3 text-[11px] leading-4 sm:text-xs"'
)
segment = replace_required(
    segment,
    'className="mt-1 truncate font-mono font-black"',
    'className="mt-1 block max-w-full break-all font-mono text-[10px] font-black leading-4 sm:text-[11px]"',
    'commit-hash',
)
segment = replace_required(
    segment,
    'className="mt-1 truncate font-black"',
    'className="mt-1 line-clamp-2 max-w-full break-words text-[11px] font-black leading-4 sm:text-xs"',
    'commit-message',
)
segment = segment.replace(
    'className="flex items-center justify-between gap-3 text-xs"',
    'className="flex min-w-0 flex-col gap-3 text-[11px] leading-4 sm:flex-row sm:items-center sm:justify-between sm:text-xs"'
)
segment = segment.replace(
    'className="mt-3 grid grid-cols-4 gap-2"',
    'className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-4"'
)

# Last Push author/date row only, scoped between Last Push and workflow.
last_push_start = segment.find('>{ui("آخر Push", "Last Push")}</h3>')
workflow_start = segment.find('<section id="github-workflow"')
if last_push_start < 0 or workflow_start < 0 or workflow_start <= last_push_start:
    raise SystemExit("BLOCKED: cannot locate Last Push/workflow scope")
last_push_scope = segment[last_push_start:workflow_start]
last_push_scope = last_push_scope.replace(
    'className="flex justify-between gap-3"',
    'className="flex min-w-0 flex-col gap-1.5 sm:flex-row sm:items-center sm:justify-between sm:gap-3"'
)
segment = segment[:last_push_start] + last_push_scope + segment[workflow_start:]

# 3) Workflow cards: balanced height, vertical alignment, responsive text.
workflow_start = segment.find('<section id="github-workflow"')
workflow_end = segment.find('<section id="github-changes"', workflow_start)
if workflow_start < 0 or workflow_end < 0:
    raise SystemExit("BLOCKED: workflow scope not found")
workflow = segment[workflow_start:workflow_end]
workflow = replace_required(
    workflow,
    'className="mt-4 grid gap-3 lg:grid-cols-4"',
    'className="mt-5 grid min-w-0 items-stretch gap-3 md:grid-cols-2 2xl:grid-cols-4"',
    'workflow-grid',
)
workflow = replace_required(
    workflow,
    'className="rounded-[20px] border border-emerald-100 bg-emerald-50/45 p-4 dark:border-emerald-500/20 dark:bg-emerald-500/5"',
    'className="flex min-h-[154px] min-w-0 flex-col rounded-[24px] border border-emerald-100 bg-emerald-50/45 p-[18px] dark:border-emerald-500/20 dark:bg-emerald-500/5"',
    'workflow-card-1',
)
workflow = workflow.replace(
    'rounded-[22px] border p-4 shadow-[0_14px_34px_rgba(70,48,14,0.07)] backdrop-blur-sm transition-all duration-200 hover:-translate-y-0.5 dark:shadow-[0_16px_34px_rgba(0,0,0,0.24)]',
    'flex min-h-[154px] min-w-0 flex-col rounded-[24px] border p-[18px] shadow-[0_14px_34px_rgba(70,48,14,0.07)] backdrop-blur-sm transition-all duration-200 hover:-translate-y-0.5 dark:shadow-[0_16px_34px_rgba(0,0,0,0.24)]'
)
workflow = workflow.replace(
    'className="flex items-center gap-3"',
    'className="flex min-w-0 items-start gap-3"'
)
workflow = workflow.replace(
    '</span><div><p',
    '</span><div className="min-w-0 flex-1"><p'
)
workflow = workflow.replace(
    'mt-1 text-[9px] font-bold',
    'mt-1 text-[10px] font-bold leading-4'
)
workflow = workflow.replace(
    'className="mt-3 w-full justify-center rounded-xl shadow-[0_8px_20px_rgba(70,48,14,0.08)] dark:shadow-[0_8px_20px_rgba(0,0,0,0.24)]"',
    'className="mt-auto h-11 w-full justify-center rounded-xl text-[11px] shadow-[0_8px_20px_rgba(70,48,14,0.08)] dark:shadow-[0_8px_20px_rgba(0,0,0,0.24)] sm:text-xs"'
)
workflow = workflow.replace(
    'className="mt-3 grid h-10 place-items-center',
    'className="mt-auto grid h-11 place-items-center'
)
segment = segment[:workflow_start] + workflow + segment[workflow_end:]

# 4) Changes/activity rows: avoid clipped activity labels/timestamps.
segment = segment.replace(
    'className="grid gap-2 px-4 py-3 sm:grid-cols-[auto_1fr_auto] sm:items-center"',
    'className="grid min-w-0 gap-2 px-4 py-3 sm:grid-cols-[auto_minmax(0,1fr)_auto] sm:items-center"'
)
segment = segment.replace(
    'className="truncate text-[11px] font-black',
    'className="min-w-0 truncate text-[11px] font-black leading-4'
)
segment = segment.replace(
    'className="text-[10px] font-bold',
    'className="min-w-0 text-[10px] font-bold leading-4 sm:whitespace-nowrap'
)

# 5) Repository information: make all compact info cells safe for long values.
# Apply only to small repository data boxes, not whole sections.
segment = segment.replace(
    'className="grid gap-3 sm:grid-cols-2 xl:grid-cols-6"',
    'className="grid min-w-0 gap-3 sm:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-6"'
)
segment = segment.replace(
    'className="rounded-2xl border border-[#EFE4CE] bg-white p-3 dark:border-[#D9AE5B]/15 dark:bg-[#090D14]"',
    'className="min-w-0 overflow-hidden rounded-2xl border border-[#EFE4CE] bg-white p-3.5 dark:border-[#D9AE5B]/15 dark:bg-[#090D14]"'
)
segment = segment.replace(
    'className="mt-1 truncate font-black" dir="ltr"',
    'className="mt-1 block max-w-full truncate text-[10px] font-black leading-4 sm:text-[11px]" dir="ltr"'
)

# 6) Sidebar labels: keep text inside the narrow sidebar frame.
segment = segment.replace(
    'className="mt-3 space-y-1.5 text-xs font-black"',
    'className="mt-3 space-y-1.5 text-[11px] font-black leading-4"'
)
segment = segment.replace(
    '<Icon size={16} /><span>{label}</span>',
    '<Icon size={16} className="shrink-0" /><span className="min-w-0 truncate">{label}</span>'
)

# Reassemble + strict safety checks.
text = text[:start] + segment + text[end:]
final_lines = len(text.splitlines())

if abs(final_lines - original_lines) > 2:
    raise SystemExit(f"BLOCKED: unexpected line delta {original_lines} -> {final_lines}")

for token in ["<section", "<article", "<Button", "onClick=", "useState(", "useEffect(", "api.github.", "<details", "<summary"]:
    before = original.count(token)
    after = text.count(token)
    if before != after:
        raise SystemExit(f"BLOCKED: structural/logic token changed: {token}: {before} -> {after}")

if text == original:
    raise SystemExit("BLOCKED: no V7 layout changes produced")

TARGET.write_text(text, encoding="utf-8")

print("PATCH_APPLIED=YES")
print("BASE=V6_EXECUTIVE")
print(f"BASELINE_LINES={original_lines}")
print(f"FINAL_LINES={final_lines}")
print("STRUCTURE_PRESERVED=YES")
print("LOGIC_PRESERVED=YES")
print("TEXT_OVERFLOW_FIXED=YES")
print("CARD_SIZING_TUNED=YES")
print("WORKFLOW_ALIGNMENT_TUNED=YES")
print("RESPONSIVE_SPACING_TUNED=YES")
