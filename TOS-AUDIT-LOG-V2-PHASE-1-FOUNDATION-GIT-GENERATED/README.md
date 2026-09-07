# TOS Audit Log V2 — Phase 1 Foundation

Deterministic additive patch for TOS base commit:

`f6b6f60b57d702e62ed488eca7265bfcde0ca601`

## Scope

Phase 1 only:

- Add `AuditEventV2` Prisma model and PostgreSQL migration.
- Add centralized fail-open `writeAuditEvent()` service.
- Add request correlation context: request ID, IP, user agent, HTTP method, and path-only route.
- Add actor snapshots from `req.user` without a hard foreign key to `User`.
- Add recursive redaction for passwords, tokens, cookies, authorization, API keys, secrets, CSRF/XSRF, OTP/session/credentials/private keys, plus bearer/JWT-like free-text scrubbing.
- Add pure Node tests for redaction, request context, and audit event construction.
- Preserve the existing `/api/audit-log` route and all legacy audit/activity tables unchanged.

## Important compatibility rule

Phase 1 is write-foundation only. It does **not** replace or rewire the current Audit Center. Security/business event wiring begins in Phase 2 and later phases.

## Generate

Run the generator while your current directory is the TOS repository root:

```bash
python3 /path/to/TOS-Patchs/TOS-AUDIT-LOG-V2-PHASE-1-FOUNDATION-GIT-GENERATED/generate_tos_audit_log_v2_phase1_foundation.py
```

The generator refuses to run unless HEAD and guarded source blobs match the exact reviewed base. It runs the pure Node tests and `git apply --check`, then writes:

`tos-audit-log-v2-phase1-foundation.patch`

next to the generator.

## Apply and verify

Follow `OPENHANDS.md` exactly. Never use `prisma migrate reset`.
