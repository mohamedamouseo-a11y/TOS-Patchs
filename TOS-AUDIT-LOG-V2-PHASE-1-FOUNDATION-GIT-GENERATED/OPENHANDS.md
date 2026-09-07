# OpenHands execution — TOS Audit Log V2 Phase 1

Work on the existing TOS checkout. Do not redesign or expand scope. Do not change the legacy Audit Center route.

1. Confirm repository and base:

```bash
git rev-parse --show-toplevel
git status --short
git rev-parse HEAD
```

Required HEAD:

`f6b6f60b57d702e62ed488eca7265bfcde0ca601`

If HEAD differs, STOP and report it. Do not bypass the guard and do not manually port the patch.

2. From the TOS repo root, run:

```bash
python3 /path/to/TOS-Patchs/TOS-AUDIT-LOG-V2-PHASE-1-FOUNDATION-GIT-GENERATED/generate_tos_audit_log_v2_phase1_foundation.py
```

Require these markers:

```text
PURE_NODE_TESTS=PASS
GIT_APPLY_CHECK=PASS
LEGACY_AUDIT_ROUTE_CHANGED=NO
PHASE_1_FOUNDATION_READY=YES
```

3. Apply the generated patch:

```bash
git apply --check /path/to/TOS-Patchs/TOS-AUDIT-LOG-V2-PHASE-1-FOUNDATION-GIT-GENERATED/tos-audit-log-v2-phase1-foundation.patch
git apply /path/to/TOS-Patchs/TOS-AUDIT-LOG-V2-PHASE-1-FOUNDATION-GIT-GENERATED/tos-audit-log-v2-phase1-foundation.patch
git diff --check
```

4. Verify source and Prisma before touching the DB:

```bash
cd backend
npm run prisma:validate
npm run prisma:generate
node --test src/utils/auditRedaction.test.js src/middleware/requestContext.test.js src/services/auditV2.core.test.js
node --check src/services/auditV2.service.js
node -e 'import("./src/prisma.js").then(({prisma}) => { if (!prisma.auditEventV2) process.exit(2); console.log("AUDIT_V2_PRISMA_DELEGATE=PASS"); })'
```

5. Inspect the diff. Required constraints:

- `backend/src/routes/auditLog.routes.js` must have **no diff**.
- No legacy audit/activity model may be removed or renamed.
- Migration must only add `AuditEventV2` and its indexes.
- Request context must strip query strings.
- Audit persistence must remain fail-open.

Check:

```bash
cd ..
git diff -- backend/src/routes/auditLog.routes.js
git diff -- backend/prisma/schema.prisma backend/src/app.js backend/src/utils backend/src/middleware/requestContext.js backend/src/services/auditV2.core.js backend/src/services/auditV2.service.js backend/prisma/migrations/20260907194000_audit_log_v2_foundation/migration.sql
```

6. Deploy the additive migration only after all checks pass:

```bash
cd backend
npm run prisma:deploy
```

Never run `prisma migrate reset`, never drop legacy tables, and never delete audit data.

7. Final report only; do not push unless Ahmed explicitly asks OpenHands to push. Return:

```text
PHASE_1_PATCH_APPLIED=YES/NO
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
