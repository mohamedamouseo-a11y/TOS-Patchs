import { prisma } from "../prisma.js";
import { buildAuditEventData, normalizeAuditText } from "./auditV2.core.js";
import { redactAuditString } from "../utils/auditRedaction.js";

export async function writeAuditEvent(input, options = {}) {
  const db = options.db || prisma;
  const logger = options.logger || console;

  try {
    const data = buildAuditEventData(input);
    return await db.auditEventV2.create({ data });
  } catch (error) {
    const requestId = normalizeAuditText(
      input?.requestId ?? input?.req?.auditContext?.requestId,
      128,
    );
    try {
      logger?.error?.("[audit-v2] write failed; business operation continues", {
        action: normalizeAuditText(input?.action, 160),
        requestId,
        error: redactAuditString(error instanceof Error ? error.message : String(error), 1024),
      });
    } catch {
      // Audit telemetry must never break the business request, even if logging fails.
    }
    return null;
  }
}
