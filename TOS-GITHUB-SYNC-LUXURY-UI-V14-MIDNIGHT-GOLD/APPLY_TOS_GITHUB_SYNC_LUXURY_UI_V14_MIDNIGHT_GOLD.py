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

# V14 is intentionally resilient to the server-side custom V13 correction.
# It only requires the stable premium structure and V7 layout guards.
required = [
    'id="github-overview"',
    'id="github-workflow"',
    'id="github-changes"',
    'id="github-connection"',
    'id="github-console"',
    'min-h-[154px]',
    'break-all font-mono',
]
for anchor in required:
    if anchor not in ui:
        raise SystemExit(f"BLOCKED: required GitHub UI anchor missing: {anchor}")

if "LUXURY_MIDNIGHT_V14" in ui:
    print("PATCH_APPLIED=ALREADY")
    print("STRUCTURE_PRESERVED=YES")
    print("LOGIC_PRESERVED=YES")
    raise SystemExit(0)

# Locate only the premium branch; do not touch the fallback/backend-mismatch UI.
start_marker = '  if (!backendVersionMismatch) {\n    return ('
end_marker = '\n  return (\n    <div className="space-y-5">'
start = ui.find(start_marker)
end = ui.find(end_marker, start + 1)
if start < 0 or end < 0:
    raise SystemExit("BLOCKED: premium GitHub UI branch not found")
segment = ui[start:end]

# Add one harmless scope class to the premium root.
root_match = re.search(r'<div className="([^"]*grid[^\"]*min-w-0[^\"]*gap-6[^\"]*)">', segment)
if not root_match:
    raise SystemExit("BLOCKED: premium root grid not found")
root_tag = root_match.group(0)
root_classes = root_match.group(1)
if "LUXURY_MIDNIGHT_V14" not in root_classes:
    new_root_tag = root_tag.replace('className="', 'className="LUXURY_MIDNIGHT_V14 ', 1)
    segment = segment[:root_match.start()] + new_root_tag + segment[root_match.end():]

