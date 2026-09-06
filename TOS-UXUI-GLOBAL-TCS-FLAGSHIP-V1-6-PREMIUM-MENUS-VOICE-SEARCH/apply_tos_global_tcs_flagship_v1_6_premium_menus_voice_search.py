from pathlib import Path
import hashlib
import shutil
import subprocess
import sys
import time

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
PATCH_DIR = Path(__file__).resolve().parent
CHAT = ROOT / "frontend/src/components/ChatPanel.jsx"
LAUNCHER = ROOT / "frontend/src/components/TcsFloatingLauncher.jsx"
WINDOW = ROOT / "frontend/src/components/TcsDesktopWindow.jsx"
STYLE = ROOT / "frontend/src/components/tcsFlagshipV1.css"
OVERRIDE = PATCH_DIR / "tcsFlagshipV1_6PremiumMenusVoiceSearch.css"
FRONTEND = ROOT / "frontend"
DIST = FRONTEND / "dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

EXPECTED_CHAT_SHA256 = "7f877606e25655c0938fb8dd3d4eaa18b141265dba355d38853b24d9dbf3f931"
EXPECTED_STYLE_SHA256 = "c82649dcbba417f2cbe0c1eefac778f2a3e7b5bccc08c1d2d66409e0b54cbd03"
EXPECTED_LAUNCHER_SHA256 = "2dfd109fbae96f97829233b95a266797b615b84a8facc8831d8c4efec023522d"
EXPECTED_WINDOW_SHA256 = "5aa5f8c047baa12f29cae33585e1f7be493c5bfbde43a706f4537dbe599dad70"
V15_RUNTIME = "--tos-tcs-flagship-v1-5-smart-search-runtime"
V16_RUNTIME = "--tos-tcs-flagship-v1-6-premium-menus-voice-search-runtime"
V12_COLLISION_ATTR = 'data-tcs-ramzy-collision-sync="v1.2"'

print("RUNNING=TOS_GLOBAL_TCS_FLAGSHIP_V1_6_PREMIUM_MENUS_VOICE_SEARCH")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_count(root: Path, needle: bytes) -> int:
    if not root.exists():
        return 0
    total = 0
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        try:
            total += path.read_bytes().count(needle)
        except OSError:
            pass
    return total


def fail(message: str):
    print("PASS/FAIL=FAIL")
    print("ERROR=" + str(message))
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("TCS_V1_6_RUNTIME=NO")
    sys.exit(1)


def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        fail(f"{label} anchor mismatch: {count}")
    return source.replace(old, new, 1)


if ROOT.resolve() == Path("/"):
    fail("unsafe ROOT")

for path in (CHAT, LAUNCHER, WINDOW, STYLE, OVERRIDE, FRONTEND, LIVE_PARENT):
    if not path.exists():
        fail(f"required path missing: {path}")

if sha256(CHAT) != EXPECTED_CHAT_SHA256:
    fail(f"ChatPanel.jsx V1.5 baseline mismatch: {sha256(CHAT)}")
if sha256(STYLE) != EXPECTED_STYLE_SHA256:
    fail(f"tcsFlagshipV1.css V1.5 baseline mismatch: {sha256(STYLE)}")
if sha256(LAUNCHER) != EXPECTED_LAUNCHER_SHA256:
    fail(f"TcsFloatingLauncher.jsx baseline mismatch: {sha256(LAUNCHER)}")
if sha256(WINDOW) != EXPECTED_WINDOW_SHA256:
    fail(f"TcsDesktopWindow.jsx baseline mismatch: {sha256(WINDOW)}")

original_chat = CHAT.read_text(encoding="utf-8")
original_style = STYLE.read_text(encoding="utf-8")
override_css = OVERRIDE.read_text(encoding="utf-8")
launcher_source = LAUNCHER.read_text(encoding="utf-8")

if V15_RUNTIME not in original_style:
    fail("TCS V1.5 runtime marker missing")
if V16_RUNTIME in original_style or "TcsPremiumSelect" in original_chat or "startVoiceSearch" in original_chat:
    fail("TCS V1.6 already applied")
if V16_RUNTIME not in override_css:
    fail("TCS V1.6 runtime marker missing from override")
if V12_COLLISION_ATTR not in launcher_source:
    fail("TCS V1.2 Ramzy collision sync marker missing")
