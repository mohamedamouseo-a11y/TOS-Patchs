#!/usr/bin/env python3
from pathlib import Path

UI = Path('frontend/src/components/GithubAdvancedAdmin.jsx')
CSS = Path('frontend/src/index.css')
for p in (UI, CSS):
    if not p.exists():
        raise SystemExit(f'BLOCKED: target not found: {p}')

ui = UI.read_text(encoding='utf-8')
css = CSS.read_text(encoding='utf-8')
css0 = css

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
        raise SystemExit(f'BLOCKED: required DOM anchor missing: {token}')

# Remove the prior V15 CSS block if present so it cannot compete with V16.
for start_marker, end_marker in [
    ('/* TOS_GITHUB_LUXURY_V15_START */', '/* TOS_GITHUB_LUXURY_V15_END */'),
    ('/* TOS_GITHUB_LUXURY_V16_START */', '/* TOS_GITHUB_LUXURY_V16_END */'),
]:
    if start_marker in css:
        a = css.find(start_marker)
        b = css.find(end_marker, a)
        if b < 0:
            raise SystemExit(f'BLOCKED: malformed CSS block: {start_marker}')
        css = css[:a] + css[b + len(end_marker):]

v16 = r'''
/* TOS_GITHUB_LUXURY_V16_START */
/* Direct-ID visual contract: no JSX root-class dependency. */

html.dark body:has(#github-overview) {
  background: #02070D !important;
}

html.dark .tos-page:has(#github-overview) {
  background:
    radial-gradient(circle at 4% 78%, rgba(214,157,40,.10), transparent 24%),
    radial-gradient(circle at 92% 5%, rgba(32,78,125,.18), transparent 30%),
    linear-gradient(145deg,#02070D 0%,#050D16 42%,#07111B 72%,#03080E 100%) !important;
  border:1px solid rgba(95,125,151,.12) !important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.025),0 34px 100px rgba(0,0,0,.34) !important;
}

/* Compact top Settings/GitHub header */
html.dark .tos-page:has(#github-overview) > header {
  min-height:76px !important;
  padding:12px 18px !important;
  border-radius:24px !important;
  background:radial-gradient(circle at 95% -30%,rgba(206,155,51,.11),transparent 32%),linear-gradient(135deg,#06111C 0%,#091827 100%) !important;
  border:1px solid rgba(202,151,54,.26) !important;
  box-shadow:0 16px 40px rgba(0,0,0,.26),inset 0 1px 0 rgba(255,255,255,.03) !important;
}
html.dark .tos-page:has(#github-overview) > header h1 { color:#F7F8FA !important; font-size:1.5rem !important; line-height:1.1 !important; letter-spacing:-.03em !important; }
html.dark .tos-page:has(#github-overview) > header p { color:#94A5B5 !important; }
html.dark .tos-page:has(#github-overview) > header > div > div:first-child { color:#E2B650 !important; background:rgba(207,154,42,.10) !important; border-color:rgba(211,161,55,.25) !important; }

/* Premium inner sidebar */
html.dark .tos-page:has(#github-overview) main aside {
  position:relative !important;
  overflow:hidden !important;
  background:radial-gradient(circle at 20% 10%,rgba(213,158,43,.08),transparent 28%),linear-gradient(180deg,#06101A 0%,#071521 50%,#06111B 100%) !important;
  border:1px solid rgba(116,145,170,.20) !important;
  box-shadow:0 26px 66px rgba(0,0,0,.32),inset 0 1px 0 rgba(255,255,255,.035) !important;
}
html.dark .tos-page:has(#github-overview) main aside::after {
  content:''; position:absolute; left:-118px; bottom:-112px; width:330px; height:330px; border-radius:50%; pointer-events:none;
  background:repeating-radial-gradient(circle,transparent 0 23px,rgba(222,164,42,.07) 24px 25px);
  filter:drop-shadow(0 0 10px rgba(222,164,42,.15)); opacity:.75;
}
html.dark .tos-page:has(#github-overview) main aside > div:first-child {
  background:linear-gradient(135deg,rgba(210,158,48,.12),rgba(255,255,255,.025)) !important;
  border-color:rgba(218,171,73,.30) !important;
}
html.dark .tos-page:has(#github-overview) main aside nav a { color:#AEBBC7 !important; background:transparent !important; border-color:transparent !important; }
html.dark .tos-page:has(#github-overview) main aside nav a:first-child {
  color:#F4D27F !important;
  background:linear-gradient(90deg,rgba(204,149,38,.18),rgba(14,27,40,.50)) !important;
  border-color:rgba(221,171,67,.34) !important;
  box-shadow:inset 3px 0 0 #D4A640,0 9px 26px rgba(0,0,0,.18) !important;
}

/* Hero */
html.dark #github-overview {
  position:relative !important; overflow:hidden !important; min-height:190px !important;
  background:radial-gradient(circle at 77% 46%,rgba(226,170,52,.13),transparent 17%),radial-gradient(circle at 89% -15%,rgba(47,97,143,.20),transparent 34%),linear-gradient(135deg,#071522 0%,#0A1B2C 50%,#07131F 100%) !important;
  border:1px solid rgba(207,157,57,.42) !important;
  box-shadow:0 30px 78px rgba(0,0,0,.34),inset 0 1px 0 rgba(255,255,255,.045) !important;
}
html.dark #github-overview::before {
  content:''; position:absolute; width:620px; height:180px; right:7%; top:35%; border-radius:50%;
  border-bottom:1px solid rgba(235,177,57,.70); transform:rotate(-4deg); filter:drop-shadow(0 2px 7px rgba(229,169,47,.38)); pointer-events:none; opacity:.92;
}
html.dark #github-overview::after {
  content:''; position:absolute; width:142px; height:142px; right:27%; top:20px; border-radius:50%;
  border:1px solid rgba(212,166,74,.30); background:radial-gradient(circle,rgba(255,255,255,.06),rgba(11,27,44,.18) 45%,rgba(4,11,18,.04) 70%);
  box-shadow:0 0 54px rgba(214,160,49,.10),inset 0 0 42px rgba(255,255,255,.025); pointer-events:none;
}
html.dark #github-overview h1, html.dark #github-overview h2, html.dark #github-overview h3 { color:#F7F8FA !important; }
html.dark #github-overview p { color:#BBC7D3 !important; }

/* All cards/sections on the GitHub page */
html.dark .tos-page:has(#github-overview) article,
html.dark #github-workflow,
html.dark #github-changes,
html.dark #github-connection,
html.dark #github-console {
  background:linear-gradient(180deg,#091827 0%,#071522 100%) !important;
  border-color:rgba(91,129,163,.20) !important;
  box-shadow:0 18px 46px rgba(0,0,0,.22),inset 0 1px 0 rgba(255,255,255,.028) !important;
}

/* Remove every white / pale gray island in dark mode on this page. */
html.dark .tos-page:has(#github-overview) [class*='bg-white'],
html.dark .tos-page:has(#github-overview) [class*='bg-zinc-50'],
html.dark .tos-page:has(#github-overview) [class*='bg-zinc-100'],
html.dark .tos-page:has(#github-overview) [class*='bg-gray-50'],
html.dark .tos-page:has(#github-overview) [class*='bg-gray-100'],
html.dark .tos-page:has(#github-overview) [class*='bg-slate-50'],
html.dark .tos-page:has(#github-overview) [class*='bg-slate-100'] {
  background:#0B1B2A !important;
}

html.dark .tos-page:has(#github-overview) article [class*='rounded-2xl'],
html.dark .tos-page:has(#github-overview) article [class*='rounded-xl'] {
  background:#0B1B2A !important; border-color:rgba(100,136,166,.18) !important; color:#DDE6EE !important;
}

/* Workflow */
html.dark #github-workflow { border:1px solid rgba(211,160,56,.24) !important; }
html.dark #github-workflow [class*='min-h-[154px]'] {
  background:linear-gradient(180deg,#0C1B29 0%,#091724 100%) !important;
  border-color:rgba(102,139,169,.21) !important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.028),0 13px 30px rgba(0,0,0,.18) !important;
}
html.dark #github-workflow [class*='min-h-[154px]']:first-child {
  background:linear-gradient(180deg,#082A2C 0%,#072126 100%) !important;
  border-color:rgba(24,200,156,.42) !important;
}
html.dark #github-workflow button { background:#050D16 !important; color:#EDF2F6 !important; border-color:rgba(103,139,169,.20) !important; }
html.dark #github-workflow [class*='min-h-[154px]']:nth-child(3) button {
  background:linear-gradient(135deg,#A96E16 0%,#D1A13A 50%,#E5C26D 100%) !important;
  color:#161006 !important; border-color:rgba(239,199,111,.56) !important;
  box-shadow:0 8px 24px rgba(207,151,45,.22),inset 0 1px 0 rgba(255,245,207,.45) !important;
}

/* Changes + activity + repository tiles */
html.dark #github-changes [class*='rounded-xl'],
html.dark .tos-page:has(#github-overview) article [class*='overflow-hidden'][class*='rounded-2xl'] {
  background:#0A1A29 !important; border-color:rgba(95,132,163,.16) !important;
}

/* Typography hierarchy */
html.dark .tos-page:has(#github-overview) h1,
html.dark .tos-page:has(#github-overview) h2,
html.dark .tos-page:has(#github-overview) h3,
html.dark .tos-page:has(#github-overview) h4 { color:#F3F6F9 !important; }
html.dark .tos-page:has(#github-overview) [class*='text-zinc-950'],
html.dark .tos-page:has(#github-overview) [class*='text-zinc-900'],
html.dark .tos-page:has(#github-overview) [class*='text-zinc-800'] { color:#E9EEF4 !important; }
html.dark .tos-page:has(#github-overview) [class*='text-zinc-700'],
html.dark .tos-page:has(#github-overview) [class*='text-zinc-600'] { color:#C7D1DB !important; }
html.dark .tos-page:has(#github-overview) [class*='text-zinc-500'] { color:#9EADBC !important; }
html.dark .tos-page:has(#github-overview) [class*='text-zinc-400'] { color:#8798A9 !important; }

/* Teal status and restrained gold. */
html.dark .tos-page:has(#github-overview) [class*='text-emerald'] { color:#32D8AE !important; }
html.dark .tos-page:has(#github-overview) [class*='bg-emerald'] { background-color:rgba(24,200,156,.10) !important; }
html.dark .tos-page:has(#github-overview) [class*='border-emerald'] { border-color:rgba(24,200,156,.28) !important; }
html.dark .tos-page:has(#github-overview) [class*='text-amber'] { color:#E4B958 !important; }

/* TOS_GITHUB_LUXURY_V16_END */
'''

css = css.rstrip() + '\n\n' + v16.strip() + '\n'

if css == css0:
    raise SystemExit('BLOCKED: no CSS changes produced')

# Safety: JSX stays byte-identical; this patch is CSS-only.
if UI.read_text(encoding='utf-8') != ui:
    raise SystemExit('BLOCKED: UI changed unexpectedly')

CSS.write_text(css, encoding='utf-8')

print('PATCH_APPLIED=YES')
print('FILES_CHANGED=1')
print('PATCH_MODE=CSS_ONLY_DIRECT_ID')
print('JSX_UNCHANGED=YES')
print('LOGIC_UNCHANGED=YES')
print('LIGHT_MODE_UNCHANGED=YES')
print('ROOT_CLASS_DEPENDENCY=NO')
print('DIRECT_DOM_IDS=YES')
print('THEME_SELECTOR=html.dark')
print('MIDNIGHT_NAVY=YES')
print('CHAMPAGNE_GOLD=YES')
print('TEAL_STATUS=YES')
print('WHITE_INNER_PANELS_REMOVED=YES')
print('HERO_ORBIT=YES')
print('WORKFLOW_PREMIUM=YES')
