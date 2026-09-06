#!/usr/bin/env python3
from pathlib import Path

ROOT = Path('/var/www/TOS')


def read(rel):
    return (ROOT / rel).read_text(encoding='utf-8')


def replace_once(text, old, new, label):
    if new in text:
        return text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'PHASE15_PATCH_ERROR={label}_COUNT_{count}')
    return text.replace(old, new, 1)


TARGETS = {
    'backend/src/agency-operator/tools/createRamzyTools.js': read('backend/src/agency-operator/tools/createRamzyTools.js'),
    'backend/src/agency-operator/services/ramzyRuntime.service.js': read('backend/src/agency-operator/services/ramzyRuntime.service.js'),
    'backend/src/agency-operator/prompts/ramzyPrompt.js': read('backend/src/agency-operator/prompts/ramzyPrompt.js'),
    'backend/src/routes/agent.routes.js': read('backend/src/routes/agent.routes.js'),
    'frontend/src/components/RamzyAssistant.jsx': read('frontend/src/components/RamzyAssistant.jsx'),
}

SERVICE = r'''import { prisma } from "../../prisma.js";
import { AppError } from "../../middleware/errors.js";
import { assertAssigneeInProject } from "../../middleware/auth.js";
import { canActorAssignTargetUser } from "../../services/projectAccessScope.service.js";
import { assertAgentTaskActionAccess, assertAgentTaskCreateAccess } from "../policies/agentAccess.service.js";
import { getActionConfirmationPolicy } from "./actionConfirmation.service.js";
import { getAgentSettings } from "./agentSettings.service.js";
import { executeApprovedTaskAction } from "./taskCommands.service.js";

export const RAMZY_MULTI_STEP_VERSION = "RAMZY_MULTI_STEP_OPERATIONS_V1";
export const RAMZY_MULTI_STEP_ACTION = "MULTI_STEP_TASK_OPERATION";

const MAX_STEPS = 5;
const CHILD_ACTIONS = new Set(["CREATE_TASK", "ADD_COMMENT", "ADD_CHECKLIST", "CHANGE_DUE_DATE", "CHANGE_ASSIGNEE"]);
const PRIORITIES = new Set(["LOW", "MEDIUM", "HIGH", "URGENT"]);
const RISK_WEIGHT = Object.freeze({ LOW: 1, MEDIUM: 2, HIGH: 3 });

function plainObject(value) {
  return value && typeof value === "object" && !Array.isArray(value) ? value : {};
}

function clip(value, max = 500) {
  return String(value || "").trim().replace(/\s+/g, " ").slice(0, max);
}

function normalizeActionType(value) {
  const actionType = String(value || "").trim().toUpperCase();
  if (!CHILD_ACTIONS.has(actionType)) throw new AppError("Unsupported multi-step task action", 400);
  return actionType;
}

function normalizeDueDate(value) {
  if (value === null || value === "") return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) throw new AppError("Invalid due date", 400);
  return date.toISOString();
}

function normalizeChildPayload(actionType, rawPayload = {}) {
  const payload = plainObject(rawPayload);
  if (JSON.stringify(payload).length > 20_000) throw new AppError("Multi-step payload is too large", 400);
  if (actionType === "CREATE_TASK") {
    const title = clip(payload.title, 500);
    if (!title) throw new AppError("Task title is required", 400);
    const priority = String(payload.priority || "MEDIUM").trim().toUpperCase();
    if (!PRIORITIES.has(priority)) throw new AppError("Invalid task priority", 400);
    return {
      title,
      description: String(payload.description || "").trim().slice(0, 10_000),
      priority,
      dueDate: payload.dueDate === undefined ? null : normalizeDueDate(payload.dueDate),
      assigneeId: clip(payload.assigneeId, 120) || null,
    };
  }
  if (actionType === "ADD_COMMENT") {
    const body = String(payload.body || "").trim();
    if (!body) throw new AppError("Comment body is required", 400);
    return { body: body.slice(0, 10_000) };
  }
  if (actionType === "ADD_CHECKLIST") {
    const title = clip(payload.title, 500);
    if (!title) throw new AppError("Checklist title is required", 400);
    return { title };
  }
  if (actionType === "CHANGE_DUE_DATE") {
    return { dueDate: normalizeDueDate(payload.dueDate) };
  }
  if (actionType === "CHANGE_ASSIGNEE") {
    const assigneeId = clip(payload.assigneeId, 120);
    if (!assigneeId) throw new AppError("assigneeId is required", 400);
    return { assigneeId };
  }
  throw new AppError("Unsupported multi-step payload", 400);
}

function normalizeInputStep(step, index) {
  const value = plainObject(step);
  const actionType = normalizeActionType(value.actionType);
  const useCreatedTask = Boolean(value.useCreatedTask);
  const projectId = clip(value.projectId, 120) || null;
  const taskId = clip(value.taskId, 120) || null;
  const payload = normalizeChildPayload(actionType, value.payload);

  if (actionType === "CREATE_TASK") {
    if (!projectId) throw new AppError(`Step ${index + 1}: projectId is required`, 400);
    if (taskId || useCreatedTask) throw new AppError(`Step ${index + 1}: CREATE_TASK cannot target another task`, 400);
    return { stepNumber: index + 1, actionType, targetRef: "PROJECT", projectId, taskId: null, payload };
  }
  if (projectId) throw new AppError(`Step ${index + 1}: projectId is only valid for CREATE_TASK`, 400);
  if (useCreatedTask && taskId) throw new AppError(`Step ${index + 1}: choose taskId or useCreatedTask, not both`, 400);
  if (!useCreatedTask && !taskId) throw new AppError(`Step ${index + 1}: taskId or useCreatedTask is required`, 400);
  return {
    stepNumber: index + 1,
    actionType,
    targetRef: useCreatedTask ? "CREATED_TASK" : "TASK",
    projectId: null,
    taskId: useCreatedTask ? null : taskId,
    payload,
  };
}

function normalizeStoredStep(step, index) {
  const value = plainObject(step);
  const actionType = normalizeActionType(value.actionType);
  const targetRef = String(value.targetRef || "").trim().toUpperCase();
  const payload = normalizeChildPayload(actionType, value.payload);
  const projectId = clip(value.projectId, 120) || null;
  const taskId = clip(value.taskId, 120) || null;
  if (actionType === "CREATE_TASK") {
    if (targetRef !== "PROJECT" || !projectId || taskId) throw new AppError(`Invalid stored multi-step create target at step ${index + 1}`, 400);
  } else if (targetRef === "TASK") {
    if (!taskId || projectId) throw new AppError(`Invalid stored task target at step ${index + 1}`, 400);
  } else if (targetRef === "CREATED_TASK") {
    if (taskId || projectId) throw new AppError(`Invalid created-task dependency at step ${index + 1}`, 400);
  } else {
    throw new AppError(`Invalid target reference at step ${index + 1}`, 400);
  }
  return { stepNumber: index + 1, actionType, targetRef, projectId, taskId, payload };
}

async function assertAssignmentTarget(user, projectId, assigneeId) {
  await assertAssigneeInProject(projectId, assigneeId);
  const target = await prisma.user.findFirst({
    where: { id: assigneeId, status: "ACTIVE" },
    select: { id: true, name: true, email: true, role: true, status: true, department: true },
  });
  if (!target) throw new AppError("Assignee not found or inactive", 400);
  if (!(await canActorAssignTargetUser(user, target, prisma))) {
    throw new AppError("You are not allowed to assign this user", 403);
  }
  return target;
}

function stepRisk(actionType, settings) {
  return getActionConfirmationPolicy(actionType, settings).riskLevel || "HIGH";
}

function highestRisk(steps) {
  return steps.reduce((best, step) => (RISK_WEIGHT[step.riskLevel] || 3) > (RISK_WEIGHT[best] || 0) ? step.riskLevel : best, "LOW");
}

function publicSummary({ actionType, payload, projectName = null, taskTitle = null, assigneeName = null, createdTask = false }) {
  const target = createdTask ? "المهمة الجديدة" : (taskTitle ? `«${clip(taskTitle, 160)}»` : "المهمة المحددة");
  if (actionType === "CREATE_TASK") {
    return `إنشاء مهمة «${clip(payload.title, 180)}»${projectName ? ` في ${clip(projectName, 160)}` : ""}${assigneeName ? ` وإسنادها إلى ${clip(assigneeName, 160)}` : ""}`;
  }
  if (actionType === "ADD_COMMENT") return `إضافة تعليق على ${target}: ${clip(payload.body, 180)}`;
  if (actionType === "ADD_CHECKLIST") return `إضافة Checklist إلى ${target}: ${clip(payload.title, 180)}`;
  if (actionType === "CHANGE_DUE_DATE") return payload.dueDate ? `تغيير موعد ${target} إلى ${payload.dueDate}` : `إزالة موعد ${target}`;
  if (actionType === "CHANGE_ASSIGNEE") return `تغيير منفذ ${target} إلى ${clip(assigneeName, 160) || "الموظف المحدد"}`;
  return actionType;
}

async function validateProposalStep({ user, step, settings, createdProjectId }) {
  if (step.actionType === "CREATE_TASK") {
    const { project } = await assertAgentTaskCreateAccess(user, step.projectId, settings.allowedWorkspaceIds, prisma);
    const target = step.payload.assigneeId ? await assertAssignmentTarget(user, project.id, step.payload.assigneeId) : null;
    return {
      ...step,
      projectId: project.id,
      publicSummary: publicSummary({ actionType: step.actionType, payload: step.payload, projectName: project.name, assigneeName: target?.name || target?.email || null }),
      riskLevel: stepRisk(step.actionType, settings),
      createdProjectId: project.id,
    };
  }

  if (step.targetRef === "CREATED_TASK") {
    if (!createdProjectId) throw new AppError(`Step ${step.stepNumber}: useCreatedTask requires an earlier CREATE_TASK step`, 400);
    await assertAgentTaskCreateAccess(user, createdProjectId, settings.allowedWorkspaceIds, prisma);
    let target = null;
    if (step.actionType === "CHANGE_ASSIGNEE") target = await assertAssignmentTarget(user, createdProjectId, step.payload.assigneeId);
    return {
      ...step,
      publicSummary: publicSummary({ actionType: step.actionType, payload: step.payload, assigneeName: target?.name || target?.email || null, createdTask: true }),
      riskLevel: stepRisk(step.actionType, settings),
      createdProjectId,
    };
  }

  const { task } = await assertAgentTaskActionAccess(user, step.taskId, step.actionType, settings.allowedWorkspaceIds, prisma);
  let target = null;
  if (step.actionType === "CHANGE_ASSIGNEE") target = await assertAssignmentTarget(user, task.projectId, step.payload.assigneeId);
  return {
    ...step,
    taskId: task.id,
    publicSummary: publicSummary({ actionType: step.actionType, payload: step.payload, taskTitle: task.title, assigneeName: target?.name || target?.email || null }),
    riskLevel: stepRisk(step.actionType, settings),
    createdProjectId,
  };
}

function buildConfirmation(publicSteps, settings) {
  const riskLevel = highestRisk(publicSteps);
  const policyVersion = getActionConfirmationPolicy(publicSteps[0]?.actionType, settings).version || "RAMZY_ACTION_CONFIRMATION_V1";
  return {
    version: policyVersion,
    riskLevel,
    explicitConfirmationRequired: true,
    directExecutionEligible: false,
    directExecutionEnabled: false,
    revisionSupported: false,
    revisionFields: [],
    revisionCount: 0,
    multiStep: true,
    impactSummary: {
      actionType: RAMZY_MULTI_STEP_ACTION,
      headline: `تنفيذ ${publicSteps.length} إجراءات مترابطة`,
      details: publicSteps.map((step) => `${step.stepNumber}. ${step.summary}`),
    },
  };
}

function approvalPayload(approval) {
  const payload = plainObject(approval?.payload);
  if (payload.version !== RAMZY_MULTI_STEP_VERSION || !Array.isArray(payload.steps)) throw new AppError("Invalid multi-step approval payload", 400);
  if (payload.steps.length < 2 || payload.steps.length > MAX_STEPS) throw new AppError("Invalid multi-step operation size", 400);
  return payload;
}

function safeStepError(error) {
  return String(error?.message || error || "تعذر تنفيذ الخطوة")
    .replace(/(?:sk-|AIza|key[-_ ]?)[A-Za-z0-9_\-]{12,}/gi, "[REDACTED]")
    .replace(/\bc[a-z0-9]{20,40}\b/gi, "[internal reference]")
    .replace(/[A-Za-z0-9_-]{40,}/g, "[internal reference]")
    .slice(0, 500);
}

export function isMultiStepTaskOperationApproval(approval) {
  return String(approval?.actionType || "").toUpperCase() === RAMZY_MULTI_STEP_ACTION;
}

export async function createMultiStepTaskOperationProposal({ user, conversationId, runId, toolExecutionId = null, steps = [], reason = "" } = {}) {
  if (!user?.id) throw new AppError("User is required", 401);
  if (!Array.isArray(steps) || steps.length < 2 || steps.length > MAX_STEPS) throw new AppError(`Multi-step operations require 2-${MAX_STEPS} steps`, 400);
  const normalized = steps.map(normalizeInputStep);
  if (normalized.filter((step) => step.actionType === "CREATE_TASK").length > 1) {
    throw new AppError("Phase 15 supports at most one CREATE_TASK step per operation", 400);
  }
  const settings = await getAgentSettings();
  let createdProjectId = null;
  const validated = [];
  for (const step of normalized) {
    const checked = await validateProposalStep({ user, step, settings, createdProjectId });
    if (checked.actionType === "CREATE_TASK") createdProjectId = checked.projectId;
    validated.push(checked);
  }
  const publicSteps = validated.map((step) => ({
    stepNumber: step.stepNumber,
    actionType: step.actionType,
    riskLevel: step.riskLevel,
    summary: step.publicSummary,
  }));
  const storedSteps = validated.map(({ publicSummary: _summary, riskLevel, createdProjectId: _createdProjectId, ...step }) => ({ ...step, riskLevel }));
  const confirmation = buildConfirmation(publicSteps, settings);
  const [conversation, run, execution] = await Promise.all([
    prisma.agentConversation.findFirst({ where: { id: conversationId, userId: user.id, archivedAt: null }, select: { id: true } }),
    prisma.agentRun.findFirst({ where: { id: runId, userId: user.id, conversationId }, select: { id: true } }),
    toolExecutionId
      ? prisma.agentToolExecution.findFirst({ where: { id: toolExecutionId, runId, userId: user.id }, select: { id: true } })
      : Promise.resolve({ id: null }),
  ]);
  if (!conversation || !run || (toolExecutionId && !execution)) throw new AppError("Invalid agent execution context", 409);

  return prisma.agentApprovalRequest.create({
    data: {
      conversationId,
      runId,
      toolExecutionId,
      userId: user.id,
      actionType: RAMZY_MULTI_STEP_ACTION,
      title: `تنفيذ ${publicSteps.length} إجراءات مترابطة بواسطة رمزي`,
      reason: clip(reason, 2000) || null,
      targetType: "CONVERSATION",
      targetId: conversation.id,
      payload: {
        version: RAMZY_MULTI_STEP_VERSION,
        executionMode: "SEQUENTIAL_NO_ROLLBACK",
        steps: storedSteps,
        publicSteps,
        confirmation,
      },
      status: "PENDING",
      expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000),
    },
  });
}

export async function assertMultiStepApprovalStillAuthorized({ approval, user } = {}) {
  if (!isMultiStepTaskOperationApproval(approval) || approval?.targetType !== "CONVERSATION") throw new AppError("Invalid multi-step approval", 400);
  if (!user?.id || approval.userId !== user.id) throw new AppError("Invalid approval owner", 403);
  const conversation = await prisma.agentConversation.findFirst({ where: { id: approval.targetId, userId: user.id, archivedAt: null }, select: { id: true } });
  if (!conversation) throw new AppError("المحادثة غير موجودة", 404);
  const settings = await getAgentSettings();
  const payload = approvalPayload(approval);
  let createdProjectId = null;
  const steps = payload.steps.map(normalizeStoredStep);
  for (const step of steps) {
    if (step.actionType === "CREATE_TASK") {
      const { project } = await assertAgentTaskCreateAccess(user, step.projectId, settings.allowedWorkspaceIds, prisma);
      if (step.payload.assigneeId) await assertAssignmentTarget(user, project.id, step.payload.assigneeId);
      createdProjectId = project.id;
      continue;
    }
    if (step.targetRef === "CREATED_TASK") {
      if (!createdProjectId) throw new AppError(`Step ${step.stepNumber}: created task dependency is unavailable`, 409);
      await assertAgentTaskCreateAccess(user, createdProjectId, settings.allowedWorkspaceIds, prisma);
      if (step.actionType === "CHANGE_ASSIGNEE") await assertAssignmentTarget(user, createdProjectId, step.payload.assigneeId);
      continue;
    }
    const { task } = await assertAgentTaskActionAccess(user, step.taskId, step.actionType, settings.allowedWorkspaceIds, prisma);
    if (step.actionType === "CHANGE_ASSIGNEE") await assertAssignmentTarget(user, task.projectId, step.payload.assigneeId);
  }
  return { authorized: true, stepCount: steps.length };
}

export async function executeApprovedMultiStepOperation({ approval, user, io = null } = {}) {
  await assertMultiStepApprovalStillAuthorized({ approval, user });
  const payload = approvalPayload(approval);
  const steps = payload.steps.map(normalizeStoredStep);
  const publicSteps = Array.isArray(payload.publicSteps) ? payload.publicSteps : [];
  const results = [];
  let createdTaskId = null;

  for (const step of steps) {
    const publicStep = publicSteps.find((item) => Number(item?.stepNumber) === step.stepNumber) || {};
    const summary = clip(publicStep.summary, 500) || `Step ${step.stepNumber}: ${step.actionType}`;
    if (step.targetRef === "CREATED_TASK" && !createdTaskId) {
      results.push({ stepNumber: step.stepNumber, actionType: step.actionType, status: "SKIPPED", summary, error: "تم تخطي الخطوة لأن المهمة الجديدة لم يتم إنشاؤها بنجاح." });
      continue;
    }
    const childApproval = {
      ...approval,
      actionType: step.actionType,
      targetType: step.actionType === "CREATE_TASK" ? "PROJECT" : "TASK",
      targetId: step.actionType === "CREATE_TASK" ? step.projectId : (step.targetRef === "CREATED_TASK" ? createdTaskId : step.taskId),
      payload: step.payload,
    };
    try {
      const result = await executeApprovedTaskAction({ approval: childApproval, user, io });
      if (step.actionType === "CREATE_TASK") {
        createdTaskId = String(result?.id || "").trim() || null;
        if (!createdTaskId) throw new AppError("Created task result is unavailable", 500);
      }
      results.push({ stepNumber: step.stepNumber, actionType: step.actionType, status: "EXECUTED", summary });
    } catch (error) {
      results.push({ stepNumber: step.stepNumber, actionType: step.actionType, status: "FAILED", summary, error: safeStepError(error) });
    }
  }

  const executedSteps = results.filter((step) => step.status === "EXECUTED").length;
  const failedSteps = results.filter((step) => step.status === "FAILED").length;
  const skippedSteps = results.filter((step) => step.status === "SKIPPED").length;
  const outcome = executedSteps === results.length
    ? "SUCCESS"
    : executedSteps > 0
      ? "PARTIAL_SUCCESS"
      : "FAILED";

  return {
    version: RAMZY_MULTI_STEP_VERSION,
    outcome,
    partialSuccess: outcome === "PARTIAL_SUCCESS",
    executionMode: "SEQUENTIAL_NO_ROLLBACK",
    rollbackApplied: false,
    totalSteps: results.length,
    executedSteps,
    failedSteps,
    skippedSteps,
    steps: results,
  };
}

export function getMultiStepOperationConfig() {
  return {
    version: RAMZY_MULTI_STEP_VERSION,
    actionType: RAMZY_MULTI_STEP_ACTION,
    minSteps: 2,
    maxSteps: MAX_STEPS,
    maxCreateSteps: 1,
    alwaysExplicitConfirmation: true,
    directExecutionEnabled: false,
    executionMode: "SEQUENTIAL_NO_ROLLBACK",
    partialOutcome: "PARTIAL_SUCCESS",
    dependencyTarget: "CREATED_TASK",
    childActions: [...CHILD_ACTIONS],
  };
}

export const __testables = {
  buildConfirmation,
  highestRisk,
  normalizeChildPayload,
  normalizeInputStep,
  publicSummary,
};
'''

