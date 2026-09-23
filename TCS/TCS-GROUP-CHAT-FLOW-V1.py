#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import shutil, sys

PATCH = "TCS-GROUP-CHAT-FLOW-V1"
ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS").resolve()
CHAT = ROOT / "frontend/src/components/ChatPanel.jsx"
API = ROOT / "frontend/src/lib/api.js"
ROUTE = ROOT / "backend/src/routes/chat.routes.js"

for path in (CHAT, API, ROUTE):
    if not path.exists():
        raise SystemExit(f"{PATCH}: missing {path}")

backup = Path("/tmp") / f"{PATCH}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
backup.mkdir(parents=True, exist_ok=True)
for path in (CHAT, API, ROUTE):
    shutil.copy2(path, backup / path.name)

chat = CHAT.read_text(encoding="utf-8")
api = API.read_text(encoding="utf-8")
route = ROUTE.read_text(encoding="utf-8")

# ---------------- backend: owner metadata + safe group management ----------------
old_sanitize = '''function sanitizeConversation(conversation) {
  return {
    id: conversation.id,
    type: conversation.type,
    name: conversation.name || null,
    unreadCount: conversation.unreadCount || 0,
    createdAt: conversation.createdAt,
    updatedAt: conversation.updatedAt || null,
    members: (conversation.members || []).map((member) => ({ userId: member.userId, user: sanitizeChatUser(member.user) })),
    lastMessage: conversation.messages?.[0] ? sanitizeMessage(conversation.messages[0]) : null,
  };
}'''

new_sanitize = '''function sanitizeConversation(conversation) {
  return {
    id: conversation.id,
    type: conversation.type,
    name: conversation.name || null,
    ownerId: conversation.ownerId || null,
    unreadCount: conversation.unreadCount || 0,
    createdAt: conversation.createdAt,
    updatedAt: conversation.updatedAt || null,
    members: (conversation.members || []).map((member) => ({ userId: member.userId, user: sanitizeChatUser(member.user) })),
    lastMessage: conversation.messages?.[0] ? sanitizeMessage(conversation.messages[0]) : null,
  };
}

async function resolveGroupOwnerId(conversation) {
  if (!conversation || conversation.type !== "GROUP") return null;
  const audit = await prisma.chatAuditLog.findFirst({
    where: { conversationId: conversation.id, action: "CONVERSATION_CREATED" },
    orderBy: { createdAt: "asc" },
    select: { actorId: true },
  });
  if (audit?.actorId) return audit.actorId;
  const firstMember = [...(conversation.members || [])].sort((a, b) => {
    const byTime = new Date(a.createdAt || 0).getTime() - new Date(b.createdAt || 0).getTime();
    return byTime || String(a.id || "").localeCompare(String(b.id || ""));
  })[0];
  return firstMember?.userId || null;
}

async function attachConversationOwners(conversations = []) {
  return Promise.all(conversations.map(async (conversation) => ({
    ...conversation,
    ownerId: await resolveGroupOwnerId(conversation),
  })));
}'''

if "async function resolveGroupOwnerId(" not in route:
    if old_sanitize not in route:
        raise SystemExit(f"{PATCH}: sanitizeConversation anchor missing")
    route = route.replace(old_sanitize, new_sanitize, 1)

old_list = '''  const conversationsWithUnread = await attachConversationUnreadCounts(conversations, req.user.id);
  res.json(conversationsWithUnread.map(sanitizeConversation));'''
new_list = '''  const conversationsWithUnread = await attachConversationUnreadCounts(conversations, req.user.id);
  const conversationsWithOwners = await attachConversationOwners(conversationsWithUnread);
  res.json(conversationsWithOwners.map(sanitizeConversation));'''
if "conversationsWithOwners" not in route:
    if old_list not in route:
        raise SystemExit(f"{PATCH}: conversation list anchor missing")
    route = route.replace(old_list, new_list, 1)

