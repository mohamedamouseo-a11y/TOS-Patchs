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
OVERRIDE = PATCH_DIR / "tcsFlagshipV1_5SmartSearchExecutivePolish.css"
FRONTEND = ROOT / "frontend"
DIST = FRONTEND / "dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

EXPECTED_CHAT_GIT_BLOB_SHA = "839eb37b5af54ab0819cb852442f895eaeed73f8"
EXPECTED_LAUNCHER_SHA256 = "2dfd109fbae96f97829233b95a266797b615b84a8facc8831d8c4efec023522d"
EXPECTED_WINDOW_SHA256 = "5aa5f8c047baa12f29cae33585e1f7be493c5bfbde43a706f4537dbe599dad70"
EXPECTED_STYLE_SHA256 = "0b9cd9289a07723a06c5f3778945cce42d3b528d033d39542a908e855a35cf8f"
V14_RUNTIME = "--tos-tcs-flagship-v1-4-luxe-depth-runtime"
V15_RUNTIME = "--tos-tcs-flagship-v1-5-smart-search-runtime"
V12_COLLISION_ATTR = 'data-tcs-ramzy-collision-sync="v1.2"'

print("RUNNING=TOS_GLOBAL_TCS_FLAGSHIP_V1_5_SMART_SEARCH_EXECUTIVE_POLISH")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


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
    print("TCS_V1_5_RUNTIME=NO")
    sys.exit(1)


if ROOT.resolve() == Path("/"):
    fail("unsafe ROOT")
for path in (CHAT, LAUNCHER, WINDOW, STYLE, OVERRIDE, FRONTEND, LIVE_PARENT):
    if not path.exists():
        fail(f"required path missing: {path}")

if git_blob_sha(CHAT) != EXPECTED_CHAT_GIT_BLOB_SHA:
    fail(f"ChatPanel.jsx baseline mismatch: {git_blob_sha(CHAT)}")
if sha256(LAUNCHER) != EXPECTED_LAUNCHER_SHA256:
    fail(f"TcsFloatingLauncher.jsx baseline mismatch: {sha256(LAUNCHER)}")
if sha256(WINDOW) != EXPECTED_WINDOW_SHA256:
    fail(f"TcsDesktopWindow.jsx baseline mismatch: {sha256(WINDOW)}")
if sha256(STYLE) != EXPECTED_STYLE_SHA256:
    fail(f"tcsFlagshipV1.css V1.4 baseline mismatch: {sha256(STYLE)}")

original_chat = CHAT.read_text(encoding="utf-8")
original_style = STYLE.read_text(encoding="utf-8")
override_css = OVERRIDE.read_text(encoding="utf-8")
launcher_source = LAUNCHER.read_text(encoding="utf-8")

if V14_RUNTIME not in original_style:
    fail("TCS V1.4 runtime marker missing")
if V15_RUNTIME in original_style or "normalizeSmartSearchText" in original_chat:
    fail("TCS V1.5 smart search already applied")
if V15_RUNTIME not in override_css:
    fail("V1.5 runtime marker missing from override")
if V12_COLLISION_ATTR not in launcher_source:
    fail("TCS V1.2 Ramzy collision sync marker missing")

source = original_chat

# 1) Smart search becomes the default unified mode while preserving all existing category tabs.
search_types_anchor = 'const CHAT_SEARCH_TYPES = [\n'
if source.count(search_types_anchor) != 1:
    fail(f"CHAT_SEARCH_TYPES anchor mismatch: {source.count(search_types_anchor)}")
source = source.replace(search_types_anchor, search_types_anchor + '  { value: "smart", label: "ذكي", labelEn: "Smart" },\n', 1)

state_anchor = 'const [workspaceSearchType, setWorkspaceSearchType] = useState("messages");'
if source.count(state_anchor) != 1:
    fail(f"workspace search state anchor mismatch: {source.count(state_anchor)}")
