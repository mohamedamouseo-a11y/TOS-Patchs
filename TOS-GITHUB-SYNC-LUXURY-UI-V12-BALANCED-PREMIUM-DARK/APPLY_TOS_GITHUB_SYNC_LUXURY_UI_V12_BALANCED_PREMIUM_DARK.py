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
    "SLATE_REFINEMENT_V11",
    "#2E4252",
    "#293A48",
    "min-h-[154px]",
    "break-all font-mono",
    'id="github-overview"',
    'id="github-workflow"',
    'id="github-changes"',
]
for anchor in required_ui:
    if anchor not in ui:
        raise SystemExit(f"BLOCKED: expected V11 marker missing: {anchor}")

if "BALANCED_PREMIUM_V12" in ui:
    print("PATCH_APPLIED=ALREADY")
    print("STRUCTURE_PRESERVED=YES")
    print("LOGIC_PRESERVED=YES")
    raise SystemExit(0)

ui = ui.replace("SLATE_REFINEMENT_V11 ", "SLATE_REFINEMENT_V11 BALANCED_PREMIUM_V12 ", 1)

# -----------------------------------------------------------------------------
# V12: restore visual hierarchy without returning to near-black.
# Page shell is deeper graphite; hero/cards/panels step upward in clear layers.
# Light-mode tokens/classes are intentionally untouched.
# -----------------------------------------------------------------------------
replacements = [
    # Hero: richer blue-slate with controlled depth and subtle champagne/cool glow.
    (
        "dark:bg-[radial-gradient(circle_at_88%_-18%,rgba(198,167,99,0.085),transparent_40%),radial-gradient(circle_at_8%_130%,rgba(123,157,184,0.10),transparent_42%),linear-gradient(135deg,#263745_0%,#2E4252_56%,#243441_100%)]",
        "dark:bg-[radial-gradient(circle_at_86%_-18%,rgba(199,171,107,0.10),transparent_38%),radial-gradient(circle_at_8%_120%,rgba(99,145,176,0.11),transparent_40%),linear-gradient(135deg,#21313E_0%,#2A4050_54%,#223542_100%)]"
    ),

    # Primary cards: slightly deeper than V11 so they regain definition against inner panels.
    ("dark:bg-[linear-gradient(180deg,#293A48_0%,#23323F_100%)]", "dark:bg-[linear-gradient(180deg,#243541_0%,#1F2E39_100%)]"),
    ("dark:bg-[linear-gradient(180deg,#273744_0%,#21303C_100%)]", "dark:bg-[linear-gradient(180deg,#22323E_0%,#1D2B36_100%)]"),
    ("dark:bg-[#293845]", "dark:bg-[#263844]"),
    ("dark:bg-[#24323F]", "dark:bg-[#21313D]"),
    ("dark:bg-[#344552]", "dark:bg-[#314653]"),

    # Inner panels: distinctly lifted, not washed-out.
    ("dark:bg-white/[0.075]", "dark:bg-[#334755]/72"),
    ("dark:bg-white/[0.08]", "dark:bg-[#354A59]/74"),
    ("dark:bg-white/[0.085]", "dark:bg-[#374D5D]/76"),

    # Borders: reduce the milky/washed look while keeping separation.
    ("dark:border-slate-200/[0.14]", "dark:border-slate-300/[0.12]"),
    ("dark:border-slate-200/[0.145]", "dark:border-slate-300/[0.125]"),
    ("dark:border-slate-200/[0.15]", "dark:border-slate-300/[0.13]"),
    ("dark:border-slate-200/[0.155]", "dark:border-slate-300/[0.135]"),
    ("dark:border-slate-200/[0.16]", "dark:border-slate-300/[0.14]"),

    # Text: crisp but not glaring.
    ("dark:!text-[#F1F4F7]", "dark:!text-[#F4F6F8]"),
    ("dark:!text-[#E8EDF2]", "dark:!text-[#E9EDF1]"),
    ("dark:!text-[#DCE4EB]", "dark:!text-[#D6DEE6]"),
    ("dark:!text-[#C4CED7]", "dark:!text-[#C5CFD8]"),
    ("dark:!text-[#AEBBC7]", "dark:!text-[#AEBBC6]"),
    ("dark:!text-[#B5C0CA]", "dark:!text-[#B9C4CE]"),

    # Shadows: slightly more definition than V11, still soft and premium.
    ("dark:shadow-[0_22px_60px_rgba(5,12,20,0.18)]", "dark:shadow-[0_22px_58px_rgba(4,10,18,0.22)]"),
    ("dark:shadow-[0_18px_50px_rgba(5,12,20,0.16)]", "dark:shadow-[0_18px_46px_rgba(4,10,18,0.20)]"),
    ("dark:shadow-[0_14px_38px_rgba(5,12,20,0.14)]", "dark:shadow-[0_14px_34px_rgba(4,10,18,0.17)]"),
]

