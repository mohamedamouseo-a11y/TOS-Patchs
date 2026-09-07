import { writeAuditEvent } from "../services/auditV2.service.js";

const MUTATING_METHODS = new Set(["POST", "PUT", "PATCH"]);
const SENSITIVE_KEY_PATTERN = /password|passwd|passcode|token|secret|authorization|cookie|otp|api[_-]?key|credential|session|csrf|xsrf|private[_-]?key|signing[_-]?key|invite|reset/i;
const PHASE_4_PATH_PATTERN = /\/(?:chat|comments?|files?|attachments?|downloads?|exports?|restore|delete)(?:\/|$)/i;
const INTEGRATION_SENSITIVE_PATH_PATTERN = /\/(?:keys?|api-keys?|credentials?|secrets?|settings)(?:\/|$)/i;
const SAFE_BODY_KEYS = [
  "status", "stage", "priority", "projectId", "taskId", "clientId", "assigneeId", "assigneeIds",
  "userId", "department", "departmentId", "boardId", "listId", "workspaceId", "serviceId", "templateId",
  "ruleId", "provider", "integration", "source", "destination", "role", "approvalStatus", "dueDate",
  "startDate", "endDate", "name", "title", "lifecycle", "effect", "scopeType", "scopeId", "isActive",
];

function objectBody(value) {
  return value && typeof value === "object" && !Array.isArray(value) ? value : {};
}

function boundedScalar(value) {
  if (value == null) return null;
  if (typeof value === "boolean" || typeof value === "number") return value;
  if (typeof value === "string") return value.slice(0, 240);
  if (value instanceof Date) return value.toISOString();
  if (Array.isArray(value)) {
    return value
      .slice(0, 25)
      .map((item) => boundedScalar(item))
      .filter((item) => item == null || ["string", "number", "boolean"].includes(typeof item));
  }
  return undefined;
}

export function coreOperationPath(req = {}) {
  const raw = String(req.originalUrl || req.url || "/").split("?")[0] || "/";
  const apiIndex = raw.indexOf("/api/");
  if (apiIndex >= 0) return raw.slice(apiIndex);
  return raw.endsWith("/api") ? "/api" : raw;
}

export function sanitizeCoreOperationMetadata(req = {}, statusCode = null) {
  const body = objectBody(req.body);
  const changedFields = Object.keys(body)
    .filter((key) => !SENSITIVE_KEY_PATTERN.test(key))
    .slice(0, 30);

  const metadata = {
    method: String(req.method || "").toUpperCase(),
    path: coreOperationPath(req),
    statusCode: Number(statusCode) || null,
    changedFields,
  };

  for (const key of SAFE_BODY_KEYS) {
    if (!Object.prototype.hasOwnProperty.call(body, key) || SENSITIVE_KEY_PATTERN.test(key)) continue;
    const value = boundedScalar(body[key]);
    if (value !== undefined) metadata[key] = value;
  }
  return metadata;
}

function hasOwn(body, key) {
  return Object.prototype.hasOwnProperty.call(body, key);
}

function taskSubsystemOperation(method, path) {
  const definitions = [
    ["workflow-rules", "WORKFLOW_RULE"],
    ["saved-views", "SAVED_VIEW"],
    ["lists", "LIST"],
    ["boards", "BOARD"],
    ["services", "SERVICE"],
    ["templates", "TEMPLATE"],
    ["labels", "LABEL"],
    ["workspaces", "WORKSPACE"],
  ];
  for (const [segment, entity] of definitions) {
    if (!path.includes(`/${segment}`)) continue;
    const entityType = `Task${entity.replaceAll("_", "")}`;
    if (path.includes("/reorder")) return { action: `TASK.${entity}.REORDERED`, entityType };
    if (path.includes("/members")) return { action: `TASK.${entity}.MEMBERSHIP_CHANGED`, entityType };
    const createLike = method === "POST" && (
      path.endsWith(`/${segment}`)
      || (path.includes("/project/") && path.endsWith(`/${segment}`))
      || (path.includes("/workspaces/") && path.endsWith(`/${segment}`))
      || (path.includes("/boards/") && path.endsWith(`/${segment}`))
    );
    return {
      action: createLike ? `TASK.${entity}.CREATED` : `TASK.${entity}.UPDATED`,
      entityType,
    };
  }
  return null;
}

