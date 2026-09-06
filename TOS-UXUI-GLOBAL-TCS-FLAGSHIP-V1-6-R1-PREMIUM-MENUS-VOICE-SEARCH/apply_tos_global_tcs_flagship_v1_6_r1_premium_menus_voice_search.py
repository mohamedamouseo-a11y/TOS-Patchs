from pathlib import Path
import hashlib
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
PATCH_ROOT = Path(__file__).resolve().parent.parent
BASE_DIR = PATCH_ROOT / "TOS-UXUI-GLOBAL-TCS-FLAGSHIP-V1-6-PREMIUM-MENUS-VOICE-SEARCH"
BASE_INSTALLER = BASE_DIR / "apply_tos_global_tcs_flagship_v1_6_premium_menus_voice_search.py"
BASE_CSS = BASE_DIR / "tcsFlagshipV1_6PremiumMenusVoiceSearch.css"
CHAT = ROOT / "frontend/src/components/ChatPanel.jsx"
STYLE = ROOT / "frontend/src/components/tcsFlagshipV1.css"

EXPECTED_BASE_INSTALLER_BLOB_SHA = "5b367eaf88de3dfe4a31641d8192fe8d3ae20b69"
EXPECTED_BASE_CSS_BLOB_SHA = "5e041d76e07cdb45811af554b51710192f72932e"
EXPECTED_CHAT_SHA256 = "7f877606e25655c0938fb8dd3d4eaa18b141265dba355d38853b24d9dbf3f931"
EXPECTED_STYLE_SHA256 = "c82649dcbba417f2cbe0c1eefac778f2a3e7b5bccc08c1d2d66409e0b54cbd03"
ANCHOR = 'override_css = OVERRIDE.read_text(encoding="utf-8")'

print("RUNNING=TOS_GLOBAL_TCS_FLAGSHIP_V1_6_R1_PREMIUM_MENUS_VOICE_SEARCH")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def fail(message: str):
    print("PASS/FAIL=FAIL")
    print("ERROR=" + str(message))
    print("R1_MENU_ALIGNMENT=NO")
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    sys.exit(1)


for path in (BASE_INSTALLER, BASE_CSS, CHAT, STYLE):
    if not path.exists():
        fail(f"required path missing: {path}")

if git_blob_sha(BASE_INSTALLER) != EXPECTED_BASE_INSTALLER_BLOB_SHA:
    fail(f"base V1.6 installer mismatch: {git_blob_sha(BASE_INSTALLER)}")
if git_blob_sha(BASE_CSS) != EXPECTED_BASE_CSS_BLOB_SHA:
    fail(f"base V1.6 CSS mismatch: {git_blob_sha(BASE_CSS)}")
if sha256(CHAT) != EXPECTED_CHAT_SHA256:
    fail(f"ChatPanel V1.5 baseline mismatch: {sha256(CHAT)}")
if sha256(STYLE) != EXPECTED_STYLE_SHA256:
    fail(f"TCS style V1.5 baseline mismatch: {sha256(STYLE)}")

base_source = BASE_INSTALLER.read_text(encoding="utf-8")
if base_source.count(ANCHOR) != 1:
    fail(f"override-css anchor mismatch: {base_source.count(ANCHOR)}")

alignment_css = r'''

/* V1.6 R1 — keep Conversation Tools fully inside the TCS window. */
.tcs-v16-tools-menu {
  left: auto !important;
  right: 0 !important;
  overflow: visible !important;
}
.tcs-v16-tools-menu::before { border-radius: inherit; }
[dir="rtl"] .tcs-v16-tools-menu {
  right: auto !important;
  left: 0 !important;
}
'''
corrected = base_source.replace(
    ANCHOR,
    'override_css = OVERRIDE.read_text(encoding="utf-8") + ' + repr(alignment_css),
    1,
)

print("R1_BASE_V1_6=EXACT_GUARDED")
print("R1_CHAT_BASELINE=V1_5_EXACT")
print("R1_TOOLS_MENU_EDGE_ALIGNMENT=IN_MEMORY_FIX")
print("R1_EXECUTION=CORRECTED_V1_6_INSTALLER")

old_argv = sys.argv[:]
try:
    sys.argv = [str(BASE_INSTALLER), str(ROOT)]
    exec(compile(corrected, str(BASE_INSTALLER), "exec"), {
        "__file__": str(BASE_INSTALLER),
        "__name__": "__main__",
    })
finally:
    sys.argv = old_argv

print("R1_MENU_ALIGNMENT=YES")
print("R1_TOOLS_MENU_WINDOW_CONTAINED=YES")
print("R1_STATUS=READY")
