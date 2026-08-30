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

if 'xl:grid-cols-[236px_minmax(0,1fr)]' in segment and 'dark:text-[#FFF8E8]' in segment:
    print("PATCH_APPLIED=ALREADY")
    print("STRUCTURE_PRESERVED=YES")
    print("LOGIC_PRESERVED=YES")
    raise SystemExit(0)

# This standalone patch intentionally targets the current stable/baseline premium JSX.
required = [
    'className="grid gap-5 xl:grid-cols-[220px_minmax(0,1fr)]"',
    'className="hidden self-start rounded-[28px] border border-zinc-200/70 bg-white p-3',
    'id="github-overview"',
    'id="github-workflow"',
    'id="github-changes"',
    'id="github-connection"',
    'id="github-console"',
]
for anchor in required:
    if anchor not in segment:
        raise SystemExit(f"BLOCKED: required stable anchor missing: {anchor}")

# Exact premium layout + hero + sidebar replacements.
exact = [
    (
        'className="grid gap-5 xl:grid-cols-[220px_minmax(0,1fr)]"',
        'className="grid gap-6 text-[#352812] dark:text-[#F7F1E3] xl:grid-cols-[236px_minmax(0,1fr)]"'
    ),
    (
        'className="hidden self-start rounded-[28px] border border-zinc-200/70 bg-white p-3 shadow-[0_18px_45px_rgba(15,23,42,0.05)] dark:border-white/10 dark:bg-zinc-950 xl:sticky xl:top-4 xl:block"',
        'className="hidden self-start rounded-[30px] border border-[#D9AE5B]/28 bg-[linear-gradient(180deg,#FFFDF8_0%,#F7F0E2_100%)] p-3 shadow-[0_24px_72px_rgba(99,70,20,0.12)] ring-1 ring-white/70 dark:border-[#D9AE5B]/22 dark:bg-[linear-gradient(180deg,#0D121B_0%,#070A0F_100%)] dark:shadow-[0_28px_90px_rgba(0,0,0,0.46)] dark:ring-white/[0.04] xl:sticky xl:top-4 xl:block"'
    ),
    (
        'className="rounded-[22px] border border-zinc-100 bg-zinc-50/80 p-4 dark:border-white/10 dark:bg-white/[0.035]"',
        'className="rounded-[24px] border border-[#D9AE5B]/24 bg-[radial-gradient(circle_at_18%_0%,rgba(217,174,91,0.18),transparent_42%),rgba(255,255,255,0.72)] p-4 shadow-inner dark:border-[#D9AE5B]/18 dark:bg-[radial-gradient(circle_at_18%_0%,rgba(217,174,91,0.16),transparent_44%),rgba(255,255,255,0.05)]"'
    ),
    (
        'className="grid h-11 w-11 place-items-center rounded-2xl bg-zinc-950 text-white shadow-lg dark:bg-white dark:text-zinc-950"',
        'className="grid h-11 w-11 place-items-center rounded-2xl border border-[#D9AE5B]/40 bg-[linear-gradient(145deg,#2A2113_0%,#0D121B_100%)] text-[#F6D98D] shadow-[0_10px_30px_rgba(185,133,46,0.28)] dark:text-[#F6D98D]"'
    ),
    (
        'className={premiumClass("flex items-center gap-3 rounded-2xl px-3 py-3 transition hover:bg-zinc-50 dark:hover:bg-white/5", index === 0 ? "bg-amber-50 text-amber-700 ring-1 ring-amber-100 dark:bg-amber-500/10 dark:text-amber-300 dark:ring-amber-500/20" : "text-zinc-500 dark:text-zinc-300")}',
        'className={premiumClass("flex items-center gap-3 rounded-2xl border px-3 py-3 transition-all duration-200 hover:-translate-y-0.5", index === 0 ? "border-[#D9AE5B]/34 bg-[linear-gradient(135deg,#FFF8E8_0%,#F5E4B8_100%)] text-[#855714] shadow-[0_10px_28px_rgba(185,133,46,0.15)] dark:bg-[linear-gradient(135deg,rgba(185,133,46,0.24),rgba(217,174,91,0.08))] dark:text-[#F4D582]" : "border-transparent text-[#746651] hover:border-[#D9AE5B]/24 hover:bg-[#FBF6EA] dark:text-[#D9D0BF] dark:hover:border-[#D9AE5B]/18 dark:hover:bg-[#D9AE5B]/[0.075]")} '
    ),
    (
        'className="min-w-0 space-y-5"',
        'className="min-w-0 space-y-6"'
    ),
    (
        'className="overflow-hidden rounded-[30px] border border-zinc-200/70 bg-[radial-gradient(circle_at_82%_0%,rgba(245,158,11,0.13),transparent_30%),linear-gradient(135deg,#ffffff_0%,#fffdf8_100%)] p-5 shadow-[0_18px_50px_rgba(15,23,42,0.055)] dark:border-white/10 dark:bg-[radial-gradient(circle_at_82%_0%,rgba(245,158,11,0.12),transparent_28%),linear-gradient(135deg,#09090b_0%,#111827_100%)] sm:p-6"',
        'className="relative overflow-hidden rounded-[32px] border border-[#D9AE5B]/32 bg-[radial-gradient(circle_at_84%_-12%,rgba(217,174,91,0.30),transparent_34%),linear-gradient(135deg,#FFFDF8_0%,#F7EEDB_58%,#FFFDFC_100%)] p-6 shadow-[0_26px_84px_rgba(99,70,20,0.14)] ring-1 ring-white/80 dark:border-[#D9AE5B]/22 dark:bg-[radial-gradient(circle_at_84%_-12%,rgba(217,174,91,0.22),transparent_34%),linear-gradient(135deg,#070A0F_0%,#0D121B_56%,#080B11_100%)] dark:shadow-[0_32px_110px_rgba(0,0,0,0.52)] dark:ring-white/[0.045] sm:p-7"'
    ),
    (
        'className="mt-2 text-2xl font-black tracking-[-0.03em] text-zinc-950 dark:text-white sm:text-3xl"',
        'className="mt-2 text-2xl font-black tracking-[-0.045em] text-[#18130B] drop-shadow-sm dark:text-[#FFF8E8] sm:text-[32px]"'
    ),
    (
        'className="mt-2 text-xs font-bold text-zinc-500 dark:text-zinc-400"',
        'className="mt-2 max-w-2xl text-xs font-bold leading-5 text-[#71644F] dark:text-[#C8BEAE]"'
    ),
    (
        'className="min-w-[250px] rounded-2xl border border-zinc-200 bg-white px-4 py-3 text-xs font-black text-zinc-700 shadow-sm dark:border-white/10 dark:bg-white/5 dark:text-zinc-100"',
        'className="min-w-[260px] rounded-2xl border border-[#D9AE5B]/32 bg-white/82 px-4 py-3 text-xs font-black text-[#4B3820] shadow-[0_10px_30px_rgba(185,133,46,0.12)] backdrop-blur dark:border-[#D9AE5B]/22 dark:bg-[#D9AE5B]/[0.07] dark:text-[#F8E7BE]"'
    ),
]

