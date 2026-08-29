#!/usr/bin/env python3
from pathlib import Path
import subprocess

BASELINE = "66f7dd32794e9c5bb42dd63222b9a0bc5d4a7ee9"
TARGET = Path("frontend/src/components/GithubAdvancedAdmin.jsx")

if not TARGET.exists():
    raise SystemExit(f"BLOCKED: target not found: {TARGET}")

head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
if head != BASELINE:
    raise SystemExit(f"BLOCKED: expected baseline {BASELINE}, got {head}")

text = TARGET.read_text(encoding="utf-8")
original = text
original_lines = len(text.splitlines())

# Exact styling-only replacements. No JSX structure, handlers, state, effects or API calls are changed.
replacements = [
    (
        'className="grid gap-5 xl:grid-cols-[220px_minmax(0,1fr)]"',
        'className="grid gap-6 xl:grid-cols-[236px_minmax(0,1fr)]"'
    ),
    (
        'className="hidden self-start rounded-[28px] border border-zinc-200/70 bg-white p-3 shadow-[0_18px_45px_rgba(15,23,42,0.05)] dark:border-white/10 dark:bg-zinc-950 xl:sticky xl:top-4 xl:block"',
        'className="hidden self-start rounded-[30px] border border-[#D9AE5B]/25 bg-[linear-gradient(180deg,#fffdf8_0%,#f8f3e8_100%)] p-3 shadow-[0_22px_70px_rgba(99,70,20,0.10)] ring-1 ring-white/70 backdrop-blur-xl dark:border-[#D9AE5B]/20 dark:bg-[linear-gradient(180deg,#0B1018_0%,#070A0F_100%)] dark:shadow-[0_28px_90px_rgba(0,0,0,0.42)] dark:ring-white/[0.04] xl:sticky xl:top-4 xl:block"'
    ),
    (
        'className="rounded-[22px] border border-zinc-100 bg-zinc-50/80 p-4 dark:border-white/10 dark:bg-white/[0.035]"',
        'className="rounded-[24px] border border-[#D9AE5B]/20 bg-[radial-gradient(circle_at_15%_0%,rgba(217,174,91,0.16),transparent_38%),rgba(255,255,255,0.72)] p-4 shadow-inner dark:border-[#D9AE5B]/15 dark:bg-[radial-gradient(circle_at_15%_0%,rgba(217,174,91,0.14),transparent_42%),rgba(255,255,255,0.035)]"'
    ),
    (
        'className="grid h-11 w-11 place-items-center rounded-2xl bg-zinc-950 text-white shadow-lg dark:bg-white dark:text-zinc-950"',
        'className="grid h-11 w-11 place-items-center rounded-2xl border border-[#D9AE5B]/35 bg-[linear-gradient(145deg,#2A2113_0%,#0D121B_100%)] text-[#F6D98D] shadow-[0_10px_28px_rgba(185,133,46,0.24)] dark:bg-[linear-gradient(145deg,#2A2113_0%,#090D14_100%)] dark:text-[#F6D98D]"'
    ),
    (
        'className={premiumClass("flex items-center gap-3 rounded-2xl px-3 py-3 transition hover:bg-zinc-50 dark:hover:bg-white/5", index === 0 ? "bg-amber-50 text-amber-700 ring-1 ring-amber-100 dark:bg-amber-500/10 dark:text-amber-300 dark:ring-amber-500/20" : "text-zinc-500 dark:text-zinc-300")}',
        'className={premiumClass("flex items-center gap-3 rounded-2xl px-3 py-3 transition-all duration-200 hover:-translate-y-0.5 hover:border-[#D9AE5B]/25 hover:bg-[#FBF6EA] hover:shadow-[0_8px_24px_rgba(185,133,46,0.10)] dark:hover:bg-[#D9AE5B]/[0.07]", index === 0 ? "border border-[#D9AE5B]/30 bg-[linear-gradient(135deg,#FFF8E8_0%,#F7E8BF_100%)] text-[#8A5B12] shadow-[0_10px_28px_rgba(185,133,46,0.12)] dark:bg-[linear-gradient(135deg,rgba(185,133,46,0.20),rgba(217,174,91,0.07))] dark:text-[#F1CA72]" : "border border-transparent text-zinc-500 dark:text-zinc-300")}'
    ),
    (
        'className="mt-4 rounded-[20px] border border-zinc-100 p-4 dark:border-white/10"',
        'className="mt-4 rounded-[22px] border border-[#D9AE5B]/15 bg-white/55 p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.75)] dark:border-[#D9AE5B]/10 dark:bg-white/[0.025]"'
    ),
    (
        'className="min-w-0 space-y-5"',
        'className="min-w-0 space-y-6"'
    ),
    (
        'className="overflow-hidden rounded-[30px] border border-zinc-200/70 bg-[radial-gradient(circle_at_82%_0%,rgba(245,158,11,0.13),transparent_30%),linear-gradient(135deg,#ffffff_0%,#fffdf8_100%)] p-5 shadow-[0_18px_50px_rgba(15,23,42,0.055)] dark:border-white/10 dark:bg-[radial-gradient(circle_at_82%_0%,rgba(245,158,11,0.12),transparent_28%),linear-gradient(135deg,#09090b_0%,#111827_100%)] sm:p-6"',
        'className="relative overflow-hidden rounded-[32px] border border-[#D9AE5B]/30 bg-[radial-gradient(circle_at_84%_-10%,rgba(217,174,91,0.28),transparent_34%),linear-gradient(135deg,#FFFDF8_0%,#F8F0DE_55%,#FFFDFC_100%)] p-6 shadow-[0_24px_80px_rgba(99,70,20,0.12)] ring-1 ring-white/80 dark:border-[#D9AE5B]/20 dark:bg-[radial-gradient(circle_at_84%_-10%,rgba(217,174,91,0.20),transparent_34%),linear-gradient(135deg,#070A0F_0%,#0D121B_56%,#080B11_100%)] dark:shadow-[0_30px_100px_rgba(0,0,0,0.48)] dark:ring-white/[0.04] sm:p-7"'
    ),
    (
        'className="mt-2 text-2xl font-black tracking-[-0.03em] text-zinc-950 dark:text-white sm:text-3xl"',
        'className="mt-2 text-2xl font-black tracking-[-0.045em] text-[#18130B] drop-shadow-sm dark:text-[#FFF7E6] sm:text-[32px]"'
    ),
    (
        'className="min-w-[250px] rounded-2xl border border-zinc-200 bg-white px-4 py-3 text-xs font-black text-zinc-700 shadow-sm dark:border-white/10 dark:bg-white/5 dark:text-zinc-100"',
        'className="min-w-[260px] rounded-2xl border border-[#D9AE5B]/30 bg-white/80 px-4 py-3 text-xs font-black text-[#4B3820] shadow-[0_10px_30px_rgba(185,133,46,0.10)] backdrop-blur dark:border-[#D9AE5B]/20 dark:bg-[#D9AE5B]/[0.055] dark:text-[#F8E7BE]"'
    ),
    (
        'className="rounded-[26px] border border-zinc-200/70 bg-white p-5 shadow-[0_16px_40px_rgba(15,23,42,0.045)] dark:border-white/10 dark:bg-zinc-950"',
        'className="rounded-[28px] border border-[#D9AE5B]/18 bg-[linear-gradient(180deg,rgba(255,255,255,0.96),rgba(255,252,246,0.92))] p-5 shadow-[0_18px_55px_rgba(99,70,20,0.08)] ring-1 ring-white/70 transition-all duration-200 hover:-translate-y-0.5 hover:border-[#D9AE5B]/32 hover:shadow-[0_24px_70px_rgba(99,70,20,0.12)] dark:border-[#D9AE5B]/12 dark:bg-[linear-gradient(180deg,#0D121B_0%,#090D14_100%)] dark:ring-white/[0.035] dark:hover:border-[#D9AE5B]/25"'
    ),
    (
        'className="mt-4 rounded-[18px] border border-zinc-100 bg-zinc-50/70 p-4 dark:border-white/10 dark:bg-white/[0.035]"',
        'className="mt-4 rounded-[20px] border border-[#D9AE5B]/12 bg-[#FBF7EE]/85 p-4 shadow-inner dark:border-[#D9AE5B]/10 dark:bg-white/[0.028]"'
    ),
    (
        'className="rounded-[28px] border border-zinc-200/70 bg-white p-5 shadow-[0_16px_45px_rgba(15,23,42,0.05)] dark:border-white/10 dark:bg-zinc-950"',
        'className="rounded-[30px] border border-[#D9AE5B]/20 bg-[linear-gradient(180deg,#FFFDF9_0%,#FAF5EA_100%)] p-5 shadow-[0_22px_70px_rgba(99,70,20,0.09)] ring-1 ring-white/70 dark:border-[#D9AE5B]/14 dark:bg-[linear-gradient(180deg,#0C1119_0%,#080B11_100%)] dark:ring-white/[0.035]"'
    ),
    (
        'className="rounded-[20px] border border-zinc-200 bg-zinc-50 p-4 dark:border-white/10 dark:bg-white/[0.035]"',
        'className="rounded-[22px] border border-[#D9AE5B]/14 bg-[#FAF6ED] p-4 shadow-inner dark:border-[#D9AE5B]/10 dark:bg-white/[0.028]"'
    ),
    (
        'className="h-full rounded-full bg-amber-500 transition-all"',
        'className="h-full rounded-full bg-[linear-gradient(90deg,#B9852E_0%,#D9AE5B_55%,#F4D98F_100%)] shadow-[0_0_18px_rgba(217,174,91,0.32)] transition-all"'
    ),
    (
        'className="mt-4 max-h-48 overflow-auto rounded-2xl bg-zinc-950 p-4 font-mono text-[10px] text-zinc-200"',
        'className="mt-4 max-h-48 overflow-auto rounded-2xl border border-[#D9AE5B]/15 bg-[#05070B] p-4 font-mono text-[10px] text-zinc-200 shadow-inner"'
    ),
]

applied = []
for old, new in replacements:
    count = text.count(old)
    if count == 0:
        raise SystemExit(f"BLOCKED: expected styling anchor not found:\n{old[:180]}")
    text = text.replace(old, new)
    applied.append((old[:80], count))

if text == original:
    raise SystemExit("BLOCKED: no styling changes produced")

# Hard safety guards: styling-only patch must not alter structural/logic tokens.
final_lines = len(text.splitlines())
if abs(final_lines - original_lines) > 2:
    raise SystemExit(f"BLOCKED: line delta too large: {original_lines} -> {final_lines}")

for token in ["<section", "<article", "<Button", "onClick=", "useState(", "useEffect(", "api.github."]:
    before = original.count(token)
    after = text.count(token)
    if before != after:
        raise SystemExit(f"BLOCKED: structural/logic token changed: {token}: {before} -> {after}")

TARGET.write_text(text, encoding="utf-8")

print("PATCH_APPLIED=YES")
print(f"BASELINE_LINES={original_lines}")
print(f"FINAL_LINES={final_lines}")
print(f"REPLACEMENT_GROUPS={len(replacements)}")
print("STRUCTURE_PRESERVED=YES")
print("LOGIC_PRESERVED=YES")
