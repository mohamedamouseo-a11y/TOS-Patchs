#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import shutil, sys

PATCH = "TCS-UNREAD-READ-FLOW-V1"
ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS").resolve()
CHAT = ROOT / "frontend/src/components/ChatPanel.jsx"
HOOK = ROOT / "frontend/src/hooks/useChat.js"

for path in (CHAT, HOOK):
    if not path.exists():
        raise SystemExit(f"{PATCH}: missing {path}")

chat = CHAT.read_text(encoding="utf-8")
hook = HOOK.read_text(encoding="utf-8")
backup_dir = Path("/tmp") / f"{PATCH}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
backup_dir.mkdir(parents=True, exist_ok=True)
shutil.copy2(CHAT, backup_dir / "ChatPanel.jsx")
shutil.copy2(HOOK, backup_dir / "useChat.js")

# ------------------------------------------------------------------
# 1) useChat: DO NOT mark read merely because messages loaded/changed.
#    Read acknowledgement is now controlled by the visible viewport.
# ------------------------------------------------------------------
auto_mark = '''  useEffect(() => {
    if (messages.length) markRead();
  }, [projectId, channelId, conversationId, messages.length]);
'''
if auto_mark in hook:
    hook = hook.replace(
        auto_mark,
        '''  // TCS_UNREAD_READ_FLOW_V1
  // Do not auto-mark on load/message arrival. ChatPanel marks read only
  // after the active message viewport is actually visible at the latest edge.
''',
        1
    )
elif "TCS_UNREAD_READ_FLOW_V1" not in hook:
    raise SystemExit(f"{PATCH}: useChat auto-mark effect not found")

# ------------------------------------------------------------------
# 2) Correct unread semantics when this scope has never been read.
# ------------------------------------------------------------------
old_unread = '''function isUnreadMessage(message = {}, readAt = "", currentUserId = "") {
  if (!message?.createdAt || !readAt || message.deletedAt || message.userId === currentUserId) return false;
  return new Date(message.createdAt) > new Date(readAt);
}'''
new_unread = '''function isUnreadMessage(message = {}, readAt = "", currentUserId = "") {
  if (!message?.createdAt || message.deletedAt || message.userId === currentUserId) return false;
  if (!readAt) return true;
  return new Date(message.createdAt) > new Date(readAt);
}'''
if old_unread in chat:
    chat = chat.replace(old_unread, new_unread, 1)
elif "if (!readAt) return true;" not in chat:
    raise SystemExit(f"{PATCH}: isUnreadMessage anchor not found")

# ------------------------------------------------------------------
# 3) State/refs for durable unread divider + read acknowledgement guard.
# ------------------------------------------------------------------
state_anchor = '  const [localLastReadAt, setLocalLastReadAt] = useState("");'
if "unreadDividerMessageId" not in chat:
    if state_anchor not in chat:
        raise SystemExit(f"{PATCH}: localLastReadAt state anchor not found")
    chat = chat.replace(
        state_anchor,
        state_anchor + '\n  const [unreadDividerMessageId, setUnreadDividerMessageId] = useState("");',
        1
    )

ref_anchor = '  const voiceSearchRecognitionRef = useRef(null);'
if "markReadInFlightRef" not in chat:
    if ref_anchor not in chat:
        raise SystemExit(f"{PATCH}: voiceSearchRecognitionRef anchor not found")
    chat = chat.replace(
        ref_anchor,
        ref_anchor + '''
  const markReadInFlightRef = useRef(false);
  const autoReadTimerRef = useRef(null);
  const unreadDividerScopeRef = useRef("");''',
        1
    )

