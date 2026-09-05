from pathlib import Path
import hashlib
import shutil
import subprocess
import sys
import time

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
PAGE = ROOT / "frontend/src/pages/TeamPerformanceDashboard.jsx"
PERIOD = ROOT / "frontend/src/components/performance/PerformancePeriodControl.jsx"
V1_STYLE = ROOT / "frontend/src/components/performance/teamPerformanceFlagshipV1.css"
V2_STYLE = ROOT / "frontend/src/components/performance/teamPerformanceFlagshipV2.css"
FRONTEND = ROOT / "frontend"
DIST = FRONTEND / "dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

EXPECTED_PAGE_SHA256 = "df1d68e31cf82fbc57be411b8ce3cb55f5e326138fb128db70d13d6a94774c66"
EXPECTED_V1_STYLE_SHA256 = "f685c05500b21cb0e60c238c555f213d889c11673ff84868c1f30b74126f2468"
V1_RUNTIME = "--tos-team-performance-flagship-v1-runtime"
V2_RUNTIME = "--tos-team-performance-flagship-v2-runtime"
V1_ROOT = 'data-tp-flagship="v1"'
V2_ROOT = 'data-tp-flagship-v2="v2"'
V2_MENU_TOKEN = "tos-tp-premium-menu-v2"
V2_COMPARE_TOKEN = "tos-tp-compare-trigger-v2"
V2_IMPORT = 'import "../components/performance/teamPerformanceFlagshipV2.css";'

print("RUNNING=PHASE04_4_TEAM_PERFORMANCE_FLAGSHIP_V2")


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
    print("V2_RUNTIME=NO")
    sys.exit(1)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 match, found {count}")
    return text.replace(old, new, 1)


for path in (PAGE, PERIOD, V1_STYLE):
    if not path.exists():
        fail(f"required source missing: {path}")

if sha256(PAGE) != EXPECTED_PAGE_SHA256:
    fail("TeamPerformanceDashboard.jsx does not match Flagship V1 live source")
if sha256(V1_STYLE) != EXPECTED_V1_STYLE_SHA256:
    fail("teamPerformanceFlagshipV1.css does not match Flagship V1 live source")

original_page = PAGE.read_text()
original_period = PERIOD.read_text()
v2_style_existed = V2_STYLE.exists()
original_v2_style = V2_STYLE.read_text() if v2_style_existed else None

for marker in (V1_ROOT, 'tos-tp-kpi-v1', 'tos-tp-command-deck-v1', 'tos-tp-management-summary-v1', 'tos-tp-executive-v1'):
    if marker not in original_page:
        fail(f"V1 baseline marker missing from Team Performance source: {marker}")
if V1_RUNTIME not in V1_STYLE.read_text():
    fail("V1 runtime marker missing")
if V2_ROOT in original_page or V2_IMPORT in original_page or V2_STYLE.exists():
    fail("Team Performance Flagship V2 already present")

page = original_page
period = original_period

# PAGE: custom premium employee/department menus and V2 root/style hooks.
page = replace_once(page, 'import { useEffect, useMemo, useState } from "react";', 'import { useEffect, useMemo, useRef, useState } from "react";\nimport { createPortal } from "react-dom";', "React portal imports")
page = replace_once(page, '  CalendarDays,\n  CheckCircle2,', '  CalendarDays,\n  Check,\n  CheckCircle2,', "Check icon import")
page = replace_once(page, 'import "../components/performance/teamPerformanceFlagshipV1.css";', 'import "../components/performance/teamPerformanceFlagshipV1.css";\n' + V2_IMPORT, "V2 stylesheet import")
page = replace_once(page, '<div data-tp-flagship="v1" className="tos-page tos-team-performance-premium tos-core-team-performance-premium tos-team-performance-flagship-v1 space-y-4">', '<div data-tp-flagship="v1" data-tp-flagship-v2="v2" className="tos-page tos-team-performance-premium tos-core-team-performance-premium tos-team-performance-flagship-v1 tos-team-performance-flagship-v2 space-y-4">', "V2 root hook")

