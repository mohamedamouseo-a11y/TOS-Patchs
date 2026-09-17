# PATCH — RAMZY SMART TASK V3 — PHASE 1 R3 FINAL RUNTIME FIX

## Baseline
Current TOS main HEAD verified as `10c07cf4249d7b8044f740b09425726bee87fd07`.

## Verified source defects
`frontend/src/components/RamzyAssistant.jsx` currently has these Phase 1 defects:

1. `resolveSmartTaskIntent()` loops over `SMART_TASK_INVOCATION_ONLY_PHRASES` and returns `isCreateTask:false` when a phrase matches. This is the opposite of the required behavior. Invocation-only phrases must return `isCreateTask:true, title:null`.
2. `SMART_TASK_CREATE_AR_VERBS` does not support the required prefixes `عايز/عاوز/محتاج`, so prefixed Arabic commands can miss CREATE_TASK.
3. Legacy helpers `ramzyIsTaskCreationIntent()` and `ramzyTaskTitleFromIntent()` are still present.
4. `startSmartTask(intentText = "")` reads `parsedIntent?.title`, but `parsedIntent` is not defined in that function. Calling Smart Task can therefore raise a runtime `ReferenceError`.
5. Blocked CREATE_TASK currently uses a synthetic `smartTask.step="ERROR"`, while the Smart Task renderer has no ERROR step. Use the existing visible Ramzy error/status mechanism instead.

## Required final Phase 1 behavior

### Canonical parser only
Keep exactly one CREATE_TASK parser: `resolveSmartTaskIntent()`.
Remove the two legacy helpers if unused.

### Invocation-only phrases
These must OPEN Smart Task TITLE and must never become titles:
- `مهمة جديدة`
- `مهمة ذكية`
- `new task`
- `smart task`

Expected parser result:
`{ isCreateTask: true, title: null }`

Do exact normalized invocation matching before negative/search matching. Do not reject these phrases as search phrases.

### Prefixed Arabic create phrases
Must work:
- `عايز اعمل مهمة` => CREATE_TASK, title=null
- `عاوز انشئ مهمة تصميم بوست` => CREATE_TASK, title=`تصميم بوست`
- `محتاج اعمل تاسك مراجعة الموقع` => CREATE_TASK, title=`مراجعة الموقع`

### Other explicit create examples
- `إنشاء مهمة` => TITLE
- `انشي مهمة` => TITLE
- `أنشئ مهمة تصميم بوست` => PROJECT, title=`تصميم بوست`
- `اعمل تاسك مراجعة الصفحة` => PROJECT, title=`مراجعة الصفحة`
- `create task homepage QA` => PROJECT, title=`homepage QA`

### Non-create protection
Must stay normal Ramzy chat:
- `دور على مهمة تصميم`
- `فين مهمة التصميم`
- `ايه حالة مهمة التصميم`
- `غير موعد المهمة`
- `عدل مهمة التصميم`
- `احذف مهمة`
- `انقل مهمة`
- `لخص التاسكات`

### startSmartTask contract
Change the function to consume the parser result directly, for example conceptually:
`startSmartTask(parsedIntent)`
Then derive title only from `parsedIntent?.title`.
Do not reparse raw text.
No undefined variable may remain.

### Permission gate
If `status.executionControl.canExecute !== true`:
- do not open Smart Task
- do not send CREATE_TASK
- do not create synthetic Smart Task ERROR state
- immediately show the existing localized server reason through the already-rendered Ramzy error/status mechanism (`setError(...)` or equivalent visible existing UI)
- Arabic uses `messageAr`, English uses `messageEn`

Do not change any RBAC or approval behavior.

## Must NOT change
- `ramzy.execute_actions`
- `assertRamzyActionExecutionAllowed()`
- `assertAgentTaskCreateAccess()`
- project/workspace/board RBAC
- approval flow
- task creation business logic
- project picker UX
- assignee picker UX
- Phase 2+

## Verification
Build-only verification is not sufficient.

Required source checks:
- `CANONICAL_PARSER_COUNT=1`
- `LEGACY_CREATE_HELPERS_REMAIN=NO`
- `UNDEFINED_PARSED_INTENT_REFERENCE=NO`
- `INVOCATION_ONLY_REJECTED_AS_NON_CREATE=NO`

Required authenticated live runtime checks:
1. `مهمة جديدة` opens TITLE.
2. `مهمة ذكية` opens TITLE.
3. `عاوز انشئ مهمة تصميم بوست` opens PROJECT with exact extracted title.
4. `محتاج اعمل تاسك مراجعة الموقع` opens PROJECT with exact extracted title.
5. `create task homepage QA` opens PROJECT with exact extracted title.
6. `دور على مهمة تصميم` does not open Smart Task.
7. blocked user does not open Smart Task and sees localized permission reason.
8. Browser console has no Smart Task ReferenceError.

After fixing:
- frontend build
- authenticated live runtime QA
- atomic deploy
- new commit after `10c07cf`
- push main
- verify production source matches new commit
- clean worktree

## Required report

PATCH=RAMZY-SMART-TASK-V3-PHASE-1-R3-FINAL-RUNTIME-FIX
PASS/FAIL=<result>
BASELINE_COMMIT=10c07cf
R3_NEW_COMMIT=<sha>
CANONICAL_PARSER_COUNT=1
LEGACY_CREATE_HELPERS_REMAIN=NO
UNDEFINED_PARSED_INTENT_REFERENCE=NO
INVOCATION_ONLY_CREATE_PASS=YES/NO
INVOCATION_ONLY_USED_AS_TITLE=YES/NO
PREFIXED_ARABIC_CREATE_PASS=YES/NO
NON_CREATE_REGRESSION_PASS=YES/NO
BLOCKED_USER_SMART_TASK_OPENED=YES/NO
BLOCKED_USER_REASON_VISIBLE=YES/NO
SMART_TASK_INTENT_REFERENCE_ERROR=YES/NO
FRONTEND_BUILD=PASS/FAIL
LIVE_RUNTIME_QA=PASS/FAIL
LIVE_DEPLOY=PASS/FAIL
PRODUCTION_MATCHES_R3_COMMIT=YES/NO
WORKTREE_CLEAN=YES/NO
SERVER_RBAC_CHANGED=NO
PROJECT_RBAC_CHANGED=NO
APPROVAL_LOGIC_CHANGED=NO
FILES_CHANGED=<paths>
ERROR=<NONE or exact error>
