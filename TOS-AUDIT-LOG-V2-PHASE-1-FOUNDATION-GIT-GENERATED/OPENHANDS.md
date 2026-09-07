# OpenHands execution — TOS Audit Log V2 Phase 1 (R1 generator fix)

Work on the existing TOS checkout. Do not redesign or expand scope. Do not change the legacy Audit Center route.

## 0. Recover from the known partial apply (only if present)

The previous generator could produce a patch containing only:

- `backend/prisma/schema.prisma`
- `backend/src/app.js`

If that partial patch was applied, inspect first:

```bash
git rev-parse --show-toplevel
git rev-parse HEAD
git status --short
git diff -- backend/prisma/schema.prisma backend/src/app.js
```

Required HEAD:

`f6b6f60b57d702e62ed488eca7265bfcde0ca601`

If HEAD differs, STOP and report it.

If the only Phase 1 changes currently present are the known partial edits in those two guarded files, restore only those two files to HEAD:

```bash
git restore --source=HEAD -- backend/prisma/schema.prisma backend/src/app.js
```

Do not use `git reset --hard`, `git clean`, or restore unrelated files.

Confirm the Phase 1 guarded paths are clean/absent:

```bash
git status --short -- \
  backend/prisma/schema.prisma \
  backend/src/app.js \
  backend/src/utils/auditRedaction.js \
  backend/src/utils/auditRedaction.test.js \
  backend/src/middleware/requestContext.js \
  backend/src/middleware/requestContext.test.js \
  backend/src/services/auditV2.core.js \
  backend/src/services/auditV2.core.test.js \
  backend/src/services/auditV2.service.js \
  backend/prisma/migrations/20260907194000_audit_log_v2_foundation/migration.sql
```

If any unrelated edits exist in the two guarded files, STOP instead of restoring them.

## 1. Generate the corrected patch

From the TOS repo root, run:

```bash
python3 /path/to/TOS-Patchs/TOS-AUDIT-LOG-V2-PHASE-1-FOUNDATION-GIT-GENERATED/generate_tos_audit_log_v2_phase1_foundation.py
```

Require all markers:

```text
PURE_NODE_TESTS=PASS
PATCH_FILES_VALIDATED=PASS
PATCH_FILE_COUNT=10
PATCH_NEW_FILE_COUNT=8
GIT_APPLY_CHECK=PASS
LEGACY_AUDIT_ROUTE_CHANGED=NO
PHASE_1_FOUNDATION_READY=YES
```

If any marker is missing, STOP.

Before applying, independently inspect the patch file list:

```bash
grep '^diff --git ' /path/to/TOS-Patchs/TOS-AUDIT-LOG-V2-PHASE-1-FOUNDATION-GIT-GENERATED/tos-audit-log-v2-phase1-foundation.patch
```

It must contain exactly these 10 paths:

```text
backend/prisma/schema.prisma
backend/src/app.js
backend/prisma/migrations/20260907194000_audit_log_v2_foundation/migration.sql
backend/src/utils/auditRedaction.js
backend/src/utils/auditRedaction.test.js
backend/src/middleware/requestContext.js
backend/src/middleware/requestContext.test.js
backend/src/services/auditV2.core.js
backend/src/services/auditV2.core.test.js
backend/src/services/auditV2.service.js
```

## 2. Apply

```bash
git apply --check /path/to/TOS-Patchs/TOS-AUDIT-LOG-V2-PHASE-1-FOUNDATION-GIT-GENERATED/tos-audit-log-v2-phase1-foundation.patch
git apply /path/to/TOS-Patchs/TOS-AUDIT-LOG-V2-PHASE-1-FOUNDATION-GIT-GENERATED/tos-audit-log-v2-phase1-foundation.patch
git diff --check
```

Confirm all new files exist before any Prisma deploy:

```bash
test -f backend/src/utils/auditRedaction.js
test -f backend/src/utils/auditRedaction.test.js
test -f backend/src/middleware/requestContext.js
test -f backend/src/middleware/requestContext.test.js
test -f backend/src/services/auditV2.core.js
test -f backend/src/services/auditV2.core.test.js
test -f backend/src/services/auditV2.service.js
test -f backend/prisma/migrations/20260907194000_audit_log_v2_foundation/migration.sql
```

## 3. Verify source and Prisma before touching the DB

```bash
cd backend
npm run prisma:validate
npm run prisma:generate
node --test src/utils/auditRedaction.test.js src/middleware/requestContext.test.js src/services/auditV2.core.test.js
node --check src/services/auditV2.service.js
node -e 'import("./src/prisma.js").then(({prisma}) => { if (!prisma.auditEventV2) process.exit(2); console.log("AUDIT_V2_PRISMA_DELEGATE=PASS"); })'
```

## 4. Inspect compatibility

Required constraints:

- `backend/src/routes/auditLog.routes.js` has **no diff**.
- No legacy audit/activity model is removed or renamed.
- Migration only adds `AuditEventV2` and indexes.
- Request context strips query strings.
- Audit persistence remains fail-open.

Check:

```bash
cd ..
git diff -- backend/src/routes/auditLog.routes.js
git diff -- \
  backend/prisma/schema.prisma \
  backend/src/app.js \
  backend/src/utils \
  backend/src/middleware/requestContext.js \
  backend/src/services/auditV2.core.js \
  backend/src/services/auditV2.service.js \
  backend/prisma/migrations/20260907194000_audit_log_v2_foundation/migration.sql
```

## 5. Deploy the additive migration only after every check passes

```bash
cd backend
npm run prisma:deploy
```

Never run `prisma migrate reset`, never drop legacy tables, and never delete audit data.

## 6. Final report only

Do not push unless Ahmed explicitly asks OpenHands to push.

Return:

```text
PHASE_1_PATCH_APPLIED=YES/NO
PATCH_FILES_VALIDATED=PASS/FAIL
PATCH_FILE_COUNT=<number>
PATCH_NEW_FILE_COUNT=<number>
PRISMA_VALIDATE=PASS/FAIL
PRISMA_GENERATE=PASS/FAIL
AUDIT_V2_TESTS=PASS/FAIL
AUDIT_V2_PRISMA_DELEGATE=PASS/FAIL
MIGRATION_DEPLOY=PASS/FAIL
LEGACY_AUDIT_ROUTE_CHANGED=NO/YES
LEGACY_TABLES_PRESERVED=YES/NO
REQUEST_ID_CONTEXT=PASS/FAIL
REDACTION_GUARDS=PASS/FAIL
FAIL_OPEN_AUDIT_WRITER=PASS/FAIL
READY_FOR_GIT_PUSH=YES/NO
```
