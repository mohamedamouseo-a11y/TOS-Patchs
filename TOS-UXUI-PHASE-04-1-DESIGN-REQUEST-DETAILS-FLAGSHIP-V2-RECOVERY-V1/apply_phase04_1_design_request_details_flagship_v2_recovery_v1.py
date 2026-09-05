from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
PATCH_ROOT = Path(__file__).resolve().parent.parent
V2_SCRIPT = PATCH_ROOT / "TOS-UXUI-PHASE-04-1-DESIGN-REQUEST-DETAILS-FLAGSHIP-V2" / "apply_phase04_1_design_request_details_flagship_v2.py"

print("RECOVERY=PHASE04_1_DESIGN_REQUEST_DETAILS_FLAGSHIP_V2_RECOVERY_V1")

if not V2_SCRIPT.exists():
    print("PASS/FAIL=FAIL")
    print(f"ERROR=required V2 patch script missing: {V2_SCRIPT}")
    print("BUILD_RESULT=SKIPPED")
    print("LIVE_DEPLOY=SKIPPED")
    sys.exit(1)

text = V2_SCRIPT.read_text()

# V2 itself built successfully, but its verifier looked for the JSX source form
# data-dq-details-flagship="v2" inside minified production JS. Vite/esbuild does
# not preserve JSX attributes in that exact serialized form. Verify the stable
# attribute key instead, while keeping the V2-only CSS marker and menu-meta
# marker checks. Source validation still requires the exact v2 hook.
old_probe = "b'data-dq-details-flagship=\"v2\"'"
new_probe = 'b"data-dq-details-flagship"'
probe_count = text.count(old_probe)
if probe_count != 2:
    print("PASS/FAIL=FAIL")
    print(f"ERROR=unexpected V2 verifier shape: expected 2 brittle probes, found {probe_count}")
    print("BUILD_RESULT=SKIPPED")
    print("LIVE_DEPLOY=SKIPPED")
    sys.exit(1)

text = text.replace(old_probe, new_probe)
text = text.replace(
    'print("RUNNING=PHASE04_1_DESIGN_REQUEST_DETAILS_FLAGSHIP_V2")',
    'print("RUNNING=PHASE04_1_DESIGN_REQUEST_DETAILS_FLAGSHIP_V2_RECOVERY_V1")',
    1,
)

with tempfile.NamedTemporaryFile("w", suffix=".py", prefix="tos_dq_details_v2_recovery_", delete=False) as handle:
    handle.write(text)
    temp_script = Path(handle.name)

try:
    result = subprocess.run([sys.executable, str(temp_script), str(ROOT)])
    sys.exit(result.returncode)
finally:
    try:
        temp_script.unlink(missing_ok=True)
    except Exception:
        pass