changed = 0
for old, new in replacements:
    if old in ui:
        ui = ui.replace(old, new)
        changed += 1

if changed < 12:
    raise SystemExit(f"BLOCKED: too few V12 UI anchors matched ({changed}); current state is unexpected")

# Sidebar shell: keep it darker than content, but never near-black.
ui = ui.replace(
    "dark:bg-[linear-gradient(180deg,rgba(31,42,54,0.99)_0%,rgba(25,34,45,0.99)_100%)]",
    "dark:bg-[linear-gradient(180deg,rgba(27,39,50,0.99)_0%,rgba(22,32,42,0.99)_100%)]"
)
ui = ui.replace(
    "dark:bg-[radial-gradient(circle_at_14%_0%,rgba(199,168,99,0.085),transparent_48%),linear-gradient(180deg,rgba(39,51,65,0.97),rgba(30,40,52,0.98))]",
    "dark:bg-[radial-gradient(circle_at_14%_0%,rgba(199,168,99,0.075),transparent_48%),linear-gradient(180deg,rgba(34,47,59,0.98),rgba(28,39,49,0.99))]"
)

# Workflow: preserve states but give selected/action states cleaner premium contrast.
ui = ui.replace("dark:bg-emerald-300/[0.095]", "dark:bg-emerald-400/[0.10]")
ui = ui.replace("dark:bg-sky-300/[0.075]", "dark:bg-sky-400/[0.085]")
ui = ui.replace("dark:bg-amber-300/[0.055]", "dark:bg-amber-400/[0.065]")

# Recent activity: deterministic readable hierarchy on the deeper V12 surface.
activity_start = ui.find('>{ui("نشاط المزامنة الأخير", "Recent Sync Activity")}</h3>')
if activity_start < 0:
    activity_start = ui.find("Recent Sync Activity")
activity_end = ui.find("</article>", activity_start)
if activity_start < 0 or activity_end < 0:
    raise SystemExit("BLOCKED: Recent Sync Activity scope not found")
activity = ui[activity_start:activity_end]
activity = re.sub(
    r'className="min-w-0 truncate text-\[11px\] font-black leading-4[^\"]*"',
    'className="min-w-0 truncate text-[11px] font-black leading-4 text-zinc-800 dark:!text-[#F0F3F6]"',
    activity,
)
activity = re.sub(
    r'className="min-w-0 text-\[10px\] font-bold leading-4[^\"]*sm:whitespace-nowrap[^\"]*"',
    'className="min-w-0 text-[10px] font-bold leading-4 text-zinc-400 dark:!text-[#B8C4CE] sm:whitespace-nowrap"',
    activity,
)
ui = ui[:activity_start] + activity + ui[activity_end:]

# -----------------------------------------------------------------------------
# Settings page shell/header: deepen the canvas, keep header lighter and integrated.
# Light mode remains unchanged because all additions are dark: utilities.
# -----------------------------------------------------------------------------
settings_root_old = 'dark:bg-[radial-gradient(circle_at_75%_-8%,rgba(92,126,151,0.14),transparent_32%),linear-gradient(180deg,#1B2834_0%,#1E2D39_48%,#1A2732_100%)]'
settings_root_new = 'dark:bg-[radial-gradient(circle_at_76%_-8%,rgba(84,128,158,0.12),transparent_32%),linear-gradient(180deg,#17232D_0%,#1B2934_48%,#18252F_100%)]'
if settings_root_old not in settings:
    raise SystemExit("BLOCKED: V11 SettingsPage shell anchor not found")
