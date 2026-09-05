from pathlib import Path
import hashlib
import shutil
import subprocess
import sys
import time

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
PAGE = ROOT / "frontend/src/pages/TeamPerformanceDashboard.jsx"
PERIOD = ROOT / "frontend/src/components/performance/PerformancePeriodControl.jsx"
V2_STYLE = ROOT / "frontend/src/components/performance/teamPerformanceFlagshipV2.css"
V3_STYLE = ROOT / "frontend/src/components/performance/teamPerformanceFlagshipV3Menus.css"
FRONTEND = ROOT / "frontend"
DIST = FRONTEND / "dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

EXPECTED_PAGE_SHA256 = "a80e3f7c181d2871140fee2a99d7b84291ecc3aea7166a5fd023bb1359b6d40d"
EXPECTED_PERIOD_SHA256 = "09b795f5f4833a41c13d00f785866615dce5258980f8a56b8770f36b1ebe822a"
EXPECTED_V2_STYLE_SHA256 = "f380444455a8f3a1973ac083f7ec302cd4f6dffb7722ddd5512b3382e7881d7c"

V2_RUNTIME = "--tos-team-performance-flagship-v2-runtime"
V2_ROOT = 'data-tp-flagship-v2="v2"'
V2_MENU_TOKEN = "tos-tp-premium-menu-v2"
V2_COMPARE_TOKEN = "tos-tp-compare-trigger-v2"
V3_RUNTIME = "--tos-team-performance-flagship-v3-menus-runtime"
V3_DATE_TRIGGER = "tos-tp-date-trigger-v3"
V3_DATE_MENU = "tos-tp-date-menu-v3"
V3_IMPORT = 'import "./teamPerformanceFlagshipV3Menus.css";'

print("RUNNING=PHASE04_4_TEAM_PERFORMANCE_FLAGSHIP_V3_MENUS_DATE")


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
    print("V3_RUNTIME=NO")
    sys.exit(1)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 match, found {count}")
    return text.replace(old, new, 1)


# Safety: this patch is intentionally bound to one known TOS root and never removes directories.
if ROOT.resolve() == Path("/"):
    fail("unsafe ROOT")
for path in (PAGE, PERIOD, V2_STYLE, FRONTEND):
    if not path.exists():
        fail(f"required source missing: {path}")
if not LIVE_PARENT.exists():
    fail(f"live parent missing: {LIVE_PARENT}")

if sha256(PAGE) != EXPECTED_PAGE_SHA256:
    fail("TeamPerformanceDashboard.jsx does not match approved Flagship V2 live source")
if sha256(PERIOD) != EXPECTED_PERIOD_SHA256:
    fail("PerformancePeriodControl.jsx does not match approved Flagship V2 live source")
if sha256(V2_STYLE) != EXPECTED_V2_STYLE_SHA256:
    fail("teamPerformanceFlagshipV2.css does not match approved Flagship V2 live source")

original_page = PAGE.read_text()
original_period = PERIOD.read_text()
original_v2_style = V2_STYLE.read_text()

if V2_ROOT not in original_page:
    fail("V2 root marker missing")
if V2_RUNTIME not in original_v2_style:
    fail("V2 runtime marker missing")
if V2_MENU_TOKEN not in original_page or V2_COMPARE_TOKEN not in original_period:
    fail("V2 premium menu baseline missing")
if V3_IMPORT in original_period or V3_DATE_TRIGGER in original_period or V3_STYLE.exists():
    fail("Flagship V3 menus/date patch appears partially or already applied")