source = source.replace(state_anchor, 'const [workspaceSearchType, setWorkspaceSearchType] = useState("smart");', 1)

# 2) Add bilingual normalization, intent detection and fuzzy relevance helpers.
lower_anchor = 'function lowerText(value = "") { return String(value || "").toLowerCase(); }\n'
if source.count(lower_anchor) != 1:
    fail(f"lowerText anchor mismatch: {source.count(lower_anchor)}")
smart_helpers = r'''function normalizeSmartSearchText(value = "") {
  return String(value || "")
    .normalize("NFKD")
    .replace(/[\u064B-\u065F\u0670\u06D6-\u06ED]/g, "")
    .replace(/\u0640/g, "")
    .replace(/[أإآٱ]/g, "ا")
    .replace(/ى/g, "ي")
    .replace(/ة/g, "ه")
    .replace(/ؤ/g, "و")
    .replace(/ئ/g, "ي")
    .toLowerCase()
    .replace(/[^a-z0-9\u0600-\u06ff@._-]+/g, " ")
    .trim()
    .replace(/\s+/g, " ");
}
const SMART_SEARCH_STOP_WORDS = new Set(["من", "في", "على", "عن", "مع", "الى", "الي", "و", "the", "a", "an", "from", "in", "on", "by", "with", "of", "for"]);
const SMART_SEARCH_INTENT_TERMS = {
  file: ["ملف", "ملفات", "file", "files", "pdf", "صوره", "صور", "image", "images", "document", "doc", "video", "فيديو"],
  mention: ["منشن", "اشاره", "اشارات", "mention", "mentions", "@"],
  pin: ["مثبت", "مثبته", "قرار", "قرارات", "pin", "pinned", "decision", "decisions"],
  task: ["مهمه", "مهام", "task", "tasks", "todo", "followup", "follow-up"],
  message: ["رساله", "رسائل", "message", "messages", "chat", "محادثه", "محادثات"],
};
function smartSearchTokens(value = "") {
  return normalizeSmartSearchText(value).split(" ").filter((token) => token && !SMART_SEARCH_STOP_WORDS.has(token));
}
function smartSearchBigrams(value = "") {
  const text = normalizeSmartSearchText(value).replace(/\s+/g, "");
  if (text.length < 2) return text ? [text] : [];
  return Array.from({ length: text.length - 1 }, (_, index) => text.slice(index, index + 2));
}
function smartSearchSimilarity(a = "", b = "") {
  const left = smartSearchBigrams(a);
  const right = smartSearchBigrams(b);
  if (!left.length || !right.length) return 0;
  const pool = [...right];
  let hits = 0;
  left.forEach((pair) => {
    const index = pool.indexOf(pair);
    if (index >= 0) { hits += 1; pool.splice(index, 1); }
  });
  return (2 * hits) / (left.length + right.length);
}
function smartSearchIntentKinds(query = "") {
  const normalized = normalizeSmartSearchText(query);
  const tokens = new Set(smartSearchTokens(query));
  return Object.entries(SMART_SEARCH_INTENT_TERMS).filter(([, terms]) => terms.some((term) => {
    const normalizedTerm = normalizeSmartSearchText(term);
    return tokens.has(normalizedTerm) || normalized.includes(normalizedTerm);
  })).map(([kind]) => kind);
}
function smartSearchScore(query = "", label = "", description = "", kind = "message", searchable = "") {
  const normalizedQuery = normalizeSmartSearchText(query);
  if (!normalizedQuery) return 1;
  const normalizedLabel = normalizeSmartSearchText(label);
  const haystack = normalizeSmartSearchText(`${label} ${description} ${searchable}`);
  const queryTokens = smartSearchTokens(normalizedQuery);
  const hayTokens = smartSearchTokens(haystack);
  const intents = smartSearchIntentKinds(normalizedQuery);
  let score = 0;
  if (normalizedLabel === normalizedQuery) score += 220;
  if (normalizedLabel.startsWith(normalizedQuery)) score += 145;
  if (haystack.includes(normalizedQuery)) score += 105;
  let matchedTokens = 0;
  queryTokens.forEach((token) => {
    if (normalizedLabel.split(" ").includes(token)) { score += 36; matchedTokens += 1; return; }
    if (hayTokens.includes(token)) { score += 25; matchedTokens += 1; return; }
    if (hayTokens.some((candidate) => candidate.startsWith(token) || token.startsWith(candidate))) { score += 17; matchedTokens += 1; return; }
    if (token.length >= 3) {
      const fuzzy = hayTokens.reduce((best, candidate) => Math.max(best, smartSearchSimilarity(token, candidate)), 0);
      if (fuzzy >= .72) { score += Math.round(10 + fuzzy * 13); matchedTokens += 1; }
    }
  });
  if (queryTokens.length && matchedTokens === queryTokens.length) score += 34;
  else if (matchedTokens > 1) score += 12;
  if (intents.includes(kind)) score += 38;
  return score;
}
function smartSearchKindLabel(kind = "message", lang = "ar") {
  const labels = lang === "en"
    ? { message: "Message", file: "File", mention: "Mention", pin: "Pinned", task: "Task" }
    : { message: "رسالة", file: "ملف", mention: "منشن", pin: "مثبت", task: "مهمة" };
  return labels[kind] || labels.message;
}
'''
source = source.replace(lower_anchor, lower_anchor + smart_helpers, 1)

