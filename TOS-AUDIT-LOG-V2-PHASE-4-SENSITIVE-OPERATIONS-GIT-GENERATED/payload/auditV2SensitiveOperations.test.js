import test from "node:test";
import assert from "node:assert/strict";
import { EventEmitter } from "node:events";
import {
  classifySensitiveOperation,
  sensitiveOperationPath,
  sanitizeSensitiveOperationMetadata,
  createSensitiveOperationsAuditMiddleware,
} from "./auditV2SensitiveOperations.js";

test("classifies file upload, download, preview and deletion", () => {
  assert.equal(classifySensitiveOperation({ method: "POST", originalUrl: "/api/files/upload", body: {} })?.action, "FILE.UPLOADED");
  assert.equal(classifySensitiveOperation({ method: "GET", originalUrl: "/api/files/f1/download", body: {} })?.action, "FILE.DOWNLOADED");
  assert.equal(classifySensitiveOperation({ method: "GET", originalUrl: "/api/files/f1/preview", body: {} })?.action, "FILE.PREVIEWED");
  assert.equal(classifySensitiveOperation({ method: "DELETE", originalUrl: "/api/files/f1", body: {} })?.action, "FILE.DELETED");
});

test("classifies high-value chat mutations without routine noise", () => {
  assert.equal(classifySensitiveOperation({ method: "POST", originalUrl: "/api/chat/messages", body: { body: "secret text" } })?.action, "CHAT.MESSAGE_SENT");
  assert.equal(classifySensitiveOperation({ method: "PATCH", originalUrl: "/api/chat/messages/m1", body: { body: "edited" } })?.action, "CHAT.MESSAGE_EDITED");
  assert.equal(classifySensitiveOperation({ method: "DELETE", originalUrl: "/api/chat/messages/m1", body: {} })?.action, "CHAT.MESSAGE_DELETED");
  assert.equal(classifySensitiveOperation({ method: "PATCH", originalUrl: "/api/chat/presence", body: { presenceStatus: "ONLINE" } }), null);
  assert.equal(classifySensitiveOperation({ method: "POST", originalUrl: "/api/chat/messages/read", body: {} }), null);
});

test("classifies central native chat and chat file downloads", () => {
  assert.equal(classifySensitiveOperation({ method: "POST", originalUrl: "/api/central-chat/native/conversations/direct", body: { userId: "u2" } })?.action, "CHAT.CONVERSATION_CREATED");
  assert.equal(classifySensitiveOperation({ method: "GET", originalUrl: "/api/central-chat/native/files/f9/download?token=leak", body: {} })?.action, "CHAT.FILE_DOWNLOADED");
});

test("classifies settings, admin and backup operations", () => {
  assert.equal(classifySensitiveOperation({ method: "PATCH", originalUrl: "/api/email-settings", body: { host: "smtp" } })?.action, "SETTINGS.EMAIL_CHANGED");
  assert.equal(classifySensitiveOperation({ method: "POST", originalUrl: "/api/email-settings/test", body: { to: "a@example.com" } })?.action, "SETTINGS.EMAIL_TEST_TRIGGERED");
  assert.equal(classifySensitiveOperation({ method: "PATCH", originalUrl: "/api/system-backups/settings", body: { enabled: true } })?.action, "BACKUP.SYSTEM_SETTINGS_CHANGED");
  assert.equal(classifySensitiveOperation({ method: "POST", originalUrl: "/api/system-backups/run-now", body: {} })?.action, "BACKUP.SYSTEM_RUN_TRIGGERED");
  assert.equal(classifySensitiveOperation({ method: "PATCH", originalUrl: "/api/notification-center/admin/governance", body: { enabled: true } })?.action, "ADMIN.OPERATION_EXECUTED");
});

