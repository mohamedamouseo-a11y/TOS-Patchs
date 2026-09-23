#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import shutil
import sys

PATCH = "TCS-TASKS-PINS-DECISIONS-FLOW-V1"
ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS").resolve()
CHAT = ROOT / "frontend/src/components/ChatPanel.jsx"
HOOK = ROOT / "frontend/src/hooks/useChat.js"
API = ROOT / "frontend/src/lib/api.js"
ROUTE = ROOT / "backend/src/routes/chat.routes.js"

for path in (CHAT, HOOK, API, ROUTE):
    if not path.exists():
        raise SystemExit(f"{PATCH}: missing {path}")

backup = Path("/tmp") / f"{PATCH}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
backup.mkdir(parents=True, exist_ok=True)
for path in (CHAT, HOOK, API, ROUTE):
    shutil.copy2(path, backup / path.name)

api = API.read_text(encoding="utf-8")
old = '    toTask: (messageId, title = "") =>'
pos = api.find(old)
if pos >= 0:
    line_end = api.find("\n", pos)
    api = api[:pos] + '    toTask: (messageId, payload = {}) => request("/api/chat/messages/" + messageId + "/to-task", { method: "POST", body: JSON.stringify(typeof payload === "string" ? { title: payload } : payload) }),' + api[line_end:]
if "tasks: (filters = {})" not in api:
    pos = api.find('    decisions: (filters = {}) =>')
    if pos < 0:
        raise SystemExit(f"{PATCH}: api decisions anchor missing")
    api = api[:pos] + '    tasks: (filters = {}) => request("/api/chat/tasks" + queryString(filters)),\n' + api[pos:]
API.write_text(api, encoding="utf-8")

hook = HOOK.read_text(encoding="utf-8")
hook = hook.replace('async function convertToTask(messageId, title = "")', 'async function convertToTask(messageId, payload = {})', 1)
hook = hook.replace('api.chat.toTask(messageId, title)', 'api.chat.toTask(messageId, payload)', 1)
HOOK.write_text(hook, encoding="utf-8")

route = ROUTE.read_text(encoding="utf-8")

if "function safeChatTaskPayload(" not in route:
    anchor = "function emitToBoard(req, boardId, event, payload) {"
    idx = route.find(anchor)
    if idx < 0:
        raise SystemExit(f"{PATCH}: backend task helper anchor missing")
    helper = '''function safeChatTaskPayload(task) {
  if (!task) return null;
  return {
    id: task.id,
    title: task.title,
    status: task.status,
    priority: task.priority,
    projectId: task.projectId || null,
    boardId: task.boardId || null,
    listId: task.listId || null,
    assigneeId: task.assigneeId || null,
    assignee: task.assignee ? sanitizeChatUser(task.assignee) : null,
    dueDate: task.dueDate || null,
    createdById: task.createdById || null,
    createdAt: task.createdAt,
    updatedAt: task.updatedAt,
  };
}

'''
    route = route[:idx] + helper + route[idx:]

if 'router.get("/tasks", asyncHandler' not in route:
    idx = route.find('router.get("/decisions", asyncHandler')
    if idx < 0:
        raise SystemExit(f"{PATCH}: backend decisions anchor missing")
    block = '''router.get("/tasks", asyncHandler(async (req, res) => {
  const projectId = optionalString(req.query.projectId);
  const conversationId = optionalString(req.query.conversationId);
  const channelId = optionalString(req.query.channelId);
  const resolved = await resolveChatScopeForRequest(req.user, { projectId, channelId, conversationId });
  const linkedMessages = await prisma.message.findMany({
    where: { ...resolved.where, deletedAt: null, convertedTaskId: { not: null } },
    include: messageInclude,
    orderBy: { createdAt: "desc" },
    take: clampNumber(req.query.limit, 1, 100, 50),
  });
  const taskIds = [...new Set(linkedMessages.map((message) => message.convertedTaskId).filter(Boolean))];
  const tasks = taskIds.length ? await prisma.task.findMany({
    where: { id: { in: taskIds }, archivedAt: null },
    include: { assignee: true },
  }) : [];
  const byId = new Map(tasks.map((task) => [task.id, task]));
  res.json(linkedMessages.map((message) => ({
    message: sanitizeMessage(message),
    task: safeChatTaskPayload(byId.get(message.convertedTaskId)),
  })).filter((item) => item.task));
}));

'''
    route = route[:idx] + block + route[idx:]

