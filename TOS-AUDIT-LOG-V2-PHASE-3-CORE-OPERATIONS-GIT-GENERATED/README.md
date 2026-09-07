# TOS Audit Log V2 — Phase 3 Core Operations

Required TOS HEAD: `5c157f20bbc71696a18bced97319cf8eb216f24f`

Run `run_phase3.py` from the existing TOS repository root. The runner downloads and verifies its payloads, generates an exact Git patch in a temporary directory, applies it to the server checkout, runs Prisma validation/generation, syntax checks, Phase 1/2/3 tests, and stops without committing or pushing.

Phase 3 covers:
- Projects
- Tasks and task board/list/workflow operations
- Design Queue (`/api/tasks/reports/design-queue`)
- Integrations, including Trello classification when present

Phase 4-sensitive scope is intentionally excluded here: DELETE, restore, chat, comments, files/attachments, download/export, and integration credentials/settings.

Expected TOS changes: exactly 3 paths:
- `backend/src/app.js`
- `backend/src/middleware/auditV2CoreOperations.js` (new)
- `backend/src/middleware/auditV2CoreOperations.test.js` (new)

No Prisma schema change. No migration. Existing Audit Center route remains untouched. All V2 writes go through the centralized `writeAuditEvent` writer.
