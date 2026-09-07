# TOS Ramzy Phase 16 — Execution Control DB Env Repair V1

Purpose: finish the already-applied `RAMZY_EXECUTION_CONTROL_V1` rollout after the original runner stopped because Prisma was launched from a shell without the production database environment.

This repair does **not** modify TOS source files. It:

- verifies the existing execution-control source contracts,
- runs the focused execution-control tests,
- resolves the production DB environment from the backend working directory first and PM2 runtime environment as fallback,
- syncs the dynamic permission catalog,
- enables `ramzy.execute_actions` for the ADMIN role for the initial rollout,
- transitions the legacy global read-only state to Emergency Lock OFF and approval actions ON,
- verifies an ACTIVE ADMIN can execute after approval according to the new control,
- rebuilds/deploys the frontend and reloads the existing backend process because the original V1 stopped before deploy,
- preserves normal TOS RBAC and the Phase 16 voice/security boundaries,
- performs no commit or push.

Run:

```bash
cd /var/www/TOS-Patchs
git pull --ff-only origin main
cd TOS-RAMZY-PHASE16-EXECUTION-CONTROL-DB-ENV-REPAIR-V1-GIT-GENERATED
bash run_phase16_execution_control_db_env_repair_v1.sh
```
