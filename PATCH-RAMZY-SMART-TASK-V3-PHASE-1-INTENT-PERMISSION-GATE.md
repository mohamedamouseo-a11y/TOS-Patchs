# PATCH: RAMZY SMART TASK V3 — PHASE 1 — INTENT + PERMISSION GATE

## Goal
Make Smart Task entry deterministic and permission-safe before any later UX redesign.

This phase MUST NOT redesign the Smart Task card, project picker, assignee picker, review flow, approval flow, or execution logic.

## Current verified behavior
The current frontend has two different task-create intent paths inside `frontend/src/components/RamzyAssistant.jsx`:

1. `ramzyIsTaskCreationIntent(content)`
   - opens the local Smart Task composer via `startSmartTask(content)`
   - currently matches only a narrower set of phrases.

2. `detectSmartTaskCreateIntent(content)`
   - can still classify broader phrases as CREATE_TASK
   - sends `metadata.intent = "CREATE_TASK"` to the SSE backend
   - does NOT necessarily open the local Smart Task composer.

This creates inconsistent behavior where phrases such as Arabic task-create variants can be recognized as CREATE_TASK by the backend path while the Smart Task UI does not open.

The backend already exposes `/api/agent/status` and returns `executionControl` from `resolveRamzyExecutionControl()`.
The control includes:
- `state`
- `canExecute`
- `permissionGranted`
- `emergencyLocked`
- `approvalActionsEnabled`
- `agentEnabled`
- `roleAllowed`
- localized messages

The permission key is currently `ramzy.execute_actions`.

Server-side task creation authorization must remain authoritative. Project-specific create access is already enforced later by `assertAgentTaskCreateAccess()` and TOS project/board RBAC.

## Scope

### A. Unify CREATE_TASK intent detection
Replace the split frontend logic with ONE canonical task-create intent detector used for BOTH:
- opening the Smart Task composer
- setting structured metadata intent when needed

Do not keep two independent regex rule sets that can disagree.

The canonical detector must recognize explicit task creation phrases including common Arabic variations such as:
- إنشاء مهمة
- انشاء مهمة
- أنشئ مهمة
- انشئ مهمة
- انشي مهمة
- اعمل مهمة
- اعمل تاسك
- عايز اعمل مهمة
- عاوز اعمل تاسك
- محتاج اعمل مهمة
- مهمة جديدة
- مهمة ذكية

And English variants such as:
- create task
- create a task
- create new task
- add task
- make task
- new task

It must NOT classify search/query/update phrases as create intent, for example:
- دور على مهمة تصميم
- فين مهمة التصميم؟
- ايه حالة مهمة التصميم؟
- لخص التاسكات
- عدّل مهمة التصميم
- غيّر موعد المهمة

The canonical helper should ideally return a normalized result such as:

```js
{
  intent: "CREATE_TASK" | null,
  title: "..." | ""
}
```

or equivalent, so intent detection and title extraction cannot diverge.

### B. Fix title extraction consistency
Use the same normalization rules for the optional title embedded in the user's command.

Examples:
- `إنشاء مهمة` -> CREATE_TASK, no title -> open at TITLE
- `انشي مهمة` -> CREATE_TASK, no title -> open at TITLE
- `اعمل تاسك تصميم بوست رمضان` -> CREATE_TASK, title=`تصميم بوست رمضان` -> open at PROJECT
- `create task homepage QA` -> CREATE_TASK, title=`homepage QA` -> open at PROJECT

Generic action phrases must NEVER become the task title:
- `مهمة ذكية`
- `مهمة جديدة`
- `smart task`
- `new task`

### C. Permission gate BEFORE opening Smart Task UI
Before opening the Smart Task composer for explicit CREATE_TASK intent, use the server-provided Ramzy execution control already returned by `/api/agent/status`.

Rules:
- If Ramzy itself is unavailable for the user, preserve current Ramzy availability behavior.
- If `executionControl.canExecute === true`, allow Smart Task composer to open.
- If execution is blocked by `PERMISSION_DENIED`, `ROLE_NOT_ALLOWED`, `EMERGENCY_LOCK`, `APPROVALS_DISABLED`, or `AGENT_DISABLED`, do NOT open Smart Task composer.
- Show a concise in-chat/user-visible explanation based on the server-provided localized message. Do not invent a new permission result in the frontend.
- Do not add a permanent dashboard button or extra menu.

Important:
Frontend gating is UX only. Server-side authorization MUST remain authoritative.
Do not weaken or bypass:
- `ramzy.execute_actions`
- `assertRamzyActionExecutionAllowed()`
- `assertAgentTaskCreateAccess()`
- project/workspace/board RBAC
- approval requirements

