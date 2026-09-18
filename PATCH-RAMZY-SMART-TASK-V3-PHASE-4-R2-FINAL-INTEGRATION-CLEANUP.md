# PATCH-RAMZY-SMART-TASK-V3-PHASE-4-R2-FINAL-INTEGRATION-CLEANUP

Baseline: c7aa93b303bce00a2d0087ac6c440f61710f3ab9

Fix only:

Backend:
- import canActorAssignTargetUser from services/projectAccessScope.service.js (correct module)
- reuse existing top-level prisma; no local prisma import
- candidates = active project members + active SUPER_ADMIN, dedupe by id
- filter each with canActorAssignTargetUser(req.user,target,prisma)
- do not swallow unexpected errors
- keep assertRamzyActionExecutionAllowed + assertAgentTaskCreateAccess

Frontend:
- remove all smartTaskOptions.users refs/shape
- render options from smartTaskAssignees
- add assignee loading + visible error state
- no project => disabled placeholder
- endpoint error must not affect project picker
- keep AUTO/NONE and exact assigneeId

Do not change RBAC, taskCommands, approval, Phase5+.

Build/test/deploy/commit/push.
