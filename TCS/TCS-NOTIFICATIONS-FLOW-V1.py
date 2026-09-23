#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import shutil, sys

PATCH = "TCS-NOTIFICATIONS-FLOW-V1"
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

# Bell icon.
old_import = 'import { Archive, Download, Eye, FileText, FolderKanban, Image as ImageIcon, Lock, MessageCircle, Mic, MicOff, Monitor, MoreHorizontal, Paperclip, Phone, PhoneOff, RefreshCw, Search, Send, Settings2, Trash2, Users, Video, VideoOff, X } from "lucide-react";'
new_import = 'import { Archive, Bell, Download, Eye, FileText, FolderKanban, Image as ImageIcon, Lock, MessageCircle, Mic, MicOff, Monitor, MoreHorizontal, Paperclip, Phone, PhoneOff, RefreshCw, Search, Send, Settings2, Trash2, Users, Video, VideoOff, X } from "lucide-react";'
if old_import in chat:
    chat = chat.replace(old_import, new_import, 1)
elif "Bell" not in chat.split("\n", 3)[1]:
    raise SystemExit(f"{PATCH}: lucide import anchor not found")

# Robust notification target resolver.
target_anchor = '''function conversationLastTime(conversation = {}) {
  const value = conversation.lastMessage?.createdAt || conversation.latestMessage?.createdAt || conversation.updatedAt || conversation.createdAt;
  return value ? new Date(value).toLocaleTimeString("ar-EG", { hour: "2-digit", minute: "2-digit" }) : "";
}'''
target_helper = target_anchor + '''

function chatNotificationTarget(notification = {}) {
  const data = notification?.data && typeof notification.data === "object" ? notification.data : {};
  const metadata = notification?.metadata && typeof notification.metadata === "object" ? notification.metadata : {};
  const payload = notification?.payload && typeof notification.payload === "object" ? notification.payload : {};
  const source = { ...payload, ...metadata, ...data, ...notification };
  return {
    conversationId: String(source.conversationId || source.chatConversationId || source.targetConversationId || "").trim(),
    projectId: String(source.projectId || source.targetProjectId || "").trim(),
    channelId: String(source.channelId || source.targetChannelId || "").trim(),
    messageId: String(source.messageId || source.targetMessageId || source.entityId || "").trim(),
    url: String(source.url || source.href || source.link || "").trim(),
  };
}'''
if "function chatNotificationTarget(" not in chat:
    if target_anchor not in chat:
        raise SystemExit(f"{PATCH}: conversationLastTime anchor not found")
    chat = chat.replace(target_anchor, target_helper, 1)

# Pending message jump state.
state_anchor = '  const [localLastReadAt, setLocalLastReadAt] = useState("");'
if "pendingNotificationMessageId" not in chat:
    if state_anchor not in chat:
        raise SystemExit(f"{PATCH}: localLastReadAt anchor not found")
    chat = chat.replace(
        state_anchor,
        state_anchor + '\n  const [pendingNotificationMessageId, setPendingNotificationMessageId] = useState("");',
        1
    )

# useChat callback now receives notification object; suppress toast noise for active scope.
old_notify = '''    onNotify: (message) => setLocalSuccess(message),'''
new_notify = '''    onNotify: (message, notification) => {
      const target = chatNotificationTarget(notification || {});
      const sameDirect = Boolean(target.conversationId && isDirectMode && target.conversationId === activeConversationId);
      const sameProject = Boolean(!target.conversationId && target.projectId && !isDirectMode && target.projectId === projectId && (target.channelId || "") === (activeChannelId || ""));
      if (!sameDirect && !sameProject) setLocalSuccess(message);
    },'''
if old_notify in chat:
    chat = chat.replace(old_notify, new_notify, 1)
elif "const sameDirect = Boolean(target.conversationId" not in chat:
    raise SystemExit(f"{PATCH}: onNotify anchor not found")

