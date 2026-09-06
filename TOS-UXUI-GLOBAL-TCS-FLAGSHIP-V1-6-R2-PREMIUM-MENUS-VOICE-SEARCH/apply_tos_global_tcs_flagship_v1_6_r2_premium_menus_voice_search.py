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

COUNT_GUARD_OLD = '''if original_chat.count("<select") != 7:\n    fail(f"expected 7 native TCS selects before V1.6, found {original_chat.count('<select')}")'''
COUNT_GUARD_NEW = '''if original_chat.count("<select") != 9:\n    fail(f"expected 9 native TCS selects before V1.6, found {original_chat.count('<select')}")'''

FINAL_SELECT_GUARD = '''if source.count("<select") != 0:\n    fail(f"native TCS selects remain after V1.6 transform: {source.count('<select')}")'''

OVERRIDE_ANCHOR = 'override_css = OVERRIDE.read_text(encoding="utf-8")'

print("RUNNING=TOS_GLOBAL_TCS_FLAGSHIP_V1_6_R2_PREMIUM_MENUS_VOICE_SEARCH")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def fail(message: str):
    print("PASS/FAIL=FAIL")
    print("ERROR=" + str(message))
    print("R2_NATIVE_SELECT_BASELINE=NO")
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

chat_source = CHAT.read_text(encoding="utf-8")
if chat_source.count("<select") != 9:
    fail(f"exact current ChatPanel must contain 9 native selects, found {chat_source.count('<select')}")

# Exact baseline inventory. These nine selects are pre-existing in the current V1.5 ChatPanel.
required_select_tokens = (
    'taskDraft.assignee',
    'taskDraft.priority',
    'newChannelType',
    'selectedDirectUserId',
    'advancedSearch.userId',
    'chatStatus',
)
for token in required_select_tokens:
    if token not in chat_source:
        fail(f"required current native-select token missing: {token}")
if chat_source.count('<select value={chatStatus}') != 2:
    fail(f"expected two native chatStatus selects, found {chat_source.count('<select value={chatStatus}')}")
if chat_source.count('<select value={newChannelType}') != 2:
    fail(f"expected two native newChannelType selects, found {chat_source.count('<select value={newChannelType}')}")
if chat_source.count('<select value={selectedDirectUserId}') != 2:
    fail(f"expected two native selectedDirectUserId selects, found {chat_source.count('<select value={selectedDirectUserId}')}")

base_source = BASE_INSTALLER.read_text(encoding="utf-8")
if base_source.count(COUNT_GUARD_OLD) != 1:
    fail(f"base count-guard anchor mismatch: {base_source.count(COUNT_GUARD_OLD)}")
if base_source.count(FINAL_SELECT_GUARD) != 1:
    fail(f"base final-select guard anchor mismatch: {base_source.count(FINAL_SELECT_GUARD)}")
if base_source.count(OVERRIDE_ANCHOR) != 1:
    fail(f"override-css anchor mismatch: {base_source.count(OVERRIDE_ANCHOR)}")

# The original V1.6 transformer already handles eight of the nine native selects.
# The missed ninth select is the duplicate Chat Status control inside Internal Notes.
internal_notes_select_old = '''              <select value={chatStatus} onChange={(event) => setChatStatus(event.target.value)} className="mb-2.5 w-full rounded-xl border border-zinc-100 bg-zinc-50 px-2.5 py-1.5 text-xs font-black text-zinc-700 outline-none dark:border-white/10 dark:bg-zinc-950 dark:text-zinc-200">\n                {chatStatusOptions.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}\n              </select>'''
internal_notes_select_new = '''              <TcsPremiumSelect value={chatStatus} onChange={setChatStatus} options={chatStatusOptions.map((item) => ({ value: item.value, label: item.label }))} placeholder={lang === "en" ? "Chat status" : "حالة الشات"} className="mb-2.5" />'''

if chat_source.count(internal_notes_select_old) != 1:
    fail(f"internal-notes Chat Status select anchor mismatch: {chat_source.count(internal_notes_select_old)}")

extra_transform = f'''\n# V1.6 R2: replace the ninth native select (Internal Notes Chat Status).\nold_internal_notes_status = {internal_notes_select_old!r}\nnew_internal_notes_status = {internal_notes_select_new!r}\nsource = replace_once(source, old_internal_notes_status, new_internal_notes_status, "internal-notes chat status select")\n\n'''

alignment_css = r'''

/* V1.6 R2 — keep Conversation Tools fully inside the TCS desktop window. */
.tcs-v16-tools-menu {
  left: auto !important;
  right: 0 !important;
}
[dir="rtl"] .tcs-v16-tools-menu {
  right: auto !important;
  left: 0 !important;
}
'''

corrected = base_source.replace(COUNT_GUARD_OLD, COUNT_GUARD_NEW, 1)
corrected = corrected.replace(FINAL_SELECT_GUARD, extra_transform + FINAL_SELECT_GUARD, 1)
corrected = corrected.replace(
    OVERRIDE_ANCHOR,
    'override_css = OVERRIDE.read_text(encoding="utf-8") + ' + repr(alignment_css),
    1,
)

if COUNT_GUARD_OLD in corrected:
    fail("legacy 7-select guard remained after correction")
if COUNT_GUARD_NEW not in corrected:
    fail("correct 9-select guard missing after correction")
if "internal-notes chat status select" not in corrected:
    fail("ninth-select transform missing after correction")

print("R2_ROOT_CAUSE=V1_6_INSTALLER_NATIVE_SELECT_INVENTORY_MISCOUNT")
print("R2_ACTUAL_NATIVE_SELECTS=9")
print("R2_ORIGINAL_V1_6_REPLACEMENTS=8")
print("R2_MISSED_SELECT=INTERNAL_NOTES_CHAT_STATUS")
print("R2_NATIVE_SELECT_BASELINE=EXACT_GUARDED")
print("R2_TOOLS_MENU_EDGE_ALIGNMENT=IN_MEMORY_FIX")
print("R2_EXECUTION=CORRECTED_V1_6_INSTALLER")

old_argv = sys.argv[:]
try:
    sys.argv = [str(BASE_INSTALLER), str(ROOT)]
    exec(compile(corrected, str(BASE_INSTALLER), "exec"), {
        "__file__": str(BASE_INSTALLER),
        "__name__": "__main__",
    })
finally:
    sys.argv = old_argv

print("R2_NATIVE_SELECT_BASELINE=YES")
print("R2_NATIVE_SELECTS_REMAINING=0")
print("R2_INTERNAL_NOTES_STATUS=PREMIUM")
print("R2_TOOLS_MENU_WINDOW_CONTAINED=YES")
print("R2_STATUS=READY")