TEST = r'''import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { getMultiStepOperationConfig, __testables } from "../services/ramzyMultiStepOperations.service.js";

const here = path.dirname(fileURLToPath(import.meta.url));
const backendSrc = path.resolve(here, "../..");
const repoRoot = path.resolve(backendSrc, "../..");
const readBackend = (relative) => readFile(path.join(backendSrc, relative), "utf8");
const readRepo = (relative) => readFile(path.join(repoRoot, relative), "utf8");

test("Phase 15 multi-step policy is bounded and always explicitly confirmed", () => {
  const config = getMultiStepOperationConfig();
  assert.equal(config.version, "RAMZY_MULTI_STEP_OPERATIONS_V1");
  assert.equal(config.minSteps, 2);
  assert.equal(config.maxSteps, 5);
  assert.equal(config.maxCreateSteps, 1);
  assert.equal(config.alwaysExplicitConfirmation, true);
  assert.equal(config.directExecutionEnabled, false);
  assert.equal(config.executionMode, "SEQUENTIAL_NO_ROLLBACK");
  assert.equal(config.partialOutcome, "PARTIAL_SUCCESS");
});

test("Phase 15 dependent steps can target only a task created earlier in the same plan", () => {
  const create = __testables.normalizeInputStep({ actionType: "CREATE_TASK", projectId: "project-1", payload: { title: "Banner review" } }, 0);
  const checklist = __testables.normalizeInputStep({ actionType: "ADD_CHECKLIST", useCreatedTask: true, payload: { title: "Publish" } }, 1);
  assert.equal(create.targetRef, "PROJECT");
  assert.equal(checklist.targetRef, "CREATED_TASK");
  assert.throws(() => __testables.normalizeInputStep({ actionType: "ADD_COMMENT", payload: { body: "x" } }, 1));
});

test("Phase 15 confirmation inherits the highest child risk but never enables direct execution", () => {
  const confirmation = __testables.buildConfirmation([
    { stepNumber: 1, actionType: "ADD_COMMENT", riskLevel: "LOW", summary: "Comment" },
    { stepNumber: 2, actionType: "CHANGE_DUE_DATE", riskLevel: "MEDIUM", summary: "Due" },
    { stepNumber: 3, actionType: "CREATE_TASK", riskLevel: "HIGH", summary: "Create" },
  ], { readOnlyMode: false, approvalActionsEnabled: true });
  assert.equal(confirmation.riskLevel, "HIGH");
  assert.equal(confirmation.explicitConfirmationRequired, true);
  assert.equal(confirmation.directExecutionEnabled, false);
  assert.equal(confirmation.revisionSupported, false);
});

test("Phase 15 executes every side effect through the existing task action service and reports partial outcomes", async () => {
  const service = await readBackend("agency-operator/services/ramzyMultiStepOperations.service.js");
  assert.match(service, /executeApprovedTaskAction/);
  assert.match(service, /assertAgentTaskCreateAccess/);
  assert.match(service, /assertAgentTaskActionAccess/);
  assert.match(service, /assertAssigneeInProject/);
  assert.match(service, /canActorAssignTargetUser/);
  assert.match(service, /PARTIAL_SUCCESS/);
  assert.match(service, /SKIPPED/);
  assert.match(service, /SEQUENTIAL_NO_ROLLBACK/);
  assert.match(service, /rollbackApplied: false/);
});

test("Phase 15 approval route reauthorizes the full plan before claim and handles all-failed distinctly", async () => {
  const routes = await readBackend("routes/agent.routes.js");
  assert.match(routes, /isMultiStepTaskOperationApproval/);
  assert.match(routes, /assertMultiStepApprovalStillAuthorized/);
  assert.match(routes, /executeApprovedMultiStepOperation/);
  assert.match(routes, /targetType === "CONVERSATION"/);
  assert.match(routes, /result\?\.outcome === "FAILED"/);
});

test("Phase 15 tool is a side effect and prompt keeps voice on the same RBAC path", async () => {
  const tools = await readBackend("agency-operator/tools/createRamzyTools.js");
  const runtime = await readBackend("agency-operator/services/ramzyRuntime.service.js");
  const prompt = await readBackend("agency-operator/prompts/ramzyPrompt.js");
  const voice = await readBackend("agency-operator/services/ramzyVoice.service.js");
  assert.match(tools, /propose_multi_step_task_operation/);
  assert.match(tools, /createMultiStepTaskOperationProposal/);
  assert.match(runtime, /propose_multi_step_task_operation/);
  assert.match(prompt, /Phase 15:/);
  assert.match(prompt, /Multi-Step Voice Operations/);
  assert.match(prompt, /PARTIAL_SUCCESS/);
  assert.match(prompt, /الصوت لا يمنح/);
  assert.match(voice, /actionExecutionFromVoice:\s*false/);
});

test("Phase 15 frontend renders only public plan summaries and safe per-step execution results", async () => {
  const frontend = await readRepo("frontend/src/components/RamzyAssistant.jsx");
  assert.match(frontend, /MULTI_STEP_TASK_OPERATION/);
  assert.match(frontend, /publicSteps/);
  assert.match(frontend, /executionResult/);
  assert.match(frontend, /PARTIAL_SUCCESS/);
  assert.match(frontend, /step\.summary/);
  assert.doesNotMatch(frontend, /multiStepPlan[^\n]*payload\.steps/);
});
'''

