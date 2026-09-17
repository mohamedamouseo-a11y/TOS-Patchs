# PATCH-RAMZY-SMART-TASK-V3-PHASE-1-R1-INTENT-COVERAGE

## Scope
Correction-only follow-up to Phase 1. Do not start Phase 2.

## Verified issues in commit 9b70908
1. `مهمة جديدة` and `new task` are placed in `SMART_TASK_GENERIC_SEARCH_PHRASES`, so the canonical parser rejects them. They are explicit create-task intents and must open Smart Task TITLE step, while never being used as task titles.
2. The canonical Arabic create detector only matches commands beginning directly with create verbs. Natural phrases such as `عايز اعمل مهمة`, `عاوز انشئ مهمة`, `محتاج اعمل تاسك`, and equivalent polite prefixes can fail even though title stripping already anticipates those prefixes.
3. When CREATE_TASK intent is detected for a blocked user, `sendMessage()` currently returns without surfacing the execution-control reason at the moment of the attempted action. The compact status badge exists, but the attempted action should surface the existing `executionControl.messageAr/messageEn` without sending the request or opening Smart Task.

## Required behavior
- `مهمة جديدة` => CREATE_TASK, title=null, open TITLE.
- `مهمة ذكية` => CREATE_TASK, title=null, open TITLE if this phrase is intentionally supported as the Smart Task invocation phrase; never use it as title/project name.
- `new task` / `smart task` => CREATE_TASK, title=null where supported.
- `عايز اعمل مهمة` => CREATE_TASK, title=null.
- `عاوز انشئ مهمة تصميم بوست` => CREATE_TASK, title=`تصميم بوست`.
- `محتاج اعمل تاسك مراجعة الموقع` => CREATE_TASK, title=`مراجعة الموقع`.
- Search/status/update phrases remain non-create intents.
- Blocked users do not open Smart Task and immediately see the existing localized server execution-control message.

## Non-goals
- No Smart Task UI redesign.
- No project filtering changes.
- No assignee changes.
- No RBAC changes.
- No approval changes.
- No auto-create.

## Acceptance
- One canonical parser only.
- Explicit generic create phrases open TITLE but are never stored as title.
- Natural Arabic prefixed create phrases are covered.
- Search/update false positives remain zero in the regression set.
- Blocked-user action provides visible localized feedback using existing server-provided execution-control message.
- Existing server-side RBAC remains authoritative and unchanged.
