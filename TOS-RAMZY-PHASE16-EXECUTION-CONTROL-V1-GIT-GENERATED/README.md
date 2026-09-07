# TOS Ramzy Phase 16 — Execution Control V1

Baseline: `f6b6f60b57d702e62ed488eca7265bfcde0ca601`

Purpose: replace the legacy global `Read-only` operating mode with a professional layered execution-control model so Ramzy can execute approved task actions for authorized users without bypassing normal TOS RBAC.

## Control model

1. `ramzy.execute_actions` is a dynamic permission managed from the existing Permissions dashboard.
2. Default execution roles: `SUPER_ADMIN` and `ADMIN`.
3. `MANAGER`, `PROJECT_MANAGER`, and `TEAM_MEMBER` default to disabled and can only be enabled through the normal role-permission matrix.
4. `readOnlyMode` becomes the system-wide emergency execution lock. Only `SUPER_ADMIN` can change it; ADMIN can still manage normal Ramzy settings.
5. `approvalActionsEnabled` remains the operational feature switch.
6. Every approved action is still rechecked through existing project/task/assignment RBAC at execution time.
7. Voice adds no permission and uses the exact same execution path.

## One-time transition performed by runner

The runner syncs the existing permission catalog, creates `ramzy.execute_actions`, enables it for ADMIN by default, and converts the legacy current state to normal execution mode by setting:

- emergency lock (`readOnlyMode`) = OFF
- approval actions = ON

This is intentional so existing ADMIN accounts can execute after approval immediately. Other roles remain blocked by `ramzy.execute_actions` unless explicitly enabled from the Permissions dashboard.

No Prisma schema or package changes are required.

## Run

```bash
cd /var/www/TOS-Patchs
git pull --ff-only origin main
cd TOS-RAMZY-PHASE16-EXECUTION-CONTROL-V1-GIT-GENERATED
bash run_phase16_ramzy_execution_control_v1.sh
```

The runner builds/deploys frontend, reloads the existing backend PM2 process, syncs the permission catalog, validates ADMIN execution state, runs Ramzy tests, smoke tests, and auth/CSRF boundaries. It does not commit or push `/var/www/TOS`.
