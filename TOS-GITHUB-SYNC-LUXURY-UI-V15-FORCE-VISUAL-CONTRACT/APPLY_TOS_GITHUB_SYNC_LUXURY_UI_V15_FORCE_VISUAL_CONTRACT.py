#!/usr/bin/env python3
from pathlib import Path
import re

UI = Path("frontend/src/components/GithubAdvancedAdmin.jsx")
SETTINGS = Path("frontend/src/pages/SettingsPage.jsx")
CSS = Path("frontend/src/index.css")

for p in (UI, SETTINGS, CSS):
    if not p.exists():
        raise SystemExit(f"BLOCKED: target not found: {p}")

ui = UI.read_text(encoding="utf-8")
settings = SETTINGS.read_text(encoding="utf-8")
css = CSS.read_text(encoding="utf-8")
ui0, settings0, css0 = ui, settings, css

# Stable structure contract only. V15 may run on the local V12/V14 visual state.
required = [
    'id="github-overview"',
    'id="github-workflow"',
    'id="github-changes"',
    'id="github-connection"',
    'id="github-console"',
    'min-h-[154px]',
    'break-all font-mono',
]
for token in required:
    if token not in ui:
        raise SystemExit(f"BLOCKED: required GitHub UI anchor missing: {token}")

if "GITHUB_LUXURY_V15" in ui and "TOS_GITHUB_LUXURY_V15_START" in css:
    print("PATCH_APPLIED=ALREADY")
    print("STRUCTURE_PRESERVED=YES")
    print("LOGIC_PRESERVED=YES")
    raise SystemExit(0)

# -----------------------------------------------------------------------------
# 1) Add a stable visual scope class to the actual premium GitHub root.
# -----------------------------------------------------------------------------
if "LUXURY_MIDNIGHT_V14" in ui:
    ui = ui.replace("LUXURY_MIDNIGHT_V14", "LUXURY_MIDNIGHT_V14 GITHUB_LUXURY_V15", 1)
else:
    # Fallback to stable premium root signature.
    root = re.search(r'<div className="([^"]*grid[^\"]*min-w-0[^\"]*gap-6[^\"]*)">', ui)
    if not root:
        raise SystemExit("BLOCKED: premium GitHub root grid not found")
    tag = root.group(0)
    ui = ui[:root.start()] + tag.replace('className="', 'className="GITHUB_LUXURY_V15 ', 1) + ui[root.end():]

# -----------------------------------------------------------------------------
# 2) Add a stable scope class to GitHub SettingsSectionHeader.
# -----------------------------------------------------------------------------
fn_start = settings.find("function SettingsSectionHeader({ section })")
fn_end = settings.find("\nfunction ", fn_start + 10)
if fn_start < 0:
    raise SystemExit("BLOCKED: SettingsSectionHeader function not found")
if fn_end < 0:
    fn_end = len(settings)
header = settings[fn_start:fn_end]

if "GITHUB_HEADER_V15" not in header:
    if "GITHUB_HEADER_V14" in header:
        header = header.replace("GITHUB_HEADER_V14", "GITHUB_HEADER_V14 GITHUB_HEADER_V15")
    else:
        m = re.search(r'<header className="([^"]*)">', header)
        if not m:
            raise SystemExit("BLOCKED: SettingsSectionHeader className not found")
        base = m.group(1)
        replacement = '<header className={`' + base + ' ${section?.key === "github" ? "GITHUB_HEADER_V15" : ""}`}>'
        header = header[:m.start()] + replacement + header[m.end():]
settings = settings[:fn_start] + header + settings[fn_end:]

# -----------------------------------------------------------------------------
# 3) Append a real, high-specificity stylesheet after the existing design system.
#    This intentionally wins over accumulated Tailwind dark utilities and the
#    V14 in-component style tag. Light mode is untouched.
# -----------------------------------------------------------------------------
START = "/* TOS_GITHUB_LUXURY_V15_START */"
END = "/* TOS_GITHUB_LUXURY_V15_END */"
if START in css:
    a = css.find(START)
    b = css.find(END, a)
    if b < 0:
        raise SystemExit("BLOCKED: malformed existing V15 CSS block")
    css = css[:a] + css[b + len(END):]

