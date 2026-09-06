from pathlib import Path
import hashlib
import sys

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "TOS-EMPLOYEE-WORK-HUB-PREMIUM-DATE-PICKER-V1" / "apply_employee_work_hub_premium_date_picker_v1.py"
EXPECTED_SOURCE_BLOB_SHA = "52140ad46ec7eae946d0604f66a276c810323b54"


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode("utf-8") + data).hexdigest()


def stop(message: str):
    print("RUNNING=EMPLOYEE_WORK_HUB_PREMIUM_DATE_PICKER_V1_2")
    print("PASS/FAIL=FAIL")
    print("ERROR=" + message)
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    sys.exit(1)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        stop(f"{label}: expected 1 patch-script target, found {count}")
    return text.replace(old, new, 1)


if not SOURCE.exists():
    stop(f"base patch script missing: {SOURCE}")
if git_blob_sha(SOURCE) != EXPECTED_SOURCE_BLOB_SHA:
    stop("base V1 patch script changed unexpectedly")

text = SOURCE.read_text(encoding="utf-8")

text = replace_once(
    text,
    'print("RUNNING=EMPLOYEE_WORK_HUB_PREMIUM_DATE_PICKER_V1")',
    'print("RUNNING=EMPLOYEE_WORK_HUB_PREMIUM_DATE_PICKER_V1_2")',
    "runtime label",
)

text = replace_once(
    text,
    '''native_before = original_page.count('type="date"')
if native_before != 6:
    fail(f"expected exactly 6 native date inputs in EmployeeWorkHub.jsx, found {native_before}")''',
    '''native_before = original_page.count('type="date"')
if native_before != 7:
    fail(f"expected exactly 7 native date inputs in EmployeeWorkHub.jsx, found {native_before}")''',
    "seven native dates guard",
)

overtime_tail = '''        (
            '<input type="date" value={form.startDate} onChange={(event) => setForm((current) => ({ ...current, startDate: event.target.value, endDate: event.target.value }))} className={inputClass()} required />',
            '<EmployeeWorkDatePickerV1 value={form.startDate} onChange={(value) => setForm((current) => ({ ...current, startDate: value, endDate: value }))} isAr={isAr} ariaLabel={isAr ? "تاريخ العمل الإضافي" : "Overtime date"} required />',
            "overtime date",
        ),
    ]'''

overtime_plus_admin = '''        (
            '<input type="date" value={form.startDate} onChange={(event) => setForm((current) => ({ ...current, startDate: event.target.value, endDate: event.target.value }))} className={inputClass()} required />',
            '<EmployeeWorkDatePickerV1 value={form.startDate} onChange={(value) => setForm((current) => ({ ...current, startDate: value, endDate: value }))} isAr={isAr} ariaLabel={isAr ? "تاريخ العمل الإضافي" : "Overtime date"} required />',
            "overtime date",
        ),
        (
            '<input type="date" value={adminFilters.requestDay} onChange={(event) => setAdminFilter("requestDay", event.target.value)} className={inputClass()} />',
            '<EmployeeWorkDatePickerV1 value={adminFilters.requestDay} onChange={(value) => setAdminFilter("requestDay", value)} isAr={isAr} ariaLabel={isAr ? "يوم الطلب" : "Request day"} />',
            "admin request-day filter",
        ),
    ]'''
text = replace_once(text, overtime_tail, overtime_plus_admin, "admin date filter replacement")

# Preserve the original safety condition while fixing the known Python parser issue in V1.
bad_syntax = '''    if page.count('type="date"') != 0:
        raise RuntimeError(f"native date inputs remain after patch: {page.count('type=\\"date\\"')}")'''
good_syntax = '''    remaining_native_dates = page.count('type="date"')
    if remaining_native_dates != 0:
        raise RuntimeError(f"native date inputs remain after patch: {remaining_native_dates}")'''
text = replace_once(text, bad_syntax, good_syntax, "V1 syntax fix")

text = replace_once(
    text,
    '''    if page.count("<EmployeeWorkDatePickerV1") != 6:
        raise RuntimeError("expected exactly 6 premium date picker usages")''',
    '''    if page.count("<EmployeeWorkDatePickerV1") != 7:
        raise RuntimeError("expected exactly 7 premium date picker usages")''',
    "seven premium picker postcondition",
)

text = replace_once(text, 'print("PREMIUM_DATE_PICKERS=6")', 'print("PREMIUM_DATE_PICKERS=7")', "report picker count")
text = replace_once(
    text,
    'print("OVERTIME_DATE=PREMIUM")',
    'print("OVERTIME_DATE=PREMIUM")\nprint("ADMIN_REQUEST_DAY_FILTER=PREMIUM")',
    "report admin filter date",
)

try:
    code = compile(text, str(SOURCE) + "[V1.2]", "exec")
except SyntaxError as exc:
    stop(f"V1.2 patch compile validation failed: {exc}")

root_arg = sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS"
sys.argv = [str(SOURCE), root_arg]
namespace = {"__name__": "__main__", "__file__": str(SOURCE)}
exec(code, namespace, namespace)