old_created_safe = '''  const safe = sanitizeConversation({ ...conversation, unreadCount: 0 });
  await logChatAudit({ action: "CONVERSATION_CREATED", actorId: req.user.id, message: { conversationId: conversation.id }, metadata: { name, type: "GROUP", membersCount: String(memberIds.length) } });'''
new_created_safe = '''  const safe = sanitizeConversation({ ...conversation, unreadCount: 0, ownerId: req.user.id });
  await logChatAudit({ action: "CONVERSATION_CREATED", actorId: req.user.id, message: { conversationId: conversation.id }, metadata: { name, type: "GROUP", membersCount: String(memberIds.length) } });'''
if "ownerId: req.user.id" not in route:
    if old_created_safe not in route:
        raise SystemExit(f"{PATCH}: group create safe anchor missing")
    route = route.replace(old_created_safe, new_created_safe, 1)

group_route_anchor = '''  for (const member of conversation.members) emitToRoom(req, `user:${member.userId}`, "conversation:created", safe);
  res.json(safe);
}));

router.get("/bookmarks", asyncHandler(async (req, res) => {'''

group_manage_route = '''  for (const member of conversation.members) emitToRoom(req, `user:${member.userId}`, "conversation:created", safe);
  res.json(safe);
}));

router.patch("/conversations/:conversationId/group", asyncHandler(async (req, res) => {
  const conversationId = required(req.params.conversationId, "conversationId");
  const existing = await assertConversationAccess(req.user, conversationId);
  if (existing.type !== "GROUP") throw new AppError("Only group conversations can be managed here", 400);

  const ownerId = await resolveGroupOwnerId(existing);
  if (!ownerId) throw new AppError("Group owner could not be resolved", 409);
  if (!isSystemAdmin(req.user) && ownerId !== req.user.id) throw new AppError("Only the group owner can manage members or name", 403);

  const data = {};
  if (req.body.name !== undefined) {
    const nextName = optionalString(req.body.name);
    if (!nextName) throw new AppError("Group name is required", 400);
    data.name = nextName.slice(0, 120);
  }

  let desiredMemberIds = existing.members.map((member) => member.userId);
  if (req.body.memberUserIds !== undefined) {
    const requestedIds = listBodyIds(req.body.memberUserIds).filter((userId) => userId !== ownerId);
    if (requestedIds.length < 2) throw new AppError("Group chat requires at least two other users", 400);

    const validUsers = await prisma.user.findMany({
      where: {
        id: { in: requestedIds },
        status: "ACTIVE",
        role: { in: ["SUPER_ADMIN", "ADMIN", "MANAGER", "PROJECT_MANAGER", "TEAM_MEMBER"] },
      },
      select: { id: true },
    });
    if (validUsers.length !== requestedIds.length) throw new AppError("Every group member must be an active internal user", 400);
    desiredMemberIds = [ownerId, ...validUsers.map((item) => item.id)];
  }

  if (!Object.keys(data).length && req.body.memberUserIds === undefined) {
    throw new AppError("No group changes supplied", 400);
  }

  const oldMemberIds = existing.members.map((member) => member.userId);
  const removedMemberIds = oldMemberIds.filter((userId) => !desiredMemberIds.includes(userId));
  const updated = await prisma.$transaction(async (tx) => {
    if (req.body.memberUserIds !== undefined) {
      await tx.conversationMember.deleteMany({
        where: { conversationId, userId: { notIn: desiredMemberIds } },
      });
      await tx.conversationMember.createMany({
        data: desiredMemberIds.map((userId) => ({ conversationId, userId })),
        skipDuplicates: true,
      });
    }
    return tx.conversation.update({
      where: { id: conversationId },
      data,
      include: {
        members: { include: { user: { select: { id: true, name: true, email: true, role: true, department: true, jobTitle: true, phone: true, avatarUrl: true, statusMessage: true, presenceStatus: true, lastSeenAt: true } } } },
        messages: { include: messageInclude, orderBy: { createdAt: "desc" }, take: 1 },
      },
    });
  });

  const safe = sanitizeConversation({ ...updated, ownerId, unreadCount: 0 });
  const io = req.app.get("io");
  for (const userId of removedMemberIds) {
    emitToRoom(req, `user:${userId}`, "conversation:removed", { id: conversationId });
    io?.in(`user:${userId}`)?.socketsLeave?.(`conversation:${conversationId}`);
  }
  for (const member of updated.members) emitToRoom(req, `user:${member.userId}`, "conversation:updated", safe);

  await logChatAudit({
    action: "MODERATION_ACTION",
    actorId: req.user.id,
    message: { conversationId },
    metadata: {
      operation: "GROUP_UPDATED",
      name: updated.name || "",
      membersCount: String(updated.members.length),
      removedMemberIds,
    },
  });

  res.json(safe);
}));

router.get("/bookmarks", asyncHandler(async (req, res) => {'''

