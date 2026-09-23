#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import shutil
import sys

PATCH = "TCS-REPLY-EDIT-DELETE-REACTIONS-FLOW-V1"
ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS").resolve()
CHAT = ROOT / "frontend/src/components/ChatPanel.jsx"

if not CHAT.exists():
    raise SystemExit(PATCH + ": missing " + str(CHAT))

src = CHAT.read_text(encoding="utf-8")
backup_dir = Path("/tmp") / (PATCH + "-" + datetime.now().strftime("%Y%m%d-%H%M%S"))
backup_dir.mkdir(parents=True, exist_ok=True)
shutil.copy2(CHAT, backup_dir / "ChatPanel.jsx")

state_anchor = '  const [editingMessage, setEditingMessage] = useState(null);'
if "deleteConfirmMessage" not in src:
    if state_anchor not in src:
        raise SystemExit(PATCH + ": editingMessage state anchor not found")
    src = src.replace(
        state_anchor,
        state_anchor + '''
  const [deleteConfirmMessage, setDeleteConfirmMessage] = useState(null);
  const [deletingMessageId, setDeletingMessageId] = useState("");
  const [reactionPendingKey, setReactionPendingKey] = useState("");''',
        1,
    )

ref_anchor = '  const voiceSearchRecognitionRef = useRef(null);'
if "reactionPendingRef" not in src:
    if ref_anchor not in src:
        raise SystemExit(PATCH + ": ref anchor not found")
    src = src.replace(
        ref_anchor,
        ref_anchor + '''
  const reactionPendingRef = useRef(new Set());''',
        1,
    )

reply_anchor = '''  function scrollToMessage(messageId) {
    const node = messageRefs.current.get(messageId);
    if (!node) {
      setLocalError("الرسالة الأصلية غير ظاهرة في النتائج الحالية.");
      return;
    }
    node.scrollIntoView({ behavior: "smooth", block: "center" });
    setFocusedMessageId(messageId);
    window.setTimeout(() => {
      setFocusedMessageId((current) => (current === messageId ? "" : current));
    }, 1800);
  }'''

if "function beginReplyToMessage(" not in src:
    if reply_anchor not in src:
        raise SystemExit(PATCH + ": scrollToMessage anchor not found")
    src = src.replace(
        reply_anchor,
        reply_anchor + '''

  function beginReplyToMessage(message) {
    if (!message?.id || message.deletedAt) return;
    setEditingMessage(null);
    setReplyingTo(message);
    setLocalError("");
    window.setTimeout(() => composerRef.current?.focus?.(), 0);
  }''',
        1,
    )

old_delete = '''  async function handleDelete(message) {
    try {
      setLocalError("");
      await deleteMessage(message.id);
      if (isDirectMode) loadDirectFiles(activeConversationId);
      await loadFailedDriveDeletes();
      if (editingMessage?.id === message.id) resetMessageContext();
    } catch (err) {
      setLocalError(getErrorMessage(err, "تعذر حذف الرسالة."));
    }
  }'''

new_delete = '''  function handleDelete(message) {
    if (!message?.id || message.deletedAt) return;
    const canDelete = message.userId === user?.id || canManageChat;
    if (!canDelete) {
      setLocalError(lang === "en" ? "You do not have permission to delete this message." : "لا تملك صلاحية حذف هذه الرسالة.");
      return;
    }
    setLocalError("");
    setDeleteConfirmMessage(message);
  }

  async function confirmDeleteMessage() {
    const message = deleteConfirmMessage;
    if (!message?.id || deletingMessageId) return;
    try {
      setDeletingMessageId(message.id);
      setLocalError("");
      setLocalSuccess("");
      await deleteMessage(message.id);
      setDeleteConfirmMessage(null);
      setSelectedMessageIds((prev) => prev.filter((id) => id !== message.id));
      if (replyingTo?.id === message.id) setReplyingTo(null);
      if (editingMessage?.id === message.id) {
        setEditingMessage(null);
        setDraft("");
      }
      if (isDirectMode) loadDirectFiles(activeConversationId);
      await loadFailedDriveDeletes();
      setLocalSuccess(lang === "en" ? "Message deleted." : "تم حذف الرسالة.");
    } catch (err) {
      setLocalError(getErrorMessage(err, lang === "en" ? "Could not delete the message." : "تعذر حذف الرسالة."));
    } finally {
      setDeletingMessageId("");
    }
  }'''

if "async function confirmDeleteMessage()" not in src:
    if old_delete not in src:
        raise SystemExit(PATCH + ": handleDelete anchor not found")
    src = src.replace(old_delete, new_delete, 1)

old_edit = '''  function handleEdit(message) {
    setEditingMessage(message);
    setReplyingTo(null);
    setSelectedFiles([]);
    if (fileInputRef.current) fileInputRef.current.value = "";
    setDraft(message.body || "");
    window.setTimeout(() => composerRef.current?.focus(), 0);
  }'''

