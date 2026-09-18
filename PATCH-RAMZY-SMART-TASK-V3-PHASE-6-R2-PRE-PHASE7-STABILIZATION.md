# PATCH-RAMZY-SMART-TASK-V3-PHASE-6-R2-PRE-PHASE7-STABILIZATION

Baseline main commit:
c4682854f5e58c4566dbc80ef81318f570a4418d

This is a tiny Phase 6 stabilization patch required before Phase 7. Do not implement Phase 7 here.

## 1) Do not re-reject an already-approved reminder during final execution
Current CREATE_TASK normalization validates reminderAt > now, and final approved execution calls the same normalizer. That means a valid reminder can become past while waiting for approval and then the approved task fails to execute.

Preserve future validation at:
- CREATE_TASK proposal creation
- pending CREATE_TASK approval revision

But final approved execution must NOT fail solely because reminderAt has become past since approval.

Implement this cleanly without weakening:
- date parsing
- startDate <= dueDate
- reminderAt <= dueDate
- all RBAC/approval checks

Preferred approach:
- make the future-reminder check controllable via a narrow normalization option, default ON
- proposal/revision paths keep default ON
- executeApprovedTaskCreate calls normalization with future-reminder validation OFF only
- do not bypass any other validation

Add behavior test proving:
- past reminder is rejected for proposal/revision normalization
- same already-approved payload can be normalized for final execution with only future check skipped

## 2) Fix CUSTOM due-date submit validation
Current Smart Task stores CUSTOM dueDate as ISO but submit validates by passing that ISO into smartTaskCustomDueIso(), which expects YYYY-MM-DD.

Fix so a valid custom date is not blocked.

Requirements:
- CUSTOM with valid stored ISO submits
- CUSTOM with null/invalid dueDate is blocked
- preserve local calendar date semantics
- no UTC split
- add behavior coverage

## 3) Disable Review & Create for invalid advanced values
The button must include current advanced validation in its disabled state.

Rules:
- blank advanced fields remain valid
- invalid hours/start/reminder/order => disabled
- valid advanced => enabled when all existing basic required fields are valid
- keep the visible compact advanced error on submit

Do not remove existing submit-time validation; disabled state is an additional UX guard.

## 4) Exact Phase 6 labels
Use exact user-facing labels:
- collapsed toggle AR: `تفاصيل إضافية`
- expanded hide AR: `إخفاء التفاصيل الإضافية`
- Estimated hours AR: `الساعات المتوقعة`
- Start date AR: `تاريخ البداية`
- Reminder time EN: `Reminder time`
- Reminder time AR: `وقت التذكير`

Use the same labels in approval/revision display where applicable.

## Preserve
- Phase 1-5 behavior
- Phase 6 three advanced fields only
- advanced default closed
- approval mandatory
- protected projectId/assigneeId revision boundaries
- no DB migration
- no reminder scheduler
- no Phase 7
- no unrelated refactor
- backup files unstaged

## Verification
- frontend build PASS
- backend Ramzy tests PASS
- valid CUSTOM due submits
- invalid CUSTOM due blocks
- reminder future check active at proposal/revision
- reminder future check skipped only during final approved execution
- static date/order checks still active at execution
- advanced-invalid button disabled
- blank advanced does not disable
- exact labels above
- ONE NEW COMMIT
- COMMIT ONLY
- DO NOT PUSH

## Return only
PATCH=RAMZY-SMART-TASK-V3-PHASE-6-R2-PRE-PHASE7-STABILIZATION
PASS/FAIL=
BASELINE_COMMIT=c468285
R2_NEW_COMMIT=
CUSTOM_DUE_VALID_SUBMITS=
CUSTOM_DUE_INVALID_BLOCKS=
REMINDER_FUTURE_PROPOSAL_REVISION=
REMINDER_FUTURE_SKIPPED_EXECUTION_ONLY=
STATIC_DATE_RULES_PRESERVED=
ADVANCED_INVALID_DISABLES=
BLANK_ADVANCED_VALID=
LABELS_EXACT=
APPROVAL_REQUIRED=YES
PHASE7_INCLUDED=NO
FRONTEND_BUILD=
BACKEND_TEST=
UNTRACKED_BACKUPS_UNSTAGED=
ERROR=