for token in ("normalizeSmartSearchText", "smartSearchScore", 'value: "smart"', "tcs-v15-smart-search-dialog", "uploadChatFile", "sendMessage"):
    if token not in original_chat:
        fail(f"required V1.5/current behavior token missing: {token}")
if original_chat.count("<select") != 7:
    fail(f"expected 7 native TCS selects before V1.6, found {original_chat.count('<select')}")

source = original_chat

# 1) Reusable premium, searchable dropdown. Replaces browser-native menus while preserving values/onChange semantics.
component_anchor = "\n\nfunction deliveryStatusLabel(message = {}, isOwner = false) {"
if source.count(component_anchor) != 1:
    fail(f"premium select component anchor mismatch: {source.count(component_anchor)}")
premium_select_component = r'''

function TcsPremiumSelect({ value = "", options = [], onChange = () => {}, placeholder = "", searchable = false, searchPlaceholder = "", disabled = false, className = "" }) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const rootRef = useRef(null);
  const selected = options.find((item) => String(item.value) === String(value));
  const normalizedQuery = lowerText(query).trim();
  const visibleOptions = options.filter((item) => !normalizedQuery || lowerText(`${item.label || ""} ${item.meta || ""}`).includes(normalizedQuery));

  useEffect(() => {
    if (!open) return undefined;
    const handleOutside = (event) => {
      if (!rootRef.current?.contains(event.target)) setOpen(false);
    };
    document.addEventListener("pointerdown", handleOutside);
    return () => document.removeEventListener("pointerdown", handleOutside);
  }, [open]);

  function choose(nextValue) {
    onChange(nextValue);
    setOpen(false);
    setQuery("");
  }

  return (
    <div ref={rootRef} className={`tcs-v16-premium-select ${open ? "is-open" : ""} ${className}`} onKeyDown={(event) => { if (event.key === "Escape") setOpen(false); }}>
      <button type="button" disabled={disabled} onClick={() => setOpen((current) => !current)} className="tcs-v16-premium-select-trigger" aria-haspopup="listbox" aria-expanded={open}>
        <span className="tcs-v16-select-label">{selected?.label || placeholder}</span>
        <span className="tcs-v16-premium-select-chevron" aria-hidden="true">⌄</span>
      </button>
      {open && !disabled && (
        <div className="tcs-v16-premium-select-menu">
          {searchable && (
            <label className="tcs-v16-premium-select-search">
              <Search size={14} />
              <input value={query} onChange={(event) => setQuery(event.target.value)} autoFocus placeholder={searchPlaceholder || placeholder} />
            </label>
          )}
          <div className="tcs-v16-premium-select-options" role="listbox">
            {visibleOptions.map((item) => {
              const isSelected = String(item.value) === String(value);
              return (
                <button key={String(item.value)} type="button" role="option" aria-selected={isSelected} onClick={() => choose(item.value)} className={`tcs-v16-premium-select-option ${isSelected ? "is-selected" : ""}`}>
                  <span className="tcs-v16-premium-select-option-main">
                    <span className="tcs-v16-premium-select-option-label">{item.label}</span>
                    {item.meta && <span className="tcs-v16-premium-select-option-meta">{item.meta}</span>}
                  </span>
                  {isSelected && <span className="tcs-v16-premium-select-check">✓</span>}
                </button>
              );
            })}
            {!visibleOptions.length && <div className="tcs-v16-premium-select-empty">{currentChatLang() === "en" ? "No matching options" : "لا توجد نتائج مطابقة"}</div>}
          </div>
        </div>
      )}
    </div>
  );
}
'''
source = source.replace(component_anchor, premium_select_component + component_anchor, 1)

# 2) Voice-search state/ref: browser Web Speech API only; graceful unsupported-browser fallback.
state_anchor = '  const [workspaceSearchActiveIndex, setWorkspaceSearchActiveIndex] = useState(0);'
source = replace_once(source, state_anchor, state_anchor + '\n  const [voiceSearchListening, setVoiceSearchListening] = useState("");\n  const [voiceSearchSupported] = useState(() => typeof window !== "undefined" && Boolean(window.SpeechRecognition || window.webkitSpeechRecognition));', "voice search state")

ref_anchor = '  const longPressTimerRef = useRef(null);'
source = replace_once(source, ref_anchor, ref_anchor + '\n  const voiceSearchRecognitionRef = useRef(null);', "voice search ref")

