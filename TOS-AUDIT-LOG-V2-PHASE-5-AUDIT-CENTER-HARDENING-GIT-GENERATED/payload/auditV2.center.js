export function clampAuditInt(value, fallback, { min = 1, max = 200 } = {}) {
  const parsed = Number.parseInt(String(value ?? ""), 10);
  if (!Number.isFinite(parsed)) return fallback;
  return Math.min(max, Math.max(min, parsed));
}

export function safeAuditDate(value) {
  if (!value) return null;
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? null : date;
}

function clean(value, max = 256) {
  if (value === undefined || value === null) return "";
  return String(value).trim().slice(0, max);
}

export function parseAuditV2Query(query = {}) {
  return {
    page: clampAuditInt(query.page, 1, { min: 1, max: 100000 }),
    limit: clampAuditInt(query.limit, 50, { min: 20, max: 200 }),
    q: clean(query.q, 240),
    action: clean(query.action, 160),
    category: clean(query.category, 80),
    entityType: clean(query.entityType, 120),
    entityId: clean(query.entityId, 256),
    actorId: clean(query.actorId, 256),
    actorRole: clean(query.actorRole, 80),
    outcome: clean(query.outcome, 32).toUpperCase(),
    severity: clean(query.severity, 32).toUpperCase(),
    source: clean(query.source, 80),
    requestId: clean(query.requestId, 128),
    projectId: clean(query.projectId, 256),
    from: safeAuditDate(query.from),
    to: safeAuditDate(query.to),
  };
}

export function buildAuditV2Where(query = {}) {
  const filters = parseAuditV2Query(query);
  const AND = [];

  for (const key of ["action", "category", "entityType", "entityId", "actorId", "actorRole", "outcome", "severity", "source", "requestId"]) {
    if (filters[key]) AND.push({ [key]: filters[key] });
  }

  if (filters.from || filters.to) {
    AND.push({
      occurredAt: {
        ...(filters.from ? { gte: filters.from } : {}),
        ...(filters.to ? { lte: filters.to } : {}),
      },
    });
  }

  if (filters.projectId) {
    AND.push({
      OR: [
        { entityType: "Project", entityId: filters.projectId },
        { metadata: { path: ["projectId"], equals: filters.projectId } },
      ],
    });
  }

  if (filters.q) {
    const contains = { contains: filters.q, mode: "insensitive" };
    AND.push({
      OR: [
        { action: contains },
        { category: contains },
        { entityType: contains },
        { entityId: contains },
        { actorName: contains },
        { actorEmail: contains },
        { actorRole: contains },
        { route: contains },
        { requestId: contains },
        { errorCode: contains },
      ],
    });
  }

  return { filters, where: AND.length ? { AND } : {} };
}

export function serializeAuditV2Row(row) {
  if (!row) return null;
  return {
    id: row.id,
    occurredAt: row.occurredAt,
    createdAt: row.createdAt,
    action: row.action,
    category: row.category,
    entityType: row.entityType,
    entityId: row.entityId,
    actor: {
      id: row.actorId,
      type: row.actorType,
      name: row.actorName,
      email: row.actorEmail,
      role: row.actorRole,
    },
    outcome: row.outcome,
    severity: row.severity,
    source: row.source,
    requestId: row.requestId,
    ipAddress: row.ipAddress,
    userAgent: row.userAgent,
    httpMethod: row.httpMethod,
    route: row.route,
    legacySource: row.legacySource,
    legacyId: row.legacyId,
    metadata: row.metadata,
    beforeState: row.beforeState,
    afterState: row.afterState,
    errorCode: row.errorCode,
    errorMessage: row.errorMessage,
  };
}

export async function listAuditV2(db, query = {}) {
  const { filters, where } = buildAuditV2Where(query);
  const [total, rows] = await Promise.all([
    db.auditEventV2.count({ where }),
    db.auditEventV2.findMany({
      where,
      orderBy: [{ occurredAt: "desc" }, { id: "desc" }],
      skip: (filters.page - 1) * filters.limit,
      take: filters.limit,
    }),
  ]);

  return {
    entries: rows.map(serializeAuditV2Row),
    page: filters.page,
    limit: filters.limit,
    total,
    totalPages: Math.max(1, Math.ceil(total / filters.limit)),
  };
}

async function distinctValues(db, field, take = 500) {
  const rows = await db.auditEventV2.findMany({
    distinct: [field],
    select: { [field]: true },
    orderBy: { [field]: "asc" },
    take,
  });
  return rows.map((row) => row[field]).filter(Boolean);
}

export async function auditV2Filters(db) {
  const [actions, categories, entityTypes, actorRoles, outcomes, severities, sources] = await Promise.all([
    distinctValues(db, "action"),
    distinctValues(db, "category"),
    distinctValues(db, "entityType"),
    distinctValues(db, "actorRole"),
    distinctValues(db, "outcome"),
    distinctValues(db, "severity"),
    distinctValues(db, "source"),
  ]);
  return { actions, categories, entityTypes, actorRoles, outcomes, severities, sources };
}

function csvSafeText(value) {
  if (value === undefined || value === null) return "";
  const text = typeof value === "object" ? JSON.stringify(value) : String(value);
  return /^[=+\-@]/.test(text) ? `'${text}` : text;
}

export function auditCsvCell(value) {
  return `"${csvSafeText(value).replaceAll('"', '""')}"`;
}

export function auditRowsToCsv(rows = []) {
  const columns = [
    "occurredAt", "action", "category", "severity", "outcome", "source",
    "actorId", "actorName", "actorEmail", "actorRole",
    "entityType", "entityId", "httpMethod", "route", "requestId",
    "ipAddress", "errorCode", "errorMessage", "metadata",
  ];
  const header = columns.map(auditCsvCell).join(",");
  const lines = rows.map((row) => columns.map((column) => auditCsvCell(row[column])).join(","));
  return [header, ...lines].join("\r\n");
}

export async function exportAuditV2Csv(db, query = {}) {
  const { where } = buildAuditV2Where(query);
  const take = clampAuditInt(query.exportLimit || query.limit, 5000, { min: 1, max: 5000 });
  const rows = await db.auditEventV2.findMany({
    where,
    orderBy: [{ occurredAt: "desc" }, { id: "desc" }],
    take,
  });
  return { csv: auditRowsToCsv(rows), count: rows.length };
}

export async function getAuditV2Event(db, id) {
  const row = await db.auditEventV2.findUnique({ where: { id: String(id || "") } });
  return serializeAuditV2Row(row);
}