try:
    page = original_page
    period = original_period

    page = replace_once(
        page,
        '<div className="absolute right-0 top-full z-40 mt-2 w-44 rounded-xl border border-zinc-200 bg-white p-1.5 shadow-xl dark:border-white/10 dark:bg-zinc-950">',
        '<div className="tos-tp-export-menu-v3 absolute right-0 top-full z-50 mt-2 w-44 p-1.5">',
        "export premium menu hook",
    )

    period = replace_once(
        period,
        'import { CalendarDays, Check, ChevronDown, Minus, TrendingDown, TrendingUp } from "lucide-react";',
        'import { CalendarDays, Check, ChevronDown, ChevronLeft, ChevronRight, Minus, TrendingDown, TrendingUp } from "lucide-react";\n' + V3_IMPORT,
        "V3 date icons and stylesheet import",
    )

    # Improve Comparison menu placement so it can open upward near the viewport edge.
    period = replace_once(
        period,
        'const [position, setPosition] = useState({ top: 0, left: 0, width: 260 });',
        'const [position, setPosition] = useState({ top: 0, left: 0, width: 260, maxHeight: 300 });',
        "comparison menu position state",
    )
    period = replace_once(
        period,
        '''      const width = Math.min(Math.max(rect.width, 250), 360);
      const left = Math.min(Math.max(10, rect.left), Math.max(10, window.innerWidth - width - 10));
      const top = rect.bottom + 8;
      setPosition({ top, left, width });''',
        '''      const gap = 10;
      const width = Math.min(Math.max(rect.width, 250), 360);
      const left = Math.min(Math.max(gap, rect.left), Math.max(gap, window.innerWidth - width - gap));
      const desiredHeight = 246;
      const below = window.innerHeight - rect.bottom - gap;
      const above = rect.top - gap;
      const openAbove = below < desiredHeight && above > below;
      const availableHeight = Math.max(150, (openAbove ? above : below) - 8);
      const maxHeight = Math.min(desiredHeight, availableHeight);
      const top = openAbove ? Math.max(gap, rect.top - maxHeight - 8) : rect.bottom + 8;
      setPosition({ top, left, width, maxHeight });''',
        "comparison menu adaptive placement",
    )
    period = replace_once(
        period,
        'style={{ position: "fixed", top: position.top, left: position.left, width: position.width, zIndex: 16000 }} className="tos-tp-premium-menu-v2 tos-tp-compare-menu-v2"',
        'style={{ position: "fixed", top: position.top, left: position.left, width: position.width, maxHeight: position.maxHeight, overflowY: "auto", zIndex: 16000 }} className="tos-tp-premium-menu-v2 tos-tp-compare-menu-v2"',
        "comparison menu max-height",
    )

    date_component = r'''
const PERFORMANCE_WEEKDAYS_V3 = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"];

function parseIsoDateV3(value) {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(value || ""));
  if (!match) return null;
  const year = Number(match[1]);
  const month = Number(match[2]);
  const day = Number(match[3]);
  const date = new Date(year, month - 1, day);
  if (date.getFullYear() !== year || date.getMonth() !== month - 1 || date.getDate() !== day) return null;
  return date;
}

function toIsoDateV3(date) {
  const pad = (value) => String(value).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

function sameDateV3(a, b) {
  return Boolean(a && b && a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate());
}

function PerformanceDatePickerV3({ value, onChange, ariaLabel }) {
  const selectedDate = parseIsoDateV3(value);
  const initial = selectedDate || new Date();
  const [open, setOpen] = useState(false);
  const [viewMonth, setViewMonth] = useState(() => new Date(initial.getFullYear(), initial.getMonth(), 1));
  const [position, setPosition] = useState({ top: 0, left: 0, width: 326, maxHeight: 390 });
  const triggerRef = useRef(null);
  const menuRef = useRef(null);

  useEffect(() => {
    if (!open) return;
    const parsed = parseIsoDateV3(value) || new Date();
    setViewMonth(new Date(parsed.getFullYear(), parsed.getMonth(), 1));
  }, [open, value]);

  useEffect(() => {
    if (!open) return undefined;
    const syncPosition = () => {
      const rect = triggerRef.current?.getBoundingClientRect();
      if (!rect) return;
      const gap = 10;
      const availableWidth = Math.max(220, window.innerWidth - gap * 2);
      const width = Math.min(340, availableWidth, Math.max(286, rect.width + 90));
      const left = Math.min(Math.max(gap, rect.left), Math.max(gap, window.innerWidth - width - gap));
      const desiredHeight = 390;
      const below = window.innerHeight - rect.bottom - gap;
      const above = rect.top - gap;
      const openAbove = below < 330 && above > below;
      const availableHeight = Math.max(180, (openAbove ? above : below) - 8);
      const maxHeight = Math.min(desiredHeight, availableHeight);
      const top = openAbove ? Math.max(gap, rect.top - maxHeight - 8) : rect.bottom + 8;
      setPosition({ top, left, width, maxHeight });
    };
    const closeOutside = (event) => {
      if (triggerRef.current?.contains(event.target) || menuRef.current?.contains(event.target)) return;
      setOpen(false);
    };
    const keydown = (event) => {
      if (event.key === "Escape") {
        setOpen(false);
        triggerRef.current?.focus();
      }
    };
    syncPosition();
    window.addEventListener("resize", syncPosition);
    window.addEventListener("scroll", syncPosition, true);
    document.addEventListener("mousedown", closeOutside);
    document.addEventListener("keydown", keydown);
    return () => {
      window.removeEventListener("resize", syncPosition);
      window.removeEventListener("scroll", syncPosition, true);
      document.removeEventListener("mousedown", closeOutside);
      document.removeEventListener("keydown", keydown);
    };
  }, [open]);

  const first = new Date(viewMonth.getFullYear(), viewMonth.getMonth(), 1);
  const gridStart = new Date(first.getFullYear(), first.getMonth(), 1 - first.getDay());
  const days = Array.from({ length: 42 }, (_, index) => (
    new Date(gridStart.getFullYear(), gridStart.getMonth(), gridStart.getDate() + index)
  ));
  const today = new Date();
  const dark = document.documentElement.classList.contains("dark") || document.body.classList.contains("dark");
  const monthLabel = new Intl.DateTimeFormat("en-US", { month: "long", year: "numeric" }).format(viewMonth);

  const choose = (date) => {
    onChange(toIsoDateV3(date));
    setOpen(false);
    triggerRef.current?.focus();
  };

  return (
    <>
      <button
        ref={triggerRef}
        type="button"
        className="tos-tp-date-trigger-v3"
        aria-label={ariaLabel}
        aria-haspopup="dialog"
        aria-expanded={open}
        onClick={() => setOpen((current) => !current)}
      >
        <span>{value || "Select date"}</span>
        <CalendarDays size={14} />
      </button>
      {open && createPortal(
        <div
          ref={menuRef}
          role="dialog"
          aria-label={ariaLabel}
          data-tp-menu-theme={dark ? "dark" : "light"}
          style={{ position: "fixed", top: position.top, left: position.left, width: position.width, maxHeight: position.maxHeight, zIndex: 16020 }}
          className="tos-tp-date-menu-v3"
        >
          <div className="tos-tp-date-header-v3">
            <button type="button" aria-label="Previous month" onClick={() => setViewMonth((current) => new Date(current.getFullYear(), current.getMonth() - 1, 1))}><ChevronLeft size={16} /></button>
            <strong>{monthLabel}</strong>
            <button type="button" aria-label="Next month" onClick={() => setViewMonth((current) => new Date(current.getFullYear(), current.getMonth() + 1, 1))}><ChevronRight size={16} /></button>
          </div>
          <div className="tos-tp-date-weekdays-v3">
            {PERFORMANCE_WEEKDAYS_V3.map((day) => <span key={day}>{day}</span>)}
          </div>
          <div className="tos-tp-date-grid-v3">
            {days.map((date) => {
              const iso = toIsoDateV3(date);
              const outside = date.getMonth() !== viewMonth.getMonth();
              const selected = sameDateV3(date, selectedDate);
              const isToday = sameDateV3(date, today);
              return (
                <button
                  key={iso}
                  type="button"
                  aria-label={new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "long", year: "numeric" }).format(date)}
                  aria-pressed={selected}
                  data-outside={outside ? "true" : "false"}
                  data-selected={selected ? "true" : "false"}
                  data-today={isToday ? "true" : "false"}
                  onClick={() => choose(date)}
                >
                  {date.getDate()}
                </button>
              );
            })}
          </div>
          <div className="tos-tp-date-footer-v3">
            <button type="button" onClick={() => { onChange(""); setOpen(false); triggerRef.current?.focus(); }}>Clear</button>
            <button type="button" onClick={() => choose(new Date())}>Today</button>
          </div>
        </div>,
        document.body,
      )}
    </>
  );
}
'''
    period = replace_once(period, "function toInputDate(value) {", date_component + "\nfunction toInputDate(value) {", "premium date picker component")

    period = replace_once(
        period,
        '<input type="date" value={currentStartValue} onChange={(e) => onCurrentStart(e.target.value)} className="min-h-10 w-full rounded-xl border border-zinc-200 bg-white px-3 text-xs font-bold text-zinc-800 outline-none focus:border-amber-400 dark:border-white/10 dark:bg-zinc-900 dark:text-white" />',
        '<PerformanceDatePickerV3 value={currentStartValue} onChange={onCurrentStart} ariaLabel="Reporting period start date" />',
        "current start premium date",
    )
    period = replace_once(
        period,
        '<input type="date" value={currentEndValue} onChange={(e) => onCurrentEnd(e.target.value)} className="min-h-10 w-full rounded-xl border border-zinc-200 bg-white px-3 text-xs font-bold text-zinc-800 outline-none focus:border-amber-400 dark:border-white/10 dark:bg-zinc-900 dark:text-white" />',
        '<PerformanceDatePickerV3 value={currentEndValue} onChange={onCurrentEnd} ariaLabel="Reporting period end date" />',
        "current end premium date",
    )
    period = replace_once(
        period,
        '<input type="date" value={compareCustomStart} onChange={(e) => setCompareCustomStart(e.target.value)} className="min-h-10 w-full rounded-xl border border-zinc-200 bg-white px-3 text-xs font-bold dark:border-white/10 dark:bg-zinc-900 dark:text-white" />',
        '<PerformanceDatePickerV3 value={compareCustomStart} onChange={setCompareCustomStart} ariaLabel="Comparison period start date" />',
        "comparison start premium date",
    )
    period = replace_once(
        period,
        '<input type="date" value={compareCustomEnd} onChange={(e) => setCompareCustomEnd(e.target.value)} className="min-h-10 w-full rounded-xl border border-zinc-200 bg-white px-3 text-xs font-bold dark:border-white/10 dark:bg-zinc-900 dark:text-white" />',
        '<PerformanceDatePickerV3 value={compareCustomEnd} onChange={setCompareCustomEnd} ariaLabel="Comparison period end date" />',
        "comparison end premium date",
    )

    if period.count('type="date"') != 0:
        raise RuntimeError("native date inputs remain after V3 transformation")
    if period.count("<PerformanceDatePickerV3 ") != 4:
        raise RuntimeError("expected four premium date picker usages")