cleanup_anchor = '''  useEffect(() => {\n    setWorkspaceSearchActiveIndex(0);\n  }, [workspaceSearchQuery, workspaceSearchType, activeChannelId, activeConversationId]);'''
cleanup_new = cleanup_anchor + '''\n\n  useEffect(() => () => {\n    try { voiceSearchRecognitionRef.current?.abort?.(); } catch {}\n    voiceSearchRecognitionRef.current = null;\n  }, []);'''
source = replace_once(source, cleanup_anchor, cleanup_new, "voice search cleanup")

voice_function_anchor = '  function highlightWorkspaceSearchText(value = "") {'
voice_functions = r'''  function startVoiceSearch(target = "workspace") {
    if (typeof window === "undefined") return;
    if (voiceSearchListening) {
      try { voiceSearchRecognitionRef.current?.abort?.(); } catch {}
      setVoiceSearchListening("");
      return;
    }
    const SpeechRecognitionApi = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognitionApi) {
      setLocalError(lang === "en" ? "Voice search is not supported in this browser." : "البحث الصوتي غير مدعوم في هذا المتصفح.");
      return;
    }
    try {
      const recognition = new SpeechRecognitionApi();
      recognition.lang = lang === "en" ? "en-US" : "ar-EG";
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.maxAlternatives = 1;
      voiceSearchRecognitionRef.current = recognition;
      setVoiceSearchListening(target);
      recognition.onresult = (event) => {
        const transcript = String(event.results?.[0]?.[0]?.transcript || "").trim();
        if (!transcript) return;
        if (target === "workspace") {
          setWorkspaceSearchType("smart");
          setWorkspaceSearchOpen(true);
          setWorkspaceSearchQuery((current) => `${current ? `${current} ` : ""}${transcript}`.trim());
        } else {
          setSearch((current) => `${current ? `${current} ` : ""}${transcript}`.trim());
        }
      };
      recognition.onerror = (event) => {
        if (event?.error === "aborted") return;
        const message = event?.error === "not-allowed"
          ? (lang === "en" ? "Microphone permission is required for voice search." : "اسمح باستخدام الميكروفون لتشغيل البحث الصوتي.")
          : (lang === "en" ? "Voice search could not understand the audio. Try again." : "تعذر فهم الصوت. جرّب مرة أخرى.");
        setLocalError(message);
      };
      recognition.onend = () => {
        setVoiceSearchListening("");
        voiceSearchRecognitionRef.current = null;
      };
      recognition.start();
    } catch {
      setVoiceSearchListening("");
      voiceSearchRecognitionRef.current = null;
      setLocalError(lang === "en" ? "Voice search could not start." : "تعذر بدء البحث الصوتي.");
    }
  }

'''
source = replace_once(source, voice_function_anchor, voice_functions + voice_function_anchor, "voice search function")

# 3) Replace all 7 native selects with premium controls/segmented status control.
old_new_channel_dark = '''                  <select value={newChannelType} onChange={(event) => setNewChannelType(event.target.value)} className="mt-2 w-full rounded-xl border border-white/10 bg-zinc-900 px-3 py-2 text-sm text-white outline-none">\n                    <option value="TEAM">{ui.teamChannel}</option>\n                    <option value="PRIVATE">{ui.privateChannel}</option>\n                  </select>'''
new_new_channel_dark = '''                  <TcsPremiumSelect value={newChannelType} onChange={setNewChannelType} options={[{ value: "TEAM", label: ui.teamChannel }, { value: "PRIVATE", label: ui.privateChannel }]} placeholder={ui.teamChannel} className="mt-2" />'''
source = replace_once(source, old_new_channel_dark, new_new_channel_dark, "desktop new-channel type select")

old_new_channel_light = '''                  <select value={newChannelType} onChange={(event) => setNewChannelType(event.target.value)} className="rounded-2xl border border-zinc-100 bg-white px-4 py-2 text-sm outline-none">\n                    <option value="TEAM">{ui.teamChannel}</option>\n                    <option value="PRIVATE">{ui.privateChannel}</option>\n                  </select>'''
new_new_channel_light = '''                  <TcsPremiumSelect value={newChannelType} onChange={setNewChannelType} options={[{ value: "TEAM", label: ui.teamChannel }, { value: "PRIVATE", label: ui.privateChannel }]} placeholder={ui.teamChannel} />'''
source = replace_once(source, old_new_channel_light, new_new_channel_light, "mobile/page new-channel type select")

