from pathlib import Path
import hashlib
import re
import shutil
import subprocess
import sys
import time

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
PAGE = FRONTEND / "src/pages/AuditLogPage.jsx"
V1_STYLE = FRONTEND / "src/pages/auditLogFlagshipLuxuryV1.css"
V21_STYLE = FRONTEND / "src/pages/auditLogFlagshipLuxuryV2_1R2.css"
DIST = FRONTEND / "dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

EXPECTED_PAGE_SHA256 = "bf412ab1e37e72b5fc101489bd4a7fa407f1ead64238215709fbc5fe43120808"
EXPECTED_V1_STYLE_SHA256 = "c9b2cf5e1eac5dbca40a9835694fa14d58127119083ffc78b0b013edfd83a507"

IMPORT_V1 = 'import "./auditLogFlagshipLuxuryV1.css";'
IMPORT_V21 = 'import "./auditLogFlagshipLuxuryV2_1R2.css";'

HELPERS = r'''
const AUDIT_V21_MONTHS_EN = ["January","February","March","April","May","June","July","August","September","October","November","December"];
const AUDIT_V21_MONTHS_AR = ["يناير","فبراير","مارس","أبريل","مايو","يونيو","يوليو","أغسطس","سبتمبر","أكتوبر","نوفمبر","ديسمبر"];
const AUDIT_V21_WEEK_EN = ["Su","Mo","Tu","We","Th","Fr","Sa"];
const AUDIT_V21_WEEK_AR = ["ح","ن","ث","ر","خ","ج","س"];

function auditV21Ymd(date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

function AuditV21LuxuryDatePicker({ value, onChange, isEnglish, align = "start" }) {
  const selected = value ? new Date(`${value}T12:00:00`) : null;
  const [open, setOpen] = useState(false);
  const [cursor, setCursor] = useState(() => selected || new Date());
  const rootRef = useRef(null);

  useEffect(() => {
    if (selected && !Number.isNaN(selected.getTime())) setCursor(selected);
  }, [value]);

  useEffect(() => {
    if (!open) return undefined;
    const onPointerDown = (event) => {
      if (rootRef.current && !rootRef.current.contains(event.target)) setOpen(false);
    };
    const onKeyDown = (event) => {
      if (event.key === "Escape") setOpen(false);
    };
    document.addEventListener("pointerdown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("pointerdown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open]);

  const year = cursor.getFullYear();
  const month = cursor.getMonth();
  const startOffset = new Date(year, month, 1).getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const todayKey = auditV21Ymd(new Date());
  const selectedKey = value || "";
  const monthNames = isEnglish ? AUDIT_V21_MONTHS_EN : AUDIT_V21_MONTHS_AR;
  const weekNames = isEnglish ? AUDIT_V21_WEEK_EN : AUDIT_V21_WEEK_AR;
  const cells = [];
  for (let i = 0; i < startOffset; i += 1) cells.push(null);
  for (let day = 1; day <= daysInMonth; day += 1) cells.push(day);

  function choose(day) {
    onChange(auditV21Ymd(new Date(year, month, day)));
    setOpen(false);
  }

  function chooseToday() {
    const now = new Date();
    setCursor(now);
    onChange(auditV21Ymd(now));
    setOpen(false);
  }

  return (
    <div ref={rootRef} className={`tos-audit-v21-date tos-audit-v21-date-${align} ${open ? "is-open" : ""}`}>
      <button
        type="button"
        className="tos-audit-v21-date-trigger"
        onClick={() => setOpen((current) => !current)}
        aria-expanded={open}
      >
        <span className={value ? "has-value" : "is-placeholder"}>{value || "yyyy-mm-dd"}</span>
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M7 2v3M17 2v3M4 9h16M5 4h14a2 2 0 0 1 2 2v13a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2Z" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
        </svg>
      </button>
      {open && (
        <div className="tos-audit-v21-calendar" role="dialog" aria-label={isEnglish ? "Choose date" : "اختر التاريخ"}>
          <div className="tos-audit-v21-calendar-head">
            <button type="button" onClick={() => setCursor(new Date(year, month - 1, 1))} aria-label={isEnglish ? "Previous month" : "الشهر السابق"}>&lsaquo;</button>
            <div><strong>{monthNames[month]}</strong><span>{year}</span></div>
            <button type="button" onClick={() => setCursor(new Date(year, month + 1, 1))} aria-label={isEnglish ? "Next month" : "الشهر التالي"}>&rsaquo;</button>
          </div>
          <div className="tos-audit-v21-weekdays">
            {weekNames.map((day) => <span key={day}>{day}</span>)}
          </div>
          <div className="tos-audit-v21-calendar-grid">
            {cells.map((day, index) => {
              if (!day) return <span className="is-blank" key={`blank-${index}`} />;
              const key = auditV21Ymd(new Date(year, month, day));
              return (
                <button
                  type="button"
                  key={key}
                  onClick={() => choose(day)}
                  className={`${key === selectedKey ? "is-selected" : ""} ${key === todayKey ? "is-today" : ""}`}
                >
                  {day}
                </button>
              );
            })}
          </div>
          <div className="tos-audit-v21-calendar-foot">
            <button type="button" onClick={() => { onChange(""); setOpen(false); }}>{isEnglish ? "Clear" : "مسح"}</button>
            <button type="button" className="is-primary" onClick={chooseToday}>{isEnglish ? "Today" : "اليوم"}</button>
          </div>
        </div>
      )}
    </div>
  );
}

function auditV21SmartChips(query, isEnglish) {
  const raw = String(query || "").trim();
  if (!raw) return [];
  const chips = [];
  const seen = new Set();
  const labels = {
    user: isEnglish ? "User" : "المستخدم",
    actor: isEnglish ? "Actor" : "المنفذ",
    severity: isEnglish ? "Severity" : "الخطورة",
    outcome: isEnglish ? "Outcome" : "النتيجة",
    category: isEnglish ? "Category" : "الفئة",
    source: isEnglish ? "Source" : "المصدر",
    action: isEnglish ? "Action" : "الإجراء",
    entity: isEnglish ? "Entity" : "الكيان",
    route: isEnglish ? "Route" : "المسار",
    request: isEnglish ? "Request" : "الطلب",
  };
  const tokenRegex = /\b(user|actor|severity|outcome|category|source|action|entity|route|request):("[^"]+"|'[^']+'|[^\s]+)/gi;
  let match;
  while ((match = tokenRegex.exec(raw)) !== null) {
    const key = match[1].toLowerCase();
    const value = match[2].replace(/^['"]|['"]$/g, "");
    const id = `${key}:${value.toLowerCase()}`;
    if (!seen.has(id)) {
      seen.add(id);
      chips.push({ key, label: labels[key] || key, value });
    }
  }
  [
    [/(^|\s)(today|اليوم)($|\s)/i, isEnglish ? "Today" : "اليوم"],
    [/(^|\s)(yesterday|أمس)($|\s)/i, isEnglish ? "Yesterday" : "أمس"],
    [/(^|\s)(this\s+week|هذا\s+الأسبوع)($|\s)/i, isEnglish ? "This week" : "هذا الأسبوع"],
  ].forEach(([regex, value]) => {
    if (regex.test(raw) && !seen.has(`date:${value}`)) {
      seen.add(`date:${value}`);
      chips.push({ key: "date", label: isEnglish ? "Date" : "التاريخ", value });
    }
  });
  return chips.slice(0, 8);
}

function AuditV21SmartQueryChips({ query, isEnglish }) {
  const chips = auditV21SmartChips(query, isEnglish);
  if (!chips.length) return null;
  return (
    <div className="tos-audit-v21-smart-chips">
      <div className="tos-audit-v21-smart-title">
        <span className="tos-audit-v21-spark">✦</span>
        <span>{isEnglish ? "Smart interpretation" : "تفسير البحث الذكي"}</span>
      </div>
      <div className="tos-audit-v21-smart-list">
        {chips.map((chip) => (
          <span className={`tos-audit-v21-chip is-${chip.key}`} key={`${chip.key}-${chip.value}`}>
            <b>{chip.label}</b><em>{chip.value}</em>
          </span>
        ))}
      </div>
    </div>
  );
}
'''

