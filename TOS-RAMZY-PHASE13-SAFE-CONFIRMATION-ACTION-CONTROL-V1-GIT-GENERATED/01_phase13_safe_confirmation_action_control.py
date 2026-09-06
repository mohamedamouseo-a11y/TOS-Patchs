#!/usr/bin/env python3
from pathlib import Path

ROOT = Path('/var/www/TOS')


def read(rel):
    return (ROOT / rel).read_text(encoding='utf-8')


def replace_exact(text, old, new, label, expected=1):
    if new in text:
        return text
    count = text.count(old)
    if count != expected:
        raise SystemExit(f'PHASE13_PATCH_ERROR={label}_COUNT_{count}')
    return text.replace(old, new, expected)


def replace_all_exact(text, old, new, label, expected):
    if new in text and old not in text:
        return text
    count = text.count(old)
    if count != expected:
        raise SystemExit(f'PHASE13_PATCH_ERROR={label}_COUNT_{count}')
    return text.replace(old, new)


TARGETS = {
    'backend/src/agency-operator/services/taskCommands.service.js': read('backend/src/agency-operator/services/taskCommands.service.js'),
    'backend/src/agency-operator/tools/createRamzyTools.js': read('backend/src/agency-operator/tools/createRamzyTools.js'),
    'backend/src/agency-operator/services/ramzyRuntime.service.js': read('backend/src/agency-operator/services/ramzyRuntime.service.js'),
    'backend/src/routes/agent.routes.js': read('backend/src/routes/agent.routes.js'),
    'backend/src/agency-operator/prompts/ramzyPrompt.js': read('backend/src/agency-operator/prompts/ramzyPrompt.js'),
    'frontend/src/lib/api.js': read('frontend/src/lib/api.js'),
    'frontend/src/components/RamzyAssistant.jsx': read('frontend/src/components/RamzyAssistant.jsx'),
}

confirmation_service = r'''const CONFIRMATION_VERSION = "RAMZY_ACTION_CONFIRMATION_V1";

const ACTION_POLICIES = Object.freeze({
  CREATE_TASK: Object.freeze({ riskLevel: "HIGH", directExecutionEligible: false, revisionFields: ["title", "description", "priority", "dueDate"] }),
  CHANGE_ASSIGNEE: Object.freeze({ riskLevel: "HIGH", directExecutionEligible: false, revisionFields: [] }),
  CHANGE_DUE_DATE: Object.freeze({ riskLevel: "MEDIUM", directExecutionEligible: false, revisionFields: ["dueDate"] }),
  ADD_CHECKLIST: Object.freeze({ riskLevel: "MEDIUM", directExecutionEligible: false, revisionFields: ["title"] }),
  ADD_COMMENT: Object.freeze({ riskLevel: "LOW", directExecutionEligible: true, revisionFields: ["body"] }),
});

function envFlag(name, fallback = false) {
  const raw = process.env[name];
  if (raw === undefined) return fallback;
  return ["1", "true", "yes", "on"].includes(String(raw).toLowerCase());
}

function normalizedAction(value) {
  return String(value || "").trim().toUpperCase();
}

function compact(value, max = 240) {
  return String(value || "").trim().replace(/\s+/g, " ").slice(0, max) || null;
}

function safeDueDate(value) {
  if (!value) return null;
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? null : parsed.toISOString();
}

function impactSummary(actionType, payload = {}) {
  const action = normalizedAction(actionType);
  const summary = { actionType: action, headline: null, details: [] };
  if (action === "CREATE_TASK") {
    const title = compact(payload.title, 180) || "مهمة جديدة";
    summary.headline = `إنشاء مهمة «${title}»`;
    if (compact(payload.projectName, 160)) summary.details.push(`المشروع: ${compact(payload.projectName, 160)}`);
    if (compact(payload.assigneeName, 160)) summary.details.push(`المنفذ: ${compact(payload.assigneeName, 160)}`);
    if (safeDueDate(payload.dueDate)) summary.details.push(`الموعد: ${safeDueDate(payload.dueDate)}`);
    if (compact(payload.priority, 40)) summary.details.push(`الأولوية: ${compact(payload.priority, 40)}`);
  } else if (action === "CHANGE_ASSIGNEE") {
    summary.headline = `تغيير منفذ المهمة إلى ${compact(payload.assigneeName, 160) || "الموظف المحدد"}`;
  } else if (action === "CHANGE_DUE_DATE") {
    summary.headline = safeDueDate(payload.dueDate) ? `تغيير موعد المهمة إلى ${safeDueDate(payload.dueDate)}` : "إزالة موعد المهمة";
  } else if (action === "ADD_CHECKLIST") {
    summary.headline = `إضافة Checklist: ${compact(payload.title, 180) || "عنصر جديد"}`;
  } else if (action === "ADD_COMMENT") {
    summary.headline = `إضافة تعليق: ${compact(payload.body, 220) || "تعليق جديد"}`;
  }
  return summary;
}

export function getActionConfirmationPolicy(actionType, settings = {}) {
  const action = normalizedAction(actionType);
  const profile = ACTION_POLICIES[action] || null;
  if (!profile) {
    return {
      version: CONFIRMATION_VERSION,
      supported: false,
      actionType: action,
      riskLevel: "UNKNOWN",
      explicitConfirmationRequired: true,
      directExecutionEligible: false,
      directExecutionEnabled: false,
      revisionSupported: false,
      revisionFields: [],
      serverOptIn: false,
    };
  }

  const serverOptIn = envFlag("RAMZY_LOW_RISK_DIRECT_ACTIONS", false);
  const directExecutionEnabled = Boolean(
    profile.riskLevel === "LOW"
    && profile.directExecutionEligible
    && serverOptIn
    && settings.readOnlyMode !== true
    && settings.approvalActionsEnabled !== false,
  );

  return {
    version: CONFIRMATION_VERSION,
    supported: true,
    actionType: action,
    riskLevel: profile.riskLevel,
    explicitConfirmationRequired: !directExecutionEnabled,
    directExecutionEligible: Boolean(profile.directExecutionEligible),
    directExecutionEnabled,
    revisionSupported: profile.revisionFields.length > 0,
    revisionFields: [...profile.revisionFields],
    serverOptIn,
  };
}

export function buildActionConfirmationMetadata({ actionType, payload = {}, settings = {}, revisionCount = 0 } = {}) {
  const policy = getActionConfirmationPolicy(actionType, settings);
  return {
    version: CONFIRMATION_VERSION,
    riskLevel: policy.riskLevel,
    explicitConfirmationRequired: policy.explicitConfirmationRequired,
    directExecutionEligible: policy.directExecutionEligible,
    directExecutionEnabled: policy.directExecutionEnabled,
    revisionSupported: policy.revisionSupported,
    revisionFields: policy.revisionFields,
    revisionCount: Math.max(0, Math.min(99, Number(revisionCount || 0))),
    impactSummary: impactSummary(actionType, payload),
  };
}

export function getActionRevisionFields(actionType) {
  const action = normalizedAction(actionType);
  return [...(ACTION_POLICIES[action]?.revisionFields || [])];
}

export function assertLowRiskDirectActionAllowed(actionType, settings = {}) {
  const policy = getActionConfirmationPolicy(actionType, settings);
  if (!policy.supported || policy.riskLevel !== "LOW" || !policy.directExecutionEligible || !policy.directExecutionEnabled) {
    const error = new Error("Direct execution is not allowed for this action");
    error.status = 403;
    error.code = "RAMZY_DIRECT_ACTION_NOT_ALLOWED";
    throw error;
  }
  return policy;
}

export function getActionConfirmationConfig() {
  return {
    version: CONFIRMATION_VERSION,
    safeDefault: "EXPLICIT_CONFIRMATION",
    lowRiskDirectEnvironmentFlag: "RAMZY_LOW_RISK_DIRECT_ACTIONS",
    directExecutionAllowlist: Object.entries(ACTION_POLICIES).filter(([, value]) => value.directExecutionEligible).map(([key]) => key),
    policies: Object.fromEntries(Object.entries(ACTION_POLICIES).map(([key, value]) => [key, {
      riskLevel: value.riskLevel,
      directExecutionEligible: value.directExecutionEligible,
      revisionFields: [...value.revisionFields],
    }])),
  };
}
'''

