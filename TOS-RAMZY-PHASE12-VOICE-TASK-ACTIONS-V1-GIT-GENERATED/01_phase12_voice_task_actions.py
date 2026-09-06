#!/usr/bin/env python3
from pathlib import Path

ROOT = Path('/var/www/TOS')


def read(rel):
    return (ROOT / rel).read_text(encoding='utf-8')


def write(rel, text):
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def replace_once(text, old, new, label):
    if new in text:
        return text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'PHASE12_PATCH_ERROR={label}_COUNT_{count}')
    return text.replace(old, new, 1)


# 1) Semantic intent: CREATE_TASK becomes an approval-supported operation and can resolve assignee names.
rel = 'backend/src/agency-operator/services/semanticIntentResolver.service.js'
text = read(rel)
text = replace_once(
    text,
    'const SUPPORTED_PROPOSAL_OPERATIONS = new Set([\n  "CHANGE_ASSIGNEE",\n  "CHANGE_DUE_DATE",\n  "ADD_COMMENT",\n  "ADD_CHECKLIST",\n]);',
    'const SUPPORTED_PROPOSAL_OPERATIONS = new Set([\n  "CREATE_TASK",\n  "CHANGE_ASSIGNEE",\n  "CHANGE_DUE_DATE",\n  "ADD_COMMENT",\n  "ADD_CHECKLIST",\n]);',
    'SEMANTIC_SUPPORTED_ACTIONS',
)
text = replace_once(
    text,
    '  const patterns = [\n    /(?:خلي|خلّي)\\s+(.+?)\\s+(?:يمسك|ياخد|يستلم)(?:\\s|$)/iu,',
    '  const patterns = [\n    /(?:اعمل|انشئ|أنشئ|create|make)\\s+(?:(?:لي|a|new|جديده|جديدة)\\s+)?(?:task|تاسك|التاسك|مهمه|مهمة|المهمه|المهمة)[^،,؟?!]*?(?:لـ?|ل|إلى|الى|for|to)\\s+([^،,؟?!]+)/iu,\n    /(?:خلي|خلّي)\\s+(.+?)\\s+(?:يمسك|ياخد|يستلم)(?:\\s|$)/iu,',
    'SEMANTIC_CREATE_ASSIGNEE_PATTERN',
)
text = replace_once(
    text,
    '  const assigneeQuery = operation === "CHANGE_ASSIGNEE" ? detectAssigneeQuery(message) : null;',
    '  const assigneeQuery = ["CHANGE_ASSIGNEE", "CREATE_TASK"].includes(operation) ? detectAssigneeQuery(message) : null;',
    'SEMANTIC_CREATE_ASSIGNEE_SLOT',
)
write(rel, text)


# 2) Agent access: explicit project-create authorization with workspace restriction awareness.
rel = 'backend/src/agency-operator/policies/agentAccess.service.js'
text = read(rel)
text = replace_once(
    text,
    'const SUPPORTED_ACTIONS = new Set(["ADD_COMMENT", "ADD_CHECKLIST", "CHANGE_DUE_DATE", "CHANGE_ASSIGNEE"]);',
    'const SUPPORTED_ACTIONS = new Set(["CREATE_TASK", "ADD_COMMENT", "ADD_CHECKLIST", "CHANGE_DUE_DATE", "CHANGE_ASSIGNEE"]);',
    'ACCESS_SUPPORTED_ACTIONS',
)
create_access = '''export async function assertAgentTaskCreateAccess(user, projectId, allowedWorkspaceIds = [], db = prisma) {
  const { project, access } = await resolveAgentProjectAccess(user, projectId, db);
  const role = projectManagerBypass(user, access) ? "MANAGER" : (access.projectRole || "MEMBER");
  if (!canCreateWork(role, user.role)) throw new AppError("You are not allowed to create tasks in this project", 403);

  const allowed = normalizeIds(allowedWorkspaceIds);
  if (allowed.length) {
    const scopedWorkspace = await db.workspace.findFirst({
      where: { id: { in: allowed }, projectId: project.id, archivedAt: null },
      select: { id: true },
    });
    if (!scopedWorkspace) throw new AppError("Ramzy cannot create tasks in this project within the allowed workspace scope", 403);
  }

  return { project, access: { ...access, effectiveRole: role } };
}

'''
text = replace_once(
    text,
    'export async function assertAgentTaskAccess(user, taskId, allowedWorkspaceIds = [], db = prisma) {',
    create_access + 'export async function assertAgentTaskAccess(user, taskId, allowedWorkspaceIds = [], db = prisma) {',
    'ACCESS_CREATE_GUARD',
)
write(rel, text)


