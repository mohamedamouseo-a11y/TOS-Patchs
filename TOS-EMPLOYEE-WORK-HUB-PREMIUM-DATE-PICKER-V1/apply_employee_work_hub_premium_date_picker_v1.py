from pathlib import Path
import hashlib
import shutil
import subprocess
import sys
import time

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
PAGE = ROOT / "frontend/src/pages/EmployeeWorkHub.jsx"
STYLE = ROOT / "frontend/src/pages/employeeWorkHubDatePickerV1.css"
FRONTEND = ROOT / "frontend"
DIST = FRONTEND / "dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

EXPECTED_PAGE_GIT_BLOB_SHA = "c0a4ce0df0b130df6ad537a7bda63a02acdf333c"
RUNTIME_TOKEN = "--tos-employee-work-date-picker-v1-runtime"
TRIGGER_TOKEN = "tos-ewh-date-trigger-v1"
MENU_TOKEN = "tos-ewh-date-menu-v1"
STYLE_IMPORT = 'import "./employeeWorkHubDatePickerV1.css";'

print("RUNNING=EMPLOYEE_WORK_HUB_PREMIUM_DATE_PICKER_V1")


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    header = f"blob {len(data)}\0".encode("utf-8")
    return hashlib.sha1(header + data).hexdigest()


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
    sys.exit(1)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 match, found {count}")
    return text.replace(old, new, 1)


if ROOT.resolve() == Path("/"):
    fail("unsafe ROOT")
for path in (PAGE, FRONTEND, LIVE_PARENT):
    if not path.exists():
        fail(f"required path missing: {path}")

actual_blob_sha = git_blob_sha(PAGE)
if actual_blob_sha != EXPECTED_PAGE_GIT_BLOB_SHA:
    fail(f"EmployeeWorkHub.jsx source guard mismatch: {actual_blob_sha}")

original_page = PAGE.read_text(encoding="utf-8")
if STYLE.exists():
    fail("date picker stylesheet already exists")
if STYLE_IMPORT in original_page or TRIGGER_TOKEN in original_page or MENU_TOKEN in original_page:
    fail("premium date picker patch appears partially or already applied")

native_before = original_page.count('type="date"')
if native_before != 6:
    fail(f"expected exactly 6 native date inputs in EmployeeWorkHub.jsx, found {native_before}")

