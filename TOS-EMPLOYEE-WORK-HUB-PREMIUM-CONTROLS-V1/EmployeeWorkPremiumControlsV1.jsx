import { useEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { Check, ChevronDown, Clock3 } from "lucide-react";
import "./employeeWorkHubPremiumControlsV1.css";

function nodeText(node) {
  if (node === null || node === undefined || node === false) return "";
  if (typeof node === "string" || typeof node === "number") return String(node);
  if (Array.isArray(node)) return node.map(nodeText).join("");
  if (typeof node === "object" && node?.props?.children !== undefined) return nodeText(node.props.children);
  return "";
}

function collectOptions(children, output = []) {
  if (children === null || children === undefined || children === false) return output;
  if (Array.isArray(children)) {
    children.forEach((child) => collectOptions(child, output));
    return output;
  }
  if (typeof children !== "object") return output;
  if (children.type === "option") {
    output.push({
      value: String(children.props?.value ?? ""),
      label: children.props?.children,
      text: nodeText(children.props?.children),
      disabled: Boolean(children.props?.disabled),
    });
    return output;
  }
  if (children.props?.children !== undefined) collectOptions(children.props.children, output);
  return output;
}

function detectRtl(trigger) {
  return trigger?.closest?.("[dir]")?.getAttribute?.("dir") === "rtl" || document.documentElement.dir === "rtl";
}

function emitValue(onChange, value) {
  onChange?.({ target: { value }, currentTarget: { value } });
}

export function EmployeeWorkSelectV1({ value, onChange, children, disabled = false, required = false, className = "", title = "", "aria-label": ariaLabel = "Select" }) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [rtl, setRtl] = useState(false);
  const [position, setPosition] = useState({ top: 0, left: 0, width: 280, maxHeight: 360, openAbove: false });
  const triggerRef = useRef(null);
  const menuRef = useRef(null);
  const options = useMemo(() => collectOptions(children, []), [children]);
  const selected = options.find((option) => String(option.value) === String(value ?? "")) || null;
  const searchable = options.length > 8;
  const full = String(className || "").includes("w-full") || String(className || "").includes("flex-1");
  const visibleOptions = useMemo(() => {
    const needle = String(query || "").trim().toLowerCase();
    return needle ? options.filter((option) => option.text.toLowerCase().includes(needle)) : options;
  }, [options, query]);

  useEffect(() => {
    if (!open) return undefined;
    setQuery("");
    setRtl(detectRtl(triggerRef.current));
    const sync = () => {
      const rect = triggerRef.current?.getBoundingClientRect();
      if (!rect) return;
      const gap = 10;
      const width = Math.min(Math.max(rect.width, 220), Math.max(240, window.innerWidth - gap * 2));
      const left = Math.min(Math.max(gap, rect.left), Math.max(gap, window.innerWidth - width - gap));
      const desiredHeight = Math.min(420, Math.max(180, (searchable ? 56 : 0) + Math.min(options.length, 8) * 44 + 28));
      const below = Math.max(0, window.innerHeight - rect.bottom - gap);
      const above = Math.max(0, rect.top - gap);
      const openAbove = below < Math.min(280, desiredHeight) && above > below;
      const side = openAbove ? above : below;
      const maxHeight = Math.max(150, Math.min(desiredHeight, side - 8));
      const top = openAbove ? Math.max(gap, rect.top - maxHeight - 8) : rect.bottom + 8;
      setPosition({ top, left, width, maxHeight, openAbove });
    };
    const closeOutside = (event) => {
      if (triggerRef.current?.contains(event.target) || menuRef.current?.contains(event.target)) return;
      setOpen(false);
    };
    const closeEscape = (event) => {
      if (event.key !== "Escape") return;
      setOpen(false);
      triggerRef.current?.focus();
    };
    sync();
    window.addEventListener("resize", sync);
    window.addEventListener("scroll", sync, true);
    document.addEventListener("mousedown", closeOutside);
    document.addEventListener("keydown", closeEscape);
    return () => {
      window.removeEventListener("resize", sync);
      window.removeEventListener("scroll", sync, true);
      document.removeEventListener("mousedown", closeOutside);
      document.removeEventListener("keydown", closeEscape);
    };
  }, [open, options.length, searchable]);

  const choose = (option) => {
    if (!option || option.disabled) return;
    emitValue(onChange, option.value);
    setOpen(false);
    triggerRef.current?.focus();
  };

  return (
    <div className={`tos-ewh-select-v1 ${full ? "tos-ewh-select-v1--full" : "tos-ewh-select-v1--compact"}`}>
      <button ref={triggerRef} type="button" disabled={disabled} title={title} aria-label={ariaLabel} aria-haspopup="listbox" aria-expanded={open} aria-required={required} className="tos-ewh-select-trigger-v1" onClick={() => setOpen((current) => !current)}>
        <span className={selected && selected.value !== "" ? "tos-ewh-select-value-v1" : "tos-ewh-select-placeholder-v1"}>{selected?.label ?? "—"}</span>
        <ChevronDown size={16} className={open ? "rotate-180" : ""} />
      </button>
      {open && createPortal(
        <>
          <button type="button" className="tos-ewh-control-backdrop-v1" aria-label={rtl ? "إغلاق القائمة" : "Close menu"} onClick={() => setOpen(false)} />
          <div ref={menuRef} role="listbox" aria-label={ariaLabel} dir={rtl ? "rtl" : "ltr"} className="tos-ewh-select-menu-v1" data-placement={position.openAbove ? "top" : "bottom"} style={{ position: "fixed", top: position.top, left: position.left, width: position.width, maxHeight: position.maxHeight, zIndex: 18120 }}>
            {searchable && <div className="tos-ewh-select-search-wrap-v1"><input autoFocus value={query} onChange={(event) => setQuery(event.target.value)} placeholder={rtl ? "بحث..." : "Search..."} className="tos-ewh-select-search-v1" /></div>}
            <div className="tos-ewh-select-options-v1">
              {visibleOptions.length ? visibleOptions.map((option, index) => {
                const active = String(option.value) === String(value ?? "");
                return <button key={`${option.value}-${index}`} type="button" role="option" aria-selected={active} disabled={option.disabled} className="tos-ewh-select-option-v1" data-active={active ? "true" : "false"} onClick={() => choose(option)}><span>{option.label}</span>{active && <Check size={15} />}</button>;
              }) : <div className="tos-ewh-select-empty-v1">{rtl ? "لا توجد نتائج" : "No matching options"}</div>}
            </div>
          </div>
        </>,
        document.body,
      )}
    </div>
  );
}