# Notification opener and message jump.
helper_anchor = '''  function jumpToLatestMessage() {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    setShowJumpToLatest(false);
    if (unreadMessagesCount > 0) scheduleVisibleRead(650);
  }'''
notification_helpers = helper_anchor + '''

  async function openChatNotification(notification) {
    if (!notification?.id) return;
    const target = chatNotificationTarget(notification);
    await markNotificationsRead([notification.id]);

    setDetailsPanelOpen(false);
    setToolbarOpen(false);
    setStatusMenuOpen(false);

    if (target.conversationId) {
      setMode("direct");
      setActiveConversationId(target.conversationId);
      resetMessageContext();
      if (target.messageId) setPendingNotificationMessageId(target.messageId);
      return;
    }

    if (target.projectId && target.projectId === projectId) {
      setMode("project");
      setActiveConversationId("");
      setActiveChannelId(target.channelId || "");
      resetMessageContext();
      if (target.messageId) setPendingNotificationMessageId(target.messageId);
      return;
    }

    if (target.url && typeof window !== "undefined") {
      try {
        const resolved = new URL(target.url, window.location.origin);
        if (resolved.origin === window.location.origin) {
          window.location.assign(resolved.href);
          return;
        }
      } catch {}
    }

    if (target.messageId) {
      setPendingNotificationMessageId(target.messageId);
      window.setTimeout(() => scrollToMessage(target.messageId), 0);
    }
  }

  async function markAllChatNotificationsRead() {
    if (!notificationUnreadCount) return;
    await markNotificationsRead([]);
  }'''
if "async function openChatNotification(" not in chat:
    if helper_anchor not in chat:
        raise SystemExit(f"{PATCH}: jumpToLatestMessage anchor not found")
    chat = chat.replace(helper_anchor, notification_helpers, 1)

# Jump once messages for the target scope have loaded.
effect_anchor = '''  useEffect(() => {
    const node = messagesScrollRef.current;
    const nearBottom = !node || node.scrollHeight - node.scrollTop - node.clientHeight < 260;
    if (nearBottom || !showJumpToLatest) bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length, activeChannelId, activeConversationId]);'''
pending_effect = effect_anchor + '''

  // TCS_NOTIFICATIONS_FLOW_V1
  useEffect(() => {
    if (!pendingNotificationMessageId || loading) return;
    const exists = messages.some((message) => message.id === pendingNotificationMessageId);
    if (!exists) return;
    window.setTimeout(() => {
      scrollToMessage(pendingNotificationMessageId);
      setPendingNotificationMessageId("");
    }, 120);
  }, [pendingNotificationMessageId, loading, messages.length, activeChannelId, activeConversationId]);'''
if "TCS_NOTIFICATIONS_FLOW_V1" not in chat:
    if effect_anchor not in chat:
        raise SystemExit(f"{PATCH}: messages scroll effect anchor not found")
    chat = chat.replace(effect_anchor, pending_effect, 1)

# Add Bell action + badge before Search in desktop header.
search_button = '''            <button
              type="button"
              onClick={() => { setStatusMenuOpen(false); setWorkspaceSearchType("smart"); setWorkspaceSearchOpen(true); setToolbarOpen(false); }}
              className="tcs-v3-icon-action"
              title={lang === "en" ? "Search" : "بحث"}
              aria-label={lang === "en" ? "Search" : "بحث"}
            >
              <Search size={16} />
            </button>'''
bell_plus_search = '''            <button
              type="button"
              onClick={() => { setStatusMenuOpen(false); setToolbarOpen(false); setDetailsTab("activity"); setDetailsPanelOpen(true); }}
              className="tcs-v3-icon-action relative"
              title={lang === "en" ? "Notifications" : "الإشعارات"}
              aria-label={lang === "en" ? "Notifications" : "الإشعارات"}
              data-tcs-notifications-flow="v1"
            >
              <Bell size={16} />
              {notificationUnreadCount > 0 && (
                <span className="absolute -right-1 -top-1 grid min-h-[16px] min-w-[16px] place-items-center rounded-full bg-red-500 px-1 text-[8px] font-black leading-none text-white">
                  {notificationUnreadCount > 99 ? "99+" : notificationUnreadCount}
                </span>
              )}
            </button>

''' + search_button
if 'data-tcs-notifications-flow="v1"' not in chat:
    if search_button not in chat:
        raise SystemExit(f"{PATCH}: desktop Search button anchor not found")
    chat = chat.replace(search_button, bell_plus_search, 1)

