# TOS Ramzy Phase 13 — Safe Confirmation & Action Control V1

Baseline: `f8d892f2b596cf4f09863cfac7545aa279a7a6e7`

## Goal

Add a server-owned safety layer between Ramzy task-action understanding and execution.

Flow:

`Voice/Text -> Intent -> Identity/Project Resolution -> RBAC -> Risk Policy -> Draft/Revision -> Confirmation -> Server-side Reauthorization -> Execute`

Voice remains transport only and never owns permissions.

## Risk policy

- `CREATE_TASK` — HIGH — explicit confirmation always required.
- `CHANGE_ASSIGNEE` — HIGH — explicit confirmation always required.
- `CHANGE_DUE_DATE` — MEDIUM — explicit confirmation always required.
- `ADD_CHECKLIST` — MEDIUM — explicit confirmation always required.
- `ADD_COMMENT` — LOW — confirmation by default; server may opt in to direct execution with `RAMZY_LOW_RISK_DIRECT_ACTIONS=true`.

The low-risk direct flag is disabled by default. It cannot widen HIGH/MEDIUM actions. Even a direct LOW action is reauthorized on the server and leaves an approval/audit record.

## Revise draft

Pending approval drafts can be revised without execution.

Supported revision fields:
- CREATE_TASK: title, description, priority, dueDate.
- CHANGE_DUE_DATE: dueDate.
- ADD_CHECKLIST: title.
- ADD_COMMENT: body.

Project and assignee IDs cannot be changed through generic revision. Changing the assignee requires a new user request so Phase 10 identity resolution and RBAC run again.

Revision is available from the Approval Card and through Ramzy's `revise_task_action_proposal` tool for the latest pending draft in the current conversation.

## UI

Approval cards show:
- action summary;
- risk/impact level;
- confirmation mode;
- revision count;
- Confirm & Execute / Revise Draft / Reject controls when applicable.

No internal database ID is intentionally rendered.

## Expected TOS files

Modified:
- `backend/src/agency-operator/services/taskCommands.service.js`
- `backend/src/agency-operator/tools/createRamzyTools.js`
- `backend/src/agency-operator/services/ramzyRuntime.service.js`
- `backend/src/routes/agent.routes.js`
- `backend/src/agency-operator/prompts/ramzyPrompt.js`
- `frontend/src/lib/api.js`
- `frontend/src/components/RamzyAssistant.jsx`

New:
- `backend/src/agency-operator/services/actionConfirmation.service.js`
- `backend/src/agency-operator/tests/ramzyActionConfirmationPhase13.static.test.js`
- `frontend/src/components/ramzyActionControlPhase13.css`

No Prisma schema, migration, or package change is intended.

## Run

```bash
cd /var/www/TOS-Patchs
git pull --ff-only origin main
cd TOS-RAMZY-PHASE13-SAFE-CONFIRMATION-ACTION-CONTROL-V1-GIT-GENERATED
bash run_phase13_safe_confirmation_action_control_v1.sh
```

The runner never commits/pushes TOS and never resets/cleans `/var/www/TOS`.