pin_anchor = 'router.patch("/messages/:messageId/pin", asyncHandler(async (req, res) => {'
idx = route.find(pin_anchor)
if idx >= 0 and "Cannot pin a deleted message" not in route[idx:idx+1000]:
    msg_line = route.find("\n", route.find("const message =", idx))
    route = route[:msg_line+1] + '  if (message.deletedAt) throw new AppError("Cannot pin a deleted message", 400);\n' + route[msg_line+1:]

start = route.find('router.post("/messages/:messageId/to-task", asyncHandler')
end = route.find('router.get("/messages/:messageId/thread"', start)
if start < 0 or end < 0:
    raise SystemExit(f"{PATCH}: backend to-task bounds missing")
task_route = '''router.post("/messages/:messageId/to-task", asyncHandler(async (req, res) => {
  const message = await assertMessageAccess(req.user, required(req.params.messageId, "messageId"));
  await assertCanWorkInMessageProject(req.user, message);

  const fullMessage = await prisma.message.findUnique({ where: { id: message.id }, include: { user: true } });
  if (!fullMessage || fullMessage.deletedAt) throw new AppError("Message not found", 404);

  if (fullMessage.convertedTaskId) {
    const existingTask = await prisma.task.findUnique({ where: { id: fullMessage.convertedTaskId }, include: { assignee: true } });
    if (existingTask) {
      const currentMessage = await getMessageForResponse(fullMessage.id);
      return res.json({ task: safeChatTaskPayload(existingTask), message: sanitizeMessage(currentMessage), alreadyConverted: true });
    }
  }

  const title = optionalString(req.body.title) || fullMessage.body.replace(/\\s+/g, " ").slice(0, 120) || "Task from chat";
  const priority = enumValue(req.body.priority, ["LOW", "MEDIUM", "HIGH", "URGENT"], "MEDIUM");
  const dueDate = req.body.dueDate ? safeDate(req.body.dueDate) : null;
  if (req.body.dueDate && !dueDate) throw new AppError("Invalid due date", 400);

  const boardData = await assertBoardForMessageTask(req.user, fullMessage.projectId, optionalString(req.body.boardId));
  const board = boardData.board;
  const list = boardData.list;
  const requestedAssigneeId = optionalString(req.body.assigneeId);
  let assigneeId = null;

  if (requestedAssigneeId) {
    const boardMember = await prisma.boardMember.findFirst({
      where: { boardId: board.id, userId: requestedAssigneeId },
      select: { id: true },
    });
    if (!boardMember) throw new AppError("Selected assignee is not a member of this project board", 400);
    assigneeId = requestedAssigneeId;
  } else {
    const creatorBoardMember = await prisma.boardMember.findFirst({
      where: { boardId: board.id, userId: req.user.id },
      select: { id: true },
    });
    assigneeId = creatorBoardMember ? req.user.id : null;
  }

  const status = list?.status || "BACKLOG";
  const positionResult = await prisma.task.aggregate({
    where: { projectId: fullMessage.projectId, boardId: board.id, listId: list?.id || null, status },
    _max: { position: true },
  });

  const task = await prisma.task.create({
    data: {
      title,
      description: sanitizeRichText("تم إنشاء هذه المهمة من رسالة في الشات.<br><br><strong>المرسل:</strong> " + (fullMessage.user?.name || fullMessage.userId) + "<br><strong>الرسالة:</strong> " + fullMessage.body),
      projectId: fullMessage.projectId,
      boardId: board.id,
      listId: list?.id || null,
      assigneeId,
      dueDate,
      createdById: req.user.id,
      status,
      priority,
      serviceType: "OTHER",
      position: (positionResult._max.position || 0) + 1000,
    },
    include: { assignee: true },
  });

  const updated = await prisma.message.update({
    where: { id: fullMessage.id },
    data: { convertedTaskId: task.id },
    include: messageInclude,
  });
  const safe = sanitizeMessage(updated);
  await emitToMessageAudience(req, updated, "message:updated", safe);
  emitToBoard(req, board.id, "task:created", safeTaskSocketPayload(task));
  res.json({ task: safeChatTaskPayload(task), message: safe, alreadyConverted: false });
}));

'''
route = route[:start] + task_route + route[end:]
ROUTE.write_text(route, encoding="utf-8")

