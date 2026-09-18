# PATCH-RAMZY-SMART-TASK-V3-PHASE-6-OPTIONAL-ADVANCED-DETAILS

Baseline main commit:
1904a3882a3014f5e7c9c117320bb969197f8894

## Goal
Implement Phase 6 only: optional advanced task details inside the existing single Smart Task card.

Keep the fast/basic flow unchanged. Advanced details must be collapsed by default and entirely optional.

Phase 6 fields:
- estimatedHours
- startDate
- reminderAt

Do not add service/template/department/checklist/dependency/watcher/internal-note features in this phase.

## 1) Smart Task UI — collapsed optional section
Inside the existing Smart Task card, after the basic assignee/priority/due controls and before the footer, add one compact toggle:

AR: `تفاصيل إضافية`
EN: `Advanced details`

Rules:
- collapsed by default for every new Smart Task
- opening/closing it never clears values
- no modal and no second card
- preserve the existing compact one-card UX
- no advanced field is required

Fields when expanded:

### Estimated hours
AR: `الساعات المتوقعة`
EN: `Estimated hours`
- native number input
- step 0.25
- valid range: > 0 and <= 999
- blank => null
- invalid value must not enter submission

### Start date
AR: `تاريخ البداية`
EN: `Start date`
- native date input
- blank => null
- convert selected LOCAL calendar date to 09:00 local, then ISO
- display the stored ISO back as the same LOCAL calendar date
- invalid/nonexistent date => null
- if dueDate exists, startDate must be <= dueDate

### Reminder
AR: `وقت التذكير`
EN: `Reminder time`
- native datetime-local input
- blank => null
- convert local datetime to ISO
- display ISO back in local datetime form
- invalid datetime => null
- reminder must be in the future at submission time
- if dueDate exists, reminderAt must be <= dueDate

Show one compact local advanced-validation error when an entered advanced value is invalid.
The Review & Create button must be disabled only when an entered advanced value is invalid; blank optional fields remain valid.

## 2) Smart Task draft + current prompt path
Extend the Smart Task draft with:
- advancedOpen: false
- estimatedHours: null/blank
- startDate: null
- reminderAt: null

The current Phase 6 submission MUST remain the existing:
`submitSmartTask -> smartTaskPrompt -> sendMessage(... metadata.intent=CREATE_TASK)`

Do NOT implement Phase 7 structured direct submission.

When an advanced field has a valid value, append explicit machine-readable lines to the current generated CREATE_TASK prompt:
- `Estimated hours: <number>`
- `Start date: <ISO>`
- `Reminder at: <ISO>`

Use localized labels in the Arabic prompt but keep exact ISO/number values.
Do not append lines for blank fields.

## 3) CREATE_TASK action contract
The advanced values must survive the current model/tool/proposal/approval/execution path.

Locate the canonical CREATE_TASK tool/action input schema already used by Ramzy and add ONLY these optional fields:
- `estimatedHours?: number|null`
- `startDate?: string|null`
- `reminderAt?: string|null`

Do not create a second CREATE_TASK implementation.

In `normalizeTaskActionPayload("CREATE_TASK", ...)`:
- preserve all existing title/description/priority/dueDate/assignee behavior
- estimatedHours:
  - blank/null/undefined => null
  - Number(...)
  - finite, >0, <=999
  - otherwise AppError 400
  - normalize to max 2 decimal places
- startDate:
  - blank/null/undefined => null
  - valid date required
  - normalize to ISO
- reminderAt:
  - blank/null/undefined => null
  - valid date required
  - normalize to ISO
- if startDate + dueDate: reject when startDate > dueDate
- if reminderAt + dueDate: reject when reminderAt > dueDate
- reject reminderAt that is already in the past when proposal is created
- return the advanced fields in the normalized CREATE_TASK payload

Do not loosen existing RBAC, project checks, assignee checks, or approval requirements.

## 4) Approval must preserve and show advanced values
The existing approval flow remains mandatory.