component = r'''
const EWH_DATE_WEEKDAYS_AR_V1 = ["ح", "ن", "ث", "ر", "خ", "ج", "س"];
const EWH_DATE_WEEKDAYS_EN_V1 = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"];

function parseEwhIsoDateV1(value) {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(value || ""));
  if (!match) return null;
  const year = Number(match[1]);
  const month = Number(match[2]);
  const day = Number(match[3]);
  const date = new Date(year, month - 1, day);
  if (date.getFullYear() !== year || date.getMonth() !== month - 1 || date.getDate() !== day) return null;
  return date;
}

function toEwhIsoDateV1(date) {
  const part = (value) => String(value).padStart(2, "0");
  return `${date.getFullYear()}-${part(date.getMonth() + 1)}-${part(date.getDate())}`;
}

function sameEwhDateV1(a, b) {
  return Boolean(a && b && a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate());
}

function formatEwhDateV1(value, isAr) {
  const date = parseEwhIsoDateV1(value);
  if (!date) return isAr ? "اختر التاريخ" : "Select date";
  try {
    return new Intl.DateTimeFormat(isAr ? "ar-EG" : "en-GB", {
      day: "numeric",
      month: "long",
      year: "numeric",
    }).format(date);
  } catch {
    return value;
  }
}

function EmployeeWorkDatePickerV1({ value, onChange, min = "", disabled = false, isAr = false, ariaLabel = "Date", required = false }) {
  const selectedDate = parseEwhIsoDateV1(value);
  const initialDate = selectedDate || new Date();
  const [open, setOpen] = useState(false);
  const [viewMonth, setViewMonth] = useState(() => new Date(initialDate.getFullYear(), initialDate.getMonth(), 1));
  const [position, setPosition] = useState({ top: 0, left: 0, width: 338, maxHeight: 430 });
  const triggerRef = useRef(null);
  const menuRef = useRef(null);

  const minDate = parseEwhIsoDateV1(min);
  const weekdays = isAr ? EWH_DATE_WEEKDAYS_AR_V1 : EWH_DATE_WEEKDAYS_EN_V1;

  useEffect(() => {
    if (!open) return;
    const next = parseEwhIsoDateV1(value) || parseEwhIsoDateV1(min) || new Date();
    setViewMonth(new Date(next.getFullYear(), next.getMonth(), 1));
  }, [open, value, min]);

  useEffect(() => {
    if (!open) return undefined;

    const syncPosition = () => {
      const rect = triggerRef.current?.getBoundingClientRect();
      if (!rect) return;
      const gap = 12;
      const availableWidth = Math.max(260, window.innerWidth - gap * 2);
      const width = Math.min(356, availableWidth, Math.max(310, rect.width + 70));
      const left = Math.min(Math.max(gap, rect.left), Math.max(gap, window.innerWidth - width - gap));
      const desiredHeight = 430;
      const below = window.innerHeight - rect.bottom - gap;
      const above = rect.top - gap;
      const openAbove = below < 360 && above > below;
      const availableHeight = Math.max(240, (openAbove ? above : below) - 8);
      const maxHeight = Math.min(desiredHeight, availableHeight);
      const top = openAbove ? Math.max(gap, rect.top - maxHeight - 8) : rect.bottom + 8;
      setPosition({ top, left, width, maxHeight });
    };

    const closeOutside = (event) => {
      if (triggerRef.current?.contains(event.target) || menuRef.current?.contains(event.target)) return;
      setOpen(false);
    };

    const closeOnEscape = (event) => {
      if (event.key !== "Escape") return;
      setOpen(false);
      triggerRef.current?.focus();
    };

    syncPosition();
    window.addEventListener("resize", syncPosition);
    window.addEventListener("scroll", syncPosition, true);
    document.addEventListener("mousedown", closeOutside);
    document.addEventListener("keydown", closeOnEscape);
    return () => {
      window.removeEventListener("resize", syncPosition);
      window.removeEventListener("scroll", syncPosition, true);
      document.removeEventListener("mousedown", closeOutside);
      document.removeEventListener("keydown", closeOnEscape);
    };
  }, [open]);

  const firstOfMonth = new Date(viewMonth.getFullYear(), viewMonth.getMonth(), 1);
  const gridStart = new Date(firstOfMonth.getFullYear(), firstOfMonth.getMonth(), 1 - firstOfMonth.getDay());
  const days = Array.from({ length: 42 }, (_, index) => new Date(gridStart.getFullYear(), gridStart.getMonth(), gridStart.getDate() + index));
  const today = new Date();
  const monthLabel = new Intl.DateTimeFormat(isAr ? "ar-EG" : "en-US", { month: "long", year: "numeric" }).format(viewMonth);

  const beforeMin = (date) => Boolean(minDate && toEwhIsoDateV1(date) < toEwhIsoDateV1(minDate));
  const choose = (date) => {
    if (beforeMin(date)) return;
    onChange(toEwhIsoDateV1(date));
    setOpen(false);
    triggerRef.current?.focus();
  };

  return (
    <>
      <button
        ref={triggerRef}
        type="button"
        className="tos-ewh-date-trigger-v1"
        disabled={disabled}
        aria-label={ariaLabel}
        aria-haspopup="dialog"
        aria-expanded={open}
        aria-required={required}
        onClick={() => setOpen((current) => !current)}
      >
        <span className={value ? "tos-ewh-date-value-v1" : "tos-ewh-date-placeholder-v1"}>{formatEwhDateV1(value, isAr)}</span>
        <CalendarDays size={17} aria-hidden="true" />
      </button>

      {open && createPortal(
        <>
          <button type="button" className="tos-ewh-date-backdrop-v1" aria-label={isAr ? "إغلاق التقويم" : "Close calendar"} onClick={() => setOpen(false)} />
          <div
            ref={menuRef}
            role="dialog"
            aria-label={ariaLabel}
            dir={isAr ? "rtl" : "ltr"}
            style={{ position: "fixed", top: position.top, left: position.left, width: position.width, maxHeight: position.maxHeight, zIndex: 18020 }}
            className="tos-ewh-date-menu-v1"
          >
            <div className="tos-ewh-date-sheet-handle-v1" aria-hidden="true" />
            <div className="tos-ewh-date-header-v1">
              <button type="button" aria-label={isAr ? "الشهر السابق" : "Previous month"} onClick={() => setViewMonth((current) => new Date(current.getFullYear(), current.getMonth() - 1, 1))}>
                <ChevronLeft size={17} />
              </button>
              <div>
                <span>{isAr ? "اختيار التاريخ" : "Select date"}</span>
                <strong>{monthLabel}</strong>
              </div>
              <button type="button" aria-label={isAr ? "الشهر التالي" : "Next month"} onClick={() => setViewMonth((current) => new Date(current.getFullYear(), current.getMonth() + 1, 1))}>
                <ChevronRight size={17} />
              </button>
            </div>

            <div className="tos-ewh-date-weekdays-v1">
              {weekdays.map((day, index) => <span key={`${day}-${index}`}>{day}</span>)}
            </div>

            <div className="tos-ewh-date-grid-v1">
              {days.map((date) => {
                const iso = toEwhIsoDateV1(date);
                const outside = date.getMonth() !== viewMonth.getMonth();
                const selected = sameEwhDateV1(date, selectedDate);
                const isToday = sameEwhDateV1(date, today);
                const blocked = beforeMin(date);
                return (
                  <button
                    key={iso}
                    type="button"
                    disabled={blocked}
                    aria-label={new Intl.DateTimeFormat(isAr ? "ar-EG" : "en-GB", { day: "numeric", month: "long", year: "numeric" }).format(date)}
                    aria-pressed={selected}
                    data-outside={outside ? "true" : "false"}
                    data-selected={selected ? "true" : "false"}
                    data-today={isToday ? "true" : "false"}
                    onClick={() => choose(date)}
                  >
                    {new Intl.NumberFormat(isAr ? "ar-EG" : "en-US", { useGrouping: false }).format(date.getDate())}
                  </button>
                );
              })}
            </div>

            <div className="tos-ewh-date-footer-v1">
              <button type="button" className="tos-ewh-date-clear-v1" onClick={() => { onChange(""); setOpen(false); triggerRef.current?.focus(); }}>
                {isAr ? "مسح" : "Clear"}
              </button>
              <button type="button" className="tos-ewh-date-today-v1" disabled={beforeMin(today)} onClick={() => choose(today)}>
                <CalendarDays size={14} /> {isAr ? "اليوم" : "Today"}
              </button>
            </div>
          </div>
        </>,
        document.body,
      )}
    </>
  );
}
'''

