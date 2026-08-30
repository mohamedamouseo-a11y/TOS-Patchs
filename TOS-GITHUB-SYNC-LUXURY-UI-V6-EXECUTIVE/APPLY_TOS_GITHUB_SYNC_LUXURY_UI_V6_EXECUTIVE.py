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

# V6 is intentionally incremental on the successfully deployed V5 standalone styling.
required = [
    'xl:grid-cols-[236px_minmax(0,1fr)]',
    'dark:text-[#FFF8E8]',
    '#D9AE5B',
    '#0D121B',
    'id="github-overview"',
    'id="github-workflow"',
    'id="github-changes"',
    'id="github-connection"',
    'id="github-console"',
]
for anchor in required:
    if anchor not in segment:
        raise SystemExit(f"BLOCKED: expected V5 marker missing: {anchor}")

if '#F3CC72' in segment and '#0A1018' in segment and 'shadow-[0_30px_95px_rgba(0,0,0,0.58)]' in segment:
    print("PATCH_APPLIED=ALREADY")
    print("STRUCTURE_PRESERVED=YES")
    print("LOGIC_PRESERVED=YES")
    raise SystemExit(0)

# ---- Executive V6: exact high-value surface replacements ----
exact = [
    (
        'className="grid gap-6 text-[#352812] dark:text-[#F7F1E3] xl:grid-cols-[236px_minmax(0,1fr)]"',
        'className="grid gap-6 text-[#2E2417] dark:text-[#F8F2E7] xl:grid-cols-[248px_minmax(0,1fr)]"'
    ),
    (
        'className="hidden self-start rounded-[30px] border border-[#D9AE5B]/28 bg-[linear-gradient(180deg,#FFFDF8_0%,#F7F0E2_100%)] p-3 shadow-[0_24px_72px_rgba(99,70,20,0.12)] ring-1 ring-white/70 dark:border-[#D9AE5B]/22 dark:bg-[linear-gradient(180deg,#0D121B_0%,#070A0F_100%)] dark:shadow-[0_28px_90px_rgba(0,0,0,0.46)] dark:ring-white/[0.04] xl:sticky xl:top-4 xl:block"',
        'className="hidden self-start rounded-[32px] border border-[#D7B56B]/32 bg-[linear-gradient(180deg,rgba(255,254,250,0.98)_0%,rgba(249,244,234,0.96)_100%)] p-3.5 shadow-[0_26px_80px_rgba(88,61,18,0.13)] ring-1 ring-white/80 backdrop-blur-xl dark:border-[#D9AE5B]/24 dark:bg-[linear-gradient(180deg,rgba(13,19,29,0.98)_0%,rgba(6,9,14,0.99)_100%)] dark:shadow-[0_30px_95px_rgba(0,0,0,0.58)] dark:ring-white/[0.045] xl:sticky xl:top-4 xl:block"'
    ),
    (
        'className="rounded-[24px] border border-[#D9AE5B]/24 bg-[radial-gradient(circle_at_18%_0%,rgba(217,174,91,0.18),transparent_42%),rgba(255,255,255,0.72)] p-4 shadow-inner dark:border-[#D9AE5B]/18 dark:bg-[radial-gradient(circle_at_18%_0%,rgba(217,174,91,0.16),transparent_44%),rgba(255,255,255,0.05)]"',
        'className="rounded-[26px] border border-[#D9AE5B]/28 bg-[radial-gradient(circle_at_14%_0%,rgba(236,198,117,0.24),transparent_42%),linear-gradient(180deg,rgba(255,255,255,0.90),rgba(250,246,236,0.82))] p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.92),0_10px_28px_rgba(109,78,25,0.08)] dark:border-[#D9AE5B]/20 dark:bg-[radial-gradient(circle_at_14%_0%,rgba(217,174,91,0.20),transparent_46%),linear-gradient(180deg,rgba(20,27,39,0.88),rgba(11,15,23,0.92))]"'
    ),
    (
        'className="grid h-11 w-11 place-items-center rounded-2xl border border-[#D9AE5B]/40 bg-[linear-gradient(145deg,#2A2113_0%,#0D121B_100%)] text-[#F6D98D] shadow-[0_10px_30px_rgba(185,133,46,0.28)] dark:text-[#F6D98D]"',
        'className="grid h-12 w-12 place-items-center rounded-[18px] border border-[#E2BD68]/45 bg-[radial-gradient(circle_at_30%_20%,rgba(241,205,125,0.28),transparent_38%),linear-gradient(145deg,#2D2212_0%,#0A1018_100%)] text-[#F3CC72] shadow-[0_14px_36px_rgba(185,133,46,0.30),inset_0_1px_0_rgba(255,255,255,0.08)] dark:text-[#F3CC72]"'
    ),
    (
        'className="relative overflow-hidden rounded-[32px] border border-[#D9AE5B]/32 bg-[radial-gradient(circle_at_84%_-12%,rgba(217,174,91,0.30),transparent_34%),linear-gradient(135deg,#FFFDF8_0%,#F7EEDB_58%,#FFFDFC_100%)] p-6 shadow-[0_26px_84px_rgba(99,70,20,0.14)] ring-1 ring-white/80 dark:border-[#D9AE5B]/22 dark:bg-[radial-gradient(circle_at_84%_-12%,rgba(217,174,91,0.22),transparent_34%),linear-gradient(135deg,#070A0F_0%,#0D121B_56%,#080B11_100%)] dark:shadow-[0_32px_110px_rgba(0,0,0,0.52)] dark:ring-white/[0.045] sm:p-7"',
        'className="relative overflow-hidden rounded-[34px] border border-[#D9AE5B]/34 bg-[radial-gradient(circle_at_88%_-18%,rgba(227,187,103,0.38),transparent_34%),radial-gradient(circle_at_8%_130%,rgba(185,133,46,0.10),transparent_34%),linear-gradient(135deg,#FFFEFB_0%,#FBF5E8_58%,#FFFDFC_100%)] p-7 shadow-[0_28px_90px_rgba(92,64,18,0.15)] ring-1 ring-white/90 dark:border-[#D9AE5B]/24 dark:bg-[radial-gradient(circle_at_88%_-18%,rgba(217,174,91,0.24),transparent_34%),radial-gradient(circle_at_8%_130%,rgba(185,133,46,0.10),transparent_36%),linear-gradient(135deg,#05080D_0%,#0A1018_56%,#070B11_100%)] dark:shadow-[0_34px_120px_rgba(0,0,0,0.62)] dark:ring-white/[0.05] sm:p-8"'
    ),
    (
        'className="mt-2 text-2xl font-black tracking-[-0.045em] text-[#18130B] drop-shadow-sm dark:text-[#FFF8E8] sm:text-[32px]"',
        'className="mt-2 text-[28px] font-black tracking-[-0.055em] text-[#181109] drop-shadow-sm dark:!text-[#FFF4DA] sm:text-[36px]"'
    ),
    (
        'className="mt-2 max-w-2xl text-xs font-bold leading-5 text-[#71644F] dark:text-[#C8BEAE]"',
        'className="mt-2 max-w-2xl text-[12px] font-bold leading-5 text-[#6C5B43] dark:!text-[#D9CFBE]"'
    ),
    (
        'className="min-w-[260px] rounded-2xl border border-[#D9AE5B]/32 bg-white/82 px-4 py-3 text-xs font-black text-[#4B3820] shadow-[0_10px_30px_rgba(185,133,46,0.12)] backdrop-blur dark:border-[#D9AE5B]/22 dark:bg-[#D9AE5B]/[0.07] dark:text-[#F8E7BE]"',
        'className="min-w-[272px] rounded-[18px] border border-[#D9AE5B]/36 bg-white/88 px-4 py-3 text-xs font-black text-[#44331D] shadow-[0_12px_34px_rgba(185,133,46,0.14)] backdrop-blur-md dark:border-[#D9AE5B]/24 dark:bg-[linear-gradient(180deg,rgba(217,174,91,0.10),rgba(217,174,91,0.055))] dark:!text-[#F8E8BF]"'
    ),
]