# Scoped visual system. This deliberately overrides accumulated V8-V13 utility colors
# without deleting them, so Light Mode and all handlers/logic stay intact.
style_block = r'''        <style>{`
          .dark .tos-page:has(.LUXURY_MIDNIGHT_V14) {
            background:
              radial-gradient(circle at 7% 74%, rgba(211,157,51,.085), transparent 24%),
              radial-gradient(circle at 82% 3%, rgba(28,83,128,.13), transparent 28%),
              linear-gradient(145deg,#040A11 0%,#07111B 48%,#050B12 100%) !important;
            border: 1px solid rgba(121,151,178,.10);
            box-shadow: inset 0 1px 0 rgba(255,255,255,.025), 0 32px 100px rgba(0,0,0,.28);
          }

          .dark .GITHUB_HEADER_V14 {
            padding: 10px 14px !important;
            border-radius: 22px !important;
            background: linear-gradient(135deg,rgba(7,17,27,.88),rgba(9,23,37,.82)) !important;
            border-color: rgba(198,151,59,.22) !important;
            box-shadow: 0 14px 40px rgba(0,0,0,.20) !important;
          }
          .dark .GITHUB_HEADER_V14 h1 { color:#F5F7FA !important; font-size:1.55rem !important; letter-spacing:-.025em !important; }
          .dark .GITHUB_HEADER_V14 p { color:#91A2B4 !important; }
          .dark .GITHUB_HEADER_V14 > div > div:first-child {
            color:#E6B955 !important;
            background:rgba(202,151,49,.10) !important;
            border-color:rgba(211,163,63,.24) !important;
          }

          .dark .LUXURY_MIDNIGHT_V14 {
            color:#E9EEF4 !important;
            position:relative;
            isolation:isolate;
          }
          .dark .LUXURY_MIDNIGHT_V14::before {
            content:"";
            position:absolute;
            inset:-10px;
            pointer-events:none;
            z-index:-1;
            background:radial-gradient(circle at 0% 82%,rgba(210,157,50,.06),transparent 25%);
          }

          .dark .LUXURY_MIDNIGHT_V14 > aside {
            position:relative;
            overflow:hidden;
            background:linear-gradient(180deg,#07111C 0%,#091624 48%,#08131F 100%) !important;
            border:1px solid rgba(101,137,168,.19) !important;
            box-shadow:0 24px 60px rgba(0,0,0,.28), inset 0 1px 0 rgba(255,255,255,.035) !important;
          }
          .dark .LUXURY_MIDNIGHT_V14 > aside::after {
            content:"";
            position:absolute;
            left:-85px;
            bottom:-65px;
            width:260px;
            height:260px;
            border-radius:50%;
            pointer-events:none;
            background:repeating-radial-gradient(circle,transparent 0 20px,rgba(213,158,48,.07) 21px 22px);
            filter:drop-shadow(0 0 10px rgba(226,171,54,.16));
            opacity:.72;
          }
          .dark .LUXURY_MIDNIGHT_V14 > aside nav a,
          .dark .LUXURY_MIDNIGHT_V14 > aside nav button {
            color:#B9C5D0 !important;
            border-color:transparent !important;
            background:transparent !important;
          }
          .dark .LUXURY_MIDNIGHT_V14 > aside nav a:hover,
          .dark .LUXURY_MIDNIGHT_V14 > aside nav button:hover {
            color:#F3F6F9 !important;
            background:rgba(255,255,255,.035) !important;
            border-color:rgba(104,139,170,.18) !important;
          }
          .dark .LUXURY_MIDNIGHT_V14 > aside nav > *:first-child {
            color:#F5D27D !important;
            background:linear-gradient(90deg,rgba(195,139,34,.17),rgba(255,255,255,.025)) !important;
            border-color:rgba(214,165,66,.34) !important;
            box-shadow:inset 3px 0 0 #D5A743, 0 8px 24px rgba(0,0,0,.14) !important;
          }

          .dark .LUXURY_MIDNIGHT_V14 #github-overview {
            position:relative;
            overflow:hidden;
            background:
              radial-gradient(circle at 63% 88%,rgba(225,166,50,.13),transparent 18%),
              radial-gradient(circle at 84% 0%,rgba(44,96,143,.18),transparent 34%),
              linear-gradient(135deg,#081522 0%,#0B1B2C 52%,#08131F 100%) !important;
            border:1px solid rgba(202,151,54,.38) !important;
            box-shadow:0 28px 70px rgba(0,0,0,.32), inset 0 1px 0 rgba(255,255,255,.045) !important;
          }
          .dark .LUXURY_MIDNIGHT_V14 #github-overview::before {
            content:"";
            position:absolute;
            width:580px;
            height:170px;
            right:9%;
            top:32%;
            border-radius:50%;
            border-bottom:1px solid rgba(225,169,53,.58);
            transform:rotate(-4deg);
            filter:drop-shadow(0 2px 5px rgba(229,169,47,.30));
            pointer-events:none;
          }
          .dark .LUXURY_MIDNIGHT_V14 #github-overview::after {
            content:"";
            position:absolute;
            width:132px;
            height:132px;
            right:28%;
            top:18px;
            border-radius:50%;
            border:1px solid rgba(207,161,71,.28);
            background:radial-gradient(circle,rgba(255,255,255,.055),rgba(12,27,43,.16) 48%,rgba(7,17,28,.04) 70%);
            box-shadow:0 0 42px rgba(212,157,49,.08), inset 0 0 38px rgba(255,255,255,.025);
            pointer-events:none;
          }
          .dark .LUXURY_MIDNIGHT_V14 #github-overview h1,
          .dark .LUXURY_MIDNIGHT_V14 #github-overview h2,
          .dark .LUXURY_MIDNIGHT_V14 #github-overview h3 { color:#F6F7F9 !important; }

          .dark .LUXURY_MIDNIGHT_V14 article,
          .dark .LUXURY_MIDNIGHT_V14 section:not(#github-overview) {
            background:linear-gradient(180deg,#091827 0%,#081522 100%) !important;
            border-color:rgba(91,129,163,.20) !important;
            box-shadow:0 18px 46px rgba(0,0,0,.22), inset 0 1px 0 rgba(255,255,255,.028) !important;
          }
          .dark .LUXURY_MIDNIGHT_V14 article:hover {
            border-color:rgba(201,153,61,.32) !important;
            box-shadow:0 22px 54px rgba(0,0,0,.28), 0 0 0 1px rgba(211,161,63,.05) !important;
          }

          .dark .LUXURY_MIDNIGHT_V14 article [class*="rounded-2xl"],
          .dark .LUXURY_MIDNIGHT_V14 article [class*="rounded-xl"],
          .dark .LUXURY_MIDNIGHT_V14 #github-workflow [class*="rounded-[24px]"] {
            background:#0C1C2B !important;
            border-color:rgba(100,137,168,.19) !important;
            color:#DDE5ED !important;
          }
          .dark .LUXURY_MIDNIGHT_V14 article [class*="rounded-2xl"]:hover,
          .dark .LUXURY_MIDNIGHT_V14 article [class*="rounded-xl"]:hover {
            background:#0E2132 !important;
            border-color:rgba(201,153,61,.25) !important;
          }

          .dark .LUXURY_MIDNIGHT_V14 #github-workflow {
            background:linear-gradient(180deg,#081622 0%,#07131E 100%) !important;
            border:1px solid rgba(210,160,58,.22) !important;
          }
          .dark .LUXURY_MIDNIGHT_V14 #github-workflow [class*="min-h-[154px]"] {
            background:linear-gradient(180deg,#0D1C2A 0%,#0B1825 100%) !important;
            border-color:rgba(104,140,169,.20) !important;
            box-shadow:inset 0 1px 0 rgba(255,255,255,.025), 0 12px 28px rgba(0,0,0,.16) !important;
          }
          .dark .LUXURY_MIDNIGHT_V14 #github-workflow [class*="min-h-[154px]"]:first-child {
            background:linear-gradient(180deg,#0A282B 0%,#092125 100%) !important;
            border-color:rgba(24,199,157,.40) !important;
            box-shadow:0 0 0 1px rgba(20,202,157,.05), inset 0 1px 0 rgba(255,255,255,.025) !important;
          }
          .dark .LUXURY_MIDNIGHT_V14 #github-workflow button {
            background:#07111B !important;
            color:#EAF0F5 !important;
            border-color:rgba(103,139,169,.18) !important;
            box-shadow:inset 0 1px 0 rgba(255,255,255,.025) !important;
          }
          .dark .LUXURY_MIDNIGHT_V14 #github-workflow button:hover {
            border-color:rgba(210,160,59,.35) !important;
            background:#0A1723 !important;
          }
          .dark .LUXURY_MIDNIGHT_V14 #github-workflow [class*="min-h-[154px]"]:nth-child(3) button {
            background:linear-gradient(135deg,#B5791C 0%,#D5A743 48%,#E7C36C 100%) !important;
            color:#181108 !important;
            border-color:rgba(240,201,113,.56) !important;
            box-shadow:0 8px 24px rgba(207,151,45,.22), inset 0 1px 0 rgba(255,245,207,.45) !important;
          }

          .dark .LUXURY_MIDNIGHT_V14 #github-changes [class*="rounded-xl"] {
            background:#0B1B2A !important;
            border-color:rgba(95,132,163,.16) !important;
          }
          .dark .LUXURY_MIDNIGHT_V14 #github-changes [class*="rounded-xl"]:hover {
            background:#0E2233 !important;
          }

          .dark .LUXURY_MIDNIGHT_V14 h1,
          .dark .LUXURY_MIDNIGHT_V14 h2,
          .dark .LUXURY_MIDNIGHT_V14 h3,
          .dark .LUXURY_MIDNIGHT_V14 h4 { color:#F1F4F7 !important; }
          .dark .LUXURY_MIDNIGHT_V14 [class*="text-zinc-950"],
          .dark .LUXURY_MIDNIGHT_V14 [class*="text-zinc-900"],
          .dark .LUXURY_MIDNIGHT_V14 [class*="text-zinc-800"] { color:#E9EEF4 !important; }
          .dark .LUXURY_MIDNIGHT_V14 [class*="text-zinc-700"],
          .dark .LUXURY_MIDNIGHT_V14 [class*="text-zinc-600"] { color:#C7D1DB !important; }
          .dark .LUXURY_MIDNIGHT_V14 [class*="text-zinc-500"] { color:#9EADBC !important; }
          .dark .LUXURY_MIDNIGHT_V14 [class*="text-zinc-400"] { color:#8798A9 !important; }

          .dark .LUXURY_MIDNIGHT_V14 [class*="emerald"] { --v14-status:#18C89C; }
          .dark .LUXURY_MIDNIGHT_V14 [class*="text-emerald"] { color:#32D8AE !important; }
          .dark .LUXURY_MIDNIGHT_V14 [class*="bg-emerald"] { background-color:rgba(24,200,156,.10) !important; }
          .dark .LUXURY_MIDNIGHT_V14 [class*="border-emerald"] { border-color:rgba(24,200,156,.28) !important; }

          .dark .LUXURY_MIDNIGHT_V14 [class*="amber"],
          .dark .LUXURY_MIDNIGHT_V14 [class*="text-[#D"],
          .dark .LUXURY_MIDNIGHT_V14 [class*="text-[#E"] { color:#E4B958 !important; }

          .dark .LUXURY_MIDNIGHT_V14 #github-connection,
          .dark .LUXURY_MIDNIGHT_V14 #github-console {
            background:linear-gradient(180deg,#091827,#081521) !important;
            border-color:rgba(100,137,168,.19) !important;
          }

          .dark .LUXURY_MIDNIGHT_V14 button {
            border-radius:12px !important;
            transition:transform .16s ease, border-color .16s ease, background .16s ease, box-shadow .16s ease !important;
          }
          .dark .LUXURY_MIDNIGHT_V14 button:hover { transform:translateY(-1px); }
          .dark .LUXURY_MIDNIGHT_V14 button:active { transform:translateY(0); }
        `}</style>'''

