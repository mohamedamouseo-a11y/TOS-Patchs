from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "TOS-EMPLOYEE-WORK-HUB-PREMIUM-DATE-PICKER-V1" / "apply_employee_work_hub_premium_date_picker_v1.py"

print("RUNNING=EMPLOYEE_WORK_HUB_PREMIUM_DATE_PICKER_V1_1")

if not SOURCE.exists():
    print("PASS/FAIL=FAIL")
    print(f"ERROR=base patch script missing: {SOURCE}")
    sys.exit(1)

text = SOURCE.read_text(encoding="utf-8")
bad = '''    if page.count('type=\"date\"') != 0:\n        raise RuntimeError(f\"native date inputs remain after patch: {page.count('type=\\\"date\\\"')}\")'''
good = '''    remaining_native_dates = page.count('type=\"date\"')\n    if remaining_native_dates != 0:\n        raise RuntimeError(f\"native date inputs remain after patch: {remaining_native_dates}\")'''

if text.count(bad) != 1:
    print("PASS/FAIL=FAIL")
    print(f"ERROR=expected one V1 syntax-fix target, found {text.count(bad)}")
    sys.exit(1)

fixed = text.replace(bad, good, 1)
try:
    code = compile(fixed, str(SOURCE) + "[V1.1]", "exec")
except SyntaxError as exc:
    print("PASS/FAIL=FAIL")
    print(f"ERROR=corrected patch failed compile validation: {exc}")
    sys.exit(1)

root_arg = sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS"
sys.argv = [str(SOURCE), root_arg]
namespace = {"__name__": "__main__", "__file__": str(SOURCE)}
exec(code, namespace, namespace)
