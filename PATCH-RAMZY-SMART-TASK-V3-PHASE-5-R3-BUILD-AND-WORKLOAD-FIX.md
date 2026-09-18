# PATCH-RAMZY-SMART-TASK-V3-PHASE-5-R3-BUILD-AND-WORKLOAD-FIX

Current local HEAD: ebcbdd9
Current worktree: uncommitted Phase 5 R2 changes

Do NOT reset/discard the current R2 worktree.
Fix only the current build error and finish the missing workload recommendation.

## 1) Fix frontend syntax/build error
Inspect the exact compiler error in:
frontend/src/components/RamzyAssistant.jsx

Fix the syntax only; preserve current R2 AI error handling, CUSTOM due validation, URGENT, and Smart Task behavior.

Run frontend build until PASS.

## 2) Finish real workload recommendation
Extend existing GET /api/agent/task-create/assignees response:

recommendedAssigneeId: string|null

Rules:
- first use the existing Phase 4 authorized assignable users list
- recommendation candidate MUST be one of returned users
- use only open, non-archived tasks in the selected project
- task data must be scoped to what req.user is allowed to see using the existing task visibility helper/policy
- include both legacy task.assigneeId and task.assignees relation
- dedupe same task/person
- compute deterministic workload using at least:
  active count
  urgent count
  overdue count
- recommend only if one candidate has a strictly lower score than every other candidate
- tie/no meaningful difference => null
- do not expose workload/task details in response

Frontend:
- keep recommendation in separate state
- clear it when project changes/load starts
- resolve recommendedAssigneeId only against smartTaskAssignees
- show compact clickable suggestion
- click selects that exact user
- NEVER auto-select

## 3) Preserve
- R2 real AI endpoint with no template fallback
- AI provider failure remains non-2xx
- current description preserved on AI error
- CUSTOM due date behavior
- URGENT
- Phase 1-4 RBAC
- AUTO/NONE
- approval/submit flow
- no Phase 6/7

## Workflow
Continue from the current dirty worktree.
Do not revert R2.
Build frontend + relevant backend test/syntax.
When all PASS, create ONE new commit containing R2+R3 completed Phase 5 work.
COMMIT ONLY. DO NOT PUSH.

## Return only
PATCH=RAMZY-SMART-TASK-V3-PHASE-5-R3-BUILD-AND-WORKLOAD-FIX
PASS/FAIL=
NEW_COMMIT=
FRONTEND_SYNTAX_FIXED=
FRONTEND_BUILD=
AI_TEMPLATE_FALLBACK_REMOVED=
AI_FAILURE_NON_2XX=
WORKLOAD_RECOMMENDATION_IMPLEMENTED=
VISIBLE_TASK_SCOPE_REUSED=
ACTIVE_URGENT_OVERDUE_SCORE=
RECOMMENDATION_AUTHORIZED_ONLY=
TIE_RETURNS_NULL=
AUTO_ASSIGNS=NO
BACKEND_TEST=
WORKTREE_CLEAN=
ERROR=