if 'router.patch("/conversations/:conversationId/group"' not in route:
    if group_route_anchor not in route:
        raise SystemExit(f"{PATCH}: group management insertion anchor missing")
    route = route.replace(group_route_anchor, group_manage_route, 1)

# ---------------- frontend API ----------------
api_anchor = '''    createGroup: (payload) => request("/api/chat/conversations/group", { method: "POST", body: JSON.stringify(payload) }),'''
if "updateGroup:" not in api:
    if api_anchor not in api:
        raise SystemExit(f"{PATCH}: api createGroup anchor missing")
    api = api.replace(api_anchor, api_anchor + '''
    updateGroup: (conversationId, payload) => request(`/api/chat/conversations/${conversationId}/group`, { method: "PATCH", body: JSON.stringify(payload) }),''', 1)

# ---------------- frontend UI/state ----------------
state_anchor = '''  const [startingDirectUserId, setStartingDirectUserId] = useState("");'''
if "creatingGroup" not in chat:
    if state_anchor not in chat:
        raise SystemExit(f"{PATCH}: group state anchor missing")
    chat = chat.replace(state_anchor, state_anchor + '''
  const [creatingGroup, setCreatingGroup] = useState(false);
  const [groupManageName, setGroupManageName] = useState("");
  const [groupManageMemberIds, setGroupManageMemberIds] = useState([]);
  const [groupManageSaving, setGroupManageSaving] = useState(false);''', 1)

# Derived active group/manage permission.
derived_anchor = '''  const activeConversation = conversations.find((conversation) => conversation.id === activeConversationId);
  const availableDirectUsers = useMemo(() => directUsers.filter((item) => item.id !== user?.id), [directUsers, user?.id]);'''
derived_new = '''  const activeConversation = conversations.find((conversation) => conversation.id === activeConversationId);
  const isActiveGroup = Boolean(isDirectMode && activeConversation?.type === "GROUP");
  const canManageActiveGroup = Boolean(isActiveGroup && (activeConversation?.ownerId === user?.id || isSystemAdmin(user)));
  const availableDirectUsers = useMemo(() => directUsers.filter((item) => item.id !== user?.id), [directUsers, user?.id]);'''
if "const isActiveGroup =" not in chat:
    if derived_anchor not in chat:
        raise SystemExit(f"{PATCH}: activeConversation anchor missing")
    chat = chat.replace(derived_anchor, derived_new, 1)

# Hydrate group management form.
hydrate_anchor = '''  useEffect(() => {
    setMobileWorkspaceTab("chat");
  }, [isDirectMode, activeChannelId, activeConversationId]);'''
hydrate_new = '''  useEffect(() => {
    setMobileWorkspaceTab("chat");
  }, [isDirectMode, activeChannelId, activeConversationId]);

  useEffect(() => {
    if (!isActiveGroup || !activeConversation) {
      setGroupManageName("");
      setGroupManageMemberIds([]);
      return;
    }
    setGroupManageName(activeConversation.name || "");
    setGroupManageMemberIds((activeConversation.members || []).map((member) => member.userId || member.user?.id).filter(Boolean));
  }, [isActiveGroup, activeConversationId, activeConversation?.name, activeConversation?.updatedAt]);'''