# 3) Action grounding: CREATE_TASK gets deterministic project + assignee grounding before provider/tool use.
rel = 'backend/src/agency-operator/services/actionGroundingValidation.service.js'
text = read(rel)
text = replace_once(
    text,
    'import { assertAgentTaskActionAccess } from "../policies/agentAccess.service.js";',
    'import { assertAgentTaskActionAccess, assertAgentTaskCreateAccess } from "../policies/agentAccess.service.js";',
    'GROUNDING_CREATE_ACCESS_IMPORT',
)
text = replace_once(
    text,
    'const SUPPORTED_PROPOSAL_OPERATIONS = new Set([\n  "ADD_COMMENT",',
    'const SUPPORTED_PROPOSAL_OPERATIONS = new Set([\n  "CREATE_TASK",\n  "ADD_COMMENT",',
    'GROUNDING_SUPPORTED_CREATE',
)
text = replace_once(
    text,
    'const REQUIRED_PAYLOAD_FIELDS = Object.freeze({\n  ADD_COMMENT: ["body"],',
    'const REQUIRED_PAYLOAD_FIELDS = Object.freeze({\n  CREATE_TASK: ["projectId", "title"],\n  ADD_COMMENT: ["body"],',
    'GROUNDING_CREATE_REQUIRED_FIELDS',
)
text = text.replace(
    '    if (operation === "CREATE_TASK") return "فاهم إنك عايز تنشئ مهمة، لكن رمزي في الإصدار الحالي ما بينشئش مهام مباشرة. مفيش أي مهمة اتعملت.";\n',
    '',
)
text = replace_once(
    text,
    '  actionTargetGuard = {},\n  assigneeResolution = null,\n  allowedWorkspaceIds = [],',
    '  actionTargetGuard = {},\n  assigneeResolution = null,\n  projectResolution = null,\n  allowedWorkspaceIds = [],',
    'GROUNDING_PROJECT_RESOLUTION_PARAM',
)
create_grounding = '''
  if (operation === "CREATE_TASK") {
    const project = projectResolution?.entity || null;
    if (!project?.id) {
      const grounding = result({
        capability,
        decision: DECISIONS.CLARIFY,
        reason: "PROJECT_TARGET_REQUIRED",
        operation,
        providerAllowed: false,
        proposalAllowed: false,
        requiredPayloadFields: REQUIRED_PAYLOAD_FIELDS[operation],
      });
      return { ...grounding, userMessage: "محتاج تحدد المشروع اللي هتتعمل فيه المهمة قبل ما أجهز طلب الإنشاء." };
    }

    try {
      await assertAgentTaskCreateAccess(user, project.id, allowedWorkspaceIds, prisma);
    } catch (error) {
      const grounding = result({
        capability,
        decision: DECISIONS.REJECT,
        reason: compactErrorReason(error, "TASK_CREATE_ACCESS_DENIED"),
        operation,
        providerAllowed: false,
        proposalAllowed: false,
        targetProjectId: project.id,
        requiredPayloadFields: REQUIRED_PAYLOAD_FIELDS[operation],
      });
      return { ...grounding, userMessage: actionGroundingUserMessage(grounding) || "المشروع موجود، لكن إنشاء مهمة فيه خارج صلاحياتك الحالية." };
    }

    let groundedAssigneeId = null;
    let groundedAssigneeName = null;
    const assigneeRequested = Boolean(String(intentResolution?.slots?.assigneeQuery || "").trim());
    if (assigneeRequested) {
      groundedAssigneeId = String(assigneeResolution?.entity?.id || "").trim() || null;
      if (!groundedAssigneeId) {
        return result({
          capability,
          decision: DECISIONS.CLARIFY,
          reason: "ASSIGNEE_TARGET_REQUIRED",
          operation,
          providerAllowed: false,
          proposalAllowed: false,
          targetProjectId: project.id,
          requiredPayloadFields: REQUIRED_PAYLOAD_FIELDS[operation],
        });
      }
      try {
        await assertAssigneeInProject(project.id, groundedAssigneeId);
      } catch {
        const grounding = result({
          capability,
          decision: DECISIONS.REJECT,
          reason: "ASSIGNEE_NOT_IN_PROJECT",
          operation,
          providerAllowed: false,
          proposalAllowed: false,
          targetProjectId: project.id,
          groundedAssigneeId,
          requiredPayloadFields: REQUIRED_PAYLOAD_FIELDS[operation],
        });
        return { ...grounding, userMessage: actionGroundingUserMessage(grounding) };
      }
      const target = await prisma.user.findFirst({
        where: { id: groundedAssigneeId, status: "ACTIVE" },
        select: { id: true, name: true, email: true, role: true, status: true, department: true },
      });
      if (!target || !(await canActorAssignTargetUser(user, target, prisma))) {
        const grounding = result({
          capability,
          decision: DECISIONS.REJECT,
          reason: target ? "ASSIGNEE_NOT_ASSIGNABLE" : "ASSIGNEE_INACTIVE",
          operation,
          providerAllowed: false,
          proposalAllowed: false,
          targetProjectId: project.id,
          groundedAssigneeId,
          requiredPayloadFields: REQUIRED_PAYLOAD_FIELDS[operation],
        });
        return { ...grounding, userMessage: actionGroundingUserMessage(grounding) };
      }
      groundedAssigneeName = target.name || target.email || null;
    }

    return result({
      capability,
      decision: DECISIONS.PASS,
      reason: "TASK_CREATE_GROUNDED_AND_AUTHORIZED",
      operation,
      providerAllowed: true,
      proposalAllowed: true,
      targetProjectId: project.id,
      groundedAssigneeId,
      groundedAssigneeName,
      requiredPayloadFields: REQUIRED_PAYLOAD_FIELDS[operation],
    });
  }
'''
text = replace_once(
    text,
    '  if (capability === CAPABILITIES.INTENT_ONLY || !SUPPORTED_PROPOSAL_OPERATIONS.has(operation)) {',
    create_grounding + '\n  if (capability === CAPABILITIES.INTENT_ONLY || !SUPPORTED_PROPOSAL_OPERATIONS.has(operation)) {',
    'GROUNDING_CREATE_BRANCH',
)
create_validation = '''  if (actionType === "CREATE_TASK") {
    const projectId = String(input.projectId || "").trim();
    if (!projectId || projectId !== actionGrounding.targetProjectId) return { allowed: false, reason: "PROJECT_TARGET_MISMATCH" };
    const payload = payloadObject(input.payload);
    if (!String(payload.title || "").trim()) return { allowed: false, reason: "TASK_TITLE_REQUIRED" };
    if (payload.dueDate !== null && payload.dueDate !== "" && payload.dueDate !== undefined) {
      const dueDate = new Date(payload.dueDate);
      if (Number.isNaN(dueDate.getTime())) return { allowed: false, reason: "DUE_DATE_INVALID" };
    }
    const assigneeId = String(payload.assigneeId || "").trim() || null;
    if (actionGrounding.groundedAssigneeId && assigneeId !== actionGrounding.groundedAssigneeId) {
      return { allowed: false, reason: "ASSIGNEE_TARGET_MISMATCH" };
    }
    if (!actionGrounding.groundedAssigneeId && assigneeId) return { allowed: false, reason: "UNGROUNDED_ASSIGNEE_TARGET" };
    return { allowed: true, reason: "GROUNDED_TASK_CREATE_INPUT_VALID" };
  }

'''
text = replace_once(
    text,
    '  const taskId = String(input.taskId || "").trim();\n  if (actionType !== actionGrounding.operation) return { allowed: false, reason: "ACTION_TYPE_MISMATCH" };\n  if (!taskId || taskId !== actionGrounding.targetTaskId) return { allowed: false, reason: "TASK_TARGET_MISMATCH" };',
    '  const taskId = String(input.taskId || "").trim();\n  if (actionType !== actionGrounding.operation) return { allowed: false, reason: "ACTION_TYPE_MISMATCH" };\n' + create_validation + '  if (!taskId || taskId !== actionGrounding.targetTaskId) return { allowed: false, reason: "TASK_TARGET_MISMATCH" };',
    'GROUNDING_CREATE_TOOL_VALIDATION',
)
write(rel, text)


