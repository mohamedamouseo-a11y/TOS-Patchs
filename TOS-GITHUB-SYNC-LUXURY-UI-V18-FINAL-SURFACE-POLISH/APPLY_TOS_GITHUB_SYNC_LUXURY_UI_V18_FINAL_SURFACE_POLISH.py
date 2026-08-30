#!/usr/bin/env python3
from pathlib import Path

UI = Path('frontend/src/components/GithubAdvancedAdmin.jsx')
CSS = Path('frontend/src/index.css')
SIDEBAR = Path('frontend/src/components/layout/Sidebar.jsx')

for p in (UI, CSS, SIDEBAR):
    if not p.exists():
        raise SystemExit(f'BLOCKED: target not found: {p}')

ui = UI.read_text(encoding='utf-8')
css = CSS.read_text(encoding='utf-8')
sidebar = SIDEBAR.read_text(encoding='utf-8')
css0 = css

required_ui = [
    'id="github-overview"',
    'id="github-workflow"',
    'id="github-changes"',
    'id="github-connection"',
    'id="github-console"',
    'min-h-[154px]',
    'break-all font-mono',
]
for token in required_ui:
    if token not in ui:
        raise SystemExit(f'BLOCKED: required DOM anchor missing: {token}')

if 'tos-premium-sidebar' not in sidebar or 'tos-sidebar-scroll-region' not in sidebar:
    raise SystemExit('BLOCKED: global sidebar anchors not found')

if '/* TOS_GITHUB_LUXURY_V16_START */' not in css or '/* TOS_GITHUB_LUXURY_V16_END */' not in css:
    raise SystemExit('BLOCKED: V16 direct-ID contract missing')
if '/* TOS_GITHUB_LUXURY_V17_START */' not in css or '/* TOS_GITHUB_LUXURY_V17_END */' not in css:
    raise SystemExit('BLOCKED: V17 final polish missing; V18 must run on V17')

START = '/* TOS_GITHUB_LUXURY_V18_START */'
END = '/* TOS_GITHUB_LUXURY_V18_END */'
if START in css:
    a = css.find(START)
    b = css.find(END, a)
    if b < 0:
        raise SystemExit('BLOCKED: malformed existing V18 CSS block')
    css = css[:a] + css[b + len(END):]

