# TOS — Ramzy Phase 7: Understands All TOS

Baseline TOS HEAD:

`256cc2e13f69fd0aa98a840d4ae4b63ebdc8649c`

## Purpose

Phase 7 expands Ramzy from projects/tasks/performance into a TOS-wide navigator and read-only context layer without creating parallel business logic.

The new `get_tos_module_context` tool maps the current TOS surface and reuses existing source-of-truth services for authorized live reads where safe.

## Live source reuse

- Dashboard / Projects / Tasks / My Workspace: existing Ramzy operational/task services.
- Team Performance: existing `getRamzyTeamPerformance` source.
- Central Chat: existing authorized chat context.
- Notification Center: existing normalized current-user feed.
- Employee Work Hub / THRS: existing attendance/work-session/request services.
- SLA: existing SLA inbox/dashboard services and `reports.view` check.
- TWS: existing `workspace.service.listDocuments` access model.
- TGWS: existing `listTgwsDocuments` access model.
- Permissions: current user's effective dynamic permissions only.
- Settings: public/runtime-safe operations settings only.

## Explicit Phase 7 boundaries

The module catalog includes Clients, Design Queue, Files, Audit Log, Integrations, Backups and Meetings, but Phase 7 does not invent a second access/business-logic implementation for sensitive or highly contextual modules.

A `knowledgeOnly=true` result is architectural/module knowledge, not live evidence. Ramzy is instructed to say so instead of inventing data.

Secrets, credentials, passwords, tokens and API keys are scrubbed/excluded.

## TOS files changed

Exactly:

- `backend/src/agency-operator/agents/ramzyAgencyOperator.js`
- `backend/src/agency-operator/agents/specialistAgents.js`
- `backend/src/agency-operator/prompts/ramzyPrompt.js`
- `backend/src/agency-operator/services/ramzyTosKnowledge.service.js` (new)
- `backend/src/agency-operator/tests/ramzyTosKnowledge.static.test.js` (new)
- `backend/src/agency-operator/tools/createRamzyTools.js`

No frontend, Prisma, migration, package, scoring, or permission-default changes.

## Run

```bash
cd /var/www/TOS-Patchs
git pull --ff-only origin main
cd TOS-RAMZY-PHASE7-ALL-TOS-KNOWLEDGE-V1-GIT-GENERATED
bash run_phase7_ramzy_all_tos_knowledge_v1.sh
```

The runner requires the exact clean TOS baseline, runs syntax/import checks and all Ramzy tests, reloads the existing `tamiyouz-backend`, checks `/health`, and validates the exact changed-file set.

OpenHands must not commit or push TOS. The owner pushes manually after review.
