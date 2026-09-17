# PATCH — RAMZY SMART TASK V3 — PHASE 1 R2 RUNTIME CORRECTION

## Baseline
TOS main currently includes R1 commit `b267349d46b1a98c581e6cccf0d962f9e3dc4218`.

## Why R2 is required
GitHub source verification of `frontend/src/components/RamzyAssistant.jsx` shows the R1 rename was incomplete:

- New constants exist:
  - `SMART_TASK_INVOCATION_ONLY_PHRASES`
  - `SMART_TASK_NOT_CREATE_PHRASES_SET`
  - `SMART_TASK_NOT_CREATE_PATTERNS`
- But `resolveSmartTaskIntent()` still references removed names:
  - `SMART_TASK_GENERIC_SEARCH_PHRASES`
  - `SMART_TASK_NOT_CREATE_PHRASES`
- Legacy duplicate helpers still remain:
  - `ramzyIsTaskCreationIntent()`
  - `ramzyTaskTitleFromIntent()`
- `startSmartTask(intentText)` still re-parses the raw text through the legacy title helper instead of consuming the canonical parser result.
- Blocked-user handling writes `smartTask.step = "ERROR"`; the current Smart Task renderer has no verified ERROR branch. Use the existing global/compact error presentation instead of inventing a hidden Smart Task state.

Build success is not sufficient because undefined identifiers can survive bundling and fail at runtime.

## Required correction

### 1. One canonical parser, actually one
`resolveSmartTaskIntent(text)` is the only create-task parser.

It must use exactly the new collections:

```js
SMART_TASK_INVOCATION_ONLY_PHRASES
SMART_TASK_NOT_CREATE_PHRASES_SET
SMART_TASK_NOT_CREATE_PATTERNS
```

Remove all references to:

```js
SMART_TASK_GENERIC_SEARCH_PHRASES
SMART_TASK_NOT_CREATE_PHRASES
```

Remove obsolete helpers if unused:

```js
ramzyIsTaskCreationIntent
ramzyTaskTitleFromIntent
```

### 2. Parser behavior
Invocation-only phrases:

- `مهمة جديدة`
- `مهمة ذكية`
- `new task`
- `smart task`

must return:

```js
{ isCreateTask: true, title: null }
```

Explicit create commands with optional prefixes must work:

- `إنشاء مهمة` -> create, null title
- `انشي مهمة` -> create, null title
- `عايز اعمل مهمة` -> create, null title
- `عاوز انشئ مهمة تصميم بوست` -> create, title=`تصميم بوست`
- `محتاج اعمل تاسك مراجعة الموقع` -> create, title=`مراجعة الموقع`
- `create task homepage QA` -> create, title=`homepage QA`

Non-create phrases stay normal chat:

- `دور على مهمة تصميم`
- `فين مهمة التصميم`
- `ايه حالة مهمة التصميم`
- `غير موعد المهمة`
- `عدل مهمة التصميم`
- `احذف مهمة`

### 3. Start Smart Task from canonical result
Do not pass the raw command into another parser.

Change Smart Task start API to consume canonical title, e.g. conceptually:

```js
startSmartTask({ title: intent.title })
```

or equivalent.

State must be initialized as:

- title present -> `PROJECT`
- title null -> `TITLE`

The generic invocation phrase itself must never be stored in `smartTask.title`.

### 4. Permission-denied UX
When create intent is detected and:

```js
status?.executionControl?.canExecute !== true
```

Do not open Smart Task and do not send CREATE_TASK.

Show the existing localized server reason immediately using an already-rendered error/status mechanism.

Use:

```js
status.executionControl.messageAr
status.executionControl.messageEn
```

Do not set a synthetic Smart Task step unless an explicit renderer for that step exists.

### 5. Preserve security / scope
Do not change:

- `ramzy.execute_actions`
- `assertRamzyActionExecutionAllowed()`
- `assertAgentTaskCreateAccess()`
- project/workspace/board RBAC
- approval logic
- task creation business logic
- project picker
- assignee picker
- Smart Task visual redesign

Do not start Phase 2.

## Runtime verification
Do not report success from unit-style parser output alone.

Verify in the actual rendered Ramzy flow:

1. `مهمة جديدة` -> Smart Task opens TITLE and title is empty.
2. `عاوز انشئ مهمة تصميم بوست` -> Smart Task opens PROJECT and title is exactly `تصميم بوست`.
3. `دور على مهمة تصميم` -> Smart Task does not open.
4. blocked user -> Smart Task does not open and localized reason is visibly rendered.
5. Browser console has no `ReferenceError` from Smart Task intent detection.

Also grep/source-check that obsolete identifiers/functions are gone.

## Delivery
- Backups outside repository.
- UTF-8 safe editing.
- Frontend build.
- Authenticated live runtime test.
- Atomic deploy.
- New commit after `b267349`.
- Push main.
- Production must match new commit.

## Required return

```text
PATCH=RAMZY-SMART-TASK-V3-PHASE-1-R2-RUNTIME-CORRECTION
PASS/FAIL=<result>
R2_NEW_COMMIT=<sha>
CANONICAL_PARSER_COUNT=1
OBSOLETE_IDENTIFIER_REFERENCES=0
LEGACY_CREATE_HELPERS_REMAIN=NO
START_SMART_TASK_REPARSES_RAW_INTENT=NO
INVOCATION_ONLY_RUNTIME_PASS=YES/NO
PREFIXED_CREATE_RUNTIME_PASS=YES/NO
NON_CREATE_RUNTIME_PASS=YES/NO
BLOCKED_USER_SMART_TASK_OPENED=YES/NO
BLOCKED_USER_REASON_VISIBLE=YES/NO
SMART_TASK_INTENT_REFERENCE_ERROR=YES/NO
FRONTEND_BUILD=PASS/FAIL
LIVE_RUNTIME_QA=PASS/FAIL
LIVE_DEPLOY=PASS/FAIL
PRODUCTION_MATCHES_R2_COMMIT=YES/NO
SERVER_RBAC_CHANGED=NO
PROJECT_RBAC_CHANGED=NO
APPROVAL_LOGIC_CHANGED=NO
FILES_CHANGED=<paths>
ERROR=<NONE or exact error>
```