for old, new in exact:
    if old not in segment:
        raise SystemExit(f"BLOCKED: V6 exact styling anchor missing: {old[:150]}")
    segment = segment.replace(old, new)

# ---- Surface refinement: V5 card surfaces -> cleaner executive surfaces ----
repeated = [
    (
        'rounded-[28px] border border-[#E5D4AE] bg-[linear-gradient(180deg,rgba(255,255,255,0.98),rgba(255,251,243,0.94))] p-5 shadow-[0_18px_56px_rgba(99,70,20,0.09)] ring-1 ring-white/70 transition-all duration-200 hover:-translate-y-0.5 hover:border-[#D9AE5B]/45 hover:shadow-[0_24px_74px_rgba(99,70,20,0.13)] dark:border-[#D9AE5B]/16 dark:bg-[linear-gradient(180deg,#0D121B_0%,#090D14_100%)] dark:ring-white/[0.035] dark:hover:border-[#D9AE5B]/30',
        'rounded-[30px] border border-[#E8D7B1] bg-[linear-gradient(180deg,rgba(255,255,255,0.99),rgba(255,252,246,0.96))] p-5.5 shadow-[0_20px_62px_rgba(80,55,16,0.095)] ring-1 ring-white/80 transition-all duration-200 hover:-translate-y-0.5 hover:border-[#D9AE5B]/48 hover:shadow-[0_28px_80px_rgba(80,55,16,0.14)] dark:border-[#D9AE5B]/18 dark:bg-[linear-gradient(180deg,#0E151F_0%,#080D14_100%)] dark:shadow-[0_20px_58px_rgba(0,0,0,0.30)] dark:ring-white/[0.045] dark:hover:border-[#E0B75D]/32'
    ),
    (
        'rounded-[30px] border border-[#E5D4AE] bg-[linear-gradient(180deg,#FFFDF9_0%,#FAF4E8_100%)] p-5 shadow-[0_22px_72px_rgba(99,70,20,0.10)] ring-1 ring-white/70 dark:border-[#D9AE5B]/16 dark:bg-[linear-gradient(180deg,#0C1119_0%,#080B11_100%)] dark:ring-white/[0.035]',
        'rounded-[32px] border border-[#E7D7B6] bg-[linear-gradient(180deg,#FFFEFC_0%,#FBF7EF_100%)] p-5.5 shadow-[0_24px_78px_rgba(80,55,16,0.095)] ring-1 ring-white/85 dark:border-[#D9AE5B]/18 dark:bg-[linear-gradient(180deg,#0C131D_0%,#070C12_100%)] dark:shadow-[0_22px_72px_rgba(0,0,0,0.32)] dark:ring-white/[0.045]'
    ),
    (
        'rounded-[20px] border border-[#E9DDBF] bg-[#FBF7EE]/90 p-4 shadow-inner dark:border-[#D9AE5B]/12 dark:bg-white/[0.05]',
        'rounded-[21px] border border-[#EADFC8] bg-white/72 p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.95)] dark:border-[#D9AE5B]/14 dark:bg-white/[0.06]'
    ),
    (
        'rounded-2xl border border-[#E9DDBF] bg-white/86 p-2.5 text-center shadow-sm dark:border-[#D9AE5B]/12 dark:bg-white/[0.045]',
        'rounded-[18px] border border-[#EADFC8] bg-white/92 p-2.5 text-center shadow-[0_8px_20px_rgba(80,55,16,0.06)] dark:border-[#D9AE5B]/14 dark:bg-white/[0.06]'
    ),
]
for old, new in repeated:
    if old in segment:
        segment = segment.replace(old, new)

