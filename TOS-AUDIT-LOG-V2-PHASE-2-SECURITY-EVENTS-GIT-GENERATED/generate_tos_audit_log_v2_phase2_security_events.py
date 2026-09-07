#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PATCH_NAME = "TOS-AUDIT-LOG-V2-PHASE-2-SECURITY-EVENTS-GIT-GENERATED"
EXPECTED_HEAD = "39f71ff9d4db541a86cd102e7091404bcfb89ccf"
MODIFIED_BLOBS = {
    "backend/src/routes/auth.routes.js": "90cb9e4c2e34739429aed189f7996017ef31c988",
    "backend/src/routes/users.routes.js": "2d65febb608d33aac2077e86eb70198feaaf50f6",
    "backend/src/routes/permissions.routes.js": "afd5d25fdf7e137ab4399fc9e8674c37800baf2d",
    "backend/src/services/permissions.service.js": "42f19f7327ccce834ee4569643eb6df571f2482b",
}
FOUNDATION_BLOBS = {
    "backend/prisma/schema.prisma": "8e54719b3496d04fd1fa2a9c085fa6f5e6f59572",
    "backend/src/routes/auditLog.routes.js": "cfde2be53f2654ca98bd792df81253984c56d835",
    "backend/src/middleware/requestContext.js": "0a967751b18240191c2cabdae1703592380b389c",
    "backend/src/services/auditV2.core.js": "3650c2baa3a881abd2abc53b58ac2c7e3942a44f",
    "backend/src/services/auditV2.service.js": "70bcbbd1772891fd5626d5d3e341a594c501851a",
    "backend/src/utils/auditRedaction.js": "b94eb6740cdc5e017ed8b541d81a44f7c95be31a",
}
NEW_FILES = {
    "backend/src/services/auditV2.phase2.security.test.js": "auditV2.phase2.security.test.js",
}
PATCH_PATHS = [*MODIFIED_BLOBS, *NEW_FILES]
EXPECTED_PATCH_PATHS = set(PATCH_PATHS)
OUTPUT_NAME = "tos-audit-log-v2-phase2-security-events.patch"


def run(cmd, cwd, check=True, capture=True):
    result = subprocess.run(
        cmd,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )
    if check and result.returncode != 0:
        if capture:
            sys.stderr.write(result.stdout or "")
            sys.stderr.write(result.stderr or "")
        raise RuntimeError(f"command failed ({result.returncode}): {' '.join(cmd)}")
    return result


def git(repo, *args):
    return run(["git", *args], repo).stdout.strip()


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def replace_once(text, old, new, label):
    count = text.count(old)
    require(count == 1, f"{label}: expected exactly one anchor, found {count}")
    return text.replace(old, new, 1)


