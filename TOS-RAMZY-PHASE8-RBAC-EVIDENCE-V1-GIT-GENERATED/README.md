# TOS — Ramzy Phase 8: RBAC & Evidence

Baseline TOS HEAD:

`db3d6a21184bb670d5252771c3ef3a5059ecca52`

## Purpose

Phase 8 hardens Ramzy authorization and makes the source of each answer auditable without exposing database IDs or raw records.

## Main changes

- Server-side preflight for tool-supplied `projectId` / `workspaceId` before the tool handler runs.
- Explicit project lookup now respects Ramzy `allowedWorkspaceIds`.
- Person lookup is constrained to the current user's authorized project/workspace surface instead of querying every active user.
- New `RAMZY_EVIDENCE_V1` manifest built from successful tool executions and System Intelligence.
- Evidence stores source labels, live-vs-knowledge classification and scope type only; it does not expose raw tool records or database identifiers.
- Ramzy messages show a compact `Evidence & access / الأدلة ونطاق الصلاحية` disclosure.
- Approval cards no longer print the internal task database ID.
- Existing task action approval and execution permission rechecks remain unchanged and authoritative.

## TOS files changed

Exactly 8 files:

- `backend/src/agency-operator/policies/agentPolicy.service.js`
- `backend/src/agency-operator/prompts/ramzyPrompt.js`
- `backend/src/agency-operator/services/ramzyEvidence.service.js` (new)
- `backend/src/agency-operator/services/ramzyRuntime.service.js`
- `backend/src/agency-operator/services/ramzySystemIntelligence.service.js`
- `backend/src/agency-operator/tests/ramzyRbacEvidence.static.test.js` (new)
- `backend/src/agency-operator/tools/createRamzyTools.js`
- `frontend/src/components/RamzyAssistant.jsx`

No Prisma/schema/migration/package changes and no Performance Score or permission-default changes.

## Run

```bash
cd /var/www/TOS-Patchs
git pull --ff-only origin main
cd TOS-RAMZY-PHASE8-RBAC-EVIDENCE-V1-GIT-GENERATED
bash run_phase8_ramzy_rbac_evidence_v1.sh
```

The runner requires the exact clean baseline, applies the generator, validates the exact eight-file output including untracked files, runs Ramzy tests and frontend build, deploys the existing frontend, reloads the existing backend and performs smoke checks.

Do not commit or push TOS from OpenHands. The owner pushes manually after review.