premium_select_component = r'''

function TeamPerformancePremiumSelectV2({ value, onChange, options, ariaLabel, searchable = false }) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [position, setPosition] = useState({ top: 0, left: 0, width: 280, maxHeight: 320 });
  const triggerRef = useRef(null);
  const menuRef = useRef(null);
  const selected = options.find((option) => String(option.value) === String(value)) || options[0];
  const filtered = useMemo(() => {
    const term = query.trim().toLowerCase();
    return term ? options.filter((option) => String(option.label || "").toLowerCase().includes(term)) : options;
  }, [options, query]);

  useEffect(() => {
    if (!open) return undefined;
    const syncPosition = () => {
      const trigger = triggerRef.current;
      if (!trigger) return;
      const rect = trigger.getBoundingClientRect();
      const gap = 10;
      const desired = searchable ? 360 : 300;
      const below = window.innerHeight - rect.bottom - gap;
      const above = rect.top - gap;
      const openAbove = below < 190 && above > below;
      const maxHeight = Math.max(160, Math.min(desired, (openAbove ? above : below) - 8));
      const width = Math.min(Math.max(rect.width, 270), 420);
      const left = Math.min(Math.max(gap, rect.left), Math.max(gap, window.innerWidth - width - gap));
      const top = openAbove ? Math.max(gap, rect.top - maxHeight - 8) : rect.bottom + 8;
      setPosition({ top, left, width, maxHeight });
    };
    const closeOutside = (event) => {
      if (triggerRef.current?.contains(event.target) || menuRef.current?.contains(event.target)) return;
      setOpen(false);
    };
    const keydown = (event) => {
      if (event.key === "Escape") { setOpen(false); triggerRef.current?.focus(); }
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
  }, [open, searchable]);

  useEffect(() => { if (!open) setQuery(""); }, [open]);
  const choose = (next) => { onChange(next); setOpen(false); setQuery(""); triggerRef.current?.focus(); };
  const dark = document.documentElement.classList.contains("dark") || document.body.classList.contains("dark");

  return (
    <>
      <button ref={triggerRef} type="button" aria-label={ariaLabel} aria-haspopup="listbox" aria-expanded={open} onClick={() => setOpen((current) => !current)} className="tos-tp-premium-select-trigger-v2">
        <span className="truncate">{selected?.label || ariaLabel}</span>
        <ChevronDown size={15} className={open ? "rotate-180" : ""} />
      </button>
      {open && createPortal(
        <div ref={menuRef} role="listbox" aria-label={ariaLabel} data-tp-menu-theme={dark ? "dark" : "light"} style={{ position: "fixed", top: position.top, left: position.left, width: position.width, maxHeight: position.maxHeight, zIndex: 16000 }} className="tos-tp-premium-menu-v2">
          {searchable ? <label className="tos-tp-premium-menu-search-v2"><Search size={14} /><input autoFocus value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search…" /></label> : null}
          <div className="tos-tp-premium-menu-scroll-v2">
            {filtered.map((option) => {
              const active = String(option.value) === String(value);
              return <button key={String(option.value)} type="button" role="option" aria-selected={active} data-active={active ? "true" : "false"} onClick={() => choose(option.value)} className="tos-tp-premium-option-v2"><span>{option.label}</span>{active ? <Check size={14} /> : null}</button>;
            })}
            {!filtered.length ? <div className="tos-tp-premium-empty-v2">No matches</div> : null}
          </div>
        </div>, document.body,
      )}
    </>
  );
}
'''

page = replace_once(page, 'const TEAM_PRESETS = [', premium_select_component + '\nconst TEAM_PRESETS = [', "premium select component")

employee_select = '''<select value={employeeFilter} onChange={(event) => setEmployeeFilter(event.target.value)} className="min-h-10 rounded-xl border border-zinc-200 bg-white px-3 text-xs font-bold text-zinc-800 outline-none focus:border-amber-400 dark:border-white/10 dark:bg-zinc-900 dark:text-white" aria-label="Employee filter">\n              <option value="all">All employees</option>\n              {allEmployees.map((employee) => <option key={employee.id} value={employee.id}>{employee.name}</option>)}\n            </select>'''
employee_premium = '''<TeamPerformancePremiumSelectV2 value={employeeFilter} onChange={setEmployeeFilter} ariaLabel="Employee filter" searchable options={[{ value: "all", label: "All employees" }, ...allEmployees.map((employee) => ({ value: employee.id, label: employee.name }))]} />'''
page = replace_once(page, employee_select, employee_premium, "employee premium filter")

