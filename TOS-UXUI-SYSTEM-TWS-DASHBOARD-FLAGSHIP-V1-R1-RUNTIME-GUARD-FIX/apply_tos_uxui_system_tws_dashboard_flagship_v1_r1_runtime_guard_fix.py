from pathlib import Path
import sys

PATCH_ROOT = Path(__file__).resolve().parents[1]
BASE_SCRIPT = PATCH_ROOT / "TOS-UXUI-SYSTEM-TWS-DASHBOARD-FLAGSHIP-V1" / "apply_tos_uxui_system_tws_dashboard_flagship_v1.py"

print("RUNNING=TOS_UXUI_SYSTEM_TWS_DASHBOARD_FLAGSHIP_V1_R1_RUNTIME_GUARD_FIX")

if not BASE_SCRIPT.exists():
    print("PASS/FAIL=FAIL")
    print(f"ERROR=base TWS V1 installer missing: {BASE_SCRIPT}")
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("TWS_DASHBOARD_FLAGSHIP_V1_R1_RUNTIME=NO")
    sys.exit(1)

source = BASE_SCRIPT.read_text(encoding="utf-8")

OLD_DIST_MARKER = "    b'TWS_RESULT_PAGE_SIZE',\n"
NEW_DIST_MARKER = "    b'tos-tws-pagination__page',\n"
OLD_RUNNING = 'print("RUNNING=TOS_UXUI_SYSTEM_TWS_DASHBOARD_FLAGSHIP_V1")'
NEW_RUNNING = 'print("RUNNING=TOS_UXUI_SYSTEM_TWS_DASHBOARD_FLAGSHIP_V1_R1_RUNTIME_GUARD_FIX_INNER")'

if source.count(OLD_DIST_MARKER) != 1:
    print("PASS/FAIL=FAIL")
    print(f"ERROR=base installer dist-marker anchor mismatch: {source.count(OLD_DIST_MARKER)}")
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("TWS_DASHBOARD_FLAGSHIP_V1_R1_RUNTIME=NO")
    sys.exit(1)

if source.count(NEW_DIST_MARKER) != 0:
    print("PASS/FAIL=FAIL")
    print("ERROR=base installer already contains corrected runtime marker")
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("TWS_DASHBOARD_FLAGSHIP_V1_R1_RUNTIME=NO")
    sys.exit(1)

if source.count(OLD_RUNNING) != 1:
    print("PASS/FAIL=FAIL")
    print("ERROR=base installer RUNNING marker mismatch")
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("TWS_DASHBOARD_FLAGSHIP_V1_R1_RUNTIME=NO")
    sys.exit(1)

corrected = source.replace(OLD_DIST_MARKER, NEW_DIST_MARKER, 1).replace(OLD_RUNNING, NEW_RUNNING, 1)
if corrected.count(NEW_DIST_MARKER) != 1 or OLD_DIST_MARKER in corrected:
    print("PASS/FAIL=FAIL")
    print("ERROR=R1 in-memory runtime guard correction failed")
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("TWS_DASHBOARD_FLAGSHIP_V1_R1_RUNTIME=NO")
    sys.exit(1)

# R1 changes runtime verification only. Baseline SHA guard, source transforms,
# API behavior guards, preservation checks, build, deploy, and rollback remain
# byte-identical to TWS Dashboard Flagship V1.
namespace = {
    "__name__": "__main__",
    "__file__": str(BASE_SCRIPT),
}
exec(compile(corrected, str(BASE_SCRIPT), "exec"), namespace, namespace)