chat = CHAT.read_text(encoding="utf-8")

if "function mergeActionMessages(" not in chat:
    idx = chat.find("function isUnreadMessage(")
    if idx < 0:
        raise SystemExit(f"{PATCH}: merge helper anchor missing")
    helper = '''function mergeActionMessages(...lists) {
  const merged = new Map();
  for (const list of lists) {
    for (const message of list || []) {
      if (!message?.id || message.deletedAt) continue;
      merged.set(message.id, { ...merged.get(message.id), ...message });
    }
  }
  return Array.from(merged.values()).sort((a, b) => new Date(b.decision?.updatedAt || b.pinnedAt || b.updatedAt || b.createdAt || 0) - new Date(a.decision?.updatedAt || a.pinnedAt || a.updatedAt || a.createdAt || 0));
}

'''
    chat = chat[:idx] + helper + chat[idx:]

chat = chat.replace("canManageChat = false, isOwner = false", "canManageChat = false, canPin = false, isOwner = false", 1)
chat = chat.replace('{canManageChat && <button type="button" onClick={() => onPin(message)}', '{canPin && <button type="button" onClick={() => onPin(message)}', 1)
chat = chat.replace('<button type="button" onClick={() => onDecision(message)} className={actionClass}>قرار</button>', '<button type="button" onClick={() => onDecision(message)} className={actionClass}>{message.decision ? (currentChatLang() === "en" ? "Remove decision" : "إلغاء القرار") : (currentChatLang() === "en" ? "Decision" : "قرار")}</button>', 1)

state_anchor = '  const [localDecisionMessages, setLocalDecisionMessages] = useState([]);'
if "serverChatTasks" not in chat:
    idx = chat.find(state_anchor)
    if idx < 0:
        raise SystemExit(f"{PATCH}: state anchor missing")
    idx = chat.find("\n", idx) + 1
    state = '''  const [serverChatTasks, setServerChatTasks] = useState([]);
  const [serverDecisions, setServerDecisions] = useState([]);
  const [actionCenterLoading, setActionCenterLoading] = useState(false);
  const [actionPendingKey, setActionPendingKey] = useState("");
  const [taskSaving, setTaskSaving] = useState(false);
'''
    chat = chat[:idx] + state + chat[idx:]

perm_anchor = '  const canReactInActiveScope = canSend && (!activeChannelMemberReactDisabled || canManageChat || isDirectMode) && roleCanReact;'
if "canPinInActiveScope" not in chat:
    idx = chat.find(perm_anchor)
    if idx < 0:
        raise SystemExit(f"{PATCH}: pin permission anchor missing")
    idx = chat.find("\n", idx) + 1
    chat = chat[:idx] + '  const canPinInActiveScope = isDirectMode ? canDirectChat && Boolean(activeConversationId) : canManageChat;\n' + chat[idx:]