function integrationProvider(path, body) {
  if (path.includes("/trello")) return "trello";
  if (path.startsWith("/api/google-drive")) return "google-drive";
  if (path.startsWith("/api/github")) return "github";
  const match = path.match(/^\/api\/integrations\/([^/]+)/i);
  if (match?.[1]) return String(match[1]).toLowerCase();
  const supplied = body.provider || body.integration;
  return supplied ? String(supplied).toLowerCase().slice(0, 80) : "integration";
}

function inferredPathId(path, entityType) {
  const patterns = {
    Project: /\/api\/projects\/([^/]+)/i,
    Task: /\/api\/tasks\/([^/]+)/i,
    DesignQueueItem: /\/reports\/design-queue\/([^/]+)/i,
    DesignerCapacity: /\/reports\/design-queue\/designers\/([^/]+)/i,
    TaskBoard: /\/boards\/([^/]+)/i,
    TaskList: /\/lists\/([^/]+)/i,
    TaskWorkspace: /\/workspaces\/([^/]+)/i,
    TaskService: /\/services\/([^/]+)/i,
    TaskTemplate: /\/templates\/([^/]+)/i,
    TaskWorkflowRule: /\/workflow-rules\/([^/]+)/i,
    TaskSavedView: /\/saved-views\/([^/]+)/i,
    TaskLabel: /\/labels\/([^/]+)/i,
  };
  const value = patterns[entityType]?.exec(path)?.[1] || null;
  if (!value || ["reports", "project", "my-workspace", "requests", "designers"].includes(value.toLowerCase())) return null;
  return value.slice(0, 160);
}

function inferEntityId(path, body, entityType, provider = null) {
  if (entityType === "Integration") return provider;
  const preferredKeys = entityType === "Project"
    ? ["projectId", "id"]
    : (entityType === "Task" || entityType === "DesignQueueItem")
      ? ["taskId", "id", "projectId"]
      : ["id", "boardId", "listId", "workspaceId", "serviceId", "templateId", "ruleId", "userId", "projectId"];
  for (const key of preferredKeys) {
    const value = boundedScalar(body[key]);
    if (typeof value === "string" && value) return value.slice(0, 160);
  }
  return inferredPathId(path, entityType);
}