old_direct_dark = '''                <select value={selectedDirectUserId} onChange={(event) => setSelectedDirectUserId(event.target.value)} className="w-full rounded-xl border border-white/10 bg-zinc-900 px-3 py-2 text-sm text-white outline-none">\n                  <option value="">{ui.chooseMember}</option>\n                  {availableDirectUsers.map((item) => <option key={item.id} value={item.id}>{item.name || item.email || item.role}</option>)}\n                </select>'''
new_direct_dark = '''                <TcsPremiumSelect value={selectedDirectUserId} onChange={setSelectedDirectUserId} options={availableDirectUsers.map((item) => ({ value: item.id, label: item.name || item.email || item.role, meta: item.email || item.jobTitle || item.role || "" }))} placeholder={ui.chooseMember} searchable searchPlaceholder={lang === "en" ? "Search members..." : "ابحث عن عضو..."} className="tcs-v16-member-picker" />'''
source = replace_once(source, old_direct_dark, new_direct_dark, "desktop direct-member select")

old_direct_light = '''                <select value={selectedDirectUserId} onChange={(event) => setSelectedDirectUserId(event.target.value)} className="min-w-0 flex-1 rounded-2xl border border-zinc-100 bg-white px-3 py-2 text-xs outline-none">\n                  <option value="">{ui.chooseMember}</option>\n                  {availableDirectUsers.map((item) => <option key={item.id} value={item.id}>{item.name || item.email || item.role}</option>)}\n                </select>'''
new_direct_light = '''                <TcsPremiumSelect value={selectedDirectUserId} onChange={setSelectedDirectUserId} options={availableDirectUsers.map((item) => ({ value: item.id, label: item.name || item.email || item.role, meta: item.email || item.jobTitle || item.role || "" }))} placeholder={ui.chooseMember} searchable searchPlaceholder={lang === "en" ? "Search members..." : "ابحث عن عضو..."} className="tcs-v16-member-picker min-w-0 flex-1" />'''
source = replace_once(source, old_direct_light, new_direct_light, "mobile direct-member select")

old_chat_status = '''                <select value={chatStatus} onChange={(event) => setChatStatus(event.target.value)} className="mb-2 w-full rounded-2xl border border-zinc-100 bg-zinc-50 px-3 py-2.5 text-xs font-black text-zinc-700 outline-none dark:border-white/10 dark:bg-zinc-950 dark:text-zinc-200" title={lang === "en" ? "Chat status" : "حالة الشات"}>\n                  {chatStatusOptions.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}\n                </select>'''
new_chat_status = '''                <div className="tcs-v16-status-segment mb-2 grid grid-cols-3 gap-1.5" aria-label={lang === "en" ? "Chat status" : "حالة الشات"}>{chatStatusOptions.map((item) => <button key={item.value} type="button" onClick={() => setChatStatus(item.value)} className={`rounded-xl px-2 py-2 text-[11px] font-black transition ${chatStatus === item.value ? "bg-amber-400 text-zinc-950 shadow-sm" : "border border-zinc-100 bg-zinc-50 text-zinc-600 dark:border-white/10 dark:bg-zinc-950 dark:text-zinc-300"}`}>{item.label}</button>)}</div>'''
source = replace_once(source, old_chat_status, new_chat_status, "chat status select")

old_advanced_user = '''              <select value={advancedSearch.userId} onChange={(event) => setAdvancedSearch((prev) => ({ ...prev, userId: event.target.value }))} className="rounded-2xl border border-zinc-100 bg-zinc-50 px-3 py-2 text-xs outline-none dark:border-white/10 dark:bg-zinc-950">\n                <option value="">كل المستخدمين</option>\n                {currentChatMembers.map((member) => <option key={member.id} value={member.id}>{member.name}</option>)}\n              </select>'''
new_advanced_user = '''              <TcsPremiumSelect value={advancedSearch.userId} onChange={(nextValue) => setAdvancedSearch((prev) => ({ ...prev, userId: nextValue }))} options={[{ value: "", label: lang === "en" ? "All users" : "كل المستخدمين" }, ...currentChatMembers.map((member) => ({ value: member.id, label: member.name || member.email, meta: member.email || member.jobTitle || "" }))]} placeholder={lang === "en" ? "All users" : "كل المستخدمين"} searchable searchPlaceholder={lang === "en" ? "Search users..." : "ابحث عن مستخدم..."} />'''
source = replace_once(source, old_advanced_user, new_advanced_user, "advanced-search user select")