# 4) System Intelligence: resolve CREATE_TASK assignees and pass project grounding to policy layer.
rel = 'backend/src/agency-operator/services/ramzySystemIntelligence.service.js'
text = read(rel)
text = replace_once(
    text,
    '  const assigneeIntent = ["TASK_BY_ASSIGNEE", "TASK_OVERDUE", "TASK_BLOCKED", "TASK_SEARCH"].includes(detectedIntent)\n    || intentResolution.operation === "CHANGE_ASSIGNEE";',
    '  const assigneeIntent = ["TASK_BY_ASSIGNEE", "TASK_OVERDUE", "TASK_BLOCKED", "TASK_SEARCH"].includes(detectedIntent)\n    || intentResolution.operation === "CHANGE_ASSIGNEE"\n    || (detectedIntent === "TASK_CREATE" && Boolean(intentResolution.slots?.assigneeQuery));',
    'INTELLIGENCE_CREATE_ASSIGNEE_INTENT',
)
text = replace_once(
    text,
    '    assigneeResolution,\n    allowedWorkspaceIds: settings.allowedWorkspaceIds || [],',
    '    assigneeResolution,\n    projectResolution,\n    allowedWorkspaceIds: settings.allowedWorkspaceIds || [],',
    'INTELLIGENCE_CREATE_PROJECT_GROUNDING',
)
text = replace_once(
    text,
    '  const userTargetRequired = intentResolution.operation === "CHANGE_ASSIGNEE" || detectedIntent === "TASK_BY_ASSIGNEE";',
    '  const userTargetRequired = intentResolution.operation === "CHANGE_ASSIGNEE"\n    || detectedIntent === "TASK_BY_ASSIGNEE"\n    || (detectedIntent === "TASK_CREATE" && Boolean(intentResolution.slots?.assigneeQuery));',
    'INTELLIGENCE_CREATE_USER_GUARD',
)
write(rel, text)