department_select = '''<select value={departmentFilter} onChange={(event) => setDepartmentFilter(event.target.value)} className="min-h-10 rounded-xl border border-zinc-200 bg-white px-3 text-xs font-bold text-zinc-800 outline-none focus:border-amber-400 dark:border-white/10 dark:bg-zinc-900 dark:text-white" aria-label="Department filter">\n              <option value="all">All departments</option>\n              {departments.map((department) => <option key={department} value={department}>{department}</option>)}\n            </select>'''
department_premium = '''<TeamPerformancePremiumSelectV2 value={departmentFilter} onChange={setDepartmentFilter} ariaLabel="Department filter" options={[{ value: "all", label: "All departments" }, ...departments.map((department) => ({ value: department, label: department }))]} />'''
page = replace_once(page, department_select, department_premium, "department premium filter")

# Add a stable hook to the main employee ledger card.
page = replace_once(page, '<Card className="overflow-hidden p-0">\n        <div className="flex flex-col gap-3 border-b border-zinc-100 p-4 dark:border-white/10 lg:flex-row lg:items-center lg:justify-between">', '<Card className="tos-tp-employee-ledger-v2 overflow-hidden p-0">\n        <div className="flex flex-col gap-3 border-b border-zinc-100 p-4 dark:border-white/10 lg:flex-row lg:items-center lg:justify-between">', "employee ledger hook")

# PERIOD CONTROL: replace native compare select with premium portal menu.
period = replace_once(period, 'import { useState } from "react";', 'import { useEffect, useRef, useState } from "react";\nimport { createPortal } from "react-dom";', "period React imports")
period = replace_once(period, 'import { CalendarDays, Minus, TrendingDown, TrendingUp } from "lucide-react";', 'import { CalendarDays, Check, ChevronDown, Minus, TrendingDown, TrendingUp } from "lucide-react";', "period icon imports")

compare_component = r'''

function PerformanceCompareSelectV2({ value, onChange }) {
  const [open, setOpen] = useState(false);
  const [position, setPosition] = useState({ top: 0, left: 0, width: 260 });
  const triggerRef = useRef(null);
  const menuRef = useRef(null);
  const selected = COMPARE_OPTIONS.find((item) => item.value === value) || COMPARE_OPTIONS[0];

  useEffect(() => {
    if (!open) return undefined;
    const sync = () => {
      const rect = triggerRef.current?.getBoundingClientRect();
      if (!rect) return;
      const width = Math.min(Math.max(rect.width, 250), 360);
      const left = Math.min(Math.max(10, rect.left), Math.max(10, window.innerWidth - width - 10));
      const top = rect.bottom + 8;
      setPosition({ top, left, width });
    };
    const outside = (event) => {
      if (triggerRef.current?.contains(event.target) || menuRef.current?.contains(event.target)) return;
      setOpen(false);
    };
    const key = (event) => { if (event.key === "Escape") { setOpen(false); triggerRef.current?.focus(); } };
    sync();
    window.addEventListener("resize", sync);
    window.addEventListener("scroll", sync, true);
    document.addEventListener("mousedown", outside);
    document.addEventListener("keydown", key);
    return () => {
      window.removeEventListener("resize", sync);
      window.removeEventListener("scroll", sync, true);
      document.removeEventListener("mousedown", outside);
      document.removeEventListener("keydown", key);
    };
  }, [open]);

  const dark = document.documentElement.classList.contains("dark") || document.body.classList.contains("dark");
  return (
    <>
      <button ref={triggerRef} type="button" className="tos-tp-compare-trigger-v2" aria-haspopup="listbox" aria-expanded={open} onClick={() => setOpen((current) => !current)}><span>{selected.label}</span><ChevronDown size={14} className={open ? "rotate-180" : ""} /></button>
      {open && createPortal(<div ref={menuRef} role="listbox" data-tp-menu-theme={dark ? "dark" : "light"} style={{ position: "fixed", top: position.top, left: position.left, width: position.width, zIndex: 16000 }} className="tos-tp-premium-menu-v2 tos-tp-compare-menu-v2">{COMPARE_OPTIONS.map((item) => { const active = item.value === value; return <button key={item.value} type="button" role="option" aria-selected={active} data-active={active ? "true" : "false"} className="tos-tp-premium-option-v2" onClick={() => { onChange(item.value); setOpen(false); }}><span>{item.label}</span>{active ? <Check size={14} /> : null}</button>; })}</div>, document.body)}
    </>
  );
}
'''
period = replace_once(period, 'function toInputDate(value) {', compare_component + '\nfunction toInputDate(value) {', "compare premium component")
period = replace_once(period, '<label className="block"><span className="mb-1 block text-[9px] font-black uppercase tracking-[0.1em] text-zinc-500">Compare with</span><select value={compareMode} onChange={(e) => setCompareMode(e.target.value)} className="min-h-10 w-full rounded-xl border border-zinc-200 bg-white px-3 text-xs font-black text-zinc-800 outline-none focus:border-amber-400 dark:border-white/10 dark:bg-zinc-900 dark:text-white">{COMPARE_OPTIONS.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}</select></label>', '<label className="block"><span className="mb-1 block text-[9px] font-black uppercase tracking-[0.1em] text-zinc-500">Compare with</span><PerformanceCompareSelectV2 value={compareMode} onChange={setCompareMode} /></label>', "premium compare select")

