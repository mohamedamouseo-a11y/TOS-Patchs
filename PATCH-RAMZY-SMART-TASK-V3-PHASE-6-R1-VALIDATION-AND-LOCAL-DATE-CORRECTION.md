# PATCH-RAMZY-SMART-TASK-V3-PHASE-6-R1-VALIDATION-AND-LOCAL-DATE-CORRECTION

Baseline local commit:
0bb1b41f576633c62bd93c5f7a185b15f8a28a00

Do not push yet.

The Phase 6 structure is correct, but the full source review found acceptance gaps. Fix only the items below.

## 1) Estimated hours must match the Phase 6 contract
Current implementation allows up to 100000 and uses step 0.1.

Required everywhere:
- optional / blank => null
- finite number
- > 0
- <= 999
- normalize to max 2 decimal places
- UI input:
  - min > 0
  - max 999
  - step 0.25
- Ramzy CREATE_TASK tool schema:
  `estimatedHours: z.number().positive().max(999).nullable().optional()`

Backend normalizer must reject:
- 0
- negative
- >999
- NaN / non-finite

Do not silently clamp invalid user values.

## 2) Start date is DATE-ONLY and must become local 09:00 ISO
Current implementation incorrectly uses datetime-local.

Required Smart Task UI:
- input type=`date`
- label:
  - EN: `Start date`
  - AR: `تاريخ البداية`
- blank => null
- selected YYYY-MM-DD must be parsed as LOCAL calendar date at 09:00:00.000
- store as ISO
- display stored ISO back using local year/month/day; never UTC split
- reject nonexistent/invalid date

Add/reuse a small pure helper, e.g.
- `smartTaskStartDateIso(localDate)`
- existing local date display helper may be reused

Approval revision editor should also present start date as type=date, preserving local calendar date and converting to local 09:00 ISO on save.

## 3) Reminder is datetime-local and must be future
Keep reminder as datetime-local.

Required:
- blank => null
- valid local datetime -> ISO
- invalid => null
- at proposal creation/revision time, reminderAt must be strictly in the future
- do NOT add a scheduler

Important:
Do not make an already-approved task fail later merely because time passed while approval was pending.
Therefore:
- static date parsing/order validation belongs in CREATE_TASK normalization
- "reminder is in the future" validation belongs at proposal creation and CREATE_TASK approval revision boundaries
- do not re-reject an already approved payload during final execution solely because reminderAt became past after approval wait

## 4) Cross-field validation
Backend CREATE_TASK normalization must reject:
- startDate > dueDate when both exist
- reminderAt > dueDate when both exist

Use clear AppError 400 messages.

Frontend Smart Task must mirror these rules:
- estimatedHours invalid => block Review & Create
- invalid start date => block
- invalid reminder => block
- reminder not future => block
- startDate > dueDate => block
- reminderAt > dueDate => block
- blank optional fields => valid

Add ONE compact local validation message inside Advanced details.
Do not silently just return from submit with no explanation.

The Review & Create disabled state must include advanced validity in addition to existing basic required fields.

## 5) Labels / copy
Use:
- toggle collapsed: AR `تفاصيل إضافية`, EN `Advanced details`
- expanded hide: AR `إخفاء التفاصيل الإضافية`, EN `Hide advanced details`
- Estimated hours: AR `الساعات المتوقعة`
- Start date: AR `تاريخ البداية`
- Reminder time: AR `وقت التذكير`, EN `Reminder time`

Approval display should use the same user-facing labels when those values are present.

## 6) Prompt path remains Phase 6 only
Keep:
`submitSmartTask -> smartTaskPrompt -> sendMessage(... metadata.intent=CREATE_TASK)`

Append only valid advanced values:
- Estimated hours: <normalized number>
- Start date: <ISO>
- Reminder at: <ISO>

Do not emit invalid/blank advanced lines.
No structured direct submission.

## 7) Backend proposal/revision/execution
Preserve the existing pipeline already added in 0bb1b41:
- tool schema
- action draft allowlist
- CREATE_TASK normalizer
- action confirmation revision fields
- approval detail
- execution persistence

Correct it so:
- normalized CREATE_TASK payload returns estimatedHours/startDate/reminderAt
- estimatedHours max 999 and rounded max 2 decimals
- start/due and reminder/due ordering enforced
- reminder-future validation is enforced when proposal is created and when pending CREATE_TASK approval is revised
- final approved execution persists the already-approved advanced fields without introducing a new scheduler

RBAC, project target, assignee target, approval requirement, board/list behavior stay unchanged.

## 8) Tests
Add/update behavior tests covering:
- estimatedHours 2.5 valid
- estimatedHours decimal normalization max 2 decimals
- estimatedHours 0 rejected
- estimatedHours >999 rejected
- estimatedHours NaN/non-finite rejected
- all advanced blank => null and valid
- start date YYYY-MM-DD -> local 09:00 ISO
- local start-date display roundtrip
- nonexistent start date rejected
- reminder datetime-local -> ISO -> local display roundtrip
- reminder in past rejected at proposal/revision validation
- startDate > dueDate rejected
- reminderAt > dueDate rejected
- valid start/reminder before due accepted
- basic Smart Task untouched with advanced closed remains valid
- no external AI/network dependency

## Preserve / forbidden
Preserve:
- Phase 1-5 behavior
- advanced section default closed
- current approval flow mandatory
- protected projectId/assigneeId revision boundaries
- existing Task fields / no migration
- no reminder scheduler
- no Phase 7

Do not:
- reset/revert unrelated work
- refactor unrelated Ramzy code
- stage untracked backup files

## Verification
- frontend build PASS
- backend Ramzy tests PASS
- estimatedHours max 999 everywhere
- start date is date-only in Smart Task + approval revision UI
- start date stored local 09:00 ISO
- reminder future validated at proposal/revision boundary
- due ordering enforced backend + frontend
- compact advanced error visible
- blank advanced never blocks
- approval still mandatory
- Phase 7 structured submission absent

## Workflow
Continue from local commit 0bb1b41.
Create ONE NEW commit.
COMMIT ONLY.
DO NOT PUSH.

## Return only
PATCH=RAMZY-SMART-TASK-V3-PHASE-6-R1-VALIDATION-AND-LOCAL-DATE-CORRECTION
PASS/FAIL=
BASELINE_COMMIT=0bb1b41
R1_NEW_COMMIT=
ESTIMATED_MAX_999=
ESTIMATED_STEP_025=
ESTIMATED_ROUND_2DP=
START_DATE_DATE_ONLY=
START_DATE_LOCAL_0900_ISO=
REMINDER_FUTURE_PROPOSAL_REVISION=
START_AFTER_DUE_REJECTED=
REMINDER_AFTER_DUE_REJECTED=
ADVANCED_ERROR_VISIBLE=
BLANK_ADVANCED_VALID=
APPROVAL_REQUIRED=YES
REMINDER_SCHEDULER_ADDED=NO
PHASE7_STRUCTURED_SUBMISSION=NO
FRONTEND_BUILD=
BACKEND_TEST=
UNTRACKED_BACKUPS_UNSTAGED=
ERROR=