test("classifies database backup restore with critical confirm severity", () => {
  const prepared = classifySensitiveOperation({ method: "POST", originalUrl: "/api/database-backups/restore/b1/prepare", body: {} });
  const confirmed = classifySensitiveOperation({ method: "POST", originalUrl: "/api/database-backups/restore/b1/confirm", body: { confirmationToken: "secret", confirmationText: "RESTORE" } });
  assert.equal(prepared?.action, "BACKUP.DATABASE_RESTORE_PREPARED");
  assert.equal(prepared?.entityId, "b1");
  assert.equal(confirmed?.action, "BACKUP.DATABASE_RESTORE_CONFIRMED");
  assert.equal(confirmed?.severity, "CRITICAL");
});

test("classifies generic delete, restore, export and download while Phase 2 owns users", () => {
  assert.equal(classifySensitiveOperation({ method: "DELETE", originalUrl: "/api/tasks/t1", body: {} })?.action, "TASK.DELETED");
  assert.equal(classifySensitiveOperation({ method: "POST", originalUrl: "/api/tasks/reports/design-queue/t1/restore", body: {} })?.action, "DESIGN_QUEUE.REQUEST_RESTORED");
  assert.equal(classifySensitiveOperation({ method: "GET", originalUrl: "/api/reports/export", body: {} })?.action, "DATA.EXPORTED");
  assert.equal(classifySensitiveOperation({ method: "DELETE", originalUrl: "/api/users/u1", body: {} }), null);
});

test("metadata strips query strings, content and credentials", () => {
  const req = {
    method: "POST",
    originalUrl: "/api/database-backups/restore/b1/confirm?confirmationToken=leak",
    body: {
      confirmationToken: "secret-token",
      confirmationText: "RESTORE NOW",
      password: "secret",
      body: "private message body",
      status: "READY",
      projectId: "p1",
    },
  };
  assert.equal(sensitiveOperationPath(req), "/api/database-backups/restore/b1/confirm");
  const metadata = sanitizeSensitiveOperationMetadata(req, 200);
  const serialized = JSON.stringify(metadata);
  assert.equal(metadata.status, "READY");
  assert.equal(metadata.projectId, "p1");
  assert.ok(!serialized.includes("secret"));
  assert.ok(!serialized.includes("leak"));
  assert.ok(!serialized.includes("private message"));
  assert.ok(!metadata.changedFields.includes("body"));
  assert.ok(!metadata.changedFields.includes("confirmationToken"));
});

test("middleware writes successful event through central-writer contract", async () => {
  const written = [];
  const middleware = createSensitiveOperationsAuditMiddleware({ writer: async (event) => written.push(event) });
  const req = {
    method: "DELETE",
    originalUrl: "/api/files/f1",
    body: { fileId: "f1", token: "never-store-me" },
    user: { id: "u1", name: "Ahmed", email: "a@example.com", role: "ADMIN" },
  };
  const res = new EventEmitter();
  res.statusCode = 200;
  let nextCalled = false;
  middleware(req, res, () => { nextCalled = true; });
  assert.equal(nextCalled, true);
  res.emit("finish");
  await new Promise((resolve) => setImmediate(resolve));
  assert.equal(written.length, 1);
  assert.equal(written[0].action, "FILE.DELETED");
  assert.equal(written[0].category, "SENSITIVE_OPERATIONS");
  assert.equal(written[0].severity, "WARN");
  assert.equal(written[0].metadata.path, "/api/files/f1");
  assert.ok(!JSON.stringify(written[0].metadata).includes("never-store-me"));
});

test("middleware ignores failed responses and fail-opens writer rejection", async () => {
  const written = [];
  const middleware = createSensitiveOperationsAuditMiddleware({ writer: async (event) => { written.push(event); throw new Error("db down"); } });
  const req = { method: "POST", originalUrl: "/api/system-backups/run-now", body: {}, user: { id: "u1" } };
  const failed = new EventEmitter();
  failed.statusCode = 403;
  middleware(req, failed, () => {});
  failed.emit("finish");
  await new Promise((resolve) => setImmediate(resolve));
  assert.equal(written.length, 0);

  const ok = new EventEmitter();
  ok.statusCode = 200;
  middleware(req, ok, () => {});
  ok.emit("finish");
  await new Promise((resolve) => setImmediate(resolve));
  assert.equal(written.length, 1);
});