# Insert the style block immediately inside the premium root.
root_pos = segment.find('LUXURY_MIDNIGHT_V14')
root_open_end = segment.find('>', root_pos)
if root_pos < 0 or root_open_end < 0:
    raise SystemExit("BLOCKED: could not locate V14 premium root after marking")
segment = segment[:root_open_end + 1] + "\n" + style_block + segment[root_open_end + 1:]
ui = ui[:start] + segment + ui[end:]

# Mark only the GitHub SettingsSectionHeader so the scoped CSS can compact/style it.
fn_start = settings.find("function SettingsSectionHeader({ section })")
fn_end = settings.find("\nfunction ", fn_start + 10)
if fn_start < 0:
    raise SystemExit("BLOCKED: SettingsSectionHeader function not found")
if fn_end < 0:
    fn_end = len(settings)
header_scope = settings[fn_start:fn_end]
header_match = re.search(r'<header className="([^"]*)">', header_scope)
if not header_match:
    # Accept a prior template-literal className variant if present.
    header_match_template = re.search(r'<header className=\{`([^`]*)`\}>', header_scope)
    if not header_match_template:
        raise SystemExit("BLOCKED: SettingsSectionHeader className not found")
    if "GITHUB_HEADER_V14" not in header_match_template.group(1):
        old = header_match_template.group(0)
        inner = header_match_template.group(1)
        new = '<header className={`' + inner + ' ${section?.key === "github" ? "GITHUB_HEADER_V14" : ""}`}> '
        header_scope = header_scope.replace(old, new, 1)
