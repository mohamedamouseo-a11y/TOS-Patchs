import { redactAuditString, redactAuditValue } from "../utils/auditRedaction.js";

const ACTOR_TYPES = new Set(["USER", "SYSTEM", "ANONYMOUS", "INTEGRATION"]);
const OUTCOMES = new Set(["SUCCESS", "FAILURE", "ATTEMPT"]);
const SEVERITIES = new Set(["INFO", "WARN", "ERROR", "CRITICAL"]);

export function normalizeAuditText(value, maxLength = 512) {
  if (value === null || value === undefined) return null;
  const text = String(value).trim();
  return text ? text.slice(0, maxLength) : null;
}

function requiredAuditText(value, field, maxLength) {
  const text = normalizeAuditText(value, maxLength);
  if (!text) throw new TypeError(`Audit event ${field} is required`);
  return text;
}

function enumValue(value, allowed, fallback) {
  const normalized = normalizeAuditText(value, 32)?.toUpperCase();
  return normalized && allowed.has(normalized) ? normalized : fallback;
}

function validDate(value) {
  if (!value) return undefined;
  const date = value instanceof Date ? value : new Date(value);
  return Number.isNaN(date.getTime()) ? undefined : date;
}

export function buildAuditEventData(input = {}) {
  const req = input.req || null;
  const context = req?.auditContext || {};
  const actor = input.actor || req?.user || null;
  const inferredActorType = actor ? "USER" : req ? "ANONYMOUS" : "SYSTEM";

  const data = {
    action: requiredAuditText(input.action, "action", 160),
    category: normalizeAuditText(input.category, 80),
    entityType: normalizeAuditText(input.entityType, 120),
    entityId: normalizeAuditText(input.entityId, 256),
    actorId: normalizeAuditText(input.actorId ?? actor?.id, 256),
    actorType: enumValue(input.actorType, ACTOR_TYPES, inferredActorType),
    actorName: normalizeAuditText(input.actorName ?? actor?.name, 256),
    actorEmail: normalizeAuditText(input.actorEmail ?? actor?.email, 320),
    actorRole: normalizeAuditText(input.actorRole ?? actor?.role, 80),
    outcome: enumValue(input.outcome, OUTCOMES, "SUCCESS"),
    severity: enumValue(input.severity, SEVERITIES, "INFO"),
    source: normalizeAuditText(input.source, 80) || "TOS",
    requestId: normalizeAuditText(input.requestId ?? context.requestId, 128),
    ipAddress: normalizeAuditText(input.ipAddress ?? context.ipAddress, 128),
    userAgent: normalizeAuditText(input.userAgent ?? context.userAgent, 1024),
    httpMethod: normalizeAuditText(input.httpMethod ?? context.httpMethod, 16)?.toUpperCase() || null,
    route: normalizeAuditText(input.route ?? context.route, 1024),
    legacySource: normalizeAuditText(input.legacySource, 80),
    legacyId: normalizeAuditText(input.legacyId, 256),
    metadata: input.metadata === undefined ? null : redactAuditValue(input.metadata),
    beforeState: input.beforeState === undefined ? null : redactAuditValue(input.beforeState),
    afterState: input.afterState === undefined ? null : redactAuditValue(input.afterState),
    errorCode: normalizeAuditText(input.errorCode, 120),
    errorMessage: input.errorMessage === undefined || input.errorMessage === null
      ? null
      : redactAuditString(input.errorMessage, 4096),
  };

  const occurredAt = validDate(input.occurredAt);
  if (occurredAt) data.occurredAt = occurredAt;
  return data;
}
