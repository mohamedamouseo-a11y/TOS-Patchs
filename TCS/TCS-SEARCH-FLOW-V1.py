#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import shutil, sys

PATCH = "TCS-SEARCH-FLOW-V1"
ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS").resolve()
CHAT = ROOT / "frontend/src/components/ChatPanel.jsx"
if not CHAT.exists():
    raise SystemExit(f"{PATCH}: missing {CHAT}")

src = CHAT.read_text(encoding="utf-8")
backup = Path("/tmp") / f"{PATCH}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
backup.mkdir(parents=True, exist_ok=True)
shutil.copy2(CHAT, backup / "ChatPanel.jsx")

# State
anchor = '  const [workspaceSearchActiveIndex, setWorkspaceSearchActiveIndex] = useState(0);'
if "workspaceServerResults" not in src:
    if anchor not in src:
        raise SystemExit(f"{PATCH}: state anchor missing")
    src = src.replace(anchor, anchor + '''
  const [workspaceServerResults, setWorkspaceServerResults] = useState([]);
  const [workspaceServerLoading, setWorkspaceServerLoading] = useState(false);
  const [pendingSearchMessageId, setPendingSearchMessageId] = useState("");''', 1)

# Merge local smart results with server full-history messages.
activity_anchor = '  const activityTimeline = useMemo(() => {'
if "workspaceSearchDisplayResults" not in src:
    if activity_anchor not in src:
        raise SystemExit(f"{PATCH}: activity anchor missing")
    block = '''  const workspaceSearchDisplayResults = useMemo(() => {
    const serverItems = (workspaceServerResults || []).map((message) => ({
      id: message.id,
      kind: "message",
      label: truncateMessagePreview(message.body || (lang === "en" ? "Message without text" : "رسالة بدون نص"), 96),
      description: message.user?.name || (lang === "en" ? "Message" : "رسالة"),
      targetId: message.id,
      createdAt: message.createdAt,
      serverResult: true,
    }));
    const source = (workspaceSearchType === "smart" || workspaceSearchType === "messages")
      ? [...workspaceSearchResults, ...serverItems]
      : workspaceSearchResults;
    const seen = new Set();
    return source.filter((item) => {
      const key = item.targetId || (String(item.kind) + "-" + String(item.id));
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    }).slice(0, 40);
  }, [workspaceSearchResults, workspaceServerResults, workspaceSearchType, lang]);

'''
    src = src.replace(activity_anchor, block + activity_anchor, 1)

# Debounced server search scoped to active chat.
effect_anchor = '''  useEffect(() => {
    setWorkspaceSearchActiveIndex(0);
  }, [workspaceSearchQuery, workspaceSearchType, activeChannelId, activeConversationId]);'''
if "TCS_SEARCH_FLOW_V1" not in src:
    if effect_anchor not in src:
        raise SystemExit(f"{PATCH}: reset effect anchor missing")
    server_effect = effect_anchor + '''

  // TCS_SEARCH_FLOW_V1
  useEffect(() => {
    const q = workspaceSearchQuery.trim();
    const hasScope = isDirectMode ? Boolean(activeConversationId) : Boolean(projectId);
    if (!workspaceSearchOpen || q.length < 2 || !hasScope) {
      setWorkspaceServerResults([]);
      setWorkspaceServerLoading(false);
      return undefined;
    }
    let cancelled = false;
    const timer = window.setTimeout(async () => {
      try {
        setWorkspaceServerLoading(true);
        const results = await api.chat.search({
          q,
          ...(isDirectMode ? { conversationId: activeConversationId } : { projectId, channelId: activeChannelId }),
        });
        if (!cancelled) setWorkspaceServerResults(Array.isArray(results) ? results : (results?.messages || results?.results || []));
      } catch {
        if (!cancelled) setWorkspaceServerResults([]);
      } finally {
        if (!cancelled) setWorkspaceServerLoading(false);
      }
    }, 280);
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [workspaceSearchOpen, workspaceSearchQuery, isDirectMode, activeConversationId, projectId, activeChannelId]);'''
    src = src.replace(effect_anchor, server_effect, 1)

# Pending jump after existing loader fetches an old matching message.
pending_anchor = '''  useEffect(() => {
    if (!pendingNotificationMessageId || loading) return;
    const exists = messages.some((message) => message.id === pendingNotificationMessageId);
    if (!exists) return;
    window.setTimeout(() => {
      scrollToMessage(pendingNotificationMessageId);
      setPendingNotificationMessageId("");
    }, 120);
  }, [pendingNotificationMessageId, loading, messages.length, activeChannelId, activeConversationId]);'''