new_edit = '''  function handleEdit(message) {
    if (!message?.id || message.deletedAt) return;
    if (message.userId !== user?.id) {
      setLocalError(lang === "en" ? "Only the message author can edit it." : "تعديل الرسالة متاح لكاتب الرسالة فقط.");
      return;
    }
    setLocalError("");
    setEditingMessage(message);
    setReplyingTo(null);
    setSelectedFiles([]);
    if (fileInputRef.current) fileInputRef.current.value = "";
    setDraft(message.body || "");
    window.setTimeout(() => composerRef.current?.focus(), 0);
  }'''

if "Only the message author can edit it." not in src:
    if old_edit not in src:
        raise SystemExit(PATCH + ": handleEdit anchor not found")
    src = src.replace(old_edit, new_edit, 1)

old_reaction = '''  async function handleReaction(messageId, emoji) {
    if (!canReactInActiveScope) {
      setLocalError("لا تملك صلاحية إضافة تفاعل في هذه القناة.");
      return;
    }
    try {
      setLocalError("");
      await addReaction(messageId, emoji);
    } catch (err) {
      setLocalError(getErrorMessage(err, "تعذر إضافة التفاعل."));
    }
  }'''

new_reaction = '''  async function handleReaction(messageId, emoji) {
    if (!canReactInActiveScope) {
      setLocalError("لا تملك صلاحية إضافة تفاعل في هذه القناة.");
      return;
    }
    const pendingKey = String(messageId) + ":" + String(emoji);
    if (reactionPendingRef.current.has(pendingKey)) return;
    reactionPendingRef.current.add(pendingKey);
    setReactionPendingKey(pendingKey);
    try {
      setLocalError("");
      await addReaction(messageId, emoji);
    } catch (err) {
      setLocalError(getErrorMessage(err, "تعذر تغيير التفاعل."));
    } finally {
      reactionPendingRef.current.delete(pendingKey);
      setReactionPendingKey((current) => current === pendingKey ? "" : current);
    }
  }'''

if "reactionPendingRef.current.has(pendingKey)" not in src:
    if old_reaction not in src:
        raise SystemExit(PATCH + ": handleReaction anchor not found")
    src = src.replace(old_reaction, new_reaction, 1)

submit_anchor = '''    if (!editingMessage && commandText === "/file") {
      fileInputRef.current?.click();
      return;
    }
    try {'''

submit_new = '''    if (!editingMessage && commandText === "/file") {
      fileInputRef.current?.click();
      return;
    }
    if (editingMessage && draft.trim() === String(editingMessage.body || "").trim()) {
      setEditingMessage(null);
      setDraft("");
      setLocalSuccess(lang === "en" ? "No changes to save." : "لا توجد تغييرات للحفظ.");
      return;
    }
    try {'''

if "No changes to save." not in src:
    if submit_anchor not in src:
        raise SystemExit(PATCH + ": submit anchor not found")
    src = src.replace(submit_anchor, submit_new, 1)

edit_submit = '''      } else if (editingMessage) {
        await editMessage(editingMessage.id, draft);
        setEditingMessage(null);
      } else {'''

edit_submit_new = '''      } else if (editingMessage) {
        await editMessage(editingMessage.id, draft.trim());
        setEditingMessage(null);
        setLocalSuccess(lang === "en" ? "Message updated." : "تم تعديل الرسالة.");
      } else {'''

if 'Message updated.' not in src:
    if edit_submit not in src:
        raise SystemExit(PATCH + ": edit submit anchor not found")
    src = src.replace(edit_submit, edit_submit_new, 1)

map_anchor = '''          const mentionedMembers = extractMentionedMembers(message.body, currentChatMembers);
          return ('''

map_new = '''          const mentionedMembers = extractMentionedMembers(message.body, currentChatMembers);
          const replyParent = message.parentMessage || (message.parentMessageId ? messages.find((item) => item.id === message.parentMessageId) : null);
          return ('''

if "const replyParent = message.parentMessage" not in src:
    if map_anchor not in src:
        raise SystemExit(PATCH + ": message map anchor not found")
    src = src.replace(map_anchor, map_new, 1)

old_parent = '''                  {message.parentMessage && (
                    <button
                      type="button"
                      onClick={() => scrollToMessage(message.parentMessage.id)}
                      className="mb-2 max-w-full rounded-2xl border-r-4 border-amber-300 bg-white px-4 py-2 text-start text-xs text-zinc-500 shadow-sm transition hover:-translate-y-0.5 hover:border-amber-400 hover:bg-amber-50 dark:bg-zinc-900 dark:text-zinc-300 dark:hover:bg-amber-500/10"
                      title="الانتقال للرسالة الأصلية"
                    >
                      <span className="font-black text-zinc-700 dark:text-zinc-100">رد على {message.parentMessage.user?.name || "رسالة"}: </span>{truncateMessagePreview(message.parentMessage.body)}
                    </button>
                  )}'''