Ensure advanced fields survive:
- CREATE_TASK proposal payload
- confirmation metadata/revision normalization
- approval revisions where CREATE_TASK revision fields are supported
- final approved execution

Extend CREATE_TASK revision fields to allow:
- estimatedHours
- startDate
- reminderAt
in addition to the existing editable fields.

In the existing CREATE_TASK approval display/impact detail, show advanced values only when present:
- Estimated hours / الساعات المتوقعة
- Start / البداية
- Reminder / التذكير

Do not expose internal IDs or unrelated metadata.

## 5) Final task persistence
In the existing approved CREATE_TASK execution only, persist:
- `estimatedHours`
- `startDate`
- `reminderAt`

Use the existing Task model fields.
Do not add a Prisma migration: these columns already exist.

Do not invent a new reminder scheduler/notification system in Phase 6.
This phase stores the existing `reminderAt` task field only.

Preserve all current creation behavior:
- board/list resolution
- status
- serviceType
- dueDate/slaDueAt behavior
- assignee legacy + TaskAssignee behavior
- createdBy
- events/sync

## 6) Validation helpers
Prefer small pure helpers for local date/datetime conversions and advanced validation so they can be behavior-tested.

Do not use UTC `.split("T")[0]` for local date display.

Tests must cover at minimum:
- estimatedHours valid normalization
- estimatedHours <=0 / >999 / NaN rejected
- local start-date roundtrip
- datetime-local reminder roundtrip
- startDate > dueDate invalid
- reminderAt > dueDate invalid
- past reminder invalid
- all three blank => valid/null
- CREATE_TASK normalized payload preserves advanced values
- approval revision preserves them
- execution maps them to existing Task fields
- basic Smart Task behavior remains valid when advanced section untouched

No external AI/network dependency in these tests.

## 7) Preserve / forbidden
Preserve exactly:
- Phase 1 deterministic CREATE_TASK intent
- Phase 3 project permission gate
- Phase 4 authorized assignee source
- Phase 5 AI description/workload/CUSTOM due/URGENT
- AUTO/NONE behavior
- current mandatory approval flow
- current prompt-based Smart Task submission

DO NOT:
- implement Phase 7
- send a structured direct create request from the card
- add new DB columns/migration
- add checklist/dependencies/watchers/service/template/department/internalNotes
- add a reminder scheduler
- refactor unrelated Ramzy code
- stage untracked backup files

## Verification
- frontend build PASS
- backend Ramzy tests PASS
- basic Smart Task with advanced section untouched behaves exactly as before
- advanced toggle defaults closed
- optional blank fields never block submit
- invalid entered advanced values block submit
- advanced fields survive prompt -> action payload -> approval -> approved task persistence
- approval remains mandatory
- no Phase 7 structured submission
- only intended source/test files staged

## Workflow
Implement against current main baseline 1904a388.
Build/test.
Create ONE NEW COMMIT.
COMMIT ONLY.
DO NOT PUSH.

## Return only
PATCH=RAMZY-SMART-TASK-V3-PHASE-6-OPTIONAL-ADVANCED-DETAILS
PASS/FAIL=
BASELINE_COMMIT=1904a38
PHASE6_NEW_COMMIT=
ADVANCED_DEFAULT_CLOSED=
ESTIMATED_HOURS=
START_DATE_LOCAL_ISO=
REMINDER_LOCAL_ISO=
INVALID_ADVANCED_BLOCKS_SUBMIT=
BLANK_ADVANCED_OPTIONAL=
CREATE_TASK_SCHEMA_EXTENDED=
NORMALIZER_EXTENDED=
APPROVAL_PRESERVES_ADVANCED=
APPROVAL_SHOWS_ADVANCED=
EXECUTION_PERSISTS_ADVANCED=
REMINDER_SCHEDULER_ADDED=NO
PHASE7_STRUCTURED_SUBMISSION=NO
RBAC_CHANGED=NO
APPROVAL_REQUIRED=YES
FRONTEND_BUILD=
BACKEND_TEST=
UNTRACKED_BACKUPS_UNSTAGED=
ERROR=
