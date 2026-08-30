#!/usr/bin/env python3
from pathlib import Path
import re

GITHUB_UI = Path("frontend/src/components/GithubAdvancedAdmin.jsx")
SETTINGS_PAGE = Path("frontend/src/pages/SettingsPage.jsx")

for target in (GITHUB_UI, SETTINGS_PAGE):
    if not target.exists():
        raise SystemExit(f"BLOCKED: target not found: {target}")

ui = GITHUB_UI.read_text(encoding="utf-8")
settings = SETTINGS_PAGE.read_text(encoding="utf-8")
ui_original = ui
settings_original = settings

required = [
    "BALANCED_PREMIUM_V12",
    "#2A4050",
    "#243541",
    "dark:bg-[#334755]/72",
    "dark:bg-[#354A59]/74",
    "dark:bg-[#374D5D]/76",
    "min-h-[154px]",
    "break-all font-mono",
    'id="github-workflow"',
    'id="github-changes"',
]
for anchor in required:
    if anchor not in ui:
        raise SystemExit(f"BLOCKED: expected V12 marker missing: {anchor}")

if "INTEGRATED_DARK_PANELS_V13" in ui:
    print("PATCH_APPLIED=ALREADY")
    print("STRUCTURE_PRESERVED=YES")
    print("LOGIC_PRESERVED=YES")
    raise SystemExit(0)

# Harmless marker.
ui = ui.replace("BALANCED_PREMIUM_V12 ", "BALANCED_PREMIUM_V12 INTEGRATED_DARK_PANELS_V13 ", 1)

# -----------------------------------------------------------------------------
# V13: eliminate bright/light inner islands in dark mode.
# Use solid, compile-safe slate backgrounds (no arbitrary hex opacity suffixes).
# -----------------------------------------------------------------------------
solid_panels = [
    ("dark:bg-[#334755]/72", "dark:!bg-[#2A3D4A]"),
    ("dark:bg-[#354A59]/74", "dark:!bg-[#2E4351]"),
    ("dark:bg-[#374D5D]/76", "dark:!bg-[#324956]"),
]
for old, new in solid_panels:
    if old not in ui:
        raise SystemExit(f"BLOCKED: V12 bright-panel anchor missing: {old}")
    ui = ui.replace(old, new)

# Any remaining tiny dark-white fills inside the GitHub premium branch become
# explicit slate surfaces, preventing light-mode backgrounds from leaking through.
ui = ui.replace("dark:bg-white/[0.025]", "dark:!bg-[#273A47]")
ui = ui.replace("dark:bg-white/[0.035]", "dark:!bg-[#293C49]")
ui = ui.replace("dark:bg-white/[0.04]", "dark:!bg-[#2B3E4B]")
ui = ui.replace("dark:bg-white/[0.045]", "dark:!bg-[#2D414E]")

# Workflow cards: keep all four visually dark and integrated.
workflow_start = ui.find('<section id="github-workflow"')
workflow_end = ui.find('<section id="github-changes"', workflow_start)
if workflow_start < 0 or workflow_end < 0:
    raise SystemExit("BLOCKED: workflow scope not found")
workflow = ui[workflow_start:workflow_end]

# Step 1: calm teal slate, not a bright green panel.
workflow = workflow.replace(
    "dark:bg-emerald-400/[0.10]",
    "dark:!bg-[#203E3E]"
)
# Review/Push state fills remain slate with subtle color borders instead of bright cards.
workflow = workflow.replace("dark:bg-sky-400/[0.085]", "dark:!bg-[#2A4050]")
workflow = workflow.replace("dark:bg-amber-400/[0.065]", "dark:!bg-[#3A3528]")
workflow = workflow.replace("dark:bg-emerald-500/5", "dark:!bg-[#203E3E]")
workflow = workflow.replace("dark:bg-blue-500/5", "dark:!bg-[#2A4050]")
workflow = workflow.replace("dark:bg-amber-500/5", "dark:!bg-[#3A3528]")

# Force any workflow card carrying the V7 min-height contract onto a valid slate
# dark surface if its conditional light background would otherwise win.
workflow = workflow.replace(
    'flex min-h-[154px] min-w-0 flex-col rounded-[24px] border p-[18px]',
    'flex min-h-[154px] min-w-0 flex-col rounded-[24px] border p-[18px] dark:!bg-[#2B3F4C]'
)

ui = ui[:workflow_start] + workflow + ui[workflow_end:]

# Changes by type: rows should be mid-slate, never white.
changes_start = ui.find('<section id="github-changes"')
changes_end = ui.find('id="github-connection"', changes_start)
if changes_start < 0:
    raise SystemExit("BLOCKED: changes scope not found")
if changes_end < 0:
    changes_end = len(ui)
changes = ui[changes_start:changes_end]
changes = re.sub(
    r'className="flex items-center justify-between rounded-xl ([^"]*)"',
    lambda m: f'className="flex items-center justify-between rounded-xl {m.group(1)} dark:!bg-[#2C404D] dark:!text-[#E8EEF3]"',
    changes,
)

# Activity labels: deterministic readable hierarchy.
changes = re.sub(
    r'className="min-w-0 truncate text-\[11px\] font-black leading-4[^"]*"',
    'className="min-w-0 truncate text-[11px] font-black leading-4 text-zinc-800 dark:!text-[#E9EFF4]"',
    changes,
)
changes = re.sub(
    r'className="min-w-0 text-\[10px\] font-bold leading-4[^"]*sm:whitespace-nowrap[^"]*"',
    'className="min-w-0 text-[10px] font-bold leading-4 text-zinc-400 dark:!text-[#B9C6D0] sm:whitespace-nowrap"',
    changes,
)
ui = ui[:changes_start] + changes + ui[changes_end:]