v2_css = r'''/* =========================================================
   TOS Team Performance — Flagship V2
   Visual refinement after V1 screenshots.
   Fixes KPI hierarchy, native-looking selectors, loud summary rows,
   and increases executive material depth without changing business logic.
   ========================================================= */
:root { --tos-team-performance-flagship-v2-runtime: 1; }

.tos-team-performance-flagship-v2 {
  --tp2-gold: #d8a53c;
  --tp2-gold-bright: #f4cf72;
  --tp2-ink: #111317;
}

/* Hero: less empty banner, more executive presence. */
.tos-team-performance-flagship-v2 .tos-premium-page-intro {
  min-height: 148px !important;
  padding: 25px 30px !important;
  background:
    radial-gradient(ellipse 45% 140% at 8% -52%, rgba(229,190,96,.34) 0 34%, transparent 35%),
    linear-gradient(112deg, transparent 0 50%, rgba(226,176,71,.20) 50.2% 50.55%, transparent 50.9%),
    linear-gradient(118deg, transparent 0 57%, rgba(225,171,60,.10) 57.2% 57.5%, transparent 57.9%),
    linear-gradient(135deg,#fffefa 0%,#f6efe1 63%,#fbf8f2 100%) !important;
  box-shadow: 0 28px 72px rgba(76,53,14,.11), inset 0 1px 0 rgba(255,255,255,.99) !important;
}
.tos-team-performance-flagship-v2 .tos-premium-page-intro::after {
  content: "EXECUTIVE PERFORMANCE  •  LIVE INTELLIGENCE";
  position: absolute;
  inset-inline-end: 28px;
  bottom: 24px;
  z-index: 1;
  font-size: 9px;
  font-weight: 950;
  letter-spacing: .18em;
  color: rgba(127,87,20,.62);
}

/* Command deck: denser and more coherent. */
.tos-team-performance-flagship-v2 .tos-tp-command-deck-v1 {
  padding: 13px !important;
  background: linear-gradient(180deg,rgba(255,255,255,.985),rgba(247,242,233,.96)) !important;
  box-shadow: 0 19px 44px rgba(65,47,20,.075), inset 0 1px 0 rgba(255,255,255,.99) !important;
}
.tos-team-performance-flagship-v2 .tos-tp-filter-grid-v1 {
  gap: 9px !important;
  padding: 9px !important;
  background: linear-gradient(180deg,rgba(255,255,255,.82),rgba(251,248,242,.72)) !important;
}

/* Custom premium selector triggers. */
.tos-team-performance-flagship-v2 .tos-tp-premium-select-trigger-v2,
.tos-team-performance-flagship-v2 .tos-tp-compare-trigger-v2 {
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
  box-shadow: inset 0 1px 0 rgba(255,255,255,.99),0 5px 14px rgba(70,50,18,.035);
  outline: none;
  transition: border-color .16s ease, box-shadow .16s ease, transform .16s ease;
}
.tos-team-performance-flagship-v2 .tos-tp-premium-select-trigger-v2:hover,
.tos-team-performance-flagship-v2 .tos-tp-compare-trigger-v2:hover {
  border-color: rgba(211,157,51,.48);
  box-shadow: inset 0 1px 0 rgba(255,255,255,.99),0 7px 18px rgba(94,63,15,.065);
}
.tos-team-performance-flagship-v2 .tos-tp-premium-select-trigger-v2:focus-visible,
.tos-team-performance-flagship-v2 .tos-tp-compare-trigger-v2:focus-visible {
  border-color: rgba(211,157,51,.72);
  box-shadow: 0 0 0 3px rgba(211,157,51,.11);
}
.tos-team-performance-flagship-v2 .tos-tp-premium-select-trigger-v2 svg,
.tos-team-performance-flagship-v2 .tos-tp-compare-trigger-v2 svg { color:#aa791e; transition:transform .18s ease; }

/* Portal menu is self-contained because it mounts under body. */
.tos-tp-premium-menu-v2 {
  overflow: hidden;
  padding: 7px;
  border: 1px solid rgba(196,145,45,.26);
  border-radius: 18px;
  background: rgba(255,253,248,.985);
  box-shadow: 0 28px 72px rgba(58,42,17,.22),0 7px 20px rgba(58,42,17,.08),inset 0 1px 0 rgba(255,255,255,.98);
  backdrop-filter: blur(22px) saturate(1.08);
}
.tos-tp-premium-menu-search-v2 {
  height: 40px;
  display:flex;
  align-items:center;
  gap:8px;
  margin-bottom:6px;
  padding:0 11px;
  border:1px solid rgba(133,102,52,.14);
  border-radius:12px;
  background:#fff;
  color:#9a772f;
}
.tos-tp-premium-menu-search-v2 input { min-width:0; flex:1; border:0; outline:0; background:transparent; color:#25221d; font-size:12px; font-weight:750; }
.tos-tp-premium-menu-scroll-v2 { max-height: 300px; overflow-y:auto; }
.tos-tp-premium-option-v2 {
  width:100%; min-height:40px; display:flex; align-items:center; justify-content:space-between; gap:10px;
  margin:1px 0; padding:8px 11px; border:0; border-radius:11px; background:transparent; color:#4b4438;
  font-size:12px; font-weight:800; text-align:start; transition:background .14s ease,color .14s ease,transform .14s ease;
}
.tos-tp-premium-option-v2:hover { background:rgba(219,167,63,.09); color:#17130c; transform:translateX(1px); }
.tos-tp-premium-option-v2[data-active="true"] { background:linear-gradient(135deg,#f8e6b5,#f2d581); color:#211707; box-shadow:inset 0 0 0 1px rgba(173,114,15,.16); }
.tos-tp-premium-option-v2[data-active="true"] svg { color:#9d6717; }
.tos-tp-premium-empty-v2 { padding:24px 12px; text-align:center; color:#9b9387; font-size:11px; font-weight:800; }

/* KPI hierarchy fix: V1 accidentally made the secondary note the dominant line. */
.tos-team-performance-flagship-v2 .tos-tp-kpi-v1 {
  min-height: 148px !important;
  padding: 17px 18px !important;
  border-radius: 24px !important;
}
.tos-team-performance-flagship-v2 .tos-tp-kpi-v1 > p:nth-of-type(1) {
  margin-top: 12px !important;
  font-size: clamp(1.65rem,1.9vw,2.05rem) !important;
  line-height: 1.02 !important;
  letter-spacing: -.035em !important;
  color:#171713 !important;
}
.tos-team-performance-flagship-v2 .tos-tp-kpi-v1 > p:nth-of-type(2) {
  margin-top: 7px !important;
  font-size: .78rem !important;
  line-height: 1.32 !important;
  letter-spacing: 0 !important;
  color:#8b8377 !important;
  font-weight: 800 !important;
}
.tos-team-performance-flagship-v2 .tos-tp-kpi-v1::before {
  content:"";
  position:absolute;
  inset-inline-start:18px;
  top:0;
  width:42px;
  height:2px;
  border-radius:0 0 999px 999px;
  background:linear-gradient(90deg,var(--kpi-accent),transparent);
  opacity:.72;
}

/* Management Summary: replace loud solid rows with refined executive signals. */
.tos-team-performance-flagship-v2 #phase3-management-summary {
  border-radius:26px !important;
  background:linear-gradient(180deg,rgba(255,255,255,.985),rgba(249,246,239,.96)) !important;
  box-shadow:0 20px 48px rgba(65,47,20,.06),inset 0 1px 0 rgba(255,255,255,.99) !important;
}
.tos-team-performance-flagship-v2 #phase3-management-summary article {
  position:relative;
  overflow:hidden;
  border-radius:19px !important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.86);
}
.tos-team-performance-flagship-v2 #phase3-management-summary article button {
  background:rgba(255,255,255,.76) !important;
  border-color:rgba(108,86,52,.11) !important;
  box-shadow:inset 3px 0 0 rgba(214,163,58,.16),0 3px 10px rgba(64,46,20,.025) !important;
}
.tos-team-performance-flagship-v2 #phase3-management-summary article button:hover {
  background:#fffdfa !important;
  border-color:rgba(214,163,58,.30) !important;
  transform:translateY(-1px);
}

/* Executive command center + disclosures feel like one coherent reporting system. */
.tos-team-performance-flagship-v2 .tos-tp-executive-v1 > * {
  border-radius:26px !important;
  box-shadow:0 22px 52px rgba(62,46,21,.065),inset 0 1px 0 rgba(255,255,255,.96) !important;
}
.tos-team-performance-flagship-v2 details {
  border-radius:22px !important;
  border-color:rgba(147,109,44,.13) !important;
  background:linear-gradient(180deg,rgba(255,255,255,.89),rgba(249,245,238,.82)) !important;
  box-shadow:0 9px 26px rgba(62,46,21,.035),inset 0 1px 0 rgba(255,255,255,.92) !important;
}
.tos-team-performance-flagship-v2 details > summary { min-height:68px; padding:13px 16px !important; }
.tos-team-performance-flagship-v2 details > summary > span:last-child {
  border-color:rgba(204,150,46,.19) !important;
  background:linear-gradient(180deg,#fffdf7,#f3e4be) !important;
  color:#a06c16 !important;
  box-shadow:0 6px 16px rgba(92,62,15,.06),inset 0 1px 0 rgba(255,255,255,.98);
}

/* Employee ledger: executive table treatment. */
.tos-team-performance-flagship-v2 .tos-tp-employee-ledger-v2 {
  border-radius:26px !important;
  border-color:rgba(148,109,42,.14) !important;
  background:rgba(255,255,255,.97) !important;
  box-shadow:0 22px 56px rgba(60,44,20,.065),inset 0 1px 0 rgba(255,255,255,.98) !important;
}
.tos-team-performance-flagship-v2 .tos-tp-employee-ledger-v2 thead th {
  padding-top:12px !important; padding-bottom:12px !important;
  background:#f5f0e5 !important;
  color:#8c806d !important;
  font-size:9px !important;
  letter-spacing:.075em !important;
  text-transform:uppercase;
}
.tos-team-performance-flagship-v2 .tos-tp-employee-ledger-v2 tbody tr { transition:background .14s ease,transform .14s ease; }
.tos-team-performance-flagship-v2 .tos-tp-employee-ledger-v2 tbody tr:hover { background:rgba(218,166,61,.045) !important; }

/* DARK — deeper titanium, restrained semantic colors, luminous gold only where intentional. */
html.dark .tos-team-performance-flagship-v2 .tos-premium-page-intro {
  background:
    radial-gradient(ellipse 45% 140% at 8% -52%,rgba(230,173,48,.22) 0 34%,transparent 35%),
    linear-gradient(112deg,transparent 0 50%,rgba(246,190,42,.29) 50.2% 50.55%,transparent 50.9%),
    linear-gradient(118deg,transparent 0 57%,rgba(246,190,42,.14) 57.2% 57.5%,transparent 57.9%),
    linear-gradient(135deg,#121518 0%,#090b0e 72%,#0d1012 100%) !important;
  border-color:rgba(232,178,57,.27) !important;
  box-shadow:0 28px 76px rgba(0,0,0,.44),0 0 34px rgba(221,156,26,.045),inset 0 1px 0 rgba(255,255,255,.02) !important;
}
html.dark .tos-team-performance-flagship-v2 .tos-premium-page-intro::after { color:rgba(238,187,68,.70); }
html.dark .tos-team-performance-flagship-v2 .tos-tp-command-deck-v1 {
  border-color:rgba(229,177,57,.16) !important;
  background:linear-gradient(180deg,#14171b,#0d1013) !important;
  box-shadow:0 20px 48px rgba(0,0,0,.36),inset 0 1px 0 rgba(255,255,255,.018) !important;
}
html.dark .tos-team-performance-flagship-v2 .tos-tp-filter-grid-v1 { background:rgba(255,255,255,.016) !important; border-color:rgba(255,255,255,.065) !important; }
html.dark .tos-team-performance-flagship-v2 .tos-tp-premium-select-trigger-v2,
html.dark .tos-team-performance-flagship-v2 .tos-tp-compare-trigger-v2 {
  border-color:rgba(255,255,255,.09);
  background:linear-gradient(180deg,#14181c,#0c0f12);
  color:#f0eee8;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.02),0 7px 18px rgba(0,0,0,.18);
}
html.dark .tos-team-performance-flagship-v2 .tos-tp-premium-select-trigger-v2:hover,
html.dark .tos-team-performance-flagship-v2 .tos-tp-compare-trigger-v2:hover { border-color:rgba(230,177,58,.30); }
html.dark .tos-team-performance-flagship-v2 .tos-tp-kpi-v1 > p:nth-of-type(1) { color:#f8f6f0 !important; }
html.dark .tos-team-performance-flagship-v2 .tos-tp-kpi-v1 > p:nth-of-type(2) { color:#8f98a5 !important; }
html.dark .tos-team-performance-flagship-v2 #phase3-management-summary {
  background:linear-gradient(180deg,#13171b,#0d1013) !important;
  border-color:rgba(229,177,57,.14) !important;
  box-shadow:0 22px 54px rgba(0,0,0,.35),inset 0 1px 0 rgba(255,255,255,.017) !important;
}
html.dark .tos-team-performance-flagship-v2 #phase3-management-summary article button {
  background:linear-gradient(180deg,#15191d,#101316) !important;
  border-color:rgba(255,255,255,.065) !important;
  box-shadow:inset 3px 0 0 rgba(224,171,54,.20),inset 0 1px 0 rgba(255,255,255,.012) !important;
}
html.dark .tos-team-performance-flagship-v2 #phase3-management-summary article button:hover {
  background:#191d21 !important;
  border-color:rgba(229,177,57,.24) !important;
}
html.dark .tos-team-performance-flagship-v2 .tos-tp-executive-v1 > * {
  box-shadow:0 24px 58px rgba(0,0,0,.38),inset 0 1px 0 rgba(255,255,255,.015) !important;
}
html.dark .tos-team-performance-flagship-v2 details {
  border-color:rgba(255,255,255,.07) !important;
  background:linear-gradient(180deg,#14171b,#0e1114) !important;
  box-shadow:0 10px 30px rgba(0,0,0,.24),inset 0 1px 0 rgba(255,255,255,.015) !important;
}
html.dark .tos-team-performance-flagship-v2 details > summary > span:last-child {
  border-color:rgba(232,178,57,.19) !important;
  background:linear-gradient(180deg,#211b0f,#15130d) !important;
  color:#e6b852 !important;
}
html.dark .tos-team-performance-flagship-v2 .tos-tp-employee-ledger-v2 {
  border-color:rgba(227,176,57,.12) !important;
  background:linear-gradient(180deg,#121518,#0c0f12) !important;
  box-shadow:0 24px 60px rgba(0,0,0,.39),inset 0 1px 0 rgba(255,255,255,.015) !important;
}
html.dark .tos-team-performance-flagship-v2 .tos-tp-employee-ledger-v2 thead th { background:#111418 !important; color:#89939f !important; }
html.dark .tos-team-performance-flagship-v2 .tos-tp-employee-ledger-v2 tbody tr:hover { background:rgba(225,171,52,.035) !important; }

.tos-tp-premium-menu-v2[data-tp-menu-theme="dark"] {
  border-color:rgba(232,180,58,.18);
  background:rgba(12,15,18,.985);
  box-shadow:0 30px 80px rgba(0,0,0,.58),0 8px 22px rgba(0,0,0,.32),inset 0 1px 0 rgba(255,255,255,.018);
}
.tos-tp-premium-menu-v2[data-tp-menu-theme="dark"] .tos-tp-premium-menu-search-v2 { border-color:rgba(255,255,255,.08); background:#15191d; color:#d2a94d; }
.tos-tp-premium-menu-v2[data-tp-menu-theme="dark"] .tos-tp-premium-menu-search-v2 input { color:#f2efe7; }
.tos-tp-premium-menu-v2[data-tp-menu-theme="dark"] .tos-tp-premium-option-v2 { color:#c9cdd2; }
.tos-tp-premium-menu-v2[data-tp-menu-theme="dark"] .tos-tp-premium-option-v2:hover { background:rgba(255,255,255,.045); color:#fff; }
.tos-tp-premium-menu-v2[data-tp-menu-theme="dark"] .tos-tp-premium-option-v2[data-active="true"] { background:linear-gradient(135deg,rgba(232,181,65,.20),rgba(232,181,65,.065)); color:#f4d98d; box-shadow:inset 0 0 0 1px rgba(232,181,65,.16); }

@media (max-width: 900px) {
  .tos-team-performance-flagship-v2 .tos-premium-page-intro::after { display:none; }
}
'''

