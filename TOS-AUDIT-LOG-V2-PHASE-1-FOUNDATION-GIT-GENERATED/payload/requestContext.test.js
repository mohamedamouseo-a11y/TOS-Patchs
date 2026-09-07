import test from "node:test";
import assert from "node:assert/strict";
import { requestContextMiddleware, requestPathOnly, sanitizeRequestId } from "./requestContext.js";

test("accepts a safe upstream request id", () => {
  assert.equal(sanitizeRequestId("req-12345678"), "req-12345678");
  assert.equal(sanitizeRequestId("bad id with spaces"), null);
});

test("captures safe request metadata and never stores the query string", () => {
  const req = {
    headers: { "x-request-id": "req-12345678", "user-agent": "AuditTest/1.0" },
    ip: "203.0.113.15",
    method: "post",
    originalUrl: "/api/users?access_token=must-not-leak",
  };
  const headers = {};
  const res = { setHeader(name, value) { headers[name] = value; } };
  let nextCalled = false;

  requestContextMiddleware(req, res, () => { nextCalled = true; });

  assert.equal(nextCalled, true);
  assert.equal(req.auditContext.requestId, "req-12345678");
  assert.equal(req.auditContext.route, "/api/users");
  assert.equal(req.auditContext.httpMethod, "POST");
  assert.equal(headers["X-Request-Id"], "req-12345678");
  assert.equal(JSON.stringify(req.auditContext).includes("must-not-leak"), false);
  assert.equal(requestPathOnly(req), "/api/users");
});

test("generates a request id when incoming id is unsafe", () => {
  const req = { headers: { "x-request-id": "x" }, method: "GET", url: "/health" };
  const res = { setHeader() {} };
  requestContextMiddleware(req, res, () => {});
  assert.match(req.auditContext.requestId, /^[0-9a-f-]{36}$/i);
});