function parseTime(value) {
  const match = /^(\d{2}):(\d{2})$/.exec(String(value || ""));
  const now = new Date();
  const hour24 = match ? Math.max(0, Math.min(23, Number(match[1]))) : now.getHours();
  const minute = match ? Math.max(0, Math.min(59, Number(match[2]))) : now.getMinutes();
  return { hour12: hour24 % 12 || 12, minute, period: hour24 >= 12 ? "PM" : "AM" };
}

function toTime(hour12, minute, period) {
  let hour = Math.max(1, Math.min(12, Number(hour12) || 12)) % 12;
  if (period === "PM") hour += 12;
  return `${String(hour).padStart(2, "0")}:${String(Math.max(0, Math.min(59, Number(minute) || 0))).padStart(2, "0")}`;
}

function formatTime(value, rtl) {
  const match = /^(\d{2}):(\d{2})$/.exec(String(value || ""));
  if (!match) return rtl ? "اختر الوقت" : "Select time";
  const date = new Date(2000, 0, 1, Number(match[1]), Number(match[2]), 0, 0);
  try { return date.toLocaleTimeString(rtl ? "ar-EG" : "en-US", { hour: "2-digit", minute: "2-digit" }); } catch { return value; }
}

export function EmployeeWorkTimePickerV1({ value, onChange, disabled = false, required = false, "aria-label": ariaLabel = "Time" }) {
  const parsed = parseTime(value);
  const [open, setOpen] = useState(false);
  const [rtl, setRtl] = useState(false);
  const [draftHour, setDraftHour] = useState(parsed.hour12);
  const [draftMinute, setDraftMinute] = useState(parsed.minute);
  const [draftPeriod, setDraftPeriod] = useState(parsed.period);
  const [position, setPosition] = useState({ top: 0, left: 0, width: 330, maxHeight: 390, openAbove: false });
  const triggerRef = useRef(null);
  const menuRef = useRef(null);

  useEffect(() => {
    if (!open) return;
    const next = parseTime(value);
    setDraftHour(next.hour12);
    setDraftMinute(next.minute);
    setDraftPeriod(next.period);
    setRtl(detectRtl(triggerRef.current));
  }, [open, value]);

  useEffect(() => {
    if (!open) return undefined;
    const sync = () => {
      const rect = triggerRef.current?.getBoundingClientRect();
      if (!rect) return;
      const gap = 10;
      const width = Math.min(350, Math.max(310, rect.width), Math.max(260, window.innerWidth - gap * 2));
      const left = Math.min(Math.max(gap, rect.left), Math.max(gap, window.innerWidth - width - gap));
      const desiredHeight = 390;
      const below = Math.max(0, window.innerHeight - rect.bottom - gap);
      const above = Math.max(0, rect.top - gap);
      const openAbove = below < 330 && above > below;
      const side = openAbove ? above : below;
      const maxHeight = Math.max(260, Math.min(desiredHeight, side - 8));
      const top = openAbove ? Math.max(gap, rect.top - maxHeight - 8) : rect.bottom + 8;
      setPosition({ top, left, width, maxHeight, openAbove });
    };
    const closeOutside = (event) => {
      if (triggerRef.current?.contains(event.target) || menuRef.current?.contains(event.target)) return;
      setOpen(false);
    };
    const closeEscape = (event) => {
      if (event.key !== "Escape") return;
      setOpen(false);
      triggerRef.current?.focus();
    };
    sync();
    window.addEventListener("resize", sync);
    window.addEventListener("scroll", sync, true);
    document.addEventListener("mousedown", closeOutside);
    document.addEventListener("keydown", closeEscape);
    return () => {
      window.removeEventListener("resize", sync);
      window.removeEventListener("scroll", sync, true);
      document.removeEventListener("mousedown", closeOutside);
      document.removeEventListener("keydown", closeEscape);
    };
  }, [open]);

  const apply = () => {
    emitValue(onChange, toTime(draftHour, draftMinute, draftPeriod));
    setOpen(false);
    triggerRef.current?.focus();
  };
  const setNow = () => {
    const now = new Date();
    const next = parseTime(`${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")}`);
    setDraftHour(next.hour12);
    setDraftMinute(next.minute);
    setDraftPeriod(next.period);
  };

  return (
    <>
      <button ref={triggerRef} type="button" disabled={disabled} aria-label={ariaLabel} aria-haspopup="dialog" aria-expanded={open} aria-required={required} className="tos-ewh-time-trigger-v1" onClick={() => setOpen((current) => !current)}><span className={value ? "tos-ewh-time-value-v1" : "tos-ewh-time-placeholder-v1"}>{formatTime(value, rtl)}</span><Clock3 size={16} /></button>
      {open && createPortal(
        <>
          <button type="button" className="tos-ewh-control-backdrop-v1" aria-label={rtl ? "إغلاق اختيار الوقت" : "Close time picker"} onClick={() => setOpen(false)} />
          <div ref={menuRef} role="dialog" aria-label={ariaLabel} dir={rtl ? "rtl" : "ltr"} className="tos-ewh-time-menu-v1" data-placement={position.openAbove ? "top" : "bottom"} style={{ position: "fixed", top: position.top, left: position.left, width: position.width, maxHeight: position.maxHeight, zIndex: 18130 }}>
            <div className="tos-ewh-time-sheet-handle-v1" aria-hidden="true" />
            <div className="tos-ewh-time-heading-v1"><span>{rtl ? "اختيار الوقت" : "Select time"}</span><strong>{String(draftHour).padStart(2, "0")}:{String(draftMinute).padStart(2, "0")} {draftPeriod}</strong></div>
            <div className="tos-ewh-time-columns-v1">
              <div className="tos-ewh-time-column-v1"><span className="tos-ewh-time-column-label-v1">{rtl ? "الساعة" : "Hour"}</span><div>{Array.from({ length: 12 }, (_, index) => index + 1).map((hour) => <button key={hour} type="button" data-active={draftHour === hour ? "true" : "false"} onClick={() => setDraftHour(hour)}>{String(hour).padStart(2, "0")}</button>)}</div></div>
              <div className="tos-ewh-time-column-v1"><span className="tos-ewh-time-column-label-v1">{rtl ? "الدقيقة" : "Minute"}</span><div>{Array.from({ length: 60 }, (_, index) => index).map((minute) => <button key={minute} type="button" data-active={draftMinute === minute ? "true" : "false"} onClick={() => setDraftMinute(minute)}>{String(minute).padStart(2, "0")}</button>)}</div></div>
              <div className="tos-ewh-time-column-v1"><span className="tos-ewh-time-column-label-v1">{rtl ? "الفترة" : "Period"}</span><div>{["AM", "PM"].map((period) => <button key={period} type="button" data-active={draftPeriod === period ? "true" : "false"} onClick={() => setDraftPeriod(period)}>{period}</button>)}</div></div>
            </div>
            <div className="tos-ewh-time-footer-v1"><button type="button" className="tos-ewh-time-clear-v1" onClick={() => { emitValue(onChange, ""); setOpen(false); triggerRef.current?.focus(); }}>{rtl ? "مسح" : "Clear"}</button><button type="button" className="tos-ewh-time-now-v1" onClick={setNow}>{rtl ? "الآن" : "Now"}</button><button type="button" className="tos-ewh-time-apply-v1" onClick={apply}><Check size={14} />{rtl ? "تطبيق" : "Apply"}</button></div>
          </div>
        </>,
        document.body,
      )}
    </>
  );
}
