import { Router } from "express";
import { prisma } from "../prisma.js";
import { auth } from "../middleware/auth.js";
import { asyncHandler, AppError } from "../middleware/errors.js";
import { optionalString } from "../middleware/validate.js";
import {
  auditV2Filters,
  exportAuditV2Csv,
  getAuditV2Event,
  listAuditV2,
} from "../services/auditV2.center.js";
import {
  getAuditRetentionStatus,
  purgeExpiredAuditEvents,
} from "../services/auditV2.retention.js";

const router = Router();
router.use(auth);

function assertAuditAccess(user) {
  if (!["SUPER_ADMIN", "ADMIN", "MANAGER"].includes(user?.role)) {
    throw new AppError("Audit Log access is restricted", 403);
  }
}

function assertRetentionAdmin(user) {
  if (user?.role !== "SUPER_ADMIN") {
    throw new AppError("Audit retention requires SUPER_ADMIN", 403);
  }
}

function safeDate(value) {
  if (!value) return null;
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? null : date;
}

function clampLimit(value) {
  const next = Number(value);
  if (!Number.isFinite(next)) return 100;
  return Math.max(20, Math.min(200, Math.floor(next)));
}

function normalizeMetadata(metadata) {
  if (!metadata || typeof metadata !== "object") return metadata || null;
  return metadata;
}

const AUDIT_USER_SELECT = { id: true, name: true, role: true };

function sanitizeAuditUser(user) {
  if (!user) return null;
  return { id: user.id, name: user.name, role: user.role };
}

function auditItem({ id, source, action, title, message = null, actor = null, target = null, projectId = null, taskId = null, channelId = null, conversationId = null, messageId = null, fileId = null, metadata = null, createdAt }) {
  return {
    id: `${source}:${id}`,
    rawId: id,
    source,
    action,
    title,
    message,
    actor: sanitizeAuditUser(actor),
    target: sanitizeAuditUser(target),
    projectId,
    taskId,
    channelId,
    conversationId,
    messageId,
    fileId,
    metadata: normalizeMetadata(metadata),
    createdAt,
  };
}

// Audit Log V2 center. Legacy GET / remains unchanged below for compatibility.
router.get("/v2", asyncHandler(async (req, res) => {
  assertAuditAccess(req.user);
  res.json(await listAuditV2(prisma, req.query || {}));
}));

router.get("/v2/filters", asyncHandler(async (req, res) => {
  assertAuditAccess(req.user);
  res.json(await auditV2Filters(prisma));
}));

router.get("/v2/export", asyncHandler(async (req, res) => {
  assertAuditAccess(req.user);
  const result = await exportAuditV2Csv(prisma, req.query || {});
  const stamp = new Date().toISOString().slice(0, 10);
  res.setHeader("Content-Type", "text/csv; charset=utf-8");
  res.setHeader("Content-Disposition", `attachment; filename="tos-audit-v2-${stamp}.csv"`);
  res.setHeader("X-Audit-Export-Count", String(result.count));
  res.send(`\uFEFF${result.csv}`);
}));

router.get("/v2/retention", asyncHandler(async (req, res) => {
  assertAuditAccess(req.user);
  res.json(await getAuditRetentionStatus(prisma));
}));

router.post("/v2/retention/run", asyncHandler(async (req, res) => {
  assertAuditAccess(req.user);
  assertRetentionAdmin(req.user);
  res.json(await purgeExpiredAuditEvents(prisma, {
    days: req.body?.days,
    actor: req.user,
    req,
  }));
}));

router.get("/v2/:id", asyncHandler(async (req, res) => {
  assertAuditAccess(req.user);
  const event = await getAuditV2Event(prisma, req.params.id);
  if (!event) throw new AppError("Audit event not found", 404);
  res.json(event);
}));

router.get("/", asyncHandler(async (req, res) => {
  assertAuditAccess(req.user);

  const limit = clampLimit(req.query.limit);
  const source = optionalString(req.query.source);
  const projectId = optionalString(req.query.projectId);
  const action = optionalString(req.query.action);
  const includeNoise = String(req.query.includeNoise || "").toLowerCase() === "true";
  const from = safeDate(req.query.from);
  const to = safeDate(req.query.to);
  const createdAt = from || to ? { ...(from ? { gte: from } : {}), ...(to ? { lte: to } : {}) } : undefined;

  const sources = source ? [source] : ["chat", "permissions", "projects", "tasks"];
  const jobs = [];

  if (sources.includes("chat")) {
    const chatNoiseFilter = includeNoise || action ? {} : { action: { notIn: ["MESSAGE_DELIVERED"] } };
    jobs.push(prisma.chatAuditLog.findMany({
      where: { ...(projectId ? { projectId } : {}), ...(action ? { action } : chatNoiseFilter), ...(createdAt ? { createdAt } : {}) },
      include: { actor: { select: AUDIT_USER_SELECT } },
      orderBy: { createdAt: "desc" },
      take: limit,
    }).then((rows) => rows.map((row) => auditItem({
      id: row.id,
      source: "chat",
      action: row.action,
      title: `Chat: ${row.action}`,
      actor: row.actor,
      projectId: row.projectId,
      channelId: row.channelId,
      conversationId: row.conversationId,
      messageId: row.messageId,
      fileId: row.fileId,
      metadata: row.metadata,
      createdAt: row.createdAt,
    }))));
  }

  if (sources.includes("permissions")) {
    jobs.push(prisma.permissionAuditLog.findMany({
      where: { ...(createdAt ? { createdAt } : {}) },
      include: { actor: { select: AUDIT_USER_SELECT }, targetUser: { select: AUDIT_USER_SELECT } },
      orderBy: { createdAt: "desc" },
      take: limit,
    }).then((rows) => rows.map((row) => auditItem({
      id: row.id,
      source: "permissions",
      action: row.action,
      title: `Permissions: ${row.action}`,
      actor: row.actor,
      target: row.targetUser,
      metadata: { permissionKey: row.permissionKey, role: row.role, ...(row.metadata || {}) },
      createdAt: row.createdAt,
    }))));
  }

  if (sources.includes("projects")) {
    jobs.push(prisma.projectActivity.findMany({
      where: { ...(projectId ? { projectId } : {}), ...(createdAt ? { createdAt } : {}) },
      include: { user: { select: AUDIT_USER_SELECT } },
      orderBy: { createdAt: "desc" },
      take: limit,
    }).then((rows) => rows.map((row) => auditItem({
      id: row.id,
      source: "projects",
      action: row.type,
      title: row.title,
      message: row.message,
      actor: row.user,
      projectId: row.projectId,
      metadata: row.metadata,
      createdAt: row.createdAt,
    }))));
  }

  if (sources.includes("tasks")) {
    jobs.push(prisma.taskActivity.findMany({
      where: { ...(createdAt ? { createdAt } : {}), ...(projectId ? { task: { projectId } } : {}) },
      include: { user: { select: AUDIT_USER_SELECT }, task: { select: { projectId: true } } },
      orderBy: { createdAt: "desc" },
      take: limit,
    }).then((rows) => rows.map((row) => auditItem({
      id: row.id,
      source: "tasks",
      action: row.type,
      title: row.message,
      actor: row.user,
      projectId: row.task?.projectId || null,
      taskId: row.taskId,
      metadata: row.metadata,
      createdAt: row.createdAt,
    }))));
  }

  const entries = (await Promise.all(jobs)).flat()
    .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
    .slice(0, limit);

  res.json({ entries, count: entries.length });
}));

export default router;
