#!/usr/bin/env python3
from pathlib import Path

TARGET = Path("frontend/src/components/GithubAdvancedAdmin.jsx")

if not TARGET.exists():
    raise SystemExit(f"BLOCKED: target not found: {TARGET}")

text = TARGET.read_text(encoding="utf-8")
original = text
original_lines = len(text.splitlines())

# V5 must be applied on top of the successfully-applied V4 styling state.
v4_markers = [
    'className="grid gap-6 xl:grid-cols-[236px_minmax(0,1fr)]"',
    'dark:bg-[linear-gradient(180deg,#0B1018_0%,#070A0F_100%)]',
    'dark:bg-[radial-gradient(circle_at_84%_-10%,rgba(217,174,91,0.20),transparent_34%),linear-gradient(135deg,#070A0F_0%,#0D121B_56%,#080B11_100%)]',
    'bg-[linear-gradient(90deg,#B9852E_0%,#D9AE5B_55%,#F4D98F_100%)]',
]
for marker in v4_markers:
    if marker not in text:
        raise SystemExit(f"BLOCKED: V4 marker missing: {marker[:140]}")

# Styling-only exact replacements. No JSX structure, handlers, state, effects or API calls.
replacements = [
    (
        'className="grid gap-6 xl:grid-cols-[236px_minmax(0,1fr)]"',
        'className="grid gap-6 text-[#2B2113] dark:!text-[#F4E8D0] xl:grid-cols-[236px_minmax(0,1fr)]"'
    ),
    (
        'className="hidden self-start rounded-[30px] border border-[#D9AE5B]/25 bg-[linear-gradient(180deg,#fffdf8_0%,#f8f3e8_100%)] p-3 shadow-[0_22px_70px_rgba(99,70,20,0.10)] ring-1 ring-white/70 backdrop-blur-xl dark:border-[#D9AE5B]/20 dark:bg-[linear-gradient(180deg,#0B1018_0%,#070A0F_100%)] dark:shadow-[0_28px_90px_rgba(0,0,0,0.42)] dark:ring-white/[0.04] xl:sticky xl:top-4 xl:block"',
        'className="hidden self-start rounded-[30px] border border-[#D9AE5B]/30 bg-[linear-gradient(180deg,#FFFDF8_0%,#F6EFDFFF_100%)] p-3 shadow-[0_24px_80px_rgba(99,70,20,0.12)] ring-1 ring-white/80 backdrop-blur-xl dark:border-[#D9AE5B]/24 dark:bg-[linear-gradient(180deg,#0D141E_0%,#080D14_100%)] dark:shadow-[0_30px_100px_rgba(0,0,0,0.52)] dark:ring-[#D9AE5B]/[0.05] xl:sticky xl:top-4 xl:block"'
    ),
    (
        'className={premiumClass("flex items-center gap-3 rounded-2xl px-3 py-3 transition-all duration-200 hover:-translate-y-0.5 hover:border-[#D9AE5B]/25 hover:bg-[#FBF6EA] hover:shadow-[0_8px_24px_rgba(185,133,46,0.10)] dark:hover:bg-[#D9AE5B]/[0.07]", index === 0 ? "border border-[#D9AE5B]/30 bg-[linear-gradient(135deg,#FFF8E8_0%,#F7E8BF_100%)] text-[#8A5B12] shadow-[0_10px_28px_rgba(185,133,46,0.12)] dark:bg-[linear-gradient(135deg,rgba(185,133,46,0.20),rgba(217,174,91,0.07))] dark:text-[#F1CA72]" : "border border-transparent text-zinc-500 dark:text-zinc-300")}',
        'className={premiumClass("flex items-center gap-3 rounded-2xl border px-3 py-3 transition-all duration-200 hover:-translate-y-0.5 hover:border-[#D9AE5B]/35 hover:shadow-[0_10px_30px_rgba(185,133,46,0.12)] dark:hover:bg-[#D9AE5B]/[0.10]", index === 0 ? "border-[#D9AE5B]/40 bg-[linear-gradient(135deg,#FFF5D8_0%,#F4DEAA_100%)] text-[#744A0B] shadow-[0_12px_32px_rgba(185,133,46,0.16)] dark:bg-[linear-gradient(135deg,rgba(185,133,46,0.27),rgba(217,174,91,0.09))] dark:!text-[#FFE2A0]" : "border-[#E9DFC9]/70 bg-white/70 text-[#665A46] dark:border-white/[0.07] dark:bg-[#0F1620]/90 dark:!text-[#DCE3EA]")}'
    ),
    (
        'className="min-w-0 space-y-6"',
        'className="min-w-0 space-y-6 text-[#2B2113] dark:!text-[#F4E8D0]"'
    ),
    (
        'className="relative overflow-hidden rounded-[32px] border border-[#D9AE5B]/30 bg-[radial-gradient(circle_at_84%_-10%,rgba(217,174,91,0.28),transparent_34%),linear-gradient(135deg,#FFFDF8_0%,#F8F0DE_55%,#FFFDFC_100%)] p-6 shadow-[0_24px_80px_rgba(99,70,20,0.12)] ring-1 ring-white/80 dark:border-[#D9AE5B]/20 dark:bg-[radial-gradient(circle_at_84%_-10%,rgba(217,174,91,0.20),transparent_34%),linear-gradient(135deg,#070A0F_0%,#0D121B_56%,#080B11_100%)] dark:shadow-[0_30px_100px_rgba(0,0,0,0.48)] dark:ring-white/[0.04] sm:p-7"',
        'className="relative overflow-hidden rounded-[32px] border border-[#D9AE5B]/34 bg-[radial-gradient(circle_at_84%_-10%,rgba(217,174,91,0.30),transparent_34%),linear-gradient(135deg,#FFFDF8_0%,#F7ECCE_55%,#FFFDFC_100%)] p-6 shadow-[0_28px_90px_rgba(99,70,20,0.14)] ring-1 ring-white/90 before:absolute before:inset-x-8 before:bottom-0 before:h-px before:bg-[linear-gradient(90deg,transparent,rgba(185,133,46,0.65),transparent)] dark:border-[#D9AE5B]/26 dark:bg-[radial-gradient(circle_at_84%_-10%,rgba(217,174,91,0.24),transparent_34%),linear-gradient(135deg,#0A0F17_0%,#111A27_56%,#090E15_100%)] dark:shadow-[0_34px_110px_rgba(0,0,0,0.58)] dark:ring-[#D9AE5B]/[0.06] sm:p-7"'
    ),
    (
        'className="flex items-center gap-2 text-[10px] font-black text-amber-600 dark:text-amber-300"',
        'className="flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.15em] text-[#9A6510] dark:!text-[#E7B958]"'
    ),
    (
        'className="mt-2 text-2xl font-black tracking-[-0.045em] text-[#18130B] drop-shadow-sm dark:text-[#FFF7E6] sm:text-[32px]"',
        'className="mt-2 text-[28px] font-black tracking-[-0.05em] text-[#171108] drop-shadow-sm dark:!text-[#FFF1CE] sm:text-[34px]"'
    ),
    (
        'className="rounded-[28px] border border-[#D9AE5B]/18 bg-[linear-gradient(180deg,rgba(255,255,255,0.96),rgba(255,252,246,0.92))] p-5 shadow-[0_18px_55px_rgba(99,70,20,0.08)] ring-1 ring-white/70 transition-all duration-200 hover:-translate-y-0.5 hover:border-[#D9AE5B]/32 hover:shadow-[0_24px_70px_rgba(99,70,20,0.12)] dark:border-[#D9AE5B]/12 dark:bg-[linear-gradient(180deg,#0D121B_0%,#090D14_100%)] dark:ring-white/[0.035] dark:hover:border-[#D9AE5B]/25"',
        'className="rounded-[28px] border border-[#D9AE5B]/22 bg-[linear-gradient(180deg,rgba(255,255,255,0.98),rgba(255,250,240,0.94))] p-5 text-[#2A2013] shadow-[0_20px_60px_rgba(99,70,20,0.10)] ring-1 ring-white/80 transition-all duration-200 hover:-translate-y-0.5 hover:border-[#D9AE5B]/38 hover:shadow-[0_26px_76px_rgba(99,70,20,0.14)] dark:border-[#D9AE5B]/18 dark:bg-[linear-gradient(180deg,#111925_0%,#0B1119_100%)] dark:!text-[#F4E8D0] dark:ring-white/[0.045] dark:hover:border-[#D9AE5B]/32"'
    ),
    (
        'className="rounded-[30px] border border-[#D9AE5B]/20 bg-[linear-gradient(180deg,#FFFDF9_0%,#FAF5EA_100%)] p-5 shadow-[0_22px_70px_rgba(99,70,20,0.09)] ring-1 ring-white/70 dark:border-[#D9AE5B]/14 dark:bg-[linear-gradient(180deg,#0C1119_0%,#080B11_100%)] dark:ring-white/[0.035]"',
        'className="rounded-[30px] border border-[#D9AE5B]/22 bg-[linear-gradient(180deg,#FFFDF9_0%,#F8F0E1_100%)] p-5 text-[#2A2013] shadow-[0_24px_76px_rgba(99,70,20,0.10)] ring-1 ring-white/80 dark:border-[#D9AE5B]/18 dark:bg-[linear-gradient(180deg,#101823_0%,#0A1018_100%)] dark:!text-[#F4E8D0] dark:ring-white/[0.045]"'
    ),
    (
        'className="mt-4 rounded-[20px] border border-zinc-200 bg-zinc-50 p-4 dark:border-white/10 dark:bg-white/[0.035]"',
        'className="mt-4 rounded-[20px] border border-[#D9AE5B]/14 bg-[#FBF5E8] p-4 dark:border-[#D9AE5B]/12 dark:bg-[#121A25] dark:!text-[#F0E4CF]"'
    ),
    (
        'className="rounded-2xl border border-zinc-100 bg-white p-2.5 text-center dark:border-white/10 dark:bg-zinc-950"',
        'className="rounded-2xl border border-[#D9AE5B]/12 bg-white/85 p-2.5 text-center shadow-sm dark:border-[#D9AE5B]/10 dark:bg-[#0D141D] dark:!text-[#F2E7D3]"'
    ),
    (
        'className="rounded-[20px] border border-emerald-100 bg-emerald-50/45 p-4 dark:border-emerald-500/20 dark:bg-emerald-500/5"',
        'className="rounded-[22px] border border-emerald-200/80 bg-[linear-gradient(180deg,#F1FFF8_0%,#E7F8EF_100%)] p-4 shadow-[0_12px_34px_rgba(16,185,129,0.08)] dark:border-emerald-400/25 dark:bg-[linear-gradient(180deg,rgba(16,185,129,0.12),rgba(16,185,129,0.045))]"'
    ),
    (
        'premiumReviewReady ? "border-blue-200 bg-blue-50/50 dark:border-blue-500/20 dark:bg-blue-500/5" : "border-zinc-200 bg-zinc-50/50 dark:border-white/10 dark:bg-white/[0.025]"',
        'premiumReviewReady ? "border-sky-200 bg-sky-50/70 shadow-[0_12px_34px_rgba(14,165,233,0.07)] dark:border-sky-400/25 dark:bg-sky-400/[0.09]" : "border-[#E9DFC9] bg-[#FBF8F1] dark:border-white/[0.08] dark:bg-[#111925]"'
    ),
    (
        'premiumReviewReady ? "border-amber-200 bg-amber-50/60 dark:border-amber-500/20 dark:bg-amber-500/5" : "border-zinc-200 bg-zinc-50/50 dark:border-white/10 dark:bg-white/[0.025]"',
        'premiumReviewReady ? "border-[#D9AE5B]/45 bg-[linear-gradient(180deg,#FFF7DF_0%,#F8EAC4_100%)] shadow-[0_12px_34px_rgba(185,133,46,0.10)] dark:border-[#D9AE5B]/35 dark:bg-[#D9AE5B]/[0.10]" : "border-[#E9DFC9] bg-[#FBF8F1] dark:border-white/[0.08] dark:bg-[#111925]"'
    ),
    (
        'premiumPushCompleted ? "border-emerald-200 bg-emerald-50/50 dark:border-emerald-500/20 dark:bg-emerald-500/5" : "border-zinc-200 bg-zinc-50/50 dark:border-white/10 dark:bg-white/[0.025]"',
        'premiumPushCompleted ? "border-emerald-200 bg-emerald-50/70 dark:border-emerald-400/25 dark:bg-emerald-400/[0.09]" : "border-[#E9DFC9] bg-[#FBF8F1] dark:border-white/[0.08] dark:bg-[#111925]"'
    ),
    (
        'className="mt-3 grid h-10 place-items-center rounded-xl border border-zinc-100 bg-white text-xs font-black text-zinc-400 dark:border-white/10 dark:bg-zinc-950"',
        'className="mt-3 grid h-10 place-items-center rounded-xl border border-[#E9DFC9] bg-white/90 text-xs font-black text-[#8A7654] dark:border-white/[0.08] dark:bg-[#0D141D] dark:!text-[#AEB8C5]"'
    ),
    (
        'className="grid h-full w-full place-items-center rounded-full bg-white text-center shadow-inner dark:bg-zinc-950"',
        'className="grid h-full w-full place-items-center rounded-full bg-[#FFFDF8] text-center shadow-[inset_0_0_0_1px_rgba(185,133,46,0.10),inset_0_8px_24px_rgba(99,70,20,0.06)] dark:bg-[#0B121A] dark:!text-[#FFF0CE]"'
    ),
]