# createRamzyTools imports
rel = 'backend/src/agency-operator/tools/createRamzyTools.js'
text = TARGETS[rel]
old = '''import { getActionConfirmationPolicy } from "../services/actionConfirmation.service.js";\nimport {\n  discardConversationActionDraft,'''
new = '''import { getActionConfirmationPolicy } from "../services/actionConfirmation.service.js";\nimport { createMultiStepTaskOperationProposal } from "../services/ramzyMultiStepOperations.service.js";\nimport {\n  discardConversationActionDraft,'''
text = replace_once(text, old, new, 'TOOLS_IMPORT')

anchor = '''  return {\n    getOperationalSnapshotTool,'''
insert = r'''  const proposeMultiStepTaskOperationTool = createTool({
    id: "propose_multi_step_task_operation",
    description: "Create one explicit-confirmation approval for 2-5 linked task actions from a single typed or speech-to-text request. Every child action is reauthorized and executed through the existing TOS task-action service. Use useCreatedTask=true only for steps that depend on an earlier CREATE_TASK in the same plan.",
    inputSchema: z.object({
      steps: z.array(z.object({
        actionType: z.enum(["CREATE_TASK", "ADD_COMMENT", "ADD_CHECKLIST", "CHANGE_DUE_DATE", "CHANGE_ASSIGNEE"]),
        projectId: z.string().optional(),
        taskId: z.string().optional(),
        useCreatedTask: z.boolean().optional(),
        payload: z.record(z.string(), z.any()).default({}),
      })).min(2).max(5),
      reason: z.string().max(2000).optional(),
    }),
    execute: async (input) => executeLogged("propose_multi_step_task_operation", input, async (execution) => {
      if (!settings.approvalActionsEnabled) return { created: false, reason: "Approval actions are disabled by Super Admin" };
      const approval = await createMultiStepTaskOperationProposal({
        user,
        conversationId,
        runId,
        toolExecutionId: execution.id,
        steps: input.steps,
        reason: input.reason || "Composite Ramzy task operation",
      });
      return {
        created: true,
        approvalId: approval.id,
        status: approval.status,
        title: approval.title,
        directExecuted: false,
        riskLevel: approval?.payload?.confirmation?.riskLevel || "HIGH",
        stepCount: Array.isArray(approval?.payload?.publicSteps) ? approval.payload.publicSteps.length : input.steps.length,
      };
    }),
  });

'''
text = replace_once(text, anchor, insert + anchor, 'TOOLS_DEFINITION')
old = '''    discardTaskActionDraftTool,\n    proposeTaskActionDraftTool,\n  };'''
new = '''    discardTaskActionDraftTool,\n    proposeTaskActionDraftTool,\n    proposeMultiStepTaskOperationTool,\n  };'''
text = replace_once(text, old, new, 'TOOLS_RETURN')
TARGETS[rel] = text