if "setGroupManageName(activeConversation.name" not in chat:
    if hydrate_anchor not in chat:
        raise SystemExit(f"{PATCH}: group hydrate anchor missing")
    chat = chat.replace(hydrate_anchor, hydrate_new, 1)

# Group create: guard + active mode/open.
old_submit = '''  async function submitGroupConversation(event) {
    event.preventDefault();
    if (!canDirectChat || groupMemberIds.length < 2) {
      setLocalError("اختر عضوين على الأقل للمحادثة الجماعية.");
      return;
    }
    try {
      setLocalError("");
      const conversation = await api.chat.createGroup({ name: newGroupName.trim() || "Group chat", memberUserIds: groupMemberIds });
      setConversations((prev) => upsertById(prev, conversation));
      closeHuddle();
      setActiveConversationId(conversation.id);
      setNewGroupName("");
      setGroupMemberIds([]);
      setShowNewGroup(false);
      resetMessageContext();
    } catch (err) {
      setLocalError(getErrorMessage(err, "تعذر إنشاء المحادثة الجماعية."));
    }
  }'''

new_submit = '''  async function submitGroupConversation(event) {
    event.preventDefault();
    if (!canDirectChat || creatingGroup || groupMemberIds.length < 2) {
      if (groupMemberIds.length < 2) setLocalError(lang === "en" ? "Choose at least two teammates." : "اختر عضوين على الأقل للمحادثة الجماعية.");
      return;
    }
    try {
      setCreatingGroup(true);
      setLocalError("");
      const conversation = await api.chat.createGroup({ name: newGroupName.trim() || (lang === "en" ? "Group chat" : "مجموعة جديدة"), memberUserIds: groupMemberIds });
      setConversations((prev) => upsertById(prev, conversation));
      closeHuddle();
      setMode("direct");
      setActiveConversationId(conversation.id);
      setNewGroupName("");
      setGroupMemberIds([]);
      setShowNewGroup(false);
      setShowV8NewConversation(false);
      resetMessageContext();
      setLocalSuccess(lang === "en" ? "Group created." : "تم إنشاء المجموعة.");
    } catch (err) {
      setLocalError(getErrorMessage(err, lang === "en" ? "Could not create the group." : "تعذر إنشاء المحادثة الجماعية."));
    } finally {
      setCreatingGroup(false);
    }
  }

  async function saveActiveGroupSettings(event) {
    event?.preventDefault?.();
    if (!canManageActiveGroup || !activeConversation?.id || groupManageSaving) return;
    const ownerId = activeConversation.ownerId || "";
    const otherMemberIds = [...new Set(groupManageMemberIds)].filter((id) => id && id !== ownerId);
    if (otherMemberIds.length < 2) {
      setLocalError(lang === "en" ? "A group needs at least two members besides the owner." : "المجموعة تحتاج عضوين على الأقل غير المالك.");
      return;
    }
    try {
      setGroupManageSaving(true);
      setLocalError("");
      const updated = await api.chat.updateGroup(activeConversation.id, {
        name: groupManageName.trim() || (lang === "en" ? "Group chat" : "مجموعة"),
        memberUserIds: otherMemberIds,
      });
      setConversations((prev) => upsertById(prev, updated));
      setLocalSuccess(lang === "en" ? "Group updated." : "تم تحديث المجموعة.");
    } catch (err) {
      setLocalError(getErrorMessage(err, lang === "en" ? "Could not update the group." : "تعذر تحديث المجموعة."));
    } finally {
      setGroupManageSaving(false);
    }
  }

  function toggleManagedGroupMember(userId) {
    if (!userId || userId === activeConversation?.ownerId) return;
    setGroupManageMemberIds((prev) => prev.includes(userId) ? prev.filter((id) => id !== userId) : [...prev, userId]);
  }'''

if "async function saveActiveGroupSettings(" not in chat:
    if old_submit not in chat:
        raise SystemExit(f"{PATCH}: submitGroupConversation anchor missing")
    chat = chat.replace(old_submit, new_submit, 1)

