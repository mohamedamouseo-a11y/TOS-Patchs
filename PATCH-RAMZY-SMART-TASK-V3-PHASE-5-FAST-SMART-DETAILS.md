# PATCH-RAMZY-SMART-TASK-V3-PHASE-5-FAST-SMART-DETAILS

Baseline: 92e4f3e48a8947f5b1545051bd508e8602f8c952

## Goal
Implement the roadmap's Phase 5 only: AI description generation + workload-aware assignee suggestion + smarter fast due/priority controls.

Keep the current single-card Smart Task, Phase 3 project authorization, Phase 4 assignee authorization, and existing approval flow.

## 1) AI description — explicit user action only
Add a compact button beside/under Description:
- empty description: `صياغة الوصف مع رمزي` / `Write with Ramzy`
- non-empty description: `تحسين الوصف مع رمزي` / `Improve with Ramzy`

Add POST:
`/api/agent/task-create/suggest-description`

Body:
`{ projectId, title, description?, language }`

Backend rules:
- require authenticated Ramzy route
- getAgentSettings/getAgentRuntimeSettings
- assertRamzyActionExecutionAllowed
- assertAgentTaskCreateAccess for exact project and allowedWorkspaceIds
- title required, trim/cap consistently with Smart Task
- description optional/capped
- reuse the current configured AI provider/model via existing provider stack; no new dependency
- use a model call with NO tools and NO side-effect agent/tool path
- prompt only for a short actionable task description in requested language
- do not invent assignee, due date, priority, IDs, credentials, or facts not provided
- plain text only; cap returned description <= 4000 chars
- provider/config failure => proper non-2xx error; do not break the Smart Task card

Frontend:
- user must click; never auto-call AI
- show local loading/error for description suggestion
- on success replace only `smartTask.description`
- preserve every other draft field
- generated text remains editable
- endpoint failure leaves current description unchanged

## 2) Workload-aware assignee suggestion
Extend the existing authorized assignee endpoint; do NOT create a second generic users source.

After Phase 4 candidate authorization:
- only consider the already-authorized candidate IDs
- derive workload only from tasks the requesting actor is allowed to see in the selected project, reusing existing task visibility logic
- open tasks only; exclude DONE/CANCELLED and archived
- dedupe legacy assigneeId + assignees relation per task
- deterministic score may weight active + urgent + overdue, but do not duplicate assignment/RBAC rules
- if there is no meaningful workload difference, return no recommendation instead of arbitrary alphabetical selection

Response may add:
`recommendedAssigneeId`
The ID must be null or one of returned `users`.

Do not expose hidden task titles/IDs or unauthorized workload data.

Frontend:
- if a recommendation exists, show one compact suggestion row/button:
  `اقتراح حسب ضغط العمل: <name>` / `Workload suggestion: <name>`
- clicking it selects that exact authorized user
- do NOT auto-assign
- AUTO and NONE remain
- changing project clears old recommendation and reloads it with that project's assignees
- assignee endpoint error behavior remains independent from project picker

## 3) Fast due-date controls
Keep current chips:
TODAY, TOMORROW, IN_2_DAYS, IN_1_WEEK, NONE

Add:
CUSTOM / `تاريخ آخر` / `Custom date`

Behavior:
- choosing CUSTOM reveals a compact native date input inside the card
- selected local date becomes dueDate at 17:00 local time, then stored as ISO
- no invalid/NaN date may enter the draft
- switching to another preset hides custom input and recalculates dueDate
- NONE => dueDate null
- keep draft fields intact

## 4) Priority completeness
Backend CREATE_TASK already supports:
LOW, MEDIUM, HIGH, URGENT

Add URGENT to Smart Task quick priority choices and localized label:
- AR: `عاجلة`
- EN: `Urgent`

Keep AUTO unchanged.
Do not change backend priority semantics.

## Do not change
- canonical CREATE_TASK intent parser
- project picker/RBAC
- assignee authorization rules
- taskCommands CREATE_TASK authorization
- approval requirement
- current submitSmartTask -> sendMessage metadata.intent=CREATE_TASK path
- structured direct submission (Phase 7)
- optional advanced fields (Phase 6)
- AI provider/model settings UI
- normal Ramzy conversation behavior

## Source/build verification
- no generic api.users source for Smart Task
- description AI has no tools/side effects
- recommendation ID always belongs to authorized returned users
- exact assigneeId preserved after applying recommendation
- CUSTOM date produces valid ISO
- URGENT passes current CREATE_TASK vocabulary
- frontend build PASS
- relevant backend syntax/tests PASS
- no browser/live QA yet

## Workflow
Implement against baseline, build/test, COMMIT ONLY.
DO NOT push.

## Return
PATCH=RAMZY-SMART-TASK-V3-PHASE-5-FAST-SMART-DETAILS
PASS/FAIL=<result>
BASELINE_COMMIT=92e4f3e
PHASE5_NEW_COMMIT=<sha>
AI_DESCRIPTION_BUTTON=YES/NO
AI_DESCRIPTION_NO_TOOLS=YES/NO
AI_DESCRIPTION_ERROR_ISOLATED=YES/NO
WORKLOAD_RECOMMENDATION_AUTHORIZED_ONLY=YES/NO
WORKLOAD_RECOMMENDATION_VISIBLE_SCOPE_ONLY=YES/NO
RECOMMENDATION_AUTO_ASSIGNS=NO
CUSTOM_DUE_DATE=YES/NO
URGENT_PRIORITY=YES/NO
APPROVAL_CHANGED=NO
PHASE7_STRUCTURED_SUBMISSION=NO
FRONTEND_BUILD=PASS/FAIL
BACKEND_TEST=PASS/FAIL
WORKTREE_CLEAN=YES/NO
ERROR=<NONE or exact error>
