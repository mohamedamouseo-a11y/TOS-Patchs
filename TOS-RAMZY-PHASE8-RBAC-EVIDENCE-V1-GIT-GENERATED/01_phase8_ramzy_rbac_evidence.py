#!/usr/bin/env python3
from pathlib import Path

ROOT = Path("/var/www/TOS")

def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")

def write(rel, text):
    (ROOT / rel).write_text(text, encoding="utf-8")

def replace_once(rel, old, new):
    text = read(rel)
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"PHASE8_PATCH_ERROR=ANCHOR_COUNT:{rel}:{count}")
    write(rel, text.replace(old, new, 1))

def create_new(rel, content):
    path = ROOT / rel
    if path.exists():
        raise SystemExit(f"PHASE8_PATCH_ERROR=NEW_FILE_EXISTS:{rel}")
    path.write_text(content, encoding="utf-8")

# 1) Central tool scope preflight.
replace_once(
    "backend/src/agency-operator/policies/agentPolicy.service.js",
    '''export async function assertTaskWithinAgentWorkspaceScope(user, taskId, allowedWorkspaceIds = null) {
  const settings = allowedWorkspaceIds === null ? await getAgentSettings() : null;
  const allowed = Array.isArray(allowedWorkspaceIds) ? allowedWorkspaceIds : (settings?.allowedWorkspaceIds || []);
  const { task, access } = await assertAgentTaskAccess(user, taskId, allowed, prisma);
  return { ...task, access };
}

export async function assertConversationOwner(user, conversationId) {''',
    '''export async function assertTaskWithinAgentWorkspaceScope(user, taskId, allowedWorkspaceIds = null) {
  const settings = allowedWorkspaceIds === null ? await getAgentSettings() : null;
  const allowed = Array.isArray(allowedWorkspaceIds) ? allowedWorkspaceIds : (settings?.allowedWorkspaceIds || []);
  const { task, access } = await assertAgentTaskAccess(user, taskId, allowed, prisma);
  return { ...task, access };
}

export async function assertRamzyToolInvocationScope(user, input = {}, allowedWorkspaceIds = null) {
  const projectId = String(input?.projectId || "").trim() || null;
  const workspaceId = String(input?.workspaceId || "").trim() || null;
  const settings = allowedWorkspaceIds === null ? await getAgentSettings() : null;
  const allowed = Array.isArray(allowedWorkspaceIds) ? allowedWorkspaceIds : (settings?.allowedWorkspaceIds || []);

  const workspace = workspaceId
    ? await assertAgentWorkspaceAccess(user, workspaceId, allowed)
    : null;
  const project = projectId
    ? await assertAgentProjectAccess(user, projectId, allowed)
    : null;

  if (workspace && project && workspace.projectId !== project.id) {
    throw new AppError("Workspace does not belong to the requested project", 403);
  }

  return {
    checked: Boolean(projectId || workspaceId),
    projectId: project?.id || null,
    workspaceId: workspace?.id || null,
  };
}

export async function assertConversationOwner(user, conversationId) {'''
)

# 2) Tool preflight.
replace_once(
    "backend/src/agency-operator/tools/createRamzyTools.js",
    '''import { getRamzyTosModuleContext, RAMZY_TOS_MODULE_KEYS } from "../services/ramzyTosKnowledge.service.js";

function safeErrorMessage(error) {''',
    '''import { getRamzyTosModuleContext, RAMZY_TOS_MODULE_KEYS } from "../services/ramzyTosKnowledge.service.js";
import { assertRamzyToolInvocationScope } from "../policies/agentPolicy.service.js";

function safeErrorMessage(error) {'''
)
replace_once(
    "backend/src/agency-operator/tools/createRamzyTools.js",
    '''  async function executeLogged(toolName, input, handler) {
    calls += 1;''',
    '''  async function executeLogged(toolName, input, handler) {
    await assertRamzyToolInvocationScope(user, input, settings.allowedWorkspaceIds);
    calls += 1;'''
)

