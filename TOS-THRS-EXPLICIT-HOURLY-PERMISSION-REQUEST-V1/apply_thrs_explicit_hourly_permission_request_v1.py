#!/usr/bin/env python3
from pathlib import Path
import re, subprocess, sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS").resolve()
TARGET = ROOT / "frontend/src/pages/EmployeeWorkHub.jsx"
MARKER = "TOS_THRS_EXPLICIT_HOURLY_PERMISSION_REQUEST_V1"

def die(msg, original=None):
    if original is not None and TARGET.exists():
        TARGET.write_text(original, encoding="utf-8")
    print("PATCH=FAIL"); print(f"ERROR={msg}"); raise SystemExit(1)

def once(old, new, label):
    global text
    n = text.count(old)
    if n != 1: die(f"{label}: expected 1 anchor, found {n}", original)
    text = text.replace(old, new, 1)

def rx(pattern, repl, label):
    global text
    text2, n = re.subn(pattern, repl, text, count=1, flags=re.S)
    if n != 1: die(f"{label}: pattern not found", original)
    text = text2

if not (ROOT / ".git").is_dir(): die(f"TOS git repo not found: {ROOT}")
if not TARGET.is_file(): die(f"Missing {TARGET}")
original = TARGET.read_text(encoding="utf-8")
if MARKER in original:
    print("PATCH=PASS"); print("ACTION=ALREADY_APPLIED"); print("EXPLICIT_PERMISSION=ACTIVE"); print("FILES_CHANGED=0"); raise SystemExit(0)
text = original

rx(
    r'(const REQUEST_TYPE_LABELS = \{.*?\n\};)\n(const ATTENDANCE_CORRECTION_LABELS = \{)',
    r'''\1
// TOS_THRS_EXPLICIT_HOURLY_PERMISSION_REQUEST_V1
const REQUEST_COMPOSER_TYPE_OPTIONS = ["LEAVE", "HOURLY_PERMISSION", "SCHEDULE_CHANGE", "ATTENDANCE_CORRECTION", "OVERTIME", "SHIFT_SWAP"];
const REQUEST_COMPOSER_TYPE_LABELS = {
  ...REQUEST_TYPE_LABELS,
  HOURLY_PERMISSION: { ar: "طلب إذن", en: "Permission Request" },
};
\2''',
    "composer constants",
)

rx(
    r'function requestTypeDisplayLabel\(item = \{\}, leaveTypes = \[\], isAr\) \{.*?\n\}\n\nfunction isFinalThrsApprovedRequest',
    '''function requestTypeDisplayLabel(item = {}, leaveTypes = [], isAr) {
  const type = canonicalRequestType(item) || item?.requestType;
  if (type !== "LEAVE") return labelFrom(REQUEST_TYPE_LABELS, type, isAr);
  const hourlyPermission = String(item?.metadata?.leaveCalculationUnit || item?.metadata?.calculationUnit || "").toUpperCase() === "HOURS"
    || Boolean(item?.startTime && item?.endTime);
  const main = hourlyPermission
    ? labelFrom(REQUEST_COMPOSER_TYPE_LABELS, "HOURLY_PERMISSION", isAr)
    : labelFrom(REQUEST_TYPE_LABELS, type, isAr);
  const leave = leaveTypeLabel(leaveTypes, item?.metadata?.leaveTypeId || item?.metadata?.thrsLeaveTypeId)
    || (hourlyPermission ? (isAr ? "نوع إذن غير محدد" : "Permission type not specified") : (isAr ? "نوع إجازة غير محدد" : "Leave type not specified"));
  return `${main} - ${leave}`;
}

function isFinalThrsApprovedRequest''',
    "history/admin label",
)

once(
'''  const [form, setForm] = useState(() => requestFormDefaults());
  const [requestAttachments, setRequestAttachments] = useState([]);''',
'''  const [form, setForm] = useState(() => requestFormDefaults());
  const [leaveRequestMode, setLeaveRequestMode] = useState("DAYS");
  const [requestAttachments, setRequestAttachments] = useState([]);''',
"mode state")

