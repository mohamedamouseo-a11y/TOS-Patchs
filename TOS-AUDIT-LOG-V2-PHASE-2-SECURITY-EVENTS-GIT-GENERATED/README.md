# TOS Audit Log V2 — Phase 2 Security Events

Deterministic additive patch for TOS base commit:

`39f71ff9d4db541a86cd102e7091404bcfb89ccf`

## Scope

Phase 2 wires security-sensitive operations into the Phase 1 `AuditEventV2` foundation while preserving the existing legacy audit flow.

Events added:

- `AUTH.LOGIN.SUCCESS`
- `AUTH.LOGIN.FAILURE`
- `AUTH.LOGOUT`
- User lifecycle: invite, resend invite, password-reset request, invite cancel, disable/enable, former employee, restore, permanent delete, user update
- `ROLE.USER_ASSIGNMENT_CHANGED`
- Department manager/deputy role changes
- `ROLE.PERMISSION_CHANGED`
- `PERMISSION.USER_OVERRIDE_CREATED`
- `PERMISSION.USER_OVERRIDE_UPDATED`
- `PERMISSION.USER_OVERRIDE_DELETED`
- `USER.PASSWORD_CHANGED_BY_ADMIN`

## Compatibility / security invariants

- Existing `PermissionAuditLog` writes are preserved: Phase 2 dual-writes, it does not replace legacy audit.
- `backend/src/routes/auditLog.routes.js` is unchanged.
- Prisma schema is unchanged; **no migration is required**.
- Phase 1 request context, redaction, audit core, and fail-open writer are guarded by exact blob SHA and remain unchanged.
- Authentication audit metadata never contains submitted passwords or tokens.
- All V2 persistence goes through the centralized fail-open `writeAuditEvent()` service.

## Patch shape

The generated patch must contain exactly 5 paths:

1. `backend/src/routes/auth.routes.js`
2. `backend/src/routes/users.routes.js`
3. `backend/src/routes/permissions.routes.js`
4. `backend/src/services/permissions.service.js`
5. `backend/src/services/auditV2.phase2.security.test.js`

Follow `OPENHANDS.md` exactly. Do not push until Ahmed explicitly asks.
