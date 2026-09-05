from pathlib import Path
import hashlib
import shutil
import subprocess
import sys
import time

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
PAGE = ROOT / "frontend/src/pages/TeamPerformanceDashboard.jsx"
STYLE = ROOT / "frontend/src/components/performance/teamPerformanceFlagshipV1.css"
FRONTEND = ROOT / "frontend"
DIST = FRONTEND / "dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

RUNTIME_MARKER = "--tos-team-performance-flagship-v1-runtime"
ROOT_HOOK_TOKEN = "data-tp-flagship"
KPI_HOOK = "tos-tp-kpi-v1"
STYLE_IMPORT = 'import "../components/performance/teamPerformanceFlagshipV1.css";'

print("RUNNING=PHASE04_4_TEAM_PERFORMANCE_FLAGSHIP_V1")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_count(root: Path, needle: bytes) -> int:
    if not root.exists():
        return 0
    total = 0
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        try:
            total += path.read_bytes().count(needle)
        except OSError:
            pass
    return total


def fail(message: str):
    print("PASS/FAIL=FAIL")
    print("ERROR=" + str(message))
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("V1_RUNTIME=NO")
    sys.exit(1)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 match, found {count}")
    return text.replace(old, new, 1)


def replace_first(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f"{label}: match not found")
    return text.replace(old, new, 1)


if not PAGE.exists():
    fail(f"required source missing: {PAGE}")

original_page = PAGE.read_text()
style_existed = STYLE.exists()
original_style = STYLE.read_text() if style_existed else None

required_markers = (
    'className="tos-page tos-team-performance-premium tos-core-team-performance-premium space-y-4"',
    'import "../components/performance/teamPerformancePremiumDark.css";',
    'id="team-performance-kpis"',
    'id="team-performance-management-summary"',
    'id="team-performance-executive"',
    'PerformancePeriodControl',
    'ManagementSummary',
    'ExecutiveCommandCenterPanel',
    'PerformanceDisclosure',
)
for marker in required_markers:
    if marker not in original_page:
        fail(f"latest Team Performance baseline marker missing: {marker}")

if STYLE_IMPORT in original_page or ROOT_HOOK_TOKEN in original_page or RUNTIME_MARKER in (original_style or ""):
    fail("Team Performance Flagship V1 already present")

updated_page = original_page
updated_page = replace_once(
    updated_page,
    'import "../components/performance/teamPerformancePremiumDark.css";',
    'import "../components/performance/teamPerformancePremiumDark.css";\nimport "../components/performance/teamPerformanceFlagshipV1.css";',
    "flagship stylesheet import",
)
updated_page = replace_once(
    updated_page,
    '<div className="tos-page tos-team-performance-premium tos-core-team-performance-premium space-y-4">',
    '<div data-tp-flagship="v1" className="tos-page tos-team-performance-premium tos-core-team-performance-premium tos-team-performance-flagship-v1 space-y-4">',
    "flagship root hook",
)
updated_page = replace_once(
    updated_page,
    '<div className={`rounded-2xl border p-4 ${shell}`}>',
    '<div data-tp-tone={tone} className={`tos-tp-kpi-v1 rounded-2xl border p-4 ${shell}`}>',
    "KPI flagship hook",
)
updated_page = replace_once(
    updated_page,
    '<Icon size={17} className="text-zinc-500 dark:text-zinc-300" />',
    '<span className="tos-tp-kpi-icon-v1"><Icon size={17} className="text-zinc-500 dark:text-zinc-300" /></span>',
    "KPI icon medallion",
)
updated_page = replace_first(
    updated_page,
    '<Card className="p-4">\n        <div className="flex flex-col gap-3">\n          <PerformancePeriodControl',
    '<Card className="tos-tp-command-deck-v1 p-4">\n        <div className="flex flex-col gap-3">\n          <PerformancePeriodControl',
    "command deck hook",
)
updated_page = replace_once(
    updated_page,
    '<div className="grid gap-2 md:grid-cols-2 xl:grid-cols-[1fr_1fr_1.2fr_auto_auto]">',
    '<div className="tos-tp-filter-grid-v1 grid gap-2 md:grid-cols-2 xl:grid-cols-[1fr_1fr_1.2fr_auto_auto]">',
    "filter grid hook",
)
updated_page = replace_once(
    updated_page,
    '<div id="team-performance-kpis" className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">',
    '<div id="team-performance-kpis" className="tos-tp-kpi-deck-v1 grid gap-3 sm:grid-cols-2 xl:grid-cols-5">',
    "KPI deck hook",
)
updated_page = replace_once(
    updated_page,
    '<div id="team-performance-management-summary">',
    '<div id="team-performance-management-summary" className="tos-tp-management-summary-v1">',
    "management summary hook",
)
updated_page = replace_once(
    updated_page,
    '<div id="team-performance-executive">',
    '<div id="team-performance-executive" className="tos-tp-executive-v1">',
    "executive center hook",
)

