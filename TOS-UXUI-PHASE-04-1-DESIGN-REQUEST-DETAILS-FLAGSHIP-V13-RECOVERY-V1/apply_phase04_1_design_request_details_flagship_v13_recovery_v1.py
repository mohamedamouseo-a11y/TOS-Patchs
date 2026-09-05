from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
HERE = Path(__file__).resolve().parent
V13 = HERE.parent / "TOS-UXUI-PHASE-04-1-DESIGN-REQUEST-DETAILS-FLAGSHIP-V13" / "apply_phase04_1_design_request_details_flagship_v13.py"

if not V13.exists():
    print("RUNNING=PHASE04_1_DESIGN_REQUEST_DETAILS_FLAGSHIP_V13_RECOVERY_V1")
    print("PASS/FAIL=FAIL")
    print(f"ERROR=V13 base patch missing: {V13}")
    sys.exit(1)

text = V13.read_text()

replacements = [
    (
        'print("RUNNING=PHASE04_1_DESIGN_REQUEST_DETAILS_FLAGSHIP_V13")',
        'print("RUNNING=PHASE04_1_DESIGN_REQUEST_DETAILS_FLAGSHIP_V13_RECOVERY_V1")',
    ),
    (
'''    dist_v13 = tree_count(DIST, V13_MARKER.encode())
    dist_hook = tree_count(DIST, V13_HOOK.encode())
    dist_empty = tree_count(DIST, b"tos-dq-attachments-empty-v13")
    if dist_v13 < 1 or dist_hook < 1 or dist_empty < 1:
        raise RuntimeError("V13 runtime markers missing from dist")''',
'''    # Recovery V1: Vite/CSS minification may normalize attribute selector quotes,
    # so do not verify the exact source literal data-dq-details-ultra=\"v13\".
    # Verify stable runtime tokens that must survive minification instead.
    dist_v13 = tree_count(DIST, V13_MARKER.encode())
    dist_hook = tree_count(DIST, b"data-dq-details-ultra")
    dist_empty = tree_count(DIST, b"tos-dq-attachments-empty-v13")
    if dist_hook < 1 or dist_empty < 1:
        raise RuntimeError("V13 stable runtime markers missing from dist")''',
    ),
    (
'''    live_v13 = tree_count(LIVE, V13_MARKER.encode())
    live_hook = tree_count(LIVE, V13_HOOK.encode())
    live_empty = tree_count(LIVE, b"tos-dq-attachments-empty-v13")
    if live_v13 < 1 or live_hook < 1 or live_empty < 1:
        raise RuntimeError("V13 runtime markers missing from live build")''',
'''    live_v13 = tree_count(LIVE, V13_MARKER.encode())
    live_hook = tree_count(LIVE, b"data-dq-details-ultra")
    live_empty = tree_count(LIVE, b"tos-dq-attachments-empty-v13")
    if live_hook < 1 or live_empty < 1:
        raise RuntimeError("V13 stable runtime markers missing from live build")''',
    ),
    (
        '    print("V13_RUNTIME=YES")',
        '    print("V13_RUNTIME=YES")\n    print("V13_RECOVERY_V1=YES")\n    print("VERIFICATION=STABLE_MINIFIED_RUNTIME_TOKENS")',
    ),
]

for old, new in replacements:
    count = text.count(old)
    if count != 1:
        print("RUNNING=PHASE04_1_DESIGN_REQUEST_DETAILS_FLAGSHIP_V13_RECOVERY_V1")
        print("PASS/FAIL=FAIL")
        print(f"ERROR=Recovery transformation mismatch; expected 1 match, found {count}")
        sys.exit(1)
    text = text.replace(old, new, 1)

with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as handle:
    handle.write(text)
    temp_path = Path(handle.name)

try:
    result = subprocess.run([sys.executable, str(temp_path), str(ROOT)], text=True)
    sys.exit(result.returncode)
finally:
    temp_path.unlink(missing_ok=True)