if "resolvedDecisionLogMessages" not in chat:
    idx = chat.find("  const decisionLogMessages = useMemo(")
    if idx < 0:
        raise SystemExit(f"{PATCH}: decision list anchor missing")
    idx = chat.find("\n", idx) + 1
    derived = '''  const resolvedDecisionLogMessages = useMemo(() => mergeActionMessages(
    fullPins,
    serverDecisions.map((decision) => decision?.message ? { ...decision.message, decision } : null).filter(Boolean),
    decisionLogMessages
  ), [fullPins, serverDecisions, decisionLogMessages]);
'''
    chat = chat[:idx] + derived + chat[idx:]

if "async function loadActionCenter()" not in chat:
    idx = chat.find("  async function loadScopedFiles()")
    if idx < 0:
        raise SystemExit(f"{PATCH}: load action anchor missing")
    fn = '''  async function loadActionCenter() {
    const filters = isDirectMode ? { conversationId: activeConversationId } : { projectId, channelId: activeChannelId || "" };
    if ((isDirectMode && !activeConversationId) || (!isDirectMode && !projectId)) {
      setServerChatTasks([]);
      setServerDecisions([]);
      return;
    }
    try {
      setActionCenterLoading(true);
      const results = await Promise.all([api.chat.tasks(filters), api.chat.decisions(filters)]);
      setServerChatTasks(Array.isArray(results[0]) ? results[0] : []);
      setServerDecisions(Array.isArray(results[1]) ? results[1] : []);
    } catch {
      setServerChatTasks([]);
      setServerDecisions([]);
    } finally {
      setActionCenterLoading(false);
    }
  }

'''
    chat = chat[:idx] + fn + chat[idx:]

old_effect = '''  useEffect(() => {
    loadFullPins();
    loadScopedFiles();
  }, [isDirectMode, activeConversationId, activeChannelId, projectId]);'''
new_effect = '''  useEffect(() => {
    loadFullPins();
    loadScopedFiles();
    loadActionCenter();
  }, [isDirectMode, activeConversationId, activeChannelId, projectId]);'''
if old_effect in chat:
    chat = chat.replace(old_effect, new_effect, 1)

start = chat.find("  async function handlePin(message) {")
end = chat.find("  function toggleMessageSelection(message)", start)
if start < 0 or end < 0:
    raise SystemExit(f"{PATCH}: action handler bounds missing")