# 3) Existing inline message search becomes functional and typo-tolerant without reordering the timeline.
old_filtered = '''  const filteredMessages = useMemo(() => {\n    const context = { readAt: effectiveLastReadAt, currentUserId: user?.id || "", members: currentChatMembers, savedMessageIds };\n    return messages.filter((message) => matchesChatMessageFilter(message, messageFilter, context));\n  }, [messages, messageFilter, effectiveLastReadAt, user?.id, currentChatMembers, savedMessageIds]);'''
new_filtered = '''  const filteredMessages = useMemo(() => {\n    const context = { readAt: effectiveLastReadAt, currentUserId: user?.id || "", members: currentChatMembers, savedMessageIds };\n    const base = messages.filter((message) => matchesChatMessageFilter(message, messageFilter, context));\n    if (!normalizeSmartSearchText(search)) return base;\n    return base.filter((message) => {\n      const filesText = (message.files || []).map((file) => `${file.name || ""} ${file.mimeType || ""}`).join(" ");\n      const metadataText = `${message.user?.name || ""} ${message.decision?.type || ""} ${message.decision?.tag || ""} ${message.taskDraft?.title || ""} ${filesText}`;\n      return smartSearchScore(search, message.body || "", metadataText, "message", metadataText) >= 18;\n    });\n  }, [messages, messageFilter, effectiveLastReadAt, user?.id, currentChatMembers, savedMessageIds, search]);'''
if source.count(old_filtered) != 1:
    fail(f"filteredMessages anchor mismatch: {source.count(old_filtered)}")
source = source.replace(old_filtered, new_filtered, 1)