style = r'''
:root {
  --tos-employee-work-date-picker-v1-runtime: 1;
}

.tos-ewh-date-trigger-v1 {
  min-height: 44px;
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  border: 1px solid rgba(203, 213, 225, 0.92);
  border-radius: 16px;
  background: linear-gradient(180deg, rgba(255,255,255,0.99), rgba(250,248,243,0.96));
  padding: 0 13px;
  color: #1f2937;
  font-size: 14px;
  font-weight: 800;
  text-align: start;
  outline: none;
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.9), 0 1px 2px rgba(15,23,42,0.04);
  transition: border-color 160ms ease, box-shadow 160ms ease, transform 160ms ease, background 160ms ease;
}

.tos-ewh-date-trigger-v1:hover:not(:disabled) {
  border-color: rgba(180, 139, 64, 0.48);
  background: linear-gradient(180deg, #fff, #fbf7ee);
}

.tos-ewh-date-trigger-v1:focus-visible,
.tos-ewh-date-trigger-v1[aria-expanded="true"] {
  border-color: rgba(180, 139, 64, 0.72);
  box-shadow: 0 0 0 3px rgba(214, 177, 104, 0.16), 0 10px 26px rgba(74, 56, 24, 0.08);
}

.tos-ewh-date-trigger-v1:disabled {
  cursor: not-allowed;
  opacity: 0.58;
}

.tos-ewh-date-trigger-v1 svg {
  flex: 0 0 auto;
  color: #a57b30;
}

.tos-ewh-date-value-v1 {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tos-ewh-date-placeholder-v1 {
  color: #94a3b8;
  font-weight: 700;
}

.tos-ewh-date-backdrop-v1 {
  display: none;
}

.tos-ewh-date-menu-v1 {
  overflow: auto;
  border: 1px solid rgba(191, 161, 105, 0.28);
  border-radius: 24px;
  background:
    radial-gradient(circle at 80% 0%, rgba(224, 196, 139, 0.16), transparent 34%),
    linear-gradient(180deg, rgba(255,255,255,0.995), rgba(250,248,243,0.995));
  padding: 14px;
  color: #172033;
  box-shadow: 0 28px 70px rgba(33, 29, 22, 0.18), 0 8px 24px rgba(33,29,22,0.10), inset 0 1px 0 rgba(255,255,255,0.95);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
}

.tos-ewh-date-sheet-handle-v1 {
  display: none;
}

.tos-ewh-date-header-v1 {
  display: grid;
  grid-template-columns: 38px 1fr 38px;
  align-items: center;
  gap: 9px;
  margin-bottom: 11px;
}

.tos-ewh-date-header-v1 > button {
  width: 38px;
  height: 38px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(203,213,225,0.84);
  border-radius: 13px;
  background: rgba(255,255,255,0.78);
  color: #475569;
  transition: background 150ms ease, border-color 150ms ease, color 150ms ease, transform 150ms ease;
}

.tos-ewh-date-header-v1 > button:hover {
  border-color: rgba(180,139,64,0.48);
  background: #fffaf0;
  color: #8a641f;
  transform: translateY(-1px);
}

.tos-ewh-date-header-v1 > div {
  min-width: 0;
  text-align: center;
}

.tos-ewh-date-header-v1 span {
  display: block;
  margin-bottom: 2px;
  color: #94a3b8;
  font-size: 10px;
  font-weight: 900;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.tos-ewh-date-header-v1 strong {
  display: block;
  overflow: hidden;
  color: #1e293b;
  font-size: 14px;
  font-weight: 950;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tos-ewh-date-weekdays-v1,
.tos-ewh-date-grid-v1 {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 4px;
}

.tos-ewh-date-weekdays-v1 {
  margin-bottom: 5px;
}

.tos-ewh-date-weekdays-v1 span {
  padding: 5px 0;
  color: #94a3b8;
  font-size: 10px;
  font-weight: 950;
  text-align: center;
}

.tos-ewh-date-grid-v1 button {
  aspect-ratio: 1;
  min-width: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid transparent;
  border-radius: 12px;
  background: transparent;
  color: #334155;
  font-size: 12px;
  font-weight: 900;
  transition: background 130ms ease, border-color 130ms ease, color 130ms ease, transform 130ms ease, box-shadow 130ms ease;
}

.tos-ewh-date-grid-v1 button:hover:not(:disabled) {
  border-color: rgba(203, 166, 94, 0.32);
  background: rgba(246, 237, 219, 0.72);
  color: #7a581d;
  transform: translateY(-1px);
}

.tos-ewh-date-grid-v1 button[data-outside="true"] {
  color: #c0c7d1;
}

.tos-ewh-date-grid-v1 button[data-today="true"] {
  border-color: rgba(180,139,64,0.52);
  box-shadow: inset 0 0 0 1px rgba(255,255,255,0.7);
}

.tos-ewh-date-grid-v1 button[data-selected="true"] {
  border-color: #b48739;
  background: linear-gradient(135deg, #c9a151, #9b7027);
  color: #fffdf7;
  box-shadow: 0 8px 18px rgba(155,112,39,0.24), inset 0 1px 0 rgba(255,255,255,0.34);
}

.tos-ewh-date-grid-v1 button:disabled {
  cursor: not-allowed;
  opacity: 0.22;
}

.tos-ewh-date-footer-v1 {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 9px;
  margin-top: 12px;
  padding-top: 11px;
  border-top: 1px solid rgba(203,213,225,0.7);
}

.tos-ewh-date-footer-v1 button {
  min-height: 36px;
  border-radius: 12px;
  padding: 0 13px;
  font-size: 11px;
  font-weight: 950;
}

.tos-ewh-date-clear-v1 {
  border: 1px solid rgba(203,213,225,0.9);
  background: rgba(255,255,255,0.72);
  color: #64748b;
}

.tos-ewh-date-today-v1 {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 1px solid rgba(180,139,64,0.36);
  background: rgba(246,237,219,0.84);
  color: #805d20;
}

.tos-ewh-date-today-v1:disabled {
  cursor: not-allowed;
  opacity: 0.4;
}

.dark .tos-ewh-date-trigger-v1 {
  border-color: rgba(255,255,255,0.11);
  background: linear-gradient(180deg, rgba(24,24,27,0.98), rgba(14,14,16,0.98));
  color: #f4f4f5;
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.035), 0 1px 2px rgba(0,0,0,0.3);
}

.dark .tos-ewh-date-trigger-v1:hover:not(:disabled),
.dark .tos-ewh-date-trigger-v1[aria-expanded="true"] {
  border-color: rgba(209, 169, 92, 0.48);
  background: linear-gradient(180deg, rgba(30,28,24,0.99), rgba(15,14,13,0.99));
}

.dark .tos-ewh-date-trigger-v1 svg {
  color: #d7b56f;
}

.dark .tos-ewh-date-placeholder-v1 {
  color: #71717a;
}

.dark .tos-ewh-date-menu-v1 {
  border-color: rgba(219, 181, 108, 0.22);
  background:
    radial-gradient(circle at 80% 0%, rgba(213, 174, 98, 0.10), transparent 36%),
    linear-gradient(180deg, rgba(19,19,21,0.995), rgba(9,9,11,0.995));
  color: #f4f4f5;
  box-shadow: 0 34px 90px rgba(0,0,0,0.62), 0 8px 26px rgba(0,0,0,0.44), inset 0 1px 0 rgba(255,255,255,0.035);
}

.dark .tos-ewh-date-header-v1 > button {
  border-color: rgba(255,255,255,0.09);
  background: rgba(39,39,42,0.72);
  color: #d4d4d8;
}

.dark .tos-ewh-date-header-v1 > button:hover {
  border-color: rgba(215,181,111,0.34);
  background: rgba(68,56,32,0.36);
  color: #f1d79f;
}

.dark .tos-ewh-date-header-v1 span,
.dark .tos-ewh-date-weekdays-v1 span {
  color: #71717a;
}

.dark .tos-ewh-date-header-v1 strong {
  color: #fafafa;
}

.dark .tos-ewh-date-grid-v1 button {
  color: #d4d4d8;
}

.dark .tos-ewh-date-grid-v1 button:hover:not(:disabled) {
  border-color: rgba(215,181,111,0.26);
  background: rgba(86,67,34,0.30);
  color: #f4dca9;
}

.dark .tos-ewh-date-grid-v1 button[data-outside="true"] {
  color: #52525b;
}

.dark .tos-ewh-date-grid-v1 button[data-today="true"] {
  border-color: rgba(215,181,111,0.48);
}

.dark .tos-ewh-date-grid-v1 button[data-selected="true"] {
  border-color: #d5ae61;
  background: linear-gradient(135deg, #c69a45, #7d581e);
  color: #fffaf0;
  box-shadow: 0 10px 24px rgba(180,132,49,0.20), inset 0 1px 0 rgba(255,255,255,0.18);
}

.dark .tos-ewh-date-footer-v1 {
  border-top-color: rgba(255,255,255,0.08);
}

.dark .tos-ewh-date-clear-v1 {
  border-color: rgba(255,255,255,0.09);
  background: rgba(39,39,42,0.7);
  color: #a1a1aa;
}

.dark .tos-ewh-date-today-v1 {
  border-color: rgba(215,181,111,0.28);
  background: rgba(91,68,30,0.34);
  color: #eed39b;
}

@media (max-width: 640px) {
  .tos-ewh-date-backdrop-v1 {
    position: fixed;
    inset: 0;
    z-index: 18010;
    display: block;
    border: 0;
    background: rgba(15, 23, 42, 0.26);
    backdrop-filter: blur(3px);
    -webkit-backdrop-filter: blur(3px);
  }

  .dark .tos-ewh-date-backdrop-v1 {
    background: rgba(0,0,0,0.58);
  }

  .tos-ewh-date-menu-v1 {
    top: auto !important;
    right: 10px !important;
    bottom: max(10px, env(safe-area-inset-bottom)) !important;
    left: 10px !important;
    width: auto !important;
    max-height: min(520px, calc(100dvh - 20px)) !important;
    z-index: 18020 !important;
    border-radius: 26px;
    padding: 10px 14px max(14px, env(safe-area-inset-bottom));
    box-shadow: 0 30px 80px rgba(15,23,42,0.28), 0 8px 30px rgba(15,23,42,0.18);
  }

  .tos-ewh-date-sheet-handle-v1 {
    width: 42px;
    height: 4px;
    display: block;
    margin: 1px auto 9px;
    border-radius: 999px;
    background: rgba(100,116,139,0.28);
  }

  .dark .tos-ewh-date-sheet-handle-v1 {
    background: rgba(212,212,216,0.22);
  }

  .tos-ewh-date-grid-v1 {
    gap: 5px;
  }

  .tos-ewh-date-grid-v1 button {
    min-height: 40px;
    aspect-ratio: auto;
    border-radius: 13px;
    font-size: 13px;
  }

  .tos-ewh-date-weekdays-v1 span {
    padding: 6px 0;
    font-size: 11px;
  }

  .tos-ewh-date-footer-v1 button {
    min-height: 40px;
    padding-inline: 16px;
    font-size: 12px;
  }
}
'''

