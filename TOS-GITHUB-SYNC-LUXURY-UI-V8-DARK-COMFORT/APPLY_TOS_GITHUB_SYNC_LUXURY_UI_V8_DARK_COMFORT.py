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

# V8 is dark-mode-only and expects the successful V7 layout-tuned state.
required = [
    'xl:grid-cols-[260px_minmax(0,1fr)]',
    'min-h-[154px]',
    'break-all font-mono',
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
        raise SystemExit(f"BLOCKED: expected V7 marker missing: {anchor}")

if '#161F2A' in segment and 'dark:!text-[#F3F5F7]' in segment and 'DARK_COMFORT_V8' in segment:
    print("PATCH_APPLIED=ALREADY")
    print("STRUCTURE_PRESERVED=YES")
    print("LOGIC_PRESERVED=YES")
    raise SystemExit(0)

# Marker is added only as a harmless class token in the premium root.
root_old = 'className="grid min-w-0 gap-6 text-[#2E2417] dark:text-[#F8F2E7] xl:grid-cols-[260px_minmax(0,1fr)] 2xl:grid-cols-[272px_minmax(0,1fr)]"'
root_new = 'className="DARK_COMFORT_V8 grid min-w-0 gap-6 text-[#2E2417] dark:text-[#D7DCE2] xl:grid-cols-[260px_minmax(0,1fr)] 2xl:grid-cols-[272px_minmax(0,1fr)]"'
if root_old not in segment:
    raise SystemExit("BLOCKED: V7 root class not found")
segment = segment.replace(root_old, root_new, 1)

# Dark surfaces only: move away from near-black to comfortable graphite/navy layers.
dark_surface_replacements = [
    (
        'dark:bg-[linear-gradient(180deg,rgba(13,19,29,0.98)_0%,rgba(6,9,14,0.99)_100%)]',
        'dark:bg-[linear-gradient(180deg,rgba(20,27,37,0.98)_0%,rgba(14,20,28,0.99)_100%)]'
    ),
    (
        'dark:bg-[radial-gradient(circle_at_14%_0%,rgba(217,174,91,0.20),transparent_46%),linear-gradient(180deg,rgba(20,27,39,0.88),rgba(11,15,23,0.92))]',
        'dark:bg-[radial-gradient(circle_at_14%_0%,rgba(205,171,96,0.11),transparent_48%),linear-gradient(180deg,rgba(24,32,43,0.94),rgba(16,22,31,0.96))]'
    ),
    (
        'dark:bg-[radial-gradient(circle_at_88%_-18%,rgba(217,174,91,0.24),transparent_34%),radial-gradient(circle_at_8%_130%,rgba(185,133,46,0.10),transparent_36%),linear-gradient(135deg,#05080D_0%,#0A1018_56%,#070B11_100%)]',
        'dark:bg-[radial-gradient(circle_at_88%_-18%,rgba(205,171,96,0.14),transparent_36%),radial-gradient(circle_at_8%_130%,rgba(185,133,46,0.055),transparent_38%),linear-gradient(135deg,#111821_0%,#161F2A_56%,#10161E_100%)]'
    ),
    (
        'dark:bg-[linear-gradient(180deg,#0E151F_0%,#080D14_100%)]',
        'dark:bg-[linear-gradient(180deg,#151D27_0%,#101720_100%)]'
    ),
    (
        'dark:bg-[linear-gradient(180deg,#0C131D_0%,#070C12_100%)]',
        'dark:bg-[linear-gradient(180deg,#141C26_0%,#0F161F_100%)]'
    ),
    ('dark:bg-[#090D14]', 'dark:bg-[#141B24]'),
    ('dark:bg-zinc-800', 'dark:bg-[#232C37]'),
    ('dark:bg-zinc-950', 'dark:bg-[#111821]'),
    ('dark:bg-white/[0.065]', 'dark:bg-white/[0.045]'),
    ('dark:bg-white/[0.06]', 'dark:bg-white/[0.045]'),
    ('dark:bg-white/[0.055]', 'dark:bg-white/[0.04]'),
    ('dark:bg-white/[0.045]', 'dark:bg-white/[0.035]'),
]
for old, new in dark_surface_replacements:
    segment = segment.replace(old, new)

# Dark typography only: neutral warm-white hierarchy, less yellow and less glare.
dark_text_replacements = [
    ('dark:!text-[#FFF4DA]', 'dark:!text-[#F3F5F7]'),
    ('dark:!text-[#FFF5DF]', 'dark:!text-[#F3F5F7]'),
    ('dark:!text-[#FFF6E3]', 'dark:!text-[#F4F6F8]'),
    ('dark:!text-[#F8EEDC]', 'dark:!text-[#E2E6EB]'),
    ('dark:!text-[#EFE5D5]', 'dark:!text-[#D8DDE4]'),
    ('dark:!text-[#D8CEBD]', 'dark:!text-[#B8C0CA]'),
    ('dark:!text-[#CFC3AE]', 'dark:!text-[#9FA9B5]'),
    ('dark:!text-[#F8E8BF]', 'dark:!text-[#E4D3A8]'),
    ('dark:text-[#F8F2E7]', 'dark:text-[#D7DCE2]'),
    ('dark:text-[#F3CC72]', 'dark:text-[#D7B768]'),
    ('dark:text-[#F6D98D]', 'dark:text-[#D8BC78]'),
]
for old, new in dark_text_replacements:
    segment = segment.replace(old, new)

# Calm borders: cards use neutral separators, gold remains only on premium focal accents.
dark_border_replacements = [
    ('dark:border-[#D9AE5B]/12', 'dark:border-white/[0.065]'),
    ('dark:border-[#D9AE5B]/14', 'dark:border-white/[0.07]'),
    ('dark:border-[#D9AE5B]/15', 'dark:border-white/[0.075]'),
    ('dark:border-[#D9AE5B]/16', 'dark:border-white/[0.08]'),
    ('dark:border-[#D9AE5B]/18', 'dark:border-white/[0.085]'),
    ('dark:border-[#D9AE5B]/20', 'dark:border-[#C9A85F]/16'),
    ('dark:border-[#D9AE5B]/22', 'dark:border-[#C9A85F]/18'),
    ('dark:border-[#D9AE5B]/24', 'dark:border-[#C9A85F]/20'),
    ('dark:hover:border-[#E0B75D]/32', 'dark:hover:border-[#C9A85F]/24'),
]
for old, new in dark_border_replacements:
    segment = segment.replace(old, new)

# Reduce heavy dark shadows/glows which make the screen visually tiring.
dark_shadow_replacements = [
    ('dark:shadow-[0_34px_120px_rgba(0,0,0,0.62)]', 'dark:shadow-[0_28px_84px_rgba(0,0,0,0.38)]'),
    ('dark:shadow-[0_30px_95px_rgba(0,0,0,0.58)]', 'dark:shadow-[0_24px_72px_rgba(0,0,0,0.36)]'),
    ('dark:shadow-[0_22px_72px_rgba(0,0,0,0.32)]', 'dark:shadow-[0_18px_52px_rgba(0,0,0,0.24)]'),
    ('dark:shadow-[0_20px_58px_rgba(0,0,0,0.30)]', 'dark:shadow-[0_16px_44px_rgba(0,0,0,0.22)]'),
    ('dark:shadow-[0_16px_34px_rgba(0,0,0,0.24)]', 'dark:shadow-[0_12px_28px_rgba(0,0,0,0.18)]'),
    ('dark:shadow-[0_8px_20px_rgba(0,0,0,0.24)]', 'dark:shadow-[0_6px_16px_rgba(0,0,0,0.16)]'),
]
for old, new in dark_shadow_replacements:
    segment = segment.replace(old, new)

# Tone down active gold/glow in dark mode while leaving light mode untouched.
segment = segment.replace(
    'dark:bg-[linear-gradient(135deg,rgba(185,133,46,0.24),rgba(217,174,91,0.08))] dark:text-[#F4D582]',
    'dark:bg-[linear-gradient(135deg,rgba(185,133,46,0.14),rgba(217,174,91,0.045))] dark:text-[#D8BB73]'
)
segment = segment.replace(
    'dark:bg-[linear-gradient(180deg,rgba(217,174,91,0.10),rgba(217,174,91,0.055))]',
    'dark:bg-[linear-gradient(180deg,rgba(205,171,96,0.07),rgba(205,171,96,0.035))]'
)

# Workflow state fills stay visible but softer on the eyes.
segment = segment.replace('dark:bg-emerald-500/5', 'dark:bg-emerald-500/[0.075]')
segment = segment.replace('dark:bg-blue-500/5', 'dark:bg-blue-500/[0.065]')
segment = segment.replace('dark:bg-amber-500/5', 'dark:bg-amber-500/[0.055]')

# Reassemble and strict safety validation.
text = text[:start] + segment + text[end:]
final_lines = len(text.splitlines())

if abs(final_lines - original_lines) > 2:
    raise SystemExit(f"BLOCKED: unexpected line delta {original_lines} -> {final_lines}")

for token in ["<section", "<article", "<Button", "onClick=", "useState(", "useEffect(", "api.github.", "<details", "<summary"]:
    before = original.count(token)
    after = text.count(token)
    if before != after:
        raise SystemExit(f"BLOCKED: structural/logic token changed: {token}: {before} -> {after}")

# Light mode safety: no light surface tokens may be changed by this patch.
light_sentinels = [
    '#FFFEFB', '#FBF5E8', '#FFFDFC', '#E8D7B1', '#E7D7B6', '#EADFC8'
]
for token in light_sentinels:
    if original.count(token) != text.count(token):
        raise SystemExit(f"BLOCKED: light-mode token changed unexpectedly: {token}")

if text == original:
    raise SystemExit("BLOCKED: no V8 dark comfort changes produced")

TARGET.write_text(text, encoding="utf-8")

print("PATCH_APPLIED=YES")
print("BASE=V7_LAYOUT_TUNING")
print(f"BASELINE_LINES={original_lines}")
print(f"FINAL_LINES={final_lines}")
print("STRUCTURE_PRESERVED=YES")
print("LOGIC_PRESERVED=YES")
print("LIGHT_MODE_UNCHANGED=YES")
print("DARK_BACKGROUND_SOFTENED=YES")
print("DARK_TEXT_NEUTRALIZED=YES")
print("DARK_GOLD_RESTRAINED=YES")
print("DARK_SHADOWS_SOFTENED=YES")
print("DARK_EYE_COMFORT=YES")
