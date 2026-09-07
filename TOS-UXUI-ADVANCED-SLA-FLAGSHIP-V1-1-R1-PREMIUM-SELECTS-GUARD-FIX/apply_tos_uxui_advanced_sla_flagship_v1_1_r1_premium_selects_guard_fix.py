from pathlib import Path
import hashlib
import sys

PATCH_ROOT = Path(__file__).resolve().parents[1]
BASE_SCRIPT = PATCH_ROOT / "TOS-UXUI-ADVANCED-SLA-FLAGSHIP-V1-1-PREMIUM-SELECTS-DARK-FIELD-CONTRAST" / "apply_tos_uxui_advanced_sla_flagship_v1_1_premium_selects_dark_field_contrast.py"

print("RUNNING=TOS_UXUI_ADVANCED_SLA_FLAGSHIP_V1_1_R1_PREMIUM_SELECTS_GUARD_FIX")

if not BASE_SCRIPT.exists():
    print("PASS/FAIL=FAIL")
    print(f"ERROR=base V1.1 installer missing: {BASE_SCRIPT}")
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("ADVANCED_SLA_FLAGSHIP_V1_1_R1_RUNTIME=NO")
    sys.exit(1)

source = BASE_SCRIPT.read_text(encoding="utf-8")

WRONG_GUARD = "    'className=\"tos-advanced-sla-field w-full',\n"
CORRECT_GUARD = "    'const field = \"tos-advanced-sla-field w-full',\n"
OLD_RUNNING = 'print("RUNNING=TOS_UXUI_ADVANCED_SLA_FLAGSHIP_V1_1_PREMIUM_SELECTS_DARK_FIELD_CONTRAST")'
NEW_RUNNING = 'print("RUNNING=TOS_UXUI_ADVANCED_SLA_FLAGSHIP_V1_1_R1_PREMIUM_SELECTS_GUARD_FIX_INNER")'

if source.count(WRONG_GUARD) != 1:
    print("PASS/FAIL=FAIL")
    print(f"ERROR=base installer wrong-guard anchor mismatch: {source.count(WRONG_GUARD)}")
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("ADVANCED_SLA_FLAGSHIP_V1_1_R1_RUNTIME=NO")
    sys.exit(1)

if source.count(CORRECT_GUARD) != 0:
    print("PASS/FAIL=FAIL")
    print("ERROR=base installer already contains corrected field guard")
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("ADVANCED_SLA_FLAGSHIP_V1_1_R1_RUNTIME=NO")
    sys.exit(1)

if source.count(OLD_RUNNING) != 1:
    print("PASS/FAIL=FAIL")
    print("ERROR=base installer RUNNING marker mismatch")
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("ADVANCED_SLA_FLAGSHIP_V1_1_R1_RUNTIME=NO")
    sys.exit(1)

corrected = source.replace(WRONG_GUARD, CORRECT_GUARD, 1).replace(OLD_RUNNING, NEW_RUNNING, 1)

# R1 changes only the faulty preflight anchor. All transforms, baseline SHA guards,
# preservation checks, build, deploy, rollback, and runtime verification remain
# byte-identical to the original V1.1 installer.
if corrected.count(CORRECT_GUARD) != 1 or WRONG_GUARD in corrected:
    print("PASS/FAIL=FAIL")
    print("ERROR=R1 in-memory guard correction verification failed")
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("ADVANCED_SLA_FLAGSHIP_V1_1_R1_RUNTIME=NO")
    sys.exit(1)

namespace = {
    "__name__": "__main__",
    "__file__": str(BASE_SCRIPT),
}
exec(compile(corrected, str(BASE_SCRIPT), "exec"), namespace, namespace)
