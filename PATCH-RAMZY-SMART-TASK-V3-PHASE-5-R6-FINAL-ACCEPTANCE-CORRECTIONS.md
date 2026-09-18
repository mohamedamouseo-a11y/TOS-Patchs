# PATCH-RAMZY-SMART-TASK-V3-PHASE-5-R6-FINAL-ACCEPTANCE-CORRECTIONS

Baseline local commit: 5357dbebfb3eafa5b227a5325cb30928bc25c707

Do not push yet.

## Verified acceptance gaps

### 1) Workload recommendation must reuse authorized visible-task scope
Current Phase 5 workload code queries open tasks directly by projectId and returns a recommendation user object.

Required:
- reuse the existing canonical task visibility helper/policy used by Ramzy task queries, e.g. `buildAgentTaskVisibilityWhere`
- build visibility for `req.user` and the selected project
- task query must combine:
  - exact `projectId`
  - `archivedAt: null`
  - status not in `DONE/CANCELLED`
  - the authorized task visibility scope
- candidate IDs must remain restricted to the already-authorized Phase 4 assignee list
- count assignment from both legacy `task.assigneeId` and `task.assignees`
- dedupe the same task/person
- score:
  - active = 1
  - urgent = +2
  - overdue = +3
- if fewer than 2 authorized candidates => recommendation null
- if the lowest score is tied => recommendation null
- otherwise return only:
  `recommendedAssigneeId: string|null`
- never return workload/task details

Frontend:
- keep recommendation as an ID, not a trusted user object
- accept the ID only if it exists in the returned `smartTaskAssignees`
- resolve the displayed recommendation from that authorized list
- clicking the suggestion selects the exact existing user
- never auto-select
- clear recommendation before each assignee reload/project change

### 2) AI description must use current description + requested language
Current generator only receives title/user.

Required request body:
`{ projectId, title, description?, language }`

Backend route:
- keep exact project authorization with `assertAgentTaskCreateAccess`
- trim/cap title and description
- normalize language to `ar` or `en`
- call `generateTaskDescription` with title + current description + language
- no template/static fallback
- provider/config/generation failure must propagate non-2xx
- empty model text must also be treated as failure, not `200 {suggestion:null}`
- return plain-text suggestion <= 4000 chars

`generateTaskDescription`:
- use current configured model/provider only
- no tools/actions/side effects
- prompt must write or improve a concise actionable task description
- preserve useful facts already present in current description
- answer in the requested language
- do not invent people, dates, IDs, assignee, priority, credentials, acceptance criteria, or unsupported facts

Frontend:
- send exact projectId
- send trimmed title
- send current description
- send current UI language
- keep description error isolated
- failure must preserve current description and all other draft fields

### 3) CUSTOM due date must display the LOCAL calendar date
Current write path stores local 17:00 as ISO correctly, but the native date input value is derived with `.split("T")[0]`, which can show the wrong calendar date after timezone conversion.

Required:
- add a tiny helper that converts stored ISO to local `YYYY-MM-DD` using:
  - `getFullYear()`
  - `getMonth()`
  - `getDate()`
- use that helper for the native date input value
- keep input -> local date at 17:00 -> `toISOString()`
- invalid/nonexistent/past date => do not store a dueDate
- `CUSTOM` with no valid dueDate must keep submit disabled
- `NONE` => `dueDate:null`
- keep all presets unchanged

### 4) Keep URGENT and CUSTOM labels explicit
Ensure:
- `URGENT: { ar: "عاجلة", en: "Urgent" }`
- `CUSTOM: { ar: "تاريخ آخر", en: "Custom date" }`

### 5) Tests must validate behavior, not only source regex
Existing source-regex guards may remain, but add focused executable unit tests for pure logic where practical:
- workload ranking unique lowest
- workload tie => null
- fewer than 2 candidates => null
- recommendation ID membership rule
- custom local date parse validity / invalid date
- no external AI/network dependency in tests

If helpers need extraction/export for testing, keep them small and local to Phase 5 behavior.

## Preserve
- Phase 1 canonical parser
- Phase 3 project RBAC
- Phase 4 assignee authorization
- AUTO/NONE
- current approval flow
- current prompt-based submit path
- no Phase 6/7
- no structured direct submission
- no unrelated refactor
- do not stage any untracked backup files

## Verification
- frontend build PASS
- backend Ramzy tests PASS
- no unscoped direct workload query remains
- workload response field is `recommendedAssigneeId`
- recommendation ID is always null or a returned authorized user ID
- AI request carries description + language
- AI empty output is non-2xx
- CUSTOM input displays local calendar date
- CUSTOM invalid/empty blocks submit
- `git diff --cached --name-only` contains only intended Phase 5 source/test files
- untracked backups remain unstaged

## Workflow
Continue from local commit:
`5357dbebfb3eafa5b227a5325cb30928bc25c707`

Implement only these acceptance corrections.

Build/test, then create ONE NEW commit.

COMMIT ONLY.
DO NOT PUSH.

## Return only
PATCH=RAMZY-SMART-TASK-V3-PHASE-5-R6-FINAL-ACCEPTANCE-CORRECTIONS
PASS/FAIL=
BASELINE_COMMIT=5357dbe
R6_NEW_COMMIT=
VISIBLE_TASK_SCOPE_REUSED=
WORKLOAD_RESPONSE_ID_ONLY=
AUTHORIZED_ONLY=
TIE_RETURNS_NULL=
LESS_THAN_2_RETURNS_NULL=
AUTO_ASSIGNS=NO
AI_DESCRIPTION_CONTEXT_USED=
AI_LANGUAGE_USED=
AI_EMPTY_OUTPUT_NON_2XX=
AI_NO_TOOLS=
CUSTOM_LOCAL_DATE_DISPLAY=
CUSTOM_LOCAL_1700_ISO=
CUSTOM_INVALID_BLOCKED=
URGENT_LOCALIZED=
CUSTOM_LOCALIZED=
BEHAVIOR_TESTS_ADDED=
FRONTEND_BUILD=
BACKEND_TEST=
UNTRACKED_BACKUPS_UNSTAGED=
ERROR=