# 3) System Intelligence RBAC.
replace_once(
    "backend/src/agency-operator/services/ramzySystemIntelligence.service.js",
    '''import { buildProjectVisibilityWhere } from "../../services/projectAccessScope.service.js";
import { getOperationalSnapshot, getTaskContext } from "./agentQueries.service.js";
import { buildAgentTaskVisibilityWhere, resolveAgentProjectAccess, resolveAgentWorkspaceAccess } from "../policies/agentAccess.service.js";''',
    '''import { buildProjectVisibilityWhere, hasSystemWideProjectAccess } from "../../services/projectAccessScope.service.js";
import { getOperationalSnapshot, getTaskContext } from "./agentQueries.service.js";
import { buildAgentTaskVisibilityWhere, resolveAgentWorkspaceAccess } from "../policies/agentAccess.service.js";
import { assertAgentProjectAccess, assertAgentWorkspaceAccess } from "../policies/agentPolicy.service.js";'''
)
replace_once(
    "backend/src/agency-operator/services/ramzySystemIntelligence.service.js",
    '''  if (explicitProjectId) {
    await resolveAgentProjectAccess(user, explicitProjectId, prisma);
    const project = await prisma.project.findUnique({ where: { id: explicitProjectId }, select: { id: true, name: true, code: true, status: true, stage: true, priority: true, progress: true, startDate: true, dueDate: true, deliveryDate: true, clientId: true, projectManagerId: true, teamLeadId: true, workspaces: { select: { id: true } } } });
    return project ? { entity: project, confidence: 1, aliasUsed: false, candidates: [project] } : { entity: null, confidence: 0, aliasUsed: false, candidates: [] };
  }''',
    '''  if (explicitProjectId) {
    await assertAgentProjectAccess(user, explicitProjectId, settings?.allowedWorkspaceIds || []);
    const project = await prisma.project.findUnique({ where: { id: explicitProjectId }, select: { id: true, name: true, code: true, status: true, stage: true, priority: true, progress: true, startDate: true, dueDate: true, deliveryDate: true, clientId: true, projectManagerId: true, teamLeadId: true, workspaces: { select: { id: true } } } });
    return project ? { entity: project, confidence: 1, aliasUsed: false, candidates: [project] } : { entity: null, confidence: 0, aliasUsed: false, candidates: [] };
  }'''
)

old_resolve_user = '''async function resolveUser(user, project, query, workspaceId = null, explicitUserId = null) {
  const where = { status: "ACTIVE" };
  const projectIds = project ? [project.id] : [];
  if (projectIds.length) where.OR = [{ projectMemberships: { some: { projectId: { in: projectIds } } } }, { id: project.projectManagerId || "__none__" }, { id: project.teamLeadId || "__none__" }];
  const users = await prisma.user.findMany({
    where,
    select: { id: true, name: true, email: true, department: true, jobTitle: true },
    take: 100,
  });
  const effectiveWorkspaceId = workspaceId || project?.workspaces?.[0]?.id || null;
  const aliases = await findMatchingEntityAliases({ user, workspaceId: effectiveWorkspaceId, entityType: "USER", query, limit: 20 });
  const enriched = users.map((candidate) => ({
    ...candidate,
    aliasMatch: aliases.some((alias) => alias.entityId === candidate.id),
  }));
  const resolution = resolveEntityCandidates({
    query,
    candidates: enriched,
    fields: ["name", "email"],
    explicitId: explicitUserId,
    exactFields: ["name", "email"],
    aliasField: "aliasMatch",
    entityType: "USER",
    limit: MAX_USER_CANDIDATES,
    ambiguityDelta: 0.05,
    ambiguityAutoResolveThreshold: 0.95,
  });
  return {
    ...resolution,
    aliasUsed: Boolean(resolution.entity?.aliasMatch),
  };
}'''