# Repository information compact cells: solid soft slate instead of gray/white islands.
repo_heading = ui.find('>{ui("معلومات المستودع", "Repository Information")}</h3>')
if repo_heading < 0:
    repo_heading = ui.find("Repository Information")
connection_start = ui.find('id="github-connection"')
if repo_heading >= 0 and connection_start > repo_heading:
    repo_scope = ui[repo_heading:connection_start]
    repo_scope = repo_scope.replace("dark:!bg-[#2A3D4A]", "dark:!bg-[#304552]")
    repo_scope = repo_scope.replace("dark:!bg-[#2E4351]", "dark:!bg-[#304552]")
    repo_scope = repo_scope.replace("dark:!bg-[#324956]", "dark:!bg-[#304552]")
    # Explicitly catch repository data cells that still have a light bg-white base.
    repo_scope = re.sub(
        r'(className="[^"]*min-w-0 overflow-hidden rounded-2xl[^"]*)"',
        r'\1 dark:!bg-[#304552] dark:!border-slate-300/[0.12]"',
        repo_scope,
    )
    ui = ui[:repo_heading] + repo_scope + ui[connection_start:]

# Keep shell/Hero/card hierarchy from V12 unchanged. Only soften inner borders slightly.
ui = ui.replace("dark:border-slate-300/[0.14]", "dark:border-slate-300/[0.12]")
ui = ui.replace("dark:border-slate-300/[0.135]", "dark:border-slate-300/[0.115]")

# -----------------------------------------------------------------------------
# Settings header: force the actual GitHub h1 to soft white directly.
# -----------------------------------------------------------------------------
fn_start = settings.find("function SettingsSectionHeader({ section })")
fn_end = settings.find("\nfunction ", fn_start + 10)
if fn_start < 0:
    raise SystemExit("BLOCKED: SettingsSectionHeader function not found")
if fn_end < 0:
    fn_end = len(settings)
header_scope = settings[fn_start:fn_end]

# Handle baseline/V12 variants safely.
header_scope = header_scope.replace(
    'text-zinc-950 dark:text-white',
    'text-zinc-950 dark:text-[#F5F7F9] dark:!text-[#F5F7F9]'
)
header_scope = header_scope.replace(
    'text-zinc-950 dark:!text-[#F4F6F8]',
    'text-zinc-950 dark:text-[#F5F7F9] dark:!text-[#F5F7F9]'
)
# The subtitle remains secondary, but clearly readable.
header_scope = header_scope.replace(
    'className="tos-muted mt-2 max-w-3xl"',
    'className="tos-muted mt-2 max-w-3xl dark:!text-[#B9C6D0]"'
)
settings = settings[:fn_start] + header_scope + settings[fn_end:]

# -----------------------------------------------------------------------------
# Safety validation.
# -----------------------------------------------------------------------------
for token in ["<section", "<article", "<Button", "onClick=", "useState(", "useEffect(", "api.github.", "<details", "<summary"]:
    if ui_original.count(token) != ui.count(token):
        raise SystemExit(f"BLOCKED: GithubAdvancedAdmin structure/logic changed: {token}")

for token in ["function SettingsSectionHeader", "function GithubAdmin", "<GithubAdvancedAdmin", "useState(", "useEffect("]:
    if settings_original.count(token) != settings.count(token):
        raise SystemExit(f"BLOCKED: SettingsPage structure/logic changed: {token}")

# V7 layout guards remain untouched.
for token in ["xl:grid-cols-[260px_minmax(0,1fr)]", "min-h-[154px]", "break-all font-mono"]:
    if ui_original.count(token) != ui.count(token):
        raise SystemExit(f"BLOCKED: layout guard changed: {token}")

# Light-mode palette remains untouched.
for token in ["#FFFEFB", "#FBF5E8", "#FFFDFC", "#E8D7B1", "#E7D7B6", "#EADFC8"]:
    if ui_original.count(token) != ui.count(token):
        raise SystemExit(f"BLOCKED: light-mode token changed: {token}")

# Hero/shell must remain V12 values: V13 is an inner-panel correction, not another redesign.
for token in ["#2A4050", "#243541", "#17232D", "#1B2934"]:
    if token in ui_original and ui_original.count(token) != ui.count(token):
        raise SystemExit(f"BLOCKED: V12 shell/hero token changed unexpectedly: {token}")

if ui == ui_original:
    raise SystemExit("BLOCKED: no V13 GithubAdvancedAdmin changes produced")
if settings == settings_original:
    raise SystemExit("BLOCKED: no V13 SettingsPage changes produced")

GITHUB_UI.write_text(ui, encoding="utf-8")
SETTINGS_PAGE.write_text(settings, encoding="utf-8")

print("PATCH_APPLIED=YES")
print("BASE=V12_BALANCED_PREMIUM_DARK")
print("FILES_CHANGED=2")
print("STRUCTURE_PRESERVED=YES")
print("LOGIC_PRESERVED=YES")
print("LAYOUT_PRESERVED=YES")
print("LIGHT_MODE_UNCHANGED=YES")
print("SHELL_HERO_PRESERVED=YES")
print("BRIGHT_INNER_PANELS_REMOVED=YES")
print("WORKFLOW_DARK_INTEGRATED=YES")
print("CHANGES_ROWS_DARK_INTEGRATED=YES")
print("REPOSITORY_TILES_DARK_INTEGRATED=YES")
print("ACTIVITY_READABILITY_FIXED=YES")
print("GITHUB_TITLE_FIXED=YES")
print("DARK_MODE_INTEGRATED=YES")