test_content = r'''import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";
import {
  buildActionConfirmationMetadata,
  getActionConfirmationConfig,
  getActionConfirmationPolicy,
  getActionRevisionFields,
} from "../services/actionConfirmation.service.js";

const here = path.dirname(fileURLToPath(import.meta.url));
const backendSrc = path.resolve(here, "../..");
const repoRoot = path.resolve(backendSrc, "../..");
const readBackend = (relative) => readFile(path.join(backendSrc, relative), "utf8");
const readRepo = (relative) => readFile(path.join(repoRoot, relative), "utf8");

test("Phase 13 risk policy requires confirmation for impactful actions", () => {
  const settings = { readOnlyMode: false, approvalActionsEnabled: true };
  assert.equal(getActionConfirmationPolicy("CREATE_TASK", settings).riskLevel, "HIGH");
  assert.equal(getActionConfirmationPolicy("CREATE_TASK", settings).explicitConfirmationRequired, true);
  assert.equal(getActionConfirmationPolicy("CHANGE_ASSIGNEE", settings).directExecutionEligible, false);
  assert.equal(getActionConfirmationPolicy("CHANGE_DUE_DATE", settings).riskLevel, "MEDIUM");
  assert.equal(getActionConfirmationPolicy("ADD_CHECKLIST", settings).explicitConfirmationRequired, true);
});

test("Phase 13 low-risk direct execution is server opt-in and cannot widen to high/medium", () => {
  const previous = process.env.RAMZY_LOW_RISK_DIRECT_ACTIONS;
  process.env.RAMZY_LOW_RISK_DIRECT_ACTIONS = "true";
  try {
    const settings = { readOnlyMode: false, approvalActionsEnabled: true };
    assert.equal(getActionConfirmationPolicy("ADD_COMMENT", settings).directExecutionEnabled, true);
    assert.equal(getActionConfirmationPolicy("CREATE_TASK", settings).directExecutionEnabled, false);
    assert.equal(getActionConfirmationPolicy("CHANGE_ASSIGNEE", settings).directExecutionEnabled, false);
    assert.equal(getActionConfirmationPolicy("CHANGE_DUE_DATE", settings).directExecutionEnabled, false);
    assert.equal(getActionConfirmationPolicy("ADD_CHECKLIST", settings).directExecutionEnabled, false);
  } finally {
    if (previous === undefined) delete process.env.RAMZY_LOW_RISK_DIRECT_ACTIONS;
    else process.env.RAMZY_LOW_RISK_DIRECT_ACTIONS = previous;
  }
});

test("Phase 13 confirmation metadata is human-readable and excludes internal IDs", () => {
  const metadata = buildActionConfirmationMetadata({
    actionType: "CREATE_TASK",
    settings: { readOnlyMode: false, approvalActionsEnabled: true },
    payload: {
      title: "راجع البنر",
      projectName: "Cuir",
      assigneeName: "Youssef",
      projectId: "cprojectinternal1234567890",
      assigneeId: "cuserinternal123456789012",
    },
  });
  const serialized = JSON.stringify(metadata);
  assert.match(serialized, /Cuir/);
  assert.match(serialized, /Youssef/);
  assert.doesNotMatch(serialized, /cprojectinternal1234567890/);
  assert.doesNotMatch(serialized, /cuserinternal123456789012/);
});

test("Phase 13 revision fields never allow project or assignee ID mutation", () => {
  assert.deepEqual(getActionRevisionFields("CREATE_TASK"), ["title", "description", "priority", "dueDate"]);
  assert.deepEqual(getActionRevisionFields("CHANGE_ASSIGNEE"), []);
  assert.ok(!getActionRevisionFields("CREATE_TASK").includes("projectId"));
  assert.ok(!getActionRevisionFields("CREATE_TASK").includes("assigneeId"));
  assert.equal(getActionConfirmationConfig().safeDefault, "EXPLICIT_CONFIRMATION");
});

test("Phase 13 tool, route, runtime and UI preserve approval control", async () => {
  const commands = await readBackend("agency-operator/services/taskCommands.service.js");
  const tools = await readBackend("agency-operator/tools/createRamzyTools.js");
  const runtime = await readBackend("agency-operator/services/ramzyRuntime.service.js");
  const routes = await readBackend("routes/agent.routes.js");
  const prompt = await readBackend("agency-operator/prompts/ramzyPrompt.js");
  const ui = await readRepo("frontend/src/components/RamzyAssistant.jsx");
  const api = await readRepo("frontend/src/lib/api.js");

  assert.match(commands, /revisePendingTaskActionProposal/);
  assert.match(commands, /assertLowRiskDirectActionAllowed/);
  assert.match(commands, /executeApprovedTaskAction/);
  assert.match(tools, /revise_task_action_proposal/);
  assert.match(tools, /executeLowRiskTaskActionApproval/);
  assert.match(tools, /String\(output\?\.status \|\| ""\)\.toUpperCase\(\) === "PENDING"/);
  assert.match(runtime, /revise_task_action_proposal/);
  assert.match(runtime, /hasWaitingApproval/);
  assert.match(routes, /approvals\/:approvalId\/revise/);
  assert.match(prompt, /Phase 13:/);
  assert.match(prompt, /Risk Policy/);
  assert.match(ui, /ramzy-confirmation-risk/);
  assert.match(ui, /RevisionEditor/);
  assert.match(api, /reviseApproval/);
  assert.doesNotMatch(ui, /confirmation[\s\S]{0,1200}targetId/);
});
'''

