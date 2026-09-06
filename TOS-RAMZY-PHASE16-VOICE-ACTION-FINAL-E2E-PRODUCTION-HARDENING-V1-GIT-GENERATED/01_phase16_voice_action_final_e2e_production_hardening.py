#!/usr/bin/env python3
from pathlib import Path
import sys

BASELINE = "f7678ab1ab7b5b0261a9e3a3a78c43533999b66d"
MARKER = "RAMZY_VOICE_ACTION_PRODUCTION_HARDENING_V1"

SERVICE_REL = "backend/src/agency-operator/services/ramzyProductionHardening.service.js"
TEST_REL = "backend/src/agency-operator/tests/ramzyVoiceActionProductionHardeningPhase16.test.js"
PROMPT_REL = "backend/src/agency-operator/prompts/ramzyPrompt.js"
RUNTIME_REL = "backend/src/agency-operator/services/ramzyRuntime.service.js"
COMMANDS_REL = "backend/src/agency-operator/services/taskCommands.service.js"
ROUTES_REL = "backend/src/routes/agent.routes.js"


def fail(reason):
    raise SystemExit(f"PHASE16_PATCH_ERROR={reason}")


def read(root, rel):
    path = root / rel
    if not path.exists():
        fail(f"MISSING_FILE:{rel}")
    return path.read_text(encoding="utf-8")


def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        fail(f"{label}_COUNT_{count}")
    return text.replace(old, new, 1)


