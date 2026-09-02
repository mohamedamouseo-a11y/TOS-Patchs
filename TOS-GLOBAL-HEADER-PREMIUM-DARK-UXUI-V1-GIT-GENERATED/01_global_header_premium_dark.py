#!/usr/bin/env python3
from pathlib import Path

ROOT = Path('/var/www/TOS')
TOPBAR = ROOT / 'frontend/src/components/layout/Topbar.jsx'
CSS = ROOT / 'frontend/src/components/layout/premiumHeaderDark.css'

text = TOPBAR.read_text()

import_line = 'import "./premiumHeaderDark.css";\n'
if import_line not in text:
    anchor = 'import { useT } from "../../i18n/translations";\n'
    if anchor not in text:
        raise SystemExit('Topbar import anchor not found')
    text = text.replace(anchor, anchor + import_line, 1)

replacements = {
    'className="flex min-w-0 items-center gap-3"': 'className="tos-premium-topbar-identity flex min-w-0 items-center gap-3"',
    'className="min-w-0">\n          <h1': 'className="tos-premium-topbar-copy min-w-0">\n          <h1',
    'className="truncate text-xl font-black tracking-[-0.02em] text-zinc-950 dark:text-white sm:text-2xl"': 'className="tos-premium-topbar-title truncate text-xl font-black tracking-[-0.02em] text-zinc-950 dark:text-white sm:text-2xl"',
    'className="mt-1 truncate text-sm font-semibold text-zinc-500 dark:text-zinc-400"': 'className="tos-premium-topbar-subtitle mt-1 truncate text-sm font-semibold text-zinc-500 dark:text-zinc-400"',
    'className="flex min-w-0 items-center gap-1.5 rounded-2xl border border-zinc-200/70 bg-zinc-50/80 p-1.5 shadow-sm dark:border-white/10 dark:bg-white/[0.04]"': 'className="tos-premium-topbar-actions flex min-w-0 items-center gap-1.5 rounded-2xl border border-zinc-200/70 bg-zinc-50/80 p-1.5 shadow-sm dark:border-white/10 dark:bg-white/[0.04]"',
}
for old, new in replacements.items():
    if old in text and new not in text:
        text = text.replace(old, new, 1)

# Add a common class to the compact action buttons without touching handlers or semantics.
button_patterns = [
    'className="relative grid h-10 w-10 shrink-0 place-items-center rounded-xl border border-transparent bg-white text-zinc-600 transition hover:border-amber-200 hover:bg-amber-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-400 dark:bg-zinc-900 dark:text-zinc-300 dark:hover:bg-zinc-800"',
    'className="grid h-10 w-10 shrink-0 place-items-center rounded-xl border border-transparent bg-white text-zinc-600 transition hover:border-amber-200 hover:bg-amber-50 dark:bg-zinc-900 dark:text-amber-300 dark:hover:bg-zinc-800"',
    'className="grid h-10 w-10 shrink-0 place-items-center rounded-xl border border-transparent bg-white text-xs font-black text-zinc-600 transition hover:border-amber-200 hover:bg-amber-50 dark:bg-zinc-900 dark:text-amber-300 dark:hover:bg-zinc-800"',
    'className="grid h-10 w-10 place-items-center rounded-xl border border-transparent bg-white text-zinc-500 dark:bg-zinc-900 dark:text-zinc-300 lg:hidden"',
]
for old in button_patterns:
    if old in text:
        new = old.replace('className="', 'className="tos-premium-topbar-icon-button ', 1)
        text = text.replace(old, new, 1)

TOPBAR.write_text(text)