# Runtime side-effect guard.
rel = 'backend/src/agency-operator/services/ramzyRuntime.service.js'
text = TARGETS[rel]
old = '''  return ["propose_task_action", "revise_task_action_proposal", "update_task_action_draft", "discard_task_action_draft", "propose_task_action_draft"].includes(toolNameFromCall(value));'''
new = '''  return ["propose_task_action", "revise_task_action_proposal", "update_task_action_draft", "discard_task_action_draft", "propose_task_action_draft", "propose_multi_step_task_operation"].includes(toolNameFromCall(value));'''
text = replace_once(text, old, new, 'RUNTIME_SIDE_EFFECT')
TARGETS[rel] = text

# Prompt rules.
rel = 'backend/src/agency-operator/prompts/ramzyPrompt.js'
text = TARGETS[rel]
anchor = '''- إذا قال المستخدم «الغِ المسودة/انسَ الطلب/ابدأ من جديد» استخدم discard_task_action_draft فقط، بدون أي تنفيذ. مسودة Action لا تُحفظ في Persistent Memory طويلة المدى.\n'''
addition = '''- Phase 15: Multi-Step Voice Operations يعني أن الطلب المكتوب أو Speech-to-Text الذي يحتوي 2 إلى 5 Side Effects مترابطة يمكن تجميعه في Approval واحد باستخدام propose_multi_step_task_operation بعد تثبيت كل Project/Task/User من أدوات TOS المصرح بها.\n- استخدم العملية المركبة فقط عندما طلب المستخدم فعلًا أكثر من Side Effect في نفس الطلب. حافظ على ترتيب الخطوات، واستخدم useCreatedTask=true فقط للخطوة التي تعتمد على CREATE_TASK أقدم داخل نفس الخطة. لو CREATE_TASK يدعم dueDate أو assignee مباشرة ففضّل وضعهما في Payload الإنشاء بدل اختراع خطوة إضافية بلا داعٍ.\n- كل Multi-Step Approval يحتاج Confirm صريح دائمًا حتى لو كانت كل الخطوات LOW-risk؛ لا يوجد Direct execution للعملية المركبة. الصوت لا يمنح أي Confirm إضافي ولا أي صلاحية إضافية.\n- عند الاعتماد، كل Step يعيد RBAC والهدف في لحظة التنفيذ ويستخدم نفس خدمة TOS الأصلية. لا تعتبر نجاح خطوة تصريحًا للخطوة التالية ولا تستخدم IDs أو صلاحيات قديمة من الذاكرة.\n- التنفيذ Sequential بدون rollback تلقائي: لو نجحت خطوات ثم فشلت خطوة لاحقة، لا تقل إن العملية كلها نجحت ولا تدّع التراجع عن الخطوات الناجحة. اعرض النتيجة الحقيقية من executionResult: SUCCESS أو PARTIAL_SUCCESS أو FAILED، واذكر كل Step كـEXECUTED أو FAILED أو SKIPPED.\n- إذا فشل CREATE_TASK، أي Step تستهدف CREATED_TASK تُصبح SKIPPED، بينما الخطوات المستقلة الأخرى يمكن أن تستمر. لا تحاول إعادة تنفيذ الخطوات الناجحة تلقائيًا.\n'''
text = replace_once(text, anchor, anchor + addition, 'PROMPT_PHASE15')
TARGETS[rel] = text