css_content = r'''.ramzy-confirmation-strip {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-top: 9px;
}

.ramzy-confirmation-risk,
.ramzy-confirmation-mode,
.ramzy-confirmation-revision-count {
  display: inline-flex;
  align-items: center;
  min-height: 26px;
  padding: 4px 9px;
  border: 1px solid currentColor;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 800;
  line-height: 1;
  opacity: .88;
}

.ramzy-confirmation-risk.risk-high { font-weight: 950; }
.ramzy-confirmation-risk.risk-medium { font-weight: 900; }
.ramzy-confirmation-risk.risk-low { font-weight: 800; }

.ramzy-revision-editor {
  display: grid;
  gap: 9px;
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid rgba(127, 127, 127, .22);
}

.ramzy-revision-editor label {
  display: grid;
  gap: 5px;
  font-size: 11px;
  font-weight: 800;
}

.ramzy-revision-editor input,
.ramzy-revision-editor textarea,
.ramzy-revision-editor select {
  width: 100%;
  border: 1px solid rgba(127, 127, 127, .3);
  border-radius: 10px;
  padding: 8px 10px;
  background: transparent;
  color: inherit;
  font: inherit;
}

.ramzy-revision-editor textarea {
  min-height: 72px;
  resize: vertical;
}

.ramzy-revision-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.ramzy-approval-actions .secondary,
.ramzy-revision-actions .secondary {
  background: transparent;
  border: 1px solid rgba(127, 127, 127, .35);
  color: inherit;
}
'''