css = r'''/* TOS_GLOBAL_HEADER_PREMIUM_DARK_UXUI_V1
   Dark-mode-only refinement for the global TOS topbar.
   Light mode is intentionally untouched. */

html.dark .tos-premium-topbar,
html.dark[data-tos-design-system="true"] .tos-premium-topbar {
  min-height: 68px !important;
  margin: 10px 10px 0;
  padding-inline: 18px !important;
  border: 1px solid rgba(255,255,255,0.075) !important;
  border-radius: 22px !important;
  background:
    radial-gradient(circle at 88% -100%, rgba(217,164,65,0.12), transparent 34%),
    linear-gradient(135deg, rgba(20,23,28,0.98), rgba(13,15,18,0.96)) !important;
  box-shadow:
    0 14px 34px rgba(0,0,0,0.24),
    inset 0 1px 0 rgba(255,255,255,0.025) !important;
  backdrop-filter: blur(20px) saturate(125%) !important;
}

html.dark .tos-premium-topbar-title,
html.dark[data-tos-design-system="true"] .tos-premium-topbar-title {
  color: #f5f7fa !important;
  font-size: 1.125rem !important;
  line-height: 1.25rem !important;
  letter-spacing: -0.03em !important;
}

html.dark .tos-premium-topbar-subtitle,
html.dark[data-tos-design-system="true"] .tos-premium-topbar-subtitle {
  margin-top: 3px !important;
  color: #98a2b3 !important;
  font-size: 0.72rem !important;
  line-height: 1rem !important;
  font-weight: 700 !important;
}

html.dark .tos-premium-topbar-actions,
html.dark[data-tos-design-system="true"] .tos-premium-topbar-actions {
  gap: 4px !important;
  padding: 4px !important;
  border: 1px solid rgba(255,255,255,0.07) !important;
  border-radius: 16px !important;
  background: rgba(20,23,28,0.78) !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.018) !important;
}

html.dark .tos-premium-topbar .tos-premium-user-chip,
html.dark[data-tos-design-system="true"] .tos-premium-topbar .tos-premium-user-chip {
  min-height: 38px !important;
  padding: 5px 10px !important;
  border: 1px solid rgba(255,255,255,0.065) !important;
  border-radius: 12px !important;
  background: #191d24 !important;
  box-shadow: none !important;
}

html.dark .tos-premium-topbar .tos-premium-user-chip:hover,
html.dark[data-tos-design-system="true"] .tos-premium-topbar .tos-premium-user-chip:hover {
  border-color: rgba(217,164,65,0.24) !important;
  background: #1d2129 !important;
  transform: none !important;
}

html.dark .tos-premium-topbar .tos-premium-user-chip img {
  width: 30px !important;
  height: 30px !important;
  border-radius: 10px !important;
}

html.dark .tos-premium-topbar .tos-premium-user-chip p:first-of-type {
  color: #f5f7fa !important;
  font-size: 0.76rem !important;
}

html.dark .tos-premium-topbar .tos-premium-user-chip p:last-of-type {
  color: #8993a1 !important;
  font-size: 0.64rem !important;
}

html.dark .tos-premium-topbar .tos-premium-topbar-icon-button,
html.dark[data-tos-design-system="true"] .tos-premium-topbar .tos-premium-topbar-icon-button {
  width: 36px !important;
  height: 36px !important;
  min-width: 36px !important;
  min-height: 36px !important;
  border: 1px solid transparent !important;
  border-radius: 11px !important;
  background: transparent !important;
  color: #aab3bf !important;
  box-shadow: none !important;
}

html.dark .tos-premium-topbar .tos-premium-topbar-icon-button:hover,
html.dark[data-tos-design-system="true"] .tos-premium-topbar .tos-premium-topbar-icon-button:hover {
  border-color: rgba(217,164,65,0.18) !important;
  background: rgba(217,164,65,0.075) !important;
  color: #e4b75e !important;
  transform: none !important;
}

html.dark .tos-premium-topbar .tos-premium-topbar-icon-button:focus-visible,
html.dark[data-tos-design-system="true"] .tos-premium-topbar .tos-premium-topbar-icon-button:focus-visible,
html.dark .tos-premium-topbar .tos-premium-user-chip:focus-visible {
  outline: none !important;
  box-shadow: 0 0 0 2px rgba(217,164,65,0.28) !important;
}

html.dark .tos-premium-topbar .tos-premium-topbar-icon-button > span[class*="bg-red"],
html.dark[data-tos-design-system="true"] .tos-premium-topbar .tos-premium-topbar-icon-button > span[class*="bg-red"] {
  border: 2px solid #14171c;
  box-shadow: 0 2px 8px rgba(0,0,0,0.35);
}

@media (max-width: 1023px) {
  html.dark .tos-premium-topbar,
  html.dark[data-tos-design-system="true"] .tos-premium-topbar {
    min-height: 64px !important;
    margin: 8px 8px 0;
    padding-inline: 12px !important;
    border-radius: 18px !important;
  }

  html.dark .tos-premium-topbar-title,
  html.dark[data-tos-design-system="true"] .tos-premium-topbar-title {
    font-size: 1rem !important;
  }
}
'''
CSS.write_text(css)

print('TOS_GLOBAL_HEADER_PREMIUM_DARK_UXUI_V1_APPLIED=YES')
