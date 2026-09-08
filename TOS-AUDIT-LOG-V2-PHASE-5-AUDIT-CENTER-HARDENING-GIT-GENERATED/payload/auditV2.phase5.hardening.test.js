import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  auditCsvCell,
  auditRowsToCsv,
  buildAuditV2Where,
  parseAuditV2Query,
  serializeAuditV2Row,
} from "./auditV2.center.js";
import {
  auditRetentionDays,
  auditRetentionPolicy,
  purgeExpiredAuditEvents,
} from "./auditV2.retention.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const BACKEND_ROOT = path.resolve(__dirname, "../..");
const MIGRATION = path.join(BACKEND_ROOT, "prisma/migrations/20260908073000_audit_log_v2_hardening/migration.sql");
const SCHEMA = path.join(BACKEND_ROOT, "prisma/schema.prisma");
const ROUTE = path.join(BACKEND_ROOT, "src/routes/auditLog.routes.js");

test("normalizes Audit Center V2 filters and pagination bounds", () => {
  const parsed = parseAuditV2Query({ page: "0", limit: "999", q: "  auth  ", severity: "warn" });
  assert.equal(parsed.page, 1);
  assert.equal(parsed.limit, 200);
  assert.equal(parsed.q, "auth");
  assert.equal(parsed.severity, "WARN");

  const { where } = buildAuditV2Where({ q: "LOGIN", projectId: "p1", outcome: "SUCCESS" });
  assert.ok(Array.isArray(where.AND));
  assert.ok(JSON.stringify(where).includes("LOGIN"));
  assert.ok(JSON.stringify(where).includes("projectId"));
});

test("serializes AuditEventV2 rows into the stable center contract", () => {
  const row = serializeAuditV2Row({
    id: "a1", action: "AUTH.LOGIN.SUCCESS", category: "SECURITY", actorId: "u1", actorType: "USER",
    actorName: "User", actorEmail: "u@example.com", actorRole: "ADMIN", outcome: "SUCCESS", severity: "INFO",
    source: "TOS", occurredAt: new Date("2026-09-08T00:00:00Z"), createdAt: new Date("2026-09-08T00:00:00Z"),
  });
  assert.equal(row.actor.id, "u1");
  assert.equal(row.action, "AUTH.LOGIN.SUCCESS");
  assert.equal(row.category, "SECURITY");
});

test("CSV export prevents spreadsheet formula injection", () => {
  assert.equal(auditCsvCell("=2+2"), '"\'=2+2"');
  const csv = auditRowsToCsv([{ action: "+SUM(A1:A2)", actorEmail: "safe@example.com" }]);
  assert.ok(csv.includes("'+SUM(A1:A2)"));
  assert.ok(csv.includes("safe@example.com"));
});

test("retention clamps policy and calculates deterministic cutoff", () => {
  assert.equal(auditRetentionDays("1"), 30);
  assert.equal(auditRetentionDays("99999"), 3650);
  assert.equal(auditRetentionDays("bad"), 365);
  const policy = auditRetentionPolicy({ days: 365, now: new Date("2026-09-08T00:00:00Z") });
  assert.equal(policy.days, 365);
  assert.equal(policy.cutoff.toISOString(), "2025-09-08T00:00:00.000Z");
});

test("controlled retention enables the transaction-local delete gate and audits the purge", async () => {
  const calls = [];
  const db = {
    $transaction: async (fn) => fn({
      $queryRawUnsafe: async (sql) => calls.push(sql),
      auditEventV2: { deleteMany: async ({ where }) => { calls.push(where); return { count: 7 }; } },
    }),
  };
  const written = [];
  const result = await purgeExpiredAuditEvents(db, {
    days: 365,
    now: new Date("2026-09-08T00:00:00Z"),
    writer: async (event) => written.push(event),
    actor: { id: "u1", role: "SUPER_ADMIN" },
  });
  assert.equal(result.deletedCount, 7);
  assert.ok(String(calls[0]).includes("audit_v2_retention_purge"));
  assert.equal(written[0].action, "AUDIT.RETENTION_PURGE");
});

test("database migration enforces append-only UPDATE and controlled DELETE", () => {
  const sql = fs.readFileSync(MIGRATION, "utf8");
  assert.ok(sql.includes("BEFORE UPDATE OR DELETE"));
  assert.ok(sql.includes("AuditEventV2 is append-only"));
  assert.ok(sql.includes("app.audit_v2_retention_purge"));
  assert.ok(sql.includes("AuditEventV2_severity_occurredAt_idx"));
  assert.ok(sql.includes("AuditEventV2_source_occurredAt_idx"));
});

test("Prisma model contains Phase 5 query-hardening indexes", () => {
  const schema = fs.readFileSync(SCHEMA, "utf8");
  assert.ok(schema.includes("@@index([entityType, entityId, occurredAt])"));
  assert.ok(schema.includes("@@index([outcome, occurredAt])"));
  assert.ok(schema.includes("@@index([severity, occurredAt])"));
  assert.ok(schema.includes("@@index([source, occurredAt])"));
});

test("Audit Center V2 endpoints coexist with the legacy merged audit endpoint", () => {
  const source = fs.readFileSync(ROUTE, "utf8");
  for (const route of ["/v2", "/v2/filters", "/v2/export", "/v2/retention", "/v2/retention/run", "/v2/:id"]) {
    assert.ok(source.includes(`router.${route === "/v2/retention/run" ? "post" : "get"}(\"${route}\"`));
  }
  assert.ok(source.includes('router.get("/"'));
  assert.ok(source.includes("prisma.chatAuditLog.findMany"));
  assert.ok(source.includes("prisma.permissionAuditLog.findMany"));
  assert.ok(source.includes("prisma.projectActivity.findMany"));
  assert.ok(source.includes("prisma.taskActivity.findMany"));
});
