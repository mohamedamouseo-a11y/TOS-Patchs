# TOS Ramzy Phase 15 — Multi-Step Voice Operations V1

Baseline: `ccda1f7e378c1ef8d1045a55aaca3b6376ce6369`

## Goal
Allow one typed or speech-to-text request to propose 2–5 linked task side effects under one explicit confirmation, while executing every child step through the existing TOS task-action service and current server-side RBAC.

## Safety model
- Voice is transport only; no independent voice permission or execution path.
- Composite operations always require explicit confirmation, even when all child steps are low risk.
- Every child action is reauthorized at approval time and again by the existing task action service at execution time.
- One operation may contain at most one CREATE_TASK step.
- Dependent steps may reference only the task created earlier in the same plan via `useCreatedTask=true`.
- Execution is sequential with no fake rollback. Results distinguish `SUCCESS`, `PARTIAL_SUCCESS`, and `FAILED`.
- If task creation fails, dependent `CREATED_TASK` steps are `SKIPPED`; independent later steps may continue.
- UI renders public step summaries and sanitized per-step results, not internal target IDs.
- No Prisma/schema/package changes.

## Run
```bash
cd /var/www/TOS-Patchs
git pull --ff-only origin main
cd TOS-RAMZY-PHASE15-MULTI-STEP-VOICE-OPERATIONS-V1-GIT-GENERATED
bash run_phase15_multi_step_voice_operations_v1.sh
```

Do not commit, push, reset, or clean `/var/www/TOS` from the runner workflow.