# Approval route imports and decision behavior.
rel = 'backend/src/routes/agent.routes.js'
text = TARGETS[rel]
old = '''import { executeApprovedTaskAction, revisePendingTaskActionProposal } from "../agency-operator/services/taskCommands.service.js";\nimport { assertAgentTaskCreateAccess, isSupportedAgentAction } from "../agency-operator/policies/agentAccess.service.js";'''
new = '''import { executeApprovedTaskAction, revisePendingTaskActionProposal } from "../agency-operator/services/taskCommands.service.js";\nimport {\n  assertMultiStepApprovalStillAuthorized,\n  executeApprovedMultiStepOperation,\n  isMultiStepTaskOperationApproval,\n} from "../agency-operator/services/ramzyMultiStepOperations.service.js";\nimport { assertAgentTaskCreateAccess, isSupportedAgentAction } from "../agency-operator/policies/agentAccess.service.js";'''
text = replace_once(text, old, new, 'ROUTE_IMPORT')

old = '''  const isCreateTaskApproval = String(approval.actionType || "").toUpperCase() === "CREATE_TASK";\n  const validTargetType = isCreateTaskApproval ? approval.targetType === "PROJECT" : approval.targetType === "TASK";\n  if (!validTargetType || !isSupportedAgentAction(approval.actionType)) {\n    throw new AppError("Unsupported approval action", 400);\n  }'''
new = '''  const isMultiStepApproval = isMultiStepTaskOperationApproval(approval);\n  const isCreateTaskApproval = String(approval.actionType || "").toUpperCase() === "CREATE_TASK";\n  const validTargetType = isMultiStepApproval\n    ? approval.targetType === "CONVERSATION"\n    : (isCreateTaskApproval ? approval.targetType === "PROJECT" : approval.targetType === "TASK");\n  if (!validTargetType || (!isMultiStepApproval && !isSupportedAgentAction(approval.actionType))) {\n    throw new AppError("Unsupported approval action", 400);\n  }'''
text = replace_once(text, old, new, 'ROUTE_TARGET')

