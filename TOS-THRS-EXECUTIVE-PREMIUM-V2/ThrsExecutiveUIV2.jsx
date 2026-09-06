import { useEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { Mic, MicOff, Search, Sparkles, UserRound, X } from "lucide-react";
import "./employeeWorkHubThrsExecutiveV2.css";

const ROLE_LABELS = {
  SUPER_ADMIN: { ar: "مدير النظام", en: "System Manager" },
  ADMIN: { ar: "مدير", en: "Admin" },
  MANAGER: { ar: "قائد فريق", en: "Team Lead" },
  PROJECT_MANAGER: { ar: "مدير مشاريع", en: "Project Manager" },
  TEAM_MEMBER: { ar: "عضو فريق", en: "Team Member" },
};

const REQUEST_TYPE_LABELS = {
  LEAVE: { ar: "طلب إجازة", en: "Leave Request" },
  SCHEDULE_CHANGE: { ar: "طلب تعديل مواعيد", en: "Schedule Change Request" },
  ATTENDANCE_CORRECTION: { ar: "طلب تصحيح حضور", en: "Attendance Correction Request" },
  OVERTIME: { ar: "طلب عمل إضافي", en: "Overtime Request" },
  SHIFT_SWAP: { ar: "طلب تبديل شيفت", en: "Shift Swap Request" },
};

const STATUS_LABELS = {
  PENDING_SHADOW_APPROVAL: { ar: "في انتظار موافقة موظف التغطية", en: "Pending shadow approval" },
  PENDING_SHADOW_RESELECTION: { ar: "إعادة اختيار موظف تغطية", en: "Shadow reselection" },
  PENDING_TOS_REVIEW: { ar: "في انتظار TOS", en: "Pending TOS" },
  APPROVED_BY_TOS_PENDING_THRS: { ar: "مقبول من TOS — انتظار THRS", en: "TOS approved — pending THRS" },
  SENT_TO_THRS: { ar: "في انتظار HR", en: "Pending HR" },
  THRS_APPROVED_FINAL: { ar: "مقبول نهائيًا", en: "Final approved" },
  THRS_REJECTED: { ar: "مرفوض من THRS", en: "Rejected by THRS" },
  THRS_SYNC_FAILED: { ar: "فشل مزامنة THRS", en: "THRS sync failed" },
  PENDING_TEAM_LEAD: { ar: "في انتظار المسؤول", en: "Pending manager" },
  PENDING_HR: { ar: "في انتظار HR", en: "Pending HR" },
  APPROVED: { ar: "مقبول", en: "Approved" },
  REJECTED: { ar: "مرفوض", en: "Rejected" },
  CANCELLED: { ar: "ملغي", en: "Cancelled" },
};

function normalizeSmartText(value) {
  return String(value || "")
    .normalize("NFKD")
    .toLowerCase()
    .replace(/[أإآ]/g, "ا")
    .replace(/ى/g, "ي")
    .replace(/ة/g, "ه")
    .replace(/[\u064B-\u065F]/g, "")
    .replace(/[_\-/]+/g, " ")
    .replace(/[^\p{L}\p{N}@. ]+/gu, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function requestTypeValue(row) {
  return String(row?.requestType || row?.type || row?.metadata?.requestType || "").trim();
}

function labelFor(map, value, isAr) {
  return map?.[value]?.[isAr ? "ar" : "en"] || String(value || "").replace(/_/g, " ") || "—";
}

function smartRowText(row, isAr) {
  const requester = row?.requester || {};
  const type = requestTypeValue(row);
  const role = requester.role || row?.requesterRole || "";
  const status = row?.status || "";
  return [
    requester.name,
    requester.email,
    requester.department,
    requester.departmentName,
    role,
    labelFor(ROLE_LABELS, role, isAr),
    type,
    labelFor(REQUEST_TYPE_LABELS, type, isAr),
    status,
    labelFor(STATUS_LABELS, status, isAr),
    row?.startDate,
    row?.endDate,
  ].filter(Boolean).join(" ");
}

function fuzzyScore(text, query) {
  const haystack = normalizeSmartText(text);
  const needle = normalizeSmartText(query);
  if (!needle) return 0;
  if (haystack === needle) return 120;
  if (haystack.startsWith(needle)) return 100;
  if (haystack.includes(needle)) return 80;
  const tokens = needle.split(" ").filter(Boolean);
  const hits = tokens.filter((token) => haystack.includes(token)).length;
  if (hits === tokens.length) return 60 + hits;
  return hits ? 20 + hits : 0;
}

function initials(value) {
  const words = String(value || "").trim().split(/\s+/).filter(Boolean);
  if (!words.length) return "•";
  return words.slice(0, 2).map((word) => word[0]?.toUpperCase()).join("");
}

function MarkMatch({ text, query }) {
  const raw = String(text || "");
  const needle = String(query || "").trim();
  if (!needle) return raw;
  const index = raw.toLowerCase().indexOf(needle.toLowerCase());
  if (index < 0) return raw;
  return <>{raw.slice(0, index)}<mark>{raw.slice(index, index + needle.length)}</mark>{raw.slice(index + needle.length)}</>;
}

export function ThrsExecutiveKpiV2({ label, value, max = 0, note = "", tone = "slate", suffix = "" }) {
  const numeric = Number(value) || 0;
  const safeMax = Math.max(Number(max) || numeric || 1, 1);
  const percent = Math.max(0, Math.min(100, Math.round((numeric / safeMax) * 100)));
  return (
    <div className="tos-thrs-kpi-v2" data-tone={tone}>
      <div className="tos-thrs-kpi-ring-v2" style={{ "--tos-thrs-kpi-progress": `${percent}%` }}>
        <div className="tos-thrs-kpi-ring-core-v2"><span>{numeric}{suffix}</span></div>
      </div>
      <div className="tos-thrs-kpi-copy-v2">
        <strong>{label}</strong>
        <span>{note || `${percent}%`}</span>
      </div>
    </div>
  );
}

export function ThrsSmartSearchV2({ value = "", onChange, rows = [], isAr = false }) {
  const [focused, setFocused] = useState(false);
  const [activeIndex, setActiveIndex] = useState(0);
  const [listening, setListening] = useState(false);
  const [voiceAvailable, setVoiceAvailable] = useState(true);
  const [position, setPosition] = useState({ top: 0, left: 0, width: 420, maxHeight: 390, openAbove: false });
  const inputRef = useRef(null);
  const menuRef = useRef(null);
  const recognitionRef = useRef(null);
  const query = String(value || "");

  const suggestions = useMemo(() => {
    const normalized = normalizeSmartText(query);
    if (!normalized) return [];
    const seen = new Set();
    return rows
      .map((row) => ({ row, score: fuzzyScore(smartRowText(row, isAr), normalized) }))
      .filter((entry) => entry.score > 0)
      .sort((a, b) => b.score - a.score)
      .filter((entry) => {
        const requester = entry.row?.requester || {};
        const key = `${requester.id || entry.row?.requesterId || requester.email || requester.name || "person"}|${requestTypeValue(entry.row)}|${entry.row?.status || ""}`;
        if (seen.has(key)) return false;
        seen.add(key);
        return true;
      })
      .slice(0, 8);
  }, [rows, query, isAr]);

  const open = focused && Boolean(query.trim());

  useEffect(() => {
    if (!open) return undefined;
    setActiveIndex(0);
    const sync = () => {
      const rect = inputRef.current?.getBoundingClientRect();
      if (!rect) return;
      const gap = 10;
      const width = Math.min(Math.max(rect.width, 360), Math.max(280, window.innerWidth - gap * 2));
      const left = Math.min(Math.max(gap, rect.left), Math.max(gap, window.innerWidth - width - gap));
      const desiredHeight = Math.min(410, Math.max(180, suggestions.length * 62 + 58));
      const below = Math.max(0, window.innerHeight - rect.bottom - gap);
      const above = Math.max(0, rect.top - gap);
      const openAbove = below < Math.min(320, desiredHeight) && above > below;
      const side = openAbove ? above : below;
      const maxHeight = Math.max(170, Math.min(desiredHeight, side - 8));
      const top = openAbove ? Math.max(gap, rect.top - maxHeight - 8) : rect.bottom + 8;
      setPosition({ top, left, width, maxHeight, openAbove });
    };
    const outside = (event) => {
      if (inputRef.current?.closest?.(".tos-thrs-smart-search-v2")?.contains(event.target) || menuRef.current?.contains(event.target)) return;
      setFocused(false);
    };
    sync();
    window.addEventListener("resize", sync);
    window.addEventListener("scroll", sync, true);
    document.addEventListener("mousedown", outside);
    return () => {
      window.removeEventListener("resize", sync);
      window.removeEventListener("scroll", sync, true);
      document.removeEventListener("mousedown", outside);
    };
  }, [open, suggestions.length]);

  useEffect(() => () => {
    try { recognitionRef.current?.stop?.(); } catch {}
  }, []);

  const emit = (next) => onChange?.({ target: { value: next }, currentTarget: { value: next } });

  const selectSuggestion = (entry) => {
    const requester = entry?.row?.requester || {};
    const next = requester.name || requester.email || labelFor(REQUEST_TYPE_LABELS, requestTypeValue(entry?.row), isAr);
    emit(next);
    setFocused(false);
    requestAnimationFrame(() => inputRef.current?.focus());
  };

  const startVoice = () => {
    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Recognition) {
      setVoiceAvailable(false);
      return;
    }
    if (listening) {
      try { recognitionRef.current?.stop?.(); } catch {}
      setListening(false);
      return;
    }
    const recognition = new Recognition();
    recognitionRef.current = recognition;
    recognition.lang = isAr ? "ar-SA" : "en-US";
    recognition.interimResults = false;
    recognition.continuous = false;
    recognition.maxAlternatives = 1;
    recognition.onstart = () => setListening(true);
    recognition.onend = () => setListening(false);
    recognition.onerror = () => setListening(false);
    recognition.onresult = (event) => {
      const transcript = event?.results?.[0]?.[0]?.transcript || "";
      if (transcript) {
        emit(transcript);
        setFocused(true);
      }
    };
    try { recognition.start(); } catch { setListening(false); }
  };

  const onKeyDown = (event) => {
    if (!open || !suggestions.length) return;
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActiveIndex((current) => (current + 1) % suggestions.length);
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setActiveIndex((current) => (current - 1 + suggestions.length) % suggestions.length);
    } else if (event.key === "Enter") {
      event.preventDefault();
      selectSuggestion(suggestions[activeIndex]);
    } else if (event.key === "Escape") {
      setFocused(false);
    }
  };

  return (
    <div className="tos-thrs-smart-search-v2" dir={isAr ? "rtl" : "ltr"}>
      <Search size={17} className="tos-thrs-smart-search-icon-v2" />
      <input
        ref={inputRef}
        value={query}
        onChange={(event) => { emit(event.target.value); setFocused(true); }}
        onFocus={() => setFocused(true)}
        onKeyDown={onKeyDown}
        autoComplete="off"
        placeholder={isAr ? "ابحث بالاسم، الإيميل، الدور، النوع أو الحالة..." : "Search name, email, role, type or status..."}
        aria-label={isAr ? "بحث ذكي في طلبات THRS" : "Smart THRS request search"}
      />
      <div className="tos-thrs-smart-search-actions-v2">
        {query && <button type="button" onClick={() => { emit(""); inputRef.current?.focus(); }} aria-label={isAr ? "مسح البحث" : "Clear search"}><X size={15} /></button>}
        <button type="button" data-listening={listening ? "true" : "false"} data-unavailable={!voiceAvailable ? "true" : "false"} onClick={startVoice} title={!voiceAvailable ? (isAr ? "البحث الصوتي غير مدعوم في هذا المتصفح" : "Voice search is not supported in this browser") : (isAr ? "بحث صوتي" : "Voice search")} aria-label={isAr ? "بحث صوتي" : "Voice search"}>{listening ? <MicOff size={16} /> : <Mic size={16} />}</button>
      </div>
      {open && createPortal(
        <div ref={menuRef} className="tos-thrs-smart-search-menu-v2" dir={isAr ? "rtl" : "ltr"} data-placement={position.openAbove ? "top" : "bottom"} style={{ position: "fixed", top: position.top, left: position.left, width: position.width, maxHeight: position.maxHeight, zIndex: 18220 }}>
          <div className="tos-thrs-smart-search-menu-head-v2"><span><Sparkles size={14} />{isAr ? "اقتراحات ذكية" : "Smart suggestions"}</span><small>{isAr ? "↑↓ للتنقل · Enter للاختيار" : "↑↓ navigate · Enter select"}</small></div>
          <div className="tos-thrs-smart-search-results-v2">
            {suggestions.length ? suggestions.map((entry, index) => {
              const requester = entry.row?.requester || {};
              const type = requestTypeValue(entry.row);
              const status = entry.row?.status || "";
              const role = requester.role || entry.row?.requesterRole || "";
              return (
                <button key={`${entry.row?.id || index}-${index}`} type="button" data-active={index === activeIndex ? "true" : "false"} onMouseEnter={() => setActiveIndex(index)} onClick={() => selectSuggestion(entry)}>
                  <span className="tos-thrs-smart-avatar-v2">{requester.name ? initials(requester.name) : <UserRound size={15} />}</span>
                  <span className="tos-thrs-smart-result-copy-v2">
                    <strong><MarkMatch text={requester.name || requester.email || (isAr ? "موظف" : "Employee")} query={query} /></strong>
                    <small>{requester.email || labelFor(ROLE_LABELS, role, isAr)}</small>
                    <em>{labelFor(REQUEST_TYPE_LABELS, type, isAr)} · {labelFor(STATUS_LABELS, status, isAr)}</em>
                  </span>
                </button>
              );
            }) : <div className="tos-thrs-smart-search-empty-v2">{isAr ? "لا توجد نتائج مطابقة. جرّب اسمًا أو إيميلًا أو دورًا أو حالة." : "No matching results. Try a name, email, role, type or status."}</div>}
          </div>
        </div>,
        document.body,
      )}
    </div>
  );
}
