# TOS Ramzy Phase 16 — Admin Settings Auth Boundary Acceptance V3

Validation-only corrective acceptance. It makes **no TOS source changes**.

It verifies:
- Ramzy settings source access is `ADMIN + SUPER_ADMIN`.
- Ramzy full audit remains `SUPER_ADMIN` only.
- Global CSRF intentionally returns `403` for unauthenticated unsafe PATCH without a CSRF pair.
- With a valid double-submit CSRF cookie/header but no login, the same PATCH reaches agent auth and returns `401`.
- Public and loopback boundaries agree.
- Existing local Phase 16 work and worktree diff remain byte-for-byte unchanged during this run.

Run only:

```bash
bash run_phase16_admin_settings_auth_boundary_acceptance_v3.sh
```

Do not commit, push, reset, clean, or manually edit `/var/www/TOS` during this validation.