once(
'''  const selectedLeaveType = findLeaveType(leaveTypes, form.leaveTypeId);
  const selectedLeaveCalculationUnit = leaveTypeCalculationUnit(selectedLeaveType);
  const isHourlyLeaveForm = form.requestType === "LEAVE" && selectedLeaveCalculationUnit === "HOURS";''',
'''  const selectedLeaveType = findLeaveType(leaveTypes, form.leaveTypeId);
  const selectedLeaveCalculationUnit = leaveTypeCalculationUnit(selectedLeaveType);
  const dailyLeaveTypes = useMemo(() => leaveTypes.filter((type) => leaveTypeCalculationUnit(type) !== "HOURS"), [leaveTypes]);
  const hourlyPermissionTypes = useMemo(() => leaveTypes.filter((type) => leaveTypeCalculationUnit(type) === "HOURS"), [leaveTypes]);
  const composerLeaveTypes = leaveRequestMode === "HOURS" ? hourlyPermissionTypes : dailyLeaveTypes;
  const isHourlyLeaveForm = form.requestType === "LEAVE" && (leaveRequestMode === "HOURS" || selectedLeaveCalculationUnit === "HOURS");''',
"filtered leave types")

once(
'''      if (!String(form.leaveTypeId || "").trim()) add("نوع الإجازة مطلوب.", "Leave type is required.");''',
'''      if (!String(form.leaveTypeId || "").trim()) add(leaveRequestMode === "HOURS" ? "نوع الإذن مطلوب." : "نوع الإجازة مطلوب.", leaveRequestMode === "HOURS" ? "Permission type is required." : "Leave type is required.");''',
"validation label")
once(
'''  }, [employeeMappingReady, form, isAr, isHourlyLeaveForm, requestOptions, requesterAssignments.length, targetAssignments.length]);''',
'''  }, [employeeMappingReady, form, isAr, isHourlyLeaveForm, leaveRequestMode, requestOptions, requesterAssignments.length, targetAssignments.length]);''',
"validation deps")

once(
'''  function setFormField(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
  }''',
'''  function setFormField(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  function selectRequestComposerType(uiType) {
    const hourly = uiType === "HOURLY_PERMISSION";
    const canonical = hourly ? "LEAVE" : uiType;
    setLeaveRequestMode(hourly ? "HOURS" : "DAYS");
    setRequestComposerStep("DETAILS");
    setShadowEvaluation(null);
    setForm((current) => {
      const selected = findLeaveType(leaveTypes, current.leaveTypeId);
      const unit = selected ? leaveTypeCalculationUnit(selected) : "";
      const keep = canonical === "LEAVE" && current.leaveTypeId && (hourly ? unit === "HOURS" : unit !== "HOURS");
      const next = {
        ...current,
        requestType: canonical,
        leaveTypeId: keep ? current.leaveTypeId : "",
        leaveCalculationUnit: canonical === "LEAVE" ? (keep ? unit : (hourly ? "HOURS" : "")) : "",
        shadowMemberId: "",
        correctionType: "BOTH",
        requesterAssignmentId: canonical === "SHIFT_SWAP" ? current.requesterAssignmentId : "",
        targetAssignmentId: canonical === "SHIFT_SWAP" ? current.targetAssignmentId : "",
        workModel: canonical === "SCHEDULE_CHANGE" ? (current.workModel || "OFFICE") : "OFFICE",
      };
      if (hourly || ["ATTENDANCE_CORRECTION", "OVERTIME"].includes(canonical)) next.endDate = current.startDate;
      if (canonical === "SHIFT_SWAP") { next.startTime = ""; next.endTime = ""; }
      else if (!current.startTime || !current.endTime) { next.startTime = "09:00"; next.endTime = "17:00"; }
      return next;
    });
  }''',
"composer selector")

