from pathlib import Path
import hashlib
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
PATCH_ROOT = Path(__file__).resolve().parent.parent
BASE = PATCH_ROOT / "TOS-GLOBAL-PERFORMANCE-POST-PAINT-ASSET-DELIVERY-V1" / "apply_tos_global_performance_post_paint_asset_delivery_v1.py"
EXPECTED_BASE_BLOB_SHA = "9f224f10621e4173b01fbc4e42ae20b6c476221c"

print("RUNNING=TOS_GLOBAL_PERFORMANCE_POST_PAINT_ASSET_DELIVERY_V1_R1")


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def fail(message: str):
    print("PASS/FAIL=FAIL")
    print("ERROR=" + str(message))
    print("R1_REGEX_FIX=NO")
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    sys.exit(1)


if not BASE.exists():
    fail(f"base installer missing: {BASE}")
actual_blob = git_blob_sha(BASE)
if actual_blob != EXPECTED_BASE_BLOB_SHA:
    fail(f"base installer mismatch: {actual_blob}")

source = BASE.read_text(encoding="utf-8")
# V1 accidentally emitted two backslashes in the two entry-JS regexes. In a
# Python raw regex that would look for a literal backslash before any char,
# instead of matching the normal `.js` suffix. Correct only those 2 tokens in
# memory; the V1 source file in the patch repository remains immutable.
old = "\\\\.js"
new = "\\.js"
if source.count(old) != 2:
    fail(f"entry regex correction anchor mismatch: {source.count(old)}")
corrected = source.replace(old, new)

print("R1_ROOT_CAUSE=ENTRY_JS_REGEX_DOUBLE_ESCAPE")
print("R1_BASE_INSTALLER=EXACT_GUARDED")
print("R1_REGEX_FIX=IN_MEMORY_ONLY")
print("R1_EXECUTION=CORRECTED_V1_INSTALLER")

old_argv = sys.argv[:]
try:
    sys.argv = [str(BASE), str(ROOT)]
    exec(compile(corrected, str(BASE), "exec"), {
        "__file__": str(BASE),
        "__name__": "__main__",
    })
finally:
    sys.argv = old_argv

print("R1_REGEX_FIX=YES")
print("R1_STATUS=READY")