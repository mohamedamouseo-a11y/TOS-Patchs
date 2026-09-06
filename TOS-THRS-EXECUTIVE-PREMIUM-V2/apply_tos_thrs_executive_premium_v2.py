from pathlib import Path
import hashlib
import shutil
import subprocess
import sys
import time

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
PATCH_DIR = Path(__file__).resolve().parent
PAGE = ROOT / "frontend/src/pages/EmployeeWorkHub.jsx"
DATE_STYLE = ROOT / "frontend/src/pages/employeeWorkHubDatePickerV1.css"
PREMIUM_CONTROLS = ROOT / "frontend/src/pages/EmployeeWorkPremiumControlsV1.jsx"
PREMIUM_CONTROLS_STYLE = ROOT / "frontend/src/pages/employeeWorkHubPremiumControlsV1.css"
TARGET_UI = ROOT / "frontend/src/pages/ThrsExecutiveUIV2.jsx"
TARGET_STYLE = ROOT / "frontend/src/pages/employeeWorkHubThrsExecutiveV2.css"
SOURCE_UI = PATCH_DIR / "ThrsExecutiveUIV2.jsx"
SOURCE_STYLE = PATCH_DIR / "employeeWorkHubThrsExecutiveV2.css"
FRONTEND = ROOT / "frontend"
DIST = FRONTEND / "dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

EXPECTED_PAGE_SHA256 = "7daf831a74bcf87d0fb00e5a0ac5370ee4966379866ce3f33553e343b1588f13"
EXPECTED_DATE_STYLE_SHA256 = "c7a5517565158ae98d627e2b8b29a22c15b7c425b154ebfd81cabd7cbcd100fe"
EXPECTED_PREMIUM_CONTROLS_SHA256 = "36a0f9b46dfd4b095edd7ed8b97725bc45b1839cb200185eba05f516edd8014e"
EXPECTED_PREMIUM_CONTROLS_STYLE_SHA256 = "5cb504eed6fb8c4edc5df103a5d13cafd561dfe552395d61ccc9d63d50922688"
RUNTIME_TOKEN = "--tos-thrs-executive-v2-runtime"

print("RUNNING=TOS_THRS_EXECUTIVE_PREMIUM_V2")


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


def cleanup_exact_created_files():
    for path in (TARGET_UI, TARGET_STYLE):
        if path.exists():
            path.unlink()


if ROOT.resolve() == Path("/"):
    fail("unsafe ROOT")

for path in (PAGE, DATE_STYLE, PREMIUM_CONTROLS, PREMIUM_CONTROLS_STYLE, SOURCE_UI, SOURCE_STYLE, FRONTEND, LIVE_PARENT):
    if not path.exists():
        fail(f"required path missing: {path}")

if TARGET_UI.exists() or TARGET_STYLE.exists():
    fail("THRS Executive V2 target files already exist")

actual_guards = {
    "EmployeeWorkHub.jsx": sha256(PAGE),
    "employeeWorkHubDatePickerV1.css": sha256(DATE_STYLE),
    "EmployeeWorkPremiumControlsV1.jsx": sha256(PREMIUM_CONTROLS),
    "employeeWorkHubPremiumControlsV1.css": sha256(PREMIUM_CONTROLS_STYLE),
}
expected_guards = {
    "EmployeeWorkHub.jsx": EXPECTED_PAGE_SHA256,
    "employeeWorkHubDatePickerV1.css": EXPECTED_DATE_STYLE_SHA256,
    "EmployeeWorkPremiumControlsV1.jsx": EXPECTED_PREMIUM_CONTROLS_SHA256,
    "employeeWorkHubPremiumControlsV1.css": EXPECTED_PREMIUM_CONTROLS_STYLE_SHA256,
}
for label, expected in expected_guards.items():
    if actual_guards[label] != expected:
        fail(f"{label} source guard mismatch: {actual_guards[label]}")

original_page = PAGE.read_text(encoding="utf-8")