flagship_css = r'''/* =========================================================
   TOS Team Performance — Flagship V1
   Phase 04.4 visual-only executive redesign.
   Light: Porcelain / Ivory / Champagne.
   Dark: Obsidian / Black Titanium / Platinum / Champagne.
   ========================================================= */
:root { --tos-team-performance-flagship-v1-runtime: 1; }

.tos-team-performance-flagship-v1 {
  --tpf-gold: #d8a43c;
  --tpf-gold-soft: #f0cf82;
  --tpf-gold-deep: #9d6717;
  --tpf-ink: #151412;
  --tpf-muted: #7d7568;
  --tpf-line: rgba(151, 111, 39, .16);
  position: relative;
  isolation: isolate;
  padding-bottom: 10px;
}

/* CINEMATIC EXECUTIVE HERO */
.tos-team-performance-flagship-v1 .tos-premium-page-intro {
  position: relative;
  overflow: hidden;
  min-height: 164px;
  padding: 27px 30px !important;
  border: 1px solid rgba(193, 143, 45, .30) !important;
  border-radius: 30px !important;
  background:
    radial-gradient(ellipse 46% 138% at 8% -48%, rgba(227, 188, 95, .36) 0 34%, transparent 35%),
    radial-gradient(ellipse 72% 160% at 30% -82%, transparent 0 61%, rgba(216, 164, 60, .24) 61.3% 61.8%, transparent 62.2%),
    radial-gradient(ellipse 82% 170% at 38% -92%, transparent 0 69%, rgba(216, 164, 60, .12) 69.2% 69.7%, transparent 70.1%),
    linear-gradient(135deg, #fffefa 0%, #f7f0e2 62%, #fbf8f2 100%) !important;
  box-shadow:
    0 30px 78px rgba(83, 57, 13, .12),
    inset 0 1px 0 rgba(255, 255, 255, .99),
    inset 0 -1px 0 rgba(167, 113, 19, .07) !important;
}
.tos-team-performance-flagship-v1 .tos-premium-page-intro::before {
  content: "";
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(112deg, transparent 0 48%, rgba(242, 203, 104, .25) 48.2% 48.5%, transparent 48.8%),
    linear-gradient(118deg, transparent 0 54%, rgba(234, 191, 90, .15) 54.2% 54.5%, transparent 54.8%);
  filter: drop-shadow(0 0 16px rgba(209, 154, 43, .08));
}
.tos-team-performance-flagship-v1 .tos-premium-page-intro > * { position: relative; z-index: 1; }
.tos-team-performance-flagship-v1 .tos-premium-page-intro h1 {
  font-size: clamp(2.25rem, 3vw, 3.35rem) !important;
  line-height: .98 !important;
  letter-spacing: -.055em !important;
  font-weight: 950 !important;
  color: #15130f !important;
}
.tos-team-performance-flagship-v1 .tos-premium-page-intro p { max-width: 780px; }
.tos-team-performance-flagship-v1 .tos-premium-page-intro button,
.tos-team-performance-flagship-v1 .tos-premium-page-intro [class*="rounded-full"] {
  border-radius: 999px !important;
  box-shadow: 0 8px 22px rgba(116, 79, 18, .07);
}

/* COMMAND DECK: period + filters + export */
.tos-team-performance-flagship-v1 .tos-tp-command-deck-v1 {
  position: relative;
  overflow: visible;
  padding: 15px !important;
  border: 1px solid rgba(161, 119, 43, .15) !important;
  border-radius: 26px !important;
  background: linear-gradient(180deg, rgba(255,255,255,.97), rgba(248,244,236,.94)) !important;
  box-shadow: 0 18px 46px rgba(71, 51, 21, .07), inset 0 1px 0 rgba(255,255,255,.99) !important;
}
.tos-team-performance-flagship-v1 .tos-tp-command-deck-v1 > div > section {
  border-color: rgba(167, 123, 41, .14) !important;
  border-radius: 20px !important;
  background:
    radial-gradient(circle at 0% 0%, rgba(222, 174, 74, .09), transparent 28%),
    linear-gradient(180deg, #fbf8f1, #f6f1e7) !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.98);
}
.tos-team-performance-flagship-v1 .tos-tp-command-deck-v1 > div > section > div:first-child > div:first-child span:first-child {
  border: 1px solid rgba(211, 158, 54, .24);
  background: radial-gradient(circle at 35% 28%, #fffdf7, #f3dfad 58%, #dfb85d) !important;
  box-shadow: 0 8px 18px rgba(142, 91, 15, .10), inset 0 1px 0 rgba(255,255,255,.98);
}
.tos-team-performance-flagship-v1 .tos-tp-command-deck-v1 button[aria-pressed="true"] {
  border-color: rgba(179, 119, 15, .34) !important;
  background: linear-gradient(135deg, #f5d77f 0%, #dca83e 56%, #b97b19 100%) !important;
  color: #1b1306 !important;
  box-shadow: 0 10px 24px rgba(169, 104, 12, .18), inset 0 1px 0 rgba(255,255,255,.40) !important;
}
.tos-team-performance-flagship-v1 .tos-tp-filter-grid-v1 {
  padding: 10px;
  border: 1px solid rgba(158, 118, 48, .12);
  border-radius: 18px;
  background: rgba(255,255,255,.62);
  box-shadow: inset 0 1px 0 rgba(255,255,255,.98);
}
.tos-team-performance-flagship-v1 .tos-tp-filter-grid-v1 select,
.tos-team-performance-flagship-v1 .tos-tp-filter-grid-v1 label,
.tos-team-performance-flagship-v1 .tos-tp-filter-grid-v1 > button,
.tos-team-performance-flagship-v1 .tos-tp-filter-grid-v1 > div > button,
.tos-team-performance-flagship-v1 .tos-tp-command-deck-v1 input,
.tos-team-performance-flagship-v1 .tos-tp-command-deck-v1 select {
  min-height: 44px !important;
  border-radius: 13px !important;
  border-color: rgba(119, 92, 49, .15) !important;
  background-color: rgba(255,255,255,.90) !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.98), 0 4px 14px rgba(70,50,18,.035) !important;
}
.tos-team-performance-flagship-v1 .tos-tp-filter-grid-v1 > div > button {
  border: 1px solid rgba(159, 101, 14, .22) !important;
  background: linear-gradient(135deg, #f9df8d 0%, #e1ad42 48%, #b87917 100%) !important;
  color: #171005 !important;
  box-shadow: 0 12px 28px rgba(161, 99, 12, .17), inset 0 1px 0 rgba(255,255,255,.42) !important;
}

/* EXECUTIVE KPI DECK */
.tos-team-performance-flagship-v1 .tos-tp-kpi-deck-v1 { gap: 12px !important; }
.tos-team-performance-flagship-v1 .tos-tp-kpi-v1 {
  --kpi-accent: #d8a43c;
  position: relative;
  overflow: hidden;
  min-height: 156px;
  padding: 18px !important;
  border-radius: 23px !important;
  border-color: rgba(126, 94, 42, .13) !important;
  background:
    radial-gradient(circle at 88% 10%, color-mix(in srgb, var(--kpi-accent) 12%, transparent), transparent 34%),
    linear-gradient(180deg, rgba(255,255,255,.99), rgba(247,243,235,.96)) !important;
  box-shadow: 0 17px 38px rgba(67,49,20,.07), inset 0 1px 0 rgba(255,255,255,.99) !important;
  transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease;
}
.tos-team-performance-flagship-v1 .tos-tp-kpi-v1:hover {
  transform: translateY(-2px);
  border-color: color-mix(in srgb, var(--kpi-accent) 34%, transparent) !important;
  box-shadow: 0 24px 48px rgba(67,49,20,.10), inset 0 1px 0 rgba(255,255,255,.99) !important;
}
.tos-team-performance-flagship-v1 .tos-tp-kpi-v1::after {
  content: "";
  position: absolute;
  inset: auto 18px 0;
  height: 2px;
  border-radius: 999px;
  background: linear-gradient(90deg, transparent, var(--kpi-accent), transparent);
  opacity: .72;
}
.tos-team-performance-flagship-v1 .tos-tp-kpi-v1[data-tp-tone="green"] { --kpi-accent: #29a77a; }
.tos-team-performance-flagship-v1 .tos-tp-kpi-v1[data-tp-tone="red"] { --kpi-accent: #d45a59; }
.tos-team-performance-flagship-v1 .tos-tp-kpi-v1[data-tp-tone="gold"] { --kpi-accent: #d39b2f; }
.tos-team-performance-flagship-v1 .tos-tp-kpi-v1[data-tp-tone="neutral"] { --kpi-accent: #87909d; }
.tos-team-performance-flagship-v1 .tos-tp-kpi-icon-v1 {
  display: grid;
  width: 42px;
  height: 42px;
  place-items: center;
  border-radius: 50%;
  border: 1px solid color-mix(in srgb, var(--kpi-accent) 32%, transparent);
  background: radial-gradient(circle at 34% 26%, #fffefb, color-mix(in srgb, var(--kpi-accent) 22%, #f8f4eb) 62%, #f0eadf);
  color: var(--kpi-accent);
  box-shadow: 0 0 0 5px color-mix(in srgb, var(--kpi-accent) 6%, transparent), 0 8px 18px rgba(60,43,17,.08), inset 0 1px 0 rgba(255,255,255,.99);
}
.tos-team-performance-flagship-v1 .tos-tp-kpi-icon-v1 svg { color: currentColor !important; }
.tos-team-performance-flagship-v1 .tos-tp-kpi-v1 > p:nth-of-type(2) {
  margin-top: 12px !important;
  font-size: clamp(1.65rem, 2vw, 2.15rem) !important;
  line-height: 1 !important;
  letter-spacing: -.035em;
}

/* MAIN EXECUTIVE SURFACES */
.tos-team-performance-flagship-v1 .tos-premium-card,
.tos-team-performance-flagship-v1 .tos-premium-system-card,
.tos-team-performance-flagship-v1 .tos-tp-management-summary-v1 > *,
.tos-team-performance-flagship-v1 .tos-tp-executive-v1 > * {
  border-radius: 25px !important;
  border-color: rgba(131, 98, 45, .13) !important;
  background: linear-gradient(180deg, rgba(255,255,255,.985), rgba(249,246,240,.96)) !important;
  box-shadow: 0 18px 44px rgba(66,48,20,.06), inset 0 1px 0 rgba(255,255,255,.99) !important;
}
.tos-team-performance-flagship-v1 .tos-tp-management-summary-v1,
.tos-team-performance-flagship-v1 .tos-tp-executive-v1 {
  position: relative;
}
.tos-team-performance-flagship-v1 .tos-tp-management-summary-v1::before,
.tos-team-performance-flagship-v1 .tos-tp-executive-v1::before {
  content: "";
  position: absolute;
  z-index: 2;
  inset: 0 auto auto 28px;
  width: 86px;
  height: 2px;
  border-radius: 999px;
  background: linear-gradient(90deg, #c88a1d, #f1d27e, transparent);
  pointer-events: none;
}

/* DISCLOSURES — premium accordion system */
.tos-team-performance-flagship-v1 > details,
.tos-team-performance-flagship-v1 details[id*="disclosure"] {
  overflow: hidden;
  border-radius: 25px !important;
  border-color: rgba(135, 101, 45, .14) !important;
  background: linear-gradient(180deg, rgba(255,255,255,.94), rgba(248,244,236,.92)) !important;
  box-shadow: 0 15px 38px rgba(65,47,19,.05), inset 0 1px 0 rgba(255,255,255,.98) !important;
}
.tos-team-performance-flagship-v1 details[id*="disclosure"] > summary {
  min-height: 78px;
  padding: 16px 18px !important;
  border-radius: 24px !important;
  background:
    radial-gradient(circle at 0 0, rgba(222,174,73,.08), transparent 24%),
    linear-gradient(180deg, rgba(255,255,255,.75), rgba(249,245,238,.64));
}
.tos-team-performance-flagship-v1 details[id*="disclosure"][open] {
  border-color: rgba(204, 152, 51, .28) !important;
  box-shadow: 0 22px 50px rgba(75,52,15,.07), inset 0 1px 0 rgba(255,255,255,.98) !important;
}
.tos-team-performance-flagship-v1 details[id*="disclosure"] > summary > span:last-child {
  border-radius: 50% !important;
  border-color: rgba(199,148,49,.22) !important;
  background: linear-gradient(180deg, #fffdf8, #f2e4c2) !important;
  color: #9a6817 !important;
  box-shadow: 0 7px 16px rgba(116,77,13,.07);
}

/* TABLES — executive ledger, not spreadsheet */
.tos-team-performance-flagship-v1 table {
  border-collapse: separate;
  border-spacing: 0;
}
.tos-team-performance-flagship-v1 thead th {
  padding-top: 11px !important;
  padding-bottom: 11px !important;
  font-size: 10px !important;
  letter-spacing: .07em;
  text-transform: uppercase;
  color: #8b8273 !important;
  background: #f5f1e8 !important;
}
.tos-team-performance-flagship-v1 tbody tr { transition: background .15s ease, transform .15s ease; }
.tos-team-performance-flagship-v1 tbody tr:hover { background: rgba(218,166,62,.045) !important; }

/* MODALS / DRAWERS / POPOVERS */
.tos-team-performance-flagship-v1 [class*="shadow-2xl"],
.tos-team-performance-flagship-v1 [class*="shadow-xl"] {
  border-color: rgba(139,101,38,.15) !important;
  box-shadow: 0 28px 74px rgba(52,36,13,.18) !important;
}

/* DARK — Obsidian / Black Titanium */
html.dark .tos-team-performance-flagship-v1 {
  --tpf-gold: #e1ad45;
  --tpf-gold-soft: #f0cf7b;
  --tpf-gold-deep: #8d5a13;
  --tpf-ink: #f6f3eb;
  --tpf-muted: #9099a6;
  --tpf-line: rgba(230,177,60,.16);
}
html.dark .tos-team-performance-flagship-v1 .tos-premium-page-intro {
  border-color: rgba(236,183,58,.30) !important;
  background:
    radial-gradient(ellipse 46% 140% at 8% -48%, rgba(237, 184, 53, .25) 0 34%, transparent 35%),
    radial-gradient(ellipse 72% 160% at 30% -82%, transparent 0 61%, rgba(246,194,60,.25) 61.3% 61.8%, transparent 62.2%),
    radial-gradient(ellipse 82% 170% at 38% -92%, transparent 0 69%, rgba(246,194,60,.13) 69.2% 69.7%, transparent 70.1%),
    linear-gradient(135deg, #15181b 0%, #090b0e 70%, #0d1012 100%) !important;
  box-shadow: 0 32px 84px rgba(0,0,0,.48), 0 0 36px rgba(216,156,30,.05), inset 0 1px 0 rgba(255,255,255,.022) !important;
}
html.dark .tos-team-performance-flagship-v1 .tos-premium-page-intro h1 { color: #fff !important; }
html.dark .tos-team-performance-flagship-v1 .tos-premium-page-intro::before {
  background:
    linear-gradient(112deg, transparent 0 48%, rgba(255,204,71,.36) 48.2% 48.5%, transparent 48.8%),
    linear-gradient(118deg, transparent 0 54%, rgba(255,196,53,.20) 54.2% 54.5%, transparent 54.8%);
  filter: drop-shadow(0 0 20px rgba(255,190,45,.13));
}
html.dark .tos-team-performance-flagship-v1 .tos-tp-command-deck-v1,
html.dark .tos-team-performance-flagship-v1 .tos-premium-card,
html.dark .tos-team-performance-flagship-v1 .tos-premium-system-card,
html.dark .tos-team-performance-flagship-v1 .tos-tp-management-summary-v1 > *,
html.dark .tos-team-performance-flagship-v1 .tos-tp-executive-v1 > * {
  border-color: rgba(234,180,57,.13) !important;
  background: linear-gradient(180deg, #15181c, #0d1013) !important;
  box-shadow: 0 20px 48px rgba(0,0,0,.34), inset 0 1px 0 rgba(255,255,255,.018) !important;
}
html.dark .tos-team-performance-flagship-v1 .tos-tp-command-deck-v1 > div > section {
  border-color: rgba(238,185,60,.14) !important;
  background:
    radial-gradient(circle at 0 0, rgba(227,173,52,.07), transparent 28%),
    linear-gradient(180deg, #121519, #0c0f12) !important;
}
html.dark .tos-team-performance-flagship-v1 .tos-tp-filter-grid-v1 {
  border-color: rgba(237,183,55,.12);
  background: rgba(255,255,255,.012);
  box-shadow: inset 0 1px 0 rgba(255,255,255,.018);
}
html.dark .tos-team-performance-flagship-v1 .tos-tp-filter-grid-v1 select,
html.dark .tos-team-performance-flagship-v1 .tos-tp-filter-grid-v1 label,
html.dark .tos-team-performance-flagship-v1 .tos-tp-filter-grid-v1 > button,
html.dark .tos-team-performance-flagship-v1 .tos-tp-command-deck-v1 input,
html.dark .tos-team-performance-flagship-v1 .tos-tp-command-deck-v1 select {
  border-color: rgba(255,255,255,.08) !important;
  background-color: #0b0e11 !important;
  color: #f4f1ea !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.018) !important;
}
html.dark .tos-team-performance-flagship-v1 .tos-tp-kpi-v1 {
  background:
    radial-gradient(circle at 88% 10%, color-mix(in srgb, var(--kpi-accent) 12%, transparent), transparent 34%),
    linear-gradient(180deg, #171a1e, #0e1114) !important;
  border-color: rgba(255,255,255,.07) !important;
  box-shadow: 0 18px 42px rgba(0,0,0,.32), inset 0 1px 0 rgba(255,255,255,.018) !important;
}
html.dark .tos-team-performance-flagship-v1 .tos-tp-kpi-v1:hover {
  border-color: color-mix(in srgb, var(--kpi-accent) 30%, rgba(255,255,255,.05)) !important;
  box-shadow: 0 25px 54px rgba(0,0,0,.40), 0 0 26px color-mix(in srgb, var(--kpi-accent) 5%, transparent), inset 0 1px 0 rgba(255,255,255,.022) !important;
}
html.dark .tos-team-performance-flagship-v1 .tos-tp-kpi-icon-v1 {
  background: radial-gradient(circle at 34% 26%, color-mix(in srgb, var(--kpi-accent) 34%, #29210f), #161616 66%, #0d1013) !important;
  border-color: color-mix(in srgb, var(--kpi-accent) 38%, transparent) !important;
  box-shadow: 0 0 0 5px color-mix(in srgb, var(--kpi-accent) 6%, transparent), 0 0 24px color-mix(in srgb, var(--kpi-accent) 12%, transparent), inset 0 1px 0 rgba(255,255,255,.05) !important;
}
html.dark .tos-team-performance-flagship-v1 details[id*="disclosure"] {
  border-color: rgba(236,182,56,.13) !important;
  background: linear-gradient(180deg, #14171b, #0c0f12) !important;
  box-shadow: 0 16px 40px rgba(0,0,0,.28), inset 0 1px 0 rgba(255,255,255,.015) !important;
}
html.dark .tos-team-performance-flagship-v1 details[id*="disclosure"] > summary {
  background:
    radial-gradient(circle at 0 0, rgba(229,174,52,.06), transparent 24%),
    linear-gradient(180deg, #171a1e, #111418) !important;
}
html.dark .tos-team-performance-flagship-v1 details[id*="disclosure"][open] {
  border-color: rgba(239,185,58,.24) !important;
  box-shadow: 0 22px 54px rgba(0,0,0,.36), 0 0 30px rgba(220,157,25,.035), inset 0 1px 0 rgba(255,255,255,.018) !important;
}
html.dark .tos-team-performance-flagship-v1 details[id*="disclosure"] > summary > span:last-child {
  border-color: rgba(239,185,58,.20) !important;
  background: radial-gradient(circle at 36% 28%, #3d2d0c, #19150b 56%, #101214) !important;
  color: #efc45e !important;
}
html.dark .tos-team-performance-flagship-v1 thead th {
  color: #9aa4b1 !important;
  background: #111418 !important;
}
html.dark .tos-team-performance-flagship-v1 tbody tr:hover { background: rgba(255,255,255,.022) !important; }

@media (max-width: 900px) {
  .tos-team-performance-flagship-v1 .tos-premium-page-intro { min-height: auto; padding: 22px !important; }
  .tos-team-performance-flagship-v1 .tos-premium-page-intro h1 { font-size: 2rem !important; }
  .tos-team-performance-flagship-v1 .tos-tp-kpi-v1 { min-height: 138px; }
}

@media (prefers-reduced-motion: reduce) {
  .tos-team-performance-flagship-v1 *,
  .tos-team-performance-flagship-v1 *::before,
  .tos-team-performance-flagship-v1 *::after {
    transition-duration: .01ms !important;
    animation-duration: .01ms !important;
  }
}
'''