# taskCommands.service.js
rel = 'backend/src/agency-operator/services/taskCommands.service.js'
text = TARGETS[rel]
text = replace_exact(
    text,
    'import { getAgentSettings } from "./agentSettings.service.js";',
    'import { getAgentSettings } from "./agentSettings.service.js";\nimport {\n  assertLowRiskDirectActionAllowed,\n  buildActionConfirmationMetadata,\n  getActionConfirmationPolicy,\n  getActionRevisionFields,\n} from "./actionConfirmation.service.js";',
    'TASK_COMMAND_CONFIRMATION_IMPORT',
)
helper_block = r'''
function confirmationRevisionCount(payload = {}) {
  return Math.max(0, Math.min(99, Number(payload?.confirmation?.revisionCount || 0)));
}

function withActionConfirmation(actionType, payload, settings, revisionCount = 0) {
  const clean = { ...(payload && typeof payload === "object" ? payload : {}) };
  delete clean.confirmation;
  return {
    ...clean,
    confirmation: buildActionConfirmationMetadata({ actionType, payload: clean, settings, revisionCount }),
  };
}

function approvalTitleFromPayload(actionType, payload = {}, fallback = "") {
  if (actionType === "CREATE_TASK") {
    return `إنشاء مهمة «${payload.title || "مهمة جديدة"}»${payload.projectName ? ` في ${payload.projectName}` : ""}${payload.assigneeName ? ` وإسنادها إلى ${payload.assigneeName}` : ""}`.slice(0, 240);
  }
  if (actionType === "CHANGE_DUE_DATE") {
    return payload.dueDate
      ? `تغيير موعد المهمة إلى ${new Date(payload.dueDate).toLocaleString("ar-EG")}`
      : "إزالة موعد المهمة";
  }
  if (actionType === "CHANGE_ASSIGNEE") return `استبدال منفذي المهمة بـ ${payload.assigneeName || "الموظف المحدد"}`.slice(0, 240);
  return TITLE_MAP[actionType] || fallback || "إجراء رمزي";
}

function normalizeApprovalRevision(actionType, currentPayload = {}, revision = {}, settings = {}) {
  const allowed = new Set(getActionRevisionFields(actionType));
  if (!allowed.size) throw new AppError("هذا النوع يحتاج اختيار هدف جديد من خلال رمزي ولا يمكن تعديله كمسودة نصية", 409);
  const requested = ensurePlainPayload(revision);
  const keys = Object.keys(requested);
  if (!keys.length) throw new AppError("Revision fields are required", 400);
  const forbidden = keys.filter((key) => !allowed.has(key));
  if (forbidden.length) throw new AppError(`Unsupported revision field: ${forbidden[0]}`, 400);

  const base = { ...(currentPayload && typeof currentPayload === "object" ? currentPayload : {}) };
  delete base.confirmation;
  let next;
  if (actionType === "CREATE_TASK") {
    const normalized = normalizeTaskActionPayload("CREATE_TASK", { ...base, ...requested });
    next = {
      ...normalized,
      ...(base.projectName ? { projectName: String(base.projectName).slice(0, 200) } : {}),
      ...(base.assigneeName ? { assigneeName: String(base.assigneeName).slice(0, 160) } : {}),
    };
  } else {
    next = normalizeTaskActionPayload(actionType, { ...base, ...requested });
  }
  return withActionConfirmation(actionType, next, settings, confirmationRevisionCount(currentPayload) + 1);
}
'''
text = replace_exact(
    text,
    '  throw new AppError("Unsupported Ramzy action", 400);\n}\n\nfunction emitTaskChanged(io, task) {',
    '  throw new AppError("Unsupported Ramzy action", 400);\n}\n' + helper_block + '\nfunction emitTaskChanged(io, task) {',
    'TASK_COMMAND_CONFIRMATION_HELPERS',
)
text = replace_exact(
    text,
    '  const [conversation, run, execution] = await Promise.all([',
    '  approvalPayload = withActionConfirmation(normalizedAction, approvalPayload, settings, 0);\n\n  const [conversation, run, execution] = await Promise.all([',
    'TASK_COMMAND_ATTACH_CONFIRMATION',
)
control_functions = r'''
export async function revisePendingTaskActionProposal({
  user,
  conversationId = null,
  approvalId = null,
  revision = {},
  io = null,
} = {}) {
  if (!user?.id) throw new AppError("User is required", 401);
  if (!approvalId && !conversationId) throw new AppError("Approval or conversation context is required", 400);
  const approval = await prisma.agentApprovalRequest.findFirst({
    where: {
      userId: user.id,
      status: "PENDING",
      ...(approvalId ? { id: approvalId } : {}),
      ...(conversationId ? { conversationId } : {}),
    },
    orderBy: { createdAt: "desc" },
  });
  if (!approval) throw new AppError("لا توجد مسودة موافقة معلقة قابلة للتعديل", 404);
  if (approval.expiresAt && approval.expiresAt < new Date()) {
    await prisma.agentApprovalRequest.updateMany({
      where: { id: approval.id, userId: user.id, status: "PENDING" },
      data: { status: "EXPIRED", decidedAt: new Date(), decidedById: user.id },
    });
    throw new AppError("طلب الموافقة انتهت صلاحيته", 409);
  }

  const settings = await getAgentSettings();
  if (!settings.approvalActionsEnabled) throw new AppError("إجراءات رمزي متوقفة من إعدادات Super Admin", 409);
  const actionType = String(approval.actionType || "").toUpperCase();
  if (!ACTIONS.has(actionType)) throw new AppError("Unsupported approval action", 400);
  const policy = getActionConfirmationPolicy(actionType, settings);
  if (!policy.revisionSupported) throw new AppError("هذا الإجراء يحتاج طلبًا جديدًا لتثبيت الهدف بأمان", 409);

  const currentPayload = approval.payload && typeof approval.payload === "object" ? approval.payload : {};
  if (actionType === "CREATE_TASK") {
    if (approval.targetType !== "PROJECT") throw new AppError("Invalid task create target", 400);
    const { project } = await assertAgentTaskCreateAccess(user, approval.targetId, settings.allowedWorkspaceIds, prisma);
    if (currentPayload.assigneeId) await assertAssignmentTarget(user, project.id, currentPayload.assigneeId);
  } else {
    if (approval.targetType !== "TASK") throw new AppError("Invalid task action target", 400);
    await assertAgentTaskActionAccess(user, approval.targetId, actionType, settings.allowedWorkspaceIds, prisma);
  }

  const nextPayload = normalizeApprovalRevision(actionType, currentPayload, revision, settings);
  const nextTitle = approvalTitleFromPayload(actionType, nextPayload, approval.title);
  const updated = await prisma.agentApprovalRequest.updateMany({
    where: { id: approval.id, userId: user.id, status: "PENDING" },
    data: { title: nextTitle, payload: nextPayload },
  });
  if (updated.count !== 1) throw new AppError("تم التعامل مع طلب الموافقة بالفعل", 409);
  const revised = await prisma.agentApprovalRequest.findUnique({ where: { id: approval.id } });
  io?.to(`user:${user.id}`).emit("ramzy:approval", revised);
  return revised;
}

export async function executeLowRiskTaskActionApproval({ approval, user, io = null } = {}) {
  if (!approval?.id || !user?.id || approval.userId !== user.id) throw new AppError("Invalid approval context", 403);
  if (approval.status !== "PENDING") throw new AppError("Approval is not pending", 409);
  const settings = await getAgentSettings();
  if (settings.readOnlyMode) throw new AppError("رمزي يعمل في وضع الاقتراحات فقط", 409);
  if (!settings.approvalActionsEnabled) throw new AppError("تنفيذ إجراءات رمزي متوقف", 409);
  const policy = assertLowRiskDirectActionAllowed(approval.actionType, settings);

  const claimed = await prisma.agentApprovalRequest.updateMany({
    where: { id: approval.id, userId: user.id, status: "PENDING" },
    data: {
      status: "EXECUTING",
      decidedAt: new Date(),
      decidedById: user.id,
      decisionNote: "RAMZY_LOW_RISK_DIRECT_ACTION_V1",
    },
  });
  if (claimed.count !== 1) throw new AppError("Approval was already handled", 409);
  const executing = await prisma.agentApprovalRequest.findUnique({ where: { id: approval.id } });
  try {
    const result = await executeApprovedTaskAction({ approval: executing, user, io });
    const executed = await prisma.agentApprovalRequest.update({
      where: { id: approval.id },
      data: { status: "EXECUTED", executedAt: new Date(), executionResult: result, executionError: null },
    });
    io?.to(`user:${user.id}`).emit("ramzy:approval", executed);
    return { approval: executed, result, policy };
  } catch (error) {
    await prisma.agentApprovalRequest.update({
      where: { id: approval.id },
      data: { status: "FAILED", executionError: String(error?.message || error).slice(0, 2000) },
    }).catch(() => null);
    throw error;
  }
}
'''
text = replace_exact(
    text,
    'export async function executeApprovedTaskAction({ approval, user, io }) {',
    control_functions + '\nexport async function executeApprovedTaskAction({ approval, user, io }) {',
    'TASK_COMMAND_CONTROL_FUNCTIONS',
)
TARGETS[rel] = text