# ------------------------------------------------------------------
# 4) Snapshot the first unread divider per scope. Keep it visible even
#    after server read acknowledgement until the user changes scope.
# ------------------------------------------------------------------
first_unread_anchor = '''  const firstUnreadMessageId = useMemo(() => messages.find((message) => isUnreadMessage(message, effectiveLastReadAt, user?.id))?.id || "", [messages, effectiveLastReadAt, user?.id]);'''
if "TCS_UNREAD_DIVIDER_SNAPSHOT_V1" not in chat:
    if first_unread_anchor not in chat:
        raise SystemExit(f"{PATCH}: firstUnreadMessageId anchor not found")
    chat = chat.replace(
        first_unread_anchor,
        first_unread_anchor + '''
  // TCS_UNREAD_DIVIDER_SNAPSHOT_V1
  useEffect(() => {
    if (unreadDividerScopeRef.current !== chatScopeStorageKey) {
      unreadDividerScopeRef.current = chatScopeStorageKey;
      setUnreadDividerMessageId(firstUnreadMessageId || "");
      return;
    }
    if (!unreadDividerMessageId && firstUnreadMessageId) {
      setUnreadDividerMessageId(firstUnreadMessageId);
    }
  }, [chatScopeStorageKey, firstUnreadMessageId, unreadDividerMessageId]);''',
        1
    )

# The above effect references chatScopeStorageKey, which is declared a few lines
# later in the current source. Move the effect after chatScopeStorageKey definition
# if necessary by replacing that inserted block in-place.
inserted_block = '''  // TCS_UNREAD_DIVIDER_SNAPSHOT_V1
  useEffect(() => {
    if (unreadDividerScopeRef.current !== chatScopeStorageKey) {
      unreadDividerScopeRef.current = chatScopeStorageKey;
      setUnreadDividerMessageId(firstUnreadMessageId || "");
      return;
    }
    if (!unreadDividerMessageId && firstUnreadMessageId) {
      setUnreadDividerMessageId(firstUnreadMessageId);
    }
  }, [chatScopeStorageKey, firstUnreadMessageId, unreadDividerMessageId]);
'''
if inserted_block in chat:
    chat = chat.replace(inserted_block, "", 1)
    storage_end = '''  }, [user?.id, isDirectMode, activeConversationId, projectId, activeChannelId]);'''
    storage_pos = chat.find(storage_end, chat.find("const chatScopeStorageKey"))
    if storage_pos == -1:
        raise SystemExit(f"{PATCH}: chatScopeStorageKey end anchor not found")
    storage_pos += len(storage_end)
    chat = chat[:storage_pos] + '\n' + inserted_block + chat[storage_pos:]

# ------------------------------------------------------------------
# 5) Selecting a direct conversation must NOT zero unread immediately.
# ------------------------------------------------------------------
old_active_effect = '''    setConversations((prev) => prev.map((conversation) => (
      conversation.id === activeConversationId ? { ...conversation, unreadCount: 0 } : conversation
    )));
    if (isDirectMode) {'''
if old_active_effect in chat:
    chat = chat.replace(old_active_effect, '''    if (isDirectMode) {''', 1)
elif "conversation.id === activeConversationId ? { ...conversation, unreadCount: 0 }" in chat:
    raise SystemExit(f"{PATCH}: direct unread clearing anchor changed unexpectedly")

# ------------------------------------------------------------------
# 6) Active incoming messages increment unread until actually seen.
# ------------------------------------------------------------------
old_socket_count = '''            unreadCount: isOwnMessage || isActive ? 0 : (conversation.unreadCount || 0) + 1,'''
new_socket_count = '''            unreadCount: isOwnMessage ? (conversation.unreadCount || 0) : (conversation.unreadCount || 0) + 1,'''
if old_socket_count in chat:
    chat = chat.replace(old_socket_count, new_socket_count, 1)
elif new_socket_count not in chat:
    raise SystemExit(f"{PATCH}: direct socket unread anchor not found")

# Schedule a visible read for an incoming active message, but only if viewport is actually at latest.
notify_anchor = '''      if (!isOwnMessage && !isActive) setLocalSuccess(`رسالة خاصة جديدة من ${message.user?.name || "عضو"}`);'''
if "scheduleVisibleRead(650)" not in chat:
    if notify_anchor not in chat:
        raise SystemExit(f"{PATCH}: direct socket notify anchor not found")
    chat = chat.replace(
        notify_anchor,
        '''      if (!isOwnMessage && isActive && isChatViewportAtLatest()) scheduleVisibleRead(650);
      if (!isOwnMessage && !isActive) setLocalSuccess(`رسالة خاصة جديدة من ${message.user?.name || "عضو"}`);''',
        1
    )

