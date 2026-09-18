# PATCH-RAMZY-SMART-TASK-V3-PHASE-7-STRUCTURED-REVIEW-APPROVAL

Baseline main commit:
d821d387a464861e8af66108ca6b13f0f7062c83

## Goal
Implement the FINAL Smart Task V3 phase.

Replace the Smart Task card's natural-language prompt submission with a structured CREATE_TASK proposal request, while preserving the existing mandatory Ramzy approval flow.

Final flow:
1. User completes the existing Smart Task card.
2. Click `Review & create`.
3. The SAME card switches to a compact review state.
4. User clicks `Submit for approval`.
5. Frontend sends structured task fields directly to TOS.
6. Backend creates a normal PENDING CREATE_TASK approval using the existing proposal pipeline.
7. No task is created until the user explicitly approves the existing ApprovalCard.

NO LLM/model/stream/message round-trip is allowed for Smart Task submission in Phase 7.

## 1) Structured endpoint
Add authenticated endpoint:

`POST /api/agent/task-create/proposal`

Body:
```json
{
  "conversationId": "...",
  "projectId": "...",
  "title": "...",
  "description": "...",
  "priority": "LOW|MEDIUM|HIGH|URGENT",
  "dueDate": "ISO|null",
  "assigneeId": "user-id|null",
  "estimatedHours": "number|null",
  "startDate": "ISO|null",
  "reminderAt": "ISO|null"
}
```

Do not accept client projectName, assigneeName, confirmation metadata, targetType, targetId, actionType, status, or execution fields.

Endpoint requirements:
- `assertAgentEnabledForUser`
- exact conversation ownership via existing `assertConversationOwner`
- `getAgentSettings`
- `assertRamzyActionExecutionAllowed`
- exact project CREATE_TASK authorization
- exact assignee authorization remains server-side through existing CREATE_TASK proposal service
- use current CREATE_TASK normalizer and Phase 6 validation
- response is the existing public approval view
- emit `ramzy:approval` to the current user if useful, but frontend must also consume the direct response
- status 201

This endpoint creates a PENDING approval only. It must NEVER call approved execution.

## 2) Reuse the canonical proposal pipeline
Do NOT duplicate CREATE_TASK proposal logic.

Adapt `createTaskActionProposal` narrowly so a structured Smart Task proposal may exist without an AgentRun/tool execution:
- existing model/tool callers continue to require their existing run context unchanged
- structured Smart Task path may use `runId=null`, `toolExecutionId=null`
- conversation ownership must still be validated
- only CREATE_TASK may use this runless structured path
- PENDING approval schema already supports nullable runId
- keep existing project resolution, assignee validation, normalized payload, projectName/assigneeName server enrichment, confirmation metadata, expiry, approval title
- no DB migration

Prefer an explicit option/wrapper such as `allowRunlessCreate` / `createStructuredTaskCreateProposal`; do not silently make every action runless.

## 3) Frontend API
Add:
`api.agent.proposeTaskCreate(payload)`

POST to:
`/api/agent/task-create/proposal`

No `streamMessage`, no `sendMessage`, no model call.

## 4) Structured payload builder
Create/reuse a small pure helper for the final Smart Task payload.

Payload MUST use IDs/values already held by the card:
- projectId = selected authorized project id
- title = trimmed title, max 180
- description = current editable description, max 4000
- dueDate = exact current ISO or null
- priority = exact concrete LOW/MEDIUM/HIGH/URGENT
- assigneeId = exact authorized selected/resolved ID or null
- estimatedHours = normalized number or null
- startDate = current Phase 6 ISO or null
- reminderAt = current Phase 6 ISO or null

Never derive project/assignee from visible names.
Never stringify IDs into a natural-language prompt.

### AUTO assignee
Keep the existing AUTO option, but structured submission needs a concrete result:
- if AUTO is selected AND `recommendedAssigneeId` resolves to one of the currently returned authorized assignee users, use that exact ID
- show that resolved person's name in the review
- if AUTO is selected but there is no valid authorized recommendation, block review and show:
  - EN: `No unique workload suggestion is available. Choose an assignee or Unassigned.`
  - AR: `لا يوجد اقتراح فريد حسب ضغط العمل. اختر منفذًا أو بدون تحديد.`
- never auto-pick an arbitrary user

### AUTO priority
Do NOT silently convert AUTO to MEDIUM or invent a heuristic.
There is no current structured priority recommender.

Keep the existing AUTO chip visible for compatibility, but before structured review require a concrete priority:
- if priority is AUTO, block review with:
  - EN: `Choose a specific priority before review.`
  - AR: `اختر أولوية محددة قبل المراجعة.`

No model call should be added only to resolve AUTO priority in this phase.

## 5) Review state inside the SAME card
Do not open a modal or second card.

Add draft state `reviewing: false` (or equivalent).

When user clicks current `Review & create`:
- run all existing basic + CUSTOM due + Phase 6 advanced validation
- resolve AUTO assignee as above
- require concrete priority
- if valid, switch the same card to review mode
- DO NOT send anything to backend yet

Review state should show compact human-readable rows, no internal IDs:
- Title
- Description only if present
- Project name
- Due date / No due date
- Priority
- Assignee name / Unassigned
- advanced values only if present:
  - Estimated hours
  - Start date
  - Reminder time

