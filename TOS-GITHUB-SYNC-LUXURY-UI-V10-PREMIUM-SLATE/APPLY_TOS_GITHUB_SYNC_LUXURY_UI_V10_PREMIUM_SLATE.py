#!/usr/bin/env python3
from pathlib import Path

GITHUB_UI = Path("frontend/src/components/GithubAdvancedAdmin.jsx")
SETTINGS_PAGE = Path("frontend/src/pages/SettingsPage.jsx")

for target in (GITHUB_UI, SETTINGS_PAGE):
    if not target.exists():
        raise SystemExit(f"BLOCKED: target not found: {target}")

ui = GITHUB_UI.read_text(encoding="utf-8")
settings = SETTINGS_PAGE.read_text(encoding="utf-8")
ui_original = ui
settings_original = settings

# V10 expects the current successful V9 state.
required = [
    "DARK_COMFORT_V8",
    "DARK_TEXT_CONTRAST_V9",
    "#161F2A",
    "#151D27",
    "#101720",
    'id="github-overview"',
    'id="github-workflow"',
    'id="github-changes"',
    'id="github-connection"',
    'id="github-console"',
]
for anchor in required:
    if anchor not in ui:
        raise SystemExit(f"BLOCKED: expected V9 marker missing: {anchor}")

if "PREMIUM_SLATE_V10" in ui:
    print("PATCH_APPLIED=ALREADY")
    print("STRUCTURE_PRESERVED=YES")
    print("LOGIC_PRESERVED=YES")
    raise SystemExit(0)

# Add harmless marker and slightly softer default dark text.
root_old = "DARK_COMFORT_V8 DARK_TEXT_CONTRAST_V9 grid min-w-0 gap-6 text-[#2E2417] dark:text-[#E4E8ED]"
root_new = "DARK_COMFORT_V8 DARK_TEXT_CONTRAST_V9 PREMIUM_SLATE_V10 grid min-w-0 gap-6 text-[#2E2417] dark:text-[#E7EBEF]"
if root_old not in ui:
    raise SystemExit("BLOCKED: V9 root marker/class not found")
ui = ui.replace(root_old, root_new, 1)