# 4) Replace simple substring Workspace search with unified ranked Smart Search.
old_workspace = '''  const workspaceSearchResults = useMemo(() => {\n    const query = lowerText(workspaceSearchQuery);\n    if (!query) return [];\n    const source = workspaceSearchType === "files" ? workspaceFiles.map((file) => ({ id: file.id || file.name, kind: "file", label: file.name || "ملف", description: fileTypeLabel(chatFileType(file)), targetId: file.messageId })) : (workspaceSearchType === "mentions" ? mentionInboxMessages : workspaceSearchType === "pins" ? decisionLogMessages : workspaceSearchType === "tasks" ? localTaskMessages : chatMetrics.visible).map((message) => ({ id: message.id, kind: "message", label: truncateMessagePreview(message.body || "رسالة بدون نص", 90), description: message.user?.name || "رسالة", targetId: message.id }));\n    return source.filter((item) => lowerText(`${item.label} ${item.description}`).includes(query)).slice(0, 18);\n  }, [workspaceSearchQuery, workspaceSearchType, workspaceFiles, mentionInboxMessages, decisionLogMessages, localTaskMessages, chatMetrics.visible]);'''
new_workspace = '''  const workspaceSearchResults = useMemo(() => {\n    const messageItems = chatMetrics.visible.map((message) => ({\n      id: message.id, kind: "message", label: truncateMessagePreview(message.body || (lang === "en" ? "Message without text" : "رسالة بدون نص"), 96),\n      description: message.user?.name || (lang === "en" ? "Message" : "رسالة"), targetId: message.id, createdAt: message.createdAt,\n      searchable: `${message.body || ""} ${message.user?.name || ""} ${(message.files || []).map((file) => `${file.name || ""} ${file.mimeType || ""}`).join(" ")}`,\n    }));\n    const fileItems = workspaceFiles.map((file) => ({\n      id: file.id || file.name, kind: "file", label: file.name || (lang === "en" ? "File" : "ملف"),\n      description: `${fileTypeLabel(chatFileType(file), lang)}${file.messageUser?.name ? ` · ${file.messageUser.name}` : ""}`, targetId: file.messageId, createdAt: file.createdAt,\n      searchable: `${file.name || ""} ${file.mimeType || ""} ${file.messageUser?.name || ""}`,\n    }));\n    const mentionItems = mentionInboxMessages.map((message) => ({\n      id: message.id, kind: "mention", label: truncateMessagePreview(message.body || "@", 96), description: message.user?.name || "Mention",\n      targetId: message.id, createdAt: message.createdAt, searchable: `${message.body || ""} ${message.user?.name || ""}`,\n    }));\n    const pinItems = decisionLogMessages.map((message) => ({\n      id: message.id, kind: "pin", label: truncateMessagePreview(message.body || message.decision?.type || "Decision", 96),\n      description: `${message.decision?.type || message.decision?.tag || (message.isPinned ? "Pinned" : "Decision")}${message.user?.name ? ` · ${message.user.name}` : ""}`,\n      targetId: message.id, createdAt: message.createdAt, searchable: `${message.body || ""} ${message.user?.name || ""} ${message.decision?.type || ""} ${message.decision?.tag || ""}`,\n    }));\n    const taskItems = localTaskMessages.map((message) => ({\n      id: message.id, kind: "task", label: message.taskDraft?.title || truncateMessagePreview(message.body || "Task", 96),\n      description: `${message.linkedTask?.priority || message.taskDraft?.priority || "Task"}${message.user?.name ? ` · ${message.user.name}` : ""}`,\n      targetId: message.id, createdAt: message.createdAt, searchable: `${message.body || ""} ${message.user?.name || ""} ${message.taskDraft?.title || ""}`,\n    }));\n    const byType = { messages: messageItems, files: fileItems, mentions: mentionItems, pins: pinItems, tasks: taskItems };\n    const sourceItems = workspaceSearchType === "smart" ? [...fileItems, ...taskItems, ...pinItems, ...mentionItems, ...messageItems] : (byType[workspaceSearchType] || messageItems);\n    const normalizedQuery = normalizeSmartSearchText(workspaceSearchQuery);\n    const ranked = sourceItems.map((item) => ({\n      ...item,\n      score: normalizedQuery ? smartSearchScore(workspaceSearchQuery, item.label, item.description, item.kind, item.searchable) : 1,\n      matchHint: normalizedQuery ? (lang === "en" ? "Best relevance" : "الأكثر صلة") : (lang === "en" ? "Recent" : "الأحدث"),\n    })).filter((item) => !normalizedQuery || item.score >= 18);\n    ranked.sort((a, b) => b.score - a.score || new Date(b.createdAt || 0).getTime() - new Date(a.createdAt || 0).getTime());\n    if (workspaceSearchType !== "smart") return ranked.slice(0, 24);\n    const deduped = [];\n    const seen = new Set();\n    ranked.forEach((item) => {\n      const key = item.targetId || `${item.kind}-${item.id}`;\n      if (!seen.has(key)) { seen.add(key); deduped.push(item); }\n    });\n    return deduped.slice(0, 24);\n  }, [workspaceSearchQuery, workspaceSearchType, workspaceFiles, mentionInboxMessages, decisionLogMessages, localTaskMessages, chatMetrics.visible, lang]);'''
if source.count(old_workspace) != 1:
    fail(f"workspaceSearchResults anchor mismatch: {source.count(old_workspace)}")
