from pathlib import Path
import hashlib
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
PATCH_ROOT = Path(__file__).resolve().parent.parent
BASE = PATCH_ROOT / "TOS-GLOBAL-PERFORMANCE-CRITICAL-RENDER-V2" / "apply_tos_global_performance_critical_render_v2.py"
EXPECTED_BASE_BLOB_SHA = "2ae6e45c4505cbbebe31e7905ba066984051bf07"

print("RUNNING=TOS_GLOBAL_PERFORMANCE_CRITICAL_RENDER_V2_R1")


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def fail(message: str):
    print("PASS/FAIL=FAIL")
    print("ERROR=" + str(message))
    print("R1_VERIFICATION_FIX=NO")
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    sys.exit(1)


if not BASE.exists():
    fail(f"base installer missing: {BASE}")
if git_blob_sha(BASE) != EXPECTED_BASE_BLOB_SHA:
    fail(f"base installer mismatch: {git_blob_sha(BASE)}")

source = BASE.read_text(encoding="utf-8")
old = '''if re.search(r'<link[^>]+href=\"https://fonts\\.googleapis\\.com[^>]+rel=\"stylesheet\"', dist_index):\n    fail(\"Google Fonts still render-blocking in dist index\", originals)'''
new = '''blocking_font_check = re.sub(r'<noscript>.*?</noscript>', '', dist_index, flags=re.S)\nif re.search(r'<link[^>]+href=\"https://fonts\\.googleapis\\.com[^>]+rel=\"stylesheet\"', blocking_font_check):\n    fail(\"Google Fonts still render-blocking in active dist head\", originals)'''
if source.count(old) != 1:
    fail(f"verification anchor mismatch: {source.count(old)}")
corrected = source.replace(old, new, 1)

print("R1_ROOT_CAUSE=NOSCRIPT_FALLBACK_FALSE_POSITIVE_IN_BUILD_VERIFICATION")
print("R1_BASE_INSTALLER=EXACT_GUARDED")
print("R1_ACTIVE_HEAD_FONT_CHECK=NOSCRIPT_EXCLUDED")
print("R1_EXECUTION=IN_MEMORY_CORRECTED_V2_INSTALLER")

old_argv = sys.argv[:]
try:
    sys.argv = [str(BASE), str(ROOT)]
    exec(compile(corrected, str(BASE), "exec"), {
        "__file__": str(BASE),
        "__name__": "__main__",
    })
finally:
    sys.argv = old_argv

print("R1_VERIFICATION_FIX=YES")
print("R1_STATUS=READY")