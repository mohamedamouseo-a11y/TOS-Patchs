import { writeAuditEvent } from "../services/auditV2.service.js";

const MUTATING_METHODS = new Set(["POST", "PUT", "PATCH", "DELETE"]);
const SENSITIVE_KEY_PATTERN = /password|passwd|passcode|token|secret|authorization|cookie|otp|api[_-]?key|credential|session|csrf|xsrf|private[_-]?key|signing[_-]?key|invite|reset|confirmation/i;
const CONTENT_KEY_PATTERN = /^(?:body|message|description|notes?|content|text|html|subject|comment|copy)$/i;
const SAFE_BODY_KEYS = [
  "status", "enabled", "type", "role", "scopeType", "scopeId", "provider",
  "projectId", "taskId", "userId", "assigneeId", "conversationId", "channelId",
  "messageId", "fileId", "templateId", "incidentId", "backupId", "targetType", "targetId",
];

function objectBody(value) {
  return value && typeof value === "object" && !Array.isArray(value) ? value : {};
}

function boundedScalar(value) {
  if (value == null) return null;
  if (typeof value === "boolean" || typeof value === "number") return value;
  if (typeof value === "string") return value.slice(0, 160);
  if (value instanceof Date) return value.toISOString();
  if (Array.isArray(value)) {
    return value.slice(0, 20)
      .map((item) => boundedScalar(item))
      .filter((item) => item == null || ["string", "number", "boolean"].includes(typeof item));
  }
  return undefined;
}

export function sensitiveOperationPath(req = {}) {
  const raw = String(req.originalUrl || req.url || "/").split("?")[0] || "/";
  const apiIndex = raw.indexOf("/api/");
  if (apiIndex >= 0) return raw.slice(apiIndex);
  return raw.endsWith("/api") ? "/api" : raw;
}

