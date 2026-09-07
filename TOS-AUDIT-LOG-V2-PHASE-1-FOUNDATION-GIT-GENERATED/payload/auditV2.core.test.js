import test from "node:test";
import assert from "node:assert/strict";
import { buildAuditEventData } from "./auditV2.core.js";

test("builds actor and request snapshots while redacting event payloads", () => {
  const req = {
    user: { id: "user_1", email: "admin@example.com", role: "SUPER_ADMIN", name: "Admin" },
    auditContext: {
      requestId: "req-12345678",
      ipAddress: "203.0.113.15",
      userAgent: "AuditTest/1.0",
      httpMethod: "PATCH",
      route: "/api/users/user_2",
    },
  };

  const data = buildAuditEventData({
    req,
    action: "USER.UPDATE",
    category: "SECURITY",
    entityType: "User",
    entityId: "user_2",
    metadata: { password: "never-store", changedField: "role" },
  });

  assert.equal(data.actorId, "user_1");
  assert.equal(data.actorEmail, "admin@example.com");
  assert.equal(data.actorRole, "SUPER_ADMIN");
  assert.equal(data.actorType, "USER");
  assert.equal(data.requestId, "req-12345678");
  assert.equal(data.route, "/api/users/user_2");
  assert.equal(data.metadata.password, "[REDACTED]");
  assert.equal(data.metadata.changedField, "role");
});

test("defaults internal events to SYSTEM and rejects missing action", () => {
  assert.equal(buildAuditEventData({ action: "SYSTEM.TEST" }).actorType, "SYSTEM");
  assert.throws(() => buildAuditEventData({}), /action is required/);
});