try:
    page = original_page

    page = replace_once(
        page,
        'import { useEffect, useMemo, useRef, useState } from "react";',
        'import { useEffect, useMemo, useRef, useState } from "react";\nimport { createPortal } from "react-dom";',
        "react portal import",
    )

    page = replace_once(
        page,
        'import { Archive, ArchiveRestore, Ban, Bold, CalendarDays, Check, CheckCircle2, ChevronDown, ClipboardList, Clock3, CloudOff, Coffee, FileText, Italic, List, ListOrdered, Info, LogIn, LogOut, MessageSquare, Paperclip, Quote, RefreshCw, Send, ShieldCheck, Trash2, Underline, UploadCloud, User, UserCheck, Users, XCircle } from "lucide-react";',
        'import { Archive, ArchiveRestore, Ban, Bold, CalendarDays, Check, CheckCircle2, ChevronDown, ChevronLeft, ChevronRight, ClipboardList, Clock3, CloudOff, Coffee, FileText, Italic, List, ListOrdered, Info, LogIn, LogOut, MessageSquare, Paperclip, Quote, RefreshCw, Send, ShieldCheck, Trash2, Underline, UploadCloud, User, UserCheck, Users, XCircle } from "lucide-react";\n' + STYLE_IMPORT,
        "date picker icons and stylesheet import",
    )

    page = replace_once(
        page,
        '''function inputClass() {
  return "min-h-[42px] w-full rounded-2xl border border-slate-200 bg-white px-3 text-sm font-bold text-slate-800 outline-none transition focus:border-slate-500 dark:border-white/10 dark:bg-zinc-900 dark:text-zinc-100";
}''',
        '''function inputClass() {
  return "min-h-[42px] w-full rounded-2xl border border-slate-200 bg-white px-3 text-sm font-bold text-slate-800 outline-none transition focus:border-slate-500 dark:border-white/10 dark:bg-zinc-900 dark:text-zinc-100";
}

''' + component,
        "premium date picker component",
    )

    replacements = [
        (
            '<input type="date" value={form.startDate} onChange={(event) => setForm((current) => ({ ...current, startDate: event.target.value, endDate: current.leaveCalculationUnit === "HOURS" ? event.target.value : current.endDate }))} className={inputClass()} required />',
            '<EmployeeWorkDatePickerV1 value={form.startDate} onChange={(value) => setForm((current) => ({ ...current, startDate: value, endDate: current.leaveCalculationUnit === "HOURS" ? value : current.endDate }))} isAr={isAr} ariaLabel={isAr ? "من تاريخ" : "Start date"} required />',
            "leave start date",
        ),
        (
            '<input type="date" value={form.endDate} min={form.startDate} onChange={(event) => setFormField("endDate", event.target.value)} className={inputClass()} disabled={isHourlyLeaveForm} required={!isHourlyLeaveForm} />',
            '<EmployeeWorkDatePickerV1 value={form.endDate} min={form.startDate} onChange={(value) => setFormField("endDate", value)} disabled={isHourlyLeaveForm} isAr={isAr} ariaLabel={isAr ? "إلى تاريخ" : "End date"} required={!isHourlyLeaveForm} />',
            "leave end date",
        ),
        (
            '<input type="date" value={form.startDate} onChange={(event) => setFormField("startDate", event.target.value)} className={inputClass()} required />',
            '<EmployeeWorkDatePickerV1 value={form.startDate} onChange={(value) => setFormField("startDate", value)} isAr={isAr} ariaLabel={isAr ? "من تاريخ" : "Start date"} required />',
            "schedule start date",
        ),
        (
            '<input type="date" value={form.endDate} min={form.startDate} onChange={(event) => setFormField("endDate", event.target.value)} className={inputClass()} required />',
            '<EmployeeWorkDatePickerV1 value={form.endDate} min={form.startDate} onChange={(value) => setFormField("endDate", value)} isAr={isAr} ariaLabel={isAr ? "إلى تاريخ" : "End date"} required />',
            "schedule end date",
        ),
        (
            '<input type="date" value={form.startDate} onChange={(event) => setForm((current) => ({ ...current, startDate: event.target.value, endDate: event.target.value, correctionType: "BOTH" }))} className={inputClass()} required />',
            '<EmployeeWorkDatePickerV1 value={form.startDate} onChange={(value) => setForm((current) => ({ ...current, startDate: value, endDate: value, correctionType: "BOTH" }))} isAr={isAr} ariaLabel={isAr ? "تاريخ الحضور" : "Attendance date"} required />',
            "attendance correction date",
        ),
        (
            '<input type="date" value={form.startDate} onChange={(event) => setForm((current) => ({ ...current, startDate: event.target.value, endDate: event.target.value }))} className={inputClass()} required />',
            '<EmployeeWorkDatePickerV1 value={form.startDate} onChange={(value) => setForm((current) => ({ ...current, startDate: value, endDate: value }))} isAr={isAr} ariaLabel={isAr ? "تاريخ العمل الإضافي" : "Overtime date"} required />',
            "overtime date",
        ),
    ]

    for old, new, label in replacements:
        page = replace_once(page, old, new, label)

    if page.count('type="date"') != 0:
        raise RuntimeError(f"native date inputs remain after patch: {page.count('type=\"date\"')}")
    if page.count("<EmployeeWorkDatePickerV1") != 6:
        raise RuntimeError("expected exactly 6 premium date picker usages")

    PAGE.write_text(page, encoding="utf-8")
    STYLE.write_text(style, encoding="utf-8")