CSS = r''':root {
  --tos-audit-log-flagship-v2-1-r2-runtime: 1;
}

.tos-audit-flagship-v1 .tos-audit-shell { overflow: visible !important; }

.tos-audit-flagship-v1 .tos-audit-v21-smart-chips {
  grid-column: 1 / -1;
  display: flex;
  align-items: center;
  gap: 12px;
  min-height: 46px;
  padding: 8px 11px;
  border: 1px solid rgba(176,115,17,.16);
  border-radius: 15px;
  background: radial-gradient(circle at 100% 0%, rgba(236,202,128,.15), transparent 30%), linear-gradient(180deg,#fffefa,#fbf4e7);
  box-shadow: inset 0 1px rgba(255,255,255,.96), 0 8px 19px rgba(69,41,2,.035);
}
.tos-audit-flagship-v1 .tos-audit-v21-smart-title { display:inline-flex; align-items:center; gap:7px; flex:0 0 auto; font-size:10px; font-weight:950; color:#79674e; letter-spacing:.02em; }
.tos-audit-flagship-v1 .tos-audit-v21-spark { display:grid; width:25px; height:25px; place-items:center; border:1px solid rgba(151,94,6,.24); border-radius:9px; color:#5f3d04; background:linear-gradient(145deg,#fff4c7,#e6bc53 65%,#c78b18); box-shadow:0 6px 14px rgba(120,73,2,.12), inset 0 1px rgba(255,255,255,.82); }
.tos-audit-flagship-v1 .tos-audit-v21-smart-list { display:flex; align-items:center; flex-wrap:wrap; gap:6px; min-width:0; }
.tos-audit-flagship-v1 .tos-audit-v21-chip { display:inline-flex; align-items:center; gap:6px; min-height:28px; padding:4px 8px; border:1px solid rgba(171,111,15,.13); border-radius:9px; background:rgba(255,255,255,.66); box-shadow:inset 0 1px rgba(255,255,255,.88); }
.tos-audit-flagship-v1 .tos-audit-v21-chip b { font-size:9px; font-weight:950; text-transform:uppercase; color:#a06d14; }
.tos-audit-flagship-v1 .tos-audit-v21-chip em { max-width:180px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; font-size:10px; font-style:normal; font-weight:850; color:#40331f; }

.tos-audit-flagship-v1 .tos-audit-v21-date { position:relative; min-width:0; z-index:24; }
.tos-audit-flagship-v1 .tos-audit-v21-date.is-open { z-index:150; }
.tos-audit-flagship-v1 .tos-audit-v21-date-trigger {
  width:100%; min-height:46px; padding:0 14px; display:flex; align-items:center; justify-content:space-between; gap:10px;
  border:1px solid rgba(168,108,12,.18); border-radius:14px; color:#2b2114; background:linear-gradient(180deg,#fffefa,#fbf4e6);
  box-shadow:inset 0 1px rgba(255,255,255,.98), 0 7px 18px rgba(74,44,2,.035);
}
.tos-audit-flagship-v1 .tos-audit-v21-date-trigger:hover { border-color:rgba(183,120,16,.30); box-shadow:0 8px 20px rgba(78,46,2,.06), inset 0 1px rgba(255,255,255,.98); }
.tos-audit-flagship-v1 .tos-audit-v21-date.is-open .tos-audit-v21-date-trigger { border-color:rgba(194,132,22,.46); box-shadow:0 0 0 3px rgba(224,181,79,.13), inset 0 1px rgba(255,255,255,.98); }
.tos-audit-flagship-v1 .tos-audit-v21-date-trigger .is-placeholder { color:#999083; }
.tos-audit-flagship-v1 .tos-audit-v21-date-trigger .has-value { font-weight:850; color:#372711; }
.tos-audit-flagship-v1 .tos-audit-v21-date-trigger svg { width:17px; height:17px; flex:0 0 auto; color:#a36f13; }

.tos-audit-flagship-v1 .tos-audit-v21-calendar {
  position:absolute; top:calc(100% + 9px); width:min(324px, calc(100vw - 44px)); padding:14px; overflow:hidden;
  border:1px solid rgba(168,107,12,.24); border-radius:20px; color:#251b0e;
  background:radial-gradient(circle at 92% 0%,rgba(245,221,164,.30),transparent 31%), linear-gradient(155deg,#fffefa,#fbf3e2);
  box-shadow:0 28px 60px rgba(69,41,2,.18), 0 8px 20px rgba(67,39,2,.08), inset 0 1px rgba(255,255,255,.98); z-index:180;
}
.tos-audit-flagship-v1 .tos-audit-v21-date-end .tos-audit-v21-calendar { inset-inline-end:0; }
.tos-audit-flagship-v1 .tos-audit-v21-date-start .tos-audit-v21-calendar { inset-inline-start:0; }
.tos-audit-flagship-v1 .tos-audit-v21-calendar-head { display:grid; grid-template-columns:36px 1fr 36px; align-items:center; gap:8px; padding-bottom:11px; border-bottom:1px solid rgba(154,100,12,.10); }
.tos-audit-flagship-v1 .tos-audit-v21-calendar-head > button { width:34px; height:34px; border:1px solid rgba(163,103,10,.16); border-radius:10px; color:#8b5c0a; background:linear-gradient(180deg,#fffdf7,#f6e8c7); box-shadow:inset 0 1px rgba(255,255,255,.9); font-size:22px; line-height:1; }
.tos-audit-flagship-v1 .tos-audit-v21-calendar-head > div { text-align:center; line-height:1.15; }
.tos-audit-flagship-v1 .tos-audit-v21-calendar-head strong { display:block; font-size:14px; font-weight:950; }
.tos-audit-flagship-v1 .tos-audit-v21-calendar-head span { display:block; margin-top:3px; font-size:10px; font-weight:800; color:#a28d70; }
.tos-audit-flagship-v1 .tos-audit-v21-weekdays, .tos-audit-flagship-v1 .tos-audit-v21-calendar-grid { display:grid; grid-template-columns:repeat(7,1fr); gap:4px; }
.tos-audit-flagship-v1 .tos-audit-v21-weekdays { padding:10px 0 6px; }
.tos-audit-flagship-v1 .tos-audit-v21-weekdays span { text-align:center; font-size:9px; font-weight:950; color:#9a8d79; text-transform:uppercase; }
.tos-audit-flagship-v1 .tos-audit-v21-calendar-grid button, .tos-audit-flagship-v1 .tos-audit-v21-calendar-grid .is-blank { aspect-ratio:1; min-width:0; }
.tos-audit-flagship-v1 .tos-audit-v21-calendar-grid button { border:1px solid transparent; border-radius:10px; color:#4d402f; background:transparent; font-size:11px; font-weight:850; }
.tos-audit-flagship-v1 .tos-audit-v21-calendar-grid button:hover { border-color:rgba(176,115,17,.15); background:#fff8e8; transform:translateY(-1px); }
.tos-audit-flagship-v1 .tos-audit-v21-calendar-grid button.is-today { border-color:rgba(190,127,20,.22); color:#93600a; background:rgba(230,190,94,.11); }
.tos-audit-flagship-v1 .tos-audit-v21-calendar-grid button.is-selected { color:#211500; border-color:rgba(145,89,3,.36); background:linear-gradient(180deg,#fff0ae,#edc75d 55%,#ce941c); box-shadow:0 7px 17px rgba(137,82,2,.16), inset 0 1px rgba(255,255,255,.74); }
.tos-audit-flagship-v1 .tos-audit-v21-calendar-foot { display:flex; justify-content:space-between; gap:8px; margin-top:10px; padding-top:10px; border-top:1px solid rgba(154,100,12,.10); }
.tos-audit-flagship-v1 .tos-audit-v21-calendar-foot button { min-height:34px; padding:0 12px; border:1px solid rgba(164,103,10,.16); border-radius:10px; color:#5c482b; background:linear-gradient(180deg,#fffefa,#f6e8c8); font-size:10px; font-weight:900; }
.tos-audit-flagship-v1 .tos-audit-v21-calendar-foot button.is-primary { color:#211500; border-color:rgba(145,89,3,.32); background:linear-gradient(180deg,#f7dc81,#d8a630); }

.dark .tos-audit-flagship-v1 .tos-audit-v21-smart-chips { border-color:rgba(222,176,74,.10); background:linear-gradient(180deg,rgba(21,24,26,.97),rgba(13,15,16,.97)); box-shadow:inset 0 1px rgba(255,255,255,.025); }
.dark .tos-audit-flagship-v1 .tos-audit-v21-smart-title { color:#aaa08f; }
.dark .tos-audit-flagship-v1 .tos-audit-v21-spark { color:#211500; border-color:rgba(245,206,111,.22); background:linear-gradient(145deg,#efd476,#c58a1c); }
.dark .tos-audit-flagship-v1 .tos-audit-v21-chip { border-color:rgba(222,176,74,.11); background:#181a1b; box-shadow:inset 0 1px rgba(255,255,255,.025); }
.dark .tos-audit-flagship-v1 .tos-audit-v21-chip b { color:#d3aa4b; }
.dark .tos-audit-flagship-v1 .tos-audit-v21-chip em { color:#e6dfd5; }
.dark .tos-audit-flagship-v1 .tos-audit-v21-date-trigger { color:#e6dfd5; border-color:rgba(222,176,74,.12); background:linear-gradient(180deg,#1d2022,#141617); box-shadow:inset 0 1px rgba(255,255,255,.03); }
.dark .tos-audit-flagship-v1 .tos-audit-v21-date-trigger .is-placeholder { color:#7e7b75; }
.dark .tos-audit-flagship-v1 .tos-audit-v21-date-trigger .has-value { color:#eee6da; }
.dark .tos-audit-flagship-v1 .tos-audit-v21-date-trigger svg { color:#d0a744; }
.dark .tos-audit-flagship-v1 .tos-audit-v21-date.is-open .tos-audit-v21-date-trigger { border-color:rgba(231,189,83,.30); box-shadow:0 0 0 3px rgba(222,176,74,.08), inset 0 1px rgba(255,255,255,.03); }
.dark .tos-audit-flagship-v1 .tos-audit-v21-calendar { color:#eee7dc; border-color:rgba(222,176,74,.17); background:radial-gradient(circle at 90% 0%,rgba(213,163,45,.10),transparent 31%), linear-gradient(155deg,#171a1c,#0f1112); box-shadow:0 30px 70px rgba(0,0,0,.46), 0 8px 22px rgba(0,0,0,.24), inset 0 1px rgba(255,255,255,.035); }
.dark .tos-audit-flagship-v1 .tos-audit-v21-calendar-head { border-bottom-color:rgba(222,176,74,.09); }
.dark .tos-audit-flagship-v1 .tos-audit-v21-calendar-head > button { color:#d6ac4b; border-color:rgba(222,176,74,.13); background:linear-gradient(180deg,#202326,#151719); }
.dark .tos-audit-flagship-v1 .tos-audit-v21-calendar-head span, .dark .tos-audit-flagship-v1 .tos-audit-v21-weekdays span { color:#8f897e; }
.dark .tos-audit-flagship-v1 .tos-audit-v21-calendar-grid button { color:#d8d1c7; }
.dark .tos-audit-flagship-v1 .tos-audit-v21-calendar-grid button:hover { color:#f5ecd9; border-color:rgba(222,176,74,.12); background:#1c1e1f; }
.dark .tos-audit-flagship-v1 .tos-audit-v21-calendar-grid button.is-today { color:#e8c46c; border-color:rgba(222,176,74,.25); background:rgba(222,176,74,.07); }
.dark .tos-audit-flagship-v1 .tos-audit-v21-calendar-grid button.is-selected { color:#211500; border-color:rgba(250,216,126,.34); background:linear-gradient(180deg,#f3d578,#d8a52f 65%,#b9780f); box-shadow:0 8px 19px rgba(177,114,14,.23), inset 0 1px rgba(255,255,255,.36); }
.dark .tos-audit-flagship-v1 .tos-audit-v21-calendar-foot { border-top-color:rgba(222,176,74,.09); }
.dark .tos-audit-flagship-v1 .tos-audit-v21-calendar-foot button { color:#d8d0c4; border-color:rgba(222,176,74,.13); background:linear-gradient(180deg,#1e2022,#141617); }
.dark .tos-audit-flagship-v1 .tos-audit-v21-calendar-foot button.is-primary { color:#211500; background:linear-gradient(180deg,#f1d16d,#d6a12c); }

@media (max-width: 760px) {
  .tos-audit-flagship-v1 .tos-audit-v21-smart-chips { align-items:flex-start; flex-direction:column; }
  .tos-audit-flagship-v1 .tos-audit-v21-calendar { width:min(304px, calc(100vw - 34px)); }
}
'''