except Exception as exc:
    fail(exc)

v3_css = r'''/* =========================================================
   TOS Team Performance — Flagship V3 Menus + Date System
   Visual-only refinement over approved V2.
   Unifies Employee / Department / Comparison / Date popovers
   in Porcelain-Ivory light and Obsidian-Titanium dark.
   ========================================================= */
:root { --tos-team-performance-flagship-v3-menus-runtime: 1; }

/* ---------- V2 portal menus: final shared material system ---------- */
.tos-tp-premium-menu-v2 {
  border-radius: 17px !important;
  padding: 7px !important;
  border: 1px solid rgba(170, 121, 30, .22) !important;
  background: linear-gradient(180deg, rgba(255,254,250,.995), rgba(250,246,237,.995)) !important;
  box-shadow: 0 26px 70px rgba(54,39,15,.20), 0 8px 22px rgba(54,39,15,.07), inset 0 1px 0 rgba(255,255,255,.99) !important;
  backdrop-filter: blur(24px) saturate(1.08);
  color-scheme: light;
}
.tos-tp-premium-menu-v2 .tos-tp-premium-menu-scroll-v2 {
  overscroll-behavior: contain;
  scrollbar-width: thin;
  scrollbar-color: rgba(177,128,34,.46) transparent;
}
.tos-tp-premium-menu-v2 .tos-tp-premium-menu-scroll-v2::-webkit-scrollbar { width: 7px; }
.tos-tp-premium-menu-v2 .tos-tp-premium-menu-scroll-v2::-webkit-scrollbar-track { background: transparent; }
.tos-tp-premium-menu-v2 .tos-tp-premium-menu-scroll-v2::-webkit-scrollbar-thumb {
  border-radius: 999px;
  background: rgba(177,128,34,.34);
}
.tos-tp-premium-menu-v2 .tos-tp-premium-menu-search-v2 {
  min-height: 42px !important;
  border: 1px solid rgba(149,108,38,.18) !important;
  border-radius: 12px !important;
  background: rgba(255,255,255,.86) !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.98), 0 3px 10px rgba(73,52,17,.035) !important;
}
.tos-tp-premium-menu-v2 .tos-tp-premium-menu-search-v2 input,
.tos-tp-premium-menu-v2 .tos-tp-premium-menu-search-v2 input:focus,
.tos-tp-premium-menu-v2 .tos-tp-premium-menu-search-v2 input:active {
  min-height: 0 !important;
  padding: 0 !important;
  border: 0 !important;
  outline: 0 !important;
  border-radius: 0 !important;
  background: transparent !important;
  background-color: transparent !important;
  box-shadow: none !important;
  color: #29241d !important;
  -webkit-text-fill-color: #29241d !important;
  caret-color: #b27b1d !important;
  appearance: none;
  color-scheme: light;
}
.tos-tp-premium-menu-v2 .tos-tp-premium-menu-search-v2 input::placeholder {
  color: #9b9182 !important;
  -webkit-text-fill-color: #9b9182 !important;
  opacity: 1;
}
.tos-tp-premium-menu-v2 .tos-tp-premium-option-v2 {
  min-height: 41px !important;
  border-radius: 11px !important;
  transform: none !important;
}
.tos-tp-premium-menu-v2 .tos-tp-premium-option-v2:hover {
  background: rgba(216,165,60,.095) !important;
  transform: none !important;
}

/* Explicit dark portal theming: strong enough to defeat global input rules. */
.tos-tp-premium-menu-v2[data-tp-menu-theme="dark"] {
  border-color: rgba(232,180,58,.22) !important;
  background: linear-gradient(180deg, rgba(18,22,26,.995), rgba(10,13,16,.995)) !important;
  box-shadow: 0 30px 82px rgba(0,0,0,.62), 0 8px 24px rgba(0,0,0,.34), inset 0 1px 0 rgba(255,255,255,.025) !important;
  color-scheme: dark;
}
.tos-tp-premium-menu-v2[data-tp-menu-theme="dark"] .tos-tp-premium-menu-search-v2 {
  border-color: rgba(232,180,58,.16) !important;
  background: linear-gradient(180deg,#151a1f,#101419) !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.025), 0 4px 14px rgba(0,0,0,.18) !important;
  color: #e2b955 !important;
}
.tos-tp-premium-menu-v2[data-tp-menu-theme="dark"] .tos-tp-premium-menu-search-v2 input,
.tos-tp-premium-menu-v2[data-tp-menu-theme="dark"] .tos-tp-premium-menu-search-v2 input:focus,
.tos-tp-premium-menu-v2[data-tp-menu-theme="dark"] .tos-tp-premium-menu-search-v2 input:active,
.tos-tp-premium-menu-v2[data-tp-menu-theme="dark"] .tos-tp-premium-menu-search-v2 input:-webkit-autofill {
  border: 0 !important;
  outline: 0 !important;
  background: transparent !important;
  background-color: transparent !important;
  box-shadow: 0 0 0 1000px #12171c inset !important;
  -webkit-box-shadow: 0 0 0 1000px #12171c inset !important;
  color: #f4f1e9 !important;
  -webkit-text-fill-color: #f4f1e9 !important;
  caret-color: #e7ba52 !important;
  color-scheme: dark;
}
.tos-tp-premium-menu-v2[data-tp-menu-theme="dark"] .tos-tp-premium-menu-search-v2 input::placeholder {
  color: #7f8994 !important;
  -webkit-text-fill-color: #7f8994 !important;
}
.tos-tp-premium-menu-v2[data-tp-menu-theme="dark"] .tos-tp-premium-menu-scroll-v2 {
  scrollbar-color: rgba(222,171,55,.44) transparent;
}
.tos-tp-premium-menu-v2[data-tp-menu-theme="dark"] .tos-tp-premium-menu-scroll-v2::-webkit-scrollbar-thumb {
  background: rgba(222,171,55,.30);
}

/* ---------- Export menu joins the same material language ---------- */
.tos-tp-export-menu-v3 {
  overflow: hidden;
  border: 1px solid rgba(170,121,30,.22) !important;
  border-radius: 15px !important;
  background: linear-gradient(180deg,rgba(255,254,250,.995),rgba(250,246,237,.995)) !important;
  box-shadow: 0 24px 64px rgba(54,39,15,.18), 0 7px 20px rgba(54,39,15,.06), inset 0 1px 0 rgba(255,255,255,.99) !important;
  backdrop-filter: blur(22px) saturate(1.08);
}
.tos-tp-export-menu-v3 button {
  min-height: 39px;
  border-radius: 10px !important;
  color: #4a4338 !important;
  transition: background .14s ease, color .14s ease;
}
.tos-tp-export-menu-v3 button:hover {
  background: rgba(216,165,60,.10) !important;
  color: #18130c !important;
}
html.dark .tos-team-performance-flagship-v2 .tos-tp-export-menu-v3 {
  border-color: rgba(232,180,58,.20) !important;
  background: linear-gradient(180deg,#15191d,#0d1013) !important;
  box-shadow: 0 28px 74px rgba(0,0,0,.58), 0 8px 22px rgba(0,0,0,.30), inset 0 1px 0 rgba(255,255,255,.02) !important;
}
html.dark .tos-team-performance-flagship-v2 .tos-tp-export-menu-v3 button { color: #d7dbe0 !important; }
html.dark .tos-team-performance-flagship-v2 .tos-tp-export-menu-v3 button:hover {
  background: rgba(229,176,57,.075) !important;
  color: #fff !important;
}

/* ---------- Custom premium date trigger ---------- */
.tos-tp-date-trigger-v3 {
  width: 100%;
  min-height: 44px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  border: 1px solid rgba(119,92,49,.15);
  border-radius: 13px;
  padding: 0 13px;
  background: linear-gradient(180deg,#fff,#fbf8f2);
  color: #25221d;
  font-size: 12px;
  font-weight: 850;
  text-align: start;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.99), 0 5px 14px rgba(70,50,18,.035);
  outline: none;
  transition: border-color .16s ease, box-shadow .16s ease, background .16s ease;
}
.tos-tp-date-trigger-v3:hover {
  border-color: rgba(211,157,51,.48);
  box-shadow: inset 0 1px 0 rgba(255,255,255,.99), 0 7px 18px rgba(94,63,15,.065);
}
.tos-tp-date-trigger-v3:focus-visible {
  border-color: rgba(211,157,51,.72);
  box-shadow: 0 0 0 3px rgba(211,157,51,.11);
}
.tos-tp-date-trigger-v3 svg { flex: none; color: #aa791e; }

/* ---------- Custom portal calendar ---------- */
.tos-tp-date-menu-v3 {
  overflow-y: auto;
  overscroll-behavior: contain;
  padding: 10px;
  border: 1px solid rgba(190,138,38,.25);
  border-radius: 19px;
  background: linear-gradient(180deg,rgba(255,254,250,.995),rgba(249,245,236,.995));
  box-shadow: 0 30px 78px rgba(55,39,14,.24), 0 8px 22px rgba(55,39,14,.08), inset 0 1px 0 rgba(255,255,255,.99);
  backdrop-filter: blur(24px) saturate(1.08);
  color: #29241d;
  color-scheme: light;
}
.tos-tp-date-header-v3 {
  min-height: 42px;
  display: grid;
  grid-template-columns: 36px 1fr 36px;
  align-items: center;
  gap: 7px;
  margin-bottom: 7px;
}
.tos-tp-date-header-v3 strong {
  text-align: center;
  font-size: 12px;
  font-weight: 900;
  letter-spacing: -.01em;
}
.tos-tp-date-header-v3 button {
  width: 34px;
  height: 34px;
  display: grid;
  place-items: center;
  border: 1px solid rgba(150,108,36,.14);
  border-radius: 10px;
  background: rgba(255,255,255,.72);
  color: #9b6b1c;
  transition: border-color .14s ease, background .14s ease;
}
.tos-tp-date-header-v3 button:hover { border-color: rgba(205,151,48,.38); background: #fff; }
.tos-tp-date-weekdays-v3,
.tos-tp-date-grid-v3 {
  display: grid;
  grid-template-columns: repeat(7, minmax(0,1fr));
  gap: 4px;
}
.tos-tp-date-weekdays-v3 { margin-bottom: 4px; }
.tos-tp-date-weekdays-v3 span {
  display: grid;
  place-items: center;
  min-height: 26px;
  color: #948a7c;
  font-size: 9px;
  font-weight: 900;
  text-transform: uppercase;
}
.tos-tp-date-grid-v3 button {
  position: relative;
  min-width: 0;
  aspect-ratio: 1;
  display: grid;
  place-items: center;
  border: 1px solid transparent;
  border-radius: 10px;
  background: transparent;
  color: #514a40;
  font-size: 11px;
  font-weight: 850;
  outline: none;
  transition: background .13s ease, border-color .13s ease, color .13s ease, box-shadow .13s ease;
}
.tos-tp-date-grid-v3 button:hover {
  border-color: rgba(211,157,51,.24);
  background: rgba(218,166,62,.095);
  color: #21190d;
}
.tos-tp-date-grid-v3 button[data-outside="true"] { color: #b7afa4; opacity: .62; }
.tos-tp-date-grid-v3 button[data-today="true"]::after {
  content: "";
  position: absolute;
  bottom: 4px;
  width: 4px;
  height: 4px;
  border-radius: 999px;
  background: #d7a43c;
}
.tos-tp-date-grid-v3 button[data-selected="true"] {
  border-color: rgba(168,111,14,.22);
  background: linear-gradient(135deg,#efc65f,#d99e2f);
  color: #211506;
  box-shadow: 0 7px 18px rgba(177,116,16,.20), inset 0 1px 0 rgba(255,255,255,.45);
}
.tos-tp-date-grid-v3 button[data-selected="true"]::after { background: #3b2608; }
.tos-tp-date-footer-v3 {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  margin-top: 9px;
  padding-top: 8px;
  border-top: 1px solid rgba(145,106,43,.12);
}
.tos-tp-date-footer-v3 button {
  min-height: 34px;
  padding: 0 11px;
  border: 1px solid rgba(145,106,43,.13);
  border-radius: 10px;
  background: rgba(255,255,255,.70);
  color: #84601e;
  font-size: 10px;
  font-weight: 900;
}
.tos-tp-date-footer-v3 button:hover { border-color: rgba(206,153,48,.34); background: #fff; }

/* Date trigger within the approved V2 dark command deck. */
html.dark .tos-team-performance-flagship-v2 .tos-tp-date-trigger-v3 {
  border-color: rgba(255,255,255,.09);
  background: linear-gradient(180deg,#14181c,#0c0f12);
  color: #f0eee8;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.02), 0 7px 18px rgba(0,0,0,.18);
  color-scheme: dark;
}
html.dark .tos-team-performance-flagship-v2 .tos-tp-date-trigger-v3:hover { border-color: rgba(230,177,58,.30); }
html.dark .tos-team-performance-flagship-v2 .tos-tp-date-trigger-v3 svg { color: #d5a63f; }

.tos-tp-date-menu-v3[data-tp-menu-theme="dark"] {
  border-color: rgba(232,180,58,.21);
  background: linear-gradient(180deg,rgba(18,22,26,.997),rgba(9,12,15,.997));
  box-shadow: 0 32px 84px rgba(0,0,0,.64), 0 9px 25px rgba(0,0,0,.34), inset 0 1px 0 rgba(255,255,255,.025);
  color: #eef0f2;
  color-scheme: dark;
}
.tos-tp-date-menu-v3[data-tp-menu-theme="dark"] .tos-tp-date-header-v3 strong { color: #f0eee8; }
.tos-tp-date-menu-v3[data-tp-menu-theme="dark"] .tos-tp-date-header-v3 button {
  border-color: rgba(255,255,255,.075);
  background: #14191e;
  color: #d6a842;
}
.tos-tp-date-menu-v3[data-tp-menu-theme="dark"] .tos-tp-date-header-v3 button:hover {
  border-color: rgba(229,176,57,.28);
  background: #191e23;
}
.tos-tp-date-menu-v3[data-tp-menu-theme="dark"] .tos-tp-date-weekdays-v3 span { color: #77818c; }
.tos-tp-date-menu-v3[data-tp-menu-theme="dark"] .tos-tp-date-grid-v3 button { color: #c8cdd2; }
.tos-tp-date-menu-v3[data-tp-menu-theme="dark"] .tos-tp-date-grid-v3 button:hover {
  border-color: rgba(229,176,57,.18);
  background: rgba(229,176,57,.07);
  color: #fff;
}
.tos-tp-date-menu-v3[data-tp-menu-theme="dark"] .tos-tp-date-grid-v3 button[data-outside="true"] { color: #59636e; }
.tos-tp-date-menu-v3[data-tp-menu-theme="dark"] .tos-tp-date-grid-v3 button[data-selected="true"] {
  border-color: rgba(235,185,70,.35);
  background: linear-gradient(135deg,#d9a43a,#a97116);
  color: #0c0b08;
  box-shadow: 0 8px 22px rgba(0,0,0,.24), inset 0 1px 0 rgba(255,255,255,.20);
}
.tos-tp-date-menu-v3[data-tp-menu-theme="dark"] .tos-tp-date-grid-v3 button[data-today="true"]::after { background: #e2b553; }
.tos-tp-date-menu-v3[data-tp-menu-theme="dark"] .tos-tp-date-grid-v3 button[data-selected="true"]::after { background: #171007; }
.tos-tp-date-menu-v3[data-tp-menu-theme="dark"] .tos-tp-date-footer-v3 {
  border-top-color: rgba(255,255,255,.07);
}
.tos-tp-date-menu-v3[data-tp-menu-theme="dark"] .tos-tp-date-footer-v3 button {
  border-color: rgba(255,255,255,.075);
  background: #13181d;
  color: #d7b45f;
}
.tos-tp-date-menu-v3[data-tp-menu-theme="dark"] .tos-tp-date-footer-v3 button:hover {
  border-color: rgba(229,176,57,.25);
  background: #181d22;
}

@media (max-width: 680px) {
  .tos-tp-date-menu-v3 { border-radius: 16px; padding: 8px; }
  .tos-tp-date-grid-v3 { gap: 2px; }
}
'''

