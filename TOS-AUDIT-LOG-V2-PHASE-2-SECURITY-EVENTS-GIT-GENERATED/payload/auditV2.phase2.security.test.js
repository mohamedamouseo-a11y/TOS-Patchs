import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

const here = path.dirname(fileURLToPath(import.meta.url));
const srcRoot = path.resolve(here, "..");

async function read(relative) {
  return readFile(path.join(srcRoot, relative), "utf8");
}

test("auth routes emit login success, login failure, and logout security events without auditing passwords", async () => {
  const source = await read("routes/auth.routes.js");
  assert.match(source, /action:\s*"AUTH\.LOGIN\.SUCCESS"/);
  assert.match(source, /action:\s*"AUTH\.LOGIN\.FAILURE"/);
  assert.match(source, /action:\s*"AUTH\.LOGOUT"/);
  assert.match(source, /actorType:\s*"ANONYMOUS"/);
  assert.match(source, /metadata:\s*\{\s*attemptedEmail,\s*reason,\s*statusCode\s*\}/);
  assert.doesNotMatch(source, /auditLoginFailure\([^)]*password/i);
  assert.doesNotMatch(source, /metadata:\s*\{\s*password/i);
});

test("user lifecycle dual-writes security events and isolates system role changes", async () => {
  const source = await read("routes/users.routes.js");
  for (const action of [
    "USER.INVITED",
    "USER.INVITE_RESENT",
    "USER.PASSWORD_RESET_REQUESTED",
    "USER.INVITE_CANCELLED",
    "USER.MARKED_FORMER_EMPLOYEE",
    "USER.RESTORED",
    "USER.PERMANENTLY_DELETED",
    "USER.DISABLED",
    "USER.ENABLED",
    "USER.UPDATED",
    "ROLE.USER_ASSIGNMENT_CHANGED",
    "USER.PASSWORD_CHANGED_BY_ADMIN",
  ]) {
    assert.ok(source.includes(`"${action}"`), `missing ${action}`);
  }
  assert.match(source, /await auditPermissionChange\(\{ action, actorId, targetUserId, metadata \}\)/);
  assert.match(source, /await writeAuditEvent\(\{/);
  assert.match(source, /beforeState:\s*\{\s*role:\s*safeMetadata\.previousRole\s*\}/);
  assert.match(source, /afterState:\s*\{\s*role:\s*safeMetadata\.role\s*\}/);
});

test("permission routes pass request context into permission mutations", async () => {
  const source = await read("routes/permissions.routes.js");
  assert.match(source, /setRolePermission\(\{\s*req,\s*actor:\s*req\.user/);
  assert.match(source, /createUserPermissionOverride\(\{\s*req,\s*actor:\s*req\.user/);
  assert.match(source, /updateUserPermissionOverride\(\{\s*req,\s*actor:\s*req\.user/);
  assert.match(source, /deleteUserPermissionOverride\(\{\s*req,\s*actor:\s*req\.user/);
});

test("role permissions and user permission overrides dual-write to AuditEventV2", async () => {
  const source = await read("services/permissions.service.js");
  for (const action of [
    "ROLE.PERMISSION_CHANGED",
    "PERMISSION.USER_OVERRIDE_CREATED",
    "PERMISSION.USER_OVERRIDE_UPDATED",
    "PERMISSION.USER_OVERRIDE_DELETED",
  ]) {
    assert.ok(source.includes(`"${action}"`), `missing ${action}`);
  }
  assert.match(source, /previousEnabled/);
  assert.match(source, /beforeState:\s*\{\s*enabled:\s*previousEnabled\s*\}/);
  assert.match(source, /afterState:\s*\{\s*enabled:\s*Boolean\(enabled\)\s*\}/);
  assert.match(source, /entityType:\s*"UserPermissionOverride"/);
  assert.match(source, /category:\s*"SECURITY"/);
});

test("Phase 2 keeps V2 writes fail-open by using the central writer only", async () => {
  const [auth, users, permissions] = await Promise.all([
    read("routes/auth.routes.js"),
    read("routes/users.routes.js"),
    read("services/permissions.service.js"),
  ]);
  assert.match(auth, /import \{ writeAuditEvent \} from "\.\.\/services\/auditV2\.service\.js"/);
  assert.match(users, /import \{ writeAuditEvent \} from "\.\.\/services\/auditV2\.service\.js"/);
  assert.match(permissions, /import \{ writeAuditEvent \} from "\.\/auditV2\.service\.js"/);
  assert.doesNotMatch(auth, /auditEventV2\.create/);
  assert.doesNotMatch(users, /auditEventV2\.create/);
  assert.doesNotMatch(permissions, /auditEventV2\.create/);
});
