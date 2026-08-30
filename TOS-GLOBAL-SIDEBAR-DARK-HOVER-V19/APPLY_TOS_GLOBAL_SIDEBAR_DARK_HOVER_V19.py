#!/usr/bin/env python3
from pathlib import Path

CSS = Path('frontend/src/index.css')
SIDEBAR = Path('frontend/src/components/layout/Sidebar.jsx')

for p in (CSS, SIDEBAR):
    if not p.exists():
        raise SystemExit(f'BLOCKED: target not found: {p}')

css = CSS.read_text(encoding='utf-8')
sidebar = SIDEBAR.read_text(encoding='utf-8')
css0 = css

required_sidebar = [
    'tos-premium-sidebar',
    'tos-sidebar-scroll-region',
    'aria-current={selected ? "page" : undefined}',
    'aria-current={subSelected ? "page" : undefined}',
    'hover:bg-slate-50',
]
for token in required_sidebar:
    if token not in sidebar:
        raise SystemExit(f'BLOCKED: sidebar anchor missing: {token}')

START = '/* TOS_GLOBAL_SIDEBAR_DARK_HOVER_V19_START */'
END = '/* TOS_GLOBAL_SIDEBAR_DARK_HOVER_V19_END */'
if START in css:
    a = css.find(START)
    b = css.find(END, a)
    if b < 0:
        raise SystemExit('BLOCKED: malformed existing V19 CSS block')
    css = css[:a] + css[b + len(END):]