source_written = False
staging = None
old_live = None
try:
    PAGE.write_text(updated_page)
    STYLE.parent.mkdir(parents=True, exist_ok=True)
    STYLE.write_text(flagship_css)
    source_written = True

    build = subprocess.run(
        ["npm", "run", "build"],
        cwd=FRONTEND,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if build.returncode != 0:
        print(build.stdout[-10000:])
        raise RuntimeError("frontend build failed")

    if not DIST.exists():
        raise RuntimeError("frontend dist missing after build")

    dist_runtime = tree_count(DIST, RUNTIME_MARKER.encode())
    dist_root = tree_count(DIST, ROOT_HOOK_TOKEN.encode())
    dist_kpi = tree_count(DIST, KPI_HOOK.encode())
    if dist_runtime < 1 or dist_root < 1 or dist_kpi < 1:
        raise RuntimeError("Team Performance V1 stable runtime markers missing from dist")

    ts = int(time.time())
    staging = LIVE_PARENT / f".build-phase04-4-team-performance-v1-staging-{ts}"
    old_live = LIVE_PARENT / f".build-phase04-4-team-performance-v1-before-{ts}"
    if staging.exists():
        shutil.rmtree(staging)
    shutil.copytree(DIST, staging)

    if LIVE.exists():
        LIVE.rename(old_live)
    staging.rename(LIVE)
    staging = None

    live_runtime = tree_count(LIVE, RUNTIME_MARKER.encode())
    live_root = tree_count(LIVE, ROOT_HOOK_TOKEN.encode())
    live_kpi = tree_count(LIVE, KPI_HOOK.encode())
    if live_runtime < 1 or live_root < 1 or live_kpi < 1:
        raise RuntimeError("Team Performance V1 stable runtime markers missing from live build")

    if old_live and old_live.exists():
        shutil.rmtree(old_live)
        old_live = None

    print("PASS/FAIL=PASS")
    print("BUILD_RESULT=PASS")
    print("LIVE_DEPLOY=PASS")
    print("V1_RUNTIME=YES")
    print("EXECUTIVE_CINEMATIC_HERO=YES")
    print("PERFORMANCE_COMMAND_DECK=YES")
    print("REPORTING_PERIOD_REFINED=YES")
    print("FILTER_COMMAND_SURFACE_REFINED=YES")
    print("EXECUTIVE_KPI_DECK=YES")
    print("KPI_JEWEL_MEDALLIONS=YES")
    print("MANAGEMENT_SUMMARY_REFINED=YES")
    print("EXECUTIVE_COMMAND_CENTER_REFINED=YES")
    print("DISCLOSURE_SYSTEM_REFINED=YES")
    print("EXECUTIVE_TABLE_LEDGER=YES")
    print("LIGHT_PORCELAIN_CHAMPAGNE=YES")
    print("DARK_OBSIDIAN_TITANIUM=YES")
    print("BUSINESS_LOGIC_CHANGED=NO")
    print(f"SOURCE_V1_ROOT_HOOK_COUNT={updated_page.count(ROOT_HOOK_TOKEN)}")
    print(f"SOURCE_V1_KPI_HOOK_COUNT={updated_page.count(KPI_HOOK)}")
    print(f"DIST_V1_RUNTIME_COUNT={dist_runtime}")
    print(f"DIST_V1_ROOT_HOOK_COUNT={dist_root}")
    print(f"DIST_V1_KPI_HOOK_COUNT={dist_kpi}")
    print(f"LIVE_V1_RUNTIME_COUNT={live_runtime}")
    print(f"LIVE_V1_ROOT_HOOK_COUNT={live_root}")
    print(f"LIVE_V1_KPI_HOOK_COUNT={live_kpi}")
    print(f"TEAM_PERFORMANCE_SHA256={sha256(PAGE)}")
    print(f"FLAGSHIP_CSS_SHA256={sha256(STYLE)}")
except Exception as exc:
    if source_written:
        PAGE.write_text(original_page)
        if style_existed:
            STYLE.write_text(original_style)
        else:
            STYLE.unlink(missing_ok=True)
    if staging and staging.exists():
        shutil.rmtree(staging, ignore_errors=True)
    if old_live and old_live.exists():
        if LIVE.exists():
            shutil.rmtree(LIVE, ignore_errors=True)
        old_live.rename(LIVE)
    fail(exc)
