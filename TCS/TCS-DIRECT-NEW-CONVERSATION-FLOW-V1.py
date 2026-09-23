#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import shutil, sys

PATCH = "TCS-DIRECT-NEW-CONVERSATION-FLOW-V1"
ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS").resolve()
CHAT = ROOT / "frontend/src/components/ChatPanel.jsx"

if not CHAT.exists():
    raise SystemExit(f"{PATCH}: missing {CHAT}")

src = CHAT.read_text(encoding="utf-8")
backup_dir = Path("/tmp") / f"{PATCH}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
backup_dir.mkdir(parents=True, exist_ok=True)
shutil.copy2(CHAT, backup_dir / "ChatPanel.jsx")

# 1) Add dedicated loading state for the one-click direct conversation flow.
state_anchor = '  const [selectedDirectUserId, setSelectedDirectUserId] = useState("");'
if 'startingDirectUserId' not in src:
    if state_anchor not in src:
        raise SystemExit(f"{PATCH}: selectedDirectUserId state anchor not found")
    src = src.replace(
        state_anchor,
        state_anchor + '\n  const [startingDirectUserId, setStartingDirectUserId] = useState("");',
        1
    )

# 2) Replace the old submit-only direct flow with:
#    - local duplicate reuse
#    - one-click open from member picker
#    - API create only when no loaded direct conversation exists
old_fn = '''  async function startDirectConversation(event) {
    event.preventDefault();
    if (!canDirectChat || !selectedDirectUserId) return;
    try {
      setLocalError("");
      const conversation = await api.chat.createDirect(selectedDirectUserId);
      setConversations((prev) => upsertById(prev, conversation));
      closeHuddle();
      setActiveConversationId(conversation.id);
      setSelectedDirectUserId("");
      resetMessageContext();
    } catch (err) {
      setLocalError(getErrorMessage(err, "تعذر بدء المحادثة الخاصة."));
    }
  }'''

new_fn = '''  function findExistingDirectConversation(targetUserId) {
    const targetId = String(targetUserId || "");
    const currentId = String(user?.id || "");
    if (!targetId) return null;
    return conversations.find((conversation) => {
      const memberIds = (conversation?.members || [])
        .map((member) => String(member?.userId || member?.user?.id || ""))
        .filter(Boolean);
      const otherIds = memberIds.filter((memberId) => memberId !== currentId);
      const type = String(conversation?.type || "").toUpperCase();
      const directLike = type === "DIRECT" || (!conversation?.name && !conversation?.groupName && otherIds.length === 1);
      return directLike && otherIds.length === 1 && otherIds[0] === targetId;
    }) || null;
  }

  function activateDirectConversation(conversation) {
    if (!conversation?.id) return;
    setConversations((prev) => upsertById(prev, conversation));
    closeHuddle();
    setMode("direct");
    setActiveConversationId(conversation.id);
    setSelectedDirectUserId("");
    setShowV8NewConversation(false);
    setShowNewGroup(false);
    setDetailsPanelOpen(false);
    setToolbarOpen(false);
    setStatusMenuOpen(false);
    resetMessageContext();
  }

  async function openDirectConversationWithUser(targetUserId) {
    const nextUserId = String(targetUserId || "");
    if (!canDirectChat || !nextUserId || startingDirectUserId) return;

    const existingConversation = findExistingDirectConversation(nextUserId);
    if (existingConversation) {
      setLocalError("");
      activateDirectConversation(existingConversation);
      return;
    }

    try {
      setLocalError("");
      setStartingDirectUserId(nextUserId);
      const conversation = await api.chat.createDirect(nextUserId);
      activateDirectConversation(conversation);
    } catch (err) {
      setSelectedDirectUserId(nextUserId);
      setLocalError(getErrorMessage(err, lang === "en" ? "Could not start the direct conversation." : "تعذر بدء المحادثة الخاصة."));
    } finally {
      setStartingDirectUserId("");
    }
  }

  async function startDirectConversation(event) {
    event.preventDefault();
    await openDirectConversationWithUser(selectedDirectUserId);
  }'''

if 'function findExistingDirectConversation(targetUserId)' not in src:
    if old_fn not in src:
        raise SystemExit(f"{PATCH}: old startDirectConversation function not found")
    src = src.replace(old_fn, new_fn, 1)