for old, new in exact:
    if old not in segment:
        raise SystemExit(f"BLOCKED: exact styling anchor missing: {old[:140]}")
    segment = segment.replace(old, new)

# Repeated card surfaces: safe styling-only substitutions inside the premium branch.
repeated = [
    (
        'rounded-[26px] border border-zinc-200/70 bg-white p-5 shadow-[0_16px_40px_rgba(15,23,42,0.045)] dark:border-white/10 dark:bg-zinc-950',
        'rounded-[28px] border border-[#E5D4AE] bg-[linear-gradient(180deg,rgba(255,255,255,0.98),rgba(255,251,243,0.94))] p-5 shadow-[0_18px_56px_rgba(99,70,20,0.09)] ring-1 ring-white/70 transition-all duration-200 hover:-translate-y-0.5 hover:border-[#D9AE5B]/45 hover:shadow-[0_24px_74px_rgba(99,70,20,0.13)] dark:border-[#D9AE5B]/16 dark:bg-[linear-gradient(180deg,#0D121B_0%,#090D14_100%)] dark:ring-white/[0.035] dark:hover:border-[#D9AE5B]/30'
    ),
    (
        'rounded-[28px] border border-zinc-200/70 bg-white p-5 shadow-[0_16px_45px_rgba(15,23,42,0.05)] dark:border-white/10 dark:bg-zinc-950',
        'rounded-[30px] border border-[#E5D4AE] bg-[linear-gradient(180deg,#FFFDF9_0%,#FAF4E8_100%)] p-5 shadow-[0_22px_72px_rgba(99,70,20,0.10)] ring-1 ring-white/70 dark:border-[#D9AE5B]/16 dark:bg-[linear-gradient(180deg,#0C1119_0%,#080B11_100%)] dark:ring-white/[0.035]'
    ),
    (
        'rounded-[18px] border border-zinc-100 bg-zinc-50/70 p-4 dark:border-white/10 dark:bg-white/[0.035]',
        'rounded-[20px] border border-[#E9DDBF] bg-[#FBF7EE]/90 p-4 shadow-inner dark:border-[#D9AE5B]/12 dark:bg-white/[0.05]'
    ),
    (
        'rounded-2xl border border-zinc-100 bg-white p-2.5 text-center dark:border-white/10 dark:bg-zinc-950',
        'rounded-2xl border border-[#E9DDBF] bg-white/86 p-2.5 text-center shadow-sm dark:border-[#D9AE5B]/12 dark:bg-white/[0.045]'
    ),
]
for old, new in repeated:
    if old in segment:
        segment = segment.replace(old, new)