source = source.replace(old_workspace, new_workspace, 1)

# Reset result cursor whenever the smart query/type changes.
active_index_anchor = 'const [workspaceSearchActiveIndex, setWorkspaceSearchActiveIndex] = useState(0);'
if source.count(active_index_anchor) != 1:
    fail(f"workspace active-index anchor mismatch: {source.count(active_index_anchor)}")
source = source.replace(active_index_anchor, active_index_anchor + '\n  useEffect(() => { setWorkspaceSearchActiveIndex(0); }, [workspaceSearchQuery, workspaceSearchType]);', 1)

# Every Workspace-search entry point opens the unified Smart tab.
open_anchor = 'onClick={() => setWorkspaceSearchOpen(true)}'
open_count = source.count(open_anchor)
if open_count < 1:
    fail("workspace search open anchor missing")
source = source.replace(open_anchor, 'onClick={() => { setWorkspaceSearchType("smart"); setWorkspaceSearchOpen(true); }}')

# Inline search now communicates its smarter behavior.
old_inline = 'input value={search} onChange={(event) => setSearch(event.target.value)} placeholder={lang === "en" ? "Search messages..." : "بحث داخل الرسائل..."} className="flex-1 bg-transparent text-sm text-zinc-700 outline-none placeholder:text-zinc-400 dark:text-zinc-200"'
new_inline = 'input value={search} onChange={(event) => setSearch(event.target.value)} placeholder={lang === "en" ? "Smart search messages, people or files..." : "بحث ذكي في الرسائل والأشخاص والملفات..."} className="tcs-v15-inline-smart-search flex-1 bg-transparent text-sm text-zinc-700 outline-none placeholder:text-zinc-400 dark:text-zinc-200"'
if source.count(old_inline) != 1:
    fail(f"inline search input anchor mismatch: {source.count(old_inline)}")
source = source.replace(old_inline, new_inline, 1)