new_resolve_user = '''async function ramzyVisibleUserWhere(user, settings = {}, project = null, workspaceId = null) {
  const common = {
    status: "ACTIVE",
    role: { notIn: ["CLIENT", "FORMER_EMPLOYEE"] },
  };
  const allowedWorkspaceIds = Array.isArray(settings?.allowedWorkspaceIds) ? settings.allowedWorkspaceIds : [];

  if (project?.id) {
    await assertAgentProjectAccess(user, project.id, allowedWorkspaceIds);
    const leaderIds = [project.projectManagerId, project.teamLeadId].filter(Boolean);
    return {
      ...common,
      OR: [
        { id: user.id },
        { projectMemberships: { some: { projectId: project.id } } },
        ...(leaderIds.length ? [{ id: { in: leaderIds } }] : []),
      ],
    };
  }

  if (workspaceId) {
    const workspace = await assertAgentWorkspaceAccess(user, workspaceId, allowedWorkspaceIds);
    const projectRow = await prisma.project.findUnique({
      where: { id: workspace.projectId },
      select: { projectManagerId: true, teamLeadId: true },
    });
    const leaderIds = [projectRow?.projectManagerId, projectRow?.teamLeadId].filter(Boolean);
    return {
      ...common,
      OR: [
        { id: user.id },
        { workspaceMemberships: { some: { workspaceId } } },
        ...(leaderIds.length ? [{ id: { in: leaderIds } }] : []),
      ],
    };
  }

  if (hasSystemWideProjectAccess(user)) return common;

  const projects = await visibleProjects(user, settings);
  const projectIds = projects.map((item) => item.id).filter(Boolean);
  const leaderIds = [...new Set(projects.flatMap((item) => [item.projectManagerId, item.teamLeadId]).filter(Boolean))];
  if (!projectIds.length && !leaderIds.length) return { ...common, id: user.id };

  return {
    ...common,
    OR: [
      { id: user.id },
      ...(projectIds.length ? [{ projectMemberships: { some: { projectId: { in: projectIds } } } }] : []),
      ...(leaderIds.length ? [{ id: { in: leaderIds } }] : []),
    ],
  };
}

async function resolveUser(user, project, query, workspaceId = null, explicitUserId = null, settings = {}) {
  const where = await ramzyVisibleUserWhere(user, settings, project, workspaceId);
  const users = await prisma.user.findMany({
    where,
    select: { id: true, name: true, email: true, department: true, jobTitle: true },
    take: 100,
  });
  const effectiveWorkspaceId = workspaceId || project?.workspaces?.[0]?.id || null;
  const aliases = await findMatchingEntityAliases({ user, workspaceId: effectiveWorkspaceId, entityType: "USER", query, limit: 20 });
  const enriched = users.map((candidate) => ({
    ...candidate,
    aliasMatch: aliases.some((alias) => alias.entityId === candidate.id),
  }));
  const resolution = resolveEntityCandidates({
    query,
    candidates: enriched,
    fields: ["name", "email"],
    explicitId: explicitUserId,
    exactFields: ["name", "email"],
    aliasField: "aliasMatch",
    entityType: "USER",
    limit: MAX_USER_CANDIDATES,
    ambiguityDelta: 0.05,
    ambiguityAutoResolveThreshold: 0.95,
  });
  return {
    ...resolution,
    aliasUsed: Boolean(resolution.entity?.aliasMatch),
  };
}'''
replace_once("backend/src/agency-operator/services/ramzySystemIntelligence.service.js", old_resolve_user, new_resolve_user)

for old, new in [
    (
        '''      : await resolveUser(user, null, aliasInstruction.canonicalQuery, workspaceId);''',
        '''      : await resolveUser(user, null, aliasInstruction.canonicalQuery, workspaceId, null, settings);'''
    ),
    (
        '''    ? await resolveUser(user, project, selectedUserId ? "" : userQuery, workspaceId, selectedUserId || (looksLikeId(userQuery) ? userQuery : null))
    : null;''',
        '''    ? await resolveUser(user, project, selectedUserId ? "" : userQuery, workspaceId, selectedUserId || (looksLikeId(userQuery) ? userQuery : null), settings)
    : null;'''
    ),
    (
        '''    assigneeResolution = await resolveUser(user, project, "", workspaceId, contextResolution.activeUserId);''',
        '''    assigneeResolution = await resolveUser(user, project, "", workspaceId, contextResolution.activeUserId, settings);'''
    ),
    (
        '''    const lookup = await resolveUser(user, project, userQuery || extractUserQuery(requestText), workspaceId);''',
        '''    const lookup = await resolveUser(user, project, userQuery || extractUserQuery(requestText), workspaceId, null, settings);'''
    ),
]:
    replace_once("backend/src/agency-operator/services/ramzySystemIntelligence.service.js", old, new)