old_task_assignee = '<select value={taskDraft.assignee} onChange={(event) => setTaskDraft((prev) => ({ ...prev, assignee: event.target.value }))} className="rounded-2xl border border-zinc-200 bg-white px-3 py-2 text-sm dark:border-white/10 dark:bg-white/5 dark:text-white"><option value="">بدون مسؤول</option>{currentChatMembers.map((member) => <option key={member.id} value={member.id}>{member.name || member.email}</option>)}</select>'
new_task_assignee = '<TcsPremiumSelect value={taskDraft.assignee} onChange={(nextValue) => setTaskDraft((prev) => ({ ...prev, assignee: nextValue }))} options={[{ value: "", label: lang === "en" ? "No assignee" : "بدون مسؤول" }, ...currentChatMembers.map((member) => ({ value: member.id, label: member.name || member.email, meta: member.email || "" }))]} placeholder={lang === "en" ? "No assignee" : "بدون مسؤول"} searchable searchPlaceholder={lang === "en" ? "Search members..." : "ابحث عن عضو..."} />'
source = replace_once(source, old_task_assignee, new_task_assignee, "task assignee select")

old_task_priority = '<select value={taskDraft.priority} onChange={(event) => setTaskDraft((prev) => ({ ...prev, priority: event.target.value }))} className="rounded-2xl border border-zinc-200 bg-white px-3 py-2 text-sm dark:border-white/10 dark:bg-white/5 dark:text-white"><option value="LOW">Low</option><option value="MEDIUM">Medium</option><option value="HIGH">High</option></select>'
new_task_priority = '<TcsPremiumSelect value={taskDraft.priority} onChange={(nextValue) => setTaskDraft((prev) => ({ ...prev, priority: nextValue }))} options={[{ value: "LOW", label: "Low" }, { value: "MEDIUM", label: "Medium" }, { value: "HIGH", label: "High" }]} placeholder="Medium" />'
source = replace_once(source, old_task_priority, new_task_priority, "task priority select")

if source.count("<select") != 0:
    fail(f"native TCS selects remain after V1.6 transform: {source.count('<select')}")

# 4) Conversation tools becomes a contained premium executive menu and no longer hangs off the window edge.
tools_class_old = 'className="absolute left-0 top-12 z-30 w-[340px] rounded-[24px] border border-zinc-100 bg-white p-3 text-right shadow-2xl shadow-zinc-900/15 dark:border-white/10 dark:bg-zinc-900"'
tools_class_new = 'className="tcs-v16-tools-menu absolute left-0 top-12 z-30 w-[340px] rounded-[24px] border border-zinc-100 bg-white p-3 text-right shadow-2xl shadow-zinc-900/15 dark:border-white/10 dark:bg-zinc-900"'
source = replace_once(source, tools_class_old, tools_class_new, "conversation tools menu class")

# 5) Voice button on both the always-visible smart message search and the full Smart Search palette.
inline_shell_old = 'className="mt-2 flex items-center gap-2 rounded-xl border border-zinc-100 bg-zinc-50 px-3 py-1.5 shadow-sm transition focus-within:border-amber-300 focus-within:bg-white dark:border-white/10 dark:bg-white/5 dark:focus-within:bg-zinc-900"'
inline_shell_new = 'className="tcs-v16-inline-search-shell mt-2 flex items-center gap-2 rounded-xl border border-zinc-100 bg-zinc-50 px-3 py-1.5 shadow-sm transition focus-within:border-amber-300 focus-within:bg-white dark:border-white/10 dark:bg-white/5 dark:focus-within:bg-zinc-900"'
source = replace_once(source, inline_shell_old, inline_shell_new, "inline search shell")

inline_input = '<input value={search} onChange={(event) => setSearch(event.target.value)} placeholder={lang === "en" ? "Smart search messages, people or files..." : "بحث ذكي في الرسائل والأشخاص والملفات..."} className="tcs-v15-inline-smart-search flex-1 bg-transparent text-sm text-zinc-700 outline-none placeholder:text-zinc-400 dark:text-zinc-200" />'
inline_voice = inline_input + '<button type="button" onClick={() => startVoiceSearch("inline")} disabled={!voiceSearchSupported} className={`tcs-v16-voice-button ${voiceSearchListening === "inline" ? "is-listening" : ""}`} aria-pressed={voiceSearchListening === "inline"} title={!voiceSearchSupported ? (lang === "en" ? "Voice search is unavailable in this browser" : "البحث الصوتي غير متاح في هذا المتصفح") : voiceSearchListening === "inline" ? (lang === "en" ? "Stop listening" : "إيقاف الاستماع") : (lang === "en" ? "Voice search" : "بحث صوتي")}>{voiceSearchListening === "inline" ? <MicOff size={15} /> : <Mic size={15} />}</button>'
source = replace_once(source, inline_input, inline_voice, "inline voice search button")