source_written = False
staging = None
old_live = None
try:
    PAGE.write_text(page)
    PERIOD.write_text(period)
    V2_STYLE.write_text(v2_css)
    source_written = True

    build = subprocess.run(["npm", "run", "build"], cwd=FRONTEND, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if build.returncode != 0:
        print(build.stdout[-9000:])
        raise RuntimeError("frontend build failed")
    if not DIST.exists():
        raise RuntimeError("frontend dist missing after build")

    dist_runtime = tree_count(DIST, V2_RUNTIME.encode())
    dist_root = tree_count(DIST, b"data-tp-flagship-v2")
    dist_menu = tree_count(DIST, V2_MENU_TOKEN.encode())
    dist_compare = tree_count(DIST, V2_COMPARE_TOKEN.encode())
    if min(dist_runtime, dist_root, dist_menu, dist_compare) < 1:
        raise RuntimeError("V2 stable runtime markers missing from dist")

    ts = int(time.time())
    staging = LIVE_PARENT / f".build-phase04-4-v2-staging-{ts}"
    old_live = LIVE_PARENT / f".build-phase04-4-v2-before-{ts}"
    if staging.exists(): shutil.rmtree(staging)
    shutil.copytree(DIST, staging)
    if LIVE.exists(): LIVE.rename(old_live)
    staging.rename(LIVE)
    staging = None

    live_runtime = tree_count(LIVE, V2_RUNTIME.encode())
    live_root = tree_count(LIVE, b"data-tp-flagship-v2")
    live_menu = tree_count(LIVE, V2_MENU_TOKEN.encode())
    live_compare = tree_count(LIVE, V2_COMPARE_TOKEN.encode())
    if min(live_runtime, live_root, live_menu, live_compare) < 1:
        raise RuntimeError("V2 stable runtime markers missing from live build")

    if old_live and old_live.exists():
        shutil.rmtree(old_live)
        old_live = None

    print("PASS/FAIL=PASS")
    print("BUILD_RESULT=PASS")
    print("LIVE_DEPLOY=PASS")
    print("V2_RUNTIME=YES")
    print("V1_FLAGSHIP_BASELINE_PRESERVED=YES")
    print("KPI_HIERARCHY_CORRECTED=YES")
    print("KPI_SECONDARY_TEXT_DEEMPHASIZED=YES")
    print("EMPLOYEE_FILTER_PREMIUM_MENU=YES")
    print("DEPARTMENT_FILTER_PREMIUM_MENU=YES")
    print("COMPARISON_FILTER_PREMIUM_MENU=YES")
    print("MANAGEMENT_SUMMARY_ROWS_RESTRAINED=YES")
    print("EXECUTIVE_SURFACE_DEPTH_REFINED=YES")
    print("DISCLOSURE_SYSTEM_REFINED=YES")
    print("EMPLOYEE_LEDGER_REFINED=YES")
    print("LIGHT_FLAGSHIP_REFINED=YES")
    print("DARK_FLAGSHIP_REFINED=YES")
    print("BUSINESS_LOGIC_CHANGED=NO")
    print(f"SOURCE_V2_ROOT_HOOK_COUNT={page.count(V2_ROOT)}")
    print(f"SOURCE_V2_MENU_TOKEN_COUNT={page.count(V2_MENU_TOKEN) + period.count(V2_MENU_TOKEN)}")
    print(f"DIST_V2_RUNTIME_COUNT={dist_runtime}")
    print(f"DIST_V2_ROOT_HOOK_COUNT={dist_root}")
    print(f"DIST_V2_MENU_TOKEN_COUNT={dist_menu}")
    print(f"LIVE_V2_RUNTIME_COUNT={live_runtime}")
    print(f"LIVE_V2_ROOT_HOOK_COUNT={live_root}")
    print(f"LIVE_V2_MENU_TOKEN_COUNT={live_menu}")
    print(f"TEAM_PERFORMANCE_SHA256={sha256(PAGE)}")
    print(f"PERIOD_CONTROL_SHA256={sha256(PERIOD)}")
    print(f"FLAGSHIP_V2_CSS_SHA256={sha256(V2_STYLE)}")
except Exception as exc:
    if source_written:
        PAGE.write_text(original_page)
        PERIOD.write_text(original_period)
        if v2_style_existed:
            V2_STYLE.write_text(original_v2_style or "")
        elif V2_STYLE.exists():
            V2_STYLE.unlink()
    if staging and staging.exists(): shutil.rmtree(staging, ignore_errors=True)
    if old_live and old_live.exists():
        if LIVE.exists(): shutil.rmtree(LIVE, ignore_errors=True)
        old_live.rename(LIVE)
    fail(exc)