# ---- Contrast correction: force readable premium hierarchy in dark and cleaner neutral light ----
contrast = [
    ('text-[#1F180E]', 'text-[#21180D] dark:!text-[#FFF6E3]'),
    ('text-[#4F4332]', 'text-[#4B3E2D] dark:!text-[#EFE5D5]'),
    ('text-[#706452]', 'text-[#665A47] dark:!text-[#D8CEBD]'),
    ('text-[#948671]', 'text-[#82745E] dark:!text-[#CFC3AE]'),
    ('dark:text-[#F7F1E3]', 'dark:!text-[#FFF5DF]'),
    ('dark:text-[#EEE6D8]', 'dark:!text-[#F6EDDF]'),
    ('dark:text-[#DDD3C2]', 'dark:!text-[#E5DAC9]'),
    ('dark:text-[#BEB4A3]', 'dark:!text-[#CFC3B1]'),
]
for old, new in contrast:
    segment = segment.replace(old, new)

# Section titles and primary data: explicit contrast instead of relying on inheritance.
segment = segment.replace(
    'className="text-sm font-black"',
    'className="text-sm font-black tracking-[-0.015em] text-[#261B0D] dark:!text-[#FFF4DA]"'
)
segment = segment.replace(
    'className="text-xs font-black"',
    'className="text-xs font-black text-[#302314] dark:!text-[#F8EEDC]"'
)

# Workflow cards: give them executive depth without changing structure or state-driven colors.
segment = segment.replace(
    'rounded-[20px] border p-4',
    'rounded-[22px] border p-4 shadow-[0_14px_34px_rgba(70,48,14,0.07)] backdrop-blur-sm transition-all duration-200 hover:-translate-y-0.5 dark:shadow-[0_16px_34px_rgba(0,0,0,0.24)]'
)
segment = segment.replace(
    'className="mt-3 w-full justify-center"',
    'className="mt-3 w-full justify-center rounded-xl shadow-[0_8px_20px_rgba(70,48,14,0.08)] dark:shadow-[0_8px_20px_rgba(0,0,0,0.24)]"'
)

# Stronger luxury progress indicator.
segment = segment.replace(
    'bg-[linear-gradient(90deg,#B9852E_0%,#D9AE5B_55%,#F4D98F_100%)] shadow-[0_0_18px_rgba(217,174,91,0.34)]',
    'bg-[linear-gradient(90deg,#9D6D1E_0%,#D9AE5B_48%,#F3CC72_78%,#FFE7A3_100%)] shadow-[0_0_22px_rgba(217,174,91,0.42)]'
)

# Reassemble and strict safety checks.
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
    raise SystemExit("BLOCKED: no V6 styling changes produced")

TARGET.write_text(text, encoding="utf-8")

print("PATCH_APPLIED=YES")
print("BASE=V5_STANDALONE")
print(f"BASELINE_LINES={original_lines}")
print(f"FINAL_LINES={final_lines}")
print("STRUCTURE_PRESERVED=YES")
print("LOGIC_PRESERVED=YES")
print("EXECUTIVE_CONTRAST=YES")
print("HERO_REFINED=YES")
print("SIDEBAR_REFINED=YES")
print("CARD_DEPTH_REFINED=YES")
print("WORKFLOW_REFINED=YES")