replace_once(
    "backend/src/agency-operator/services/ramzySystemIntelligence.service.js",
    '''export async function lookupRamzyUsers({ user, projectId = null, workspaceId = null, query = "", limit = MAX_USER_CANDIDATES }) {
  const project = projectId ? { id: projectId, projectManagerId: null, teamLeadId: null } : null;
  const result = await resolveUser(user, project, query, workspaceId, looksLikeId(query) ? query : null);
  return result.candidates.slice(0, Math.min(MAX_USER_CANDIDATES, Number(limit) || MAX_USER_CANDIDATES)).map((item) => ({ id: item.id, name: item.name, department: item.department, jobTitle: item.jobTitle, confidence: item.score, matchType: item.matchType || null }));
}''',
    '''export async function lookupRamzyUsers({ user, settings = {}, projectId = null, workspaceId = null, query = "", limit = MAX_USER_CANDIDATES }) {
  const project = projectId
    ? (await resolveProject(user, settings, "", workspaceId, projectId)).entity
    : null;
  const result = await resolveUser(user, project, query, workspaceId, looksLikeId(query) ? query : null, settings);
  return result.candidates.slice(0, Math.min(MAX_USER_CANDIDATES, Number(limit) || MAX_USER_CANDIDATES)).map((item) => ({ id: item.id, name: item.name, department: item.department, jobTitle: item.jobTitle, confidence: item.score, matchType: item.matchType || null }));
}'''
)

# 4) Evidence service.
create_new(
    "backend/src/agency-operator/services/ramzyEvidence.service.js",
    '''import { prisma } from "../../prisma.js";

export const RAMZY_EVIDENCE_VERSION = "RAMZY_EVIDENCE_V1";

const TOOL_SOURCE = Object.freeze({
  get_operational_snapshot: { key: "TOS_OPERATIONS", label: "TOS Operations", kind: "LIVE" },
  lookup_project: { key: "PROJECTS", label: "Projects", kind: "LIVE" },
  search_tasks: { key: "TASKS", label: "Tasks", kind: "LIVE" },
  lookup_user: { key: "TEAM", label: "Team directory", kind: "LIVE" },
  get_task_details: { key: "TASK_DETAILS", label: "Task details", kind: "LIVE" },
  get_team_performance: { key: "TEAM_PERFORMANCE", label: "Team Performance", kind: "LIVE" },
  get_tos_module_context: { key: "TOS_MODULE", label: "TOS module context", kind: "LIVE" },
  get_recent_central_chat_context: { key: "CENTRAL_CHAT", label: "Central Chat", kind: "LIVE" },
  get_chat_message_for_task_draft: { key: "CENTRAL_CHAT_MESSAGE", label: "Central Chat message", kind: "LIVE" },
});

function safeObject(value) {
  return value && typeof value === "object" && !Array.isArray(value) ? value : {};
}

function scopeLabel(input = {}) {
  const value = safeObject(input);
  if (value.workspaceId) return "WORKSPACE";
  if (value.projectId) return "PROJECT";
  if (value.employeeId) return "EMPLOYEE_AUTHORIZED";
  return "CURRENT_USER";
}

function moduleContextEvidence(output, base) {
  const value = safeObject(output);
  const knowledgeOnly = Boolean(value.knowledgeOnly);
  const title = String(value.title || value.module || base.label || "TOS module context").slice(0, 120);
  return {
    ...base,
    key: value.module ? `TOS_${String(value.module).slice(0, 60)}` : base.key,
    label: title,
    kind: knowledgeOnly ? "KNOWLEDGE" : "LIVE",
    live: !knowledgeOnly && value.live !== false,
    knowledgeOnly,
  };
}

function evidenceFromExecution(execution) {
  if (!execution || execution.status !== "SUCCEEDED") return null;
  const base = TOOL_SOURCE[execution.toolName];
  if (!base) return null;
  const classified = execution.toolName === "get_tos_module_context"
    ? moduleContextEvidence(execution.output, base)
    : { ...base, live: base.kind === "LIVE", knowledgeOnly: false };
  return {
    sourceKey: classified.key,
    label: classified.label,
    kind: classified.kind,
    live: Boolean(classified.live),
    knowledgeOnly: Boolean(classified.knowledgeOnly),
    scope: scopeLabel(execution.input),
    verified: true,
  };
}

function evidenceFromSystemIntelligence(intelligence = {}) {
  const metadata = safeObject(intelligence.metadata);
  if (!metadata.liveDataFetched && !metadata.deterministicResumeResponse && !metadata.clarificationRequired) return null;
  return {
    sourceKey: "SYSTEM_INTELLIGENCE",
    label: "TOS System Intelligence",
    kind: metadata.liveDataFetched ? "LIVE" : "KNOWLEDGE",
    live: Boolean(metadata.liveDataFetched),
    knowledgeOnly: !metadata.liveDataFetched,
    scope: "CURRENT_USER",
    verified: true,
  };
}

function dedupeSources(items = []) {
  const seen = new Set();
  return items.filter((item) => {
    if (!item) return false;
    const key = `${item.sourceKey}:${item.kind}:${item.scope}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

export async function buildRamzyRunEvidence({ runId, user, intelligence = {} } = {}) {
  if (!runId || !user?.id) {
    return {
      version: RAMZY_EVIDENCE_VERSION,
      authorization: { enforced: true, scope: "CURRENT_USER_AUTHORIZED", policy: "SERVER_SIDE_RBAC" },
      sources: [],
      summary: { verifiedSources: 0, liveSources: 0, knowledgeSources: 0 },
    };
  }

  const executions = await prisma.agentToolExecution.findMany({
    where: { runId, userId: user.id },
    orderBy: { createdAt: "asc" },
    select: {
      toolName: true,
      status: true,
      input: true,
      output: true,
    },
  });

  const sources = dedupeSources([
    evidenceFromSystemIntelligence(intelligence),
    ...executions.map(evidenceFromExecution),
  ]);
  const liveSources = sources.filter((item) => item.live).length;
  const knowledgeSources = sources.filter((item) => item.knowledgeOnly || item.kind === "KNOWLEDGE").length;

  return {
    version: RAMZY_EVIDENCE_VERSION,
    authorization: {
      enforced: true,
      scope: "CURRENT_USER_AUTHORIZED",
      policy: "SERVER_SIDE_RBAC",
      role: String(user.role || "UNKNOWN"),
      note: "Evidence only describes sources that passed the current user's server-side TOS access checks.",
    },
    sources,
    summary: {
      verifiedSources: sources.length,
      liveSources,
      knowledgeSources,
    },
  };
}
'''
)

