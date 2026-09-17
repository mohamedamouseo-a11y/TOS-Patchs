# PATCH-RAMZY-SMART-TASK-V3-PHASE-4-R1-ACTUAL-INTEGRATION-FIX

Baseline: dd43ef38ee3f669e0adf339c0eb6e0596023f867

## Fix only

### Backend
Current assignee endpoint is NOT project-scoped: buildAssignableInternalUserWhere alone can return users outside the selected project.

Keep:
- getAgentSettings
- assertRamzyActionExecutionAllowed
- assertAgentTaskCreateAccess

Then load candidates only if:
- ACTIVE
- AND (member of selected project OR active SUPER_ADMIN)

For every candidate, reuse:
canActorAssignTargetUser(req.user, candidate, prisma)

Return only candidates that pass.

Do not swallow project-create 403 into HTTP 200; let authorization error propagate.

Return minimal:
{id,name,department,jobTitle,role}

No new role logic.

### Frontend API
Add:
api.agent.taskCreateAssignees(projectId)

### Smart Task
Current code creates smartTaskAssignees but the select still reads smartTaskOptions.users.

Fix:
- remove users from smartTaskOptions shape/usages
- assignee select uses smartTaskAssignees only
- load after exact project selection
- visible loading/error state for assignees
- no project => assignee control disabled + Select project first
- keep AUTO/NONE
- project change clears specific assignee; preserve AUTO/NONE
- endpoint failure must not break project picker
- exact assigneeId preserved

## Do not change
RBAC policy functions, taskCommands authorization, project/workspace/board rules, approval flow, Phase 5+.

Build/test/deploy/commit/push.