v15 = r'''
/* TOS_GITHUB_LUXURY_V15_START */

/* APPROVED VISUAL CONTRACT: Midnight Navy + Champagne Gold + Emerald/Teal */
html.dark body .tos-page:has(.GITHUB_LUXURY_V15) {
  background:
    radial-gradient(circle at 4% 78%, rgba(215,157,40,.095), transparent 24%),
    radial-gradient(circle at 91% 4%, rgba(28,76,122,.17), transparent 30%),
    linear-gradient(145deg,#02070D 0%,#050D16 42%,#07111B 72%,#03080E 100%) !important;
  border: 1px solid rgba(93,124,151,.12) !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.025), 0 32px 96px rgba(0,0,0,.34) !important;
}

html.dark body .GITHUB_HEADER_V15 {
  min-height: 76px !important;
  padding: 12px 18px !important;
  border-radius: 24px !important;
  background:
    radial-gradient(circle at 95% -30%,rgba(206,155,51,.11),transparent 32%),
    linear-gradient(135deg,#06111C 0%,#091827 100%) !important;
  border: 1px solid rgba(202,151,54,.26) !important;
  box-shadow: 0 16px 40px rgba(0,0,0,.26), inset 0 1px 0 rgba(255,255,255,.03) !important;
}
html.dark body .GITHUB_HEADER_V15 h1 {
  color:#F7F8FA !important;
  font-size:1.5rem !important;
  line-height:1.1 !important;
  letter-spacing:-.03em !important;
}
html.dark body .GITHUB_HEADER_V15 p { color:#94A5B5 !important; }
html.dark body .GITHUB_HEADER_V15 > div > div:first-child {
  color:#E2B650 !important;
  background:rgba(207,154,42,.10) !important;
  border-color:rgba(211,161,55,.25) !important;
}

html.dark body .tos-page .GITHUB_LUXURY_V15 {
  color:#E9EEF4 !important;
  position:relative !important;
  isolation:isolate !important;
}

/* Premium sidebar */
html.dark body .tos-page .GITHUB_LUXURY_V15 > aside {
  position:relative !important;
  overflow:hidden !important;
  background:
    radial-gradient(circle at 20% 10%,rgba(213,158,43,.08),transparent 28%),
    linear-gradient(180deg,#06101A 0%,#071521 50%,#06111B 100%) !important;
  border:1px solid rgba(116,145,170,.20) !important;
  box-shadow:0 26px 66px rgba(0,0,0,.32), inset 0 1px 0 rgba(255,255,255,.035) !important;
}
html.dark body .tos-page .GITHUB_LUXURY_V15 > aside::after {
  content:"";
  position:absolute;
  left:-118px;
  bottom:-112px;
  width:330px;
  height:330px;
  border-radius:50%;
  pointer-events:none;
  background:repeating-radial-gradient(circle,transparent 0 23px,rgba(222,164,42,.07) 24px 25px);
  filter:drop-shadow(0 0 10px rgba(222,164,42,.15));
  opacity:.75;
}
html.dark body .tos-page .GITHUB_LUXURY_V15 > aside > div:first-child {
  background:linear-gradient(135deg,rgba(210,158,48,.12),rgba(255,255,255,.025)) !important;
  border-color:rgba(218,171,73,.30) !important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.03),0 12px 30px rgba(0,0,0,.18) !important;
}
html.dark body .tos-page .GITHUB_LUXURY_V15 > aside nav a,
html.dark body .tos-page .GITHUB_LUXURY_V15 > aside nav button {
  color:#AEBBC7 !important;
  background:transparent !important;
  border-color:transparent !important;
}
html.dark body .tos-page .GITHUB_LUXURY_V15 > aside nav > *:first-child {
  color:#F4D27F !important;
  background:linear-gradient(90deg,rgba(204,149,38,.18),rgba(14,27,40,.50)) !important;
  border-color:rgba(221,171,67,.34) !important;
  box-shadow:inset 3px 0 0 #D4A640,0 9px 26px rgba(0,0,0,.18) !important;
}
html.dark body .tos-page .GITHUB_LUXURY_V15 > aside nav a:hover,
html.dark body .tos-page .GITHUB_LUXURY_V15 > aside nav button:hover {
  color:#F4F7F9 !important;
  background:rgba(255,255,255,.038) !important;
  border-color:rgba(111,145,173,.18) !important;
}

/* Hero: approved orbital-gold visual */
html.dark body .tos-page .GITHUB_LUXURY_V15 #github-overview {
  position:relative !important;
  overflow:hidden !important;
  min-height:190px !important;
  background:
    radial-gradient(circle at 77% 46%,rgba(226,170,52,.13),transparent 17%),
    radial-gradient(circle at 89% -15%,rgba(47,97,143,.20),transparent 34%),
    linear-gradient(135deg,#071522 0%,#0A1B2C 50%,#07131F 100%) !important;
  border:1px solid rgba(207,157,57,.42) !important;
  box-shadow:0 30px 78px rgba(0,0,0,.34),inset 0 1px 0 rgba(255,255,255,.045) !important;
}
html.dark body .tos-page .GITHUB_LUXURY_V15 #github-overview::before {
  content:"";
  position:absolute;
  width:620px;
  height:180px;
  right:7%;
  top:35%;
  border-radius:50%;
  border-bottom:1px solid rgba(235,177,57,.70);
  transform:rotate(-4deg);
  filter:drop-shadow(0 2px 7px rgba(229,169,47,.38));
  pointer-events:none;
  opacity:.92;
}
html.dark body .tos-page .GITHUB_LUXURY_V15 #github-overview::after {
  content:"";
  position:absolute;
  width:142px;
  height:142px;
  right:27%;
  top:20px;
  border-radius:50%;
  border:1px solid rgba(212,166,74,.30);
  background:radial-gradient(circle,rgba(255,255,255,.06),rgba(11,27,44,.18) 45%,rgba(4,11,18,.04) 70%);
  box-shadow:0 0 54px rgba(214,160,49,.10),inset 0 0 42px rgba(255,255,255,.025);
  pointer-events:none;
}
html.dark body .tos-page .GITHUB_LUXURY_V15 #github-overview h1,
html.dark body .tos-page .GITHUB_LUXURY_V15 #github-overview h2,
html.dark body .tos-page .GITHUB_LUXURY_V15 #github-overview h3 { color:#F7F8FA !important; }
html.dark body .tos-page .GITHUB_LUXURY_V15 #github-overview p { color:#BBC7D3 !important; }

/* Primary cards / sections */
html.dark body .tos-page .GITHUB_LUXURY_V15 main > article,
html.dark body .tos-page .GITHUB_LUXURY_V15 main > section:not(#github-overview),
html.dark body .tos-page .GITHUB_LUXURY_V15 main > div > article {
  background:linear-gradient(180deg,#091827 0%,#071522 100%) !important;
  border-color:rgba(91,129,163,.20) !important;
  box-shadow:0 19px 50px rgba(0,0,0,.24),inset 0 1px 0 rgba(255,255,255,.028) !important;
}
html.dark body .tos-page .GITHUB_LUXURY_V15 article {
  background:linear-gradient(180deg,#091827 0%,#071522 100%) !important;
  border-color:rgba(91,129,163,.20) !important;
  box-shadow:0 18px 46px rgba(0,0,0,.22),inset 0 1px 0 rgba(255,255,255,.028) !important;
}
html.dark body .tos-page .GITHUB_LUXURY_V15 article:hover {
  border-color:rgba(208,158,60,.34) !important;
}

/* Kill all light/gray islands inside the approved dark design */
html.dark body .tos-page .GITHUB_LUXURY_V15 [class*="bg-white"],
html.dark body .tos-page .GITHUB_LUXURY_V15 [class*="bg-zinc-50"],
html.dark body .tos-page .GITHUB_LUXURY_V15 [class*="bg-zinc-100"] {
  background:#0B1B2A !important;
}
html.dark body .tos-page .GITHUB_LUXURY_V15 [class*="rounded-2xl"],
html.dark body .tos-page .GITHUB_LUXURY_V15 [class*="rounded-xl"] {
  border-color:rgba(100,136,166,.18) !important;
}

/* Top three status cards / nested panels */
html.dark body .tos-page .GITHUB_LUXURY_V15 article [class*="rounded-2xl"],
html.dark body .tos-page .GITHUB_LUXURY_V15 article [class*="rounded-xl"] {
  background:#0B1B2A !important;
  color:#DDE6EE !important;
}

/* Premium connected workflow */
html.dark body .tos-page .GITHUB_LUXURY_V15 #github-workflow {
  background:linear-gradient(180deg,#071522 0%,#06111B 100%) !important;
  border:1px solid rgba(211,160,56,.24) !important;
  box-shadow:0 18px 50px rgba(0,0,0,.23),inset 0 1px 0 rgba(255,255,255,.025) !important;
}
html.dark body .tos-page .GITHUB_LUXURY_V15 #github-workflow [class*="min-h-[154px]"] {
  background:linear-gradient(180deg,#0C1B29 0%,#091724 100%) !important;
  border-color:rgba(102,139,169,.21) !important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.028),0 13px 30px rgba(0,0,0,.18) !important;
}
html.dark body .tos-page .GITHUB_LUXURY_V15 #github-workflow [class*="min-h-[154px]"]:first-child {
  background:linear-gradient(180deg,#082A2C 0%,#072126 100%) !important;
  border-color:rgba(24,200,156,.42) !important;
}
html.dark body .tos-page .GITHUB_LUXURY_V15 #github-workflow button {
  background:#050D16 !important;
  color:#EDF2F6 !important;
  border-color:rgba(103,139,169,.20) !important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.025) !important;
}
html.dark body .tos-page .GITHUB_LUXURY_V15 #github-workflow [class*="min-h-[154px]"]:nth-child(3) button {
  background:linear-gradient(135deg,#A96E16 0%,#D3A33D 48%,#EAC96F 100%) !important;
  color:#171006 !important;
  border-color:rgba(240,202,114,.58) !important;
  box-shadow:0 9px 26px rgba(207,151,45,.25),inset 0 1px 0 rgba(255,247,213,.48) !important;
}

/* Changes + activity */
html.dark body .tos-page .GITHUB_LUXURY_V15 #github-changes [class*="rounded-xl"] {
  background:#0A1A29 !important;
  color:#E7EDF3 !important;
  border-color:rgba(97,134,165,.17) !important;
}
html.dark body .tos-page .GITHUB_LUXURY_V15 #github-changes [class*="rounded-xl"]:hover {
  background:#0C2031 !important;
}

/* Repository info + collapsible areas */
html.dark body .tos-page .GITHUB_LUXURY_V15 #github-connection,
html.dark body .tos-page .GITHUB_LUXURY_V15 #github-console {
  background:linear-gradient(180deg,#091827,#071522) !important;
  border-color:rgba(100,136,166,.20) !important;
}

/* Typography hierarchy */
html.dark body .tos-page .GITHUB_LUXURY_V15 h1,
html.dark body .tos-page .GITHUB_LUXURY_V15 h2,
html.dark body .tos-page .GITHUB_LUXURY_V15 h3,
html.dark body .tos-page .GITHUB_LUXURY_V15 h4 { color:#F3F6F9 !important; }
html.dark body .tos-page .GITHUB_LUXURY_V15 [class*="text-zinc-950"],
html.dark body .tos-page .GITHUB_LUXURY_V15 [class*="text-zinc-900"],
html.dark body .tos-page .GITHUB_LUXURY_V15 [class*="text-zinc-800"] { color:#E9EEF4 !important; }
html.dark body .tos-page .GITHUB_LUXURY_V15 [class*="text-zinc-700"],
html.dark body .tos-page .GITHUB_LUXURY_V15 [class*="text-zinc-600"] { color:#C6D1DB !important; }
html.dark body .tos-page .GITHUB_LUXURY_V15 [class*="text-zinc-500"] { color:#9EAEBD !important; }
html.dark body .tos-page .GITHUB_LUXURY_V15 [class*="text-zinc-400"] { color:#8799AA !important; }

/* Status system */
html.dark body .tos-page .GITHUB_LUXURY_V15 [class*="text-emerald"] { color:#34D9B0 !important; }
html.dark body .tos-page .GITHUB_LUXURY_V15 [class*="bg-emerald"] { background-color:rgba(24,200,156,.105) !important; }
html.dark body .tos-page .GITHUB_LUXURY_V15 [class*="border-emerald"] { border-color:rgba(24,200,156,.30) !important; }
html.dark body .tos-page .GITHUB_LUXURY_V15 [class*="text-amber"] { color:#E4B957 !important; }
html.dark body .tos-page .GITHUB_LUXURY_V15 [class*="border-amber"] { border-color:rgba(216,164,60,.28) !important; }

@media (max-width: 1024px) {
  html.dark body .tos-page .GITHUB_LUXURY_V15 #github-overview::before,
  html.dark body .tos-page .GITHUB_LUXURY_V15 #github-overview::after { opacity:.42; }
}

/* TOS_GITHUB_LUXURY_V15_END */
'''

