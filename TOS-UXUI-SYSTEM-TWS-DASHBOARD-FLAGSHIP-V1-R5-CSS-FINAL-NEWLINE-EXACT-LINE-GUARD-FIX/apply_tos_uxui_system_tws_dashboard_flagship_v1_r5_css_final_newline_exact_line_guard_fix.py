from pathlib import Path
import sys

PATCH_ROOT = Path(__file__).resolve().parents[1]
BASE_R3 = PATCH_ROOT / "TOS-UXUI-SYSTEM-TWS-DASHBOARD-FLAGSHIP-V1-R3-PARTIAL-STATE-CSS-RECONCILE" / "apply_tos_uxui_system_tws_dashboard_flagship_v1_r3_partial_state_css_reconcile.py"

print("RUNNING=TOS_UXUI_SYSTEM_TWS_DASHBOARD_FLAGSHIP_V1_R5_CSS_FINAL_NEWLINE_EXACT_LINE_GUARD_FIX")

if not BASE_R3.exists():
    print("PASS/FAIL=FAIL")
    print(f"ERROR=base R3 installer missing: {BASE_R3}")
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("TWS_DASHBOARD_FLAGSHIP_V1_R5_RUNTIME=NO")
    sys.exit(1)

source = BASE_R3.read_text(encoding="utf-8")

OLD_LINE = 'css_text = base_text[start:end]'
NEW_LINE = 'css_text = base_text[start:end] + "\\n"'
OLD_RUNNING = 'print("RUNNING=TOS_UXUI_SYSTEM_TWS_DASHBOARD_FLAGSHIP_V1_R3_PARTIAL_STATE_CSS_RECONCILE")'
NEW_RUNNING = 'print("RUNNING=TOS_UXUI_SYSTEM_TWS_DASHBOARD_FLAGSHIP_V1_R5_CSS_FINAL_NEWLINE_EXACT_LINE_GUARD_FIX_INNER")'
OLD_RUNTIME_NO = 'print("TWS_DASHBOARD_FLAGSHIP_V1_R3_RUNTIME=NO")'
NEW_RUNTIME_NO = 'print("TWS_DASHBOARD_FLAGSHIP_V1_R5_RUNTIME=NO")'
OLD_RUNTIME_YES = 'print("TWS_DASHBOARD_FLAGSHIP_V1_R3_RUNTIME=YES")'
NEW_RUNTIME_YES = 'print("TWS_DASHBOARD_FLAGSHIP_V1_R5_RUNTIME=YES")'

lines = source.splitlines()
if lines.count(OLD_LINE) != 1:
    print("PASS/FAIL=FAIL")
    print(f"ERROR=R5 exact CSS extraction line mismatch: expected 1, found {lines.count(OLD_LINE)}")
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("TWS_DASHBOARD_FLAGSHIP_V1_R5_RUNTIME=NO")
    sys.exit(1)

for needle, label in (
    (OLD_RUNNING, "RUNNING marker"),
    (OLD_RUNTIME_NO, "runtime NO marker"),
    (OLD_RUNTIME_YES, "runtime YES marker"),
):
    count = source.count(needle)
    if count != 1:
        print("PASS/FAIL=FAIL")
        print(f"ERROR=R5 wrapper {label} mismatch: expected 1, found {count}")
        print("BUILD_RESULT=FAIL_OR_SKIPPED")
        print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
        print("TWS_DASHBOARD_FLAGSHIP_V1_R5_RUNTIME=NO")
        sys.exit(1)

corrected_lines = [NEW_LINE if line == OLD_LINE else line for line in lines]
corrected = "\n".join(corrected_lines)
if source.endswith("\n"):
    corrected += "\n"

corrected = corrected.replace(OLD_RUNNING, NEW_RUNNING, 1)
corrected = corrected.replace(OLD_RUNTIME_NO, NEW_RUNTIME_NO, 1)
corrected = corrected.replace(OLD_RUNTIME_YES, NEW_RUNTIME_YES, 1)

post_lines = corrected.splitlines()
if post_lines.count(NEW_LINE) != 1 or post_lines.count(OLD_LINE) != 0:
    print("PASS/FAIL=FAIL")
    print(f"ERROR=R5 exact-line correction failed: new={post_lines.count(NEW_LINE)} old={post_lines.count(OLD_LINE)}")
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("TWS_DASHBOARD_FLAGSHIP_V1_R5_RUNTIME=NO")
    sys.exit(1)

# R5 fixes only the false-positive wrapper guard from R4-R1.
# It applies the same one-newline correction directly to the original R3 installer.
# R3 still owns the exact partial-state source SHA check, missing-stylesheet requirement,
# stylesheet blob verification, TWS behavior guards, preservation checks, cleanup-on-failure,
# build verification, atomic live deploy, live verification, and rollback.
namespace = {
    "__name__": "__main__",
    "__file__": str(BASE_R3),
}
exec(compile(corrected, str(BASE_R3), "exec"), namespace, namespace)