# createRamzyTools.js
rel = 'backend/src/agency-operator/tools/createRamzyTools.js'
text = TARGETS[rel]
text = replace_exact(
    text,
    'import { createTaskActionProposal } from "../services/taskCommands.service.js";',
    'import {\n  createTaskActionProposal,\n  executeLowRiskTaskActionApproval,\n  revisePendingTaskActionProposal,\n} from "../services/taskCommands.service.js";\nimport { getActionConfirmationPolicy } from "../services/actionConfirmation.service.js";',
    'TOOLS_ACTION_CONTROL_IMPORT',
)
text = replace_exact(
    text,
    'export function createRamzyTools({ user, conversationId, runId, settings, actionGrounding = null }) {',
    'export function createRamzyTools({ user, conversationId, runId, settings, actionGrounding = null, io = null }) {',
    'TOOLS_IO_CONTEXT',
)
text = replace_exact(
    text,
    '      const waitingApproval = Boolean(output?.created && output?.approvalId);',
    '      const waitingApproval = Boolean(output?.approvalId && String(output?.status || "").toUpperCase() === "PENDING");',
    'TOOLS_WAITING_STATUS',
)
old_proposal_return = '''      const approval = await createTaskActionProposal({
        user,
        conversationId,
        runId,
        toolExecutionId: execution.id,
        ...input,
      });
      return { created: true, approvalId: approval.id, status: approval.status, title: approval.title };
'''
new_proposal_return = '''      const approval = await createTaskActionProposal({
        user,
        conversationId,
        runId,
        toolExecutionId: execution.id,
        ...input,
      });
      const confirmationPolicy = getActionConfirmationPolicy(input.actionType, settings);
      if (confirmationPolicy.directExecutionEnabled) {
        const direct = await executeLowRiskTaskActionApproval({ approval, user, io });
        return {
          created: true,
          approvalId: direct.approval.id,
          status: direct.approval.status,
          title: direct.approval.title,
          directExecuted: true,
          riskLevel: confirmationPolicy.riskLevel,
        };
      }
      return {
        created: true,
        approvalId: approval.id,
        status: approval.status,
        title: approval.title,
        directExecuted: false,
        riskLevel: confirmationPolicy.riskLevel,
      };
'''
text = replace_exact(text, old_proposal_return, new_proposal_return, 'TOOLS_PROPOSAL_POLICY')
revise_tool = r'''

  const reviseTaskActionProposalTool = createTool({
    id: "revise_task_action_proposal",
    description: "Revise the latest pending Ramzy task-action approval draft without executing it. Only server-approved revision fields are accepted; project/assignee target IDs cannot be changed here.",
    inputSchema: z.object({
      approvalId: z.string().optional(),
      revision: z.record(z.string(), z.any()).default({}),
    }),
    execute: async (input) => executeLogged("revise_task_action_proposal", input, async () => {
      if (!settings.approvalActionsEnabled) return { revised: false, reason: "Approval actions are disabled by Super Admin" };
      const approval = await revisePendingTaskActionProposal({
        user,
        conversationId,
        approvalId: input.approvalId || null,
        revision: input.revision,
        io,
      });
      return { revised: true, approvalId: approval.id, status: approval.status, title: approval.title };
    }),
  });
'''
text = replace_exact(
    text,
    '  return {\n    getOperationalSnapshotTool,',
    revise_tool + '\n  return {\n    getOperationalSnapshotTool,',
    'TOOLS_REVISE_TOOL',
)
text = replace_exact(
    text,
    '    proposeTaskActionTool,\n  };',
    '    proposeTaskActionTool,\n    reviseTaskActionProposalTool,\n  };',
    'TOOLS_REVISE_RETURN',
)
TARGETS[rel] = text

