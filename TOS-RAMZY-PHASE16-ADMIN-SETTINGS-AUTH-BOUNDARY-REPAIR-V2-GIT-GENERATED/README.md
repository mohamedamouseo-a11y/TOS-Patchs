# TOS Ramzy Phase 16 — Admin Settings Auth Boundary Repair V2

Purpose: verify the already-applied ADMIN + SUPER_ADMIN Ramzy settings access repair, then validate backend readiness on loopback port 5006 before checking the public `/api/agent/settings` unauthenticated boundary.

This V2 does **not** modify TOS source. It preserves the current Phase 16 local work and unrelated worktree changes, does not rebuild/deploy frontend, and does not commit or push.

Run:

```bash
cd /var/www/TOS-Patchs
 git pull --ff-only origin main
cd TOS-RAMZY-PHASE16-ADMIN-SETTINGS-AUTH-BOUNDARY-REPAIR-V2-GIT-GENERATED
bash run_phase16_admin_settings_auth_boundary_repair_v2.sh
```

Expected final markers:

- `BACKEND_AGENT_ROUTE_READY=PASS`
- `AUTH_BOUNDARY_E2E=PASS`
- `ADMIN_RAMZY_SETTINGS_ACCESS=PASS`
- `SUPER_ADMIN_AUDIT_ONLY=PRESERVED`
- `PASS/FAIL=PASS`