old = '''  if (isCreateTaskApproval) {\n    await assertAgentTaskCreateAccess(req.user, approval.targetId, settings.allowedWorkspaceIds, prisma);\n  } else {\n    await assertTaskWithinAgentWorkspaceScope(req.user, approval.targetId, settings.allowedWorkspaceIds);\n  }'''
new = '''  if (isMultiStepApproval) {\n    await assertMultiStepApprovalStillAuthorized({ approval, user: req.user });\n  } else if (isCreateTaskApproval) {\n    await assertAgentTaskCreateAccess(req.user, approval.targetId, settings.allowedWorkspaceIds, prisma);\n  } else {\n    await assertTaskWithinAgentWorkspaceScope(req.user, approval.targetId, settings.allowedWorkspaceIds);\n  }'''
text = replace_once(text, old, new, 'ROUTE_PRECLAIM_RBAC')

old = '''  try {\n    const result = await executeApprovedTaskAction({\n      approval: executingApproval,\n      user: req.user,\n      io: req.app.get("io"),\n    });\n    const approved = await prisma.agentApprovalRequest.update({\n      where: { id: approval.id },\n      data: {\n        status: "EXECUTED",\n        executedAt: new Date(),\n        executionResult: result,\n        executionError: null,\n      },\n    });\n    await finishToolExecution(approval, "SUCCEEDED", { output: result });\n    req.app.get("io")?.to(`user:${req.user.id}`).emit("ramzy:approval", approved);\n    return res.json(approved);\n  } catch (error) {'''
new = '''  try {\n    const result = isMultiStepApproval\n      ? await executeApprovedMultiStepOperation({\n        approval: executingApproval,\n        user: req.user,\n        io: req.app.get("io"),\n      })\n      : await executeApprovedTaskAction({\n        approval: executingApproval,\n        user: req.user,\n        io: req.app.get("io"),\n      });\n    const multiStepAllFailed = Boolean(isMultiStepApproval && result?.outcome === "FAILED");\n    const finalStatus = multiStepAllFailed ? "FAILED" : "EXECUTED";\n    const finalError = multiStepAllFailed ? "لم تنجح أي خطوة في العملية المركبة. راجع نتيجة كل خطوة." : null;\n    const finalized = await prisma.agentApprovalRequest.update({\n      where: { id: approval.id },\n      data: {\n        status: finalStatus,\n        executedAt: multiStepAllFailed ? undefined : new Date(),\n        executionResult: result,\n        executionError: finalError,\n      },\n    });\n    await finishToolExecution(approval, multiStepAllFailed ? "FAILED" : "SUCCEEDED", { output: result, error: finalError });\n    req.app.get("io")?.to(`user:${req.user.id}`).emit("ramzy:approval", finalized);\n    return res.json(finalized);\n  } catch (error) {'''
text = replace_once(text, old, new, 'ROUTE_EXECUTION')
TARGETS[rel] = text

