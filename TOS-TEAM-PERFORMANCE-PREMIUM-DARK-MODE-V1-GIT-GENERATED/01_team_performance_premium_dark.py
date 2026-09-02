#!/usr/bin/env python3
from pathlib import Path

ROOT = Path("/var/www/TOS")
DASHBOARD = ROOT / "frontend/src/pages/TeamPerformanceDashboard.jsx"
CSS_FILE = ROOT / "frontend/src/components/performance/teamPerformancePremiumDark.css"

IMPORT_ANCHOR = 'import { ExecutiveCommandCenterPanel } from "../components/performance/ExecutiveCommandCenter";\n'
CSS_IMPORT = 'import "../components/performance/teamPerformancePremiumDark.css";\n'
ROOT_OLD = '<div className="tos-page space-y-4">'
ROOT_NEW = '<div className="tos-page tos-team-performance-premium space-y-4">'

CSS = r'''/* TOS Team Performance — Premium Dark Mode V1
   Scope: /team-performance only. Light mode remains untouched. */

html.dark .tos-team-performance-premium {
  --tp-bg: #0d0f12;
  --tp-surface: #14171c;
  --tp-surface-raised: #191d24;
  --tp-surface-soft: #171b21;
  --tp-surface-deep: #101318;
  --tp-border: rgba(255, 255, 255, 0.075);
  --tp-border-strong: rgba(255, 255, 255, 0.115);
  --tp-text: #f5f7fa;
  --tp-text-soft: #d6dbe3;
  --tp-muted: #98a2b3;
  --tp-muted-soft: #7f8998;
  --tp-gold: #d9a441;
  --tp-shadow: 0 18px 48px rgba(0, 0, 0, 0.28);
  color: var(--tp-text);
  isolation: isolate;
}

/* Premium page introduction */
html.dark .tos-team-performance-premium .tos-premium-page-intro {
  margin-bottom: 1rem;
  padding: 1.2rem 1.35rem;
  border: 1px solid var(--tp-border);
  border-radius: 22px;
  background:
    radial-gradient(circle at 8% 0%, rgba(217, 164, 65, 0.11), transparent 30%),
    linear-gradient(135deg, rgba(25, 29, 36, 0.98), rgba(15, 18, 23, 0.98));
  box-shadow: 0 14px 36px rgba(0, 0, 0, 0.22), inset 0 1px 0 rgba(255, 255, 255, 0.035);
}

/* Primary surfaces — consistent instead of light cards floating on black */
html.dark .tos-team-performance-premium .tos-premium-card,
html.dark .tos-team-performance-premium .tos-premium-system-card,
html.dark .tos-team-performance-premium .tos-premium-stat {
  background: linear-gradient(180deg, rgba(25, 29, 36, 0.97), rgba(20, 23, 28, 0.97)) !important;
  border-color: var(--tp-border) !important;
  box-shadow: var(--tp-shadow), inset 0 1px 0 rgba(255, 255, 255, 0.028) !important;
}

html.dark .tos-team-performance-premium .tos-premium-card:hover,
html.dark .tos-team-performance-premium .tos-premium-system-card:hover,
html.dark .tos-team-performance-premium .tos-premium-stat:hover {
  border-color: var(--tp-border-strong) !important;
}

/* Normalize legacy light utility surfaces used across Phases 3–12 */
html.dark .tos-team-performance-premium [class*="bg-white"],
html.dark .tos-team-performance-premium [class*="bg-zinc-50"],
html.dark .tos-team-performance-premium [class*="bg-zinc-100"] {
  background-color: var(--tp-surface-soft) !important;
}

html.dark .tos-team-performance-premium [class*="dark:bg-white/"] {
  background-color: rgba(255, 255, 255, 0.035) !important;
}

html.dark .tos-team-performance-premium [class*="dark:bg-zinc-900"],
html.dark .tos-team-performance-premium [class*="dark:bg-zinc-950"] {
  background-color: var(--tp-surface) !important;
}

/* Semantic colors stay meaningful, but become subtle executive tints */
html.dark .tos-team-performance-premium [class*="bg-emerald-"],
html.dark .tos-team-performance-premium [class*="dark:bg-emerald-"] {
  background-color: rgba(16, 185, 129, 0.055) !important;
}
html.dark .tos-team-performance-premium [class*="bg-red-"],
html.dark .tos-team-performance-premium [class*="dark:bg-red-"] {
  background-color: rgba(239, 68, 68, 0.055) !important;
}
html.dark .tos-team-performance-premium [class*="bg-orange-"],
html.dark .tos-team-performance-premium [class*="dark:bg-orange-"] {
  background-color: rgba(249, 115, 22, 0.052) !important;
}
html.dark .tos-team-performance-premium [class*="bg-amber-"],
html.dark .tos-team-performance-premium [class*="dark:bg-amber-"] {
  background-color: rgba(217, 164, 65, 0.065) !important;
}
html.dark .tos-team-performance-premium [class*="bg-blue-"],
html.dark .tos-team-performance-premium [class*="dark:bg-blue-"] {
  background-color: rgba(59, 130, 246, 0.052) !important;
}

/* Harmonized borders */
html.dark .tos-team-performance-premium [class*="border-zinc-"],
html.dark .tos-team-performance-premium [class*="dark:border-white/"] {
  border-color: var(--tp-border) !important;
}
html.dark .tos-team-performance-premium [class*="border-emerald-"] { border-color: rgba(16, 185, 129, 0.18) !important; }
html.dark .tos-team-performance-premium [class*="border-red-"] { border-color: rgba(239, 68, 68, 0.18) !important; }
html.dark .tos-team-performance-premium [class*="border-orange-"] { border-color: rgba(249, 115, 22, 0.18) !important; }
html.dark .tos-team-performance-premium [class*="border-amber-"] { border-color: rgba(217, 164, 65, 0.19) !important; }
html.dark .tos-team-performance-premium [class*="border-blue-"] { border-color: rgba(59, 130, 246, 0.17) !important; }

/* Typography hierarchy */
html.dark .tos-team-performance-premium [class*="text-zinc-950"],
html.dark .tos-team-performance-premium [class*="text-zinc-900"] { color: var(--tp-text) !important; }
html.dark .tos-team-performance-premium [class*="text-zinc-800"],
html.dark .tos-team-performance-premium [class*="text-zinc-700"] { color: var(--tp-text-soft) !important; }
html.dark .tos-team-performance-premium [class*="text-zinc-600"],
html.dark .tos-team-performance-premium [class*="text-zinc-500"] { color: var(--tp-muted) !important; }
html.dark .tos-team-performance-premium [class*="text-zinc-400"] { color: var(--tp-muted-soft) !important; }

html.dark .tos-team-performance-premium [class*="text-emerald-"] { color: #6ee7b7 !important; }
html.dark .tos-team-performance-premium [class*="text-red-"] { color: #fda4af !important; }
html.dark .tos-team-performance-premium [class*="text-orange-"] { color: #fdba74 !important; }
html.dark .tos-team-performance-premium [class*="text-amber-"] { color: #e7bd68 !important; }
html.dark .tos-team-performance-premium [class*="text-blue-"] { color: #93c5fd !important; }

/* KPI numbers and key headings remain crisp */
html.dark .tos-team-performance-premium h1,
html.dark .tos-team-performance-premium h2,
html.dark .tos-team-performance-premium h3,
html.dark .tos-team-performance-premium h4,
html.dark .tos-team-performance-premium strong,
html.dark .tos-team-performance-premium b {
  color: var(--tp-text);
}

/* Filters, inputs and selects */
html.dark .tos-team-performance-premium input,
html.dark .tos-team-performance-premium select,
html.dark .tos-team-performance-premium textarea {
  color: var(--tp-text-soft) !important;
  background-color: var(--tp-surface-deep) !important;
  border-color: var(--tp-border-strong) !important;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.025);
}
html.dark .tos-team-performance-premium input::placeholder,
html.dark .tos-team-performance-premium textarea::placeholder {
  color: #6f7885 !important;
}
html.dark .tos-team-performance-premium input:focus,
html.dark .tos-team-performance-premium select:focus,
html.dark .tos-team-performance-premium textarea:focus {
  border-color: rgba(217, 164, 65, 0.6) !important;
  box-shadow: 0 0 0 3px rgba(217, 164, 65, 0.08) !important;
}

/* Active segmented controls: premium gold instead of white inversion */
html.dark .tos-team-performance-premium button[class*="dark:bg-white"] {
  color: #0b0d10 !important;
  background: linear-gradient(135deg, #e2b458, #c9932d) !important;
  border-color: rgba(226, 180, 88, 0.55) !important;
  box-shadow: 0 7px 18px rgba(217, 164, 65, 0.14) !important;
}

/* Secondary buttons */
html.dark .tos-team-performance-premium button[class*="bg-white"]:not([class*="dark:bg-white"]) {
  color: var(--tp-text-soft) !important;
  background: var(--tp-surface-raised) !important;
  border-color: var(--tp-border) !important;
}
html.dark .tos-team-performance-premium button[class*="bg-white"]:not([class*="dark:bg-white"]):hover {
  border-color: rgba(217, 164, 65, 0.28) !important;
  background: #1c2128 !important;
}

/* Keep the main gold CTA intentional and consistent */
html.dark .tos-team-performance-premium button[class*="from-amber-500"],
html.dark .tos-team-performance-premium button[class*="from-yellow-"] {
  color: #101216 !important;
  background-image: linear-gradient(135deg, #e4b65c, #c9932d) !important;
  box-shadow: 0 10px 24px rgba(217, 164, 65, 0.16) !important;
}

/* Tables: remove beige/light sheet appearance */
html.dark .tos-team-performance-premium table {
  color: var(--tp-text-soft);
  border-color: var(--tp-border) !important;
}
html.dark .tos-team-performance-premium thead,
html.dark .tos-team-performance-premium thead tr,
html.dark .tos-team-performance-premium thead th {
  background: #11151a !important;
  border-color: var(--tp-border) !important;
  color: #aab3c0 !important;
}
html.dark .tos-team-performance-premium tbody tr {
  border-color: rgba(255, 255, 255, 0.055) !important;
  transition: background-color 140ms ease, box-shadow 140ms ease;
}
html.dark .tos-team-performance-premium tbody tr:hover {
  background-color: rgba(255, 255, 255, 0.028) !important;
}
html.dark .tos-team-performance-premium td,
html.dark .tos-team-performance-premium th {
  border-color: rgba(255, 255, 255, 0.055) !important;
}

/* Progress tracks and separators */
html.dark .tos-team-performance-premium [class*="bg-zinc-200"] {
  background-color: #232831 !important;
}
html.dark .tos-team-performance-premium hr {
  border-color: var(--tp-border) !important;
}

/* Popovers / menus */
html.dark .tos-team-performance-premium [class*="shadow-xl"],
html.dark .tos-team-performance-premium [class*="shadow-2xl"] {
  box-shadow: 0 20px 55px rgba(0, 0, 0, 0.42) !important;
}

/* Scrollbars inside long management tables/drawers */
html.dark .tos-team-performance-premium * {
  scrollbar-color: #333a44 transparent;
}
html.dark .tos-team-performance-premium *::-webkit-scrollbar { width: 10px; height: 10px; }
html.dark .tos-team-performance-premium *::-webkit-scrollbar-track { background: transparent; }
html.dark .tos-team-performance-premium *::-webkit-scrollbar-thumb {
  background: #303640;
  border: 2px solid transparent;
  border-radius: 999px;
  background-clip: padding-box;
}
html.dark .tos-team-performance-premium *::-webkit-scrollbar-thumb:hover { background-color: #3d4551; }

/* Slightly denser visual rhythm on desktop without changing layout */
@media (min-width: 1024px) {
  html.dark .tos-team-performance-premium .tos-premium-card,
  html.dark .tos-team-performance-premium .tos-premium-system-card {
    backdrop-filter: blur(10px);
  }
}

/* Respect reduced-motion users */
@media (prefers-reduced-motion: reduce) {
  html.dark .tos-team-performance-premium * {
    transition-duration: 0.01ms !important;
    animation-duration: 0.01ms !important;
  }
}
'''