css = css.rstrip() + "\n\n" + v15.strip() + "\n"

# -----------------------------------------------------------------------------
# Safety: no interactive/structural logic changed.
# -----------------------------------------------------------------------------
for token in ["<section", "<article", "<Button", "onClick=", "useState(", "useEffect(", "api.github.", "<details", "<summary"]:
    if ui0.count(token) != ui.count(token):
        raise SystemExit(f"BLOCKED: Github UI structure/logic changed: {token}")
for token in ["function SettingsSectionHeader", "function GithubAdmin", "<GithubAdvancedAdmin", "useState(", "useEffect("]:
    if settings0.count(token) != settings.count(token):
        raise SystemExit(f"BLOCKED: Settings structure/logic changed: {token}")
for token in ["xl:grid-cols-[260px_minmax(0,1fr)]", "min-h-[154px]", "break-all font-mono"]:
    if ui0.count(token) != ui.count(token):
        raise SystemExit(f"BLOCKED: V7 layout guard changed: {token}")

# The patch must produce all three file changes to guarantee the visual contract.
if ui == ui0:
    raise SystemExit("BLOCKED: root visual scope class was not added")
if settings == settings0:
    raise SystemExit("BLOCKED: GitHub header visual scope class was not added")
if css == css0:
    raise SystemExit("BLOCKED: V15 stylesheet was not produced")

UI.write_text(ui, encoding="utf-8")
SETTINGS.write_text(settings, encoding="utf-8")
CSS.write_text(css, encoding="utf-8")

print("PATCH_APPLIED=YES")
print("BASE=V14_OR_STABLE_PREMIUM_STRUCTURE")
print("FILES_CHANGED=3")
print("STRUCTURE_PRESERVED=YES")
print("LOGIC_PRESERVED=YES")
print("LAYOUT_PRESERVED=YES")
print("LIGHT_MODE_UNCHANGED=YES")
print("VISUAL_SCOPE=GITHUB_LUXURY_V15")
print("CSS_LOCATION=frontend/src/index.css")
print("CSS_SPECIFICITY_FORCED=YES")
print("MIDNIGHT_NAVY=YES")
print("CHAMPAGNE_GOLD=YES")
print("TEAL_STATUS=YES")
print("WHITE_INNER_PANELS_REMOVED=YES")
print("HERO_ORBIT=YES")
print("SIDEBAR_PREMIUM=YES")
print("WORKFLOW_PREMIUM=YES")
print("ACTIVITY_READABLE=YES")
print("TOP_HEADER_COMPACT=YES")