# 5) Task command service: CREATE_TASK proposal + approval execution via existing project/board access services.
rel = 'backend/src/agency-operator/services/taskCommands.service.js'
text = read(rel)
text = replace_once(
    text,
    'import { assertAssigneeInProject } from "../../middleware/auth.js";',
    'import { assertAssigneeInProject, canCreateWork } from "../../middleware/auth.js";',
    'TASK_COMMAND_CREATE_AUTH_IMPORT',
)
text = replace_once(
    text,
    'import { canActorAssignTargetUser } from "../../services/projectAccessScope.service.js";',
    'import { canActorAssignTargetUser } from "../../services/projectAccessScope.service.js";\nimport { DEFAULT_TASK_LISTS, ensureProjectDefaultWorkspaceBoard } from "../../services/projectBoardMembership.service.js";',
    'TASK_COMMAND_BOARD_SERVICE_IMPORT',
)
text = replace_once(
    text,
    'import { assertAgentTaskActionAccess } from "../policies/agentAccess.service.js";',
    'import { assertAgentTaskActionAccess, assertAgentTaskCreateAccess, resolveAgentBoardAccess } from "../policies/agentAccess.service.js";',
    'TASK_COMMAND_CREATE_ACCESS_IMPORT',
)
text = replace_once(
    text,
    'const ACTIONS = new Set(["ADD_COMMENT", "ADD_CHECKLIST", "CHANGE_DUE_DATE", "CHANGE_ASSIGNEE"]);',
    'const ACTIONS = new Set(["CREATE_TASK", "ADD_COMMENT", "ADD_CHECKLIST", "CHANGE_DUE_DATE", "CHANGE_ASSIGNEE"]);',
    'TASK_COMMAND_SUPPORTED_ACTIONS',
)
text = replace_once(
    text,
    'const TITLE_MAP = {\n  ADD_COMMENT: "إضافة تعليق على المهمة",',
    'const TITLE_MAP = {\n  CREATE_TASK: "إنشاء مهمة جديدة",\n  ADD_COMMENT: "إضافة تعليق على المهمة",',
    'TASK_COMMAND_CREATE_TITLE',
)
create_normalize = '''  if (actionType === "CREATE_TASK") {
    const title = String(payload.title || "").trim();
    if (!title) throw new AppError("Task title is required", 400);
    const description = String(payload.description || "").trim().slice(0, 10_000);
    const priority = String(payload.priority || "MEDIUM").trim().toUpperCase();
    if (!["LOW", "MEDIUM", "HIGH", "URGENT"].includes(priority)) throw new AppError("Invalid task priority", 400);
    let dueDate = null;
    if (payload.dueDate !== undefined && payload.dueDate !== null && payload.dueDate !== "") {
      const parsed = new Date(payload.dueDate);
      if (Number.isNaN(parsed.getTime())) throw new AppError("Invalid due date", 400);
      dueDate = parsed.toISOString();
    }
    const assigneeId = String(payload.assigneeId || "").trim() || null;
    return { title: title.slice(0, 500), description, priority, dueDate, assigneeId };
  }
'''
text = replace_once(
    text,
    '  if (actionType === "ADD_COMMENT") {',
    create_normalize + '  if (actionType === "ADD_COMMENT") {',
    'TASK_COMMAND_CREATE_PAYLOAD',
)
text = replace_once(
    text,
    '  actionType,\n  taskId,\n  payload = {},',
    '  actionType,\n  taskId = null,\n  projectId = null,\n  payload = {},',
    'TASK_COMMAND_CREATE_PROPOSAL_PARAMS',
)
old_proposal = '''  const settings = await getAgentSettings();
  const { task } = await assertAgentTaskActionAccess(user, taskId, normalizedAction, settings.allowedWorkspaceIds, prisma);
  const normalizedPayload = normalizeTaskActionPayload(normalizedAction, payload);
  let approvalPayload = normalizedPayload;
  let approvalTitle = TITLE_MAP[normalizedAction];
  if (normalizedAction === "CHANGE_ASSIGNEE") {
    const target = await assertAssignmentTarget(user, task.projectId, normalizedPayload.assigneeId);
    const assigneeName = String(target.name || target.email || target.id).trim().slice(0, 160);
    approvalPayload = { ...normalizedPayload, assigneeName };
    approvalTitle = `استبدال منفذي المهمة بـ ${assigneeName}`;
  } else if (normalizedAction === "CHANGE_DUE_DATE") {
    approvalTitle = normalizedPayload.dueDate
      ? `تغيير موعد المهمة إلى ${new Date(normalizedPayload.dueDate).toLocaleString("ar-EG")}`
      : "إزالة موعد المهمة";
  }
'''
new_proposal = '''  const settings = await getAgentSettings();
  const normalizedPayload = normalizeTaskActionPayload(normalizedAction, payload);
  let approvalPayload = normalizedPayload;
  let approvalTitle = TITLE_MAP[normalizedAction];
  let targetType = "TASK";
  let targetId = String(taskId || "").trim();

  if (normalizedAction === "CREATE_TASK") {
    const requestedProjectId = String(projectId || "").trim();
    if (!requestedProjectId) throw new AppError("projectId is required", 400);
    const { project } = await assertAgentTaskCreateAccess(user, requestedProjectId, settings.allowedWorkspaceIds, prisma);
    targetType = "PROJECT";
    targetId = project.id;
    let target = null;
    if (normalizedPayload.assigneeId) target = await assertAssignmentTarget(user, project.id, normalizedPayload.assigneeId);
    const assigneeName = target ? String(target.name || target.email || "").trim().slice(0, 160) : null;
    approvalPayload = {
      ...normalizedPayload,
      projectName: String(project.name || "").trim().slice(0, 200),
      ...(assigneeName ? { assigneeName } : {}),
    };
    approvalTitle = `إنشاء مهمة «${normalizedPayload.title}» في ${project.name}${assigneeName ? ` وإسنادها إلى ${assigneeName}` : ""}`;
  } else {
    const { task } = await assertAgentTaskActionAccess(user, taskId, normalizedAction, settings.allowedWorkspaceIds, prisma);
    targetId = task.id;
    if (normalizedAction === "CHANGE_ASSIGNEE") {
      const target = await assertAssignmentTarget(user, task.projectId, normalizedPayload.assigneeId);
      const assigneeName = String(target.name || target.email || target.id).trim().slice(0, 160);
      approvalPayload = { ...normalizedPayload, assigneeName };
      approvalTitle = `استبدال منفذي المهمة بـ ${assigneeName}`;
    } else if (normalizedAction === "CHANGE_DUE_DATE") {
      approvalTitle = normalizedPayload.dueDate
        ? `تغيير موعد المهمة إلى ${new Date(normalizedPayload.dueDate).toLocaleString("ar-EG")}`
        : "إزالة موعد المهمة";
    }
  }
'''
text = replace_once(text, old_proposal, new_proposal, 'TASK_COMMAND_CREATE_PROPOSAL_BRANCH')
text = replace_once(
    text,
    '      targetType: "TASK",\n      targetId: taskId,',
    '      targetType,\n      targetId,',
    'TASK_COMMAND_DYNAMIC_TARGET',
)
create_executor = '''async function executeApprovedTaskCreate({ approval, user, io, settings }) {
  if (approval?.targetType !== "PROJECT") throw new AppError("Invalid task create target", 400);
  const { project } = await assertAgentTaskCreateAccess(user, approval.targetId, settings.allowedWorkspaceIds, prisma);
  const payload = normalizeTaskActionPayload("CREATE_TASK", approval.payload || {});
  const target = payload.assigneeId ? await assertAssignmentTarget(user, project.id, payload.assigneeId) : null;

  const ensured = await ensureProjectDefaultWorkspaceBoard(prisma, project.id, user.id, {
    lists: DEFAULT_TASK_LISTS,
    syncMembers: true,
  });
  if (!ensured?.workspace || ensured.workspace.archivedAt || !ensured?.board || ensured.board.archivedAt) {
    throw new AppError("Project default board is unavailable", 409);
  }
  const { board, access } = await resolveAgentBoardAccess(user, ensured.board.id, settings.allowedWorkspaceIds, prisma);
  const role = access.effectiveRole || access.boardRole || access.projectRole || "MEMBER";
  if (!canCreateWork(role, user.role)) throw new AppError("You are not allowed to create tasks on this board", 403);

  const lists = Array.isArray(ensured.lists) ? ensured.lists : [];
  const targetList = lists.find((item) => item && !item.archivedAt && !item.hiddenAt && item.status === "TODO")
    || lists.find((item) => item && !item.archivedAt && !item.hiddenAt)
    || null;
  if (!targetList) throw new AppError("Project board has no available task list", 409);

  const dueDate = payload.dueDate ? new Date(payload.dueDate) : null;
  const description = sanitizeRichText(payload.description || "") || null;
  const created = await prisma.$transaction(async (tx) => {
    const last = await tx.task.aggregate({
      where: { projectId: project.id, boardId: board.id, listId: targetList.id },
      _max: { position: true },
    });
    const task = await tx.task.create({
      data: {
        title: payload.title,
        description,
        status: targetList.status || "TODO",
        priority: payload.priority || "MEDIUM",
        serviceType: "OTHER",
        dueDate,
        slaDueAt: dueDate,
        position: Number(last._max.position || 0) + 1000,
        projectId: project.id,
        boardId: board.id,
        listId: targetList.id,
        assigneeId: target?.id || null,
        createdById: user.id,
      },
    });
    if (target?.id) {
      await ensureAssigneeBoardScope(tx, task, target.id);
      await tx.taskAssignee.create({ data: { taskId: task.id, userId: target.id, assignedById: user.id } });
    }
    return task;
  });

  const fullTask = await loadAgentTask(created.id);
  emitTaskChanged(io, fullTask || created);
  pushTaskEventToTcrmSafe(fullTask || created, "task.created", user);
  pushProjectProgressEventToTcrmSafe(project.id, "project.progress.updated", user);
  return fullTask || created;
}

'''
text = replace_once(
    text,
    'export async function executeApprovedTaskAction({ approval, user, io }) {',
    create_executor + 'export async function executeApprovedTaskAction({ approval, user, io }) {',
    'TASK_COMMAND_CREATE_EXECUTOR',
)
old_execute_head = '''  const actionType = String(approval?.actionType || "").toUpperCase();
  if (approval?.targetType !== "TASK" || !ACTIONS.has(actionType)) throw new AppError("Unsupported approved action", 400);
  const settings = await getAgentSettings();
  const { task: accessibleTask } = await assertAgentTaskActionAccess(
'''
new_execute_head = '''  const actionType = String(approval?.actionType || "").toUpperCase();
  if (!ACTIONS.has(actionType)) throw new AppError("Unsupported approved action", 400);
  const settings = await getAgentSettings();
  if (actionType === "CREATE_TASK") return executeApprovedTaskCreate({ approval, user, io, settings });
  if (approval?.targetType !== "TASK") throw new AppError("Unsupported approved action target", 400);
  const { task: accessibleTask } = await assertAgentTaskActionAccess(
'''
text = replace_once(text, old_execute_head, new_execute_head, 'TASK_COMMAND_CREATE_EXECUTE_BRANCH')
write(rel, text)