# Frontend labels and safe plan/result rendering.
rel = 'frontend/src/components/RamzyAssistant.jsx'
text = TARGETS[rel]
old = '''  CHANGE_ASSIGNEE: { ar: "تغيير منفذ المهمة", en: "Change assignee" },\n};'''
new = '''  CHANGE_ASSIGNEE: { ar: "تغيير منفذ المهمة", en: "Change assignee" },\n  MULTI_STEP_TASK_OPERATION: { ar: "عملية مهام متعددة الخطوات", en: "Multi-step task operation" },\n};'''
text = replace_once(text, old, new, 'FRONTEND_LABEL')

old = '''  if (approval?.actionType === "CHANGE_DUE_DATE") return payload.dueDate\n    ? `Change task due date to ${new Date(payload.dueDate).toLocaleString("en-US")}`\n    : "Remove task due date";\n  return approvalActionLabel(approval?.actionType, true);'''
new = '''  if (approval?.actionType === "CHANGE_DUE_DATE") return payload.dueDate\n    ? `Change task due date to ${new Date(payload.dueDate).toLocaleString("en-US")}`\n    : "Remove task due date";\n  if (approval?.actionType === "MULTI_STEP_TASK_OPERATION") {\n    const count = Array.isArray(payload.publicSteps) ? payload.publicSteps.length : 0;\n    return `Execute ${count || "multiple"} linked task actions`;\n  }\n  return approvalActionLabel(approval?.actionType, true);'''
text = replace_once(text, old, new, 'FRONTEND_TITLE')

