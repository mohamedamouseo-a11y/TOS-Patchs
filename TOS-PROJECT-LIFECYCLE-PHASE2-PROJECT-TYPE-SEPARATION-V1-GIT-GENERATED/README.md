# TOS Project Lifecycle — Phase 2 Project Type Separation V1

Target project: `/var/www/TOS` only.

Base main HEAD: `b8f8c3d5c475d73fc97ab1ccf1f41ef95615feb5`.

Patch: `01_apply_phase2_project_type.py`

Changes:
- add `ProjectType` enum: `CLIENT | INTERNAL`
- add `Project.projectType` (default `INTERNAL`)
- backfill canonical CRM-linked projects from `tos_crm_project_deliveries` as `CLIENT`
- CRM-created/updated/status-synced projects self-heal to `CLIENT`
- CRM sync no longer clears `archivedAt/archivedById`; archive remains independent from lifecycle
- preserve existing `Project.type`, status enum, CRM identity/concurrency hardening

Expected after migration from audited baseline:
- TOTAL=96
- CLIENT=66
- INTERNAL=30
- mapping conflicts=0

Apply rules:
1. Verify `/var/www/TOS` HEAD exactly matches base HEAD. If not, STOP; do not pull/reset.
2. Run the supplied patch script; do not rewrite it.
3. Run Prisma format/validate, migrate deploy, generate, relevant backend tests/build, then normal TOS deploy/restart procedure.
4. Verify counts and HTTP health.
5. No git commit/push from OpenHands.