# 5) Runtime evidence persistence.
replace_once(
    "backend/src/agency-operator/services/ramzyRuntime.service.js",
    '''import { buildRamzySystemIntelligence } from "./ramzySystemIntelligence.service.js";

function fallbackText(snapshot, message) {''',
    '''import { buildRamzySystemIntelligence } from "./ramzySystemIntelligence.service.js";
import { buildRamzyRunEvidence, RAMZY_EVIDENCE_VERSION } from "./ramzyEvidence.service.js";

function fallbackText(snapshot, message) {'''
)
replace_once(
    "backend/src/agency-operator/services/ramzyRuntime.service.js",
    '''function safeErrorMessage(error) {
  return String(error?.message || error || "Agent run failed")
    .replace(/(?:sk-|AIza|key[-_ ]?)[A-Za-z0-9_\\-]{12,}/gi, "[REDACTED]")
    .slice(0, 2000);
}

function isInternalIdKey(key) {''',
    '''function safeErrorMessage(error) {
  return String(error?.message || error || "Agent run failed")
    .replace(/(?:sk-|AIza|key[-_ ]?)[A-Za-z0-9_\\-]{12,}/gi, "[REDACTED]")
    .slice(0, 2000);
}

async function safeBuildEvidence({ runId, user, intelligence }) {
  try {
    return await buildRamzyRunEvidence({ runId, user, intelligence });
  } catch (error) {
    console.warn("[Ramzy] Evidence manifest unavailable", {
      errorName: String(error?.name || "Error"),
      errorMessage: safeErrorMessage(error),
    });
    return {
      version: RAMZY_EVIDENCE_VERSION,
      unavailable: true,
      authorization: { enforced: true, scope: "CURRENT_USER_AUTHORIZED", policy: "SERVER_SIDE_RBAC" },
      sources: [],
      summary: { verifiedSources: 0, liveSources: 0, knowledgeSources: 0 },
    };
  }
}

function isInternalIdKey(key) {'''
)
replace_once(
    "backend/src/agency-operator/services/ramzyRuntime.service.js",
    '''      const clarificationUsage = {
        providerUsed: "system_intelligence",
        modelUsed: null,
        fallback: false,
        clarification: true,
        memory: { ...memory.stats, persistentMemoryCreated: 0 },
        systemIntelligence: intelligence.metadata,
      };

      if (typeof onDelta === "function") onDelta(text);''',
    '''      const clarificationUsage = {
        providerUsed: "system_intelligence",
        modelUsed: null,
        fallback: false,
        clarification: true,
        memory: { ...memory.stats, persistentMemoryCreated: 0 },
        systemIntelligence: intelligence.metadata,
      };
      const evidence = await safeBuildEvidence({ runId: run.id, user, intelligence });
      clarificationUsage.evidence = evidence.summary;

      if (typeof onDelta === "function") onDelta(text);'''
)
replace_once(
    "backend/src/agency-operator/services/ramzyRuntime.service.js",
    '''            usage: clarificationUsage,
            systemIntelligence: intelligence.metadata,
          },''',
    '''            usage: clarificationUsage,
            systemIntelligence: intelligence.metadata,
            evidence,
          },'''
)
replace_once(
    "backend/src/agency-operator/services/ramzyRuntime.service.js",
    '''          output: { text, messageId: assistantMessage.id, clarificationRequired: true },''',
    '''          output: { text, messageId: assistantMessage.id, clarificationRequired: true, evidence },'''
)
replace_once(
    "backend/src/agency-operator/services/ramzyRuntime.service.js",
    '''      return { message: assistantMessage, approvals: [], runId: run.id, fallback: false, memory: memory.stats, systemIntelligence: intelligence.metadata };''',
    '''      return { message: assistantMessage, approvals: [], runId: run.id, fallback: false, memory: memory.stats, systemIntelligence: intelligence.metadata, evidence };'''
)
replace_once(
    "backend/src/agency-operator/services/ramzyRuntime.service.js",
    '''      const deterministicUsage = {
        providerUsed: "system_intelligence",
        modelUsed: null,
        fallback: false,
        deterministic: true,
        clarificationResume: Boolean(intelligence.metadata?.clarificationSelectionUsed),
        memory: { ...memory.stats, persistentMemoryCreated: 0 },
        systemIntelligence: intelligence.metadata,
      };

      if (typeof onDelta === "function") onDelta(text);''',
    '''      const deterministicUsage = {
        providerUsed: "system_intelligence",
        modelUsed: null,
        fallback: false,
        deterministic: true,
        clarificationResume: Boolean(intelligence.metadata?.clarificationSelectionUsed),
        memory: { ...memory.stats, persistentMemoryCreated: 0 },
        systemIntelligence: intelligence.metadata,
      };
      const evidence = await safeBuildEvidence({ runId: run.id, user, intelligence });
      deterministicUsage.evidence = evidence.summary;

      if (typeof onDelta === "function") onDelta(text);'''
)
replace_once(
    "backend/src/agency-operator/services/ramzyRuntime.service.js",
    '''            usage: deterministicUsage,
            systemIntelligence: intelligence.metadata,
          },''',
    '''            usage: deterministicUsage,
            systemIntelligence: intelligence.metadata,
            evidence,
          },'''
)
replace_once(
    "backend/src/agency-operator/services/ramzyRuntime.service.js",
    '''          output: { text, messageId: assistantMessage.id, deterministic: true },''',
    '''          output: { text, messageId: assistantMessage.id, deterministic: true, evidence },'''
)
replace_once(
    "backend/src/agency-operator/services/ramzyRuntime.service.js",
    '''        systemIntelligence: intelligence.metadata,
      };
    }

    const prompt = historyPrompt''',
    '''        systemIntelligence: intelligence.metadata,
        evidence,
      };
    }

    const prompt = historyPrompt'''
)
replace_once(
    "backend/src/agency-operator/services/ramzyRuntime.service.js",
    '''      systemIntelligence: intelligence.metadata,
    };

    if (typeof onDelta === "function") onDelta(text);

    const assistantMessage = await prisma.agentMessage.create({''',
    '''      systemIntelligence: intelligence.metadata,
    };
    const evidence = await safeBuildEvidence({ runId: run.id, user, intelligence });
    usage.evidence = evidence.summary;

    if (typeof onDelta === "function") onDelta(text);

    const assistantMessage = await prisma.agentMessage.create({'''
)
replace_once(
    "backend/src/agency-operator/services/ramzyRuntime.service.js",
    '''        metadata: { runId: run.id, fallback, providerUsed, modelUsed, usage, systemIntelligence: intelligence.metadata },''',
    '''        metadata: { runId: run.id, fallback, providerUsed, modelUsed, usage, systemIntelligence: intelligence.metadata, evidence },'''
)
replace_once(
    "backend/src/agency-operator/services/ramzyRuntime.service.js",
    '''        output: { text, messageId: assistantMessage.id },''',
    '''        output: { text, messageId: assistantMessage.id, evidence },'''
)
replace_once(
    "backend/src/agency-operator/services/ramzyRuntime.service.js",
    '''    return { message: assistantMessage, approvals, runId: run.id, fallback, memory: memory.stats, systemIntelligence: intelligence.metadata };''',
    '''    return { message: assistantMessage, approvals, runId: run.id, fallback, memory: memory.stats, systemIntelligence: intelligence.metadata, evidence };'''
)