else:
    old = header_match.group(0)
    base_classes = header_match.group(1)
    new = '<header className={`' + base_classes + ' ${section?.key === "github" ? "GITHUB_HEADER_V14" : ""}`}> '
    header_scope = header_scope.replace(old, new, 1)
settings = settings[:fn_start] + header_scope + settings[fn_end:]

# Safety validation: logic and interactive structure must stay intact.
for token in ["<section", "<article", "<Button", "onClick=", "useState(", "useEffect(", "api.github.", "<details", "<summary"]:
    if ui_original.count(token) != ui.count(token):
        raise SystemExit(f"BLOCKED: GithubAdvancedAdmin structure/logic changed: {token}")

for token in ["function SettingsSectionHeader", "function GithubAdmin", "<GithubAdvancedAdmin", "useState(", "useEffect("]:
    if settings_original.count(token) != settings.count(token):
        raise SystemExit(f"BLOCKED: SettingsPage structure/logic changed: {token}")

# V7 layout and overflow protections must remain present.
for token in ["min-h-[154px]", "break-all font-mono"]:
    if ui_original.count(token) != ui.count(token):
        raise SystemExit(f"BLOCKED: layout guard changed: {token}")

# Light palette remains byte-for-byte untouched by the patch.
for token in ["#FFFEFB", "#FBF5E8", "#FFFDFC", "#E8D7B1", "#E7D7B6", "#EADFC8"]:
    if ui_original.count(token) != ui.count(token):
        raise SystemExit(f"BLOCKED: light-mode token changed: {token}")

if ui == ui_original:
    raise SystemExit("BLOCKED: no V14 GitHub UI changes produced")
if settings == settings_original:
    raise SystemExit("BLOCKED: no V14 Settings header changes produced")

GITHUB_UI.write_text(ui, encoding="utf-8")
SETTINGS_PAGE.write_text(settings, encoding="utf-8")

print("PATCH_APPLIED=YES")
print("BASE=V13_INTEGRATED_DARK")
print("FILES_CHANGED=2")
print("STRUCTURE_PRESERVED=YES")
print("LOGIC_PRESERVED=YES")
print("LIGHT_MODE_UNCHANGED=YES")
print("DESIGN_SYSTEM=MIDNIGHT_NAVY_GOLD")
print("SIDEBAR_LUXURY=YES")
print("HERO_ORBIT_GLOW=YES")
print("CARD_DEPTH_PREMIUM=YES")
print("WORKFLOW_PREMIUM=YES")
print("CHAMPAGNE_GOLD_RESTRAINED=YES")
print("TEAL_STATUS_SYSTEM=YES")
print("ACTIVITY_READABILITY=YES")
print("TOP_HEADER_COMPACT=YES")