# Realtime conversation update/remove.
socket_anchor = '''    const onConversationCreated = (conversation) => {
      setConversations((prev) => upsertById(prev, { ...conversation, unreadCount: conversation.unreadCount || 0 }));
    };'''
socket_new = '''    const onConversationCreated = (conversation) => {
      setConversations((prev) => upsertById(prev, { ...conversation, unreadCount: conversation.unreadCount || 0 }));
    };
    const onConversationUpdated = (conversation) => {
      if (!conversation?.id) return;
      setConversations((prev) => upsertById(prev, conversation));
    };
    const onConversationRemoved = ({ id } = {}) => {
      if (!id) return;
      setConversations((prev) => prev.filter((conversation) => conversation.id !== id));
      if (id === activeConversationId) {
        setActiveConversationId("");
        resetMessageContext();
        setDetailsPanelOpen(false);
      }
    };'''
if "const onConversationUpdated =" not in chat:
    if socket_anchor not in chat:
        raise SystemExit(f"{PATCH}: conversation socket anchor missing")
    chat = chat.replace(socket_anchor, socket_new, 1)

socket_on_anchor = '''    socket.on("conversation:created", onConversationCreated);
    socket.on("message:new", onNewMessage);'''
socket_on_new = '''    socket.on("conversation:created", onConversationCreated);
    socket.on("conversation:updated", onConversationUpdated);
    socket.on("conversation:removed", onConversationRemoved);
    socket.on("message:new", onNewMessage);'''
if 'socket.on("conversation:updated"' not in chat:
    chat = chat.replace(socket_on_anchor, socket_on_new, 1)

socket_off_anchor = '''      socket.off("conversation:created", onConversationCreated);
      socket.off("message:new", onNewMessage);'''
socket_off_new = '''      socket.off("conversation:created", onConversationCreated);
      socket.off("conversation:updated", onConversationUpdated);
      socket.off("conversation:removed", onConversationRemoved);
      socket.off("message:new", onNewMessage);'''
if 'socket.off("conversation:updated"' not in chat:
    chat = chat.replace(socket_off_anchor, socket_off_new, 1)

# Creation form marker + loading/selected count.
group_form_old = '''              {showNewGroup && (
                <form onSubmit={submitGroupConversation} className="rounded-2xl border border-white/10 bg-white/5 p-3">'''
group_form_new = '''              {showNewGroup && (
                <form data-tcs-group-chat-flow="v1" onSubmit={submitGroupConversation} className="rounded-2xl border border-white/10 bg-white/5 p-3">'''
if 'data-tcs-group-chat-flow="v1"' not in chat:
    if group_form_old not in chat:
        raise SystemExit(f"{PATCH}: group form anchor missing")
    chat = chat.replace(group_form_old, group_form_new, 1)

group_button_old = '''                  <button type="submit" disabled={groupMemberIds.length < 2} className="mt-3 w-full rounded-xl bg-amber-400 px-3 py-2 text-xs font-black text-zinc-950 disabled:opacity-50">{ui.createGroup}</button>'''
group_button_new = '''                  <div className="mt-2 text-[10px] text-zinc-400">{lang === "en" ? `${groupMemberIds.length} selected` : `تم اختيار ${groupMemberIds.length}`}</div>
                  <button type="submit" disabled={creatingGroup || groupMemberIds.length < 2} className="mt-2 w-full rounded-xl bg-amber-400 px-3 py-2 text-xs font-black text-zinc-950 disabled:opacity-50">{creatingGroup ? (lang === "en" ? "Creating..." : "جاري الإنشاء...") : ui.createGroup}</button>'''
if "creatingGroup ? (lang ===" not in chat:
    if group_button_old not in chat:
        raise SystemExit(f"{PATCH}: group button anchor missing")
    chat = chat.replace(group_button_old, group_button_new, 1)