# Contrast system. Dark replacements first so light-token replacements do not damage dark variants.
contrast = [
    ('dark:text-zinc-100', 'dark:text-[#F7F1E3]'),
    ('dark:text-zinc-200', 'dark:text-[#EEE6D8]'),
    ('dark:text-zinc-300', 'dark:text-[#DDD3C2]'),
    ('dark:text-zinc-400', 'dark:text-[#BEB4A3]'),
    ('dark:text-white', 'dark:text-[#FFF8E8]'),
    ('dark:border-white/10', 'dark:border-[#D9AE5B]/15'),
    ('dark:bg-white/[0.025]', 'dark:bg-white/[0.045]'),
    ('dark:bg-white/[0.035]', 'dark:bg-white/[0.055]'),
    ('dark:bg-white/5', 'dark:bg-white/[0.065]'),
    ('dark:bg-zinc-950', 'dark:bg-[#090D14]'),
    ('text-zinc-950', 'text-[#1F180E]'),
    ('text-zinc-700', 'text-[#4F4332]'),
    ('text-zinc-500', 'text-[#706452]'),
    ('text-zinc-400', 'text-[#948671]'),
    ('border-zinc-200', 'border-[#E6D7B8]'),
    ('border-zinc-100', 'border-[#EFE4CE]'),
    ('bg-zinc-50/50', 'bg-[#FBF7EE]/80'),
    ('bg-zinc-50/70', 'bg-[#FBF7EE]/90'),
]
for old, new in contrast:
    segment = segment.replace(old, new)

# Premium progress bar.
segment = segment.replace(
    'className="h-full rounded-full bg-amber-500 transition-all"',
    'className="h-full rounded-full bg-[linear-gradient(90deg,#B9852E_0%,#D9AE5B_55%,#F4D98F_100%)] shadow-[0_0_18px_rgba(217,174,91,0.34)] transition-all"'
)

# Reassemble and validate strict structure/logic preservation.
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
    raise SystemExit("BLOCKED: no changes produced")

TARGET.write_text(text, encoding="utf-8")

print("PATCH_APPLIED=YES")
print(f"BASELINE_LINES={original_lines}")
print(f"FINAL_LINES={final_lines}")
print("STRUCTURE_PRESERVED=YES")
print("LOGIC_PRESERVED=YES")
print("V4_DEPENDENCY=NO")
print("PREMIUM_CONTRAST_SYSTEM=YES")