# 3) Desktop new-conversation form becomes one-click: choose a member -> open immediately.
old_picker = '''                <TcsPremiumSelect value={selectedDirectUserId} onChange={setSelectedDirectUserId} options={availableDirectUsers.map((item) => ({ value: item.id, label: item.name || item.email || item.role, meta: item.email || item.jobTitle || item.role || "" }))} placeholder={ui.chooseMember} searchable searchPlaceholder={lang === "en" ? "Search members..." : "ابحث عن عضو..."} className="tcs-v16-member-picker" />
                <button type="submit" disabled={!selectedDirectUserId} className="mt-2 w-full rounded-xl bg-amber-400 px-3 py-2 text-xs font-black text-zinc-950 disabled:opacity-50">{ui.startConversation}</button>'''

new_picker = '''                <TcsPremiumSelect
                  value={selectedDirectUserId}
                  onChange={(nextUserId) => {
                    setSelectedDirectUserId(nextUserId);
                    if (nextUserId) void openDirectConversationWithUser(nextUserId);
                  }}
                  options={availableDirectUsers.map((item) => ({ value: item.id, label: item.name || item.email || item.role, meta: item.email || item.jobTitle || item.role || "" }))}
                  placeholder={startingDirectUserId ? (lang === "en" ? "Opening conversation..." : "جاري فتح المحادثة...") : ui.chooseMember}
                  searchable
                  searchPlaceholder={lang === "en" ? "Search members..." : "ابحث عن عضو..."}
                  disabled={Boolean(startingDirectUserId)}
                  className="tcs-v16-member-picker tcs-direct-new-conversation-v1"
                />
                <div className="mt-2 text-[10px] leading-4 text-zinc-500">
                  {startingDirectUserId
                    ? (lang === "en" ? "Opening the conversation…" : "جاري فتح المحادثة…")
                    : (lang === "en" ? "Choose a teammate to open the conversation instantly." : "اختر عضوًا لفتح المحادثة فورًا.")}
                </div>'''

if 'tcs-direct-new-conversation-v1' not in src:
    if old_picker not in src:
        raise SystemExit(f"{PATCH}: desktop direct picker block not found")
    src = src.replace(old_picker, new_picker, 1)

# 4) Mobile/new conversation picker uses the same instant-open behavior while keeping submit fallback.
mobile_picker = '''<TcsPremiumSelect value={selectedDirectUserId} onChange={setSelectedDirectUserId} options={availableDirectUsers.map((item) => ({ value: item.id, label: item.name || item.email || item.role, meta: item.email || item.jobTitle || item.role || "" }))} placeholder={ui.chooseMember} searchable searchPlaceholder={lang === "en" ? "Search members..." : "ابحث عن عضو..."} className="tcs-v16-member-picker min-w-0 flex-1" />'''
mobile_replacement = '''<TcsPremiumSelect value={selectedDirectUserId} onChange={(nextUserId) => { setSelectedDirectUserId(nextUserId); if (nextUserId) void openDirectConversationWithUser(nextUserId); }} options={availableDirectUsers.map((item) => ({ value: item.id, label: item.name || item.email || item.role, meta: item.email || item.jobTitle || item.role || "" }))} placeholder={startingDirectUserId ? (lang === "en" ? "Opening conversation..." : "جاري فتح المحادثة...") : ui.chooseMember} searchable searchPlaceholder={lang === "en" ? "Search members..." : "ابحث عن عضو..."} disabled={Boolean(startingDirectUserId)} className="tcs-v16-member-picker tcs-direct-new-conversation-v1 min-w-0 flex-1" />'''
if mobile_picker in src:
    src = src.replace(mobile_picker, mobile_replacement, 1)

# Prevent duplicate submit while an API request is active.
src = src.replace(
    'if (!canDirectChat || !selectedDirectUserId) return;\n    await openDirectConversationWithUser(selectedDirectUserId);',
    'if (!canDirectChat || !selectedDirectUserId || startingDirectUserId) return;\n    await openDirectConversationWithUser(selectedDirectUserId);',
    1
)

CHAT.write_text(src, encoding="utf-8")

print(f"PATCH={PATCH}")
print("MODE=FUNCTIONAL_FRONTEND")
print("ONE_CLICK_OPEN=YES")
print("EXISTING_DIRECT_REUSE=YES")
print("DUPLICATE_API_CALL_GUARD=YES")
print("SEARCHABLE_PICKER=PRESERVED")
print("GROUP_CHAT=PRESERVED")
print("DESIGN_SCOPE=UNCHANGED")
print("BACKEND_UNCHANGED=YES")
print(f"BACKUP_DIR={backup_dir}")
print("NEXT=BUILD_VERIFY_DEPLOY")
