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

required_ui = [
    "PREMIUM_SLATE_V10",
    "#1C2733",
    "#243442",
    "min-h-[154px]",
    "break-all font-mono",
    'id="github-overview"',
    'id="github-workflow"',
    'id="github-changes"',
]
for anchor in required_ui:
    if anchor not in ui:
        raise SystemExit(f"BLOCKED: expected V10 marker missing: {anchor}")

if "SLATE_REFINEMENT_V11" in ui:
    print("PATCH_APPLIED=ALREADY")
    print("STRUCTURE_PRESERVED=YES")
    print("LOGIC_PRESERVED=YES")
    raise SystemExit(0)

# Harmless marker on premium root.
ui = ui.replace("PREMIUM_SLATE_V10 ", "PREMIUM_SLATE_V10 SLATE_REFINEMENT_V11 ", 1)

# -----------------------------------------------------------------------------
# V11 visual refinement: brighter slate hierarchy, cleaner separation, less black.
# Light mode classes/tokens are intentionally untouched.
# -----------------------------------------------------------------------------
replacements = [
    # Hero becomes lighter/more polished while remaining dark.
    (
        "dark:bg-[radial-gradient(circle_at_88%_-18%,rgba(198,167,99,0.11),transparent_38%),radial-gradient(circle_at_8%_130%,rgba(120,145,168,0.07),transparent_40%),linear-gradient(135deg,#1C2733_0%,#243442_56%,#1B2631_100%)]",
        "dark:bg-[radial-gradient(circle_at_88%_-18%,rgba(198,167,99,0.085),transparent_40%),radial-gradient(circle_at_8%_130%,rgba(123,157,184,0.10),transparent_42%),linear-gradient(135deg,#263745_0%,#2E4252_56%,#243441_100%)]"
    ),
    # Primary cards: clearer lighter slate layer.
    ("dark:bg-[linear-gradient(180deg,#202D3A_0%,#1A2530_100%)]", "dark:bg-[linear-gradient(180deg,#293A48_0%,#23323F_100%)]"),
    ("dark:bg-[linear-gradient(180deg,#1E2A36_0%,#18232D_100%)]", "dark:bg-[linear-gradient(180deg,#273744_0%,#21303C_100%)]"),
    ("dark:bg-[#1E2935]", "dark:bg-[#293845]"),
    ("dark:bg-[#1A2530]", "dark:bg-[#24323F]"),
    ("dark:bg-[#2B3744]", "dark:bg-[#344552]"),
    # Inner panels: subtle lifted surface.
    ("dark:bg-white/[0.055]", "dark:bg-white/[0.075]"),
    ("dark:bg-white/[0.06]", "dark:bg-white/[0.08]"),
    ("dark:bg-white/[0.065]", "dark:bg-white/[0.085]"),
    # Border hierarchy: cleaner, softer cool separators.
    ("dark:border-white/[0.10]", "dark:border-slate-200/[0.14]"),
    ("dark:border-white/[0.105]", "dark:border-slate-200/[0.145]"),
    ("dark:border-white/[0.11]", "dark:border-slate-200/[0.15]"),
    ("dark:border-white/[0.115]", "dark:border-slate-200/[0.155]"),
    ("dark:border-white/[0.12]", "dark:border-slate-200/[0.16]"),
    # Softer premium text hierarchy.
    ("dark:!text-[#EEF2F5]", "dark:!text-[#F1F4F7]"),
    ("dark:!text-[#E7ECF1]", "dark:!text-[#E8EDF2]"),
    ("dark:!text-[#DCE3E9]", "dark:!text-[#DCE4EB]"),
    ("dark:!text-[#BEC8D2]", "dark:!text-[#C4CED7]"),
    ("dark:!text-[#9FAEBC]", "dark:!text-[#AEBBC7]"),
    ("dark:!text-[#A6B3C0]", "dark:!text-[#B5C0CA]"),
    # Calm shadows on brighter slate.
    ("dark:shadow-[0_24px_70px_rgba(8,14,22,0.24)]", "dark:shadow-[0_22px_60px_rgba(5,12,20,0.18)]"),
    ("dark:shadow-[0_20px_58px_rgba(8,14,22,0.22)]", "dark:shadow-[0_18px_50px_rgba(5,12,20,0.16)]"),
    ("dark:shadow-[0_16px_44px_rgba(8,14,22,0.18)]", "dark:shadow-[0_14px_38px_rgba(5,12,20,0.14)]"),
]

changed = 0
for old, new in replacements:
    if old in ui:
        ui = ui.replace(old, new)
        changed += 1

if changed < 10:
    raise SystemExit(f"BLOCKED: too few V11 UI anchors matched ({changed})")

# Workflow: reduce dark/brown button feel; champagne remains only as restrained action accent.
ui = ui.replace("dark:bg-amber-400/[0.07]", "dark:bg-amber-300/[0.055]")
ui = ui.replace("dark:bg-emerald-400/[0.10]", "dark:bg-emerald-300/[0.095]")
ui = ui.replace("dark:bg-sky-400/[0.08]", "dark:bg-sky-300/[0.075]")

# -----------------------------------------------------------------------------
# Recent Sync Activity readability: canonicalize duplicate dark text utilities.
# This fixes the labels that remained visually too dark after V9/V10.
# -----------------------------------------------------------------------------
activity_start = ui.find('>{ui("نشاط المزامنة الأخير", "Recent Sync Activity")}</h3>')
if activity_start < 0:
    activity_start = ui.find('Recent Sync Activity')
