# PATCH-RAMZY-SMART-TASK-V3-PHASE-5-R5-FINAL-SOURCE-CORRECTION

Current local HEAD: f1bde5d972263420919f1d1315f716d3b07cdb01
Current worktree: dirty; keep existing Phase 5 work. Do NOT reset/checkout/stash/discard.

## Verified current defects
1. suggest-description route does not require projectId or assert task-create access.
2. generateDescriptionSuggestion has duplicate `const data`, mixes parsed API data with fetch Response APIs, and uses assignee error state.
3. CUSTOM due currently falls through smartTaskDuePreset() to +7 days and date input stores raw YYYY-MM-DD instead of local 17:00 ISO.
4. CUSTOM/URGENT labels are incomplete.
5. assignee endpoint has no real workload recommendation.

## Fix only these issues

### A) Real AI description endpoint
Keep:
POST /api/agent/task-create/suggest-description

Body:
`{ projectId, title, description?, language }`

Backend:
- require projectId and trimmed title
- getAgentSettings + assertRamzyActionExecutionAllowed
- call `assertAgentTaskCreateAccess(req.user, projectId, settings.allowedWorkspaceIds || [], prisma)` before AI
- use current configured provider/model through the existing `generateTaskDescription` service
- adapt that service if needed so it performs a plain model generation with NO tools/actions/side effects
- pass title + optional current description + requested language
- NO template/static fallback
- provider/config/generation failure must propagate as non-2xx
- return `{ok:true,suggestion:<plain text <=4000>}`
- do not invent IDs, assignee, priority, due date, credentials, or unsupported facts

Frontend:
- add separate `smartTaskDescriptionError` state
- call only when exact project + trimmed title exist
- use parsed api result directly; DO NOT use `response.ok` or `response.json()`
- send exact projectId/title/current description/language
- success replaces description only
- error leaves description and all draft fields unchanged and displays only description error
- remove duplicate `const data`

Ensure `api.agent.suggestTaskDescription(...)` points to `/api/agent/task-create/suggest-description`.

### B) Real authorized workload recommendation
Extend existing GET /api/agent/task-create/assignees response:
`{ok:true,users:assignable,recommendedAssigneeId}`

After the existing Phase 4 authorization list is built:
- candidate IDs = returned assignable IDs only
- if fewer than 2 candidates => recommendation null
- reuse existing `buildAgentTaskVisibilityWhere` authorization
- query only selected project, `archivedAt:null`, status not in DONE/CANCELLED
- select only fields needed for score: priority,dueDate,assigneeId,assignees.userId
- combine legacy assigneeId + assignees relation with a Set per task/person
- ignore IDs not in authorized candidates
- score each candidate using:
  `active + (urgent * 2) + (overdue * 3)`
- recommendation exists only when exactly one candidate has a strictly lower score than every other candidate
- tie => null
- return only the ID, never workload/task details
- no auto-assignment

Frontend:
- add separate recommendation ID state
- clear it before each assignee load/project change
- accept response recommendation only if it matches one of returned users
- show compact clickable `Workload suggestion: <name>` / `اقتراح حسب ضغط العمل: <name>`
- click calls existing exact-user selection
- never select automatically

### C) CUSTOM due date correctness
- `smartTaskDuePreset("CUSTOM")` must return null, not +7 days
- add CUSTOM label: `تاريخ آخر` / `Custom date`
- choosing CUSTOM sets `dueKind:"CUSTOM"` and waits for user date
- native date input value must be represented in LOCAL calendar date, not UTC slicing
- on date change: parse YYYY-MM-DD as local date at 17:00:00.000; if invalid or before local today, do not store it
- store valid value as `toISOString()`
- NONE => null
- switching to preset recalculates ISO and hides custom input
- submit remains disabled while CUSTOM has no valid dueDate

### D) URGENT priority
- add `URGENT: {ar:"عاجلة",en:"Urgent"}` to `smartTaskPriorityLabel`
- keep priority chips HIGH, URGENT, MEDIUM, LOW, AUTO
- no backend priority changes

## Preserve
Phase 1 parser.
Phase 3 project RBAC.
Phase 4 assignee authorization.
AUTO/NONE.
Current approval + prompt-based submit flow.
No Phase 6/7.
Do not add backup/untracked files to commit.

## Verify
- frontend build PASS
- backend syntax + relevant Ramzy tests PASS
- no duplicate declarations
- suggestion route project authorization present
- no template fallback
- workload recommendation authorized + visible-scope only
- CUSTOM stores valid ISO at local 17:00
- URGENT localized
- git diff --cached contains only intended source files
- worktree may still contain unrelated untracked backups; do not stage them

## Workflow
Continue from current dirty worktree.
Make fixes.
Create ONE NEW commit containing completed Phase 5 source changes.
COMMIT ONLY. DO NOT PUSH.

## Return only
PATCH=RAMZY-SMART-TASK-V3-PHASE-5-R5-FINAL-SOURCE-CORRECTION
PASS/FAIL=
NEW_COMMIT=
AI_PROJECT_AUTH=
AI_NO_TEMPLATE_FALLBACK=
AI_NO_TOOLS=
AI_ERROR_ISOLATED=
WORKLOAD_RECOMMENDATION=
VISIBLE_TASK_SCOPE_REUSED=
AUTHORIZED_ONLY=
TIE_RETURNS_NULL=
AUTO_ASSIGNS=NO
CUSTOM_LOCAL_1700_ISO=
CUSTOM_INVALID_BLOCKED=
URGENT_LOCALIZED=
FRONTEND_BUILD=
BACKEND_TEST=
TRACKED_WORKTREE_CLEAN=
UNTRACKED_BACKUPS_UNSTAGED=
ERROR=