# ramzyRuntime.service.js
rel = 'backend/src/agency-operator/services/ramzyRuntime.service.js'
text = TARGETS[rel]
text = replace_exact(
    text,
    'function isSideEffectTool(value) {\n  return toolNameFromCall(value) === "propose_task_action";\n}',
    'function isSideEffectTool(value) {\n  return ["propose_task_action", "revise_task_action_proposal"].includes(toolNameFromCall(value));\n}',
    'RUNTIME_SIDE_EFFECT_TOOLS',
)
text = replace_all_exact(
    text,
    '        actionGrounding: intelligence.actionGrounding || null,\n        settings:',
    '        actionGrounding: intelligence.actionGrounding || null,\n        io,\n        settings:',
    'RUNTIME_IO_CONTEXT',
    2,
)
text = replace_exact(
    text,
    '    await prisma.agentRun.update({\n      where: { id: run.id },\n      data: {\n        status: approvals.length ? "WAITING_APPROVAL" : "SUCCEEDED",',
    '    const hasWaitingApproval = approvals.some((approval) => ["PENDING", "EXECUTING"].includes(String(approval.status || "").toUpperCase()));\n    await prisma.agentRun.update({\n      where: { id: run.id },\n      data: {\n        status: hasWaitingApproval ? "WAITING_APPROVAL" : "SUCCEEDED",',
    'RUNTIME_PENDING_APPROVAL_STATUS',
)
TARGETS[rel] = text

# agent.routes.js
rel = 'backend/src/routes/agent.routes.js'
text = TARGETS[rel]
text = replace_exact(
    text,
    'import { executeApprovedTaskAction } from "../agency-operator/services/taskCommands.service.js";',
    'import { executeApprovedTaskAction, revisePendingTaskActionProposal } from "../agency-operator/services/taskCommands.service.js";',
    'ROUTES_REVISE_IMPORT',
)
revision_route = r'''
router.post("/approvals/:approvalId/revise", asyncHandler(async (req, res) => {
  await assertAgentEnabledForUser(req.user);
  const revised = await revisePendingTaskActionProposal({
    user: req.user,
    approvalId: req.params.approvalId,
    revision: req.body?.revision || {},
    io: req.app.get("io"),
  });
  res.json(revised);
}));

'''
text = replace_exact(
    text,
    'router.post("/approvals/:approvalId/decision", asyncHandler(async (req, res) => {',
    revision_route + 'router.post("/approvals/:approvalId/decision", asyncHandler(async (req, res) => {',
    'ROUTES_REVISE_ENDPOINT',
)
TARGETS[rel] = text

# ramzyPrompt.js
rel = 'backend/src/agency-operator/prompts/ramzyPrompt.js'
text = TARGETS[rel]
phase13 = '''- Phase 13: Safe Confirmation & Action Control هو الحكم النهائي قبل أي Side Effect. اعرض ملخص التأثير ومستوى المخاطرة من بيانات السيرفر، ولا تخترع Risk Level بنفسك.\n- Risk Policy: CREATE_TASK وCHANGE_ASSIGNEE = HIGH، وCHANGE_DUE_DATE وADD_CHECKLIST = MEDIUM، وADD_COMMENT = LOW. HIGH/MEDIUM يحتاجان اعتمادًا صريحًا دائمًا.\n- إذا قال المستخدم عدّل/غيّر المسودة قبل الاعتماد، استخدم revise_task_action_proposal على آخر Approval PENDING فقط. التعديل لا يعني التنفيذ، ولا يجوز تغيير projectId أو assigneeId بهذه الأداة.\n- تغيير الموظف المستهدف يحتاج طلبًا جديدًا يمر من Identity Resolution وRBAC؛ لا تبدّل assignee داخل Revision نصية.\n- Direct execution مسموح فقط إذا أرجع السيرفر directExecuted=true لعملية LOW-risk بعد Server Opt-in. لا تحاول تحويل HIGH/MEDIUM إلى direct ولا تعتبر الصوت موافقة إضافية.\n'''
text = replace_exact(
    text,
    '- CREATE_TASK وCHANGE_ASSIGNEE وCHANGE_DUE_DATE وADD_COMMENT وADD_CHECKLIST كلها Approval-based؛ لا تقل «تم» إلا بعد أن تصبح الموافقة EXECUTED فعليًا.\n',
    '- CREATE_TASK وCHANGE_ASSIGNEE وCHANGE_DUE_DATE وADD_COMMENT وADD_CHECKLIST كلها Approval-based افتراضيًا؛ لا تقل «تم» إلا بعد أن تصبح الموافقة EXECUTED فعليًا.\n' + phase13,
    'PROMPT_PHASE13_RULES',
)
TARGETS[rel] = text

# frontend api.js
rel = 'frontend/src/lib/api.js'
text = TARGETS[rel]
text = replace_exact(
    text,
    '    decideApproval: (id, decision, note = "") => request(`/api/agent/approvals/${id}/decision`, { method: "POST", body: JSON.stringify({ decision, note }) }),',
    '    decideApproval: (id, decision, note = "") => request(`/api/agent/approvals/${id}/decision`, { method: "POST", body: JSON.stringify({ decision, note }) }),\n    reviseApproval: (id, revision = {}) => request(`/api/agent/approvals/${id}/revise`, { method: "POST", body: JSON.stringify({ revision }) }),',
    'FRONTEND_API_REVISE',
)
TARGETS[rel] = text