new_parent = '''                  {(replyParent || message.parentMessageId) && (
                    <button
                      type="button"
                      onClick={() => replyParent?.id && scrollToMessage(replyParent.id)}
                      disabled={!replyParent?.id}
                      className="mb-2 max-w-full rounded-2xl border-r-4 border-amber-300 bg-white px-4 py-2 text-start text-xs text-zinc-500 shadow-sm transition hover:-translate-y-0.5 hover:border-amber-400 hover:bg-amber-50 disabled:cursor-default disabled:opacity-70 dark:bg-zinc-900 dark:text-zinc-300 dark:hover:bg-amber-500/10"
                      title={replyParent?.id ? (lang === "en" ? "Jump to original message" : "الانتقال للرسالة الأصلية") : (lang === "en" ? "Original message is not loaded" : "الرسالة الأصلية غير محملة")}
                    >
                      <span className="font-black text-zinc-700 dark:text-zinc-100">
                        {lang === "en" ? "Reply to " + (replyParent?.user?.name || "message") + ": " : "رد على " + (replyParent?.user?.name || "رسالة") + ": "}
                      </span>
                      {replyParent ? truncateMessagePreview(replyParent.body || (lang === "en" ? "Deleted message" : "رسالة محذوفة")) : (lang === "en" ? "Original message" : "الرسالة الأصلية")}
                    </button>
                  )}'''

if "Original message is not loaded" not in src:
    if old_parent not in src:
        raise SystemExit(PATCH + ": parent reply render anchor not found")
    src = src.replace(old_parent, new_parent, 1)

old_edit_action = '{(isOwner || canManageChat) && <button type="button" onClick={() => onEdit(message)} className={actionClass}>تعديل</button>}'
new_edit_action = '{isOwner && <button type="button" onClick={() => onEdit(message)} className={actionClass}>{currentChatLang() === "en" ? "Edit" : "تعديل"}</button>}'
if old_edit_action in src:
    src = src.replace(old_edit_action, new_edit_action, 1)

old_reply_call = 'onReply={(item) => { setEditingMessage(null); setReplyingTo(item); window.setTimeout(() => composerRef.current?.focus(), 0); }}'
if old_reply_call in src:
    src = src.replace(old_reply_call, 'onReply={beginReplyToMessage}', 1)

mobile_reply_old = '''              <button type="button" onClick={() => { setReplyingTo(mobileActionMessage); setMobileActionMessage(null); composerRef.current?.focus?.(); }} className="rounded-2xl bg-zinc-100 px-3 py-2 dark:bg-white/10">Reply</button>'''
mobile_reply_new = '''              <button type="button" onClick={() => { beginReplyToMessage(mobileActionMessage); setMobileActionMessage(null); }} className="rounded-2xl bg-zinc-100 px-3 py-2 dark:bg-white/10">Reply</button>'''
if mobile_reply_old in src:
    src = src.replace(mobile_reply_old, mobile_reply_new, 1)

mobile_anchor = '''              <button type="button" onClick={() => { toggleMessageSelection(mobileActionMessage); setMobileActionMessage(null); }} className="rounded-2xl bg-zinc-950 px-3 py-2 text-white dark:bg-white dark:text-zinc-950">Select</button>
            </div>'''

mobile_new = '''              <button type="button" onClick={() => { toggleMessageSelection(mobileActionMessage); setMobileActionMessage(null); }} className="rounded-2xl bg-zinc-950 px-3 py-2 text-white dark:bg-white dark:text-zinc-950">Select</button>
              {mobileActionMessage.userId === user?.id && <button type="button" onClick={() => { handleEdit(mobileActionMessage); setMobileActionMessage(null); }} className="rounded-2xl bg-zinc-100 px-3 py-2 dark:bg-white/10">{lang === "en" ? "Edit" : "تعديل"}</button>}
              {(mobileActionMessage.userId === user?.id || canManageChat) && <button type="button" onClick={() => { handleDelete(mobileActionMessage); setMobileActionMessage(null); }} className="rounded-2xl bg-red-50 px-3 py-2 text-red-600 dark:bg-red-500/10 dark:text-red-100">{lang === "en" ? "Delete" : "حذف"}</button>}
            </div>
            <div className="mt-3 flex flex-wrap items-center gap-2 border-t border-zinc-100 pt-3 dark:border-white/10">
              <span className="text-[10px] font-black text-zinc-400">{lang === "en" ? "React" : "تفاعل"}</span>
              {CHAT_REACTION_EMOJIS.map((emoji) => (
                <button key={emoji} type="button" onClick={() => { void handleReaction(mobileActionMessage.id, emoji); setMobileActionMessage(null); }} disabled={reactionPendingKey === String(mobileActionMessage.id) + ":" + String(emoji)} className="grid h-9 w-9 place-items-center rounded-full bg-zinc-50 text-base disabled:opacity-50 dark:bg-white/5">
                  {emoji}
                </button>
              ))}
            </div>'''

