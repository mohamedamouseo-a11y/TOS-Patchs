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

OLD_LINE = "    'className=\\\"tos-tws-document-card group relative flex flex-col gap-3 p-4\\\"',"
NEW_LINE = "    '\\\"tos-tws-document-card group relative flex flex-col gap-3 p-4\\\"',"

lines = source.splitlines()
old_matches = [i for i, line in enumerate(lines) if line == OLD_LINE]
if len(old_matches) != 1:
    print("PASS/FAIL=FAIL")
    print(f"ERROR=R1 expected exactly one obsolete document-card guard line, found {len(old_matches)}")
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("TWS_DASHBOARD_FLAGSHIP_V2_1_R1_RUNTIME=NO")
    sys.exit(1)

lines[old_matches[0]] = NEW_LINE
corrected = "\n".join(lines) + ("\n" if source.endswith("\n") else "")

if OLD_LINE in corrected.splitlines():
    print("PASS/FAIL=FAIL")
    print("ERROR=R1 obsolete document-card guard still present after correction")
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("TWS_DASHBOARD_FLAGSHIP_V2_1_R1_RUNTIME=NO")
    sys.exit(1)

if corrected.splitlines().count(NEW_LINE) != 1:
    print("PASS/FAIL=FAIL")
    print("ERROR=R1 corrected document-card guard count mismatch")
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("TWS_DASHBOARD_FLAGSHIP_V2_1_R1_RUNTIME=NO")
    sys.exit(1)

# Execute the original V2.1 installer entirely in memory with only the guard line corrected.
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