# 6) Tool schema: one proposal tool handles CREATE_TASK and existing task actions.
rel = 'backend/src/agency-operator/tools/createRamzyTools.js'
text = read(rel)
text = replace_once(
    text,
    'description: "Create a human approval card for a task action. Never claim it was executed. Supported: ADD_COMMENT, ADD_CHECKLIST, CHANGE_DUE_DATE, CHANGE_ASSIGNEE.",',
    'description: "Create a human approval card for a task action. Never claim it was executed. Supported: CREATE_TASK, ADD_COMMENT, ADD_CHECKLIST, CHANGE_DUE_DATE, CHANGE_ASSIGNEE. CREATE_TASK requires an authorized projectId and title payload.",',
    'TOOL_CREATE_DESCRIPTION',
)
text = replace_once(
    text,
    '      actionType: z.enum(["ADD_COMMENT", "ADD_CHECKLIST", "CHANGE_DUE_DATE", "CHANGE_ASSIGNEE"]),\n      taskId: z.string(),',
    '      actionType: z.enum(["CREATE_TASK", "ADD_COMMENT", "ADD_CHECKLIST", "CHANGE_DUE_DATE", "CHANGE_ASSIGNEE"]),\n      taskId: z.string().optional(),\n      projectId: z.string().optional(),',
    'TOOL_CREATE_SCHEMA',
)
write(rel, text)


