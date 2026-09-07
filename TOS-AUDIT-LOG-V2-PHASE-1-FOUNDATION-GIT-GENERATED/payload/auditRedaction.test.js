import test from "node:test";
import assert from "node:assert/strict";
import { AUDIT_REDACTED, redactAuditString, redactAuditValue } from "./auditRedaction.js";

test("recursively redacts sensitive audit fields without mutating input", () => {
  const input = {
    name: "safe",
    password: "secret-pass",
    nested: {
      access_token: "abc",
      profile: { email: "safe@example.com" },
    },
    headers: { Authorization: "Bearer top-secret" },
  };
  const result = redactAuditValue(input);

  assert.equal(result.name, "safe");
  assert.equal(result.password, AUDIT_REDACTED);
  assert.equal(result.nested.access_token, AUDIT_REDACTED);
  assert.equal(result.nested.profile.email, "safe@example.com");
  assert.equal(result.headers.Authorization, AUDIT_REDACTED);
  assert.equal(input.password, "secret-pass");
});

test("scrubs bearer/JWT-like values embedded in free text", () => {
  const value = "authorization: Bearer abc.def.ghi password=hunter2";
  const result = redactAuditString(value);
  assert.equal(result.includes("hunter2"), false);
  assert.equal(result.includes("abc.def.ghi"), false);
  assert.equal(result.includes(AUDIT_REDACTED), true);
});

test("handles dates, bigint and circular references safely", () => {
  const input = { at: new Date("2026-09-07T00:00:00.000Z"), count: 7n };
  input.self = input;
  const result = redactAuditValue(input);
  assert.equal(result.at, "2026-09-07T00:00:00.000Z");
  assert.equal(result.count, "7");
  assert.equal(result.self, "[CIRCULAR]");
});
