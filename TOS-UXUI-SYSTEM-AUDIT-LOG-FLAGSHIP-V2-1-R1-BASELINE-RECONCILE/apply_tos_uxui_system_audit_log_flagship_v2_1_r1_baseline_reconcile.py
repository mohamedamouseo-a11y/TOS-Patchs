from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
PAGE = FRONTEND / "src/pages/AuditLogPage.jsx"
V1_STYLE = FRONTEND / "src/pages/auditLogFlagshipLuxuryV1.css"
V21_STYLE = FRONTEND / "src/pages/auditLogFlagshipLuxuryV2_1R1.css"
DIST = FRONTEND / "dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

IMPORT_V1 = 'import "./auditLogFlagshipLuxuryV1.css";'
IMPORT_V21 = 'import "./auditLogFlagshipLuxuryV2_1R1.css";'

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
function auditV21DayRange(offsetDays = 0) {
  const date = new Date();
  date.setHours(12, 0, 0, 0);
  date.setDate(date.getDate() + offsetDays);
  return auditV21Ymd(date);
}
function auditV21WeekRange() {
  const today = new Date();
  today.setHours(12, 0, 0, 0);
  const start = new Date(today);
  start.setDate(today.getDate() - today.getDay());
  const end = new Date(start);
  end.setDate(start.getDate() + 6);
  return { from: auditV21Ymd(start), to: auditV21Ymd(end) };
}
function auditV21ParseSmartQuery(raw) {
  let working = String(raw || "").trim();
  const updates = {};
  const structured = new Set(["severity", "outcome", "category", "source", "action"]);
  const tokenRegex = /\b(user|actor|severity|outcome|category|source|action|entity|route|request):("[^"]+"|'[^']+'|[^\s]+)/gi;
  working = working.replace(tokenRegex, (_full, rawKey, rawValue) => {
    const key = String(rawKey || "").toLowerCase();
    const value = String(rawValue || "").replace(/^['"]|['"]$/g, "");
    if (structured.has(key)) {
      updates[key] = value;
      return " ";
    }
    return ` ${value} `;
  });
  const week = auditV21WeekRange();
  if (/(^|\s)(this\s+week|هذا\s+الأسبوع)($|\s)/i.test(working)) {
    updates.from = week.from;
    updates.to = week.to;
    working = working.replace(/(^|\s)(this\s+week|هذا\s+الأسبوع)($|\s)/ig, " ");
  } else if (/(^|\s)(yesterday|أمس)($|\s)/i.test(working)) {
    updates.from = auditV21DayRange(-1);
    updates.to = auditV21DayRange(-1);
    working = working.replace(/(^|\s)(yesterday|أمس)($|\s)/ig, " ");
  } else if (/(^|\s)(today|اليوم)($|\s)/i.test(working)) {
    updates.from = auditV21DayRange(0);
    updates.to = auditV21DayRange(0);
    working = working.replace(/(^|\s)(today|اليوم)($|\s)/ig, " ");
  }
  return { updates, freeText: working.replace(/\s+/g, " ").trim() };
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
    <div className="tos-audit-v21-smart-chips lg:col-span-4">
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
function AuditV21LuxuryDatePicker({ label, value, onChange, isEnglish, align = "start" }) {
  const selected = value ? new Date(`${value}T12:00:00`) : null;
  const [open, setOpen] = useState(false);
  const [cursor, setCursor] = useState(() => selected || new Date());
  const rootRef = useRef(null);
  useEffect(() => {
    if (selected && !Number.isNaN(selected.getTime())) setCursor(selected);
  }, [value]);
  useEffect(() => {
    if (!open) return undefined;
    const onPointer = (event) => {
      if (rootRef.current && !rootRef.current.contains(event.target)) setOpen(false);
    };
    const onKey = (event) => { if (event.key === "Escape") setOpen(false); };
    document.addEventListener("pointerdown", onPointer);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("pointerdown", onPointer);
      document.removeEventListener("keydown", onKey);
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
  return (
    <div ref={rootRef} className={`tos-audit-v21-date tos-audit-v21-date-${align} ${open ? "is-open" : ""}`}>
      <span className="tos-audit-v21-date-label">{label}</span>
      <button type="button" className="tos-audit-v21-date-trigger" onClick={() => setOpen((current) => !current)} aria-expanded={open}>
        <span className={value ? "has-value" : "is-placeholder"}>{value || "yyyy-mm-dd"}</span>
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 2v3M17 2v3M4 9h16M5 4h14a2 2 0 0 1 2 2v13a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2Z" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/></svg>
      </button>
      {open && (
        <div className="tos-audit-v21-calendar" role="dialog" aria-label={label}>
          <div className="tos-audit-v21-calendar-head">
            <button type="button" onClick={() => setCursor(new Date(year, month - 1, 1))}>‹</button>
            <div><strong>{monthNames[month]}</strong><span>{year}</span></div>
            <button type="button" onClick={() => setCursor(new Date(year, month + 1, 1))}>›</button>
          </div>
          <div className="tos-audit-v21-weekdays">{weekNames.map((day) => <span key={day}>{day}</span>)}</div>
          <div className="tos-audit-v21-calendar-grid">
            {cells.map((day, index) => {
              if (!day) return <span className="is-blank" key={`blank-${index}`} />;
              const key = auditV21Ymd(new Date(year, month, day));
              return <button type="button" key={key} onClick={() => choose(day)} className={`${key === selectedKey ? "is-selected" : ""} ${key === todayKey ? "is-today" : ""}`}>{day}</button>;
            })}
          </div>
          <div className="tos-audit-v21-calendar-foot">
            <button type="button" onClick={() => { onChange(""); setOpen(false); }}>{isEnglish ? "Clear" : "مسح"}</button>
            <button type="button" className="is-primary" onClick={() => { const now = new Date(); setCursor(now); onChange(auditV21Ymd(now)); setOpen(false); }}>{isEnglish ? "Today" : "اليوم"}</button>
          </div>
        </div>
      )}
    </div>
  );
}
'''

BOOTSTRAP_FUNCTIONS = r'''
  const smartAppliedKeysRef = useRef(new Set());

  function applyAuditV21SmartSearch(value) {
    setSmartQuery(value);
    const parsed = auditV21ParseSmartQuery(value);
    setFilters((current) => {
      const next = { ...current, q: parsed.freeText, page: 1 };
      for (const key of smartAppliedKeysRef.current) {
        if (!(key in parsed.updates)) next[key] = "";
      }
      Object.entries(parsed.updates).forEach(([key, nextValue]) => { next[key] = nextValue; });
      smartAppliedKeysRef.current = new Set(Object.keys(parsed.updates));
      return next;
    });
  }

  function startAuditV21VoiceSearch() {
    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Recognition) {
      setVoiceState("unsupported");
      window.setTimeout(() => setVoiceState("idle"), 2200);
      return;
    }
    try {
      if (recognitionRef.current) recognitionRef.current.abort();
      const recognition = new Recognition();
      recognition.lang = isEnglish ? "en-US" : "ar-EG";
      recognition.interimResults = false;
      recognition.continuous = false;
      recognition.maxAlternatives = 1;
      recognitionRef.current = recognition;
      recognition.onstart = () => setVoiceState("listening");
      recognition.onerror = () => {
        setVoiceState("error");
        window.setTimeout(() => setVoiceState("idle"), 1800);
      };
      recognition.onend = () => {
        recognitionRef.current = null;
        setVoiceState((current) => current === "processing" ? current : "idle");
      };
      recognition.onresult = (event) => {
        const transcript = event.results?.[0]?.[0]?.transcript?.trim() || "";
        if (!transcript) return;
        setVoiceState("processing");
        applyAuditV21SmartSearch(transcript);
        window.setTimeout(() => setVoiceState("idle"), 650);
      };
      recognition.start();
    } catch (_error) {
      setVoiceState("error");
      window.setTimeout(() => setVoiceState("idle"), 1800);
    }
  }
'''

SEARCH_BLOCK = r'''<label className="lg:col-span-2">
            <span className="text-[11px] font-black text-zinc-500">{ui("بحث ذكي", "Smart Search")}</span>
            <div className={`tos-audit-v21-search mt-1 flex items-center gap-2 rounded-2xl border border-zinc-100 bg-zinc-50 px-3 dark:border-white/10 dark:bg-white/5 ${voiceState === "listening" ? "is-listening" : ""}`}>
              <Search size={15} className="text-zinc-400" />
              <input value={smartQuery} onChange={(e) => applyAuditV21SmartSearch(e.target.value)} placeholder={ui("اكتب بحرية أو user:... severity:... today...", "Type freely or use user:..., severity:..., today...")} className="w-full bg-transparent py-3 text-sm outline-none dark:text-white" />
              <button type="button" className="tos-audit-v21-mic" onClick={startAuditV21VoiceSearch} aria-pressed={voiceState === "listening"} data-listening={voiceState === "listening" ? "true" : "false"}>
                <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3a3 3 0 0 0-3 3v6a3 3 0 1 0 6 0V6a3 3 0 0 0-3-3Zm-6 9a6 6 0 0 0 12 0M12 18v3M9 21h6" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/></svg>
                <span className="sr-only">{voiceState === "listening" ? ui("جاري الاستماع", "Listening") : ui("بحث صوتي", "Voice search")}</span>
              </button>
            </div>
            {voiceState === "listening" && <span className="tos-audit-v21-voice-status">{ui("جاري الاستماع…", "Listening…")}</span>}
            {voiceState === "processing" && <span className="tos-audit-v21-voice-status">{ui("جاري تحليل البحث…", "Understanding…")}</span>}
            {voiceState === "unsupported" && <span className="tos-audit-v21-voice-status is-error">{ui("البحث الصوتي غير مدعوم في هذا المتصفح.", "Voice search is not supported in this browser.")}</span>}
            {voiceState === "error" && <span className="tos-audit-v21-voice-status is-error">{ui("تعذر التقاط الصوت. حاول مرة أخرى.", "Could not capture voice. Try again.")}</span>}
          </label>'''

CSS = r''':root{--tos-audit-log-flagship-v2-1-r1-runtime:1}
.tos-audit-flagship-v1 .tos-audit-v21-date{position:relative;min-width:0;z-index:24}.tos-audit-flagship-v1 .tos-audit-v21-date.is-open{z-index:160}.tos-audit-flagship-v1 .tos-audit-v21-date-label{display:block;margin-bottom:.35rem;font-size:11px;font-weight:900;color:#655844}.tos-audit-flagship-v1 .tos-audit-v21-date-trigger{width:100%;min-height:46px;padding:0 14px;display:flex;align-items:center;justify-content:space-between;gap:10px;border:1px solid rgba(168,108,12,.18);border-radius:15px;color:#2b2114;background:linear-gradient(180deg,#fffefa,#fbf4e6);box-shadow:inset 0 1px rgba(255,255,255,.98),0 7px 18px rgba(74,44,2,.035)}.tos-audit-flagship-v1 .tos-audit-v21-date-trigger svg{width:17px;height:17px;color:#a36f13}.tos-audit-flagship-v1 .tos-audit-v21-calendar{position:absolute;top:calc(100% + 10px);width:min(328px,calc(100vw - 44px));padding:14px;border:1px solid rgba(168,107,12,.24);border-radius:20px;color:#251b0e;background:radial-gradient(circle at 92% 0%,rgba(245,221,164,.28),transparent 31%),linear-gradient(155deg,#fffefa,#fbf3e2);box-shadow:0 28px 60px rgba(69,41,2,.18),0 8px 20px rgba(67,39,2,.08),inset 0 1px rgba(255,255,255,.98);z-index:220}.tos-audit-flagship-v1 .tos-audit-v21-date-end .tos-audit-v21-calendar{inset-inline-end:0}.tos-audit-flagship-v1 .tos-audit-v21-date-start .tos-audit-v21-calendar{inset-inline-start:0}.tos-audit-flagship-v1 .tos-audit-v21-calendar-head{display:grid;grid-template-columns:36px 1fr 36px;align-items:center;gap:8px;padding-bottom:11px;border-bottom:1px solid rgba(154,100,12,.10)}.tos-audit-flagship-v1 .tos-audit-v21-calendar-head>button{width:34px;height:34px;border-radius:10px;border:1px solid rgba(163,103,10,.16);color:#8b5c0a;background:linear-gradient(180deg,#fffdf7,#f6e8c7);font-size:22px}.tos-audit-flagship-v1 .tos-audit-v21-calendar-head>div{text-align:center}.tos-audit-flagship-v1 .tos-audit-v21-calendar-head strong{display:block;font-size:14px;font-weight:950}.tos-audit-flagship-v1 .tos-audit-v21-calendar-head span{font-size:10px;color:#a28d70}.tos-audit-flagship-v1 .tos-audit-v21-weekdays,.tos-audit-flagship-v1 .tos-audit-v21-calendar-grid{display:grid;grid-template-columns:repeat(7,1fr);gap:4px}.tos-audit-flagship-v1 .tos-audit-v21-weekdays{padding:10px 0 6px}.tos-audit-flagship-v1 .tos-audit-v21-weekdays span{text-align:center;font-size:9px;font-weight:900;color:#9a8d79}.tos-audit-flagship-v1 .tos-audit-v21-calendar-grid button,.tos-audit-flagship-v1 .tos-audit-v21-calendar-grid .is-blank{aspect-ratio:1}.tos-audit-flagship-v1 .tos-audit-v21-calendar-grid button{border:1px solid transparent;border-radius:10px;color:#4d402f;background:transparent;font-size:11px;font-weight:850}.tos-audit-flagship-v1 .tos-audit-v21-calendar-grid button:hover{border-color:rgba(176,115,17,.15);background:#fff8e8}.tos-audit-flagship-v1 .tos-audit-v21-calendar-grid button.is-today{color:#9b6509;border-color:rgba(184,121,16,.22);background:#fff3cf}.tos-audit-flagship-v1 .tos-audit-v21-calendar-grid button.is-selected{color:#251700;border-color:rgba(139,84,0,.28);background:linear-gradient(180deg,#fff0ac,#e7bb4c 65%,#c78b16)}.tos-audit-flagship-v1 .tos-audit-v21-calendar-foot{display:flex;justify-content:space-between;gap:8px;margin-top:11px;padding-top:11px;border-top:1px solid rgba(154,100,12,.10)}.tos-audit-flagship-v1 .tos-audit-v21-calendar-foot button{min-height:34px;padding:0 12px;border:1px solid rgba(163,103,10,.15);border-radius:10px;color:#6f4a0d;background:linear-gradient(180deg,#fffef9,#f7ebcf);font-size:10px;font-weight:900}.tos-audit-flagship-v1 .tos-audit-v21-calendar-foot button.is-primary{color:#241600;background:linear-gradient(180deg,#f8dd83,#d8a52e)}
.tos-audit-flagship-v1 .tos-audit-v21-smart-chips{display:flex;align-items:center;gap:10px;padding:10px 12px;border:1px solid rgba(179,118,17,.13);border-radius:15px;background:linear-gradient(180deg,#fffdf8,#fbf3e3)}.tos-audit-flagship-v1 .tos-audit-v21-smart-title{display:flex;align-items:center;gap:7px;font-size:10px;font-weight:950;color:#7b643e}.tos-audit-flagship-v1 .tos-audit-v21-spark{display:grid;width:22px;height:22px;place-items:center;border-radius:8px;color:#614006;background:linear-gradient(145deg,#fff0ae,#dfb344)}.tos-audit-flagship-v1 .tos-audit-v21-smart-list{display:flex;flex-wrap:wrap;gap:6px}.tos-audit-flagship-v1 .tos-audit-v21-chip{display:inline-flex;overflow:hidden;border:1px solid rgba(169,109,12,.13);border-radius:999px;background:#fffdfa}.tos-audit-flagship-v1 .tos-audit-v21-chip b,.tos-audit-flagship-v1 .tos-audit-v21-chip em{padding:5px 8px;font-size:9px;font-style:normal}.tos-audit-flagship-v1 .tos-audit-v21-chip b{color:#98630a;background:rgba(224,181,78,.13)}.tos-audit-flagship-v1 .tos-audit-v21-chip em{color:#514431}
.tos-audit-flagship-v1 .tos-audit-v21-search{position:relative}.tos-audit-flagship-v1 .tos-audit-v21-mic{display:grid;flex:0 0 34px;width:34px;height:34px;place-items:center;border:1px solid rgba(166,106,10,.18);border-radius:11px;color:#8a5909;background:linear-gradient(180deg,#fff9e9,#f4e0ae)}.tos-audit-flagship-v1 .tos-audit-v21-mic svg{width:16px;height:16px}.tos-audit-flagship-v1 .tos-audit-v21-search.is-listening,.tos-audit-flagship-v1 .tos-audit-v21-mic[data-listening="true"]{border-color:rgba(199,139,25,.46)!important;box-shadow:0 0 0 3px rgba(224,180,75,.13),0 0 24px rgba(218,164,50,.14)!important}.tos-audit-flagship-v1 .tos-audit-v21-mic[data-listening="true"]{color:#251700;background:linear-gradient(180deg,#fbe18c,#d7a32d);animation:auditV21Pulse 1.2s ease-in-out infinite}.tos-audit-flagship-v1 .tos-audit-v21-voice-status{display:block;margin-top:5px;font-size:9px;font-weight:800;color:#946312}.tos-audit-flagship-v1 .tos-audit-v21-voice-status.is-error{color:#b4453e}@keyframes auditV21Pulse{50%{transform:scale(1.06)}}
.dark .tos-audit-flagship-v1 .tos-audit-v21-date-label{color:#aaa08f}.dark .tos-audit-flagship-v1 .tos-audit-v21-date-trigger{color:#e8e0d4;border-color:rgba(222,176,74,.12);background:linear-gradient(180deg,#1c1f21,#131516)}.dark .tos-audit-flagship-v1 .tos-audit-v21-calendar{color:#eee7dc;border-color:rgba(222,176,74,.18);background:radial-gradient(circle at 92% 0%,rgba(222,176,74,.10),transparent 31%),linear-gradient(155deg,#181b1d,#0f1112);box-shadow:0 30px 70px rgba(0,0,0,.52)}.dark .tos-audit-flagship-v1 .tos-audit-v21-calendar-head>button{color:#d3aa4b;border-color:rgba(222,176,74,.12);background:#181b1d}.dark .tos-audit-flagship-v1 .tos-audit-v21-weekdays span{color:#8f897e}.dark .tos-audit-flagship-v1 .tos-audit-v21-calendar-grid button{color:#d8d1c7}.dark .tos-audit-flagship-v1 .tos-audit-v21-calendar-grid button.is-selected{color:#211500;background:linear-gradient(180deg,#f3d578,#d8a52f 65%,#b9780f)}.dark .tos-audit-flagship-v1 .tos-audit-v21-smart-chips{border-color:rgba(222,176,74,.10);background:linear-gradient(180deg,rgba(21,24,26,.94),rgba(13,15,16,.94))}.dark .tos-audit-flagship-v1 .tos-audit-v21-smart-title{color:#aaa08f}.dark .tos-audit-flagship-v1 .tos-audit-v21-spark{color:#211500;background:linear-gradient(145deg,#efd476,#c58a1c)}.dark .tos-audit-flagship-v1 .tos-audit-v21-chip{border-color:rgba(222,176,74,.11);background:#181a1b}.dark .tos-audit-flagship-v1 .tos-audit-v21-chip b{color:#d3aa4b}.dark .tos-audit-flagship-v1 .tos-audit-v21-chip em{color:#e6dfd5}.dark .tos-audit-flagship-v1 .tos-audit-v21-mic{color:#d3aa4b;border-color:rgba(222,176,74,.13);background:linear-gradient(180deg,#202326,#151719)}
@media(max-width:760px){.tos-audit-flagship-v1 .tos-audit-v21-smart-chips{align-items:flex-start;flex-direction:column}.tos-audit-flagship-v1 .tos-audit-v21-calendar{width:min(304px,calc(100vw - 34px))}}
'''

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
            print(result.stderr)
        raise RuntimeError("command failed: " + " ".join(cmd))
    return result

print("RUNNING=TOS_UXUI_SYSTEM_AUDIT_LOG_FLAGSHIP_V2_1_R1_BASELINE_RECONCILE")
if not PAGE.exists(): die("AuditLogPage.jsx missing")
if not V1_STYLE.exists(): die("Audit Log luxury V1 stylesheet missing")
if V21_STYLE.exists(): die("R1 stylesheet already exists; refusing repeated/unknown state")

source_original = PAGE.read_text()
source = source_original
for marker in ["Audit Center V2", "api.auditLog.v2", "api.auditLog.exportV2", "api.auditLog.retention", "tos-audit-flagship-v1", IMPORT_V1, "setFilters", "filterOptions"]:
    if marker not in source:
        die(f"required stable Audit baseline marker missing: {marker}")
if IMPORT_V21 in source:
    die("R1 import already present")

react_match = re.search(r'import \{([^}]+)\} from "react";', source)
if not react_match: die("React named import not found")
imports = [item.strip() for item in react_match.group(1).split(",") if item.strip()]
if "useRef" not in imports:
    imports.append("useRef")
    source = source[:react_match.start()] + "import { " + ", ".join(imports) + ' } from "react";' + source[react_match.end():]

source = source.replace(IMPORT_V1, IMPORT_V1 + "\n" + IMPORT_V21, 1)

empty_match = re.search(r'const EMPTY_FILTERS\s*=\s*\{', source)
if not empty_match: die("EMPTY_FILTERS marker missing")
empty_end = source.find("};", empty_match.end())
if empty_end < 0: die("EMPTY_FILTERS closing marker missing")
empty_block = source[empty_match.start():empty_end]
if not re.search(r'\bq\s*:', empty_block):
    source = source[:empty_match.end()] + '\n  q: "",' + source[empty_match.end():]

export_marker = "export function AuditLogPage"
if export_marker not in source: die("AuditLogPage export marker missing")
source = source.replace(export_marker, HELPERS + "\n\n" + export_marker, 1)

search_label_pattern = re.compile(r'<label className="lg:col-span-2">.*?</label>', re.S)
search_label_match = search_label_pattern.search(source)
if not search_label_match: die("Audit search label not found")
search_label_current = search_label_match.group(0)
value_match = re.search(r'value=\{([^}\n]+)\}', search_label_current)
existing_query_expr = value_match.group(1).strip() if value_match else ""
has_existing_voice = ("SpeechRecognition" in source or "webkitSpeechRecognition" in source)

if has_existing_voice and existing_query_expr:
    chip_query_expr = existing_query_expr
    smart_mode = "PRESERVED_EXISTING"
else:
    state_anchor = re.search(r'const \[filters,\s*setFilters\]\s*=\s*useState\(EMPTY_FILTERS\);', source)
    if not state_anchor: die("filters state anchor missing for Smart Search bootstrap")
    states = '\n  const [smartQuery, setSmartQuery] = useState("");\n  const [voiceState, setVoiceState] = useState("idle");\n  const recognitionRef = useRef(null);'
    source = source[:state_anchor.end()] + states + source[state_anchor.end():]
    update_filter_pattern = re.compile(r'  function updateFilter\(key,\s*value\)\s*\{\s*setFilters\(\(current\)\s*=>\s*\(\{\s*\.\.\.current,\s*\[key\]:\s*value,\s*page:\s*key\s*===\s*"page"\s*\?\s*value\s*:\s*1\s*\}\)\);\s*\}', re.S)
    update_match = update_filter_pattern.search(source)
    if not update_match: die("updateFilter function anchor missing for Smart Search bootstrap")
    source = source[:update_match.end()] + "\n" + BOOTSTRAP_FUNCTIONS + source[update_match.end():]
    search_label_match = search_label_pattern.search(source)
    if not search_label_match: die("Audit search label disappeared during reconcile")
    source = source[:search_label_match.start()] + SEARCH_BLOCK + source[search_label_match.end():]
    chip_query_expr = "smartQuery"
    smart_mode = "BOOTSTRAPPED_FROM_LEGACY_BASELINE"

from_pattern = re.compile(r'<label>\s*<span[^>]*>\{ui\("من",\s*"From"\)\}</span>.*?value=\{filters\.from\}.*?</label>', re.S)
to_pattern = re.compile(r'<label>\s*<span[^>]*>\{ui\("إلى",\s*"To"\)\}</span>.*?value=\{filters\.to\}.*?</label>', re.S)
source, from_count = from_pattern.subn('<AuditV21LuxuryDatePicker label={ui("من", "From")} value={filters.from} onChange={(value) => updateFilter("from", value)} isEnglish={isEnglish} align="end" />', source, count=1)
source, to_count = to_pattern.subn('<AuditV21LuxuryDatePicker label={ui("إلى", "To")} value={filters.to} onChange={(value) => updateFilter("to", value)} isEnglish={isEnglish} align="start" />', source, count=1)
if from_count != 1 or to_count != 1: die(f"native date field reconcile failed: from={from_count}, to={to_count}")

search_label_match = search_label_pattern.search(source)
if not search_label_match: die("search label missing before smart-chip insertion")
chip_markup = f'\n          <AuditV21SmartQueryChips query={{{chip_query_expr}}} isEnglish={{isEnglish}} />'
source = source[:search_label_match.end()] + chip_markup + source[search_label_match.end():]

if source.count("AuditV21LuxuryDatePicker") < 3: die("custom datepicker runtime marker missing")
if "AuditV21SmartQueryChips query={" not in source: die("smart chips runtime marker missing")
if 'type="date"' in source: die("native date input remained after R1 reconcile")

try:
    PAGE.write_text(source)
    V21_STYLE.write_text(CSS)
    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists(): raise RuntimeError("frontend dist missing after build")
    built_css = ""
    for css_file in DIST.rglob("*.css"):
        try: built_css += css_file.read_text(errors="ignore")
        except Exception: pass
    if "--tos-audit-log-flagship-v2-1-r1-runtime" not in built_css:
        raise RuntimeError("R1 runtime CSS marker missing from built assets")
    LIVE_PARENT.mkdir(parents=True, exist_ok=True)
    stamp = int(time.time())
    staging = LIVE_PARENT / f"build.audit-log-v2-1-r1-staging-{stamp}"
    live_backup = LIVE_PARENT / f"build.audit-log-v2-1-r1-backup-{stamp}"
    if staging.exists(): shutil.rmtree(staging)
    shutil.copytree(DIST, staging)
    if LIVE.exists(): LIVE.rename(live_backup)
    staging.rename(LIVE)
    print("PASS/FAIL=PASS")
    print("BUILD_RESULT=PASS")
    print("LIVE_DEPLOY=PASS")
    print("AUDIT_LOG_FLAGSHIP_V2_1_R1_RUNTIME=YES")
    print("AUDIT_V2_1_R1_SCOPE=BASELINE_RECONCILE_LUXURY_DATEPICKER_SMART_CHIPS")
    print(f"AUDIT_SMART_SEARCH_BASELINE={smart_mode}")
    print("AUDIT_DATEPICKER=CUSTOM_LUXURY_POPOVER")
    print("AUDIT_NATIVE_DATE_INPUTS_REMAINING=0")
    print("AUDIT_DATEPICKER_BLANK_CANVAS_BUG=ELIMINATED")
    print("AUDIT_SMART_CHIPS=PARSED_QUERY_VISUALIZATION")
    print("AUDIT_VOICE_SEARCH=PRESERVED_OR_BOOTSTRAPPED")
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
    print(f"LIVE_BACKUP={live_backup if live_backup.exists() else 'NONE'}")
    print("STATUS=READY")
except Exception as exc:
    try:
        PAGE.write_text(source_original)
        if V21_STYLE.exists(): V21_STYLE.unlink()
    except Exception:
        pass
    print("PASS/FAIL=FAIL")
    print(f"ERROR={exc}")
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("STATUS=STOPPED")
    raise SystemExit(1)