anchor = '''function toDateTimeLocal(value) {'''
helpers = r'''function multiStepPlan(approval) {
  if (approval?.actionType !== "MULTI_STEP_TASK_OPERATION") return [];
  const payload = approval?.payload && typeof approval.payload === "object" ? approval.payload : {};
  return Array.isArray(payload.publicSteps) ? payload.publicSteps.filter((step) => step && step.summary) : [];
}

function multiStepExecution(approval) {
  if (approval?.actionType !== "MULTI_STEP_TASK_OPERATION") return null;
  const result = approval?.executionResult && typeof approval.executionResult === "object" ? approval.executionResult : null;
  return result?.version === "RAMZY_MULTI_STEP_OPERATIONS_V1" ? result : null;
}

function multiStepOutcomeLabel(outcome, isEnglish) {
  const labels = {
    SUCCESS: { ar: "اكتملت كل الخطوات", en: "All steps completed" },
    PARTIAL_SUCCESS: { ar: "نجاح جزئي", en: "Partial success" },
    FAILED: { ar: "لم تنجح أي خطوة", en: "No steps succeeded" },
  };
  return labels[String(outcome || "").toUpperCase()]?.[isEnglish ? "en" : "ar"] || String(outcome || "");
}

function multiStepStepStatusLabel(status, isEnglish) {
  const labels = {
    EXECUTED: { ar: "تمت", en: "Executed" },
    FAILED: { ar: "فشلت", en: "Failed" },
    SKIPPED: { ar: "تم تخطيها", en: "Skipped" },
  };
  return labels[String(status || "").toUpperCase()]?.[isEnglish ? "en" : "ar"] || String(status || "");
}

'''
text = replace_once(text, anchor, helpers + anchor, 'FRONTEND_HELPERS')

old = '''  const revisionSupported = pending && confirmation.revisionSupported === true;\n  return ('''
new = '''  const revisionSupported = pending && confirmation.revisionSupported === true;\n  const multiPlan = multiStepPlan(approval);\n  const multiResult = multiStepExecution(approval);\n  return ('''
text = replace_once(text, old, new, 'FRONTEND_CARD_STATE')

old = '''      {approval.reason && <p>{approval.reason}</p>}\n      <small>{isEnglish ? "Action" : "الإجراء"}: {approvalActionLabel(approval.actionType, isEnglish)}</small>'''
new = '''      {approval.reason && <p>{approval.reason}</p>}\n      {multiPlan.length > 0 && (\n        <div className="ramzy-multistep-plan">\n          <strong>{isEnglish ? "Planned steps" : "الخطوات المخططة"}</strong>\n          <ol>{multiPlan.map((step) => <li key={`${step.stepNumber}-${step.actionType}`}>{step.summary}</li>)}</ol>\n        </div>\n      )}\n      {multiResult && (\n        <div className={`ramzy-multistep-result outcome-${String(multiResult.outcome || "").toLowerCase()}`}>\n          <strong>{multiStepOutcomeLabel(multiResult.outcome, isEnglish)}</strong>\n          <span>{isEnglish\n            ? `${multiResult.executedSteps || 0} executed • ${multiResult.failedSteps || 0} failed • ${multiResult.skippedSteps || 0} skipped`\n            : `${multiResult.executedSteps || 0} تمت • ${multiResult.failedSteps || 0} فشلت • ${multiResult.skippedSteps || 0} تم تخطيها`}</span>\n          <ol>{(Array.isArray(multiResult.steps) ? multiResult.steps : []).map((step) => (\n            <li key={`${step.stepNumber}-${step.actionType}-${step.status}`}>\n              <b>{multiStepStepStatusLabel(step.status, isEnglish)}:</b> {step.summary}{step.error ? ` — ${step.error}` : ""}\n            </li>\n          ))}</ol>\n        </div>\n      )}\n      <small>{isEnglish ? "Action" : "الإجراء"}: {approvalActionLabel(approval.actionType, isEnglish)}</small>'''
text = replace_once(text, old, new, 'FRONTEND_CARD_RENDER')
TARGETS[rel] = text

# Validate all transformations in memory before writing anything.
required_markers = {
    'backend/src/agency-operator/tools/createRamzyTools.js': ['propose_multi_step_task_operation', 'createMultiStepTaskOperationProposal', 'proposeMultiStepTaskOperationTool'],
    'backend/src/agency-operator/services/ramzyRuntime.service.js': ['propose_multi_step_task_operation'],
    'backend/src/agency-operator/prompts/ramzyPrompt.js': ['Phase 15:', 'Multi-Step Voice Operations', 'PARTIAL_SUCCESS'],
    'backend/src/routes/agent.routes.js': ['isMultiStepTaskOperationApproval', 'assertMultiStepApprovalStillAuthorized', 'executeApprovedMultiStepOperation', 'targetType === "CONVERSATION"'],
    'frontend/src/components/RamzyAssistant.jsx': ['MULTI_STEP_TASK_OPERATION', 'multiStepPlan', 'multiStepExecution', 'PARTIAL_SUCCESS'],
}
for rel, markers in required_markers.items():
    for marker in markers:
        if marker not in TARGETS[rel]:
            raise SystemExit(f'PHASE15_PATCH_ERROR=MARKER_MISSING:{rel}:{marker}')

service_path = ROOT / 'backend/src/agency-operator/services/ramzyMultiStepOperations.service.js'
test_path = ROOT / 'backend/src/agency-operator/tests/ramzyMultiStepVoiceOperationsPhase15.static.test.js'
if service_path.exists() or test_path.exists():
    raise SystemExit('PHASE15_PATCH_ERROR=NEW_FILE_ALREADY_EXISTS')

for rel, content in TARGETS.items():
    (ROOT / rel).write_text(content, encoding='utf-8')
service_path.write_text(SERVICE, encoding='utf-8')
test_path.write_text(TEST, encoding='utf-8')
print('PHASE15_MULTI_STEP_VOICE_OPERATIONS_PATCH=PASS')