# Group badge in conversation list.
title_old = '''                        <span className="tcs-v4-conversation-title" title={title}>{title}</span>'''
title_new = '''                        <span className="tcs-v4-conversation-title" title={title}>{title}{conversation.type === "GROUP" && <span className="ms-1 text-[9px] text-amber-300"> · {lang === "en" ? "Group" : "مجموعة"}</span>}</span>'''
if 'conversation.type === "GROUP"' not in chat:
    chat = chat.replace(title_old, title_new, 1)

# Group manager inside Members inspector.
members_head = '''              <div className="space-y-2">
                {currentChatMembers.slice(0, 12).map((member) => ('''
manager_ui = '''              {isActiveGroup && canManageActiveGroup && (
                <form onSubmit={saveActiveGroupSettings} className="mb-3 rounded-2xl border border-amber-100 bg-amber-50/60 p-3 dark:border-amber-500/20 dark:bg-amber-500/10">
                  <div className="mb-2 text-xs font-black text-amber-800 dark:text-amber-100">{lang === "en" ? "Group settings" : "إعدادات المجموعة"}</div>
                  <input value={groupManageName} onChange={(event) => setGroupManageName(event.target.value)} maxLength={120} className="w-full rounded-xl border border-amber-100 bg-white px-3 py-2 text-xs text-zinc-800 outline-none focus:border-amber-300 dark:border-amber-500/20 dark:bg-zinc-950 dark:text-white" placeholder={lang === "en" ? "Group name" : "اسم المجموعة"} />
                  <div className="mt-2 max-h-40 space-y-1 overflow-y-auto rounded-xl bg-white/80 p-2 dark:bg-zinc-950/70">
                    {allInternalMembers.map((member) => {
                      const isOwner = member.id === activeConversation?.ownerId;
                      return (
                        <label key={member.id} className="flex items-center gap-2 rounded-lg px-2 py-1 text-[11px] text-zinc-600 dark:text-zinc-300">
                          <input type="checkbox" checked={groupManageMemberIds.includes(member.id)} disabled={isOwner} onChange={() => toggleManagedGroupMember(member.id)} />
                          <span className="min-w-0 flex-1 truncate">{member.name || member.email}</span>
                          {isOwner && <span className="text-[9px] font-black text-amber-700 dark:text-amber-200">{lang === "en" ? "Owner" : "المالك"}</span>}
                        </label>
                      );
                    })}
                  </div>
                  <button type="submit" disabled={groupManageSaving || groupManageMemberIds.filter((id) => id !== activeConversation?.ownerId).length < 2} className="mt-2 w-full rounded-xl bg-zinc-950 px-3 py-2 text-[11px] font-black text-white disabled:opacity-50 dark:bg-white dark:text-zinc-950">
                    {groupManageSaving ? (lang === "en" ? "Saving..." : "جاري الحفظ...") : (lang === "en" ? "Save group" : "حفظ المجموعة")}
                  </button>
                </form>
              )}
              <div className="space-y-2">
                {currentChatMembers.slice(0, 12).map((member) => ('''
if "saveActiveGroupSettings" in chat and "Group settings" not in chat:
    if members_head not in chat:
        raise SystemExit(f"{PATCH}: members inspector anchor missing")
    chat = chat.replace(members_head, manager_ui, 1)

CHAT.write_text(chat, encoding="utf-8")
API.write_text(api, encoding="utf-8")
ROUTE.write_text(route, encoding="utf-8")

print(f"PATCH={PATCH}")
print("GROUP_CREATE=HARDENED")
print("GROUP_OPEN=YES")
print("GROUP_RENAME=YES")
print("GROUP_ADD_REMOVE_MEMBERS=YES")
print("GROUP_OWNER_GUARD=YES")
print("GROUP_REALTIME_SYNC=YES")
print("REMOVED_MEMBER_SOCKET_REVOKE=YES")
print("DB_SCHEMA_UNCHANGED=YES")
print(f"BACKUP={backup}")
print("NEXT=BUILD_VERIFY_DEPLOY")
