from pathlib import Path
import sys

PATCH_ROOT = Path(__file__).resolve().parents[1]
BASE_DIR = PATCH_ROOT / "TOS-UXUI-PHASE-04-4-TEAM-PERFORMANCE-FLAGSHIP-V3-1-VISUAL-POLISH"
BASE_SCRIPT = BASE_DIR / "apply_phase04_4_team_performance_flagship_v3_1_visual_polish.py"

OLD_SHA = 'EXPECTED_V3_STYLE_SHA256 = "964d249bd73af032442221a26e776bbf8639599e8667591d8699cdadb2e02f9a"'
NEW_SHA = 'EXPECTED_V3_STYLE_SHA256 = "cc05e379d19ee6b2fff7d80995e926fd69b3f825cde5e28265cbafb07d0ae427"'

print("RUNNING=PHASE04_4_TEAM_PERFORMANCE_FLAGSHIP_V3_1_1_CURRENT_V3_GUARD_RECOVERY_WRAPPER")

if not BASE_SCRIPT.exists():
    print("PASS/FAIL=FAIL")
    print(f"ERROR=base V3.1 script missing: {BASE_SCRIPT}")
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("V3_1_RUNTIME=NO")
    sys.exit(1)

source = BASE_SCRIPT.read_text(encoding="utf-8")
if source.count(OLD_SHA) != 1:
    print("PASS/FAIL=FAIL")
    print("ERROR=expected original V3.1 guard anchor not found exactly once")
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("V3_1_RUNTIME=NO")
    sys.exit(1)

source = source.replace(OLD_SHA, NEW_SHA, 1)

# Preserve the base script path so its visual-polish CSS asset resolves from the approved V3.1 patch directory.
namespace = {
    "__name__": "__main__",
    "__file__": str(BASE_SCRIPT),
}
exec(compile(source, str(BASE_SCRIPT), "exec"), namespace, namespace)