if "mobileActionMessage.userId === user?.id && <button" not in src:
    if mobile_anchor not in src:
        raise SystemExit(PATCH + ": mobile action anchor not found")
    src = src.replace(mobile_anchor, mobile_new, 1)

modal_anchor = '''      <UserProfileCard contained={isDesktopWindow} user={selectedProfile} currentUserId={displayUser?.id || user?.id || ""} summary={profileSummary} avatarUploading={avatarUploading} onAvatarFile={uploadAvatarFile} onClose={() => setSelectedProfile(null)} />'''

delete_modal = modal_anchor + '''
      {deleteConfirmMessage && (
        <div data-tcs-message-actions-flow="v1" className={isDesktopWindow ? "tcs-v5-contained-surface absolute inset-0 z-[70] grid place-items-center bg-zinc-950/50 p-4 backdrop-blur-sm" : "fixed inset-0 z-[70] grid place-items-center bg-zinc-950/50 p-4 backdrop-blur-sm"} role="dialog" aria-modal="true" aria-label={lang === "en" ? "Delete message confirmation" : "تأكيد حذف الرسالة"}>
          <button type="button" className="absolute inset-0 cursor-default" onClick={() => !deletingMessageId && setDeleteConfirmMessage(null)} aria-label={lang === "en" ? "Cancel delete" : "إلغاء الحذف"} />
          <div className="relative w-full max-w-md rounded-[26px] border border-zinc-200 bg-white p-5 shadow-2xl dark:border-white/10 dark:bg-zinc-950">
            <div className="text-base font-black text-zinc-950 dark:text-white">{lang === "en" ? "Delete this message?" : "حذف هذه الرسالة؟"}</div>
            <div className="mt-2 rounded-2xl bg-zinc-50 px-3 py-2 text-xs leading-5 text-zinc-500 dark:bg-white/5 dark:text-zinc-300">{truncateMessagePreview(deleteConfirmMessage.body || (lang === "en" ? "Message" : "رسالة"), 160)}</div>
            {(deleteConfirmMessage.files || []).length > 0 && <div className="mt-2 text-[11px] font-bold text-amber-700 dark:text-amber-200">{lang === "en" ? "Its attachments will also be removed from chat; Drive cleanup keeps the existing retry-safe flow." : "مرفقات الرسالة ستُحذف من الشات أيضًا، وتنظيف Drive سيستخدم مسار Retry الآمن الحالي."}</div>}
            <div className="mt-5 grid grid-cols-2 gap-2">
              <button type="button" onClick={() => setDeleteConfirmMessage(null)} disabled={Boolean(deletingMessageId)} className="rounded-2xl border border-zinc-200 px-4 py-2.5 text-sm font-black text-zinc-600 disabled:opacity-50 dark:border-white/10 dark:text-zinc-300">{lang === "en" ? "Cancel" : "إلغاء"}</button>
              <button type="button" onClick={confirmDeleteMessage} disabled={Boolean(deletingMessageId)} className="rounded-2xl bg-red-500 px-4 py-2.5 text-sm font-black text-white disabled:opacity-50">{deletingMessageId ? (lang === "en" ? "Deleting..." : "جاري الحذف...") : (lang === "en" ? "Delete" : "حذف")}</button>
            </div>
          </div>
        </div>
      )}'''

if 'data-tcs-message-actions-flow="v1"' not in src:
    if modal_anchor not in src:
        raise SystemExit(PATCH + ": delete modal anchor not found")
    src = src.replace(modal_anchor, delete_modal, 1)

CHAT.write_text(src, encoding="utf-8")

print("PATCH=" + PATCH)
print("MODE=FUNCTIONAL_FRONTEND")
print("REPLY_PARENT_FALLBACK=YES")
print("REPLY_DELETED_GUARD=YES")
print("EDIT_OWNER_ONLY=YES")
print("EDIT_NOOP_GUARD=YES")
print("DELETE_CONFIRMATION=YES")
print("DELETE_FILES_CLEANUP=PRESERVED")
print("REACTION_TOGGLE_GUARD=YES")
print("MOBILE_ACTIONS=ALIGNED")
print("REALTIME_UPDATES=PRESERVED")
print("ATTACHMENTS_FLOW=PRESERVED")
print("BACKEND_UNCHANGED=YES")
print("BACKUP_DIR=" + str(backup_dir))
print("NEXT=BUILD_VERIFY_DEPLOY")