# RamzyAssistant.jsx
rel = 'frontend/src/components/RamzyAssistant.jsx'
text = TARGETS[rel]
text = replace_exact(
    text,
    'import "./ramzyVoicePhase11.css";',
    'import "./ramzyVoicePhase11.css";\nimport "./ramzyActionControlPhase13.css";',
    'FRONTEND_PHASE13_CSS_IMPORT',
)
old_card = r'''function ApprovalCard({ approval, onDecision, busy, isEnglish }) {
  if (!approval) return null;
  const pending = approval.status === "PENDING";
  const detail = approvalDetail(approval, isEnglish);
  return (
    <div className="ramzy-approval-card">
      <div className="ramzy-approval-title"><Check size={16} />{approvalTitle(approval, isEnglish)}</div>
      {detail && <p className="ramzy-approval-detail">{detail}</p>}
      {approval.reason && <p>{approval.reason}</p>}
      <small>{isEnglish ? "Action" : "الإجراء"}: {approvalActionLabel(approval.actionType, isEnglish)}</small>
      {pending ? (
        <div className="ramzy-approval-actions">
          <button type="button" disabled={busy} onClick={() => onDecision(approval.id, "APPROVE")}>{isEnglish ? "Approve" : "اعتماد"}</button>
          <button type="button" disabled={busy} className="danger" onClick={() => onDecision(approval.id, "REJECT")}>{isEnglish ? "Reject" : "رفض"}</button>
        </div>
      ) : <span className={`ramzy-approval-status ${String(approval.status || "").toLowerCase()}`}>{approvalStatusLabel(approval.status, isEnglish)}</span>}
    </div>
  );
}
'''
new_card = r'''function confirmationMeta(approval) {
  const payload = approval?.payload && typeof approval.payload === "object" ? approval.payload : {};
  const confirmation = payload.confirmation && typeof payload.confirmation === "object" ? payload.confirmation : {};
  return confirmation;
}

function riskLabel(riskLevel, isEnglish) {
  const normalized = String(riskLevel || "MEDIUM").toUpperCase();
  const labels = {
    HIGH: { ar: "تأثير مرتفع", en: "High impact" },
    MEDIUM: { ar: "تأثير متوسط", en: "Medium impact" },
    LOW: { ar: "تأثير منخفض", en: "Low impact" },
  };
  return labels[normalized]?.[isEnglish ? "en" : "ar"] || normalized;
}

function toDateTimeLocal(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  const offset = date.getTimezoneOffset() * 60_000;
  return new Date(date.getTime() - offset).toISOString().slice(0, 16);
}

function RevisionEditor({ approval, onSave, onCancel, busy, isEnglish }) {
  const payload = approval?.payload && typeof approval.payload === "object" ? approval.payload : {};
  const [draft, setDraft] = useState(() => ({
    title: String(payload.title || ""),
    description: String(payload.description || ""),
    priority: String(payload.priority || "MEDIUM"),
    dueDate: toDateTimeLocal(payload.dueDate),
    body: String(payload.body || ""),
  }));

  async function submit(event) {
    event.preventDefault();
    let revision = {};
    if (approval.actionType === "CREATE_TASK") {
      revision = {
        title: draft.title,
        description: draft.description,
        priority: draft.priority,
        dueDate: draft.dueDate ? new Date(draft.dueDate).toISOString() : null,
      };
    } else if (approval.actionType === "ADD_COMMENT") {
      revision = { body: draft.body };
    } else if (approval.actionType === "ADD_CHECKLIST") {
      revision = { title: draft.title };
    } else if (approval.actionType === "CHANGE_DUE_DATE") {
      revision = { dueDate: draft.dueDate ? new Date(draft.dueDate).toISOString() : null };
    }
    const saved = await onSave(approval.id, revision);
    if (saved) onCancel();
  }

  return (
    <form className="ramzy-revision-editor" onSubmit={submit}>
      {approval.actionType === "CREATE_TASK" && (
        <>
          <label>{isEnglish ? "Task title" : "اسم المهمة"}<input value={draft.title} maxLength={500} onChange={(event) => setDraft((current) => ({ ...current, title: event.target.value }))} /></label>
          <label>{isEnglish ? "Description" : "الوصف"}<textarea value={draft.description} maxLength={10000} onChange={(event) => setDraft((current) => ({ ...current, description: event.target.value }))} /></label>
          <label>{isEnglish ? "Priority" : "الأولوية"}<select value={draft.priority} onChange={(event) => setDraft((current) => ({ ...current, priority: event.target.value }))}><option value="LOW">LOW</option><option value="MEDIUM">MEDIUM</option><option value="HIGH">HIGH</option><option value="URGENT">URGENT</option></select></label>
          <label>{isEnglish ? "Due date" : "الموعد"}<input type="datetime-local" value={draft.dueDate} onChange={(event) => setDraft((current) => ({ ...current, dueDate: event.target.value }))} /></label>
        </>
      )}
      {approval.actionType === "ADD_COMMENT" && <label>{isEnglish ? "Comment" : "التعليق"}<textarea value={draft.body} maxLength={10000} onChange={(event) => setDraft((current) => ({ ...current, body: event.target.value }))} /></label>}
      {approval.actionType === "ADD_CHECKLIST" && <label>{isEnglish ? "Checklist item" : "عنصر الـChecklist"}<input value={draft.title} maxLength={500} onChange={(event) => setDraft((current) => ({ ...current, title: event.target.value }))} /></label>}
      {approval.actionType === "CHANGE_DUE_DATE" && <label>{isEnglish ? "Due date" : "الموعد"}<input type="datetime-local" value={draft.dueDate} onChange={(event) => setDraft((current) => ({ ...current, dueDate: event.target.value }))} /></label>}
      <div className="ramzy-revision-actions">
        <button type="submit" disabled={busy}>{isEnglish ? "Save revision" : "حفظ التعديل"}</button>
        <button type="button" className="secondary" disabled={busy} onClick={onCancel}>{isEnglish ? "Cancel" : "إلغاء"}</button>
      </div>
    </form>
  );
}

function ApprovalCard({ approval, onDecision, onRevise, busy, isEnglish }) {
  const [editing, setEditing] = useState(false);
  if (!approval) return null;
  const pending = approval.status === "PENDING";
  const detail = approvalDetail(approval, isEnglish);
  const confirmation = confirmationMeta(approval);
  const riskLevel = String(confirmation.riskLevel || "MEDIUM").toUpperCase();
  const confirmationRequired = confirmation.explicitConfirmationRequired !== false;
  const revisionSupported = pending && confirmation.revisionSupported === true;
  return (
    <div className="ramzy-approval-card">
      <div className="ramzy-approval-title"><Check size={16} />{approvalTitle(approval, isEnglish)}</div>
      {detail && <p className="ramzy-approval-detail">{detail}</p>}
      <div className="ramzy-confirmation-strip" aria-label={isEnglish ? "Action safety summary" : "ملخص أمان الإجراء"}>
        <span className={`ramzy-confirmation-risk risk-${riskLevel.toLowerCase()}`}>{riskLabel(riskLevel, isEnglish)}</span>
        <span className="ramzy-confirmation-mode">{confirmationRequired ? (isEnglish ? "Confirmation required" : "يحتاج تأكيد") : (isEnglish ? "Server-approved low-risk direct" : "Direct منخفض المخاطر بتفعيل السيرفر")}</span>
        {Number(confirmation.revisionCount || 0) > 0 && <span className="ramzy-confirmation-revision-count">{isEnglish ? `Revised ${confirmation.revisionCount}x` : `تم التعديل ${confirmation.revisionCount} مرة`}</span>}
      </div>
      {approval.reason && <p>{approval.reason}</p>}
      <small>{isEnglish ? "Action" : "الإجراء"}: {approvalActionLabel(approval.actionType, isEnglish)}</small>
      {editing ? (
        <RevisionEditor approval={approval} onSave={onRevise} onCancel={() => setEditing(false)} busy={busy} isEnglish={isEnglish} />
      ) : pending ? (
        <div className="ramzy-approval-actions">
          <button type="button" disabled={busy} onClick={() => onDecision(approval.id, "APPROVE")}>{isEnglish ? "Confirm & execute" : "تأكيد وتنفيذ"}</button>
          {revisionSupported && <button type="button" disabled={busy} className="secondary" onClick={() => setEditing(true)}>{isEnglish ? "Revise draft" : "تعديل المسودة"}</button>}
          <button type="button" disabled={busy} className="danger" onClick={() => onDecision(approval.id, "REJECT")}>{isEnglish ? "Reject" : "رفض"}</button>
        </div>
      ) : <span className={`ramzy-approval-status ${String(approval.status || "").toLowerCase()}`}>{approvalStatusLabel(approval.status, isEnglish)}</span>}
    </div>
  );
}
'''
text = replace_exact(text, old_card, new_card, 'FRONTEND_APPROVAL_CONTROL_CARD')
text = replace_exact(
    text,
    '  async function feedback(messageId, rating) {',
    '''  async function reviseApproval(approvalId, revision) {
    try {
      setLoading(true);
      const updated = await api.agent.reviseApproval(approvalId, revision);
      setApprovals((current) => current.map((item) => item.id === updated.id ? updated : item));
      return true;
    } catch (err) {
      setError(getErrorMessage(err, isEnglish ? "Could not revise the approval draft." : "تعذر تعديل مسودة الموافقة."));
      return false;
    } finally {
      setLoading(false);
    }
  }

  async function feedback(messageId, rating) {''',
    'FRONTEND_REVISE_HANDLER',
)
text = replace_all_exact(
    text,
    'approval={approval} onDecision={decideApproval} busy={loading} isEnglish={isEnglish}',
    'approval={approval} onDecision={decideApproval} onRevise={reviseApproval} busy={loading} isEnglish={isEnglish}',
    'FRONTEND_REVISE_PROP',
    2,
)
TARGETS[rel] = text

