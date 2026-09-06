from pathlib import Path
import hashlib
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
PATCH_ROOT = Path(__file__).resolve().parent.parent
BASE_DIR = PATCH_ROOT / "TOS-UXUI-GLOBAL-TCS-FLAGSHIP-V1-5-SMART-SEARCH-EXECUTIVE-POLISH"
BASE_INSTALLER = BASE_DIR / "apply_tos_global_tcs_flagship_v1_5_smart_search_executive_polish.py"
BASE_CSS = BASE_DIR / "tcsFlagshipV1_5SmartSearchExecutivePolish.css"
CHAT = ROOT / "frontend/src/components/ChatPanel.jsx"

EXPECTED_BASE_INSTALLER_GIT_BLOB_SHA = "3819507126862348e7b6427df39ef730c5b8e33b"
EXPECTED_BASE_CSS_GIT_BLOB_SHA = "2d55b76d4b0d6965748f58be207ed4623847a7c3"
EXPECTED_CHAT_GIT_BLOB_SHA = "839eb37b5af54ab0819cb852442f895eaeed73f8"
FAULTY_GUARD = "'sendMessage', 'uploadFiles',"
FIXED_GUARD = "'sendMessage', 'uploadChatFile',"

print("RUNNING=TOS_GLOBAL_TCS_FLAGSHIP_V1_5_R1_SMART_SEARCH_GUARD_FIX")


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def fail(message: str):
    print("PASS/FAIL=FAIL")
    print("ERROR=" + str(message))
    print("R1_GUARD_FIX=NO")
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    sys.exit(1)


if ROOT.resolve() == Path("/"):
    fail("unsafe ROOT")

for path in (BASE_INSTALLER, BASE_CSS, CHAT):
    if not path.exists():
        fail(f"required path missing: {path}")

if git_blob_sha(BASE_INSTALLER) != EXPECTED_BASE_INSTALLER_GIT_BLOB_SHA:
    fail(f"base V1.5 installer mismatch: {git_blob_sha(BASE_INSTALLER)}")
if git_blob_sha(BASE_CSS) != EXPECTED_BASE_CSS_GIT_BLOB_SHA:
    fail(f"base V1.5 CSS mismatch: {git_blob_sha(BASE_CSS)}")
if git_blob_sha(CHAT) != EXPECTED_CHAT_GIT_BLOB_SHA:
    fail(f"ChatPanel.jsx baseline mismatch: {git_blob_sha(CHAT)}")

chat_source = CHAT.read_text(encoding="utf-8")
if "uploadChatFile" not in chat_source:
    fail("actual ChatPanel upload primitive missing: uploadChatFile")
if "uploadFiles" in chat_source:
    fail("unexpected legacy uploadFiles token exists in current ChatPanel; STOP for manual review")
if "sendMessage" not in chat_source:
    fail("sendMessage token missing from ChatPanel")
if "api.chat.search" not in chat_source:
    fail("api.chat.search token missing from ChatPanel")

base_source = BASE_INSTALLER.read_text(encoding="utf-8")
if base_source.count(FAULTY_GUARD) != 1:
    fail(f"faulty V1.5 guard anchor mismatch: {base_source.count(FAULTY_GUARD)}")
if FIXED_GUARD in base_source:
    fail("base V1.5 installer already contains the R1 guard fix")

corrected_source = base_source.replace(FAULTY_GUARD, FIXED_GUARD, 1)
if FAULTY_GUARD in corrected_source:
    fail("faulty uploadFiles guard remained after in-memory correction")
if corrected_source.count(FIXED_GUARD) != 1:
    fail("uploadChatFile guard correction count mismatch")

print("R1_ROOT_CAUSE=VALIDATION_TOKEN_ONLY")
print("R1_EXPECTED_UPLOAD_PRIMITIVE=uploadChatFile")
print("R1_LEGACY_UPLOADFILES_TOKEN=ABSENT")
print("R1_BASE_INSTALLER=EXACT_GUARDED")
print("R1_BASE_CSS=EXACT_GUARDED")
print("R1_CHAT_BASELINE=EXACT_GUARDED")
print("R1_EXECUTION=IN_MEMORY_CORRECTED_V1_5_INSTALLER")

old_argv = sys.argv[:]
try:
    sys.argv = [str(BASE_INSTALLER), str(ROOT)]
    exec(compile(corrected_source, str(BASE_INSTALLER), "exec"), {
        "__file__": str(BASE_INSTALLER),
        "__name__": "__main__",
    })
finally:
    sys.argv = old_argv

print("R1_GUARD_FIX=YES")
print("R1_UPLOAD_GUARD=uploadChatFile")
print("R1_MESSAGING_IMPLEMENTATION_CHANGED=NO")
print("R1_API_CHANGED=NO")
print("R1_DATABASE_CHANGED=NO")
print("R1_STATUS=READY")
