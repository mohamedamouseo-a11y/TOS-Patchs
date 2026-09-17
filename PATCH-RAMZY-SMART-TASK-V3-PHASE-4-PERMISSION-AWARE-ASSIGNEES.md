# PATCH-RAMZY-SMART-TASK-V3-PHASE-4-PERMISSION-AWARE-ASSIGNEES

Baseline: 04bc1e4183a188446331fc96730b75cdf079e7f1

## Goal
Replace Smart Task's generic /api/users assignee source with a project-scoped, server-authorized assignee list.

## Backend
Add GET /api/agent/task-create/projects/:projectId/assignees.

Use existing authorization only:
- getAgentSettings()
- assertRamzyActionExecutionAllowed(req.user,{settings})
- assertAgentTaskCreateAccess(req.user,projectId,settings.allowedWorkspaceIds,prisma)
- candidate must be ACTIVE and either ProjectMember of project OR active SUPER_ADMIN (same rule as assertAssigneeInProject)
- each candidate must pass canActorAssignTargetUser(req.user,target,prisma)
- do not duplicate role rules

Return minimal:
{ assignees:[{id,name,department,jobTitle,role}] }

## Frontend
- add api.agent.taskCreateAssignees(projectId)
- Smart Task must stop using api.users.list()
- load assignees only after exact project selection
- AUTO and NONE remain
- specific assignee choices come only from new endpoint
- if project changes, clear a specific selected assignee; AUTO/NONE may remain
- if no project selected, assignee control disabled with "اختر المشروع أولاً" / "Select a project first"
- assignee endpoint error must be visible without breaking project picker
- compact selector; show name + department/job title when available

## Do not change
Project/RBAC/workspace/board rules, taskCommands authorization, approval flow, Phase 5+.

## Verify
No api.users.list usage for Smart Task; exact assigneeId retained; build/deploy/commit/push.
