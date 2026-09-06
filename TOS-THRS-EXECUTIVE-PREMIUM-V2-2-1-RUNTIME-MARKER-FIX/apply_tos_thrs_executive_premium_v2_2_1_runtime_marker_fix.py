from pathlib import Path
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
PATCH_DIR = Path(__file__).resolve().parent
BASE_SCRIPT = PATCH_DIR.parent / "TOS-THRS-EXECUTIVE-PREMIUM-V2-2-DENSITY-REFINEMENT" / "apply_tos_thrs_executive_premium_v2_2_density_refinement.py"

print("RUNNING=TOS_THRS_EXECUTIVE_PREMIUM_V2_2_1_RUNTIME_MARKER_FIX_WRAPPER")

if not BASE_SCRIPT.exists():
    print("PASS/FAIL=FAIL")
    print(f"ERROR=base V2.2 script missing: {BASE_SCRIPT}")
    sys.exit(1)

source = BASE_SCRIPT.read_text(encoding="utf-8")

# Execute the exact guarded V2.2 logic but resolve PATCH_DIR to this V2.2.1
# directory, whose override CSS carries a real custom-property runtime marker
# instead of a minifier-stripped comment marker.
source = source.replace(
    'print("RUNNING=TOS_THRS_EXECUTIVE_PREMIUM_V2_2_DENSITY_REFINEMENT")',
    'print("RUNNING=TOS_THRS_EXECUTIVE_PREMIUM_V2_2_1_RUNTIME_MARKER_FIX")',
    1,
)

namespace = {
    "__name__": "__main__",
    "__file__": str(Path(__file__).resolve()),
}
old_argv = sys.argv[:]
try:
    sys.argv = [str(Path(__file__).resolve()), str(ROOT)]
    exec(compile(source, str(BASE_SCRIPT), "exec"), namespace, namespace)
finally:
    sys.argv = old_argv