### D. No project-level permission guessing in Phase 1
At this phase, do NOT try to determine which specific projects the user may create tasks in before the project is selected.
That belongs to Phase 3.

Phase 1 only answers:
"Can this user enter an executable Smart Task flow at all?"

Project-specific CREATE_TASK permission remains validated later by the existing backend.

### E. Preserve normal chat behavior
If the text is NOT an explicit task creation intent:
- send it through normal Ramzy chat unchanged
- do not force CREATE_TASK metadata
- do not open Smart Task composer

### F. Preserve current Smart Task UI
Do not redesign the existing Smart Task UI in this phase.
Do not change:
- current TITLE / PROJECT / DUE / PRIORITY / ASSIGNEE / REVIEW flow
- project picker UI
- archived project UI
- assignee UI
- approval cards
- execution status UI

These are later phases.

## Suggested files to inspect
- `frontend/src/components/RamzyAssistant.jsx`
- `frontend/src/lib/api.js`
- `backend/src/routes/agent.routes.js`
- `backend/src/agency-operator/services/ramzyExecutionControl.service.js`
- `backend/src/agency-operator/policies/agentAccess.service.js`

Only change backend files if required for a clean, authoritative permission capability response. Prefer reusing the existing `/api/agent/status` executionControl instead of duplicating permission logic.

## Regression tests
Test at minimum:

### Allowed user
1. `إنشاء مهمة`
   - Smart Task opens
   - TITLE step
2. `انشي مهمة`
   - Smart Task opens
   - TITLE step
3. `أنشئ مهمة تصميم بوست`
   - Smart Task opens
   - title = `تصميم بوست`
   - starts at PROJECT
4. `اعمل تاسك مراجعة الصفحة الرئيسية`
   - Smart Task opens with extracted title
5. `create task homepage QA`
   - Smart Task opens with extracted title
6. `مهمة جديدة`
   - Smart Task opens
   - no generic title stored

### Non-create queries
7. `دور على مهمة تصميم`
   - normal Ramzy chat/search
   - Smart Task does NOT open
8. `ايه حالة مهمة التصميم؟`
   - normal Ramzy query
9. `غيّر موعد المهمة`
   - not CREATE_TASK

### Blocked user
10. User without `ramzy.execute_actions`
    - explicit CREATE_TASK phrase does NOT open composer
    - concise permission message shown
    - no bypass
11. Emergency lock / approvals disabled state
    - Smart Task does NOT open
    - correct server-provided message shown

## Acceptance criteria
- ONE canonical frontend CREATE_TASK intent detector
- No disagreement between local Smart Task UI intent and SSE CREATE_TASK metadata intent
- Explicit create-task phrases open Smart Task consistently for allowed users
- Search/query phrases do not trigger Smart Task
- Generic phrases are not stored as titles
- Users blocked from Ramzy execution cannot enter Smart Task creator
- Existing server-side RBAC remains unchanged and authoritative
- Approval remains mandatory
- No task is created automatically
- No permanent Smart Task button is introduced

## QA / deployment
- Build frontend
- Run existing backend tests if backend touched
- Test with at least one allowed user and one execution-blocked user
- Validate live TOS behavior
- Deploy using the current atomic deployment flow
- Commit and push the exact source changes

## Required final report

```text
PATCH=RAMZY-SMART-TASK-V3-PHASE-1-INTENT-PERMISSION-GATE
PASS/FAIL=<result>
CANONICAL_CREATE_INTENT_DETECTOR=YES/NO
DUPLICATE_INTENT_LOGIC_REMOVED=YES/NO
AR_CREATE_VARIANTS_PASS=YES/NO
EN_CREATE_VARIANTS_PASS=YES/NO
SEARCH_FALSE_POSITIVES=0/<count>
GENERIC_TASK_PHRASE_USED_AS_TITLE=YES/NO
EXECUTION_PERMISSION_GATE=YES/NO
BLOCKED_USER_SMART_TASK_OPENED=YES/NO
SERVER_RBAC_CHANGED=NO
PROJECT_RBAC_CHANGED=NO
APPROVAL_LOGIC_CHANGED=NO
AUTO_CREATE_WITHOUT_APPROVAL=NO
ALLOWED_USER_TEST=PASS/FAIL
BLOCKED_USER_TEST=PASS/FAIL
FRONTEND_BUILD=PASS/FAIL
BACKEND_TESTS=PASS/FAIL/NOT_CHANGED
LIVE_DEPLOY=PASS/FAIL
SOURCE_COMMIT=<sha>
PUSH=YES/NO
FILES_CHANGED=<paths>
ERROR=<NONE or exact error>
```