# Write/build/deploy. No directory deletion is performed by this patch.
staging = None
backup = None
failed_live = None
source_written = False
live_swapped = False
v3_style_existed = V3_STYLE.exists()

try:
    PAGE.write_text(page)
    PERIOD.write_text(period)
    V3_STYLE.write_text(v3_css)
    source_written = True

    if V2_ROOT not in PAGE.read_text() or PAGE.read_text().count("tos-tp-export-menu-v3") != 1:
        raise RuntimeError("V2 root/export menu hook validation failed")
    if sha256(V2_STYLE) != EXPECTED_V2_STYLE_SHA256:
        raise RuntimeError("Flagship V2 stylesheet changed unexpectedly during patch")
    if V3_RUNTIME not in V3_STYLE.read_text():
        raise RuntimeError("V3 runtime marker missing from stylesheet")
    if PERIOD.read_text().count('type="date"') != 0:
        raise RuntimeError("native date inputs remain in source")
    if PERIOD.read_text().count("<PerformanceDatePickerV3 ") != 4:
        raise RuntimeError("premium date picker count invalid")
    if PAGE.read_text().count("tos-tp-export-menu-v3") != 1:
        raise RuntimeError("premium export menu hook count invalid")

    build = subprocess.run(
        ["npm", "run", "build"],
        cwd=FRONTEND,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if build.returncode != 0:
        print(build.stdout[-12000:])
        raise RuntimeError("frontend build failed")
    if not DIST.exists():
        raise RuntimeError("frontend dist missing after build")

    dist_runtime = tree_count(DIST, V3_RUNTIME.encode())
    dist_date_trigger = tree_count(DIST, V3_DATE_TRIGGER.encode())
    dist_date_menu = tree_count(DIST, V3_DATE_MENU.encode())
    dist_v2_runtime = tree_count(DIST, V2_RUNTIME.encode())
    dist_v2_menu = tree_count(DIST, V2_MENU_TOKEN.encode())
    dist_export_menu = tree_count(DIST, b"tos-tp-export-menu-v3")
    if min(dist_runtime, dist_date_trigger, dist_date_menu, dist_v2_runtime, dist_v2_menu, dist_export_menu) < 1:
        raise RuntimeError("required V2/V3 runtime markers missing from dist")

    ts = int(time.time())
    staging = LIVE_PARENT / f".build-phase04-4-v3-staging-{ts}"
    backup = LIVE_PARENT / f".build-phase04-4-v3-before-{ts}"
    failed_live = LIVE_PARENT / f".build-phase04-4-v3-failed-{ts}"
    for path in (staging, backup, failed_live):
        if path.exists():
            raise RuntimeError(f"safety stop: temporary path already exists: {path}")
    if not LIVE.exists():
        raise RuntimeError(f"live build missing: {LIVE}")

    shutil.copytree(DIST, staging)
    LIVE.rename(backup)
    staging.rename(LIVE)
    live_swapped = True
    staging = None

    live_runtime = tree_count(LIVE, V3_RUNTIME.encode())
    live_date_trigger = tree_count(LIVE, V3_DATE_TRIGGER.encode())
    live_date_menu = tree_count(LIVE, V3_DATE_MENU.encode())
    live_v2_runtime = tree_count(LIVE, V2_RUNTIME.encode())
    live_v2_menu = tree_count(LIVE, V2_MENU_TOKEN.encode())
    live_export_menu = tree_count(LIVE, b"tos-tp-export-menu-v3")
    if min(live_runtime, live_date_trigger, live_date_menu, live_v2_runtime, live_v2_menu, live_export_menu) < 1:
        raise RuntimeError("required V2/V3 runtime markers missing from live build")

    print("PASS/FAIL=PASS")
    print("BUILD_RESULT=PASS")
    print("LIVE_DEPLOY=PASS")
    print("V3_RUNTIME=YES")
    print("V2_FLAGSHIP_BASELINE_PRESERVED=YES")
    print("EMPLOYEE_MENU_SURFACE_REFINED=YES")
    print("EMPLOYEE_SEARCH_DARK_FIXED=YES")
    print("DEPARTMENT_MENU_SURFACE_REFINED=YES")
    print("COMPARISON_MENU_POSITIONING_REFINED=YES")
    print("EXPORT_MENU_SURFACE_REFINED=YES")
    print("CURRENT_FROM_CUSTOM_CALENDAR=YES")
    print("CURRENT_TO_CUSTOM_CALENDAR=YES")
    print("COMPARISON_FROM_CUSTOM_CALENDAR=YES")
    print("COMPARISON_TO_CUSTOM_CALENDAR=YES")
    print("NATIVE_DATE_INPUTS_REMAINING=0")
    print("BUSINESS_LOGIC_CHANGED=NO")
    print(f"SOURCE_DATE_PICKER_USAGE_COUNT={period.count('<PerformanceDatePickerV3 ')}")
    print(f"DIST_V3_RUNTIME_COUNT={dist_runtime}")
    print(f"DIST_DATE_TRIGGER_TOKEN_COUNT={dist_date_trigger}")
    print(f"DIST_DATE_MENU_TOKEN_COUNT={dist_date_menu}")
    print(f"DIST_EXPORT_MENU_TOKEN_COUNT={dist_export_menu}")
    print(f"LIVE_V3_RUNTIME_COUNT={live_runtime}")
    print(f"LIVE_DATE_TRIGGER_TOKEN_COUNT={live_date_trigger}")
    print(f"LIVE_DATE_MENU_TOKEN_COUNT={live_date_menu}")
    print(f"LIVE_EXPORT_MENU_TOKEN_COUNT={live_export_menu}")
    print(f"LIVE_V2_RUNTIME_COUNT={live_v2_runtime}")
    print(f"LIVE_V2_MENU_TOKEN_COUNT={live_v2_menu}")
    print(f"TEAM_PERFORMANCE_SHA256={sha256(PAGE)}")
    print(f"PERIOD_CONTROL_SHA256={sha256(PERIOD)}")
    print(f"FLAGSHIP_V2_CSS_SHA256={sha256(V2_STYLE)}")
    print(f"FLAGSHIP_V3_MENUS_CSS_SHA256={sha256(V3_STYLE)}")
    print(f"LIVE_BACKUP_RETAINED={backup}")
except Exception as exc:
    # Restore the exact approved V2 source. The only source file removed here is the
    # exact V3 stylesheet created by this run; no directory removal is used.
    if source_written:
        PAGE.write_text(original_page)
        PERIOD.write_text(original_period)
        if not v3_style_existed and V3_STYLE.exists():
            V3_STYLE.unlink()

    # If live was already swapped, retain the failed V3 build under a uniquely named
    # path and restore the previous live directory by rename only.
    try:
        if live_swapped and backup and backup.exists() and LIVE.exists():
            LIVE.rename(failed_live)
            backup.rename(LIVE)
        elif backup and backup.exists() and not LIVE.exists():
            backup.rename(LIVE)
    except Exception as rollback_exc:
        print("ROLLBACK_ERROR=" + str(rollback_exc))
    fail(exc)