handlers = '''  async function handlePin(message) {
    if (!message?.id || actionPendingKey) return;
    if (!canPinInActiveScope) {
      setLocalError(lang === "en" ? "You cannot pin messages in this chat." : "لا تملك صلاحية تثبيت الرسائل في هذا الشات.");
      return;
    }
    try {
      setActionPendingKey("pin:" + message.id);
      setLocalError("");
      await pinMessage(message.id, !message.isPinned);
      await loadFullPins();
      setLocalSuccess(message.isPinned ? (lang === "en" ? "Message unpinned." : "تم إلغاء تثبيت الرسالة.") : (lang === "en" ? "Message pinned." : "تم تثبيت الرسالة."));
    } catch (err) {
      setLocalError(getErrorMessage(err, lang === "en" ? "Could not update pin." : "تعذر تحديث التثبيت."));
    } finally {
      setActionPendingKey("");
    }
  }

  async function pinSelectedMessages() {
    if (!canPinInActiveScope || !selectedMessages.length || actionPendingKey) return;
    const candidates = selectedMessages.filter((message) => !message.isPinned && !message.deletedAt);
    if (!candidates.length) return;
    try {
      setActionPendingKey("bulk-pin");
      for (const message of candidates) await pinMessage(message.id, true);
      await loadFullPins();
      clearSelectionMode();
      setLocalSuccess(lang === "en" ? "Selected messages pinned." : "تم تثبيت الرسائل المحددة.");
    } catch (err) {
      setLocalError(getErrorMessage(err, lang === "en" ? "Could not pin selected messages." : "تعذر تثبيت بعض الرسائل."));
    } finally {
      setActionPendingKey("");
    }
  }

  function handleConvertToTask(message) {
    if (!message?.id || message.deletedAt) return;
    if (!message.projectId) {
      setLocalError(lang === "en" ? "Tasks can be created from project chat messages only." : "إنشاء Task متاح من رسائل شات المشروع فقط.");
      return;
    }
    if (message.convertedTaskId) {
      setDetailsPanelOpen(true);
      setDetailsTab("tasks");
      loadActionCenter();
      setLocalSuccess(lang === "en" ? "This message is already linked to a task." : "الرسالة مرتبطة بالفعل بمهمة.");
      return;
    }
    openLocalTaskModal(message);
  }

  function copyMessageText(message) { navigator.clipboard?.writeText(message.body || ""); setLocalSuccess("تم نسخ الرسالة."); }

  async function markMessageDecision(message, tag = "Decision") {
    if (!message?.id || actionPendingKey) return;
    const typeMap = { Decision: "DECISION", Important: "IMPORTANT", "Follow-up": "FOLLOW_UP", Blocker: "BLOCKER" };
    const removing = Boolean(message.decision);
    try {
      setActionPendingKey("decision:" + message.id);
      setLocalError("");
      await markDecision(message.id, removing ? { enabled: false } : {
        type: typeMap[tag] || "DECISION",
        title: truncateMessagePreview(message.body || "قرار من الشات", 90),
        enabled: true,
      });
      setLocalDecisionMessages((prev) => prev.filter((item) => item.messageId !== message.id));
      setLocalSuccess(removing ? (lang === "en" ? "Decision removed." : "تم إلغاء القرار.") : (lang === "en" ? "Decision saved." : "تم حفظ القرار."));
      await loadActionCenter();
      loadChatInsights();
    } catch (err) {
      if (!removing) {
        setLocalDecisionMessages((prev) => prev.some((item) => item.messageId === message.id) ? prev : [{ messageId: message.id, tag, createdAt: new Date().toISOString() }, ...prev]);
      }
      setLocalError(getErrorMessage(err, removing ? "تعذر إلغاء القرار." : "تعذر حفظ القرار."));
    } finally {
      setActionPendingKey("");
    }
    setDetailsPanelOpen(true);
    setDetailsTab("pins");
  }

  function openLocalTaskModal(message) {
    setTaskDraftMessage(message);
    setTaskDraft({
      title: truncateMessagePreview(message.body || "مهمة من الشات", 70),
      assignee: currentChatMembers.some((member) => member.id === user?.id) ? user.id : "",
      dueDate: "",
      priority: "MEDIUM",
    });
  }

  async function saveLocalTaskDraft(event) {
    event?.preventDefault?.();
    if (!taskDraftMessage?.id || taskSaving || !taskDraft.title.trim()) return;
    try {
      setTaskSaving(true);
      setLocalError("");
      const result = await convertToTask(taskDraftMessage.id, {
        title: taskDraft.title.trim(),
        assigneeId: taskDraft.assignee || undefined,
        dueDate: taskDraft.dueDate || undefined,
        priority: taskDraft.priority || "MEDIUM",
      });
      setLocalLinkedTasks((prev) => prev.filter((item) => item.messageId !== taskDraftMessage.id));
      setTaskDraftMessage(null);
      setDetailsPanelOpen(true);
      setDetailsTab("tasks");
      await loadActionCenter();
      setLocalSuccess(result?.alreadyConverted ? (lang === "en" ? "Existing task link restored." : "تم استرجاع ربط المهمة الموجودة.") : (lang === "en" ? "Task created from chat." : "تم إنشاء المهمة وربطها بالرسالة."));
    } catch (err) {
      setLocalLinkedTasks((prev) => [{ ...taskDraft, messageId: taskDraftMessage.id, createdAt: new Date().toISOString(), syncFailed: true }, ...prev.filter((item) => item.messageId !== taskDraftMessage.id)]);
      setLocalError(getErrorMessage(err, lang === "en" ? "Task creation failed. A local retry draft was kept." : "تعذر إنشاء المهمة. تم الاحتفاظ بمسودة لإعادة المحاولة."));
    } finally {
      setTaskSaving(false);
    }
  }

'''
chat = chat[:start] + handlers + chat[end:]