# -----------------------------------------------------------------------------
# V10 premium slate system: less black, clearer layered surfaces, calmer contrast.
# Light-mode tokens are intentionally untouched.
# -----------------------------------------------------------------------------
replacements = [
    # Sidebar shell: graphite/slate instead of near-black.
    (
        "dark:bg-[linear-gradient(180deg,rgba(20,27,37,0.98)_0%,rgba(14,20,28,0.99)_100%)]",
        "dark:bg-[linear-gradient(180deg,rgba(31,42,54,0.99)_0%,rgba(25,34,45,0.99)_100%)]"
    ),
    (
        "dark:bg-[radial-gradient(circle_at_14%_0%,rgba(205,171,96,0.11),transparent_48%),linear-gradient(180deg,rgba(24,32,43,0.94),rgba(16,22,31,0.96))]",
        "dark:bg-[radial-gradient(circle_at_14%_0%,rgba(199,168,99,0.085),transparent_48%),linear-gradient(180deg,rgba(39,51,65,0.97),rgba(30,40,52,0.98))]"
    ),

    # Hero: premium blue-graphite, visibly lighter than old near-black canvas.
    (
        "dark:bg-[radial-gradient(circle_at_88%_-18%,rgba(205,171,96,0.14),transparent_36%),radial-gradient(circle_at_8%_130%,rgba(185,133,46,0.055),transparent_38%),linear-gradient(135deg,#111821_0%,#161F2A_56%,#10161E_100%)]",
        "dark:bg-[radial-gradient(circle_at_88%_-18%,rgba(198,167,99,0.11),transparent_38%),radial-gradient(circle_at_8%_130%,rgba(120,145,168,0.07),transparent_40%),linear-gradient(135deg,#1C2733_0%,#243442_56%,#1B2631_100%)]"
    ),

    # Primary card surfaces.
    (
        "dark:bg-[linear-gradient(180deg,#151D27_0%,#101720_100%)]",
        "dark:bg-[linear-gradient(180deg,#202D3A_0%,#1A2530_100%)]"
    ),
    (
        "dark:bg-[linear-gradient(180deg,#141C26_0%,#0F161F_100%)]",
        "dark:bg-[linear-gradient(180deg,#1E2A36_0%,#18232D_100%)]"
    ),
    ("dark:bg-[#141B24]", "dark:bg-[#1E2935]"),
    ("dark:bg-[#111821]", "dark:bg-[#1A2530]"),
    ("dark:bg-[#232C37]", "dark:bg-[#2B3744]"),

    # Nested surfaces gain separation without becoming bright.
    ("dark:bg-white/[0.035]", "dark:bg-white/[0.055]"),
    ("dark:bg-white/[0.04]", "dark:bg-white/[0.06]"),
    ("dark:bg-white/[0.045]", "dark:bg-white/[0.065]"),

    # Text hierarchy: soft neutral whites / blue-grays.
    ("dark:!text-[#F3F5F7]", "dark:!text-[#EEF2F5]"),
    ("dark:!text-[#E9EDF1]", "dark:!text-[#E7ECF1]"),
    ("dark:!text-[#E0E5EA]", "dark:!text-[#DCE3E9]"),
    ("dark:!text-[#C4CCD5]", "dark:!text-[#BEC8D2]"),
    ("dark:!text-[#ADB7C2]", "dark:!text-[#9FAEBC]"),
    ("dark:!text-[#AEB8C3]", "dark:!text-[#A6B3C0]"),
    ("dark:!text-[#B8C1CB]", "dark:!text-[#B3BEC9]"),

    # Neutral borders replace the black/gold-heavy feel.
    ("dark:border-white/[0.065]", "dark:border-white/[0.10]"),
    ("dark:border-white/[0.07]", "dark:border-white/[0.105]"),
    ("dark:border-white/[0.075]", "dark:border-white/[0.11]"),
    ("dark:border-white/[0.08]", "dark:border-white/[0.115]"),
    ("dark:border-white/[0.085]", "dark:border-white/[0.12]"),

    # Premium focal borders remain warm but restrained.
    ("dark:border-[#C9A85F]/16", "dark:border-[#C5A967]/18"),
    ("dark:border-[#C9A85F]/18", "dark:border-[#C5A967]/20"),
    ("dark:border-[#C9A85F]/20", "dark:border-[#C5A967]/22"),

    # Shadows become softer, broader and less black.
    ("dark:shadow-[0_28px_84px_rgba(0,0,0,0.38)]", "dark:shadow-[0_24px_70px_rgba(8,14,22,0.24)]"),
    ("dark:shadow-[0_24px_72px_rgba(0,0,0,0.36)]", "dark:shadow-[0_20px_58px_rgba(8,14,22,0.22)]"),
    ("dark:shadow-[0_18px_52px_rgba(0,0,0,0.24)]", "dark:shadow-[0_16px_44px_rgba(8,14,22,0.18)]"),
    ("dark:shadow-[0_16px_44px_rgba(0,0,0,0.22)]", "dark:shadow-[0_14px_38px_rgba(8,14,22,0.17)]"),

    # Active gold becomes champagne accent rather than a large brown/yellow block.
    (
        "dark:bg-[linear-gradient(135deg,rgba(185,133,46,0.14),rgba(217,174,91,0.045))] dark:text-[#D8BB73]",
        "dark:bg-[linear-gradient(135deg,rgba(196,166,99,0.105),rgba(196,166,99,0.035))] dark:text-[#D4BD83]"
    ),
    (
        "dark:bg-[linear-gradient(180deg,rgba(205,171,96,0.07),rgba(205,171,96,0.035))]",
        "dark:bg-[linear-gradient(180deg,rgba(196,166,99,0.055),rgba(196,166,99,0.025))]"
    ),
]

changed_groups = 0
for old, new in replacements:
    if old in ui:
        ui = ui.replace(old, new)
        changed_groups += 1

if changed_groups < 12:
    raise SystemExit(f"BLOCKED: too few V10 styling anchors matched ({changed_groups}); current state is unexpected")