def fail(message: str):
    raise SystemExit(f"ERROR: {message}")


def main():
    if not DASHBOARD.exists():
        fail(f"missing {DASHBOARD}")

    source = DASHBOARD.read_text(encoding="utf-8")

    if "ExecutiveCommandCenterPanel" not in source:
        fail("Phase 12 ExecutiveCommandCenter marker/import is missing; wrong TOS baseline")

    if CSS_IMPORT not in source:
        if IMPORT_ANCHOR not in source:
            fail("ExecutiveCommandCenter import anchor not found")
        source = source.replace(IMPORT_ANCHOR, IMPORT_ANCHOR + CSS_IMPORT, 1)

    if ROOT_NEW not in source:
        if ROOT_OLD not in source:
            fail("TeamPerformanceDashboard root anchor not found")
        source = source.replace(ROOT_OLD, ROOT_NEW, 1)

    DASHBOARD.write_text(source, encoding="utf-8")

    CSS_FILE.parent.mkdir(parents=True, exist_ok=True)
    CSS_FILE.write_text(CSS, encoding="utf-8")

    print("TEAM_PERFORMANCE_PREMIUM_DARK_MODE_V1_APPLIED=YES")
    print(f"DASHBOARD={DASHBOARD}")
    print(f"CSS_FILE={CSS_FILE}")
    print("LIGHT_MODE_CHANGED=NO")
    print("LAYOUT_REDESIGN=NO")


if __name__ == "__main__":
    main()