chat = chat.replace('await convertToTask(message.id, taskCommandMatch[1].trim());\n          setLocalSuccess("تم إنشاء الرسالة وتحويلها إلى Task.");', 'await convertToTask(message.id, taskCommandMatch[1].trim());\n          await loadActionCenter();\n          setLocalSuccess("تم إنشاء الرسالة وتحويلها إلى Task.");', 1)

call_anchor = '''                    canManageChat={canManageChat}
                    isOwner={isOwner}'''
if "canPin={canPinInActiveScope}" not in chat:
    if call_anchor not in chat:
        raise SystemExit(f"{PATCH}: MessageActions call anchor missing")
    chat = chat.replace(call_anchor, '''                    canManageChat={canManageChat}
                    canPin={canPinInActiveScope}
                    isOwner={isOwner}''', 1)

chat = chat.replace('{canManageChat && <button type="button" onClick={() => handlePin({ ...message, isPinned: true })}', '{canPinInActiveScope && <button type="button" onClick={() => handlePin({ ...message, isPinned: true })}', 1)
chat = chat.replace('onClick={() => scrollToMessage(message.id)} className="rounded-xl bg-amber-100', 'onClick={() => openWorkspaceSearchResult({ targetId: message.id, label: message.body || "Pinned", kind: "pin" })} className="rounded-xl bg-amber-100', 1)

mobile = '<button type="button" onClick={() => { handleConvertToTask(mobileActionMessage); setMobileActionMessage(null); }} className="rounded-2xl bg-emerald-50 px-3 py-2 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-100">Create Task</button>'
if mobile in chat:
    replacement = '{mobileActionMessage.projectId && !mobileActionMessage.convertedTaskId && <button type="button" onClick={() => { handleConvertToTask(mobileActionMessage); setMobileActionMessage(null); }} className="rounded-2xl bg-emerald-50 px-3 py-2 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-100">Create Task</button>}\n              {canPinInActiveScope && <button type="button" onClick={() => { handlePin(mobileActionMessage); setMobileActionMessage(null); }} className="rounded-2xl bg-amber-50 px-3 py-2 text-amber-700 dark:bg-amber-500/10 dark:text-amber-100">{mobileActionMessage.isPinned ? (lang === "en" ? "Unpin" : "إلغاء التثبيت") : (lang === "en" ? "Pin" : "تثبيت")}</button>}'
    chat = chat.replace(mobile, replacement, 1)

modal_start = chat.find("      {taskDraftMessage && (")
modal_end = chat.find("      <HuddlePanel", modal_start)
if modal_start < 0 or modal_end < 0:
    raise SystemExit(f"{PATCH}: task modal bounds missing")