except Exception as exc:
    PAGE.write_text(original_page, encoding="utf-8")
    if STYLE.exists():
        STYLE.unlink()
    fail(f"source patch failed and was rolled back: {exc}")

build = subprocess.run(["npm", "run", "build"], cwd=FRONTEND, text=True, capture_output=True)
if build.returncode != 0:
    print(build.stdout[-5000:])
    print(build.stderr[-5000:])
    PAGE.write_text(original_page, encoding="utf-8")
    if STYLE.exists():
        STYLE.unlink()
    fail("frontend build failed; source changes rolled back")

if not DIST.exists():
    PAGE.write_text(original_page, encoding="utf-8")
    if STYLE.exists():
        STYLE.unlink()
    fail("frontend dist missing after successful build")

if tree_count(DIST, RUNTIME_TOKEN.encode()) < 1 or tree_count(DIST, TRIGGER_TOKEN.encode()) < 1:
    PAGE.write_text(original_page, encoding="utf-8")
    if STYLE.exists():
        STYLE.unlink()
    fail("built output does not contain Employee Work Hub date picker runtime markers")

timestamp = int(time.time())
candidate = LIVE_PARENT / f"build.ewh-date-v1-candidate-{timestamp}"
backup = LIVE_PARENT / f"build.ewh-date-v1-backup-{timestamp}"
failed_live = LIVE_PARENT / f"build.ewh-date-v1-failed-{timestamp}"

