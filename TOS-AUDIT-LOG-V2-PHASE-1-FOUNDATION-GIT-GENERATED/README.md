# TOS Audit Log V2 — Phase 1 Foundation (R1)

Deterministic additive patch for TOS base commit:

`f6b6f60b57d702e62ed488eca7265bfcde0ca601`

## R1 generator fix

The original generator wrote the new Phase 1 source files into its temporary repository but did not stage them with intent-to-add before running `git diff`. Git therefore omitted all untracked files from the generated patch.

R1 fixes that defect by:

- running `git add --intent-to-add` for all 8 new files before generating the diff;
- validating that the patch contains exactly 10 expected paths;
- validating that all 8 expected new files are represented as additions;
- requiring every expected `diff --git` header before writing a successful artifact;
- exposing `PATCH_FILES_VALIDATED=PASS`, `PATCH_FILE_COUNT=10`, and `PATCH_NEW_FILE_COUNT=8` markers.

## Scope

Phase 1 only:

- Add `AuditEventV2` Prisma model and PostgreSQL migration.
- Add centralized fail-open `writeAuditEvent()` service.
- Add request correlation context: request ID, IP, user agent, HTTP method, and path-only route.
- Add actor snapshots from `req.user` without a hard foreign key to `User`.
- Add recursive redaction for passwords, tokens, cookies, authorization, API keys, secrets, CSRF/XSRF, OTP/session/credentials/private keys, plus bearer/JWT-like free-text scrubbing.
- Add pure Node tests for redaction, request context, and audit event construction.
- Preserve the existing `/api/audit-log` route and all legacy audit/activity tables unchanged.

## Compatibility rule

Phase 1 is write-foundation only. It does **not** replace or rewire the current Audit Center. Security/business event wiring begins in Phase 2 and later phases.

## Recovery from the previous partial apply

If the old broken patch already modified only `backend/prisma/schema.prisma` and `backend/src/app.js`, follow `OPENHANDS.md` section 0. Restore only those two known Phase 1 edits after inspection. Never use `git reset --hard` or `git clean`.

## Generate and apply

Follow `OPENHANDS.md` exactly. Never use `prisma migrate reset`.