# ------------------------------------------------------------------
# 7) Replace scroll/read helpers with viewport-aware read flow.
# ------------------------------------------------------------------
old_helpers = '''  function handleMessagesScroll(event) {
    const node = event.currentTarget;
    setShowJumpToLatest(node.scrollHeight - node.scrollTop - node.clientHeight > 220);
  }
  async function markCurrentScopeRead() {
    setLocalError("");
    setLocalSuccess("");
    const didMarkRead = await markRead();
    if (!didMarkRead) {
      setLocalError(lang === "en" ? "Could not mark this chat as read. Try again." : "تعذر تعليم نطاق المحادثة كمقروء. حاول مرة أخرى.");
      return false;
    }
    const latestMessage = messages.filter((message) => !message.deletedAt).at(-1);
    const nextReadAt = latestMessage?.createdAt || new Date().toISOString();
    setLocalLastReadAt(nextReadAt);
    const saved = safeReadChatPrefs(chatScopeStorageKey);
    safeWriteChatPrefs(chatScopeStorageKey, { ...saved, draft, internalNote, chatStatus, messageDensity, showSmartPanel, detailsPanelOpen, messageFilter, composerExpanded, localLastReadAt: nextReadAt });
    setLocalSuccess(lang === "en" ? "Current chat scope marked as read." : "تم تعليم نطاق المحادثة كمقروء من الخادم.");
    return true;
  }
  function jumpToLatestMessage() {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    setShowJumpToLatest(false);
    if (unreadMessagesCount > 0) markCurrentScopeRead();
  }'''

new_helpers = '''  function isChatViewportAtLatest() {
    const node = messagesScrollRef.current;
    if (!node || typeof document === "undefined") return false;
    if (document.visibilityState !== "visible") return false;
    if (typeof document.hasFocus === "function" && !document.hasFocus()) return false;
    return node.scrollHeight - node.scrollTop - node.clientHeight <= 90;
  }

  function scheduleVisibleRead(delay = 500) {
    if (!hasActiveChatScope || !unreadMessagesCount) return;
    window.clearTimeout(autoReadTimerRef.current);
    autoReadTimerRef.current = window.setTimeout(() => {
      if (isChatViewportAtLatest()) void markCurrentScopeRead({ silent: true });
    }, delay);
  }

  function handleMessagesScroll(event) {
    const node = event.currentTarget;
    const distanceFromLatest = node.scrollHeight - node.scrollTop - node.clientHeight;
    setShowJumpToLatest(distanceFromLatest > 220);
    if (distanceFromLatest <= 90 && unreadMessagesCount > 0) scheduleVisibleRead(450);
  }

  async function markCurrentScopeRead({ silent = false } = {}) {
    if (markReadInFlightRef.current) return false;
    markReadInFlightRef.current = true;
    if (!silent) {
      setLocalError("");
      setLocalSuccess("");
    }
    try {
      const didMarkRead = await markRead();
      if (!didMarkRead) {
        if (!silent) setLocalError(lang === "en" ? "Could not mark this chat as read. Try again." : "تعذر تعليم نطاق المحادثة كمقروء. حاول مرة أخرى.");
        return false;
      }
      const latestMessage = messages.filter((message) => !message.deletedAt).at(-1);
      const nextReadAt = latestMessage?.createdAt || new Date().toISOString();
      setLocalLastReadAt(nextReadAt);
      if (isDirectMode && activeConversationId) {
        setConversations((prev) => prev.map((conversation) => (
          conversation.id === activeConversationId ? { ...conversation, unreadCount: 0 } : conversation
        )));
      }
      const saved = safeReadChatPrefs(chatScopeStorageKey);
      safeWriteChatPrefs(chatScopeStorageKey, { ...saved, draft, internalNote, chatStatus, messageDensity, showSmartPanel, detailsPanelOpen, messageFilter, composerExpanded, localLastReadAt: nextReadAt });
      if (!silent) setLocalSuccess(lang === "en" ? "Current chat scope marked as read." : "تم تعليم نطاق المحادثة كمقروء من الخادم.");
      return true;
    } finally {
      markReadInFlightRef.current = false;
    }
  }

  function jumpToLatestMessage() {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    setShowJumpToLatest(false);
    if (unreadMessagesCount > 0) scheduleVisibleRead(650);
  }'''

if old_helpers in chat:
    chat = chat.replace(old_helpers, new_helpers, 1)