# 6) Prompt contract.
replace_once(
    "backend/src/agency-operator/prompts/ramzyPrompt.js",
    '''- في Settings/Integrations/Backups لا تعرض أو تطلب أو تستنتج Password أو Secret أو Token أو API Key أو Credentials. بيانات Settings الحية المسموحة لرمزي هي Public/Runtime-safe فقط.
- أعطِ الأولوية للتأخير، SLA، العوائق، المهام غير المسندة، وضغط العمل.''',
    '''- في Settings/Integrations/Backups لا تعرض أو تطلب أو تستنتج Password أو Secret أو Token أو API Key أو Credentials. بيانات Settings الحية المسموحة لرمزي هي Public/Runtime-safe فقط.
- Phase 8: صلاحيات الأدوات تُحسم على السيرفر قبل تنفيذ القراءة. لا تعتبر وصولك لاسم أو ID في الذاكرة أو نص المستخدم أو نتيجة قديمة تصريحًا للوصول؛ لو الأداة رفضت النطاق فلا تحاول التحايل بأداة أخرى.
- الأدلة المعروضة للمستخدم تأتي من Evidence manifest المسجل بعد نجاح أدوات TOS المصرح بها. لا تدّع أن معلومة Verified/Live إلا إذا جاءت من مصدر حي ناجح في نفس التشغيل.
- المعرفة التي تحمل knowledgeOnly أو نوع KNOWLEDGE تشرح بنية النظام فقط ولا تثبت وجود سجل أو رقم أو حالة حالية.
- أعطِ الأولوية للتأخير، SLA، العوائق، المهام غير المسندة، وضغط العمل.'''
)

