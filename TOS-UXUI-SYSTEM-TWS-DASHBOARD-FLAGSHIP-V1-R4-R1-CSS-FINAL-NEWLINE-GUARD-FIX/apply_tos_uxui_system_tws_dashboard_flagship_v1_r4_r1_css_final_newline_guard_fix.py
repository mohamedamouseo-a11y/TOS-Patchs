from pathlib import Path
import sys

PATCH_ROOT = Path(__file__).resolve().parents[1]
BASE_R3 = PATCH_ROOT / "TOS-UXUI-SYSTEM-TWS-DASHBOARD-FLAGSHIP-V1-R3-PARTIAL-STATE-CSS-RECONCILE" / "apply_tos_uxui_system_tws_dashboard_flagship_v1_r3_partial_state_css_reconcile.py"

print("RUNNING=TOS_UXUI_SYSTEM_TWS_DASHBOARD_FLAGSHIP_V1_R4_R1_CSS_FINAL_NEWLINE_GUARD_FIX")

if not BASE_R3.exists():
    print("PASS/FAIL=FAIL")
    print(f"ERROR=base R3 installer missing: {BASE_R3}")
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("TWS_DASHBOARD_FLAGSHIP_V1_R4_R1_RUNTIME=NO")
    sys.exit(1)

source = BASE_R3.read_text(encoding="utf-8")

OLD_LINE = 'css_text = base_text[start:end]'
NEW_LINE = 'css_text = base_text[start:end] + "\\n"'
OLD_RUNNING = 'print("RUNNING=TOS_UXUI_SYSTEM_TWS_DASHBOARD_FLAGSHIP_V1_R3_PARTIAL_STATE_CSS_RECONCILE")'
NEW_RUNNING = 'print("RUNNING=TOS_UXUI_SYSTEM_TWS_DASHBOARD_FLAGSHIP_V1_R4_R1_CSS_FINAL_NEWLINE_GUARD_FIX_INNER")'
OLD_RUNTIME_NO = 'print("TWS_DASHBOARD_FLAGSHIP_V1_R3_RUNTIME=NO")'
NEW_RUNTIME_NO = 'print("TWS_DASHBOARD_FLAGSHIP_V1_R4_R1_RUNTIME=NO")'
OLD_RUNTIME_YES = 'print("TWS_DASHBOARD_FLAGSHIP_V1_R3_RUNTIME=YES")'
NEW_RUNTIME_YES = 'print("TWS_DASHBOARD_FLAGSHIP_V1_R4_R1_RUNTIME=YES")'

checks = [
    (OLD_LINE, 1, "CSS extraction line"),
    (OLD_RUNNING, 1, "RUNNING marker"),
    (OLD_RUNTIME_NO, 1, "runtime NO marker"),
    (OLD_RUNTIME_YES, 1, "runtime YES marker"),
]
for needle, expected, label in checks:
    count = source.count(needle)
    if count != expected:
        print("PASS/FAIL=FAIL")
        print(f"ERROR=R4-R1 wrapper {label} mismatch: expected {expected}, found {count}")
        print("BUILD_RESULT=FAIL_OR_SKIPPED")
        print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
        print("TWS_DASHBOARD_FLAGSHIP_V1_R4_R1_RUNTIME=NO")
        sys.exit(1)

corrected = source
corrected = corrected.replace(OLD_LINE, NEW_LINE, 1)
corrected = corrected.replace(OLD_RUNNING, NEW_RUNNING, 1)
corrected = corrected.replace(OLD_RUNTIME_NO, NEW_RUNTIME_NO, 1)
corrected = corrected.replace(OLD_RUNTIME_YES, NEW_RUNTIME_YES, 1)

if corrected.count(NEW_LINE) != 1 or OLD_LINE in corrected:
    print("PASS/FAIL=FAIL")
    print("ERROR=R4-R1 in-memory final-newline correction failed")
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("TWS_DASHBOARD_FLAGSHIP_V1_R4_R1_RUNTIME=NO")
    sys.exit(1)

# R4-R1 changes only the extracted CSS payload's final newline.
# All R3 exact partial-state guards, page SHA verification, style blob verification,
# behavior checks, preservation checks, build, cleanup-on-failure, atomic deploy,
# live verification and rollback remain unchanged.
namespace = {
    "__name__": "__main__",
    "__file__": str(BASE_R3),
}
exec(compile(corrected, str(BASE_R3), "exec"), namespace, namespace)