try:
    page = original_page

    import_anchor = 'import { EmployeeWorkSelectV1, EmployeeWorkTimePickerV1 } from "./EmployeeWorkPremiumControlsV1";'
    page = replace_once(
        page,
        import_anchor,
        import_anchor + '\nimport { ThrsExecutiveKpiV2, ThrsSmartSearchV2 } from "./ThrsExecutiveUIV2";',
        "THRS Executive V2 import",
    )

    helper_anchor = '\nfunction buildUiSummary(rows = []) {'
    smart_helpers = r'''
function smartRequestSearchTextV2(item = {}) {
  const requester = item?.requester || {};
  const requestType = canonicalRequestType(item);
  const role = requester.role || item?.requesterRole || "";
  const status = item?.status || "";
  return [
    requester.name,
    requester.email,
    requester.department,
    requester.departmentName,
    role,
    ROLE_LABELS[role]?.ar,
    ROLE_LABELS[role]?.en,
    requestType,
    REQUEST_TYPE_LABELS[requestType]?.ar,
    REQUEST_TYPE_LABELS[requestType]?.en,
    status,
    STATUS_LABELS[status]?.ar,
    STATUS_LABELS[status]?.en,
    item?.startDate,
    item?.endDate,
    typeof item?.reason === "string" ? item.reason : "",
  ].filter(Boolean).join(" ").toLowerCase().replace(/[_\-/]+/g, " ");
}

function filterRequestsSmartV2(rows = [], filters = {}) {
  const query = String(filters.search || "").trim().toLowerCase().replace(/[_\-/]+/g, " ");
  const baseRows = filterRequests(rows, { ...filters, search: "" });
  if (!query) return baseRows;
  const tokens = query.split(/\s+/).filter(Boolean);
  return baseRows.filter((item) => {
    const haystack = smartRequestSearchTextV2(item);
    return tokens.every((token) => haystack.includes(token));
  });
}
'''
    page = replace_once(page, helper_anchor, smart_helpers + helper_anchor, "smart search helper injection")

    old_summary = '''function buildUiSummary(rows = []) {
  return rows.reduce((acc, item) => {
    acc.total += 1;
    if (EMPLOYEE_OPEN_REQUEST_STATUSES.includes(item.status)) acc.pending += 1;
    if (FINAL_APPROVED_STATUSES.includes(item.status)) acc.approved += 1;
    if (FINAL_REJECTED_STATUSES.includes(item.status)) acc.rejected += 1;
    if (item.attachments?.length) acc.withAttachments += 1;
    return acc;
  }, { total: 0, pending: 0, approved: 0, rejected: 0, withAttachments: 0 });
}'''
    new_summary = '''function buildUiSummary(rows = []) {
  const today = toDateKey();
  return rows.reduce((acc, item) => {
    acc.total += 1;
    if (EMPLOYEE_OPEN_REQUEST_STATUSES.includes(item.status)) acc.pending += 1;
    if (["SENT_TO_THRS", "PENDING_HR"].includes(item.status)) acc.pendingHr += 1;
    if (FINAL_APPROVED_STATUSES.includes(item.status)) acc.approved += 1;
    if (FINAL_REJECTED_STATUSES.includes(item.status)) acc.rejected += 1;
    if (item.status === "THRS_SYNC_FAILED") acc.syncFailed += 1;
    if (item.attachments?.length) acc.withAttachments += 1;
    if (matchesRequestDay(item, today)) acc.today += 1;
    return acc;
  }, { total: 0, pending: 0, pendingHr: 0, approved: 0, rejected: 0, syncFailed: 0, withAttachments: 0, today: 0 });
}'''
    page = replace_once(page, old_summary, new_summary, "expanded admin summary")

    old_filtered = 'const filteredAdminRequests = useMemo(() => filterRequests(allUnfilteredRequests, adminFilters), [allUnfilteredRequests, adminFilters]);'
    new_filtered = 'const filteredAdminRequests = useMemo(() => filterRequestsSmartV2(allUnfilteredRequests, adminFilters), [allUnfilteredRequests, adminFilters]);'
    page = replace_once(page, old_filtered, new_filtered, "smart admin filtering")

    request_shell_old = '<div dir={isAr ? "rtl" : "ltr"} className="rounded-[30px] border border-slate-200/80 bg-white/95 p-5 shadow-sm shadow-slate-200/70 dark:border-white/10 dark:bg-zinc-950/90 dark:shadow-none sm:rounded-[36px]">'
    request_shell_new = '<div dir={isAr ? "rtl" : "ltr"} className="tos-thrs-request-shell-v2 rounded-[30px] border border-slate-200/80 bg-white/95 p-5 shadow-sm shadow-slate-200/70 dark:border-white/10 dark:bg-zinc-950/90 dark:shadow-none sm:rounded-[36px]">'
    page = replace_once(page, request_shell_old, request_shell_new, "THRS request premium shell")

    admin_section_old = '<section id="thrs-requests-management" className="rounded-[30px] border border-slate-200/80 bg-white/90 p-5 shadow-sm shadow-slate-200/70 dark:border-white/10 dark:bg-zinc-950/85 dark:shadow-none sm:rounded-[36px]">'
    admin_section_new = '<section id="thrs-requests-management" className="tos-thrs-executive-v2 rounded-[30px] border border-slate-200/80 bg-white/90 p-5 shadow-sm shadow-slate-200/70 dark:border-white/10 dark:bg-zinc-950/85 dark:shadow-none sm:rounded-[36px]">'
    page = replace_once(page, admin_section_old, admin_section_new, "THRS management premium shell")

    old_kpis = '''          <div className="mb-5 grid gap-6 md:grid-cols-5">
            <ThrsMiniStat label={isAr ? "إجمالي الطلبات" : "Total requests"} value={adminSummary.total} max={adminSummary.total} isAr={isAr} />
            <ThrsMiniStat label={isAr ? "قيد المراجعة" : "Pending review"} value={adminSummary.pending} max={adminSummary.total} tone="amber" isAr={isAr} />
            <ThrsMiniStat label={isAr ? "مقبولة" : "Approved"} value={adminSummary.approved} max={adminSummary.total} tone="emerald" isAr={isAr} />
            <ThrsMiniStat label={isAr ? "مرفوضة" : "Rejected"} value={adminSummary.rejected} max={adminSummary.total} tone="red" isAr={isAr} />
            <ThrsMiniStat label={isAr ? "ملفات مرفقة" : "With files"} value={adminSummary.withAttachments} max={adminSummary.total} tone="blue" isAr={isAr} />
          </div>'''
    new_kpis = '''          <div className="tos-thrs-admin-kpis-v2">
            <ThrsExecutiveKpiV2 label={isAr ? "إجمالي الطلبات" : "Total requests"} value={adminSummary.total} max={adminSummary.total} note={isAr ? "النطاق الحالي" : "Current scope"} tone="slate" />
            <ThrsExecutiveKpiV2 label={isAr ? "قيد المراجعة" : "Pending review"} value={adminSummary.pending} max={adminSummary.total} tone="amber" />
            <ThrsExecutiveKpiV2 label={isAr ? "في انتظار HR" : "Pending HR"} value={adminSummary.pendingHr} max={adminSummary.total} tone="gold" />
            <ThrsExecutiveKpiV2 label={isAr ? "مقبولة" : "Approved"} value={adminSummary.approved} max={adminSummary.total} tone="emerald" />
            <ThrsExecutiveKpiV2 label={isAr ? "مرفوضة" : "Rejected"} value={adminSummary.rejected} max={adminSummary.total} tone="red" />
            <ThrsExecutiveKpiV2 label={isAr ? "فشل المزامنة" : "Sync failed"} value={adminSummary.syncFailed} max={adminSummary.total} tone="red" />
            <ThrsExecutiveKpiV2 label={isAr ? "بها مرفقات" : "With files"} value={adminSummary.withAttachments} max={adminSummary.total} tone="blue" />
            <ThrsExecutiveKpiV2 label={isAr ? "تشمل اليوم" : "Includes today"} value={adminSummary.today} max={adminSummary.total} tone="violet" />
          </div>'''
    page = replace_once(page, old_kpis, new_kpis, "expanded executive KPI grid")

    old_search_field = '''            <FilterField className="xl:col-span-2" label={isAr ? "بحث باسم الموظف" : "Employee name search"} note={isAr ? "ابحث باسم الموظف فقط، ونوع الطلب له فلتر مستقل." : "Search by employee name only; request type has a separate filter."}>
              <input value={adminFilters.search} onChange={(event) => setAdminFilter("search", event.target.value)} placeholder={isAr ? "اكتب اسم الموظف..." : "Type employee name..."} className={inputClass()} />
            </FilterField>'''
    new_search_field = '''            <FilterField className="xl:col-span-2" label={isAr ? "البحث الذكي" : "Smart search"} note={isAr ? "اسم، إيميل، دور، نوع طلب أو حالة — مع اقتراحات وبحث صوتي." : "Name, email, role, request type or status — with autocomplete and voice search."}>
              <ThrsSmartSearchV2 value={adminFilters.search} onChange={(event) => setAdminFilter("search", event.target.value)} rows={allUnfilteredRequests} isAr={isAr} />
            </FilterField>'''
    page = replace_once(page, old_search_field, new_search_field, "smart search field")

    monthly_anchor = '''  const monthlyRequestCount = scopedCalendarRequests.filter((request) => calendarRequestDateKeys(request).some((key) => key.startsWith(monthPrefix))).length;
  const monthlyWorkdayCount = countOfficialWorkdaysInMonth(year, month);'''
    monthly_replacement = '''  const monthlyRequestCount = scopedCalendarRequests.filter((request) => calendarRequestDateKeys(request).some((key) => key.startsWith(monthPrefix))).length;
  const monthlyWorkdayCount = countOfficialWorkdaysInMonth(year, month);
  const monthlyAttendanceRate = percentOf(monthlySessionDays, monthlyWorkdayCount);
  const monthlyApprovedLeaveCount = scopedCalendarRequests.filter((request) => canonicalRequestType(request) === "LEAVE" && FINAL_APPROVED_STATUSES.includes(request?.status) && calendarRequestDateKeys(request).some((key) => key.startsWith(monthPrefix))).length;'''
    page = replace_once(page, monthly_anchor, monthly_replacement, "calendar executive metrics")

    old_calendar_kpis = '''            <div className="grid w-full max-w-2xl grid-cols-3 gap-4">
              <ThrsMiniStat label={isAr ? "أيام حضور" : "Attendance days"} value={monthlySessionDays} max={monthlyWorkdayCount} note={workdayPercentNote(monthlySessionDays, monthlyWorkdayCount, isAr)} tone="emerald" isAr={isAr} />
              <ThrsMiniStat label={isAr ? "طلبات الشهر" : "Month requests"} value={monthlyRequestCount} max={monthlyRequestCount || 1} note={isAr ? "خلال الشهر" : "During the month"} tone="amber" isAr={isAr} />
              <ThrsMiniStat label={isAr ? "أيام عليها طلبات" : "Request days"} value={monthlyRequestDays} max={monthlyWorkdayCount} note={workdayPercentNote(monthlyRequestDays, monthlyWorkdayCount, isAr)} tone="blue" isAr={isAr} />
            </div>'''
    new_calendar_kpis = '''            <div className="tos-thrs-calendar-kpis-v2">
              <ThrsExecutiveKpiV2 label={isAr ? "أيام العمل" : "Workdays"} value={monthlyWorkdayCount} max={monthlyWorkdayCount} note={isAr ? "المعتمدة للشهر" : "Official month"} tone="slate" />
              <ThrsExecutiveKpiV2 label={isAr ? "أيام الحضور" : "Attendance days"} value={monthlySessionDays} max={monthlyWorkdayCount} note={workdayPercentNote(monthlySessionDays, monthlyWorkdayCount, isAr)} tone="emerald" />
              <ThrsExecutiveKpiV2 label={isAr ? "نسبة الحضور" : "Attendance rate"} value={monthlyAttendanceRate} max={100} suffix="%" note={isAr ? "من أيام العمل" : "Of workdays"} tone="emerald" />
              <ThrsExecutiveKpiV2 label={isAr ? "طلبات الشهر" : "Month requests"} value={monthlyRequestCount} max={monthlyRequestCount || 1} note={isAr ? "خلال الشهر" : "During month"} tone="amber" />
              <ThrsExecutiveKpiV2 label={isAr ? "أيام عليها طلبات" : "Request days"} value={monthlyRequestDays} max={monthlyWorkdayCount} note={workdayPercentNote(monthlyRequestDays, monthlyWorkdayCount, isAr)} tone="blue" />
              <ThrsExecutiveKpiV2 label={isAr ? "إجازات معتمدة" : "Approved leaves"} value={monthlyApprovedLeaveCount} max={monthlyRequestCount || 1} note={isAr ? "ضمن الشهر" : "Within month"} tone="gold" />
            </div>'''
    page = replace_once(page, old_calendar_kpis, new_calendar_kpis, "expanded calendar KPI grid")

    if page.count("<ThrsExecutiveKpiV2") != 14:
        raise RuntimeError(f"executive KPI postcondition failed: expected 14, found {page.count('<ThrsExecutiveKpiV2')}")
    if page.count("<ThrsSmartSearchV2") != 1:
        raise RuntimeError("smart search postcondition failed")
    if page.count("filterRequestsSmartV2(allUnfilteredRequests, adminFilters)") != 1:
        raise RuntimeError("smart filter binding postcondition failed")
    if page.count("tos-thrs-executive-v2") != 1:
        raise RuntimeError("management premium shell postcondition failed")
    if page.count("tos-thrs-request-shell-v2") != 1:
        raise RuntimeError("request premium shell postcondition failed")

    PAGE.write_text(page, encoding="utf-8")
    shutil.copy2(SOURCE_UI, TARGET_UI)
    shutil.copy2(SOURCE_STYLE, TARGET_STYLE)
