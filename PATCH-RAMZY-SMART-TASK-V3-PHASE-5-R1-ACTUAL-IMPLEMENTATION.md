# PATCH-RAMZY-SMART-TASK-V3-PHASE-5-R1-ACTUAL-IMPLEMENTATION

Baseline: 92e4f3e48a8947f5b1545051bd508e8602f8c952

The previous Phase 5 report is not acceptable. Reported SHA 0cd3bdc is an old Phase 4 commit, the AI endpoint was only a stub, and workload recommendation was not implemented.

Fix Phase 5 only.

## Required

### AI description
Implement the real endpoint from the Phase 5 spec:
POST /api/agent/task-create/suggest-description

Do NOT use /api/agent/describe-task and do NOT leave a stub.

Requirements:
- auth via current agent router
- assertRamzyActionExecutionAllowed
- assertAgentTaskCreateAccess for exact project
- use current configured provider/model
- NO tools and NO side-effect Ramzy action path
- body: {projectId,title,description?,language}
- return generated plain-text description <= 4000
- frontend loading/error isolated; failure preserves current description and draft

### Workload recommendation
Extend existing /api/agent/task-create/assignees response with:
recommendedAssigneeId

Requirements:
- recommendation must be null or one of returned authorized users
- derive only from open, non-archived tasks visible to requesting actor inside selected project
- reuse existing task visibility logic
- account for legacy assigneeId + assignees relation without double counting a task/person
- deterministic workload score (active + urgent + overdue is acceptable)
- if no meaningful difference/tie => recommendedAssigneeId=null
- frontend shows recommendation row/button and only selects on click
- never auto-assign
- project change clears old recommendation

### Custom due
Verify actual implementation:
- CUSTOM chip
- native date input
- local selected date => 17:00 local => ISO
- invalid date never stored
- other preset hides custom input
- NONE => null

### Urgent
Verify actual implementation:
- URGENT chip
- localized label
- existing AUTO unchanged

## Preserve
Phase 1 parser, project RBAC, Phase 4 assignee authorization, AUTO/NONE, taskCommands authorization, approval flow, current prompt-based submit path, no Phase 6/7.

## Workflow
Inspect actual worktree first.
Build frontend + relevant backend syntax/tests.
COMMIT ONLY. DO NOT PUSH.
The commit SHA MUST be new and descend from current Phase 4 baseline/history; do not report an old existing SHA.

## Return only
PATCH=RAMZY-SMART-TASK-V3-PHASE-5-R1-ACTUAL-IMPLEMENTATION
PASS/FAIL=
PHASE5_R1_NEW_COMMIT=
AI_ENDPOINT_REAL=
AI_NO_TOOLS=
WORKLOAD_RECOMMENDATION_IMPLEMENTED=
RECOMMENDATION_AUTHORIZED_ONLY=
RECOMMENDATION_VISIBLE_SCOPE_ONLY=
RECOMMENDATION_AUTO_ASSIGNS=NO
CUSTOM_DUE_DATE=
URGENT_PRIORITY=
FRONTEND_BUILD=
BACKEND_TEST=
WORKTREE_CLEAN=
ERROR=