v19 = r'''
/* TOS_GLOBAL_SIDEBAR_DARK_HOVER_V19_START */
/* Global dark-sidebar interaction contract: zero white/slate flashes while navigating. */

html.dark .tos-premium-sidebar {
  background:linear-gradient(180deg,#050D16 0%,#07121D 48%,#050C14 100%) !important;
  color:#DCE5ED !important;
  border-color:rgba(102,136,165,.16) !important;
  box-shadow:0 24px 64px rgba(0,0,0,.30),inset 0 1px 0 rgba(255,255,255,.024) !important;
}

/* Header/footer chrome inside sidebar: never flash white. */
html.dark .tos-premium-sidebar > div:first-child,
html.dark .tos-premium-sidebar > div:last-of-type {
  background:transparent !important;
  border-color:rgba(103,137,165,.12) !important;
}

/* Root navigation groups: closed/open states remain midnight navy. */
html.dark .tos-premium-sidebar nav section {
  background:rgba(8,20,32,.72) !important;
  border-color:rgba(98,133,162,.13) !important;
  box-shadow:none !important;
}
html.dark .tos-premium-sidebar nav section:hover,
html.dark .tos-premium-sidebar nav section:focus-within {
  background:rgba(10,26,41,.90) !important;
  border-color:rgba(116,150,178,.20) !important;
}
html.dark .tos-premium-sidebar nav section > button {
  background:transparent !important;
  color:#B7C4CF !important;
  border-color:transparent !important;
}
html.dark .tos-premium-sidebar nav section > button:hover,
html.dark .tos-premium-sidebar nav section > button:focus-visible {
  background:#0B1B2A !important;
  color:#EEF3F7 !important;
}

/* Open submenu panel must stay dark; no bg-white/90 flash. */
html.dark .tos-premium-sidebar nav section > div {
  background:rgba(5,14,23,.82) !important;
  border-color:rgba(98,133,162,.11) !important;
}

/* Every normal nav/subnav item: transparent -> navy hover, never light gray. */
html.dark .tos-premium-sidebar nav a:not([aria-current='page']),
html.dark .tos-premium-sidebar nav button:not([aria-current='page']) {
  background:transparent !important;
  color:#91A2B2 !important;
  border-color:transparent !important;
  box-shadow:none !important;
}
html.dark .tos-premium-sidebar nav a:not([aria-current='page']):hover,
html.dark .tos-premium-sidebar nav button:not([aria-current='page']):hover,
html.dark .tos-premium-sidebar nav a:not([aria-current='page']):focus-visible,
html.dark .tos-premium-sidebar nav button:not([aria-current='page']):focus-visible {
  background:#0C1D2D !important;
  color:#EDF3F8 !important;
  border-color:rgba(112,146,175,.16) !important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.018) !important;
}

/* Selected category/subcategory: one restrained gold state everywhere. */
html.dark .tos-premium-sidebar [aria-current='page'] {
  background:linear-gradient(90deg,rgba(198,143,35,.17),rgba(9,24,37,.80)) !important;
  color:#F5D27D !important;
  border-color:rgba(214,163,60,.28) !important;
  box-shadow:inset 3px 0 0 rgba(221,169,65,.90),0 8px 22px rgba(0,0,0,.15) !important;
}
html.dark .tos-premium-sidebar [aria-current='page'] svg {
  color:#D9AE5B !important;
}

/* Parent group stays dark while its child is selected/open. */
html.dark .tos-premium-sidebar nav section:has([aria-current='page']) {
  background:linear-gradient(180deg,rgba(10,25,39,.96),rgba(7,19,30,.96)) !important;
  border-color:rgba(202,151,54,.18) !important;
}
html.dark .tos-premium-sidebar nav section:has([aria-current='page']) > button {
  background:transparent !important;
  color:#E2E8EE !important;
}

/* Neutralize Tailwind light hover/background utility remnants inside sidebar. */
html.dark .tos-premium-sidebar [class*='bg-white'],
html.dark .tos-premium-sidebar [class*='bg-slate-50'],
html.dark .tos-premium-sidebar [class*='bg-slate-100'],
html.dark .tos-premium-sidebar [class*='hover:bg-slate-50'] {
  background-color:transparent !important;
}
html.dark .tos-premium-sidebar nav section[class*='bg-white'],
html.dark .tos-premium-sidebar nav section[class*='bg-slate-50'] {
  background:rgba(8,20,32,.72) !important;
}
html.dark .tos-premium-sidebar nav section > div[class*='bg-white'],
html.dark .tos-premium-sidebar nav section > div[class*='bg-zinc-950'] {
  background:rgba(5,14,23,.82) !important;
}

/* Collapsed sidebar buttons use the same dark interaction system. */
html.dark .tos-premium-sidebar nav button:not([aria-current='page']) {
  background:transparent !important;
}
html.dark .tos-premium-sidebar nav button:not([aria-current='page']):hover {
  background:#0C1D2D !important;
}

/* Footer controls and role card also stay dark during hover/focus. */
html.dark .tos-premium-sidebar > div:last-of-type button,
html.dark .tos-premium-sidebar > div:last-of-type > div:last-child {
  background:#081521 !important;
  color:#B8C5D0 !important;
  border-color:rgba(101,136,165,.14) !important;
}
html.dark .tos-premium-sidebar > div:last-of-type button:hover,
html.dark .tos-premium-sidebar > div:last-of-type button:focus-visible {
  background:#0B1B2A !important;
  color:#EDF3F8 !important;
  border-color:rgba(119,151,179,.20) !important;
}

/* Remove transition flash caused by interpolating light backgrounds. */
html.dark .tos-premium-sidebar nav a,
html.dark .tos-premium-sidebar nav button,
html.dark .tos-premium-sidebar nav section,
html.dark .tos-premium-sidebar nav section > div {
  transition-property:background-color,border-color,color,box-shadow,transform !important;
  transition-duration:140ms !important;
  transition-timing-function:ease-out !important;
}

/* TOS_GLOBAL_SIDEBAR_DARK_HOVER_V19_END */
'''

css = css.rstrip() + '\n\n' + v19.strip() + '\n'

if css == css0:
    raise SystemExit('BLOCKED: no CSS changes produced')
if SIDEBAR.read_text(encoding='utf-8') != sidebar:
    raise SystemExit('BLOCKED: Sidebar JSX changed unexpectedly')

CSS.write_text(css, encoding='utf-8')

print('PATCH_APPLIED=YES')
print('FILES_CHANGED=1')
print('PATCH_MODE=CSS_ONLY_GLOBAL_SIDEBAR')
print('SIDEBAR_JSX_UNCHANGED=YES')
print('LOGIC_UNCHANGED=YES')
print('LIGHT_MODE_UNCHANGED=YES')
print('GLOBAL_DARK_SIDEBAR=YES')
print('WHITE_HOVER_FLASH_REMOVED=YES')
print('GROUP_HOVER_NAVY=YES')
print('SUBNAV_HOVER_NAVY=YES')
print('ACTIVE_GOLD_CONSISTENT=YES')
print('FOOTER_HOVER_DARK=YES')