def write_text(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def validate_patch_paths(tmp):
    changed = {
        line.strip()
        for line in git(tmp, "diff", "--name-only", "HEAD", "--", *PATCH_PATHS).splitlines()
        if line.strip()
    }
    missing = sorted(EXPECTED_PATCH_PATHS - changed)
    unexpected = sorted(changed - EXPECTED_PATCH_PATHS)
    require(
        changed == EXPECTED_PATCH_PATHS,
        f"generated patch path set mismatch; missing={missing}, unexpected={unexpected}, changed={sorted(changed)}",
    )

    statuses = git(tmp, "diff", "--name-status", "HEAD", "--", *PATCH_PATHS).splitlines()
    added = {
        line.split("\t", 1)[1]
        for line in statuses
        if line.startswith("A\t") and "\t" in line
    }
    require(
        added == set(NEW_FILES),
        f"new-file coverage mismatch; expected={sorted(NEW_FILES)}, added={sorted(added)}",
    )


AUTH_HELPERS = r'''
async function auditLoginFailure(req, { attemptedEmail = null, reason, entityId = null, statusCode = 401 } = {}) {
  return writeAuditEvent({
    req,
    action: "AUTH.LOGIN.FAILURE",
    category: "SECURITY",
    entityType: "User",
    entityId,
    actorType: "ANONYMOUS",
    outcome: "FAILURE",
    severity: "WARN",
    metadata: { attemptedEmail, reason, statusCode },
  });
}

async function auditLoginSuccess(req, user, method = "PASSWORD") {
  return writeAuditEvent({
    req,
    action: "AUTH.LOGIN.SUCCESS",
    category: "SECURITY",
    entityType: "User",
    entityId: user?.id || null,
    actor: user || null,
    outcome: "SUCCESS",
    severity: "INFO",
    metadata: { method },
  });
}

async function auditLogout(req, user) {
  return writeAuditEvent({
    req,
    action: "AUTH.LOGOUT",
    category: "SECURITY",
    entityType: "User",
    entityId: user?.id || null,
    actor: user || null,
    outcome: "SUCCESS",
    severity: "INFO",
  });
}
'''.strip()


NEW_LOGIN_ROUTE = r'''router.post("/login", loginLimiter, asyncHandler(async (req, res) => {
  const email = normalizeEmail(req.body.email);
  const password = required(req.body.password, "password");
  const user = await prisma.user.findUnique({ where: { email } });
  if (!user || !user.passwordHash) {
    await auditLoginFailure(req, { attemptedEmail: email, reason: "INVALID_CREDENTIALS", entityId: user?.id || null, statusCode: 401 });
    throw new AppError("Invalid credentials", 401);
  }
  if (user.status === "PENDING") {
    await auditLoginFailure(req, { attemptedEmail: email, reason: "ACCOUNT_PENDING", entityId: user.id, statusCode: 403 });
    throw new AppError("Please accept your invitation first", 403);
  }
  if (user.status === "DISABLED") {
    await auditLoginFailure(req, { attemptedEmail: email, reason: "ACCOUNT_DISABLED", entityId: user.id, statusCode: 403 });
    throw new AppError("This account is disabled", 403);
  }
  const ok = await bcrypt.compare(password, user.passwordHash);
  if (!ok) {
    await auditLoginFailure(req, { attemptedEmail: email, reason: "INVALID_CREDENTIALS", entityId: user.id, statusCode: 401 });
    throw new AppError("Invalid credentials", 401);
  }
  const updated = await prisma.user.update({ where: { id: user.id }, data: { lastLoginAt: new Date(), lastActivityAt: new Date() } });
  const repaired = await ensureProtectedSuperAdminUser(prisma, updated);
  if (isTosStaffRole(repaired.role)) {
    await ensureDailyCheckIn(repaired.id, req, "TOS_LOGIN");
  }
  const csrfToken = setAuthCookie(res, repaired);
  await auditLoginSuccess(req, repaired, "PASSWORD");
  res.json({ user: sanitizeUser(repaired), csrfToken });
}));'''


OLD_LOGIN_ROUTE = r'''router.post("/login", loginLimiter, asyncHandler(async (req, res) => {
  const email = normalizeEmail(req.body.email);
  const password = required(req.body.password, "password");
  const user = await prisma.user.findUnique({ where: { email } });
  if (!user || !user.passwordHash) throw new AppError("Invalid credentials", 401);
  if (user.status === "PENDING") throw new AppError("Please accept your invitation first", 403);
  if (user.status === "DISABLED") throw new AppError("This account is disabled", 403);
  const ok = await bcrypt.compare(password, user.passwordHash);
  if (!ok) throw new AppError("Invalid credentials", 401);
  const updated = await prisma.user.update({ where: { id: user.id }, data: { lastLoginAt: new Date(), lastActivityAt: new Date() } });
  const repaired = await ensureProtectedSuperAdminUser(prisma, updated);
  if (isTosStaffRole(repaired.role)) {
    await ensureDailyCheckIn(repaired.id, req, "TOS_LOGIN");
  }
  const csrfToken = setAuthCookie(res, repaired);
  res.json({ user: sanitizeUser(repaired), csrfToken });
}));'''


OLD_LOGOUT_ROUTE = r'''router.post("/logout", asyncHandler(async (req, res) => {
  const bearer = (req.headers.authorization || "").replace("Bearer ", "");
  const token = bearer || readCookieFromHeader(req.headers.cookie, "tamiyouz_access_token");
  if (token) {
    try {
      const payload = verifyToken(token);
      if (payload?.id) {
        const user = await prisma.user.findUnique({ where: { id: payload.id }, select: { id: true, role: true } });
        if (isTosStaffRole(user?.role)) {
          await recordDailyCheckOut(user.id, req, "TOS_LOGOUT");
        }
      }
    } catch {
      // Logout must still clear cookies even if the token is already invalid/expired.
    }
  }
  res.clearCookie("tamiyouz_access_token", authCookieOptions({ withMaxAge: false }));
  clearCsrfCookie(res);
  res.json({ ok: true });
}));'''


NEW_LOGOUT_ROUTE = r'''router.post("/logout", asyncHandler(async (req, res) => {
  const bearer = (req.headers.authorization || "").replace("Bearer ", "");
  const token = bearer || readCookieFromHeader(req.headers.cookie, "tamiyouz_access_token");
  let logoutUser = null;
  if (token) {
    try {
      const payload = verifyToken(token);
      if (payload?.id) {
        logoutUser = await prisma.user.findUnique({
          where: { id: payload.id },
          select: { id: true, name: true, email: true, role: true },
        });
        if (isTosStaffRole(logoutUser?.role)) {
          await recordDailyCheckOut(logoutUser.id, req, "TOS_LOGOUT");
        }
      }
    } catch {
      // Logout must still clear cookies even if the token is already invalid/expired.
    }
  }
  res.clearCookie("tamiyouz_access_token", authCookieOptions({ withMaxAge: false }));
  clearCsrfCookie(res);
  if (logoutUser) await auditLogout(req, logoutUser);
  res.json({ ok: true });
}));'''


USERS_AUDIT_HELPER = r'''const TEAM_AUDIT_V2_ACTIONS = new Map([
  ["TEAM_DEPARTMENT_MANAGER_UPDATED", "ROLE.DEPARTMENT_MANAGER_CHANGED"],
  ["TEAM_DEPARTMENT_DEPUTY_UPDATED", "ROLE.DEPARTMENT_DEPUTY_CHANGED"],
  ["TEAM_MEMBER_INVITED", "USER.INVITED"],
  ["TEAM_INVITE_RESENT", "USER.INVITE_RESENT"],
  ["TEAM_MEMBER_PASSWORD_RESET_REQUESTED", "USER.PASSWORD_RESET_REQUESTED"],
  ["TEAM_INVITE_CANCELLED", "USER.INVITE_CANCELLED"],
  ["TEAM_MEMBER_MARKED_FORMER_EMPLOYEE", "USER.MARKED_FORMER_EMPLOYEE"],
  ["FORMER_EMPLOYEE_RESTORED", "USER.RESTORED"],
  ["FORMER_EMPLOYEE_PERMANENTLY_DELETED", "USER.PERMANENTLY_DELETED"],
  ["TEAM_MEMBER_DISABLED", "USER.DISABLED"],
  ["TEAM_MEMBER_ENABLED", "USER.ENABLED"],
  ["TEAM_MEMBER_UPDATED", "USER.UPDATED"],
]);

function teamAuditSnapshots(action, metadata = {}) {
  if (action === "TEAM_MEMBER_UPDATED") {
    return {
      beforeState: {
        role: metadata.previousRole ?? null,
        department: metadata.previousDepartment ?? null,
        email: metadata.previousEmail ?? null,
      },
      afterState: {
        role: metadata.role ?? null,
        department: metadata.department ?? null,
        email: metadata.email ?? null,
      },
    };
  }
  if (action === "TEAM_MEMBER_DISABLED" || action === "TEAM_MEMBER_ENABLED") {
    return {
      beforeState: { status: metadata.previousStatus ?? null },
      afterState: { status: metadata.status ?? null },
    };
  }
  if (action === "TEAM_MEMBER_MARKED_FORMER_EMPLOYEE") {
    return {
      beforeState: { role: metadata.previousRole ?? null, status: metadata.previousStatus ?? null },
      afterState: { role: "FORMER_EMPLOYEE", status: "DISABLED" },
    };
  }
  if (action === "FORMER_EMPLOYEE_RESTORED") {
    return {
      beforeState: { role: metadata.previousRole ?? "FORMER_EMPLOYEE" },
      afterState: { role: metadata.restoredRole ?? null, status: metadata.restoredStatus ?? null },
    };
  }
  if (action === "TEAM_MEMBER_INVITED") {
    return {
      beforeState: null,
      afterState: { role: metadata.role ?? null, department: metadata.department ?? null, status: "PENDING" },
    };
  }
  if (action === "FORMER_EMPLOYEE_PERMANENTLY_DELETED") {
    return {
      beforeState: { id: metadata.deletedUserId ?? null, email: metadata.email ?? null, name: metadata.name ?? null },
      afterState: null,
    };
  }
  return { beforeState: null, afterState: null };
}

async function logTeamAudit({ req = null, action, actorId = null, targetUserId = null, metadata = null }) {
  await auditPermissionChange({ action, actorId, targetUserId, metadata });

  const v2Action = TEAM_AUDIT_V2_ACTIONS.get(action);
  if (!v2Action) return;

  const safeMetadata = metadata && typeof metadata === "object" ? metadata : {};
  const departmentRoleEvent = action === "TEAM_DEPARTMENT_MANAGER_UPDATED" || action === "TEAM_DEPARTMENT_DEPUTY_UPDATED";
  const entityId = departmentRoleEvent
    ? (safeMetadata.departmentKey || null)
    : (targetUserId || safeMetadata.deletedUserId || null);
  const { beforeState, afterState } = teamAuditSnapshots(action, safeMetadata);

  await writeAuditEvent({
    req,
    action: v2Action,
    category: "SECURITY",
    entityType: departmentRoleEvent ? "DepartmentRole" : "User",
    entityId,
    actor: req?.user || null,
    actorId,
    outcome: "SUCCESS",
    severity: action === "FORMER_EMPLOYEE_PERMANENTLY_DELETED" ? "WARN" : "INFO",
    metadata: { legacyAction: action, ...safeMetadata },
    beforeState,
    afterState,
  });

  if (
    action === "TEAM_MEMBER_UPDATED"
    && safeMetadata.previousRole
    && safeMetadata.role
    && safeMetadata.previousRole !== safeMetadata.role
  ) {
    await writeAuditEvent({
      req,
      action: "ROLE.USER_ASSIGNMENT_CHANGED",
      category: "SECURITY",
      entityType: "User",
      entityId,
      actor: req?.user || null,
      actorId,
      outcome: "SUCCESS",
      severity: "INFO",
      metadata: { sourceAction: action },
      beforeState: { role: safeMetadata.previousRole },
      afterState: { role: safeMetadata.role },
    });
  }

  if (action === "TEAM_MEMBER_UPDATED" && safeMetadata.passwordChanged === true) {
    await writeAuditEvent({
      req,
      action: "USER.PASSWORD_CHANGED_BY_ADMIN",
      category: "SECURITY",
      entityType: "User",
      entityId,
      actor: req?.user || null,
      actorId,
      outcome: "SUCCESS",
      severity: "WARN",
      metadata: { sourceAction: action },
    });
  }
}'''


OLD_USERS_AUDIT_HELPER = r'''async function logTeamAudit({ action, actorId = null, targetUserId = null, metadata = null }) {
  await auditPermissionChange({ action, actorId, targetUserId, metadata });
}'''


def patch_auth(text):
    text = replace_once(
        text,
        'import { ensureDailyCheckIn, isTosStaffRole, recordDailyCheckOut } from "../services/employeeWork.service.js";',
        'import { ensureDailyCheckIn, isTosStaffRole, recordDailyCheckOut } from "../services/employeeWork.service.js";\nimport { writeAuditEvent } from "../services/auditV2.service.js";',
        "auth import",
    )
    set_cookie_anchor = r'''function setAuthCookie(res, user) {
  const token = signToken(user);
  res.cookie("tamiyouz_access_token", token, authCookieOptions());
  return setCsrfCookie(res);
}'''
    text = replace_once(
        text,
        set_cookie_anchor,
        set_cookie_anchor + "\n\n\n" + AUTH_HELPERS,
        "auth helper insertion",
    )
    text = replace_once(text, OLD_LOGIN_ROUTE, NEW_LOGIN_ROUTE, "login route")
    text = replace_once(text, OLD_LOGOUT_ROUTE, NEW_LOGOUT_ROUTE, "logout route")
    return text


def patch_users(text):
    text = replace_once(
        text,
        'import { auditPermissionChange } from "../services/permissions.service.js";',
        'import { auditPermissionChange } from "../services/permissions.service.js";\nimport { writeAuditEvent } from "../services/auditV2.service.js";',
        "users import",
    )
    text = replace_once(text, OLD_USERS_AUDIT_HELPER, USERS_AUDIT_HELPER, "users audit helper")
    call_count = text.count("await logTeamAudit({")
    require(call_count >= 10, f"expected at least 10 team audit calls, found {call_count}")
    text = text.replace("await logTeamAudit({", "await logTeamAudit({ req,")
    require("await logTeamAudit({" not in text, "unscoped team audit call remained")
    return text


def patch_permissions_routes(text):
    text = replace_once(
        text,
        "await setRolePermission({ actor: req.user, role, permissionKey, enabled });",
        "await setRolePermission({ req, actor: req.user, role, permissionKey, enabled });",
        "role permission route context",
    )
    text = replace_once(
        text,
        "const saved = await createUserPermissionOverride({\n    actor: req.user,",
        "const saved = await createUserPermissionOverride({\n    req,\n    actor: req.user,",
        "override create route context",
    )
    text = replace_once(
        text,
        "res.json(await updateUserPermissionOverride({\n    actor: req.user,",
        "res.json(await updateUserPermissionOverride({\n    req,\n    actor: req.user,",
        "override update route context",
    )
    text = replace_once(
        text,
        "res.json(await deleteUserPermissionOverride({ actor: req.user, overrideId }));",
        "res.json(await deleteUserPermissionOverride({ req, actor: req.user, overrideId }));",
        "override delete route context",
    )
    return text


def patch_permissions_service(text):
    text = replace_once(
        text,
        'import { AppError } from "../middleware/errors.js";',
        'import { AppError } from "../middleware/errors.js";\nimport { writeAuditEvent } from "./auditV2.service.js";',
        "permissions service import",
    )
    text = replace_once(
        text,
        "export async function setRolePermission({ actor, role, permissionKey, enabled }) {",
        "export async function setRolePermission({ req = null, actor, role, permissionKey, enabled }) {",
        "set role permission signature",
    )
    permission_anchor = r'''  const permission = await prisma.permission.findUnique({ where: { key: permissionKey } });
  const saved = await prisma.rolePermission.upsert({'''
    permission_insert = r'''  const permission = await prisma.permission.findUnique({ where: { key: permissionKey } });
  const previousRolePermission = await prisma.rolePermission.findUnique({
    where: { role_permissionId: { role, permissionId: permission.id } },
    select: { enabled: true },
  });
  const previousEnabled = previousRolePermission?.enabled ?? rolePermissionEnabled(role, permissionKey);
  const saved = await prisma.rolePermission.upsert({'''
    text = replace_once(text, permission_anchor, permission_insert, "role permission before-state")

    role_audit_anchor = r'''  await auditPermissionChange({
    action: "ROLE_PERMISSION_UPDATED",
    actorId: actor.id,
    role,
    permissionKey,
    metadata: { enabled: Boolean(enabled), actorRole: actor.role, managedByFallbackAdmin: actor.role === "ADMIN" },
  });
  return saved;'''
    role_audit_insert = r'''  await auditPermissionChange({
    action: "ROLE_PERMISSION_UPDATED",
    actorId: actor.id,
    role,
    permissionKey,
    metadata: { enabled: Boolean(enabled), actorRole: actor.role, managedByFallbackAdmin: actor.role === "ADMIN" },
  });
  await writeAuditEvent({
    req,
    action: "ROLE.PERMISSION_CHANGED",
    category: "SECURITY",
    entityType: "RolePermission",
    entityId: `${role}:${permissionKey}`,
    actor,
    outcome: "SUCCESS",
    severity: "INFO",
    metadata: { role, permissionKey },
    beforeState: { enabled: previousEnabled },
    afterState: { enabled: Boolean(enabled) },
  });
  return saved;'''
    text = replace_once(text, role_audit_anchor, role_audit_insert, "role permission v2 audit")

    text = replace_once(
        text,
        'export async function createUserPermissionOverride({ actor, userId, permissionKey, effect = "ALLOW", scopeType = "GLOBAL", scopeId = null, startsAt = null, expiresAt = null, reason = null }) {',
        'export async function createUserPermissionOverride({ req = null, actor, userId, permissionKey, effect = "ALLOW", scopeType = "GLOBAL", scopeId = null, startsAt = null, expiresAt = null, reason = null }) {',
        "create override signature",
    )
    create_audit_anchor = r'''  await auditPermissionChange({
    action: "USER_PERMISSION_OVERRIDE_CREATED",
    actorId: actor.id,
    targetUserId: userId,
    permissionKey,
    metadata: { effect: normalizedEffect, ...scope, startsAt: startDate, expiresAt: expiryDate, reason: normalizedReason, actorRole: actor.role },
  });
  await notifyUser({'''
    create_audit_insert = r'''  await auditPermissionChange({
    action: "USER_PERMISSION_OVERRIDE_CREATED",
    actorId: actor.id,
    targetUserId: userId,
    permissionKey,
    metadata: { effect: normalizedEffect, ...scope, startsAt: startDate, expiresAt: expiryDate, reason: normalizedReason, actorRole: actor.role },
  });
  await writeAuditEvent({
    req,
    action: "PERMISSION.USER_OVERRIDE_CREATED",
    category: "SECURITY",
    entityType: "UserPermissionOverride",
    entityId: saved.id,
    actor,
    outcome: "SUCCESS",
    severity: normalizedEffect === "DENY" ? "WARN" : "INFO",
    metadata: { userId, permissionKey, reason: normalizedReason },
    afterState: {
      effect: normalizedEffect,
      scopeType: scope.scopeType,
      scopeId: scope.scopeId,
      startsAt: startDate,
      expiresAt: expiryDate,
    },
  });
  await notifyUser({'''
    text = replace_once(text, create_audit_anchor, create_audit_insert, "create override v2 audit")

    text = replace_once(
        text,
        'export async function updateUserPermissionOverride({ actor, overrideId, permissionKey, effect = "ALLOW", scopeType = "GLOBAL", scopeId = null, startsAt = null, expiresAt = null, reason = null }) {',
        'export async function updateUserPermissionOverride({ req = null, actor, overrideId, permissionKey, effect = "ALLOW", scopeType = "GLOBAL", scopeId = null, startsAt = null, expiresAt = null, reason = null }) {',
        "update override signature",
    )
    update_audit_anchor = r'''  await auditPermissionChange({
    action: "USER_PERMISSION_OVERRIDE_UPDATED",
    actorId: actor.id,
    targetUserId: existing.userId,
    permissionKey,
    metadata: {
      overrideId,
      previousPermissionKey: existing.permission?.key,
      effect: normalizedEffect,
      ...scope,
      startsAt: startDate,
      expiresAt: expiryDate,
      reason: normalizedReason,
      actorRole: actor.role,
    },
  });
  await notifyUser({'''
    update_audit_insert = r'''  await auditPermissionChange({
    action: "USER_PERMISSION_OVERRIDE_UPDATED",
    actorId: actor.id,
    targetUserId: existing.userId,
    permissionKey,
    metadata: {
      overrideId,
      previousPermissionKey: existing.permission?.key,
      effect: normalizedEffect,
      ...scope,
      startsAt: startDate,
      expiresAt: expiryDate,
      reason: normalizedReason,
      actorRole: actor.role,
    },
  });
  await writeAuditEvent({
    req,
    action: "PERMISSION.USER_OVERRIDE_UPDATED",
    category: "SECURITY",
    entityType: "UserPermissionOverride",
    entityId: overrideId,
    actor,
    outcome: "SUCCESS",
    severity: normalizedEffect === "DENY" ? "WARN" : "INFO",
    metadata: { userId: existing.userId, permissionKey, previousPermissionKey: existing.permission?.key, reason: normalizedReason },
    beforeState: {
      effect: existing.effect,
      scopeType: existing.scopeType,
      scopeId: existing.scopeId,
      startsAt: existing.startsAt,
      expiresAt: existing.expiresAt,
      reason: existing.reason,
    },
    afterState: {
      effect: normalizedEffect,
      scopeType: scope.scopeType,
      scopeId: scope.scopeId,
      startsAt: startDate,
      expiresAt: expiryDate,
      reason: normalizedReason,
    },
  });
  await notifyUser({'''
    text = replace_once(text, update_audit_anchor, update_audit_insert, "update override v2 audit")

    text = replace_once(
        text,
        "export async function deleteUserPermissionOverride({ actor, overrideId }) {",
        "export async function deleteUserPermissionOverride({ req = null, actor, overrideId }) {",
        "delete override signature",
    )
    delete_audit_anchor = r'''  await prisma.userPermissionOverride.delete({ where: { id: overrideId } });
  await auditPermissionChange({ action: "USER_PERMISSION_OVERRIDE_DELETED", actorId: actor.id, targetUserId: existing.userId, permissionKey: existing.permission.key, metadata: { overrideId, actorRole: actor.role } });
  await notifyUser({'''
    delete_audit_insert = r'''  await prisma.userPermissionOverride.delete({ where: { id: overrideId } });
  await auditPermissionChange({ action: "USER_PERMISSION_OVERRIDE_DELETED", actorId: actor.id, targetUserId: existing.userId, permissionKey: existing.permission.key, metadata: { overrideId, actorRole: actor.role } });
  await writeAuditEvent({
    req,
    action: "PERMISSION.USER_OVERRIDE_DELETED",
    category: "SECURITY",
    entityType: "UserPermissionOverride",
    entityId: overrideId,
    actor,
    outcome: "SUCCESS",
    severity: "WARN",
    metadata: { userId: existing.userId, permissionKey: existing.permission?.key },
    beforeState: {
      effect: existing.effect,
      scopeType: existing.scopeType,
      scopeId: existing.scopeId,
      startsAt: existing.startsAt,
      expiresAt: existing.expiresAt,
      reason: existing.reason,
    },
    afterState: null,
  });
  await notifyUser({'''
    text = replace_once(text, delete_audit_anchor, delete_audit_insert, "delete override v2 audit")
    return text


def main():
    script_dir = Path(__file__).resolve().parent
    payload_dir = script_dir / "payload"
    repo = Path(git(Path.cwd(), "rev-parse", "--show-toplevel"))

    print(f"PATCH={PATCH_NAME}")
    print(f"REPO={repo}")
    require(git(repo, "rev-parse", "HEAD") == EXPECTED_HEAD, f"HEAD must equal {EXPECTED_HEAD}")

    for rel, expected in {**MODIFIED_BLOBS, **FOUNDATION_BLOBS}.items():
        require((repo / rel).is_file(), f"missing source: {rel}")
        actual = git(repo, "hash-object", rel)
        require(actual == expected, f"blob mismatch for {rel}: expected {expected}, got {actual}")
        require(not git(repo, "status", "--porcelain", "--", rel), f"dirty guarded source: {rel}")

    for rel in NEW_FILES:
        require(not (repo / rel).exists(), f"Phase 2 path already exists: {rel}")
    for payload in NEW_FILES.values():
        require((payload_dir / payload).is_file(), f"missing payload: {payload}")

    with tempfile.TemporaryDirectory(prefix="tos-audit-v2-phase2-") as tmp_name:
        tmp = Path(tmp_name)
        run(["git", "init", "-q"], tmp)
        run(["git", "config", "user.email", "audit-v2-generator@tamiyouz.local"], tmp)
        run(["git", "config", "user.name", "TOS Audit V2 Generator"], tmp)

        baseline_files = [*MODIFIED_BLOBS, "backend/package.json"]
        for rel in baseline_files:
            target = tmp / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(repo / rel, target)
        run(["git", "add", "--", *baseline_files], tmp)
        run(["git", "commit", "-q", "-m", "baseline"], tmp)

        auth_path = tmp / "backend/src/routes/auth.routes.js"
        users_path = tmp / "backend/src/routes/users.routes.js"
        permission_routes_path = tmp / "backend/src/routes/permissions.routes.js"
        permission_service_path = tmp / "backend/src/services/permissions.service.js"

        write_text(auth_path, patch_auth(auth_path.read_text(encoding="utf-8")))
        write_text(users_path, patch_users(users_path.read_text(encoding="utf-8")))
        write_text(permission_routes_path, patch_permissions_routes(permission_routes_path.read_text(encoding="utf-8")))
        write_text(permission_service_path, patch_permissions_service(permission_service_path.read_text(encoding="utf-8")))

        for rel, payload in NEW_FILES.items():
            write_text(tmp / rel, (payload_dir / payload).read_text(encoding="utf-8"))

        for rel in [*MODIFIED_BLOBS, *NEW_FILES]:
            run(["node", "--check", rel], tmp, capture=False)

        run(
            ["node", "--test", "src/services/auditV2.phase2.security.test.js"],
            tmp / "backend",
            capture=False,
        )

        run(["git", "add", "--intent-to-add", "--", *NEW_FILES], tmp)
        validate_patch_paths(tmp)

        diff = run(
            ["git", "diff", "--binary", "--full-index", "--no-renames", "HEAD", "--", *PATCH_PATHS],
            tmp,
        ).stdout
        require(diff.strip(), "generated patch is empty")
        for rel in PATCH_PATHS:
            require(f"diff --git a/{rel} b/{rel}" in diff, f"generated patch missing diff header for {rel}")

        for protected in FOUNDATION_BLOBS:
            require(f"diff --git a/{protected} b/{protected}" not in diff, f"protected Phase 1 path leaked into patch: {protected}")

        output = script_dir / OUTPUT_NAME
        output.write_text(diff, encoding="utf-8", newline="\n")

        apply_check = run(["git", "apply", "--check", str(output)], repo, check=False)
        if apply_check.returncode != 0:
            sys.stderr.write(apply_check.stdout or "")
            sys.stderr.write(apply_check.stderr or "")
            raise RuntimeError("git apply --check failed")

        print("PHASE_2_STATIC_TESTS=PASS")
        print("PATCH_FILES_VALIDATED=PASS")
        print(f"PATCH_FILE_COUNT={len(PATCH_PATHS)}")
        print(f"PATCH_NEW_FILE_COUNT={len(NEW_FILES)}")
        print("AUTH_LOGIN_SUCCESS_EVENT=PASS")
        print("AUTH_LOGIN_FAILURE_EVENT=PASS")
        print("AUTH_LOGOUT_EVENT=PASS")
        print("USER_SECURITY_EVENTS=PASS")
        print("ROLE_SECURITY_EVENTS=PASS")
        print("PERMISSION_SECURITY_EVENTS=PASS")
        print("PHASE_1_FOUNDATION_PRESERVED=YES")
        print("LEGACY_AUDIT_ROUTE_CHANGED=NO")
        print("PRISMA_SCHEMA_CHANGED=NO")
        print("GIT_APPLY_CHECK=PASS")
        print(f"PATCH_FILE={output}")
        print(f"PATCH_SHA256={hashlib.sha256(output.read_bytes()).hexdigest()}")
        print("PHASE_2_SECURITY_EVENTS_READY=YES")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("PASS/FAIL=FAIL")
        print(f"ERROR={exc}")
        sys.exit(1)