smart_input = '<input value={workspaceSearchQuery} onChange={(event) => setWorkspaceSearchQuery(event.target.value)} autoFocus placeholder={lang === "en" ? "Try: PDF from Ahmed, design task, website decision..." : "مثال: PDF من أحمد، مهمة تصميم، قرار الموقع..."} className="tcs-v15-smart-search-input mt-4 w-full rounded-2xl border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm outline-none focus:border-amber-400 dark:border-white/10 dark:bg-white/5 dark:text-white" />'
smart_voice = '<div className="tcs-v16-voice-search-wrap mt-4"><input value={workspaceSearchQuery} onChange={(event) => setWorkspaceSearchQuery(event.target.value)} autoFocus placeholder={lang === "en" ? "Try: PDF from Ahmed, design task, website decision..." : "مثال: PDF من أحمد، مهمة تصميم، قرار الموقع..."} className="tcs-v15-smart-search-input w-full rounded-2xl border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm outline-none focus:border-amber-400 dark:border-white/10 dark:bg-white/5 dark:text-white" /><button type="button" onClick={() => startVoiceSearch("workspace")} disabled={!voiceSearchSupported} className={`tcs-v16-voice-button ${voiceSearchListening === "workspace" ? "is-listening" : ""}`} aria-pressed={voiceSearchListening === "workspace"} title={!voiceSearchSupported ? (lang === "en" ? "Voice search is unavailable in this browser" : "البحث الصوتي غير متاح في هذا المتصفح") : voiceSearchListening === "workspace" ? (lang === "en" ? "Stop listening" : "إيقاف الاستماع") : (lang === "en" ? "Voice search" : "بحث صوتي")}>{voiceSearchListening === "workspace" ? <MicOff size={17} /> : <Mic size={17} />}</button></div>'
source = replace_once(source, smart_input, smart_voice, "smart palette voice search button")

for token in (
    "TcsPremiumSelect", "tcs-v16-premium-select-menu", "startVoiceSearch", "webkitSpeechRecognition",
    'recognition.lang = lang === "en" ? "en-US" : "ar-EG"', "tcs-v16-voice-button", "tcs-v16-tools-menu",
    "normalizeSmartSearchText", "smartSearchScore", "uploadChatFile", "sendMessage",
):
    if token not in source:
        fail(f"post-transform required token missing: {token}")

try:
    CHAT.write_text(source, encoding="utf-8")
    STYLE.write_text(original_style.rstrip() + "\n\n" + override_css.strip() + "\n", encoding="utf-8")
except Exception as exc:
    CHAT.write_text(original_chat, encoding="utf-8")
    STYLE.write_text(original_style, encoding="utf-8")
    fail(f"V1.6 source/style transformation failed and rolled back: {exc}")

build = subprocess.run(["npm", "run", "build"], cwd=FRONTEND, text=True, capture_output=True)
if build.returncode != 0:
    print(build.stdout[-8000:])
    print(build.stderr[-8000:])
    CHAT.write_text(original_chat, encoding="utf-8")
    STYLE.write_text(original_style, encoding="utf-8")
    fail("frontend build failed; ChatPanel/style rolled back")

if not DIST.exists():
    CHAT.write_text(original_chat, encoding="utf-8")
    STYLE.write_text(original_style, encoding="utf-8")
    fail("frontend dist missing after successful build")

for marker in (
    V16_RUNTIME.encode(), b"tcs-v16-premium-select-menu", b"tcs-v16-voice-button",
    b"webkitSpeechRecognition", b"tcs-v16-tools-menu", b"tcs-v15-smart-search-dialog",
    b"data-tcs-ramzy-collision-sync", b"tcs-desktop-window",
):
    if tree_count(DIST, marker) < 1:
        CHAT.write_text(original_chat, encoding="utf-8")
        STYLE.write_text(original_style, encoding="utf-8")
        fail(f"built output missing runtime marker/token: {marker.decode()}")