# Premium Smart Search command palette classes/copy.
replacements = [
    ('className="w-full max-w-2xl rounded-[28px] border border-zinc-200 bg-white p-4 shadow-2xl dark:border-white/10 dark:bg-zinc-950"', 'className="tcs-v15-smart-search-dialog w-full max-w-2xl rounded-[28px] border border-zinc-200 bg-white p-5 shadow-2xl dark:border-white/10 dark:bg-zinc-950"'),
    ('<div className="text-base font-black text-zinc-950 dark:text-white">بحث Workspace</div><div className="text-xs text-zinc-500 dark:text-zinc-400">رسائل، ملفات، منشن، مثبت ومهام من البيانات المتاحة.</div>', '<div className="text-base font-black text-zinc-950 dark:text-white">{lang === "en" ? "TCS Smart Search" : "بحث TCS الذكي"}</div><div className="text-xs text-zinc-500 dark:text-zinc-400">{lang === "en" ? "Understands names, files, tasks, decisions, mentions and close spellings." : "يفهم الأسماء والملفات والمهام والقرارات والمنشن والتهجئة القريبة."}</div>'),
    ('placeholder="ابحث داخل الشات..." className="mt-4 w-full rounded-2xl border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm outline-none focus:border-amber-400 dark:border-white/10 dark:bg-white/5 dark:text-white"', 'placeholder={lang === "en" ? "Try: PDF from Ahmed, design task, website decision..." : "مثال: PDF من أحمد، مهمة تصميم، قرار الموقع..."} className="tcs-v15-smart-search-input mt-4 w-full rounded-2xl border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm outline-none focus:border-amber-400 dark:border-white/10 dark:bg-white/5 dark:text-white"'),
    ('<div className="mt-3 flex flex-wrap gap-2">{chatSearchTypes.map', '<div className="tcs-v15-smart-search-types mt-3 flex flex-wrap gap-2">{chatSearchTypes.map'),
    ('<div className="mt-3 flex items-center justify-between gap-2 rounded-2xl bg-zinc-50 px-3 py-2 text-xs text-zinc-500 dark:bg-white/5 dark:text-zinc-300">', '<div className="tcs-v15-smart-search-meta mt-3 flex items-center justify-between gap-2 rounded-2xl bg-zinc-50 px-3 py-2 text-xs text-zinc-500 dark:bg-white/5 dark:text-zinc-300">'),
    ('<div className="mt-4 max-h-[50vh] space-y-2 overflow-y-auto">{workspaceSearchResults.length > 0 ?', '<div className="tcs-v15-smart-search-results mt-4 max-h-[50vh] space-y-2 overflow-y-auto">{workspaceSearchResults.length > 0 ?'),
]
for old, new in replacements:
    if source.count(old) != 1:
        fail(f"smart-search visual anchor mismatch for: {old[:60]} count={source.count(old)}")
    source = source.replace(old, new, 1)

old_result_class = 'className={`w-full rounded-2xl border p-3 text-right hover:border-amber-300 dark:border-white/10 ${workspaceSearchActiveIndex === index ? "border-amber-300 bg-amber-50 dark:bg-amber-500/10" : "border-zinc-100 bg-zinc-50 dark:bg-white/5"}`}'
new_result_class = 'className={`tcs-v15-smart-search-result w-full rounded-2xl border p-3 text-right hover:border-amber-300 dark:border-white/10 ${workspaceSearchActiveIndex === index ? "is-active border-amber-300 bg-amber-50 dark:bg-amber-500/10" : "border-zinc-100 bg-zinc-50 dark:bg-white/5"}`}'
if source.count(old_result_class) != 1:
    fail(f"smart result class anchor mismatch: {source.count(old_result_class)}")
source = source.replace(old_result_class, new_result_class, 1)

result_content_anchor = '><div className="text-sm font-black text-zinc-950 dark:text-white">{highlightWorkspaceSearchText(item.label)}</div><div className="mt-1 text-xs text-zinc-500 dark:text-zinc-400">{highlightWorkspaceSearchText(item.description)}</div></button>)'
result_content_new = '><div className="mb-2 flex items-center justify-between gap-2"><span className="tcs-v15-smart-search-kind">{smartSearchKindLabel(item.kind, lang)}</span><span className="tcs-v15-smart-search-hint">{item.matchHint}</span></div><div className="text-sm font-black text-zinc-950 dark:text-white">{highlightWorkspaceSearchText(item.label)}</div><div className="mt-1 text-xs text-zinc-500 dark:text-zinc-400">{highlightWorkspaceSearchText(item.description)}</div></button>)'
if source.count(result_content_anchor) != 1:
    fail(f"smart result content anchor mismatch: {source.count(result_content_anchor)}")
source = source.replace(result_content_anchor, result_content_new, 1)

# Guard transformation: smart search exists; messaging/API semantics remain untouched.
for token in (
    'normalizeSmartSearchText', 'smartSearchScore', '{ value: "smart"', 'tcs-v15-smart-search-dialog',
    'tcs-v15-inline-smart-search', 'runAdvancedSearch', 'api.chat.search', 'sendMessage', 'uploadFiles',
):
    if token not in source:
        fail(f"post-transform required token missing: {token}")