# 7) Approval endpoint: PROJECT target is allowed only for CREATE_TASK and is reauthorized at decision time.
rel = 'backend/src/routes/agent.routes.js'
text = read(rel)
text = replace_once(
    text,
    'import { isSupportedAgentAction } from "../agency-operator/policies/agentAccess.service.js";',
    'import { assertAgentTaskCreateAccess, isSupportedAgentAction } from "../agency-operator/policies/agentAccess.service.js";',
    'AGENT_ROUTE_CREATE_ACCESS_IMPORT',
)
text = replace_once(
    text,
    '  if (approval.targetType !== "TASK" || !isSupportedAgentAction(approval.actionType)) {\n    throw new AppError("Unsupported approval action", 400);\n  }',
    '  const isCreateTaskApproval = String(approval.actionType || "").toUpperCase() === "CREATE_TASK";\n  const validTargetType = isCreateTaskApproval ? approval.targetType === "PROJECT" : approval.targetType === "TASK";\n  if (!validTargetType || !isSupportedAgentAction(approval.actionType)) {\n    throw new AppError("Unsupported approval action", 400);\n  }',
    'AGENT_ROUTE_CREATE_TARGET_TYPE',
)
text = replace_once(
    text,
    '  await assertTaskWithinAgentWorkspaceScope(req.user, approval.targetId, settings.allowedWorkspaceIds);',
    '  if (isCreateTaskApproval) {\n    await assertAgentTaskCreateAccess(req.user, approval.targetId, settings.allowedWorkspaceIds, prisma);\n  } else {\n    await assertTaskWithinAgentWorkspaceScope(req.user, approval.targetId, settings.allowedWorkspaceIds);\n  }',
    'AGENT_ROUTE_CREATE_REAUTH',
)
write(rel, text)