export function classifyCoreOperation(req = {}) {
  const method = String(req.method || "").toUpperCase();
  if (!MUTATING_METHODS.has(method)) return null;

  const path = coreOperationPath(req);
  const lowerPath = path.toLowerCase();
  const body = objectBody(req.body);

  if (PHASE_4_PATH_PATTERN.test(lowerPath)) return null;

  if (lowerPath.startsWith("/api/projects")) {
    let action = "PROJECT.UPDATED";
    if (method === "POST" && /^\/api\/projects\/?$/.test(lowerPath)) action = "PROJECT.CREATED";
    else if (lowerPath.includes("/archive")) action = "PROJECT.ARCHIVED";
    else if (lowerPath.includes("/members")) action = "PROJECT.MEMBERSHIP_CHANGED";
    else if (lowerPath.includes("/links")) action = "PROJECT.LINK_CHANGED";
    else if (lowerPath.includes("/notes")) action = "PROJECT.NOTE_ADDED";
    else if (hasOwn(body, "stage")) action = "PROJECT.STAGE_CHANGED";
    else if (hasOwn(body, "status")) action = "PROJECT.STATUS_CHANGED";
    else if (hasOwn(body, "priority")) action = "PROJECT.PRIORITY_CHANGED";
    return { action, entityType: "Project", entityId: inferEntityId(path, body, "Project") };
  }

  if (lowerPath.startsWith("/api/tasks/reports/design-queue")) {
    if (lowerPath.includes("/restore")) return null;
    let action = "DESIGN_QUEUE.UPDATED";
    let entityType = "DesignQueueItem";
    if (method === "POST" && /\/reports\/design-queue\/requests\/?$/.test(lowerPath)) action = "DESIGN_QUEUE.REQUEST_CREATED";
    else if (lowerPath.includes("/designers/") && lowerPath.endsWith("/capacity")) {
      action = "DESIGN_QUEUE.CAPACITY_CHANGED";
      entityType = "DesignerCapacity";
    } else if (lowerPath.endsWith("/self-assign") || lowerPath.endsWith("/assign")) action = "DESIGN_QUEUE.ASSIGNMENT_CHANGED";
    else if (lowerPath.endsWith("/reject")) action = "DESIGN_QUEUE.REQUEST_REJECTED";
    else if (lowerPath.endsWith("/archive")) action = "DESIGN_QUEUE.REQUEST_ARCHIVED";
    else if (lowerPath.endsWith("/request")) action = "DESIGN_QUEUE.REQUEST_UPDATED";
    return { action, entityType, entityId: inferEntityId(path, body, entityType) };
  }

  if (lowerPath.startsWith("/api/tasks")) {
    const subsystem = taskSubsystemOperation(method, lowerPath);
    if (subsystem) return { ...subsystem, entityId: inferEntityId(path, body, subsystem.entityType) };

    let action = "TASK.UPDATED";
    if (method === "POST" && (/^\/api\/tasks\/?$/.test(lowerPath) || lowerPath.endsWith("/my-workspace"))) action = "TASK.CREATED";
    else if (lowerPath.includes("/archive")) action = "TASK.ARCHIVED";
    else if (lowerPath.includes("/assignee") || hasOwn(body, "assigneeId") || hasOwn(body, "assigneeIds")) action = "TASK.ASSIGNEE_CHANGED";
    else if (lowerPath.endsWith("/time")) action = "TASK.TIME_TRACKING_CHANGED";
    else if (lowerPath.endsWith("/approval")) action = "TASK.APPROVAL_CHANGED";
    else if (lowerPath.includes("/dependencies")) action = "TASK.DEPENDENCY_CHANGED";
    else if (lowerPath.includes("/checklist")) action = "TASK.CHECKLIST_CHANGED";
    else if (lowerPath.includes("/labels")) action = "TASK.LABEL_CHANGED";
    else if (hasOwn(body, "status")) action = "TASK.STATUS_CHANGED";
    else if (hasOwn(body, "priority")) action = "TASK.PRIORITY_CHANGED";
    else if (hasOwn(body, "dueDate")) action = "TASK.DUE_DATE_CHANGED";
    else if (hasOwn(body, "listId") || hasOwn(body, "boardId") || lowerPath.includes("/move") || lowerPath.includes("/reorder")) action = "TASK.MOVED";
    return { action, entityType: "Task", entityId: inferEntityId(path, body, "Task") };
  }

  const integrationPath = lowerPath.startsWith("/api/integrations")
    || lowerPath.startsWith("/api/google-drive")
    || lowerPath.startsWith("/api/github");
  if (integrationPath) {
    if (INTEGRATION_SENSITIVE_PATH_PATTERN.test(lowerPath)) return null;
    const provider = integrationProvider(lowerPath, body);
    const trello = provider === "trello" || lowerPath.includes("trello");
    const syncLike = /\/(?:sync|pull|push|import|refresh|reconnect|test)(?:\/|$)/i.test(lowerPath);
    const action = trello
      ? (syncLike ? "TRELLO.SYNC_TRIGGERED" : "TRELLO.INTEGRATION_CHANGED")
      : (syncLike ? "INTEGRATION.SYNC_TRIGGERED" : "INTEGRATION.CHANGED");
    return { action, entityType: "Integration", entityId: provider };
  }

  return null;
}

export function createCoreOperationsAuditMiddleware({ writer = writeAuditEvent } = {}) {
  return function auditV2CoreOperations(req, res, next) {
    const classification = classifyCoreOperation(req);
    if (!classification) return next();

    res.once("finish", () => {
      const statusCode = Number(res.statusCode) || 0;
      if (statusCode < 200 || statusCode >= 400) return;

      const metadata = sanitizeCoreOperationMetadata(req, statusCode);
      const afterState = {};
      for (const key of SAFE_BODY_KEYS) {
        if (Object.prototype.hasOwnProperty.call(metadata, key)) afterState[key] = metadata[key];
      }

      Promise.resolve(writer({
        req,
        action: classification.action,
        category: "OPERATIONS",
        entityType: classification.entityType,
        entityId: classification.entityId,
        actor: req.user || null,
        outcome: "SUCCESS",
        severity: "INFO",
        metadata,
        beforeState: null,
        afterState: Object.keys(afterState).length ? afterState : null,
      })).catch(() => {});
    });

    return next();
  };
}

export const coreOperationsAuditMiddleware = createCoreOperationsAuditMiddleware();
