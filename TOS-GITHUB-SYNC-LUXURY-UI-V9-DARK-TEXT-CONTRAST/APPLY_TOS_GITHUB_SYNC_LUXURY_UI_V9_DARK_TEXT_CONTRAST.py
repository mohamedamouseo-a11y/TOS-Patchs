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
    'DARK_COMFORT_V8',
    '#161F2A',
    'dark:!text-[#F3F5F7]',
    'min-h-[154px]',
    'break-all font-mono',
    'id="github-overview"',
    'id="github-workflow"',
    'id="github-changes"',
    'id="github-connection"',
    'id="github-console"',
]
for anchor in required:
    if anchor not in segment:
        raise SystemExit(f"BLOCKED: expected V8 marker missing: {anchor}")

if 'DARK_TEXT_CONTRAST_V9' in segment:
    print("PATCH_APPLIED=ALREADY")
    print("STRUCTURE_PRESERVED=YES")
    print("LOGIC_PRESERVED=YES")
    raise SystemExit(0)

# Marker only. No structural impact.
segment = segment.replace('DARK_COMFORT_V8 ', 'DARK_COMFORT_V8 DARK_TEXT_CONTRAST_V9 ', 1)

# Dark-mode text hierarchy only. Light-mode classes remain untouched.
replacements = [
    ('dark:text-[#D7DCE2]', 'dark:text-[#E4E8ED]'),
    ('dark:!text-[#E2E6EB]', 'dark:!text-[#E9EDF1]'),
    ('dark:!text-[#D8DDE4]', 'dark:!text-[#E0E5EA]'),
    ('dark:!text-[#B8C0CA]', 'dark:!text-[#C4CCD5]'),
    ('dark:!text-[#9FA9B5]', 'dark:!text-[#ADB7C2]'),
    ('dark:!text-[#E4D3A8]', 'dark:!text-[#DDD3B8]'),
    ('dark:text-zinc-100', 'dark:!text-[#E8ECF1]'),
    ('dark:text-zinc-200', 'dark:!text-[#DDE3E9]'),
    ('dark:text-zinc-300', 'dark:!text-[#C8D0D9]'),
    ('dark:text-zinc-400', 'dark:!text-[#AEB8C3]'),
]
for old, new in replacements:
    segment = segment.replace(old, new)

# Legacy light text tokens that still render too dark in dark mode.
# We ADD dark overrides; the original light-mode token is preserved exactly.
legacy_dark_overrides = [
    ('text-zinc-950', 'text-zinc-950 dark:!text-[#F3F5F7]'),
    ('text-zinc-800', 'text-zinc-800 dark:!text-[#E6EBF0]'),
    ('text-zinc-700', 'text-zinc-700 dark:!text-[#D5DCE3]'),
    ('text-zinc-500', 'text-zinc-500 dark:!text-[#B8C1CB]'),
    ('text-zinc-400', 'text-zinc-400 dark:!text-[#AAB4C0]'),
]
for old, new in legacy_dark_overrides:
    # Avoid duplicating overrides already created by a previous replacement.
    segment = segment.replace(old, new)

# Remove accidental duplicate dark overrides if a legacy token had an existing dark class.
segment = segment.replace('dark:!text-[#AAB4C0] dark:!text-[#AEB8C3]', 'dark:!text-[#AEB8C3]')
segment = segment.replace('dark:!text-[#E6EBF0] dark:!text-[#E8ECF1]', 'dark:!text-[#E8ECF1]')
segment = segment.replace('dark:!text-[#D5DCE3] dark:!text-[#DDE3E9]', 'dark:!text-[#DDE3E9]')

# Specific activity stream labels/meta: force readable but not glaring hierarchy.
segment = segment.replace(
    'className="min-w-0 truncate text-[11px] font-black leading-4',
    'className="min-w-0 truncate text-[11px] font-black leading-4 dark:!text-[#E7EBF0]'
)
segment = segment.replace(
    'className="min-w-0 text-[10px] font-bold leading-4 sm:whitespace-nowrap',
    'className="min-w-0 text-[10px] font-bold leading-4 dark:!text-[#AEB8C3] sm:whitespace-nowrap'
)

# Small labels/subtitles across cards: brighter than V8 but still secondary.
segment = segment.replace(
    'font-bold text-[#82745E]',
    'font-bold text-[#82745E] dark:!text-[#AEB8C3]'
)
segment = segment.replace(
    'font-bold text-[#665A47]',
    'font-bold text-[#665A47] dark:!text-[#B8C1CB]'
)

# Reassemble.
text = text[:start] + segment + text[end:]
final_lines = len(text.splitlines())

# Strict safety: no structure/logic/layout token count may change.
if abs(final_lines - original_lines) > 2:
    raise SystemExit(f"BLOCKED: unexpected line delta {original_lines} -> {final_lines}")

for token in ["<section", "<article", "<Button", "onClick=", "useState(", "useEffect(", "api.github.", "<details", "<summary"]:
    before = original.count(token)
    after = text.count(token)
    if before != after:
        raise SystemExit(f"BLOCKED: structural/logic token changed: {token}: {before} -> {after}")

# Background/layout/light-mode sentinels MUST remain unchanged.
sentinels = [
    '#161F2A', '#151D27', '#101720', '#141B24',
    '#FFFEFB', '#FBF5E8', '#FFFDFC', '#E8D7B1',
    'xl:grid-cols-[260px_minmax(0,1fr)]', 'min-h-[154px]', 'break-all font-mono'
]
for token in sentinels:
    if original.count(token) != text.count(token):
        raise SystemExit(f"BLOCKED: non-text token changed unexpectedly: {token}")

if text == original:
    raise SystemExit("BLOCKED: no V9 dark text contrast changes produced")

TARGET.write_text(text, encoding="utf-8")

print("PATCH_APPLIED=YES")
print("BASE=V8_DARK_COMFORT")
print(f"BASELINE_LINES={original_lines}")
print(f"FINAL_LINES={final_lines}")
print("STRUCTURE_PRESERVED=YES")
print("LOGIC_PRESERVED=YES")
print("LAYOUT_UNCHANGED=YES")
print("BACKGROUND_UNCHANGED=YES")
print("LIGHT_MODE_UNCHANGED=YES")
print("DARK_PRIMARY_TEXT_FIXED=YES")
print("DARK_SECONDARY_TEXT_FIXED=YES")
print("DARK_ACTIVITY_TEXT_FIXED=YES")
print("DARK_METADATA_TEXT_FIXED=YES")