# Upgrade notification card: real unread count, mark all, navigation on click.
old_card = '''              <div className="tos-chat-detail-card rounded-[18px] border border-zinc-100 bg-white p-2.5 shadow-sm dark:border-white/10 dark:bg-zinc-900 2xl:rounded-[20px] 2xl:p-3">
                <div className="mb-3 text-sm font-black text-zinc-950 dark:text-white">إشعارات الشات</div>
                <div className="space-y-2">
                  {(notifications || []).slice(0, 5).map((notification) => (
                    <button key={notification.id} type="button" onClick={() => markNotificationsRead([notification.id])} className={`block w-full rounded-xl px-2.5 py-1.5 text-right text-xs ${notification.readAt ? "bg-zinc-50 text-zinc-500 dark:bg-white/5" : "bg-amber-50 text-amber-800 dark:bg-amber-500/10 dark:text-amber-100"}`}>
                      <div className="font-black">{notification.title}</div>
                      <div className="mt-1 truncate opacity-75">{notification.body}</div>
                    </button>
                  ))}
                  {(!notifications || notifications.length === 0) && <div className="rounded-2xl bg-zinc-50 px-3 py-2 text-xs text-zinc-400 dark:bg-white/5">لا توجد إشعارات.</div>}
                </div>
              </div>'''
new_card = '''              <div className="tos-chat-detail-card rounded-[18px] border border-zinc-100 bg-white p-2.5 shadow-sm dark:border-white/10 dark:bg-zinc-900 2xl:rounded-[20px] 2xl:p-3">
                <div className="mb-3 flex items-center justify-between gap-2">
                  <div>
                    <div className="text-sm font-black text-zinc-950 dark:text-white">{ui.notifications}</div>
                    {notificationUnreadCount > 0 && <div className="mt-0.5 text-[10px] font-bold text-amber-700 dark:text-amber-200">{notificationUnreadCount} {lang === "en" ? "unread" : "غير مقروء"}</div>}
                  </div>
                  {notificationUnreadCount > 0 && (
                    <button type="button" onClick={markAllChatNotificationsRead} className="rounded-lg border border-zinc-100 bg-zinc-50 px-2 py-1 text-[9px] font-black text-zinc-600 hover:bg-amber-50 hover:text-amber-700 dark:border-white/10 dark:bg-white/5 dark:text-zinc-300">
                      {lang === "en" ? "Mark all read" : "قراءة الكل"}
                    </button>
                  )}
                </div>
                <div className="space-y-2">
                  {(notifications || []).slice(0, 8).map((notification) => (
                    <button key={notification.id} type="button" onClick={() => openChatNotification(notification)} className={`block w-full rounded-xl border px-2.5 py-2 text-start text-xs transition ${notification.readAt ? "border-transparent bg-zinc-50 text-zinc-500 dark:bg-white/5" : "border-amber-100 bg-amber-50 text-amber-800 hover:border-amber-200 dark:border-amber-500/10 dark:bg-amber-500/10 dark:text-amber-100"}`}>
                      <div className="flex items-start gap-2">
                        {!notification.readAt && <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-amber-500" />}
                        <div className="min-w-0 flex-1">
                          <div className="truncate font-black">{notification.title || (lang === "en" ? "Chat notification" : "إشعار شات")}</div>
                          <div className="mt-1 line-clamp-2 opacity-75">{notification.body || ""}</div>
                          <div className="mt-1 text-[9px] opacity-55">{notification.createdAt ? new Date(notification.createdAt).toLocaleString(chatLocale(lang)) : ""}</div>
                        </div>
                      </div>
                    </button>
                  ))}
                  {(!notifications || notifications.length === 0) && <div className="rounded-2xl bg-zinc-50 px-3 py-2 text-xs text-zinc-400 dark:bg-white/5">{ui.noNotifications}</div>}
                </div>
              </div>'''