modal = chat[modal_start:modal_end]
modal = modal.replace("مسودة محلية فقط — لم تُحفظ في النظام.", "سيتم إنشاء Task حقيقية في المشروع وربطها بهذه الرسالة.")
modal = modal.replace('{ value: "HIGH", label: "High" }]}', '{ value: "HIGH", label: "High" }, { value: "URGENT", label: "Urgent" }]}', 1)
old_buttons = '<div className="mt-4 grid grid-cols-2 gap-2"><button type="button" onClick={async () => { const message = taskDraftMessage; setTaskDraftMessage(null); if (message) await handleConvertToTask(message); }} className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-black text-amber-800 dark:border-amber-500/20 dark:bg-amber-500/10 dark:text-amber-100">إعادة المحاولة في النظام</button><button type="submit" disabled={!taskDraft.title.trim()} className="rounded-2xl bg-amber-400 px-4 py-3 text-sm font-black text-zinc-950 disabled:opacity-50">حفظ مسودة غير متزامنة</button></div>'
new_buttons = '<div className="mt-4 grid grid-cols-2 gap-2"><button type="button" onClick={() => setTaskDraftMessage(null)} disabled={taskSaving} className="rounded-2xl border border-zinc-200 bg-white px-4 py-3 text-sm font-black text-zinc-600 disabled:opacity-50 dark:border-white/10 dark:bg-zinc-900 dark:text-zinc-300">{lang === "en" ? "Cancel" : "إلغاء"}</button><button type="submit" disabled={taskSaving || !taskDraft.title.trim()} className="rounded-2xl bg-amber-400 px-4 py-3 text-sm font-black text-zinc-950 disabled:opacity-50">{taskSaving ? (lang === "en" ? "Creating..." : "جاري الإنشاء...") : (lang === "en" ? "Create task" : "إنشاء المهمة")}</button></div>'
if old_buttons not in modal:
    raise SystemExit(f"{PATCH}: task modal buttons missing")
modal = modal.replace(old_buttons, new_buttons, 1)
chat = chat[:modal_start] + modal + chat[modal_end:]

panel_start = chat.find('          {detailsTab === "tasks" && (')
panel_end = chat.find('          {detailsTab === "notes" && (', panel_start)
if panel_start < 0 or panel_end < 0:
    raise SystemExit(f"{PATCH}: action panels bounds missing")