# 8) Prompt: voice and text use the same action + approval path.
rel = 'backend/src/agency-operator/prompts/ramzyPrompt.js'
text = read(rel)
text = replace_once(
    text,
    '- عند طلب تعديل على مهمة موجودة، أنشئ اقتراحًا للموافقة باستخدام proposeTaskAction ولا تدّع أن التعديل تم.',
    '- عند طلب إنشاء مهمة أو تعديل مهمة موجودة، استخدم proposeTaskAction لإنشاء Approval Card فقط، ولا تدّع أن الإجراء تم قبل اعتماد المستخدم وتنفيذه على السيرفر.',
    'PROMPT_CREATE_APPROVAL_RULE',
)
phase12_rules = '''- Phase 12: أوامر المهام المكتوبة أو القادمة من Speech-to-Text تستخدم نفس مسار الإجراءات بالضبط. الصوت لا يمنح أي صلاحية إضافية ولا يغيّر RBAC.
- لإنشاء مهمة استخدم actionType=CREATE_TASK بعد تثبيت المشروع بالـIdentity/Project Resolver. مرر projectId داخليًا وpayload يحتوي title، ويمكن description/priority/dueDate/assigneeId فقط عند ثبوتها.
- إذا طلب المستخدم إسناد المهمة الجديدة لشخص، ثبّت هوية الموظف داخل نفس المشروع ونطاق المستخدم أولًا. عند ambiguity اسأل ولا تنشئ Proposal باسم مخمّن.
- CREATE_TASK وCHANGE_ASSIGNEE وCHANGE_DUE_DATE وADD_COMMENT وADD_CHECKLIST كلها Approval-based؛ لا تقل «تم» إلا بعد أن تصبح الموافقة EXECUTED فعليًا.
'''
text = replace_once(
    text,
    '- اعتبر النص القادم لاحقًا من Speech-to-Text مثل أي نص مستخدم آخر: اختلاف النطق أو التهجئة لا يلغي التحقق من الهوية والصلاحيات قبل أي Action.\n',
    '- اعتبر النص القادم لاحقًا من Speech-to-Text مثل أي نص مستخدم آخر: اختلاف النطق أو التهجئة لا يلغي التحقق من الهوية والصلاحيات قبل أي Action.\n' + phase12_rules,
    'PROMPT_PHASE12_RULES',
)
write(rel, text)


# 9) Frontend approval card: safe human-readable CREATE_TASK summary, never raw IDs.
rel = 'frontend/src/components/RamzyAssistant.jsx'
text = read(rel)
text = replace_once(
    text,
    'const APPROVAL_ACTION_LABELS = {\n  ADD_COMMENT:',
    'const APPROVAL_ACTION_LABELS = {\n  CREATE_TASK: { ar: "إنشاء مهمة", en: "Create task" },\n  ADD_COMMENT:',
    'FRONTEND_CREATE_LABEL',
)
text = replace_once(
    text,
    '  if (approval?.actionType === "CHANGE_ASSIGNEE") return `Change task assignee to ${payload.assigneeName || "the selected employee"}`;',
    '  if (approval?.actionType === "CREATE_TASK") return `Create task “${payload.title || "New task"}”${payload.projectName ? ` in ${payload.projectName}` : ""}`;\n  if (approval?.actionType === "CHANGE_ASSIGNEE") return `Change task assignee to ${payload.assigneeName || "the selected employee"}`;',
    'FRONTEND_CREATE_TITLE',
)
create_detail = '''  if (approval?.actionType === "CREATE_TASK") {
    const parts = [
      payload.projectName ? `${isEnglish ? "Project" : "المشروع"}: ${payload.projectName}` : null,
      payload.assigneeName ? `${isEnglish ? "Assignee" : "المنفذ"}: ${payload.assigneeName}` : null,
      payload.dueDate ? `${isEnglish ? "Due" : "الموعد"}: ${new Date(payload.dueDate).toLocaleString(isEnglish ? "en-US" : "ar-EG")}` : null,
    ].filter(Boolean);
    return parts.join(" • ");
  }
'''
text = replace_once(
    text,
    '  if (approval?.actionType === "ADD_COMMENT") return `${isEnglish ? "Suggested comment" : "التعليق المقترح"}: ${payload.body || "-"}`;',
    create_detail + '  if (approval?.actionType === "ADD_COMMENT") return `${isEnglish ? "Suggested comment" : "التعليق المقترح"}: ${payload.body || "-"}`;',
    'FRONTEND_CREATE_DETAIL',
)
write(rel, text)


