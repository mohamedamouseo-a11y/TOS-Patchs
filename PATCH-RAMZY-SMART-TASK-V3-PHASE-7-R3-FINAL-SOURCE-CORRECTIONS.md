# PATCH-RAMZY-SMART-TASK-V3-PHASE-7-R3-FINAL-SOURCE-CORRECTIONS

Baseline pushed main commit:
e495d480e0eb754bf06009c2602dfdab770cf05c

Final source-verification corrections only. Do not expand scope.

## 1) Route must explicitly validate enabled user + owned conversation
In POST /api/agent/task-create/proposal:

- await assertAgentEnabledForUser(req.user)
- require conversationId/projectId/title
- await assertConversationOwner(req.user, conversationId)
- then existing settings/execution/project checks
- DO NOT create AgentConversation
- reuse supplied conversationId

Keep canonical createTaskActionProposal as the proposal creator.

## 2) Frontend final submit must ensure a conversation exists
Current source returns "Start a conversation first" when conversationId is empty. Replace this.

On Submit for approval:
- let id = conversationId
- if no id: id = (await createConversation()).id
- use id as payload.conversationId
- keep that conversation selected via existing createConversation behavior
- do not call chat/model/stream
- failure still preserves review/draft

No user should have to manually start a conversation first.

## 3) Add/use a pure structured payload builder
Create a small pure helper/function used by final submit.

Input: reviewed Smart Task state + resolved assigneeId + conversationId.
Output:
{
  conversationId,
  projectId,
  title,
  description,
  priority,
  dueDate,
  assigneeId,
  estimatedHours,
  startDate,
  reminderAt
}

Rules:
- title trim, max 180
- description current editable value, max 4000
- IDs from selected state only
- nullable optionals stay null
- estimatedHours number|null
- no visible name used as ID
- final API call uses this builder result

## 4) Fix same-card review summary completeness/readability
Current summary is incomplete and exposes raw values.

Review must show:
- Title
- Description only if present
- Project
- Due date OR No due date
- Priority localized/human-readable
- Assignee resolved name OR Unassigned
- Estimated hours if present
- Start date if present
- Reminder time if present

Requirements:
- no raw IDs
- no raw ISO
- due date rendered in local readable date/time
- start date rendered in local readable date
- reminder rendered in local readable date/time
- use smartTaskPriorityLabel for priority (or equivalent existing localized mapping)
- AUTO assignee name must come from current authorized smartTaskAssignees recommendation
- NONE shows Unassigned / بدون تحديد
- review remains read-only until Back to edit

## 5) Preserve exact final copy from R2
AUTO assignee:
EN: No unique workload suggestion is available. Choose an assignee or Unassigned.
AR: لا يوجد اقتراح فريد حسب ضغط العمل. اختر منفذًا أو بدون تحديد.

AUTO priority:
EN: Choose a specific priority before review.
AR: اختر أولوية محددة قبل المراجعة.

Buttons:
EN: Back to edit / Submit for approval
AR: رجوع للتعديل / إرسال للاعتماد

## 6) Preserve all structural safety
Do NOT regress:
- current conversation reuse
- no route-created conversation
- assigneeId nullable
- AUTO recommendation must exist in current authorized assignee list
- runless gate CREATE_TASK + !runId + !toolExecutionId
- conditional AgentRun lookup
- canonical createTaskActionProposal
- PENDING approval only
- no direct Task creation before approval
- protected projectId/assigneeId revision boundaries
- server project/assignee revalidation
- Phase 6 reminder execution behavior
- Phase 1-6
- no DB migration
- no scheduler
- no unrelated refactor
- no backups staged

## 7) Tests
Add/update focused tests for:
- route calls assertAgentEnabledForUser
- route calls assertConversationOwner with supplied conversationId
- route does NOT agentConversation.create
- frontend auto-creates/reuses conversation before structured submit when needed
- structured payload builder exact values/nulls/advanced fields
- review includes description when present
- review due/start/reminder do not render raw ISO
- localized priority label used
- exact R2 copy remains
- no sendMessage/streamMessage/runRamzyTurn in final Smart Task submit path
- existing Ramzy tests green

## Verify
- frontend build PASS
- backend test:ramzy PASS
- ONE NEW COMMIT
- COMMIT ONLY
- DO NOT PUSH

## Return only
PATCH=RAMZY-SMART-TASK-V3-PHASE-7-R3-FINAL-SOURCE-CORRECTIONS
PASS/FAIL=
BASELINE_COMMIT=e495d48
R3_NEW_COMMIT=
ENABLED_USER_CHECK=
OWNED_CONVERSATION_CHECK=
AUTO_CREATE_CONVERSATION_IF_MISSING=
STRUCTURED_BUILDER=
DESCRIPTION_IN_REVIEW=
NO_RAW_ISO_IN_REVIEW=
LOCALIZED_PRIORITY_REVIEW=
UNASSIGNED_NULL_SUPPORTED=
AUTO_AUTHORIZED_ONLY=
RUNLESS_GATE_PRESERVED=
CHAT_MODEL_SUBMIT=NO
DIRECT_TASK_EXECUTION=NO
APPROVAL_PENDING_ONLY=
FRONTEND_BUILD=
BACKEND_TEST=
UNTRACKED_BACKUPS_UNSTAGED=
ERROR=