v18 = r'''
/* TOS_GITHUB_LUXURY_V18_START */
/* Final surface polish: remove washed gray, soften harsh white, unify shell/sidebar. */

/* 1) Global left sidebar joins the Midnight Navy visual system on GitHub. */
html.dark body:has(#github-overview) .tos-premium-sidebar {
  background:
    radial-gradient(circle at 22% 5%, rgba(210,158,48,.055), transparent 25%),
    linear-gradient(180deg,#050D16 0%,#07121D 48%,#050C14 100%) !important;
  color:#DCE5ED !important;
  border-color:rgba(102,136,165,.16) !important;
  ring-color:transparent !important;
  box-shadow:0 24px 64px rgba(0,0,0,.31),inset 0 1px 0 rgba(255,255,255,.024) !important;
}
html.dark body:has(#github-overview) .tos-premium-sidebar > div:first-child,
html.dark body:has(#github-overview) .tos-premium-sidebar > div:last-of-type {
  background:transparent !important;
  border-color:rgba(103,137,165,.12) !important;
}
html.dark body:has(#github-overview) .tos-premium-sidebar section {
  background:rgba(8,20,32,.72) !important;
  border-color:rgba(98,133,162,.13) !important;
  box-shadow:none !important;
}
html.dark body:has(#github-overview) .tos-premium-sidebar section > button {
  color:#B8C5D0 !important;
}
html.dark body:has(#github-overview) .tos-premium-sidebar section > div {
  background:rgba(5,14,23,.64) !important;
  border-color:rgba(98,133,162,.10) !important;
}
html.dark body:has(#github-overview) .tos-premium-sidebar a:not([aria-current='page']) {
  color:#91A2B2 !important;
}
html.dark body:has(#github-overview) .tos-premium-sidebar a:not([aria-current='page']):hover {
  color:#E8EEF4 !important;
  background:rgba(255,255,255,.035) !important;
}
html.dark body:has(#github-overview) .tos-premium-sidebar [aria-current='page'] {
  color:#F5D27D !important;
  background:linear-gradient(90deg,rgba(198,143,35,.17),rgba(9,24,37,.74)) !important;
  border-color:rgba(214,163,60,.28) !important;
  box-shadow:inset 3px 0 0 rgba(221,169,65,.90),0 8px 22px rgba(0,0,0,.15) !important;
}
html.dark body:has(#github-overview) .tos-premium-sidebar > div:last-of-type button,
html.dark body:has(#github-overview) .tos-premium-sidebar > div:last-of-type > div:last-child {
  background:#081521 !important;
  color:#B8C5D0 !important;
  border-color:rgba(101,136,165,.14) !important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.02) !important;
}

/* 2) Calm the gold scrollbar: premium accent, not a bright rail. */
html.dark body:has(#github-overview),
html.dark body:has(#github-overview) .tos-sidebar-scroll-region,
html.dark body:has(#github-overview) .tos-page {
  scrollbar-color:rgba(181,133,41,.48) #06111B !important;
  scrollbar-width:thin !important;
}
html.dark body:has(#github-overview) *::-webkit-scrollbar { width:8px; height:8px; }
html.dark body:has(#github-overview) *::-webkit-scrollbar-track { background:#06111B !important; }
html.dark body:has(#github-overview) *::-webkit-scrollbar-thumb {
  background:linear-gradient(180deg,rgba(178,129,37,.42),rgba(134,96,29,.34)) !important;
  border:2px solid #06111B !important;
  border-radius:999px !important;
}
html.dark body:has(#github-overview) *::-webkit-scrollbar-thumb:hover {
  background:linear-gradient(180deg,rgba(200,150,53,.58),rgba(153,111,34,.48)) !important;
}

/* 3) Changes donut: remove the harsh white ring while preserving status segments. */
html.dark #github-changes article:first-child div[style*='conic-gradient'] {
  background-color:#42566A !important;
  background-blend-mode:multiply !important;
  box-shadow:0 0 0 1px rgba(112,145,173,.13),0 14px 34px rgba(0,0,0,.18) !important;
}
html.dark #github-changes article:first-child div[style*='conic-gradient'] > div {
  background:radial-gradient(circle at 38% 32%,#0C1E2E 0%,#081623 72%) !important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.025),inset 0 0 28px rgba(0,0,0,.20) !important;
}
html.dark #github-changes span[class*='bg-zinc-300'] { background:#6C8094 !important; }

/* 4) Changes + Activity: remove flat gray and create refined navy layering. */
html.dark #github-changes > article {
  background:linear-gradient(180deg,#081827 0%,#071420 100%) !important;
  border-color:rgba(101,136,165,.15) !important;
  box-shadow:0 15px 38px rgba(0,0,0,.21),inset 0 1px 0 rgba(255,255,255,.022) !important;
}
html.dark #github-changes article:first-child [class*='rounded-xl'] {
  background:#0A1B2A !important;
  border:1px solid rgba(101,137,166,.095) !important;
}
html.dark #github-changes article:last-child > div:last-of-type {
  background:#081827 !important;
  border-color:rgba(102,137,166,.14) !important;
}
html.dark #github-changes article:last-child > div:last-of-type > div {
  background:linear-gradient(90deg,rgba(10,27,42,.84),rgba(8,23,36,.84)) !important;
}

/* 5) Repository Information: remove the washed slate band. */
html.dark #github-changes + section {
  background:linear-gradient(180deg,#071522 0%,#06121D 100%) !important;
  border-color:rgba(98,133,162,.15) !important;
  box-shadow:0 15px 38px rgba(0,0,0,.20),inset 0 1px 0 rgba(255,255,255,.022) !important;
}
html.dark #github-changes + section [class*='rounded-2xl'] {
  background:linear-gradient(180deg,#0B1C2B 0%,#091824 100%) !important;
  border-color:rgba(104,140,170,.13) !important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.022) !important;
}

/* 6) Connection + Logs: subtle elevation instead of flat dark strips. */
html.dark #github-connection,
html.dark #github-console {
  background:
    radial-gradient(circle at 92% -80%,rgba(35,83,126,.10),transparent 31%),
    linear-gradient(180deg,#081725 0%,#06131F 100%) !important;
  border-color:rgba(101,136,165,.15) !important;
  box-shadow:0 15px 38px rgba(0,0,0,.21),inset 0 1px 0 rgba(255,255,255,.024) !important;
}
html.dark #github-connection button,
html.dark #github-console button {
  background:#0A1927 !important;
  color:#BFCBD6 !important;
  border-color:rgba(104,139,168,.13) !important;
}
html.dark #github-connection:hover,
html.dark #github-console:hover {
  border-color:rgba(119,152,181,.21) !important;
}

/* 7) Final surface palette: navy, soft-white, teal; no washed gray. */
html.dark .tos-page:has(#github-overview) [class*='bg-zinc-800'],
html.dark .tos-page:has(#github-overview) [class*='bg-zinc-900'] {
  background-color:#091824 !important;
}
html.dark .tos-page:has(#github-overview) [class*='text-zinc-400'] { color:#9AAABA !important; }
html.dark .tos-page:has(#github-overview) [class*='text-zinc-500'] { color:#ADBAC7 !important; }
html.dark .tos-page:has(#github-overview) [class*='text-zinc-600'],
html.dark .tos-page:has(#github-overview) [class*='text-zinc-700'] { color:#CBD5DE !important; }

/* TOS_GITHUB_LUXURY_V18_END */
'''

css = css.rstrip() + '\n\n' + v18.strip() + '\n'

if css == css0:
    raise SystemExit('BLOCKED: no CSS changes produced')
if UI.read_text(encoding='utf-8') != ui:
    raise SystemExit('BLOCKED: JSX changed unexpectedly')
if SIDEBAR.read_text(encoding='utf-8') != sidebar:
    raise SystemExit('BLOCKED: Sidebar JSX changed unexpectedly')

CSS.write_text(css, encoding='utf-8')

print('PATCH_APPLIED=YES')
print('BASE=V17_FINAL_LUXURY_POLISH')
print('FILES_CHANGED=1')
print('PATCH_MODE=CSS_ONLY_FINAL_SURFACE_POLISH')
print('JSX_UNCHANGED=YES')
print('LOGIC_UNCHANGED=YES')
print('LIGHT_MODE_UNCHANGED=YES')
print('GLOBAL_SIDEBAR_UNIFIED=YES')
print('GOLD_SCROLLBAR_SOFTENED=YES')
print('DONUT_WHITE_SOFTENED=YES')
print('CHANGES_SURFACE_REFINED=YES')
print('REPOSITORY_SURFACE_REFINED=YES')
print('CONNECTION_LOGS_DEPTH=YES')
print('WASHED_GRAY_REMOVED=YES')
