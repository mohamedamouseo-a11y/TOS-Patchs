import test from "node:test";
import assert from "node:assert/strict";
import { EventEmitter } from "node:events";
import {
  classifyCoreOperation,
  coreOperationPath,
  sanitizeCoreOperationMetadata,
  createCoreOperationsAuditMiddleware,
} from "./auditV2CoreOperations.js";

test("classifies project and task core operations", () => {
  assert.equal(classifyCoreOperation({ method: "POST", originalUrl: "/api/projects", body: {} })?.action, "PROJECT.CREATED");
  assert.equal(classifyCoreOperation({ method: "PATCH", originalUrl: "/api/projects/p1", body: { status: "ACTIVE" } })?.action, "PROJECT.STATUS_CHANGED");
  assert.equal(classifyCoreOperation({ method: "PATCH", originalUrl: "/api/tasks/t1", body: { status: "DONE" } })?.action, "TASK.STATUS_CHANGED");
  assert.equal(classifyCoreOperation({ method: "POST", originalUrl: "/api/tasks", body: { projectId: "p1" } })?.action, "TASK.CREATED");
});

test("classifies design queue lifecycle and assignment events precisely", () => {
  assert.equal(classifyCoreOperation({ method: "POST", originalUrl: "/api/tasks/reports/design-queue/requests", body: { projectId: "p1" } })?.action, "DESIGN_QUEUE.REQUEST_CREATED");
  assert.equal(classifyCoreOperation({ method: "PATCH", originalUrl: "/api/tasks/reports/design-queue/t1/assign", body: { assigneeId: "u1" } })?.action, "DESIGN_QUEUE.ASSIGNMENT_CHANGED");
  assert.equal(classifyCoreOperation({ method: "POST", originalUrl: "/api/tasks/reports/design-queue/t1/archive", body: {} })?.action, "DESIGN_QUEUE.REQUEST_ARCHIVED");
  assert.equal(classifyCoreOperation({ method: "POST", originalUrl: "/api/tasks/reports/design-queue/t1/restore", body: {} }), null);
});

test("classifies task board/list workflow and integrations including Trello", () => {
  assert.equal(classifyCoreOperation({ method: "POST", originalUrl: "/api/tasks/workspaces/w1/boards", body: {} })?.action, "TASK.BOARD.CREATED");
  assert.equal(classifyCoreOperation({ method: "PATCH", originalUrl: "/api/tasks/lists/l1", body: { status: "IN_PROGRESS" } })?.action, "TASK.LIST.UPDATED");
  assert.equal(classifyCoreOperation({ method: "POST", originalUrl: "/api/integrations/crm/pull", body: {} })?.action, "INTEGRATION.SYNC_TRIGGERED");
  assert.equal(classifyCoreOperation({ method: "POST", originalUrl: "/api/integrations/trello/sync", body: {} })?.action, "TRELLO.SYNC_TRIGGERED");
});

test("keeps Phase 4 sensitive/delete/restore scope out of Phase 3", () => {
  assert.equal(classifyCoreOperation({ method: "DELETE", originalUrl: "/api/tasks/t1", body: {} }), null);
  assert.equal(classifyCoreOperation({ method: "POST", originalUrl: "/api/tasks/t1/files", body: {} }), null);
  assert.equal(classifyCoreOperation({ method: "POST", originalUrl: "/api/integrations/crm/settings", body: {} }), null);
});

test("metadata strips query strings and never copies sensitive values", () => {
  const req = {
    method: "PATCH",
    originalUrl: "/api/tasks/t1?token=leak",
    body: {
      status: "DONE",
      password: "secret",
      apiKey: "secret-key",
      accessToken: "secret-token",
      title: "Safe title",
    },
  };
  assert.equal(coreOperationPath(req), "/api/tasks/t1");
  const metadata = sanitizeCoreOperationMetadata(req, 200);
  assert.equal(metadata.status, "DONE");
  assert.equal(metadata.title, "Safe title");
  assert.ok(!metadata.changedFields.includes("password"));
  assert.ok(!metadata.changedFields.includes("apiKey"));
  assert.ok(!metadata.changedFields.includes("accessToken"));
  assert.ok(!JSON.stringify(metadata).includes("secret"));
  assert.ok(!JSON.stringify(metadata).includes("leak"));
});

test("middleware writes one successful event through injected central-writer contract", async () => {
  const written = [];
  const middleware = createCoreOperationsAuditMiddleware({
    writer: async (event) => written.push(event),
  });
  const req = {
    method: "PATCH",
    originalUrl: "/api/tasks/t1?debug=true",
    body: { status: "DONE", token: "never-store-me" },
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
  assert.equal(written[0].action, "TASK.STATUS_CHANGED");
  assert.equal(written[0].category, "OPERATIONS");
  assert.equal(written[0].entityId, "t1");
  assert.equal(written[0].metadata.path, "/api/tasks/t1");
  assert.equal(written[0].metadata.statusCode, 200);
  assert.ok(!JSON.stringify(written[0].metadata).includes("never-store-me"));
  assert.ok(!JSON.stringify(written[0].afterState).includes("never-store-me"));
});

test("middleware does not write failed responses", async () => {
  const written = [];
  const middleware = createCoreOperationsAuditMiddleware({ writer: async (event) => written.push(event) });
  const req = { method: "PATCH", originalUrl: "/api/projects/p1", body: { status: "ACTIVE" }, user: { id: "u1" } };
  const res = new EventEmitter();
  res.statusCode = 403;
  middleware(req, res, () => {});
  res.emit("finish");
  await new Promise((resolve) => setImmediate(resolve));
  assert.equal(written.length, 0);
});