rx(
    r'''                <div className="mt-2 flex flex-wrap gap-2">\n\s*\{REQUEST_TYPE_OPTIONS\.map\(\(type\) => \(.*?\)\)\}\n                </div>''',
    '''                <div className="mt-2 flex flex-wrap gap-2">
                  {REQUEST_COMPOSER_TYPE_OPTIONS.map((type) => {
                    const hourly = type === "HOURLY_PERMISSION";
                    const canonical = hourly ? "LEAVE" : type;
                    const active = form.requestType === canonical && (canonical !== "LEAVE" || (hourly ? leaveRequestMode === "HOURS" : leaveRequestMode !== "HOURS"));
                    return (
                      <button key={type} type="button" onClick={() => { if (!active) selectRequestComposerType(type); }} className={`inline-flex min-h-[38px] items-center gap-2 rounded-2xl border px-3 text-xs font-black transition ${active ? "border-slate-950 bg-white text-slate-950 shadow-sm dark:border-white dark:bg-zinc-950 dark:text-white" : "border-slate-200 bg-white/70 text-slate-500 hover:bg-white dark:border-white/10 dark:bg-zinc-950/60 dark:text-zinc-300"}`}>
                        {hourly ? <Clock3 size={14} /> : <CalendarDays size={14} />} {labelFrom(REQUEST_COMPOSER_TYPE_LABELS, type, isAr)}
                      </button>
                    );
                  })}
                </div>''',
    "composer buttons",
)

once(
'''                    <FieldLabel>{isAr ? "نوع الإجازة *" : "Leave type *"}</FieldLabel>
                    {leaveTypes.length ? (''',
'''                    <FieldLabel>{leaveRequestMode === "HOURS" ? (isAr ? "نوع الإذن *" : "Permission type *") : (isAr ? "نوع الإجازة *" : "Leave type *")}</FieldLabel>
                    {composerLeaveTypes.length ? (''',
"leave field/filter")
once(
'''                        <option value="">{isAr ? "اختر نوع الإجازة" : "Select leave type"}</option>
                        {leaveTypes.map((type) => <option key={type.id || type.leaveTypeId} value={type.id || type.leaveTypeId}>{type.name || type.label || type.code || type.id}</option>)}''',
'''                        <option value="">{leaveRequestMode === "HOURS" ? (isAr ? "اختر نوع الإذن" : "Select permission type") : (isAr ? "اختر نوع الإجازة" : "Select leave type")}</option>
                        {composerLeaveTypes.map((type) => <option key={type.id || type.leaveTypeId} value={type.id || type.leaveTypeId}>{type.name || type.label || type.code || type.id}</option>)}''',
"leave options")
once(
'''                        {isAr ? "أنواع الإجازات غير متاحة حاليًا، لذلك تم تعطيل الإرسال." : "Leave types are unavailable, so submission is disabled."}''',
'''                        {leaveRequestMode === "HOURS" ? (isAr ? "لا يوجد نوع إذن محسوب بالساعات متاح في THRS حاليًا، لذلك تم تعطيل الإرسال." : "No hourly permission type is currently available in THRS, so submission is disabled.") : (isAr ? "لا توجد أنواع إجازات يومية متاحة حاليًا، لذلك تم تعطيل الإرسال." : "No day-based leave types are currently available, so submission is disabled.")}''',
"empty types message")
once(
'''                  <div className={`grid gap-3 ${isHourlyLeaveForm ? "md:grid-cols-4" : "md:grid-cols-2"}`}>
                    <div><FieldLabel>{isAr ? "من تاريخ *" : "Start date *"}</FieldLabel><EmployeeWorkDatePickerV1 value={form.startDate} onChange={(value) => setForm((current) => ({ ...current, startDate: value, endDate: current.leaveCalculationUnit === "HOURS" ? value : current.endDate }))} isAr={isAr} ariaLabel={isAr ? "من تاريخ" : "Start date"} required /></div>
                    <div><FieldLabel>{isAr ? "إلى تاريخ *" : "End date *"}</FieldLabel><EmployeeWorkDatePickerV1 value={form.endDate} min={form.startDate} onChange={(value) => setFormField("endDate", value)} disabled={isHourlyLeaveForm} isAr={isAr} ariaLabel={isAr ? "إلى تاريخ" : "End date"} required={!isHourlyLeaveForm} /></div>
                    {isHourlyLeaveForm && <div><FieldLabel>{isAr ? "من وقت *" : "From time *"}</FieldLabel><EmployeeWorkTimePickerV1 value={form.startTime} onChange={(event) => setFormField("startTime", event.target.value)} className={inputClass()} required /></div>}
                    {isHourlyLeaveForm && <div><FieldLabel>{isAr ? "إلى وقت *" : "To time *"}</FieldLabel><EmployeeWorkTimePickerV1 value={form.endTime} onChange={(event) => setFormField("endTime", event.target.value)} className={inputClass()} required /></div>}
                  </div>''',
'''                  <div className={`grid gap-3 ${isHourlyLeaveForm ? "md:grid-cols-3" : "md:grid-cols-2"}`}>
                    <div><FieldLabel>{isHourlyLeaveForm ? (isAr ? "التاريخ *" : "Date *") : (isAr ? "من تاريخ *" : "Start date *")}</FieldLabel><EmployeeWorkDatePickerV1 value={form.startDate} onChange={(value) => setForm((current) => ({ ...current, startDate: value, endDate: isHourlyLeaveForm ? value : current.endDate }))} isAr={isAr} ariaLabel={isHourlyLeaveForm ? (isAr ? "تاريخ الإذن" : "Permission date") : (isAr ? "من تاريخ" : "Start date")} required /></div>
                    {!isHourlyLeaveForm && <div><FieldLabel>{isAr ? "إلى تاريخ *" : "End date *"}</FieldLabel><EmployeeWorkDatePickerV1 value={form.endDate} min={form.startDate} onChange={(value) => setFormField("endDate", value)} isAr={isAr} ariaLabel={isAr ? "إلى تاريخ" : "End date"} required /></div>}
                    {isHourlyLeaveForm && <div><FieldLabel>{isAr ? "من الساعة *" : "From time *"}</FieldLabel><EmployeeWorkTimePickerV1 value={form.startTime} onChange={(event) => setFormField("startTime", event.target.value)} className={inputClass()} required /></div>}
                    {isHourlyLeaveForm && <div><FieldLabel>{isAr ? "إلى الساعة *" : "To time *"}</FieldLabel><EmployeeWorkTimePickerV1 value={form.endTime} onChange={(event) => setFormField("endTime", event.target.value)} className={inputClass()} required /></div>}
                  </div>''',
"permission fields")
once(
'''                  {isHourlyLeaveForm && <p className="text-[11px] font-black text-amber-700 dark:text-amber-300">{isAr ? "الإذن الساعي يكون في يوم واحد ويُحسب تلقائيًا من الوقتين المحددين." : "Hourly permission uses one date and is calculated from the selected times."}</p>}''',
'''                  {isHourlyLeaveForm && <p className="text-[11px] font-black text-amber-700 dark:text-amber-300">{isAr ? "طلب الإذن يكون في يوم واحد ويُحسب بالساعات من وقت البداية إلى وقت النهاية." : "A permission request uses one date and is calculated hourly from the selected start and end times."}</p>}''',
"permission hint")