# 7) Frontend evidence + remove task DB id from approval card.
replace_once(
    "frontend/src/components/RamzyAssistant.jsx",
    '''      <small>الإجراء: {approval.actionType} • المهمة: {approval.targetId}</small>''',
    '''      <small>الإجراء: {approval.actionType}</small>'''
)
replace_once(
    "frontend/src/components/RamzyAssistant.jsx",
    '''function MessageBubble({ message, onFeedback, onRetry }) {
  const assistant = message.role === "ASSISTANT";''',
    '''function EvidenceDisclosure({ evidence, isEnglish }) {
  const sources = Array.isArray(evidence?.sources) ? evidence.sources : [];
  if (!evidence || evidence.unavailable || (!sources.length && !evidence?.authorization?.enforced)) return null;
  const liveCount = Number(evidence?.summary?.liveSources || 0);
  const knowledgeCount = Number(evidence?.summary?.knowledgeSources || 0);
  return (
    <details className="ramzy-evidence-disclosure">
      <summary>{isEnglish ? "Evidence & access" : "الأدلة ونطاق الصلاحية"}</summary>
      <div className="ramzy-evidence-body">
        <small>{isEnglish ? "Server-side access scope verified for this response." : "تم التحقق من نطاق الصلاحيات على السيرفر لهذا الرد."}</small>
        {sources.length > 0 && (
          <ul>
            {sources.map((source, index) => (
              <li key={`${source.sourceKey || source.label || "source"}-${index}`}>
                {source.label || source.sourceKey}
                {" — "}
                {source.live
                  ? (isEnglish ? "Live TOS data" : "بيانات حية من TOS")
                  : (isEnglish ? "System knowledge only" : "معرفة بالنظام فقط")}
              </li>
            ))}
          </ul>
        )}
        <small>
          {isEnglish
            ? `${liveCount} live source(s)${knowledgeCount ? ` • ${knowledgeCount} knowledge source(s)` : ""}`
            : `${liveCount} مصدر حي${knowledgeCount ? ` • ${knowledgeCount} مصدر معرفة` : ""}`}
        </small>
      </div>
    </details>
  );
}

function MessageBubble({ message, onFeedback, onRetry, isEnglish }) {
  const assistant = message.role === "ASSISTANT";'''
)
replace_once(
    "frontend/src/components/RamzyAssistant.jsx",
    '''      {assistant && (
        <div className="ramzy-message-actions">''',
    '''      {assistant && <EvidenceDisclosure evidence={message.metadata?.evidence} isEnglish={isEnglish} />}
      {assistant && (
        <div className="ramzy-message-actions">'''
)
replace_once(
    "frontend/src/components/RamzyAssistant.jsx",
    '''                <MessageBubble message={message} onFeedback={feedback} onRetry={message.role === "ASSISTANT" && !message.streaming && !String(message.id).startsWith("streaming-") ? () => retryAssistantMessage(message.id) : null} />''',
    '''                <MessageBubble message={message} isEnglish={isEnglish} onFeedback={feedback} onRetry={message.role === "ASSISTANT" && !message.streaming && !String(message.id).startsWith("streaming-") ? () => retryAssistantMessage(message.id) : null} />'''
)

