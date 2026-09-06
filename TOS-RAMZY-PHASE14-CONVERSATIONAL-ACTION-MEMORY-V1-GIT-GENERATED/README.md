# TOS Ramzy Phase 14 — Conversational Action Memory V1

Baseline: `c177b43a2472adbbdf41e3f55683542dc4cef4c5`

## Goal

Add conversation-scoped multi-turn action drafts without creating a parallel execution path.

Examples:

- `اعمل تاسك ليوسف`
- `اسمها راجع البنر`
- `على مشروع Cuir`
- `خليها بكرة و High`
- `تمام اعملها`

The accumulated draft is conversation-only and expires automatically. It is never treated as authorization.

## Security model

- Draft memory does not grant permission.
- Stored internal target references are untrusted hints only.
- Project/task/assignee access is rechecked when the draft is updated and again when it is materialized.
- Final execution remains Phase 13 approval/RBAC execution.
- HIGH/MEDIUM actions still require explicit confirmation.
- LOW direct execution remains server opt-in only.
- Voice and text share the same path.
- Public/provider-facing draft view contains human-readable names and excludes target IDs.
- Changing project/task clears a stale assignee target.
- Successful conversion to an Approval clears the conversational draft to prevent duplicate proposals.

## Files

New:
- `backend/src/agency-operator/services/ramzyActionDraft.service.js`
- `backend/src/agency-operator/tests/ramzyConversationalActionMemoryPhase14.test.js`

Modified:
- `backend/src/agency-operator/services/contextResolution.service.js`
- `backend/src/agency-operator/services/ramzyMemory.service.js`
- `backend/src/agency-operator/services/ramzySystemIntelligence.service.js`
- `backend/src/agency-operator/tools/createRamzyTools.js`
- `backend/src/agency-operator/services/ramzyRuntime.service.js`
- `backend/src/agency-operator/prompts/ramzyPrompt.js`

No Prisma migration, package change, or frontend source change is part of Phase 14.

## Run

```bash
bash run_phase14_conversational_action_memory_v1.sh
```

The runner does not commit, push, reset, or clean `/var/www/TOS`.