TARGET.write_text(text, encoding="utf-8")
try:
    subprocess.run(["git","-C",str(ROOT),"diff","--check","--","frontend/src/pages/EmployeeWorkHub.jsx"], check=True)
except Exception:
    die("git diff --check failed; original restored", original)

patched = TARGET.read_text(encoding="utf-8")
for required in [MARKER, 'HOURLY_PERMISSION: { ar: "طلب إذن"', "composerLeaveTypes", "selectRequestComposerType", "No hourly permission type"]:
    if required not in patched: die(f"Post-check missing: {required}", original)
if 'REQUEST_TYPE_OPTIONS = ["LEAVE", "SCHEDULE_CHANGE", "ATTENDANCE_CORRECTION", "OVERTIME", "SHIFT_SWAP"]' not in patched:
    die("Canonical backend type list changed unexpectedly", original)

print("PATCH=PASS")
print("ACTION=APPLIED")
print("EXPLICIT_PERMISSION=ACTIVE")
print("HOURLY_TYPES_FILTER=ACTIVE")
print("DAY_LEAVE_TYPES_FILTER=ACTIVE")
print("CANONICAL_BACKEND_TYPE=LEAVE")
print("THRS_SYNC=PRESERVED")
print("SHADOWING=PRESERVED")
print("BACKEND_CHANGES=NONE")
print("DB_CHANGES=NONE")
print("FILES_CHANGED=frontend/src/pages/EmployeeWorkHub.jsx")
print("BUILD=NOT_RUN")
print("DEPLOY=NOT_RUN")
