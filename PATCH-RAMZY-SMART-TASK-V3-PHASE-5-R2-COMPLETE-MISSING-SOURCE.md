# PATCH-RAMZY-SMART-TASK-V3-PHASE-5-R2-COMPLETE-MISSING-SOURCE

Local Phase 5 HEAD reported: ebcbdd9
GitHub main baseline: 92e4f3e48a8947f5b1545051bd508e8602f8c952

The previous R1 report still does not satisfy Phase 5. Fix only the missing requirements below.

## 1) Remove fake/template AI fallback
POST /api/agent/task-create/suggest-description must use the currently configured provider/model only.

- NO template/static fallback pretending to be AI.
- If provider/model/config/call fails, return proper non-2xx error.
- Preserve the existing description in frontend on failure.
- No tools, no action proposals, no side effects.
- Keep exact project authorization before generation.

## 2) Implement actual workload recommendation
"Loading project members" is not workload recommendation.

Extend /api/agent/task-create/assignees response with:
recommendedAssigneeId: string|null

Requirements:
- first build the Phase 4 authorized returned users list
- candidate recommendation can ONLY be from that returned list
- load only open, non-archived tasks in the selected project that are visible to req.user using existing task visibility helper/policy
- count assignment from both legacy task.assigneeId and task.assignees, deduping same task/person
- deterministic workload score must at minimum consider active count, urgent count, and overdue count
- recommend only when one authorized candidate has a strictly lower workload than the rest; ties/no meaningful difference => null
- do not expose hidden task data or workload details
- frontend stores recommendation separately from selected assignee
- show compact clickable recommendation using the returned authorized user
- clicking selects exact user; never auto-select
- project change clears previous recommendation

## 3) Verify existing Phase 5 UI source
Keep/fix:
- CUSTOM due: native date input; local 17:00 -> valid ISO; invalid date never stored; NONE=null
- URGENT priority localized
- AUTO/NONE unchanged

## Preserve
No Phase 1-4 RBAC changes.
No taskCommands/approval changes.
No Phase 6/7.
No structured direct submit.

## Workflow
Inspect actual current local HEAD ebcbdd9.
Make required changes and create a NEW commit.
COMMIT ONLY. DO NOT PUSH.

The returned SHA must be different from ebcbdd9.

## Return only
PATCH=RAMZY-SMART-TASK-V3-PHASE-5-R2-COMPLETE-MISSING-SOURCE
PASS/FAIL=
BASELINE_COMMIT=ebcbdd9
R2_NEW_COMMIT=
AI_TEMPLATE_FALLBACK_REMOVED=
AI_FAILURE_NON_2XX=
AI_NO_TOOLS=
WORKLOAD_SCORE_ACTIVE_URGENT_OVERDUE=
VISIBLE_TASK_SCOPE_REUSED=
RECOMMENDATION_AUTHORIZED_ONLY=
RECOMMENDATION_TIE_RETURNS_NULL=
RECOMMENDATION_AUTO_ASSIGNS=NO
CUSTOM_DUE_VALID_ISO=
URGENT_PRIORITY=
FRONTEND_BUILD=
BACKEND_TEST=
WORKTREE_CLEAN=
ERROR=