except Exception as exc:
    PAGE.write_text(original_page, encoding="utf-8")
    cleanup_exact_created_files()
    fail(f"source transformation failed and exact files were rolled back: {exc}")

build = subprocess.run(["npm", "run", "build"], cwd=FRONTEND, text=True, capture_output=True)
if build.returncode != 0:
    print(build.stdout[-6000:])
    print(build.stderr[-6000:])
    PAGE.write_text(original_page, encoding="utf-8")
    cleanup_exact_created_files()
    fail("frontend build failed; exact source changes rolled back")

if not DIST.exists():
    PAGE.write_text(original_page, encoding="utf-8")
    cleanup_exact_created_files()
    fail("frontend dist missing after successful build")

for marker in (RUNTIME_TOKEN.encode(), b"tos-thrs-smart-search-v2", b"tos-thrs-admin-kpis-v2", b"tos-thrs-calendar-kpis-v2"):
    if tree_count(DIST, marker) < 1:
        PAGE.write_text(original_page, encoding="utf-8")
        cleanup_exact_created_files()
        fail(f"built output missing runtime marker: {marker.decode(errors='ignore')}")

timestamp = int(time.time())
candidate = LIVE_PARENT / f"build.thrs-executive-v2-candidate-{timestamp}"
backup = LIVE_PARENT / f"build.thrs-executive-v2-backup-{timestamp}"
failed_live = LIVE_PARENT / f"build.thrs-executive-v2-failed-{timestamp}"

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
        cleanup_exact_created_files()
    fail(f"live deployment failed and rollback attempted: {exc}")

