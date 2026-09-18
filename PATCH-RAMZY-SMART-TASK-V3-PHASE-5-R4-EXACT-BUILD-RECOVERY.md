# PATCH-RAMZY-SMART-TASK-V3-PHASE-5-R4-EXACT-BUILD-RECOVERY

Current local HEAD: ebcbdd9
Current worktree: dirty with Phase 5 R2 + R3 changes

Do NOT reset, checkout, stash, or discard the current worktree.

## Goal
Get the current Phase 5 worktree to a clean build, finish the missing workload recommendation, then create ONE new commit.

## 1) Exact syntax recovery
Run the frontend build and use the exact compiler file/line/column.

In frontend/src/components/RamzyAssistant.jsx:
- inspect the failing scope around the duplicate identifier / malformed block
- remove only the duplicate/conflicting declaration(s) or unmatched syntax causing the compiler error
- do not rewrite unrelated Smart Task code
- rerun build after each fix until PASS

Do not report success until frontend build actually passes.

## 2) Finish workload recommendation after build is fixed
Existing GET /api/agent/task-create/assignees must return:
recommendedAssigneeId: string|null

Rules:
- candidate must already exist in the authorized returned users list
- query only open, non-archived tasks for the selected project
- scope tasks through existing task visibility authorization for req.user
- count both legacy assigneeId and assignees relation
- dedupe same task/person
- deterministic score uses active + urgent + overdue
- only recommend when one candidate is strictly lower than all others
- tie/no meaningful difference => null
- do not expose workload/task internals

Frontend:
- separate recommendation state
- clear on project change/load
- resolve ID only against returned authorized assignees
- compact clickable suggestion
- click selects exact user
- never auto-select

## Preserve
Current dirty-worktree R2/R3 changes:
- real suggest-description endpoint
- no template/static fallback
- provider failure non-2xx
- current description preserved on failure
- CUSTOM due date
- URGENT
- Phase 1-4 RBAC
- approval/submit flow
- no Phase 6/7

## Workflow
Continue from current dirty worktree.
Frontend build PASS.
Run relevant backend syntax/tests.
Create ONE new commit.
COMMIT ONLY. DO NOT PUSH.

## Return only
PATCH=RAMZY-SMART-TASK-V3-PHASE-5-R4-EXACT-BUILD-RECOVERY
PASS/FAIL=
NEW_COMMIT=
EXACT_BUILD_ERROR_FIXED=
FRONTEND_BUILD=
WORKLOAD_RECOMMENDATION_IMPLEMENTED=
VISIBLE_TASK_SCOPE_REUSED=
ACTIVE_URGENT_OVERDUE_SCORE=
AUTHORIZED_ONLY=
TIE_RETURNS_NULL=
AUTO_ASSIGNS=NO
AI_NO_TEMPLATE_FALLBACK=
BACKEND_TEST=
WORKTREE_CLEAN=
ERROR=