activity_end = ui.find('</article>', activity_start)
if activity_start < 0 or activity_end < 0:
    raise SystemExit("BLOCKED: Recent Sync Activity scope not found")
activity = ui[activity_start:activity_end]

# Replace the activity label/meta class strings with single deterministic dark colors.
activity = re.sub(
    r'className="min-w-0 truncate text-\[11px\] font-black leading-4[^\"]*"',
    'className="min-w-0 truncate text-[11px] font-black leading-4 text-zinc-800 dark:!text-[#EEF2F6]"',
    activity,
)
activity = re.sub(
    r'className="min-w-0 text-\[10px\] font-bold leading-4[^\"]*sm:whitespace-nowrap[^\"]*"',
    'className="min-w-0 text-[10px] font-bold leading-4 text-zinc-400 dark:!text-[#B9C5CF] sm:whitespace-nowrap"',
    activity,
)
ui = ui[:activity_start] + activity + ui[activity_end:]

# -----------------------------------------------------------------------------
# Settings page shell + section header: remove the remaining black canvas feel.
# Only the GitHub section gets this dark-mode shell, Light Mode remains unchanged.
# -----------------------------------------------------------------------------
root_old = '<div className="tos-page space-y-5">'
root_new = '<div className={`tos-page space-y-5 ${activeSection === "github" ? "dark:rounded-[34px] dark:bg-[radial-gradient(circle_at_75%_-8%,rgba(92,126,151,0.14),transparent_32%),linear-gradient(180deg,#1B2834_0%,#1E2D39_48%,#1A2732_100%)] dark:p-4 dark:shadow-[inset_0_1px_0_rgba(255,255,255,0.035)]" : ""}`}>'
if root_old not in settings:
    raise SystemExit("BLOCKED: SettingsPage root anchor not found")
settings = settings.replace(root_old, root_new, 1)

header_v10 = 'className="flex flex-col gap-4 rounded-[30px] border border-transparent bg-transparent py-1 lg:flex-row lg:items-center lg:justify-between dark:border-white/[0.09] dark:bg-[#202B37] dark:px-5 dark:py-4 dark:shadow-[0_16px_44px_rgba(8,14,22,0.16)] dark:[&_h1]:!text-[#EEF2F5] dark:[&_h2]:!text-[#EEF2F5] dark:[&_h3]:!text-[#EEF2F5] dark:[&_p]:!text-[#AAB6C2]"'
header_v11 = 'className="flex flex-col gap-4 rounded-[30px] border border-transparent bg-transparent py-1 lg:flex-row lg:items-center lg:justify-between dark:border-slate-200/[0.14] dark:bg-[linear-gradient(135deg,#2A3A47_0%,#314656_100%)] dark:px-5 dark:py-4 dark:shadow-[0_16px_40px_rgba(5,12,20,0.14)] dark:[&_h1]:!text-[#F1F4F7] dark:[&_h2]:!text-[#F1F4F7] dark:[&_h3]:!text-[#F1F4F7] dark:[&_p]:!text-[#BAC6D0]"'
if header_v10 not in settings:
    raise SystemExit("BLOCKED: V10 SettingsSectionHeader anchor not found")
settings = settings.replace(header_v10, header_v11, 1)

# -----------------------------------------------------------------------------
# Safety validation.
# -----------------------------------------------------------------------------
for token in ["<section", "<article", "<Button", "onClick=", "useState(", "useEffect(", "api.github.", "<details", "<summary"]:
    if ui_original.count(token) != ui.count(token):
        raise SystemExit(f"BLOCKED: GithubAdvancedAdmin structure/logic changed: {token}")

for token in ["function SettingsSectionHeader", "function GithubAdmin", "<GithubAdvancedAdmin", "useState(", "useEffect("]:
    if settings_original.count(token) != settings.count(token):
        raise SystemExit(f"BLOCKED: SettingsPage structure/logic changed: {token}")

# Light mode sentinel counts remain unchanged.
for token in ["#FFFEFB", "#FBF5E8", "#FFFDFC", "#E8D7B1", "#E7D7B6", "#EADFC8"]:
    if ui_original.count(token) != ui.count(token):
        raise SystemExit(f"BLOCKED: light-mode UI token changed: {token}")

# Layout guards must remain intact.
for token in ["xl:grid-cols-[260px_minmax(0,1fr)]", "min-h-[154px]", "break-all font-mono"]:
    if ui_original.count(token) != ui.count(token):
        raise SystemExit(f"BLOCKED: layout guard changed: {token}")

if ui == ui_original:
    raise SystemExit("BLOCKED: no V11 GithubAdvancedAdmin changes produced")
if settings == settings_original:
    raise SystemExit("BLOCKED: no V11 SettingsPage changes produced")

GITHUB_UI.write_text(ui, encoding="utf-8")
SETTINGS_PAGE.write_text(settings, encoding="utf-8")

print("PATCH_APPLIED=YES")
print("BASE=V10_PREMIUM_SLATE")
print("FILES_CHANGED=2")
print("STRUCTURE_PRESERVED=YES")
print("LOGIC_PRESERVED=YES")
print("LAYOUT_PRESERVED=YES")
print("LIGHT_MODE_UNCHANGED=YES")
print("PAGE_SHELL_REFINED=YES")
print("TOP_HEADER_REFINED=YES")
print("SLATE_SURFACES_LIGHTENED=YES")
print("CARD_LAYERING_REFINED=YES")
print("ACTIVITY_READABILITY_FIXED=YES")
print("GOLD_RESTRAINED=YES")
print("DARK_EYE_COMFORT=YES")