elif "function isChatViewportAtLatest()" not in chat:
    raise SystemExit(f"{PATCH}: scroll/read helper block not found")

# ------------------------------------------------------------------
# 8) Auto acknowledge only after the latest edge is visible and focused.
#    Also retry when tab/window becomes visible/focused.
# ------------------------------------------------------------------
scroll_effect_anchor = '''  useEffect(() => {
    const node = messagesScrollRef.current;
    const nearBottom = !node || node.scrollHeight - node.scrollTop - node.clientHeight < 260;
    if (nearBottom || !showJumpToLatest) bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length, activeChannelId, activeConversationId]);
'''
visible_effect = '''  useEffect(() => {
    const node = messagesScrollRef.current;
    const nearBottom = !node || node.scrollHeight - node.scrollTop - node.clientHeight < 260;
    if (nearBottom || !showJumpToLatest) bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length, activeChannelId, activeConversationId]);

  // TCS_VISIBLE_READ_ACK_V1
  useEffect(() => {
    if (!hasActiveChatScope || loading || unreadMessagesCount <= 0) return undefined;
    const timer = window.setTimeout(() => {
      if (isChatViewportAtLatest()) scheduleVisibleRead(0);
    }, 850);
    return () => window.clearTimeout(timer);
  }, [hasActiveChatScope, loading, unreadMessagesCount, messages.length, activeChannelId, activeConversationId]);

  useEffect(() => {
    const tryVisibleRead = () => {
      if (unreadMessagesCount > 0 && isChatViewportAtLatest()) scheduleVisibleRead(250);
    };
    document.addEventListener("visibilitychange", tryVisibleRead);
    window.addEventListener("focus", tryVisibleRead);
    return () => {
      document.removeEventListener("visibilitychange", tryVisibleRead);
      window.removeEventListener("focus", tryVisibleRead);
      window.clearTimeout(autoReadTimerRef.current);
    };
  }, [unreadMessagesCount, activeChannelId, activeConversationId, isDirectMode]);
'''
if "TCS_VISIBLE_READ_ACK_V1" not in chat:
    if scroll_effect_anchor not in chat:
        raise SystemExit(f"{PATCH}: message scroll effect anchor not found")
    chat = chat.replace(scroll_effect_anchor, visible_effect, 1)

# ------------------------------------------------------------------
# 9) Keep unread divider visible for the current scope after acknowledgement.
# ------------------------------------------------------------------
old_divider = 'const showUnreadDivider = message.id === firstUnreadMessageId;'
new_divider = 'const showUnreadDivider = message.id === (unreadDividerMessageId || firstUnreadMessageId);'
if old_divider in chat:
    chat = chat.replace(old_divider, new_divider, 1)
elif new_divider not in chat:
    raise SystemExit(f"{PATCH}: unread divider render anchor not found")

# ------------------------------------------------------------------
# 10) Stable non-visual build/runtime marker.
# ------------------------------------------------------------------
root_anchor = '<div ref={chatShellRef} data-tcs-presentation={presentation}'
if 'data-tcs-unread-read-flow="v1"' not in chat:
    if root_anchor not in chat:
        raise SystemExit(f"{PATCH}: root marker anchor not found")
    chat = chat.replace(
        root_anchor,
        '<div ref={chatShellRef} data-tcs-unread-read-flow="v1" data-tcs-presentation={presentation}',
        1
    )

CHAT.write_text(chat, encoding="utf-8")
HOOK.write_text(hook, encoding="utf-8")

print(f"PATCH={PATCH}")
print("MODE=FUNCTIONAL_FRONTEND")
print("AUTO_MARK_ON_LOAD=REMOVED")
print("VISIBLE_READ_ACK=YES")
print("DIRECT_UNREAD_BADGE=PRESERVED_UNTIL_SEEN")
print("DIRECT_UNREAD_CLEAR=ON_SERVER_ACK")
print("FIRST_UNREAD_DIVIDER=PERSISTENT_PER_SCOPE")
print("NEVER_READ_SCOPE=SUPPORTED")
print("BACKGROUND_TAB_READ=BLOCKED")
print("DESIGN_UNCHANGED=YES")
print("BACKEND_UNCHANGED=YES")
print(f"BACKUP_DIR={backup_dir}")
print("NEXT=BUILD_VERIFY_DEPLOY")
