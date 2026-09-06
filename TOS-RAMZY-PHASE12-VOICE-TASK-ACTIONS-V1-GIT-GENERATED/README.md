# TOS Ramzy Phase 12 — Voice Task Actions V1

Baseline: `f22b0d94271477e2a58aa6d53e560b099c64356c`

## Goal

Allow Ramzy to understand task-action requests coming from typed text or Phase 11 Speech-to-Text through one shared secure action pipeline.

Examples:
- `اعمل تاسك ليوسف في مشروع X`
- `اسند التاسك دي ليوسف`
- `غير موعد التاسك للخميس`
- `ضيف تعليق على التاسك`
- `ضيف checklist`

## Security model

Voice is transport only. It does not own permissions and does not bypass TOS authorization.

Flow:

`Voice/Text -> Semantic Intent -> Identity/Project Resolution -> Server-side RBAC -> Approval Proposal -> User Approval -> Server-side Reauthorization -> Existing TOS Task Services`

Phase 12 adds `CREATE_TASK` to the existing approval-based Ramzy task actions. Existing actions remain:
- `CHANGE_ASSIGNEE`
- `CHANGE_DUE_DATE`
- `ADD_COMMENT`
- `ADD_CHECKLIST`

Creation is never executed directly by Speech-to-Text or the AI provider. A `CREATE_TASK` request produces an Approval Card. The server rechecks project/board/create permissions when the approval is accepted.

## Identity and ambiguity

Phase 10 remains authoritative for multilingual person/project resolution. If a user says `يوسف`, `Youssef`, `Yousef`, etc., Ramzy may proceed only when the shared resolver returns a sufficiently confident authorized identity. Ambiguous matches require clarification.

## Task creation

A new task is created only in an authorized project and its authorized/default TOS board/list. Optional assignee must be ACTIVE, belong to the project, and pass the current actor assignment scope. Approval cards show human-readable project/assignee names and do not expose database IDs.

## Files

- `01_phase12_voice_task_actions.py` — generated source patch.
- `run_phase12_voice_task_actions_v1.sh` — guarded apply/test/build/deploy runner.
- `README.md` — this document.

Expected TOS changes:
- `backend/src/agency-operator/services/semanticIntentResolver.service.js`
- `backend/src/agency-operator/policies/agentAccess.service.js`
- `backend/src/agency-operator/services/actionGroundingValidation.service.js`
- `backend/src/agency-operator/services/ramzySystemIntelligence.service.js`
- `backend/src/agency-operator/services/taskCommands.service.js`
- `backend/src/agency-operator/tools/createRamzyTools.js`
- `backend/src/routes/agent.routes.js`
- `backend/src/agency-operator/prompts/ramzyPrompt.js`
- `frontend/src/components/RamzyAssistant.jsx`
- `backend/src/agency-operator/tests/ramzyVoiceTaskActionsPhase12.static.test.js` (new)

No Prisma schema/migration/package change is intended.

## Run

```bash
cd /var/www/TOS-Patchs

git pull --ff-only origin main
cd TOS-RAMZY-PHASE12-VOICE-TASK-ACTIONS-V1-GIT-GENERATED
bash run_phase12_voice_task_actions_v1.sh
```

The runner does not commit or push TOS and never resets/cleans `/var/www/TOS`.