if sha256(LAUNCHER) != EXPECTED_LAUNCHER_SHA256:
    CHAT.write_text(original_chat, encoding="utf-8")
    STYLE.write_text(original_style, encoding="utf-8")
    fail("TCS launcher changed unexpectedly")
if sha256(WINDOW) != EXPECTED_WINDOW_SHA256:
    CHAT.write_text(original_chat, encoding="utf-8")
    STYLE.write_text(original_style, encoding="utf-8")
    fail("TCS desktop window source changed unexpectedly")

stamp = int(time.time())
candidate = LIVE_PARENT / f"build.tcs-v1-6-premium-menus-voice-candidate-{stamp}"
backup = LIVE_PARENT / f"build.tcs-v1-6-premium-menus-voice-backup-{stamp}"
failed_live = LIVE_PARENT / f"build.tcs-v1-6-premium-menus-voice-failed-{stamp}"

try:
    if candidate.exists() or backup.exists() or failed_live.exists():
        raise RuntimeError("timestamped deployment path already exists")
    shutil.copytree(DIST, candidate)
    if not LIVE.exists():
        raise RuntimeError(f"live build missing: {LIVE}")
    LIVE.rename(backup)
    candidate.rename(LIVE)
except Exception as exc:
    try:
        if LIVE.exists() and backup.exists():
            LIVE.rename(failed_live)
            backup.rename(LIVE)
        elif backup.exists() and not LIVE.exists():
            backup.rename(LIVE)
    finally:
        CHAT.write_text(original_chat, encoding="utf-8")
        STYLE.write_text(original_style, encoding="utf-8")
    fail(f"live deployment failed and rollback attempted: {exc}")

print("PASS/FAIL=PASS")
print("BUILD_RESULT=PASS")
print("LIVE_DEPLOY=PASS")
print("TCS_V1_5_RUNTIME=YES")
print("TCS_V1_6_RUNTIME=YES")
print("TCS_NATIVE_SELECTS_REMAINING=0")
print("TCS_MEMBER_PICKER=PREMIUM_SEARCHABLE")
print("TCS_CHANNEL_TYPE_MENU=PREMIUM")
print("TCS_TASK_MENUS=PREMIUM")
print("TCS_ADVANCED_SEARCH_USER_MENU=PREMIUM_SEARCHABLE")
print("TCS_CHAT_STATUS=PREMIUM_SEGMENTED")
print("TCS_CONVERSATION_TOOLS=EXECUTIVE_REFINED")
print("TCS_CONVERSATION_TOOLS_EDGE_OVERFLOW=TARGETED_FIX")
print("TCS_VOICE_SEARCH=YES")
print("TCS_VOICE_SEARCH_ENGINE=BROWSER_WEB_SPEECH_API")
print("TCS_VOICE_SEARCH_LANG_AR=ar-EG")
print("TCS_VOICE_SEARCH_LANG_EN=en-US")
print("TCS_VOICE_SEARCH_INLINE=YES")
print("TCS_VOICE_SEARCH_SMART_PALETTE=YES")
print("TCS_VOICE_SEARCH_UNSUPPORTED_BROWSER=GRACEFUL_DISABLED")
print("TCS_SMART_SEARCH_RELEVANCE_PRESERVED=YES")
print("TCS_EXISTING_ADVANCED_SEARCH=PRESERVED=YES")
print("TCS_CHAT_MESSAGING_LOGIC_CHANGED=NO")
print("TCS_FILE_UPLOAD_IMPLEMENTATION_CHANGED=NO")
print("TCS_LAUNCHER_CHANGED=NO")
print("TCS_WINDOW_BEHAVIOR_CHANGED=NO")
print("TCS_RAMZY_COLLISION_SYNC_PRESERVED=YES")
print("RAMZY_CHANGED=NO")
print("API_CHANGED=NO")
print("DATABASE_CHANGED=NO")
print(f"CHAT_PANEL_SHA256={sha256(CHAT)}")
print(f"TCS_STYLE_SHA256={sha256(STYLE)}")
print(f"TCS_LAUNCHER_SHA256={sha256(LAUNCHER)}")
print(f"TCS_WINDOW_SHA256={sha256(WINDOW)}")
print(f"LIVE_BACKUP={backup}")
print("STATUS=READY")