if "pendingSearchMessageId || loading" not in src:
    if pending_anchor not in src:
        raise SystemExit(f"{PATCH}: pending jump anchor missing")
    src = src.replace(pending_anchor, pending_anchor + '''

  useEffect(() => {
    if (!pendingSearchMessageId || loading) return;
    if (!messages.some((message) => message.id === pendingSearchMessageId)) return;
    window.setTimeout(() => {
      jumpToMessage(pendingSearchMessageId);
      setPendingSearchMessageId("");
    }, 120);
  }, [pendingSearchMessageId, loading, messages.length, activeChannelId, activeConversationId]);''', 1)

# Replace jump helper with robust current-page/full-history opener + keyboard nav.
jump_anchor = '''  function jumpWorkspaceSearchResult(index = workspaceSearchActiveIndex) {
    if (!workspaceSearchResults.length) return;
    const safeIndex = Math.max(0, Math.min(index, workspaceSearchResults.length - 1));
    setWorkspaceSearchActiveIndex(safeIndex);
    const item = workspaceSearchResults[safeIndex];
    if (item?.targetId) jumpToMessage(item.targetId);
  }'''
if "function openWorkspaceSearchResult(" not in src:
    if jump_anchor not in src:
        raise SystemExit(f"{PATCH}: jump helper anchor missing")
    jump_new = '''  function openWorkspaceSearchResult(item) {
    if (!item?.targetId) return;
    setWorkspaceSearchOpen(false);
    setAdvancedSearchOpen(false);
    setMessageFilter("all");
    if (messageRefs.current.get(item.targetId)) {
      jumpToMessage(item.targetId);
      return;
    }
    setPendingSearchMessageId(item.targetId);
    setSearch(workspaceSearchQuery.trim() || item.label || "");
  }

  function jumpWorkspaceSearchResult(index = workspaceSearchActiveIndex) {
    if (!workspaceSearchDisplayResults.length) return;
    const safeIndex = Math.max(0, Math.min(index, workspaceSearchDisplayResults.length - 1));
    setWorkspaceSearchActiveIndex(safeIndex);
    openWorkspaceSearchResult(workspaceSearchDisplayResults[safeIndex]);
  }

  function handleWorkspaceSearchKeyDown(event) {
    if (event.key === "Escape") {
      setWorkspaceSearchOpen(false);
      return;
    }
    if (!workspaceSearchDisplayResults.length) return;
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setWorkspaceSearchActiveIndex((index) => Math.min(index + 1, workspaceSearchDisplayResults.length - 1));
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setWorkspaceSearchActiveIndex((index) => Math.max(index - 1, 0));
    } else if (event.key === "Enter") {
      event.preventDefault();
      jumpWorkspaceSearchResult();
    }
  }'''
    src = src.replace(jump_anchor, jump_new, 1)

# Marker + keyboard handler.
needle = 'value={workspaceSearchQuery} onChange={(event) => setWorkspaceSearchQuery(event.target.value)} autoFocus'
if 'data-tcs-search-flow="v1"' not in src:
    if needle not in src:
        raise SystemExit(f"{PATCH}: search input anchor missing")
    src = src.replace(needle, 'data-tcs-search-flow="v1" value={workspaceSearchQuery} onChange={(event) => setWorkspaceSearchQuery(event.target.value)} onKeyDown={handleWorkspaceSearchKeyDown} autoFocus', 1)

# Modal uses merged local + server results.
modal_start = src.find('{workspaceSearchOpen && (')
modal_end = src.find('{taskDraftMessage && (', modal_start)
if modal_start < 0 or modal_end < 0:
    raise SystemExit(f"{PATCH}: workspace modal bounds missing")
modal = src[modal_start:modal_end]
modal = modal.replace('workspaceSearchResults.length', 'workspaceSearchDisplayResults.length')
modal = modal.replace('workspaceSearchResults.map', 'workspaceSearchDisplayResults.map')
modal = modal.replace('item.targetId && jumpToMessage(item.targetId)', 'openWorkspaceSearchResult(item)')
src = src[:modal_start] + modal + src[modal_end:]

# Advanced server search old-result jump uses the same robust opener.
src = src.replace(
    'onClick={() => scrollToMessage(message.id)} className="block w-full rounded-2xl',
    'onClick={() => openWorkspaceSearchResult({ id: message.id, targetId: message.id, label: message.body || advancedSearch.q, kind: "message" })} className="block w-full rounded-2xl',
    1,
)

CHAT.write_text(src, encoding="utf-8")
print(f"PATCH={PATCH}")
print("SERVER_HISTORY_SEARCH=YES")
print("UNLOADED_RESULT_JUMP=YES")
print("KEYBOARD_NAV=YES")
print("VOICE_SEARCH=PRESERVED")
print("ADVANCED_SEARCH_JUMP=FIXED")
print("BACKEND_UNCHANGED=YES")
print(f"BACKUP={backup}")
print("NEXT=BUILD_DEPLOY")