# 8) Tests.
create_new(
    "backend/src/agency-operator/tests/ramzyRbacEvidence.static.test.js",
    '''import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "../..");
const read = (relative) => readFile(path.join(root, relative), "utf8");

test("Phase 8 preflights provider supplied project/workspace scope before tool execution", async () => {
  const policy = await read("agency-operator/policies/agentPolicy.service.js");
  const tools = await read("agency-operator/tools/createRamzyTools.js");
  assert.match(policy, /assertRamzyToolInvocationScope/);
  assert.match(policy, /assertAgentWorkspaceAccess/);
  assert.match(policy, /assertAgentProjectAccess/);
  const preflight = tools.indexOf("await assertRamzyToolInvocationScope");
  const executionCreate = tools.indexOf("prisma.agentToolExecution.create");
  assert.ok(preflight >= 0 && executionCreate > preflight, "RBAC preflight must run before tool execution is recorded/handled");
});

test("Phase 8 prevents global person lookup and explicit project scope bypass", async () => {
  const intelligence = await read("agency-operator/services/ramzySystemIntelligence.service.js");
  assert.match(intelligence, /ramzyVisibleUserWhere/);
  assert.match(intelligence, /hasSystemWideProjectAccess/);
  assert.match(intelligence, /workspaceMemberships/);
  assert.match(intelligence, /projectMemberships/);
  assert.match(intelligence, /assertAgentProjectAccess\\(user, explicitProjectId, settings\\?\\.allowedWorkspaceIds/);
  assert.match(intelligence, /lookupRamzyUsers\\(\\{ user, settings = \\{\\}/);
  assert.doesNotMatch(intelligence, /const where = \\{ status: "ACTIVE" \\};/);
});

test("Phase 8 evidence stores provenance without user-visible database identifiers", async () => {
  const evidence = await read("agency-operator/services/ramzyEvidence.service.js");
  const runtime = await read("agency-operator/services/ramzyRuntime.service.js");
  const assistant = await read("../../frontend/src/components/RamzyAssistant.jsx");
  assert.match(evidence, /RAMZY_EVIDENCE_V1/);
  assert.match(evidence, /SERVER_SIDE_RBAC/);
  assert.match(evidence, /evidenceFromExecution/);
  assert.doesNotMatch(evidence, /targetId:/);
  assert.doesNotMatch(evidence, /projectId:/);
  assert.doesNotMatch(evidence, /workspaceId:/);
  assert.match(runtime, /safeBuildEvidence/);
  assert.match(runtime, /systemIntelligence: intelligence\\.metadata, evidence/);
  assert.match(assistant, /message\\.metadata\\?\\.evidence/);
  assert.match(assistant, /الأدلة ونطاق الصلاحية/);
  assert.doesNotMatch(assistant, /المهمة: \\{approval\\.targetId\\}/);
});
'''
)

print("PHASE8_RAMZY_RBAC_EVIDENCE_PATCH=PASS")