Use current localized labels.
Display dates in user-local readable format.
Do not expose projectId/userId/ISO raw strings in review UI.

Buttons:
- `Back to edit` / `رجوع للتعديل`
- `Submit for approval` / `إرسال للاعتماد`

Back to edit preserves the complete draft.

If any draft field changes after review mode is entered, the user must return/edit and review the current values before submission; simplest acceptable implementation is to make review state read-only until Back to edit.

## 6) Final structured submission
On `Submit for approval`:
- protect against double submit
- ensure a conversation exists; reuse current conversation or create one with existing `createConversation`
- build the structured payload from the reviewed draft
- call `api.agent.proposeTaskCreate`
- no natural-language prompt
- no streaming assistant placeholder/message
- no `metadata.intent=CREATE_TASK`
- no `runRamzyTurn`

On success:
- returned approval must be added to `approvals` exactly once
- approval has `runId=null` and is already rendered by the existing standalone ApprovalCard branch
- close/reset Smart Task card
- clear Smart Task local errors/loading
- keep conversation selected
- ApprovalCard remains the ONLY way to APPROVE/REJECT and execute

On endpoint failure:
- keep the entire Smart Task draft and review state
- show a localized compact error
- do not create optimistic approval
- allow retry

## 7) Approval / execution safety
Preserve exactly:
- CREATE_TASK remains HIGH risk
- explicit confirmation required
- no direct execution
- existing ApprovalCard Approve/Reject
- existing approval revision support
- projectId and assigneeId protected from approval revision
- project authorization rechecked on decision
- assignee authorization rechecked at execution
- Phase 6 reminder execution exception behavior
- board/list/task persistence behavior

Structured proposal creation must NOT create a Task row.

## 8) Remove old Smart Task prompt submission path
For Smart Task only:
- remove/retire `smartTaskPrompt()` natural-language serialization if no longer used
- `submitSmartTask` must not call `sendMessage`
- no `skipSmartTaskIntent`
- no `metadata.intent=CREATE_TASK`
- normal Ramzy chat and typed CREATE_TASK intent detection remain unchanged; typed intent still opens the Smart Task card

Do not change normal conversational Ramzy behavior outside the card.

## 9) Tests
Add behavior/static coverage for at least:
- structured builder emits exact projectId, assigneeId, title, description, priority, dueDate
- Phase 6 advanced fields included when present
- null optional values remain null
- no visible names are used as IDs
- AUTO assignee resolves only to current authorized recommendation
- AUTO assignee with no valid recommendation blocks
- AUTO priority blocks structured review
- review does not create proposal
- final submit calls structured endpoint, not stream/message path
- endpoint rejects missing conversation/project/title
- runless structured CREATE_TASK proposal allowed only through explicit structured option/wrapper
- non-CREATE_TASK actions cannot use runless path
- approval status is PENDING and task execution is not invoked
- protected project/assignee revision rules unchanged
- existing Phase 1-6 tests remain green

No external AI/network dependency in tests.

## 10) Preserve / forbidden
Preserve all Phase 1-6 behavior except replacing the final Smart Task prompt submission with structured review/proposal.

DO NOT:
- execute task directly from Smart Task card
- create a second task creation implementation
- bypass `createTaskActionProposal`
- weaken RBAC
- accept projectName/assigneeName from client as authority
- use LLM to reinterpret the reviewed task
- add DB migration
- add reminder scheduler
- refactor unrelated Ramzy code
- stage untracked backup files

## Verification
- frontend build PASS
- backend Ramzy tests PASS
- Smart Task final submission uses structured endpoint only
- no Smart Task prompt serialization remains active
- same-card review works
- failed proposal preserves draft
- endpoint creates PENDING approval only
- no Task before explicit approval
- existing approval decision executes through canonical path
- current project/assignee authorization preserved
- Phase 1-6 regression tests PASS
- ONE NEW COMMIT
- COMMIT ONLY
- DO NOT PUSH

## Return only
PATCH=RAMZY-SMART-TASK-V3-PHASE-7-STRUCTURED-REVIEW-APPROVAL
PASS/FAIL=
BASELINE_COMMIT=d821d38
PHASE7_NEW_COMMIT=
STRUCTURED_ENDPOINT=
SAME_CARD_REVIEW=
NATURAL_LANGUAGE_SUBMISSION_REMOVED=
AUTO_ASSIGNEE_AUTHORIZED_RESOLUTION=
AUTO_ASSIGNEE_AMBIGUOUS_BLOCKS=
AUTO_PRIORITY_REQUIRES_CONCRETE=
RUNLESS_CREATE_ONLY_EXPLICIT=
APPROVAL_CREATED_PENDING_ONLY=
DIRECT_TASK_EXECUTION=NO
PROJECT_ASSIGNEE_SERVER_REVALIDATED=
ADVANCED_FIELDS_PRESERVED=
FAILED_SUBMIT_PRESERVES_DRAFT=
APPROVAL_REQUIRED=YES
FRONTEND_BUILD=
BACKEND_TEST=
UNTRACKED_BACKUPS_UNSTAGED=
ERROR=