try:
    CHAT.write_text(source, encoding="utf-8")
    STYLE.write_text(original_style.rstrip() + "\n\n" + override_css.strip() + "\n", encoding="utf-8")
except Exception as exc:
    CHAT.write_text(original_chat, encoding="utf-8")
    STYLE.write_text(original_style, encoding="utf-8")
    fail(f"source/style transformation failed and rolled back: {exc}")

build = subprocess.run(["npm", "run", "build"], cwd=FRONTEND, text=True, capture_output=True)
if build.returncode != 0:
    print(build.stdout[-7000:])
    print(build.stderr[-7000:])
    CHAT.write_text(original_chat, encoding="utf-8")
    STYLE.write_text(original_style, encoding="utf-8")
    fail("frontend build failed; ChatPanel and style rolled back")

if not DIST.exists():
    CHAT.write_text(original_chat, encoding="utf-8")
    STYLE.write_text(original_style, encoding="utf-8")
    fail("frontend dist missing after successful build")

for marker in (
    V15_RUNTIME.encode(), b"tcs-v15-smart-search-dialog", b"tcs-v15-inline-smart-search",
    b"TCS Smart Search", b"data-tcs-ramzy-collision-sync", b"tcs-desktop-window",
):
    if tree_count(DIST, marker) < 1:
        CHAT.write_text(original_chat, encoding="utf-8")
        STYLE.write_text(original_style, encoding="utf-8")
        fail(f"built output missing runtime marker/token: {marker.decode()}")

# Strong regression guards for global launchers/window behavior.
if sha256(LAUNCHER) != EXPECTED_LAUNCHER_SHA256:
    CHAT.write_text(original_chat, encoding="utf-8")
    STYLE.write_text(original_style, encoding="utf-8")
    fail("TCS launcher changed unexpectedly")
if sha256(WINDOW) != EXPECTED_WINDOW_SHA256:
    CHAT.write_text(original_chat, encoding="utf-8")
    STYLE.write_text(original_style, encoding="utf-8")
    fail("TCS desktop window source changed unexpectedly")

timestamp = int(time.time())
candidate = LIVE_PARENT / f"build.tcs-v1-5-smart-search-candidate-{timestamp}"
backup = LIVE_PARENT / f"build.tcs-v1-5-smart-search-backup-{timestamp}"
failed_live = LIVE_PARENT / f"build.tcs-v1-5-smart-search-failed-{timestamp}"
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
print("TCS_SMART_SEARCH_DEFAULT=YES")
print("TCS_SMART_SEARCH_UNIFIED=MESSAGES_FILES_MENTIONS_PINS_TASKS")
print("TCS_SMART_SEARCH_ARABIC_NORMALIZATION=YES")
print("TCS_SMART_SEARCH_ENGLISH_NORMALIZATION=YES")
print("TCS_SMART_SEARCH_TYPO_TOLERANCE=YES")
print("TCS_SMART_SEARCH_INTENT_DETECTION=YES")
print("TCS_SMART_SEARCH_RELEVANCE_RANKING=YES")
print("TCS_INLINE_MESSAGE_SEARCH=SMART_FILTERING")
print("TCS_EXISTING_ADVANCED_SEARCH=PRESERVED")
print("TCS_SMART_SEARCH_UI=EXECUTIVE_COMMAND_PALETTE")
print("TCS_LIGHT_VISUAL_POLISH=REFINED")
print("TCS_DARK_VISUAL_POLISH=REFINED")
print("TCS_LAUNCHER_CHANGED=NO")
print("TCS_WINDOW_BEHAVIOR_CHANGED=NO")
print("TCS_CHAT_MESSAGING_LOGIC_CHANGED=NO")
print("TCS_SEARCH_LOGIC_CHANGED=YES")
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