panels = '''          {detailsTab === "tasks" && (
            <div data-tcs-action-center-flow="v1" className="tos-chat-detail-card rounded-[18px] border border-zinc-100 bg-white p-2.5 shadow-sm dark:border-white/10 dark:bg-zinc-900 2xl:rounded-[20px] 2xl:p-3">
              <div className="mb-3 flex items-center justify-between gap-2">
                <div className="text-sm font-black text-zinc-950 dark:text-white">{lang === "en" ? "Tasks From Chat" : "مهام من الشات"}</div>
                <span className="rounded-full bg-emerald-50 px-2 py-1 text-[10px] font-black text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-100">{serverChatTasks.length}</span>
              </div>
              <div className="space-y-2">
                {serverChatTasks.slice(0, 20).map((item) => (
                  <button key={item.task?.id || item.message?.id} type="button" onClick={() => openWorkspaceSearchResult({ targetId: item.message?.id, label: item.message?.body || item.task?.title, kind: "task" })} className="block w-full rounded-xl bg-emerald-50 px-2.5 py-2 text-right text-xs text-emerald-900 dark:bg-emerald-500/10 dark:text-emerald-100">
                    <div className="font-black">{item.task?.title || truncateMessagePreview(item.message?.body || "Task", 80)}</div>
                    <div className="mt-1 text-[11px] opacity-75">{item.task?.status || "TASK"} · {item.task?.priority || "MEDIUM"}{item.task?.assignee?.name ? " · " + item.task.assignee.name : ""}{item.task?.dueDate ? " · " + new Date(item.task.dueDate).toLocaleDateString(chatLocale(lang)) : ""}</div>
                  </button>
                ))}
                {localLinkedTasks.filter((task) => task.syncFailed).slice(0, 6).map((task) => (
                  <div key={"local-" + task.messageId} className="rounded-xl border border-amber-100 bg-amber-50 px-2.5 py-2 text-xs text-amber-800 dark:border-amber-500/20 dark:bg-amber-500/10 dark:text-amber-100">
                    <div className="font-black">{task.title}</div>
                    <div className="mt-1 text-[10px] opacity-75">{lang === "en" ? "Sync failed · retry from the source message" : "فشل المزامنة · أعد المحاولة من الرسالة الأصلية"}</div>
                  </div>
                ))}
                {!actionCenterLoading && serverChatTasks.length === 0 && localLinkedTasks.filter((task) => task.syncFailed).length === 0 && <ChatEmptyState title={lang === "en" ? "No linked tasks" : "لا توجد مهام مرتبطة"} description={lang === "en" ? "Use Create Task on a project message to create a real task." : "استخدم Create Task من رسالة داخل المشروع لإنشاء مهمة حقيقية."} />}
                {actionCenterLoading && <div className="rounded-xl bg-zinc-50 px-3 py-2 text-xs text-zinc-400 dark:bg-white/5">{lang === "en" ? "Loading action center..." : "جاري تحميل مركز الإجراءات..."}</div>}
              </div>
            </div>
          )}

          {detailsTab === "pins" && (
            <div className="tos-chat-detail-card rounded-[18px] border border-zinc-100 bg-white p-2.5 shadow-sm dark:border-white/10 dark:bg-zinc-900 2xl:rounded-[20px] 2xl:p-3">
              <div className="mb-3 flex items-center justify-between gap-2">
                <div className="text-sm font-black text-zinc-950 dark:text-white">{lang === "en" ? "Pins / Decisions" : "المثبت / القرارات"}</div>
                <span className="rounded-full bg-amber-50 px-2 py-1 text-[10px] font-black text-amber-700 dark:bg-amber-500/10 dark:text-amber-100">{resolvedDecisionLogMessages.length}</span>
              </div>
              <div className="space-y-2">
                {resolvedDecisionLogMessages.slice(0, 20).map((message) => {
                  const decision = message.decision || localDecisionMessages.find((item) => item.messageId === message.id);
                  const type = decision?.type || decision?.tag || (message.isPinned ? "PINNED" : "DECISION");
                  return (
                    <button key={message.id} type="button" onClick={() => openWorkspaceSearchResult({ targetId: message.id, label: message.body || type, kind: "pin" })} className="block w-full rounded-xl bg-amber-50 px-2.5 py-2 text-right text-xs text-amber-900 dark:bg-amber-500/10 dark:text-amber-100">
                      <div className="flex items-center justify-between gap-2"><b>{type}</b><span>{formatMessageTime(message.createdAt, lang)}</span></div>
                      <div className="mt-1 line-clamp-2">{truncateMessagePreview(message.body || "رسالة", 100)}</div>
                      <div className="mt-1 text-[10px] opacity-65">{message.isPinned ? (lang === "en" ? "Pinned" : "مثبت") : ""}{message.isPinned && decision ? " · " : ""}{decision ? (lang === "en" ? "Decision" : "قرار") : ""}</div>
                    </button>
                  );
                })}
                {!actionCenterLoading && resolvedDecisionLogMessages.length === 0 && <ChatEmptyState title={lang === "en" ? "No pins or decisions" : "لا توجد رسائل مثبتة أو قرارات"} description={lang === "en" ? "Pin an important message or mark it as a decision." : "ثبّت رسالة مهمة أو علّمها كقرار لتظهر هنا من كامل سجل الشات."} />}
              </div>
            </div>
          )}

'''
chat = chat[:panel_start] + panels + chat[panel_end:]
CHAT.write_text(chat, encoding="utf-8")

print(f"PATCH={PATCH}")
print("SERVER_TASK_CENTER=YES")
print("REAL_TASK_MODAL=YES")
print("TASK_IDEMPOTENCY=YES")
print("TASK_ASSIGNEE_DUE_PRIORITY=YES")
print("FULL_HISTORY_PINS_DECISIONS=YES")
print("DECISION_TOGGLE=YES")
print("DIRECT_PIN_PARITY=YES")
print("BULK_PIN_FIXED=YES")
print("DB_SCHEMA_UNCHANGED=YES")
print(f"BACKUP={backup}")
print("NEXT=BUILD_RESTART_BACKEND_DEPLOY")