# 10) Phase 12 regression/contract tests.
test_rel = 'backend/src/agency-operator/tests/ramzyVoiceTaskActionsPhase12.static.test.js'
test_content = r'''import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { resolveSemanticIntent, getSemanticIntentConfig } from "../services/semanticIntentResolver.service.js";
import { getActionGroundingValidationConfig } from "../services/actionGroundingValidation.service.js";

const here = path.dirname(fileURLToPath(import.meta.url));
const backendSrc = path.resolve(here, "../..");
const repoRoot = path.resolve(backendSrc, "../..");
const readBackend = (relative) => readFile(path.join(backendSrc, relative), "utf8");
const readRepo = (relative) => readFile(path.join(repoRoot, relative), "utf8");

test("Phase 12 recognizes voice-style task creation as an approval-supported action", () => {
  const intent = resolveSemanticIntent({ message: "اعمل تاسك ليوسف" });
  assert.equal(intent.intent, "TASK_CREATE");
  assert.equal(intent.operation, "CREATE_TASK");
  assert.equal(intent.actionCapability, "PROPOSAL_SUPPORTED");
  assert.ok(String(intent.slots?.assigneeQuery || "").includes("يوسف"));
  assert.ok(getSemanticIntentConfig().supportedProposalOperations.includes("CREATE_TASK"));
  assert.ok(getActionGroundingValidationConfig().supportedProposalOperations.includes("CREATE_TASK"));
});

test("Phase 12 CREATE_TASK is server-authorized twice and approval-only", async () => {
  const access = await readBackend("agency-operator/policies/agentAccess.service.js");
  const commands = await readBackend("agency-operator/services/taskCommands.service.js");
  const routes = await readBackend("routes/agent.routes.js");
  const tools = await readBackend("agency-operator/tools/createRamzyTools.js");
  assert.match(access, /assertAgentTaskCreateAccess/);
  assert.match(access, /canCreateWork/);
  assert.match(commands, /ensureProjectDefaultWorkspaceBoard/);
  assert.match(commands, /resolveAgentBoardAccess/);
  assert.match(commands, /actionType === "CREATE_TASK"/);
  assert.match(commands, /targetType = "PROJECT"/);
  assert.match(routes, /isCreateTaskApproval/);
  assert.match(routes, /assertAgentTaskCreateAccess/);
  assert.match(tools, /CREATE_TASK/);
  assert.match(tools, /Create a human approval card/);
  assert.doesNotMatch(tools, /executeApprovedTaskAction/);
});

test("Phase 12 keeps voice on the same RBAC/identity pipeline and never exposes create IDs in the card", async () => {
  const intelligence = await readBackend("agency-operator/services/ramzySystemIntelligence.service.js");
  const grounding = await readBackend("agency-operator/services/actionGroundingValidation.service.js");
  const prompt = await readBackend("agency-operator/prompts/ramzyPrompt.js");
  const ui = await readRepo("frontend/src/components/RamzyAssistant.jsx");
  assert.match(intelligence, /projectResolution/);
  assert.match(intelligence, /detectedIntent === "TASK_CREATE"/);
  assert.match(grounding, /TASK_CREATE_GROUNDED_AND_AUTHORIZED/);
  assert.match(grounding, /ASSIGNEE_TARGET_MISMATCH/);
  assert.match(prompt, /Phase 12:/);
  assert.match(prompt, /الصوت لا يمنح أي صلاحية إضافية/);
  assert.match(ui, /CREATE_TASK: \{ ar: "إنشاء مهمة", en: "Create task" \}/);
  assert.match(ui, /payload\.projectName/);
  assert.match(ui, /payload\.assigneeName/);
  assert.doesNotMatch(ui, /CREATE_TASK[\s\S]{0,900}payload\.assigneeId/);
});
'''
if (ROOT / test_rel).exists():
    current = read(test_rel)
    if 'Phase 12 recognizes voice-style task creation' not in current:
        raise SystemExit('PHASE12_PATCH_ERROR=PHASE12_TEST_CONFLICT')
else:
    write(test_rel, test_content)

print('PHASE12_RAMZY_VOICE_TASK_ACTIONS_PATCH=PASS')
