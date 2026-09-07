# OpenHands execution — TOS Audit Log V2 Phase 2 Security Events

Work on the existing TOS checkout. Phase 1 must already be present. Do not redesign the Audit Center and do not expand scope.

## 0. Verify exact base

From the TOS repo root:

```bash
git rev-parse --show-toplevel
git status --short
git rev-parse HEAD
```

Required HEAD:

`39f71ff9d4db541a86cd102e7091404bcfb89ccf`

If HEAD differs, STOP. Do not manually port or bypass the guard.

## 1. Generate

Run from the TOS repo root:

```bash
python3 /path/to/TOS-Patchs/TOS-AUDIT-LOG-V2-PHASE-2-SECURITY-EVENTS-GIT-GENERATED/generate_tos_audit_log_v2_phase2_security_events.py
```

Require every marker:

```text
PHASE_2_STATIC_TESTS=PASS
PATCH_FILES_VALIDATED=PASS
PATCH_FILE_COUNT=5
PATCH_NEW_FILE_COUNT=1
AUTH_LOGIN_SUCCESS_EVENT=PASS
AUTH_LOGIN_FAILURE_EVENT=PASS
AUTH_LOGOUT_EVENT=PASS
USER_SECURITY_EVENTS=PASS
ROLE_SECURITY_EVENTS=PASS
PERMISSION_SECURITY_EVENTS=PASS
PHASE_1_FOUNDATION_PRESERVED=YES
LEGACY_AUDIT_ROUTE_CHANGED=NO
PRISMA_SCHEMA_CHANGED=NO
GIT_APPLY_CHECK=PASS
PHASE_2_SECURITY_EVENTS_READY=YES
```

Independently inspect patch headers:

```bash
grep '^diff --git ' /path/to/TOS-Patchs/TOS-AUDIT-LOG-V2-PHASE-2-SECURITY-EVENTS-GIT-GENERATED/tos-audit-log-v2-phase2-security-events.patch
```

It must contain exactly these 5 paths:

```text
backend/src/routes/auth.routes.js
backend/src/routes/users.routes.js
backend/src/routes/permissions.routes.js
backend/src/services/permissions.service.js
backend/src/services/auditV2.phase2.security.test.js
```

## 2. Apply

```bash
git apply --check /path/to/TOS-Patchs/TOS-AUDIT-LOG-V2-PHASE-2-SECURITY-EVENTS-GIT-GENERATED/tos-audit-log-v2-phase2-security-events.patch
git apply /path/to/TOS-Patchs/TOS-AUDIT-LOG-V2-PHASE-2-SECURITY-EVENTS-GIT-GENERATED/tos-audit-log-v2-phase2-security-events.patch
git diff --check
```

## 3. Validate

```bash
cd backend

npm run prisma:validate
npm run prisma:generate

node --check src/routes/auth.routes.js
node --check src/routes/users.routes.js
node --check src/routes/permissions.routes.js
node --check src/services/permissions.service.js

node --test \
  src/utils/auditRedaction.test.js \
  src/middleware/requestContext.test.js \
  src/services/auditV2.core.test.js \
  src/services/auditV2.phase2.security.test.js

node -e 'import("./src/prisma.js").then(({prisma}) => { if (!prisma.auditEventV2) process.exit(2); console.log("AUDIT_V2_PRISMA_DELEGATE=PASS"); })'

node -e 'import("./src/services/auditV2.service.js").then(async ({writeAuditEvent}) => { const result = await writeAuditEvent({ action: "TEST.FAIL_OPEN" }, { db: { auditEventV2: { create: async () => { throw new Error("expected"); } } }, logger: { error() { throw new Error("logger expected"); } } }); if (result !== null) process.exit(2); console.log("FAIL_OPEN_AUDIT_WRITER=PASS"); })'
```

There is **no Phase 2 migration**. Do not run `prisma migrate reset` and do not create a migration.

## 4. Compatibility inspection

From repo root:

```bash
cd ..

git diff -- backend/src/routes/auditLog.routes.js
git diff -- backend/prisma/schema.prisma
git diff -- \
  backend/src/middleware/requestContext.js \
  backend/src/services/auditV2.core.js \
  backend/src/services/auditV2.service.js \
  backend/src/utils/auditRedaction.js

git diff --name-only
```

Required:

- Audit Center route diff is empty.
- Prisma schema diff is empty.
- All Phase 1 foundation file diffs above are empty.
- Only the 5 expected Phase 2 paths are changed.
- Existing `auditPermissionChange(...)` legacy writes remain present.
- New V2 writes use `writeAuditEvent(...)`, not direct `prisma.auditEventV2.create(...)`.
- Login failure metadata includes reason / attempted email / status code only; never submitted password/token.
- `AUTH.LOGIN.FAILURE` uses `outcome=FAILURE` and `severity=WARN`.
- User/role/permission mutation events preserve request context via `req`.

## 5. No push

Do not push. Return this report:

```text
PHASE_2_PATCH_APPLIED=YES/NO
PATCH_FILES_VALIDATED=PASS/FAIL
PATCH_FILE_COUNT=<number>
PATCH_NEW_FILE_COUNT=<number>
PRISMA_VALIDATE=PASS/FAIL
PRISMA_GENERATE=PASS/FAIL
PHASE_1_TESTS=PASS/FAIL
PHASE_2_TESTS=PASS/FAIL
AUDIT_V2_PRISMA_DELEGATE=PASS/FAIL
AUTH_LOGIN_SUCCESS_EVENT=PASS/FAIL
AUTH_LOGIN_FAILURE_EVENT=PASS/FAIL
AUTH_LOGOUT_EVENT=PASS/FAIL
USER_SECURITY_EVENTS=PASS/FAIL
ROLE_SECURITY_EVENTS=PASS/FAIL
PERMISSION_SECURITY_EVENTS=PASS/FAIL
LEGACY_AUDIT_DUAL_WRITE=PASS/FAIL
LEGACY_AUDIT_ROUTE_CHANGED=NO/YES
PRISMA_SCHEMA_CHANGED=NO/YES
PHASE_1_FOUNDATION_PRESERVED=YES/NO
FAIL_OPEN_AUDIT_WRITER=PASS/FAIL
MIGRATION_REQUIRED=NO/YES
READY_FOR_GIT_PUSH=YES/NO
```

STOP immediately on any failure.