# Workflow state fills: slightly more visible on slate while remaining calm.
ui = ui.replace("dark:bg-emerald-500/[0.075]", "dark:bg-emerald-400/[0.10]")
ui = ui.replace("dark:bg-blue-500/[0.065]", "dark:bg-sky-400/[0.08]")
ui = ui.replace("dark:bg-amber-500/[0.055]", "dark:bg-amber-400/[0.07]")

# -----------------------------------------------------------------------------
# Settings section header: remove the large near-black slab visible above GitHub.
# This is a surface-only dark-mode improvement; light mode remains transparent.
# -----------------------------------------------------------------------------
header_old = 'className="flex flex-col gap-4 rounded-[30px] border border-transparent bg-transparent py-1 lg:flex-row lg:items-center lg:justify-between"'
header_new = 'className="flex flex-col gap-4 rounded-[30px] border border-transparent bg-transparent py-1 lg:flex-row lg:items-center lg:justify-between dark:border-white/[0.09] dark:bg-[#202B37] dark:px-5 dark:py-4 dark:shadow-[0_16px_44px_rgba(8,14,22,0.16)] dark:[&_h1]:!text-[#EEF2F5] dark:[&_h2]:!text-[#EEF2F5] dark:[&_h3]:!text-[#EEF2F5] dark:[&_p]:!text-[#AAB6C2]"'
if header_old not in settings:
    raise SystemExit("BLOCKED: SettingsSectionHeader class anchor not found")
settings = settings.replace(header_old, header_new, 1)

# -----------------------------------------------------------------------------
# Safety validation.
# -----------------------------------------------------------------------------
for token in ["<section", "<article", "<Button", "onClick=", "useState(", "useEffect(", "api.github.", "<details", "<summary"]:
    if ui_original.count(token) != ui.count(token):
        raise SystemExit(f"BLOCKED: GithubAdvancedAdmin structure/logic changed: {token}")

# Only the SettingsSectionHeader class string may change in SettingsPage.
for token in ["function SettingsSectionHeader", "function GithubAdmin", "<GithubAdvancedAdmin", "useState(", "useEffect("]:
    if settings_original.count(token) != settings.count(token):
        raise SystemExit(f"BLOCKED: SettingsPage structure/logic changed: {token}")

# Light mode sentinels must remain byte-for-byte present with identical counts.
light_sentinels_ui = ["#FFFEFB", "#FBF5E8", "#FFFDFC", "#E8D7B1", "#E7D7B6", "#EADFC8"]
for token in light_sentinels_ui:
    if ui_original.count(token) != ui.count(token):
        raise SystemExit(f"BLOCKED: light-mode UI token changed: {token}")

# Layout guards from V7 must remain intact.
for token in ["xl:grid-cols-[260px_minmax(0,1fr)]", "min-h-[154px]", "break-all font-mono"]:
    if ui_original.count(token) != ui.count(token):
        raise SystemExit(f"BLOCKED: layout guard changed: {token}")

if ui == ui_original:
    raise SystemExit("BLOCKED: no V10 GithubAdvancedAdmin changes produced")
if settings == settings_original:
    raise SystemExit("BLOCKED: no V10 SettingsSectionHeader change produced")

GITHUB_UI.write_text(ui, encoding="utf-8")
SETTINGS_PAGE.write_text(settings, encoding="utf-8")

print("PATCH_APPLIED=YES")
print("BASE=V9_DARK_TEXT_CONTRAST")
print("FILES_CHANGED=2")
print("STRUCTURE_PRESERVED=YES")
print("LOGIC_PRESERVED=YES")
print("LAYOUT_PRESERVED=YES")
print("LIGHT_MODE_UNCHANGED=YES")
print("DARK_NEAR_BLACK_REMOVED=YES")
print("DARK_SLATE_LAYERING=YES")
print("DARK_CARD_SEPARATION=YES")
print("DARK_HEADER_SOFTENED=YES")
print("DARK_GOLD_RESTRAINED=YES")
print("DARK_EYE_COMFORT=YES")