SERVICE = r'''export const RAMZY_PRODUCTION_HARDENING_VERSION = "RAMZY_VOICE_ACTION_PRODUCTION_HARDENING_V1";
export const RAMZY_PUBLIC_APPROVAL_VERSION = "RAMZY_PUBLIC_APPROVAL_V1";
export const RAMZY_PUBLIC_ACTION_EXECUTION_VERSION = "RAMZY_PUBLIC_ACTION_EXECUTION_V1";

const MULTI_STEP_ACTION = "MULTI_STEP_TASK_OPERATION";
const MULTI_STEP_VERSION = "RAMZY_MULTI_STEP_OPERATIONS_V1";
const SAFE_STATUSES = new Set(["PENDING", "EXECUTING", "EXECUTED", "REJECTED", "FAILED", "EXPIRED"]);
const SAFE_RISKS = new Set(["LOW", "MEDIUM", "HIGH", "UNKNOWN"]);

function plainObject(value) {
  return value && typeof value === "object" && !Array.isArray(value) ? value : {};
}

function safeText(value, max = 2000) {
  return String(value || "")
    .replace(/(?:sk-|AIza|key[-_ ]?)[A-Za-z0-9_\-]{12,}/gi, "[REDACTED]")
    .replace(/Bearer\s+[A-Za-z0-9._\-]{12,}/gi, "Bearer [REDACTED]")
    .replace(/\bc[a-z0-9]{20,40}\b/gi, "[internal reference]")
    .slice(0, max);
}

function safeDueDate(value) {
  if (value === null || value === "" || value === undefined) return value ?? null;
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? null : date.toISOString();
}

function safeConfirmation(value) {
  const confirmation = plainObject(value);
  const impact = plainObject(confirmation.impactSummary);
  const riskLevel = String(confirmation.riskLevel || "UNKNOWN").toUpperCase();
  return {
    version: safeText(confirmation.version, 80) || "RAMZY_ACTION_CONFIRMATION_V1",
    riskLevel: SAFE_RISKS.has(riskLevel) ? riskLevel : "UNKNOWN",
    explicitConfirmationRequired: confirmation.explicitConfirmationRequired !== false,
    directExecutionEligible: confirmation.directExecutionEligible === true,
    directExecutionEnabled: confirmation.directExecutionEnabled === true,
    revisionSupported: confirmation.revisionSupported === true,
    revisionFields: Array.isArray(confirmation.revisionFields)
      ? confirmation.revisionFields.map((item) => safeText(item, 80)).filter(Boolean).slice(0, 12)
      : [],
    revisionCount: Math.max(0, Math.min(99, Number(confirmation.revisionCount || 0))),
    multiStep: confirmation.multiStep === true,
    impactSummary: {
      actionType: safeText(impact.actionType, 80) || null,
      headline: safeText(impact.headline, 500) || null,
      details: Array.isArray(impact.details)
        ? impact.details.map((item) => safeText(item, 500)).filter(Boolean).slice(0, 12)
        : [],
    },
  };
}

function publicStep(value, index) {
  const step = plainObject(value);
  return {
    stepNumber: Math.max(1, Math.min(99, Number(step.stepNumber || index + 1))),
    actionType: safeText(step.actionType, 80),
    riskLevel: safeText(step.riskLevel, 40) || null,
    summary: safeText(step.summary, 700),
  };
}

function publicExecutionStep(value, index) {
  const step = plainObject(value);
  const status = String(step.status || "").toUpperCase();
  return {
    stepNumber: Math.max(1, Math.min(99, Number(step.stepNumber || index + 1))),
    actionType: safeText(step.actionType, 80),
    status: ["EXECUTED", "FAILED", "SKIPPED"].includes(status) ? status : "FAILED",
    summary: safeText(step.summary, 700),
    error: step.error ? safeText(step.error, 700) : null,
  };
}

function safePayload(actionType, value) {
  const payload = plainObject(value);
  const confirmation = safeConfirmation(payload.confirmation);
  if (actionType === "CREATE_TASK") {
    return {
      title: safeText(payload.title, 500),
      description: safeText(payload.description, 10_000),
      priority: safeText(payload.priority, 40) || "MEDIUM",
      dueDate: safeDueDate(payload.dueDate),
      projectName: safeText(payload.projectName, 200) || null,
      assigneeName: safeText(payload.assigneeName, 160) || null,
      confirmation,
    };
  }
  if (actionType === "ADD_COMMENT") return { body: safeText(payload.body, 10_000), confirmation };
  if (actionType === "ADD_CHECKLIST") return { title: safeText(payload.title, 500), confirmation };
  if (actionType === "CHANGE_DUE_DATE") return { dueDate: safeDueDate(payload.dueDate), confirmation };
  if (actionType === "CHANGE_ASSIGNEE") return { assigneeName: safeText(payload.assigneeName, 160) || null, confirmation };
  if (actionType === MULTI_STEP_ACTION) {
    return {
      version: payload.version === MULTI_STEP_VERSION ? MULTI_STEP_VERSION : safeText(payload.version, 100),
      executionMode: safeText(payload.executionMode, 80) || "SEQUENTIAL_NO_ROLLBACK",
      publicSteps: Array.isArray(payload.publicSteps) ? payload.publicSteps.slice(0, 5).map(publicStep) : [],
      confirmation,
    };
  }
  return { confirmation };
}

function safeExecutionResult(actionType, approval) {
  const raw = plainObject(approval.executionResult);
  if (!Object.keys(raw).length) return null;
  if (actionType === MULTI_STEP_ACTION && raw.version === MULTI_STEP_VERSION) {
    const outcome = String(raw.outcome || "FAILED").toUpperCase();
    return {
      version: MULTI_STEP_VERSION,
      outcome: ["SUCCESS", "PARTIAL_SUCCESS", "FAILED"].includes(outcome) ? outcome : "FAILED",
      partialSuccess: outcome === "PARTIAL_SUCCESS",
      executionMode: safeText(raw.executionMode, 80) || "SEQUENTIAL_NO_ROLLBACK",
      rollbackApplied: false,
      totalSteps: Math.max(0, Number(raw.totalSteps || 0)),
      executedSteps: Math.max(0, Number(raw.executedSteps || 0)),
      failedSteps: Math.max(0, Number(raw.failedSteps || 0)),
      skippedSteps: Math.max(0, Number(raw.skippedSteps || 0)),
      steps: Array.isArray(raw.steps) ? raw.steps.slice(0, 5).map(publicExecutionStep) : [],
    };
  }
  const status = String(approval.status || "").toUpperCase();
  const confirmation = safeConfirmation(plainObject(approval.payload).confirmation);
  return {
    version: RAMZY_PUBLIC_ACTION_EXECUTION_VERSION,
    actionType,
    outcome: status === "EXECUTED" ? "SUCCESS" : status === "FAILED" ? "FAILED" : "RECORDED",
    summary: confirmation.impactSummary.headline || safeText(approval.title, 500) || null,
  };
}

export function publicRamzyApprovalView(approval) {
  const value = plainObject(approval);
  const actionType = String(value.actionType || "").toUpperCase();
  const status = String(value.status || "PENDING").toUpperCase();
  return {
    publicVersion: RAMZY_PUBLIC_APPROVAL_VERSION,
    id: String(value.id || ""),
    conversationId: String(value.conversationId || ""),
    runId: String(value.runId || ""),
    actionType,
    title: safeText(value.title, 500),
    reason: value.reason ? safeText(value.reason, 2000) : null,
    status: SAFE_STATUSES.has(status) ? status : "FAILED",
    payload: safePayload(actionType, value.payload),
    executionResult: safeExecutionResult(actionType, value),
    executionError: value.executionError ? safeText(value.executionError, 2000) : null,
    createdAt: value.createdAt || null,
    updatedAt: value.updatedAt || null,
    expiresAt: value.expiresAt || null,
    decidedAt: value.decidedAt || null,
    executedAt: value.executedAt || null,
  };
}

export function publicRamzyApprovalViews(values = []) {
  return (Array.isArray(values) ? values : []).map(publicRamzyApprovalView);
}

export function getRamzyProductionHardeningConfig() {
  return {
    version: RAMZY_PRODUCTION_HARDENING_VERSION,
    publicApprovalVersion: RAMZY_PUBLIC_APPROVAL_VERSION,
    publicTargetIdsExposed: false,
    publicRawExecutionRecordsExposed: false,
    voiceAutoSendAfterTranscription: false,
    voiceActionExecution: false,
    serverSideRbacAtExecution: true,
    impactfulActionsRequireConfirmation: true,
    multiStepExplicitConfirmation: true,
    multiStepExecutionMode: "SEQUENTIAL_NO_ROLLBACK",
    evidencePolicy: "SERVER_SIDE_RBAC",
    adminAuditRetainsInternalReferences: true,
    controlledRealActionE2e: "REQUIRES_EXPLICIT_SANDBOX_TARGET",
  };
}

export const __testables = {
  publicExecutionStep,
  publicStep,
  safeConfirmation,
  safeExecutionResult,
  safePayload,
  safeText,
};
'''