def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def die(message):
    print("PASS/FAIL=FAIL")
    print(f"ERROR={message}")
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("STATUS=STOPPED")
    raise SystemExit(1)

def run(cmd, cwd=None):
    result = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    if result.stdout:
        print(result.stdout, end="" if result.stdout.endswith("\n") else "\n")
    if result.returncode != 0:
        if result.stderr:
            print(result.stderr, end="" if result.stderr.endswith("\n") else "\n")
        raise RuntimeError("command failed: " + " ".join(cmd))
    return result

print("RUNNING=TOS_UXUI_SYSTEM_AUDIT_LOG_FLAGSHIP_V2_1_R2_EXACT_BASELINE")

if not PAGE.exists(): die("AuditLogPage.jsx missing")
if not V1_STYLE.exists(): die("Audit Log luxury V1 stylesheet missing")
if V21_STYLE.exists(): die("R2 stylesheet already exists; refusing repeated/unknown state")
if sha256(PAGE) != EXPECTED_PAGE_SHA256: die(f"AuditLogPage.jsx baseline SHA mismatch: got {sha256(PAGE)}")
if sha256(V1_STYLE) != EXPECTED_V1_STYLE_SHA256: die(f"Audit luxury V1 stylesheet SHA mismatch: got {sha256(V1_STYLE)}")

