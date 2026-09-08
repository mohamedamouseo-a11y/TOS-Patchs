from pathlib import Path
import sys

print("RUNNING=TOS_UXUI_SYSTEM_TWS_DASHBOARD_FLAGSHIP_V2_1_R1_DOCUMENT_CARD_GUARD_FIX")

PATCH_ROOT = Path(__file__).resolve().parents[1]
BASE = PATCH_ROOT / "TOS-UXUI-SYSTEM-TWS-DASHBOARD-FLAGSHIP-V2-1-BUTTONS-LUXURY-POLISH" / "apply_tos_uxui_system_tws_dashboard_flagship_v2_1_buttons_luxury_polish.py"

if not BASE.exists():
    print("PASS/FAIL=FAIL")
    print(f"ERROR=base V2.1 installer missing: {BASE}")
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("TWS_DASHBOARD_FLAGSHIP_V2_1_R1_RUNTIME=NO")
    sys.exit(1)

source = BASE.read_text(encoding="utf-8")
TOKEN = "tos-tws-document-card group relative flex flex-col gap-3 p-4"
NEW_LINE = "    'tos-tws-document-card group relative flex flex-col gap-3 p-4',"

lines = source.splitlines()
matches = [i for i, line in enumerate(lines) if TOKEN in line]
if len(matches) != 1:
    print("PASS/FAIL=FAIL")
    print(f"ERROR=R1 expected exactly one V2.1 document-card guard token, found {len(matches)}")
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("TWS_DASHBOARD_FLAGSHIP_V2_1_R1_RUNTIME=NO")
    sys.exit(1)

index = matches[0]
if "className=" not in lines[index]:
    print("PASS/FAIL=FAIL")
    print("ERROR=R1 matched document-card token is not the obsolete className guard")
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("TWS_DASHBOARD_FLAGSHIP_V2_1_R1_RUNTIME=NO")
    sys.exit(1)

lines[index] = NEW_LINE
corrected = "\n".join(lines) + ("\n" if source.endswith("\n") else "")

corrected_lines = corrected.splitlines()
if corrected_lines.count(NEW_LINE) != 1:
    print("PASS/FAIL=FAIL")
    print("ERROR=R1 corrected document-card guard count mismatch")
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("TWS_DASHBOARD_FLAGSHIP_V2_1_R1_RUNTIME=NO")
    sys.exit(1)
if any(TOKEN in line and "className=" in line for line in corrected_lines):
    print("PASS/FAIL=FAIL")
    print("ERROR=R1 obsolete className document-card guard still present")
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("TWS_DASHBOARD_FLAGSHIP_V2_1_R1_RUNTIME=NO")
    sys.exit(1)

# Execute the original V2.1 installer entirely in memory with only the false guard corrected.
# sys.argv is intentionally preserved so the target root remains /var/www/TOS.
namespace = {
    "__name__": "__main__",
    "__file__": str(BASE),
}
try:
    code = compile(corrected, str(BASE) + "#R1", "exec")
    exec(code, namespace, namespace)
except SystemExit:
    raise
except Exception as exc:
    print("PASS/FAIL=FAIL")
    print(f"ERROR=R1 in-memory execution failed: {exc}")
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("TWS_DASHBOARD_FLAGSHIP_V2_1_R1_RUNTIME=NO")
    sys.exit(1)

print("TWS_DASHBOARD_FLAGSHIP_V2_1_R1_RUNTIME=YES")