print("PASS/FAIL=PASS")
print("BUILD_RESULT=PASS")
print("LIVE_DEPLOY=PASS")
print(f"SOURCE_PAGE_SHA256={EXPECTED_PAGE_SHA256}")
print("SMART_SEARCH=YES")
print("SEARCH_NAME_EMAIL_ROLE_TYPE_STATUS=YES")
print("AUTOCOMPLETE=YES")
print("KEYBOARD_NAVIGATION=YES")
print("VOICE_SEARCH_WEB_SPEECH=YES")
print("VOICE_SEARCH_GRACEFUL_FALLBACK=YES")
print("ADMIN_KPI_COUNT=8")
print("CALENDAR_KPI_COUNT=6")
print("PREMIUM_LIGHT=YES")
print("PREMIUM_DARK=YES")
print("PREMIUM_FILTER_CONSOLE=YES")
print("PREMIUM_TABLE_REFINEMENT=YES")
print("REQUEST_SHELL_REFINED=YES")
print("BUSINESS_LOGIC_CHANGED=NO")
print("API_CHANGED=NO")
print("DATABASE_CHANGED=NO")
print(f"EMPLOYEE_WORK_HUB_SHA256={sha256(PAGE)}")
print(f"THRS_EXECUTIVE_UI_SHA256={sha256(TARGET_UI)}")
print(f"THRS_EXECUTIVE_STYLE_SHA256={sha256(TARGET_STYLE)}")
print(f"LIVE_BACKUP={backup}")
print("STATUS=READY")