TEST = r'''import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";
import {
  getRamzyProductionHardeningConfig,
  publicRamzyApprovalView,
  RAMZY_PRODUCTION_HARDENING_VERSION,
  RAMZY_PUBLIC_APPROVAL_VERSION,
} from "../services/ramzyProductionHardening.service.js";
import { scoreIdentityNameMatch } from "../services/identityNameMatching.service.js";
import { resolveEntityCandidates } from "../services/entityResolution.service.js";
import { getActionConfirmationPolicy, getActionRevisionFields } from "../services/actionConfirmation.service.js";
import { getMultiStepOperationConfig } from "../services/ramzyMultiStepOperations.service.js";

const here = path.dirname(fileURLToPath(import.meta.url));
const backendSrc = path.resolve(here, "../..");
const repoRoot = path.resolve(backendSrc, "../..");
const readBackend = (relative) => readFile(path.join(backendSrc, relative), "utf8");
const readRepo = (relative) => readFile(path.join(repoRoot, relative), "utf8");

test("Phase 16 production hardening config keeps voice non-authoritative and public approvals ID-safe", () => {
  const config = getRamzyProductionHardeningConfig();
  assert.equal(config.version, RAMZY_PRODUCTION_HARDENING_VERSION);
  assert.equal(config.publicApprovalVersion, RAMZY_PUBLIC_APPROVAL_VERSION);
  assert.equal(config.publicTargetIdsExposed, false);
  assert.equal(config.publicRawExecutionRecordsExposed, false);
  assert.equal(config.voiceAutoSendAfterTranscription, false);
  assert.equal(config.voiceActionExecution, false);
  assert.equal(config.serverSideRbacAtExecution, true);
  assert.equal(config.multiStepExplicitConfirmation, true);
  assert.equal(config.controlledRealActionE2e, "REQUIRES_EXPLICIT_SANDBOX_TARGET");
});

test("Phase 16 single-action public approval strips target and assignee IDs while keeping safe UX metadata", () => {
  const targetId = "cprojectprivate1234567890123";
  const assigneeId = "cuserprivate123456789012345";
  const rawResultId = "ctaskprivate1234567890123456";
  const view = publicRamzyApprovalView({
    id: "approval-control-ref",
    conversationId: "conversation-control-ref",
    runId: "run-control-ref",
    userId: "private-user-id",
    toolExecutionId: "private-tool-id",
    targetType: "PROJECT",
    targetId,
    actionType: "CREATE_TASK",
    title: "إنشاء مهمة «راجع البنر»",
    status: "EXECUTED",
    payload: {
      title: "راجع البنر",
      projectName: "Cuir",
      assigneeId,
      assigneeName: "Youssef",
      confirmation: {
        version: "RAMZY_ACTION_CONFIRMATION_V1",
        riskLevel: "HIGH",
        explicitConfirmationRequired: true,
        impactSummary: { actionType: "CREATE_TASK", headline: "إنشاء مهمة راجع البنر", details: ["المشروع: Cuir", "المنفذ: Youssef"] },
      },
    },
    executionResult: { id: rawResultId, projectId: targetId, assigneeId, title: "راجع البنر" },
  });
  const serialized = JSON.stringify(view);
  assert.equal(view.id, "approval-control-ref");
  assert.equal(view.runId, "run-control-ref");
  assert.match(serialized, /Cuir/);
  assert.match(serialized, /Youssef/);
  assert.doesNotMatch(serialized, new RegExp(targetId));
  assert.doesNotMatch(serialized, new RegExp(assigneeId));
  assert.doesNotMatch(serialized, new RegExp(rawResultId));
  assert.equal(Object.prototype.hasOwnProperty.call(view, "targetId"), false);
  assert.equal(Object.prototype.hasOwnProperty.call(view.payload, "assigneeId"), false);
});

test("Phase 16 multi-step public approval exposes only public plan/result summaries", () => {
  const privateTaskId = "ctaskprivate1234567890123456";
  const view = publicRamzyApprovalView({
    id: "approval-ref",
    conversationId: "conversation-ref",
    runId: "run-ref",
    actionType: "MULTI_STEP_TASK_OPERATION",
    status: "EXECUTED",
    payload: {
      version: "RAMZY_MULTI_STEP_OPERATIONS_V1",
      executionMode: "SEQUENTIAL_NO_ROLLBACK",
      steps: [{ stepNumber: 1, actionType: "ADD_COMMENT", taskId: privateTaskId, payload: { body: "Internal" } }],
      publicSteps: [
        { stepNumber: 1, actionType: "CREATE_TASK", riskLevel: "HIGH", summary: "إنشاء مهمة Review" },
        { stepNumber: 2, actionType: "ADD_CHECKLIST", riskLevel: "MEDIUM", summary: "إضافة Checklist إلى المهمة الجديدة" },
      ],
      confirmation: { riskLevel: "HIGH", explicitConfirmationRequired: true, multiStep: true },
    },
    executionResult: {
      version: "RAMZY_MULTI_STEP_OPERATIONS_V1",
      outcome: "PARTIAL_SUCCESS",
      partialSuccess: true,
      executionMode: "SEQUENTIAL_NO_ROLLBACK",
      totalSteps: 2,
      executedSteps: 1,
      failedSteps: 1,
      skippedSteps: 0,
      steps: [
        { stepNumber: 1, actionType: "CREATE_TASK", status: "EXECUTED", summary: "إنشاء مهمة Review" },
        { stepNumber: 2, actionType: "ADD_CHECKLIST", status: "FAILED", summary: "إضافة Checklist", error: `Task ${privateTaskId} is unavailable` },
      ],
    },
  });
  const serialized = JSON.stringify(view);
  assert.equal(view.executionResult.outcome, "PARTIAL_SUCCESS");
  assert.equal(view.payload.publicSteps.length, 2);
  assert.equal(Object.prototype.hasOwnProperty.call(view.payload, "steps"), false);
  assert.doesNotMatch(serialized, new RegExp(privateTaskId));
  assert.match(serialized, /internal reference/);
});

test("Phase 16 browser boundaries serialize approvals before API, SSE/socket and direct-action delivery", async () => {
  const routes = await readBackend("routes/agent.routes.js");
  const runtime = await readBackend("agency-operator/services/ramzyRuntime.service.js");
  const commands = await readBackend("agency-operator/services/taskCommands.service.js");
  assert.match(routes, /publicRamzyApprovalViews\(approvals\)/);
  assert.match(routes, /publicRamzyApprovalView\(revised\)/);
  assert.match(routes, /publicRamzyApprovalView\(rejected\)/);
  assert.match(routes, /publicRamzyApprovalView\(finalized\)/);
  assert.match(runtime, /const publicApprovals = approvals\.map\(publicRamzyApprovalView\)/);
  assert.match(runtime, /approvals: publicApprovals/);
  assert.match(commands, /emit\("ramzy:approval", publicRamzyApprovalView\(revised\)\)/);
  assert.match(commands, /emit\("ramzy:approval", publicRamzyApprovalView\(executed\)\)/);
});

test("Phase 16 final identity matrix keeps Arabic-English variants and duplicate ambiguity safe", () => {
  for (const latin of ["Youssef", "Yousef", "Yusuf"]) {
    assert.ok(scoreIdentityNameMatch("يوسف", latin)?.score >= 0.82);
  }
  const duplicate = resolveEntityCandidates({
    query: "يوسف",
    candidates: [{ id: "u1", name: "Youssef Ahmed" }, { id: "u2", name: "Yousef Mohamed" }],
    fields: ["name"], exactFields: ["name"], entityType: "USER",
  });
  assert.equal(duplicate.entity, null);
  assert.equal(duplicate.guardDecision, "CLARIFY");
});

test("Phase 16 voice misunderstanding remains review-before-send with no voice-side execution", async () => {
  const voice = await readBackend("agency-operator/services/ramzyVoice.service.js");
  const assistant = await readRepo("frontend/src/components/RamzyAssistant.jsx");
  assert.match(voice, /autoSendAfterTranscription:\s*false/);
  assert.match(voice, /actionExecutionFromVoice:\s*false/);
  assert.match(assistant, /Review it, then send\./);
  assert.match(assistant, /تمت إضافة كلامك للبرومبت\. راجعه ثم اضغط إرسال/);
  assert.doesNotMatch(assistant, /transcript[^\n]{0,120}sendMessage\(/);
});

test("Phase 16 confirmation and change-before-confirm cannot mutate protected targets", () => {
  const createPolicy = getActionConfirmationPolicy("CREATE_TASK", { readOnlyMode: false, approvalActionsEnabled: true });
  const duePolicy = getActionConfirmationPolicy("CHANGE_DUE_DATE", { readOnlyMode: false, approvalActionsEnabled: true });
  assert.equal(createPolicy.riskLevel, "HIGH");
  assert.equal(createPolicy.explicitConfirmationRequired, true);
  assert.equal(duePolicy.riskLevel, "MEDIUM");
  assert.equal(duePolicy.explicitConfirmationRequired, true);
  assert.deepEqual(getActionRevisionFields("CREATE_TASK"), ["title", "description", "priority", "dueDate"]);
  assert.equal(getActionRevisionFields("CREATE_TASK").includes("projectId"), false);
  assert.equal(getActionRevisionFields("CREATE_TASK").includes("assigneeId"), false);
  assert.deepEqual(getActionRevisionFields("CHANGE_ASSIGNEE"), []);
});

test("Phase 16 multi-step production contract stays explicit, reauthorized, partial-aware and no-rollback", async () => {
  const config = getMultiStepOperationConfig();
  const service = await readBackend("agency-operator/services/ramzyMultiStepOperations.service.js");
  const routes = await readBackend("routes/agent.routes.js");
  assert.equal(config.alwaysExplicitConfirmation, true);
  assert.equal(config.directExecutionEnabled, false);
  assert.equal(config.executionMode, "SEQUENTIAL_NO_ROLLBACK");
  assert.match(service, /assertMultiStepApprovalStillAuthorized/);
  assert.match(service, /executeApprovedTaskAction/);
  assert.match(service, /PARTIAL_SUCCESS/);
  assert.match(service, /SKIPPED/);
  assert.ok(routes.indexOf("assertMultiStepApprovalStillAuthorized") < routes.indexOf("const claimed = await prisma.agentApprovalRequest.updateMany"));
});

test("Phase 16 evidence and audit retain server-side provenance without making internal audit a public approval", async () => {
  const evidence = await readBackend("agency-operator/services/ramzyEvidence.service.js");
  const routes = await readBackend("routes/agent.routes.js");
  assert.match(evidence, /execution\.status !== "SUCCEEDED"/);
  assert.match(evidence, /policy: "SERVER_SIDE_RBAC"/);
  assert.match(evidence, /where: \{ runId, userId: user\.id \}/);
  assert.match(routes, /router\.get\("\/audit", requireRole\("SUPER_ADMIN"\)/);
  assert.match(routes, /productionHardening: getRamzyProductionHardeningConfig\(\)/);
});

test("Phase 16 final prompt and UI preserve Arabic-English-mixed safety reporting and no raw target rendering", async () => {
  const prompt = await readBackend("agency-operator/prompts/ramzyPrompt.js");
  const assistant = await readRepo("frontend/src/components/RamzyAssistant.jsx");
  assert.match(prompt, /Phase 16:/);
  assert.match(prompt, /Public Approval Boundary/);
  assert.match(prompt, /misheard|سماع/iu);
  assert.match(prompt, /PARTIAL_SUCCESS/);
  assert.match(assistant, /Confirm & execute/);
  assert.match(assistant, /تأكيد وتنفيذ/);
  assert.match(assistant, /publicSteps/);
  assert.doesNotMatch(assistant, /المهمة: \{approval\.targetId\}/);
  assert.doesNotMatch(assistant, /payload\.assigneeName \|\| payload\.assigneeId/);
});
'''


