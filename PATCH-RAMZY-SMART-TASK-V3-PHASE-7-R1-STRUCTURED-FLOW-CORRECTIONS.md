# PATCH-RAMZY-SMART-TASK-V3-PHASE-7-R1-STRUCTURED-FLOW-CORRECTIONS

Baseline local commit:
9cac7d901eaf256aa4bc5dc34351fbbece494780

Phase 7 is close, but do NOT push yet. Fix only the following Phase 7 gaps.

## 1) Use the CURRENT conversation; do not create a hidden Smart Task conversation
Current route creates a new AgentConversation on every proposal. Remove that.

POST /api/agent/task-create/proposal must accept:
- conversationId
- projectId
- title
- description
- priority
- dueDate
- assigneeId (nullable)
- estimatedHours
- startDate
- reminderAt

Route:
- await assertAgentEnabledForUser(req.user)
- require conversationId/projectId/title
- validate priority concrete
- await assertConversationOwner(req.user, conversationId)
- get settings + assertRamzyActionExecutionAllowed
- assertAgentTaskCreateAccess
- call canonical createTaskActionProposal using THAT conversationId
- status 201, public approval view
- DO NOT create AgentConversation in this route
- DO NOT call runRamzyTurn or task execution

Frontend final submit:
- ensure conversation exists using existing current conversation/createConversation
- send conversationId in structured payload
- keep current conversation selected
- returned runId=null approval should render in existing standalone ApprovalCard branch and persist on reload of same conversation

## 2) Preserve Unassigned
Phase 4 supports NONE / Unassigned. Phase 7 must not remove it.

- assigneeId is nullable
- route must NOT require assigneeId
- specific assignee => exact selected authorized id
- NONE => assigneeId:null
- AUTO => must resolve to a concrete CURRENT authorized recommendation or block
- canonical server assignee checks remain unchanged when assigneeId is non-null

## 3) AUTO assignee must resolve against current authorized users
Do not trust only a non-empty recommendedAssigneeId.

Resolve:
- recommended user = smartTaskAssignees.find(user.id === smartTaskRecommendedAssigneeId)
- AUTO is valid only if that user exists in the current returned authorized list
- use that exact id + name for review/payload
- never arbitrary fallback

Exact missing-AUTO copy:
EN: No unique workload suggestion is available. Choose an assignee or Unassigned.
AR: لا يوجد اقتراح فريد حسب ضغط العمل. اختر منفذًا أو بدون تحديد.

## 4) Same-card review must be a real review summary
Current review shows only "Review: <title>". Replace with compact read-only rows INSIDE the same card:

- Title
- Description only if present
- Project name
- Due date / No due date
- Priority
- Assignee resolved name / Unassigned
- Estimated hours only if present
- Start date only if present
- Reminder time only if present

Rules:
- human-readable localized values
- local date/time display
- no raw IDs
- no raw ISO strings
- review is read-only until Back to edit
- Back preserves complete draft

Buttons exact:
EN:
- Back to edit
- Submit for approval
AR:
- رجوع للتعديل
- إرسال للاعتماد

## 5) Concrete priority exact validation copy
AUTO priority must block review.

Exact:
EN: Choose a specific priority before review.
AR: اختر أولوية محددة قبل المراجعة.

Do not map AUTO silently and do not call AI.

## 6) Add a small pure structured payload builder
Build reviewed payload from state, not visible labels.

Must output:
- conversationId
- projectId
- title = trim, max 180
- description = current value, max 4000
- priority concrete
- dueDate ISO|null
- assigneeId exact id|null
- estimatedHours normalized number|null
- startDate ISO|null
- reminderAt ISO|null

Never use project/assignee visible names as IDs.

Use the SAME reviewed values for the final API call.

## 7) Tighten explicit runless gate
Current runless gate should not accidentally bypass run validation when runId is supplied.

Requirements:
- runless allowed only when:
  allowRunlessStructuredCreate === true
  AND actionType === CREATE_TASK
  AND !runId
  AND !toolExecutionId
- if runId exists, validate it normally
- do not query AgentRun with undefined runId; use conditional lookup
- all non-CREATE_TASK behavior remains unchanged

No DB migration.

## 8) Submission UX
On final submit:
- guard double-submit
- structured endpoint only
- no sendMessage / streamMessage / runRamzyTurn
- success: add approval once, close Smart Task, clear local errors
- failure: preserve full review/draft, show compact error, retry allowed
- approval mandatory; no direct Task creation

## 9) Tests
Add/upgrade tests for:
- route uses supplied conversationId and does NOT create AgentConversation
- route requires owned conversation
- assigneeId:null accepted
- AUTO recommendation must exist in current smartTaskAssignees
- NONE => null
- AUTO missing/stale => exact block
- AUTO priority exact block
- structured builder exact IDs/values + advanced/nulls
- review summary contains all required rows/labels
- final submit sends conversationId and structured endpoint only
- explicit runless gate requires !runId && !toolExecutionId
- run lookup conditional when runId absent
- PENDING approval only; no task execution
- existing Phase 1-6 tests green

Prefer behavioral/pure-helper assertions over source-regex-only checks where practical.

## Preserve
- Phase 1-6
- existing approval/revision/execution pipeline
- protected projectId/assigneeId revision boundaries
- project/assignee server revalidation
- Phase 6 reminder execution exception
- no scheduler
- no unrelated refactor
- backups unstaged

## Verify
- frontend build PASS
- backend test:ramzy PASS
- ONE NEW COMMIT
- COMMIT ONLY
- DO NOT PUSH

## Return only
PATCH=RAMZY-SMART-TASK-V3-PHASE-7-R1-STRUCTURED-FLOW-CORRECTIONS
PASS/FAIL=
BASELINE_COMMIT=9cac7d9
R1_NEW_COMMIT=
CURRENT_CONVERSATION_REUSED=
NEW_CONVERSATION_CREATED_BY_ROUTE=NO
UNASSIGNED_NULL_SUPPORTED=
AUTO_ASSIGNEE_AUTHORIZED_RESOLUTION=
AUTO_ASSIGNEE_STALE_BLOCKED=
AUTO_PRIORITY_BLOCKED=
REAL_SAME_CARD_REVIEW=
STRUCTURED_BUILDER=
RUNLESS_GATE_EXPLICIT=
DIRECT_TASK_EXECUTION=NO
APPROVAL_PENDING_ONLY=
FAILED_SUBMIT_PRESERVES_DRAFT=
FRONTEND_BUILD=
BACKEND_TEST=
UNTRACKED_BACKUPS_UNSTAGED=
ERROR=