for old, new in replacements:
    count = text.count(old)
    if count == 0:
        raise SystemExit(f"BLOCKED: expected V4 styling anchor not found:\n{old[:220]}")
    text = text.replace(old, new)

# Contrast pass restricted to this component only. These are class-token substitutions, not structure/logic changes.
contrast_replacements = [
    ("text-zinc-400", "text-[#827158] dark:!text-[#ADB8C5]"),
    ("text-zinc-500", "text-[#6F6250] dark:!text-[#C0CAD5]"),
    ("dark:text-zinc-300", "dark:!text-[#DCE3EA]"),
    ("dark:text-zinc-200", "dark:!text-[#EEE7DB]"),
    ("dark:text-zinc-100", "dark:!text-[#FFF3DA]"),
]
for old, new in contrast_replacements:
    text = text.replace(old, new)

if text == original:
    raise SystemExit("BLOCKED: no V5 styling changes produced")

final_lines = len(text.splitlines())
if abs(final_lines - original_lines) > 2:
    raise SystemExit(f"BLOCKED: line delta too large: {original_lines} -> {final_lines}")

# Hard safety guards: all functional/structural token counts must remain identical.
for token in ["<section", "<article", "<details", "<summary", "<Button", "onClick=", "useState(", "useEffect(", "api.github.", "startOperation(", "downloadSource", "disconnect"]:
    before = original.count(token)
    after = text.count(token)
    if before != after:
        raise SystemExit(f"BLOCKED: structural/logic token changed: {token}: {before} -> {after}")

TARGET.write_text(text, encoding="utf-8")

print("PATCH_APPLIED=YES")
print(f"BASELINE_LINES={original_lines}")
print(f"FINAL_LINES={final_lines}")
print(f"EXACT_REPLACEMENT_GROUPS={len(replacements)}")
print(f"CONTRAST_TOKEN_GROUPS={len(contrast_replacements)}")
print("STRUCTURE_PRESERVED=YES")
print("LOGIC_PRESERVED=YES")
print("V5_FOCUS=contrast,hero,sidebar,card-depth,workflow,gold-system")