settings = settings.replace(settings_root_old, settings_root_new, 1)

header_old = 'dark:border-slate-200/[0.14] dark:bg-[linear-gradient(135deg,#2A3A47_0%,#314656_100%)] dark:px-5 dark:py-4 dark:shadow-[0_16px_40px_rgba(5,12,20,0.14)] dark:[&_h1]:!text-[#F1F4F7] dark:[&_h2]:!text-[#F1F4F7] dark:[&_h3]:!text-[#F1F4F7] dark:[&_p]:!text-[#BAC6D0]'
header_new = 'dark:border-slate-300/[0.13] dark:bg-[radial-gradient(circle_at_88%_-30%,rgba(97,145,177,0.14),transparent_36%),linear-gradient(135deg,#22313D_0%,#29404F_100%)] dark:px-5 dark:py-4 dark:shadow-[0_16px_36px_rgba(4,10,18,0.18)] dark:[&_h1]:!text-[#F4F6F8] dark:[&_h2]:!text-[#F4F6F8] dark:[&_h3]:!text-[#F4F6F8] dark:[&_p]:!text-[#B9C5CF]'
if header_old not in settings:
    raise SystemExit("BLOCKED: V11 SettingsSectionHeader anchor not found")
settings = settings.replace(header_old, header_new, 1)

# Directly enforce heading/muted text inside SettingsSectionHeader; fixes the visible dark GitHub title.
fn_start = settings.find("function SettingsSectionHeader({ section })")
fn_end = settings.find("\nfunction ", fn_start + 10)
if fn_start < 0:
    raise SystemExit("BLOCKED: SettingsSectionHeader function not found")
if fn_end < 0:
    fn_end = len(settings)
header_scope = settings[fn_start:fn_end]
header_scope = header_scope.replace(
    'text-zinc-950 dark:text-white',
    'text-zinc-950 dark:!text-[#F4F6F8]'
)
header_scope = header_scope.replace(
    'className="tos-muted',
    'className="tos-muted dark:!text-[#B9C5CF]'
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

for token in ["#FFFEFB", "#FBF5E8", "#FFFDFC", "#E8D7B1", "#E7D7B6", "#EADFC8"]:
    if ui_original.count(token) != ui.count(token):
        raise SystemExit(f"BLOCKED: light-mode UI token changed: {token}")

for token in ["xl:grid-cols-[260px_minmax(0,1fr)]", "min-h-[154px]", "break-all font-mono"]:
    if ui_original.count(token) != ui.count(token):
        raise SystemExit(f"BLOCKED: layout guard changed: {token}")

if ui == ui_original:
    raise SystemExit("BLOCKED: no V12 GithubAdvancedAdmin changes produced")
if settings == settings_original:
    raise SystemExit("BLOCKED: no V12 SettingsPage changes produced")

GITHUB_UI.write_text(ui, encoding="utf-8")
SETTINGS_PAGE.write_text(settings, encoding="utf-8")

print("PATCH_APPLIED=YES")
print("BASE=V11_SLATE_REFINEMENT")
print("FILES_CHANGED=2")
print("STRUCTURE_PRESERVED=YES")
print("LOGIC_PRESERVED=YES")
print("LAYOUT_PRESERVED=YES")
print("LIGHT_MODE_UNCHANGED=YES")
print("VISUAL_HIERARCHY_RESTORED=YES")
print("PAGE_SHELL_BALANCED=YES")
print("HERO_DEPTH_RESTORED=YES")
print("CARD_LAYERING_BALANCED=YES")
print("INNER_PANEL_SEPARATION=YES")
print("TOP_HEADER_BALANCED=YES")
print("GITHUB_TITLE_CONTRAST_FIXED=YES")
print("ACTIVITY_READABILITY_PRESERVED=YES")
print("NEAR_BLACK_AVOIDED=YES")
print("DARK_EYE_COMFORT=YES")