# Final in-memory validation before any write: generator is atomic on transformation errors.
required = {
    'backend/src/agency-operator/services/taskCommands.service.js': ['RAMZY_LOW_RISK_DIRECT_ACTION_V1', 'revisePendingTaskActionProposal', 'buildActionConfirmationMetadata'],
    'backend/src/agency-operator/tools/createRamzyTools.js': ['revise_task_action_proposal', 'executeLowRiskTaskActionApproval', 'directExecuted'],
    'backend/src/agency-operator/services/ramzyRuntime.service.js': ['revise_task_action_proposal', 'hasWaitingApproval'],
    'backend/src/routes/agent.routes.js': ['/approvals/:approvalId/revise', 'revisePendingTaskActionProposal'],
    'backend/src/agency-operator/prompts/ramzyPrompt.js': ['Phase 13:', 'Risk Policy'],
    'frontend/src/lib/api.js': ['reviseApproval'],
    'frontend/src/components/RamzyAssistant.jsx': ['RevisionEditor', 'ramzy-confirmation-risk', 'onRevise={reviseApproval}'],
}
for rel, markers in required.items():
    for marker in markers:
        if marker not in TARGETS[rel]:
            raise SystemExit(f'PHASE13_PATCH_ERROR=FINAL_MARKER_MISSING:{rel}:{marker}')

new_files = {
    'backend/src/agency-operator/services/actionConfirmation.service.js': confirmation_service,
    'backend/src/agency-operator/tests/ramzyActionConfirmationPhase13.static.test.js': test_content,
    'frontend/src/components/ramzyActionControlPhase13.css': css_content,
}
for rel in new_files:
    path = ROOT / rel
    if path.exists():
        raise SystemExit(f'PHASE13_PATCH_ERROR=NEW_FILE_ALREADY_EXISTS:{rel}')

for rel, text in TARGETS.items():
    (ROOT / rel).write_text(text, encoding='utf-8')
for rel, text in new_files.items():
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')

print('PHASE13_SAFE_CONFIRMATION_ACTION_CONTROL_PATCH=PASS')