def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS").resolve()
    if not root.exists():
        fail("TOS_ROOT_NOT_FOUND")
    service_path = root / SERVICE_REL
    test_path = root / TEST_REL
    if service_path.exists():
        fail("PHASE16_SERVICE_ALREADY_EXISTS")
    if test_path.exists():
        fail("PHASE16_TEST_ALREADY_EXISTS")

    prompt = read(root, PROMPT_REL)
    runtime = read(root, RUNTIME_REL)
    commands = read(root, COMMANDS_REL)
    routes = read(root, ROUTES_REL)

    for text, label in [(prompt, "PROMPT"), (runtime, "RUNTIME"), (commands, "COMMANDS"), (routes, "ROUTES")]:
        if MARKER in text:
            fail(f"{label}_ALREADY_PHASE16")

    prompt_anchor = '- إذا فشل CREATE_TASK، أي Step تستهدف CREATED_TASK تُصبح SKIPPED، بينما الخطوات المستقلة الأخرى يمكن أن تستمر. لا تحاول إعادة تنفيذ الخطوات الناجحة تلقائيًا.\n- أعطِ الأولوية للتأخير، SLA، العوائق، المهام غير المسندة، وضغط العمل.'
    prompt_insert = '- إذا فشل CREATE_TASK، أي Step تستهدف CREATED_TASK تُصبح SKIPPED، بينما الخطوات المستقلة الأخرى يمكن أن تستمر. لا تحاول إعادة تنفيذ الخطوات الناجحة تلقائيًا.\n- Phase 16: Voice & Action Final E2E / Production Hardening يستخدم RAMZY_VOICE_ACTION_PRODUCTION_HARDENING_V1 وPublic Approval Boundary؛ أي Approval يخرج للمتصفح أو Socket يجب أن يكون public view آمنًا بلا targetId أو assigneeId أو raw execution records.\n- لو النص الصوتي غير واضح أو يحتمل misheard/سماع خاطئ، لا تستنتج Side Effect من نفسك: النص يظل للمراجعة قبل الإرسال، وبعد الإرسال يمر Identity Resolution وClarification وRBAC كأي نص عادي.\n- بعد Confirm، اعتمد فقط على status وexecutionResult الآمنين في تقرير النجاح أو الفشل. لا تقل تم إذا كانت النتيجة FAILED، وفي PARTIAL_SUCCESS اذكر الخطوات EXECUTED/FAILED/SKIPPED كما سجلها السيرفر.\n- الـAudit الداخلي قد يحتفظ بالمراجع التقنية للـSuper Admin، لكن لا تنقل هذه المراجع إلى رد المستخدم أو Approval UI. الصوت والذاكرة والـAI Provider لا يملكون صلاحية مستقلة.\n- أعطِ الأولوية للتأخير، SLA، العوائق، المهام غير المسندة، وضغط العمل.'
    prompt = replace_once(prompt, prompt_anchor, prompt_insert, "PROMPT_PHASE16_ANCHOR")

    runtime_import_anchor = 'import { buildRamzyRunEvidence, RAMZY_EVIDENCE_VERSION } from "./ramzyEvidence.service.js";\n'
    runtime_import_new = runtime_import_anchor + 'import { publicRamzyApprovalView } from "./ramzyProductionHardening.service.js";\n'
    runtime = replace_once(runtime, runtime_import_anchor, runtime_import_new, "RUNTIME_IMPORT")
    runtime_wait_anchor = '    const hasWaitingApproval = approvals.some((approval) => ["PENDING", "EXECUTING"].includes(String(approval.status || "").toUpperCase()));\n'
    runtime_wait_new = runtime_wait_anchor + '    const publicApprovals = approvals.map(publicRamzyApprovalView);\n'
    runtime = replace_once(runtime, runtime_wait_anchor, runtime_wait_new, "RUNTIME_PUBLIC_APPROVALS")
    runtime = replace_once(
        runtime,
        '      approvals,\n    });\n    return { message: assistantMessage, approvals, runId: run.id, fallback, memory: memory.stats, systemIntelligence: intelligence.metadata, evidence };',
        '      approvals: publicApprovals,\n    });\n    return { message: assistantMessage, approvals: publicApprovals, runId: run.id, fallback, memory: memory.stats, systemIntelligence: intelligence.metadata, evidence };',
        "RUNTIME_RETURN_BOUNDARY",
    )

    commands_import_anchor = '} from "./actionConfirmation.service.js";\n'
    commands_import_new = commands_import_anchor + 'import { publicRamzyApprovalView } from "./ramzyProductionHardening.service.js";\n'
    commands = replace_once(commands, commands_import_anchor, commands_import_new, "COMMANDS_IMPORT")
    commands = replace_once(commands, '  io?.to(`user:${user.id}`).emit("ramzy:approval", revised);', '  io?.to(`user:${user.id}`).emit("ramzy:approval", publicRamzyApprovalView(revised));', "COMMANDS_REVISE_SOCKET")
    commands = replace_once(commands, '    io?.to(`user:${user.id}`).emit("ramzy:approval", executed);', '    io?.to(`user:${user.id}`).emit("ramzy:approval", publicRamzyApprovalView(executed));', "COMMANDS_DIRECT_SOCKET")

    routes_import_anchor = 'import { getRamzyVoiceCapabilities, synthesizeRamzySpeech, transcribeRamzyAudio } from "../agency-operator/services/ramzyVoice.service.js";\n'
    routes_import_new = routes_import_anchor + 'import {\n  getRamzyProductionHardeningConfig,\n  publicRamzyApprovalView,\n  publicRamzyApprovalViews,\n} from "../agency-operator/services/ramzyProductionHardening.service.js";\n'
    routes = replace_once(routes, routes_import_anchor, routes_import_new, "ROUTES_IMPORT")
    routes = replace_once(routes, '    greeting: "يومك سعيد يا بطل تميز",\n    settings: publicAgentSettings(settings),', '    greeting: "يومك سعيد يا بطل تميز",\n    productionHardening: getRamzyProductionHardeningConfig(),\n    settings: publicAgentSettings(settings),', "ROUTES_STATUS_HARDENING")
    routes = replace_once(routes, '  res.json({ conversation, messages, approvals });', '  res.json({ conversation, messages, approvals: publicRamzyApprovalViews(approvals) });', "ROUTES_CONVERSATION_APPROVALS")
    routes = replace_once(routes, '  res.json(approvals);', '  res.json(publicRamzyApprovalViews(approvals));', "ROUTES_APPROVAL_LIST")
    routes = replace_once(routes, '  res.json(revised);', '  res.json(publicRamzyApprovalView(revised));', "ROUTES_REVISE_RESPONSE")
    routes = replace_once(routes, '    req.app.get("io")?.to(`user:${req.user.id}`).emit("ramzy:approval", rejected);\n    return res.json(rejected);', '    const publicRejected = publicRamzyApprovalView(rejected);\n    req.app.get("io")?.to(`user:${req.user.id}`).emit("ramzy:approval", publicRejected);\n    return res.json(publicRejected);', "ROUTES_REJECT_BOUNDARY")
    routes = replace_once(routes, '    req.app.get("io")?.to(`user:${req.user.id}`).emit("ramzy:approval", finalized);\n    return res.json(finalized);', '    const publicFinalized = publicRamzyApprovalView(finalized);\n    req.app.get("io")?.to(`user:${req.user.id}`).emit("ramzy:approval", publicFinalized);\n    return res.json(publicFinalized);', "ROUTES_FINAL_BOUNDARY")

    # Final in-memory contract validation before writing anything.
    checks = {
        "PROMPT_MARKER": MARKER in prompt,
        "RUNTIME_PUBLIC": 'approvals: publicApprovals' in runtime,
        "RUNTIME_IMPORT": 'ramzyProductionHardening.service.js' in runtime,
        "COMMANDS_PUBLIC": 'publicRamzyApprovalView(revised)' in commands and 'publicRamzyApprovalView(executed)' in commands,
        "ROUTES_PUBLIC_LIST": 'publicRamzyApprovalViews(approvals)' in routes,
        "ROUTES_PUBLIC_FINAL": 'publicRamzyApprovalView(finalized)' in routes,
        "ROUTES_STATUS": 'productionHardening: getRamzyProductionHardeningConfig()' in routes,
        "SERVICE_MARKER": MARKER in SERVICE,
        "TEST_MARKER": 'Phase 16 production hardening config' in TEST,
    }
    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        fail("FINAL_VALIDATION:" + ",".join(failed))

    writes = {
        PROMPT_REL: prompt,
        RUNTIME_REL: runtime,
        COMMANDS_REL: commands,
        ROUTES_REL: routes,
        SERVICE_REL: SERVICE,
        TEST_REL: TEST,
    }
    for rel, content in writes.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    print("PHASE16_VOICE_ACTION_FINAL_E2E_PRODUCTION_HARDENING_PATCH=PASS")
    print(f"PHASE16_BASELINE={BASELINE}")
    print("PHASE16_PUBLIC_APPROVAL_BOUNDARY=PASS")
    print("PHASE16_FINAL_ACCEPTANCE_MATRIX=INSTALLED")
    print("PHASE16_REAL_ACTION_E2E=REQUIRES_EXPLICIT_SANDBOX_TARGET")


if __name__ == "__main__":
    main()