export function sanitizeSensitiveOperationMetadata(req = {}, statusCode = null) {
  const body = objectBody(req.body);
  const changedFields = Object.keys(body)
    .filter((key) => !SENSITIVE_KEY_PATTERN.test(key) && !CONTENT_KEY_PATTERN.test(key))
    .slice(0, 24);

  const metadata = {
    method: String(req.method || "").toUpperCase(),
    path: sensitiveOperationPath(req),
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

function pathHas(path, segment) {
  return new RegExp(`/(?:${segment})(?:/|$)`, "i").test(path);
}

function pathId(path, segment) {
  const match = path.match(new RegExp(`/${segment}/([^/?]+)`, "i"));
  return match?.[1] ? String(match[1]).slice(0, 160) : null;
}

function classified(action, entityType, entityId = null, severity = "INFO") {
  return { action, entityType, entityId, severity };
}

function classifyDatabaseBackup(method, path) {
  if (!path.startsWith("/api/database-backups")) return null;
  if (method === "PATCH" && path.endsWith("/settings")) {
    return classified("BACKUP.DATABASE_SETTINGS_CHANGED", "DatabaseBackupSettings", null, "WARN");
  }
  if (method === "DELETE" && path.endsWith("/google-drive/disconnect")) {
    return classified("BACKUP.DATABASE_STORAGE_DISCONNECTED", "DatabaseBackupStorage", "google-drive", "WARN");
  }
  if (method === "POST" && path.endsWith("/backup-now")) {
    return classified("BACKUP.DATABASE_CREATED", "DatabaseBackup", null, "WARN");
  }
  if (method === "POST" && /\/restore\/[^/]+\/prepare$/i.test(path)) {
    return classified("BACKUP.DATABASE_RESTORE_PREPARED", "DatabaseBackup", pathId(path, "restore"), "WARN");
  }
  if (method === "POST" && /\/restore\/[^/]+\/confirm$/i.test(path)) {
    return classified("BACKUP.DATABASE_RESTORE_CONFIRMED", "DatabaseBackup", pathId(path, "restore"), "CRITICAL");
  }
  if (method === "GET" && path.endsWith("/google-drive/callback")) {
    return classified("BACKUP.DATABASE_STORAGE_CALLBACK_COMPLETED", "DatabaseBackupStorage", "google-drive", "WARN");
  }
  return null;
}

function classifySystemBackup(method, path) {
  if (!path.startsWith("/api/system-backups")) return null;
  if (method === "PATCH" && path.endsWith("/settings")) {
    return classified("BACKUP.SYSTEM_SETTINGS_CHANGED", "SystemBackupSettings", null, "WARN");
  }
  if (method === "POST" && path.endsWith("/run-now")) {
    return classified("BACKUP.SYSTEM_RUN_TRIGGERED", "SystemBackup", null, "WARN");
  }
  return null;
}

function classifyFile(method, path) {
  if (!path.startsWith("/api/files")) return null;
  const fileId = pathId(path, "files");
  if (method === "POST" && path.endsWith("/upload")) return classified("FILE.UPLOADED", "File", null);
  if (method === "PATCH" && /^\/api\/files\/[^/]+$/i.test(path)) return classified("FILE.METADATA_UPDATED", "File", fileId);
  if (method === "DELETE" && /^\/api\/files\/[^/]+$/i.test(path)) return classified("FILE.DELETED", "File", fileId, "WARN");
  if (method === "GET" && path.endsWith("/download")) return classified("FILE.DOWNLOADED", "File", fileId, "WARN");
  if (method === "GET" && path.endsWith("/preview")) return classified("FILE.PREVIEWED", "File", fileId);
  if (method === "POST" && path.endsWith("/retry-drive-delete")) return classified("FILE.DELETE_RETRIED", "File", fileId, "WARN");
  return null;
}

function chatEntityId(path) {
  return pathId(path, "messages")
    || pathId(path, "conversations")
    || pathId(path, "channels")
    || pathId(path, "drafts")
    || pathId(path, "files");
}

function classifyChat(method, path) {
  const isChat = path.startsWith("/api/chat") || path.startsWith("/api/central-chat/native");
  if (!isChat) return null;

  if (pathHas(path, "download") && method === "GET") {
    return classified("CHAT.FILE_DOWNLOADED", "ChatFile", pathId(path, "files"), "WARN");
  }

  if (method === "DELETE" && /\/messages\/[^/]+$/i.test(path)) {
    return classified("CHAT.MESSAGE_DELETED", "ChatMessage", pathId(path, "messages"), "WARN");
  }
  if (method === "DELETE" && /\/drafts\/[^/]+$/i.test(path)) {
    return classified("CHAT.DRAFT_DELETED", "ChatDraft", pathId(path, "drafts"));
  }
  if (method === "POST" && path.endsWith("/messages")) {
    return classified("CHAT.MESSAGE_SENT", "ChatMessage");
  }
  if (method === "PATCH" && /\/messages\/[^/]+$/i.test(path)) {
    return classified("CHAT.MESSAGE_EDITED", "ChatMessage", pathId(path, "messages"));
  }
  if (method === "PATCH" && path.endsWith("/pin")) {
    return classified("CHAT.MESSAGE_PIN_CHANGED", "ChatMessage", pathId(path, "messages"));
  }
  if (method === "PATCH" && path.endsWith("/decision")) {
    return classified("CHAT.MESSAGE_DECISION_CHANGED", "ChatMessage", pathId(path, "messages"));
  }
  if (method === "POST" && path.endsWith("/to-task")) {
    return classified("CHAT.MESSAGE_CONVERTED_TO_TASK", "ChatMessage", pathId(path, "messages"));
  }
  if (method === "POST" && path.endsWith("/reactions")) {
    return classified("CHAT.REACTION_CHANGED", "ChatMessage", pathId(path, "messages"));
  }
  if (method === "POST" && path.endsWith("/bookmark")) {
    return classified("CHAT.BOOKMARK_CHANGED", "ChatMessage", pathId(path, "messages"));
  }
  if (method === "POST" && /\/conversations\/(?:direct|group)$/i.test(path)) {
    return classified("CHAT.CONVERSATION_CREATED", "Conversation");
  }
  if (method === "POST" && /\/projects\/[^/]+\/channels$/i.test(path)) {
    return classified("CHAT.CHANNEL_CREATED", "Channel");
  }
  if (method === "PATCH" && /\/channels\/[^/]+$/i.test(path)) {
    return classified("CHAT.CHANNEL_UPDATED", "Channel", pathId(path, "channels"));
  }
  if (MUTATING_METHODS.has(method) && pathHas(path, "drafts")) {
    return classified("CHAT.DRAFT_CHANGED", "ChatDraft", chatEntityId(path));
  }

  return null;
}

function genericDelete(method, path) {
  if (method !== "DELETE") return null;
  if (path.startsWith("/api/users") || path.startsWith("/api/permissions") || path.startsWith("/api/auth")) {
    return null;
  }
  if (path.startsWith("/api/tasks")) return classified("TASK.DELETED", "Task", pathId(path, "tasks"), "WARN");
  if (path.startsWith("/api/projects")) return classified("PROJECT.DELETED", "Project", pathId(path, "projects"), "WARN");
  if (path.startsWith("/api/tws")) return classified("WORKSPACE.RESOURCE_DELETED", "WorkspaceResource", null, "WARN");
  if (path.includes("/admin/")) return classified("ADMIN.RESOURCE_DELETED", "AdminResource", null, "WARN");
  return classified("RESOURCE.DELETED", "Resource", null, "WARN");
}

function classifyRestore(method, path) {
  if (!MUTATING_METHODS.has(method) || !pathHas(path, "restore")) return null;
  if (path.startsWith("/api/tasks/reports/design-queue")) {
    return classified("DESIGN_QUEUE.REQUEST_RESTORED", "DesignQueueItem", pathId(path, "design-queue"), "WARN");
  }
  if (path.startsWith("/api/tasks")) return classified("TASK.RESTORED", "Task", pathId(path, "tasks"), "WARN");
  if (path.startsWith("/api/projects")) return classified("PROJECT.RESTORED", "Project", pathId(path, "projects"), "WARN");
  return classified("RESOURCE.RESTORED", "Resource", null, "WARN");
}

function classifyExportDownload(method, path) {
  if (!["GET", "POST"].includes(method)) return null;
  if (pathHas(path, "export")) return classified("DATA.EXPORTED", "Export", null, "WARN");
  if (pathHas(path, "download")) return classified("DATA.DOWNLOADED", "Download", null, "WARN");
  return null;
}

function classifySettingsAdmin(method, path) {
  if (path.startsWith("/api/email-settings")) {
    if (method === "PATCH") return classified("SETTINGS.EMAIL_CHANGED", "EmailSettings", null, "WARN");
    if (method === "POST" && path.endsWith("/test")) return classified("SETTINGS.EMAIL_TEST_TRIGGERED", "EmailSettings", null, "WARN");
    return null;
  }

  if (!MUTATING_METHODS.has(method)) return null;
  if (path.includes("/settings")) return classified("SETTINGS.CHANGED", "Settings", null, "WARN");
  if (path.includes("/admin/") || path.endsWith("/admin")) {
    return classified("ADMIN.OPERATION_EXECUTED", "AdminOperation", null, "WARN");
  }
  return null;
}

export function classifySensitiveOperation(req = {}) {
  const method = String(req.method || "").toUpperCase();
  const path = sensitiveOperationPath(req);
  const lowerPath = path.toLowerCase();

  return classifyDatabaseBackup(method, lowerPath)
    || classifySystemBackup(method, lowerPath)
    || classifyFile(method, lowerPath)
    || classifyChat(method, lowerPath)
    || classifyRestore(method, lowerPath)
    || genericDelete(method, lowerPath)
    || classifyExportDownload(method, lowerPath)
    || classifySettingsAdmin(method, lowerPath)
    || null;
}

export function createSensitiveOperationsAuditMiddleware({ writer = writeAuditEvent } = {}) {
  return function auditV2SensitiveOperations(req, res, next) {
    const classification = classifySensitiveOperation(req);
    if (!classification) return next();

    res.once("finish", () => {
      const statusCode = Number(res.statusCode) || 0;
      if (statusCode < 200 || statusCode >= 400) return;

      const metadata = sanitizeSensitiveOperationMetadata(req, statusCode);
      Promise.resolve(writer({
        req,
        action: classification.action,
        category: "SENSITIVE_OPERATIONS",
        entityType: classification.entityType,
        entityId: classification.entityId,
        actor: req.user || req.centralUser || null,
        outcome: "SUCCESS",
        severity: classification.severity || "INFO",
        metadata,
        beforeState: null,
        afterState: null,
      })).catch(() => {});
    });

    return next();
  };
}

export const sensitiveOperationsAuditMiddleware = createSensitiveOperationsAuditMiddleware();
