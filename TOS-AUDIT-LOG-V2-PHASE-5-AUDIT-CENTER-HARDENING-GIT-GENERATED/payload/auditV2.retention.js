import { writeAuditEvent } from "./auditV2.service.js";

export const AUDIT_V2_RETENTION_MIN_DAYS = 30;
export const AUDIT_V2_RETENTION_MAX_DAYS = 3650;
export const AUDIT_V2_RETENTION_DEFAULT_DAYS = 365;

export function auditRetentionDays(value = process.env.AUDIT_V2_RETENTION_DAYS) {
  const parsed = Number.parseInt(String(value ?? ""), 10);
  if (!Number.isFinite(parsed)) return AUDIT_V2_RETENTION_DEFAULT_DAYS;
  return Math.min(AUDIT_V2_RETENTION_MAX_DAYS, Math.max(AUDIT_V2_RETENTION_MIN_DAYS, parsed));
}

export function auditRetentionPolicy({ days = auditRetentionDays(), now = new Date() } = {}) {
  const safeDays = auditRetentionDays(days);
  const reference = now instanceof Date ? now : new Date(now);
  const safeNow = Number.isNaN(reference.getTime()) ? new Date() : reference;
  const cutoff = new Date(safeNow.getTime() - safeDays * 24 * 60 * 60 * 1000);
  return { days: safeDays, cutoff, mode: "APPEND_ONLY_WITH_CONTROLLED_RETENTION" };
}

export async function getAuditRetentionStatus(db, options = {}) {
  const policy = auditRetentionPolicy(options);
  const [total, expired, oldest] = await Promise.all([
    db.auditEventV2.count(),
    db.auditEventV2.count({ where: { occurredAt: { lt: policy.cutoff } } }),
    db.auditEventV2.findFirst({ orderBy: { occurredAt: "asc" }, select: { occurredAt: true } }),
  ]);
  return { ...policy, total, expired, oldestOccurredAt: oldest?.occurredAt || null };
}

export async function purgeExpiredAuditEvents(
  db,
  { days = auditRetentionDays(), now = new Date(), actor = null, req = null, writer = writeAuditEvent } = {},
) {
  const policy = auditRetentionPolicy({ days, now });

  const deletion = await db.$transaction(async (tx) => {
    await tx.$queryRawUnsafe("SELECT set_config('app.audit_v2_retention_purge', 'on', true)");
    return tx.auditEventV2.deleteMany({ where: { occurredAt: { lt: policy.cutoff } } });
  });

  try {
    await writer({
      req,
      actor,
      action: "AUDIT.RETENTION_PURGE",
      category: "AUDIT_GOVERNANCE",
      entityType: "AuditEventV2",
      outcome: "SUCCESS",
      severity: "WARN",
      metadata: {
        retentionDays: policy.days,
        cutoff: policy.cutoff.toISOString(),
        deletedCount: deletion?.count || 0,
      },
    });
  } catch {
    // Governance audit is fail-open like all central audit writes.
  }

  return { ...policy, deletedCount: deletion?.count || 0 };
}