try:
    if candidate.exists() or backup.exists() or failed_live.exists():
        raise RuntimeError("timestamped deployment path already exists")
    shutil.copytree(DIST, candidate)
    if not LIVE.exists():
        raise RuntimeError(f"live build missing: {LIVE}")
    LIVE.rename(backup)
    candidate.rename(LIVE)
except Exception as exc:
    try:
        if LIVE.exists() and backup.exists():
            LIVE.rename(failed_live)
            backup.rename(LIVE)
        elif backup.exists() and not LIVE.exists():
            backup.rename(LIVE)
    finally:
        PAGE.write_text(original_page, encoding="utf-8")
        if STYLE.exists():
            STYLE.unlink()
    fail(f"live deployment failed and rollback attempted: {exc}")

print("PASS/FAIL=PASS")
print("BUILD_RESULT=PASS")
print("LIVE_DEPLOY=PASS")
print(f"SOURCE_GUARD_GIT_BLOB_SHA={EXPECTED_PAGE_GIT_BLOB_SHA}")
print(f"NATIVE_DATE_INPUTS_BEFORE={native_before}")
print("NATIVE_DATE_INPUTS_AFTER=0")
print("PREMIUM_DATE_PICKERS=6")
print("LEAVE_START_DATE=PREMIUM")
print("LEAVE_END_DATE=PREMIUM_WITH_MIN")
print("SCHEDULE_START_DATE=PREMIUM")
print("SCHEDULE_END_DATE=PREMIUM_WITH_MIN")
print("ATTENDANCE_CORRECTION_DATE=PREMIUM")
print("OVERTIME_DATE=PREMIUM")
print("IOS_NATIVE_DATE_RENDERING=REMOVED")
print("MOBILE_BOTTOM_SHEET=YES")
print("DESKTOP_PORTAL=YES")
print("RTL_ARABIC=YES")
print("LIGHT_DARK=YES")
print("BUSINESS_LOGIC_CHANGED=NO")
print("API_CHANGED=NO")
print("DATABASE_CHANGED=NO")
print(f"EMPLOYEE_WORK_HUB_SHA256={sha256(PAGE)}")
print(f"DATE_PICKER_STYLE_SHA256={sha256(STYLE)}")
print(f"LIVE_BACKUP={backup}")
print("STATUS=READY")