if old_card in chat:
    chat = chat.replace(old_card, new_card, 1)
elif "onClick={() => openChatNotification(notification)}" not in chat:
    raise SystemExit(f"{PATCH}: notification card anchor not found")

# useChat: correct mark-read count and return status.
old_mark = '''  async function markNotificationsRead(notificationIds = []) {
    try {
      await api.chat.markNotificationsRead(notificationIds);
      setNotifications((prev) => prev.map((item) => (!notificationIds.length || notificationIds.includes(item.id) ? { ...item, readAt: item.readAt || new Date().toISOString() } : item)));
      setNotificationUnreadCount((count) => notificationIds.length ? Math.max(0, count - notificationIds.length) : 0);
    } catch {
      // Non-blocking.
    }
  }'''
new_mark = '''  async function markNotificationsRead(notificationIds = []) {
    try {
      const ids = new Set(notificationIds || []);
      const unreadBeingMarked = notifications.filter((item) => !item.readAt && (!ids.size || ids.has(item.id))).length;
      await api.chat.markNotificationsRead(notificationIds);
      const readAt = new Date().toISOString();
      setNotifications((prev) => prev.map((item) => (!ids.size || ids.has(item.id) ? { ...item, readAt: item.readAt || readAt } : item)));
      setNotificationUnreadCount((count) => ids.size ? Math.max(0, count - unreadBeingMarked) : 0);
      return true;
    } catch {
      // Non-blocking.
      return false;
    }
  }'''
if old_mark in hook:
    hook = hook.replace(old_mark, new_mark, 1)
elif "const unreadBeingMarked = notifications.filter" not in hook:
    raise SystemExit(f"{PATCH}: markNotificationsRead anchor not found")

# Realtime notification de-dupe + second callback arg.
old_realtime = '''    const onChatNotification = (notification) => {
      if (!notification?.id) return;
      setNotifications((prev) => upsertById([notification, ...prev], notification).slice(0, 30));
      setNotificationUnreadCount((count) => count + (notification.readAt ? 0 : 1));
      onNotify?.(notification.title || "إشعار جديد في الشات");
    };'''
new_realtime = '''    const onChatNotification = (notification) => {
      if (!notification?.id) return;
      setNotifications((prev) => {
        const existed = prev.some((item) => item.id === notification.id);
        if (!existed && !notification.readAt) setNotificationUnreadCount((count) => count + 1);
        return upsertById([notification, ...prev], notification).slice(0, 30);
      });
      onNotify?.(notification.title || "إشعار جديد في الشات", notification);
    };'''
if old_realtime in hook:
    hook = hook.replace(old_realtime, new_realtime, 1)
elif "const existed = prev.some((item) => item.id === notification.id)" not in hook:
    raise SystemExit(f"{PATCH}: realtime notification anchor not found")

CHAT.write_text(chat, encoding="utf-8")
HOOK.write_text(hook, encoding="utf-8")

print(f"PATCH={PATCH}")
print("MODE=FUNCTIONAL_FRONTEND")
print("HEADER_BADGE=REALTIME")
print("NOTIFICATION_OPEN_TARGET=YES")
print("SINGLE_MARK_READ=YES")
print("MARK_ALL_READ=YES")
print("REALTIME_DEDUPE=YES")
print("ACTIVE_SCOPE_NOISE=SUPPRESSED")
print("MESSAGE_JUMP=YES")
print("DESIGN_SCOPE=MINIMAL_FUNCTIONAL_UI_ONLY")
print("BACKEND_UNCHANGED=YES")
print(f"BACKUP_DIR={backup_dir}")
print("NEXT=BUILD_VERIFY_DEPLOY")