source = PAGE.read_text()
required_markers = [
    IMPORT_V1,
    "function parseSmartSearch(raw)",
    "function useVoiceSearch(onResult, onError)",
    "const [filters, setFilters] = useState(EMPTY_FILTERS);",
    "value={searchInput}",
    "onChange={(e) => handleSearchChange(e.target.value)}",
    'updateFilter("from", e.target.value)',
    'updateFilter("to", e.target.value)',
    "SpeechRecognition",
    "webkitSpeechRecognition",
]
for marker in required_markers:
    if marker not in source: die(f"required exact current-baseline marker missing: {marker}")

if IMPORT_V21 in source: die("R2 import already present")
if "AuditV21LuxuryDatePicker" in source or "AuditV21SmartQueryChips" in source: die("custom V2.1 components already present")
if source.count('type="date"') != 2: die(f"expected exactly 2 native date inputs, found {source.count('type=\"date\"')}")

react_import = re.search(r'import \{([^}]+)\} from "react";', source)
if not react_import or "useRef" not in react_import.group(1): die("current smart-search baseline must import useRef")

backup_page = PAGE.with_suffix(PAGE.suffix + f".audit-v21-r2-backup-{int(time.time())}")
shutil.copy2(PAGE, backup_page)
live_backup = None

try:
    source = source.replace(IMPORT_V1, IMPORT_V1 + "\n" + IMPORT_V21, 1)

    export_marker = "export function AuditLogPage"
    if source.count(export_marker) != 1: raise RuntimeError("AuditLogPage export marker not unique")
    source = source.replace(export_marker, HELPERS + "\n\n" + export_marker, 1)

    from_pattern = re.compile(r'<input\s+type="date"\s+value=\{filters\.from\}\s+onChange=\{\(e\)\s*=>\s*updateFilter\("from",\s*e\.target\.value\)\}\s+className="[^"]+"\s*/>')
    to_pattern = re.compile(r'<input\s+type="date"\s+value=\{filters\.to\}\s+onChange=\{\(e\)\s*=>\s*updateFilter\("to",\s*e\.target\.value\)\}\s+className="[^"]+"\s*/>')
    source, from_count = from_pattern.subn('<AuditV21LuxuryDatePicker value={filters.from} onChange={(value) => updateFilter("from", value)} isEnglish={isEnglish} align="end" />', source, count=1)
    source, to_count = to_pattern.subn('<AuditV21LuxuryDatePicker value={filters.to} onChange={(value) => updateFilter("to", value)} isEnglish={isEnglish} align="start" />', source, count=1)
    if from_count != 1 or to_count != 1: raise RuntimeError(f"exact native date replacement failed: from={from_count}, to={to_count}")

    chip_pattern = re.compile(r'(</label>\s*)(\{\[\s*\["severity")')
    source, chip_count = chip_pattern.subn(r'\1<AuditV21SmartQueryChips query={searchInput} isEnglish={isEnglish} />\n          \2', source, count=1)
    if chip_count != 1: raise RuntimeError(f"smart chips insertion failed: count={chip_count}")

    if 'type="date"' in source: raise RuntimeError("native date input remained after R2 conversion")
    if source.count("AuditV21LuxuryDatePicker") < 3: raise RuntimeError("custom datepicker component/usage verification failed")
    if "AuditV21SmartQueryChips query={searchInput}" not in source: raise RuntimeError("smart chips runtime usage marker missing")
    if "function parseSmartSearch(raw)" not in source or "function useVoiceSearch(onResult, onError)" not in source: raise RuntimeError("existing Smart Search / Voice helpers were not preserved")

    PAGE.write_text(source)
    V21_STYLE.write_text(CSS)

    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists(): raise RuntimeError("frontend dist missing after build")

    built_css = "".join(p.read_text(errors="ignore") for p in DIST.rglob("*.css"))
    built_js = "".join(p.read_text(errors="ignore") for p in DIST.rglob("*.js"))
    if "--tos-audit-log-flagship-v2-1-r2-runtime" not in built_css: raise RuntimeError("R2 CSS runtime marker missing from built assets")
    for marker in ["tos-audit-v21-calendar", "tos-audit-v21-smart-chips"]:
        if marker not in built_css or marker not in built_js: raise RuntimeError(f"R2 runtime class marker missing from built assets: {marker}")

    LIVE_PARENT.mkdir(parents=True, exist_ok=True)
    stamp = int(time.time())
    staging = LIVE_PARENT / f"build.audit-log-v2-1-r2-staging-{stamp}"
    live_backup = LIVE_PARENT / f"build.audit-log-v2-1-r2-backup-{stamp}"
    if staging.exists(): shutil.rmtree(staging)
    shutil.copytree(DIST, staging)
    if LIVE.exists(): LIVE.rename(live_backup)
    try:
        staging.rename(LIVE)
    except Exception:
        if live_backup.exists() and not LIVE.exists(): live_backup.rename(LIVE)
        raise

    print("PASS/FAIL=PASS")
    print("BUILD_RESULT=PASS")
    print("LIVE_DEPLOY=PASS")
    print("AUDIT_LOG_FLAGSHIP_V2_1_R2_RUNTIME=YES")
    print("AUDIT_BASELINE=SMART_SEARCH_NATIVE_DATE_EXACT_SHA")
    print("AUDIT_PAGE_BASELINE_SHA256=" + EXPECTED_PAGE_SHA256)
    print("AUDIT_DATEPICKER=CUSTOM_LUXURY_POPOVER")
    print("AUDIT_NATIVE_DATE_INPUTS_REMAINING=0")
    print("AUDIT_DATEPICKER_BLANK_CANVAS_BUG=ELIMINATED_BY_CUSTOM_POPOVER")
    print("AUDIT_SMART_SEARCH=PRESERVED")
    print("AUDIT_SMART_CHIPS=PARSED_QUERY_VISUALIZATION")
    print("AUDIT_VOICE_SEARCH=PRESERVED")
    print("AUDIT_LIGHT_MODE=PEARL_CHAMPAGNE")
    print("AUDIT_DARK_MODE=OBSIDIAN_TITANIUM_CHAMPAGNE")
    print("AUDIT_API_CHANGED=NO")
    print("AUDIT_FILTER_QUERY_CONTRACT_CHANGED=NO")
    print("AUDIT_EXPORT_LOGIC_CHANGED=NO")
    print("AUDIT_RETENTION_LOGIC_CHANGED=NO")
    print("AUDIT_APPEND_ONLY_CHANGED=NO")
    print("DATABASE_CHANGED=NO")
    print("TWS_CHANGED=NO")
    print("SLA_CHANGED=NO")
    print("RAMZY_CHANGED=NO")
    print("TCS_CHANGED=NO")
    print(f"AUDIT_PAGE_SHA256_AFTER={sha256(PAGE)}")
    print(f"AUDIT_V21_R2_STYLE_SHA256={sha256(V21_STYLE)}")
    print(f"LIVE_BACKUP={live_backup if live_backup and live_backup.exists() else 'NONE'}")
    print("STATUS=READY")
except Exception as exc:
    try:
        if backup_page.exists(): shutil.copy2(backup_page, PAGE)
        if V21_STYLE.exists(): V21_STYLE.unlink()
    except Exception:
        pass
    print("PASS/FAIL=FAIL")
    print(f"ERROR={exc}")
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("STATUS=STOPPED")
    raise SystemExit(1)
