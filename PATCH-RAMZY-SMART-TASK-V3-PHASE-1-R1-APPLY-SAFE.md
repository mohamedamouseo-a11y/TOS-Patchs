# PATCH-RAMZY-SMART-TASK-V3-PHASE-1-R1-APPLY-SAFE

## Purpose
Finish Phase 1 R1 safely after the previous shell/heredoc attempt failed on Arabic escaping.

## Scope
Apply ONLY the missing R1 corrections to:
- `frontend/src/components/RamzyAssistant.jsx`

Do NOT start Phase 2.
Do NOT change backend RBAC, project RBAC, approval flow, or task creation logic.

## Current baseline
Production/main baseline commit: `9b70908`.
R1 corrections are NOT yet applied to source/live.

## Required corrections

### 1) Invocation-only create phrases
The following MUST trigger CREATE_TASK but MUST NEVER become the task title:
- `مهمة جديدة`
- `مهمة ذكية`
- `new task`
- `smart task`

Expected result:
`{ isCreateTask: true, title: null }`

### 2) Prefixed Arabic create phrases
Support natural prefixes before create verbs:
- `عايز اعمل مهمة` => CREATE_TASK, title=null
- `عاوز انشئ مهمة تصميم بوست` => CREATE_TASK, title=`تصميم بوست`
- `محتاج اعمل تاسك مراجعة الموقع` => CREATE_TASK, title=`مراجعة الموقع`

Keep one canonical parser only.

### 3) Preserve non-create rejection
The following must remain normal chat / non-create intent:
- `دور على مهمة تصميم`
- `فين مهمة التصميم`
- `ايه حالة مهمة التصميم`
- `غير موعد المهمة`
- `عدل مهمة التصميم`
- `احذف مهمة`
- `انقل مهمة`

### 4) Blocked-user feedback
When CREATE_TASK intent is detected and `status.executionControl.canExecute !== true`:
- Smart Task must NOT open.
- CREATE_TASK must NOT be sent.
- Show the existing localized server message immediately:
  - Arabic: `status.executionControl.messageAr`
  - English: `status.executionControl.messageEn`

Reuse the existing compact error/status presentation. Do not invent permission wording.

## Safe application requirement
The previous patch failed because Arabic text was embedded in a shell heredoc over SSH.

DO NOT use a raw shell heredoc containing Arabic text.

Use one of these safe approaches:
1. Open/edit the file directly with the editor available to the agent.
2. Use a Python script that reads and writes the UTF-8 file directly, but deliver the script via base64 or another encoding-safe mechanism.
3. Use a complete base64-encoded replacement payload generated from the current file after applying only the required edits.

Before writing:
- read the current file from disk
- verify baseline content
- create a timestamped backup outside the repo

After writing:
- re-open the exact edited ranges and verify Arabic literals are intact UTF-8
- verify no mojibake
- verify only intended logic changed

## Regression tests
1. `إنشاء مهمة` => TITLE
2. `انشي مهمة` => TITLE
3. `مهمة جديدة` => TITLE, title=null
4. `مهمة ذكية` => TITLE, title=null
5. `new task` => TITLE, title=null
6. `smart task` => TITLE, title=null
7. `عايز اعمل مهمة` => TITLE
8. `عاوز انشئ مهمة تصميم بوست` => PROJECT, title=`تصميم بوست`
9. `محتاج اعمل تاسك مراجعة الموقع` => PROJECT, title=`مراجعة الموقع`
10. `دور على مهمة تصميم` => normal chat
11. `ايه حالة مهمة التصميم` => normal chat
12. `غير موعد المهمة` => normal chat
13. blocked user => no Smart Task + localized server reason visible

## Acceptance
- canonical parser count remains 1
- no duplicate detector reintroduced
- no backend changes
- no permission changes
- no approval changes
- no Phase 2 work

## Finalization
After tests pass:
- frontend build
- atomic deploy
- live HTTP 200
- commit the R1 changes as a NEW commit after `9b70908`
- push to `main`
- verify production matches the new R1 commit
- remove/ignore untracked temporary backup files from the repo worktree so worktree is clean

## Return exactly

PATCH=RAMZY-SMART-TASK-V3-PHASE-1-R1-APPLY-SAFE
PASS/FAIL=<result>
R1_NEW_COMMIT=<sha>
CANONICAL_PARSER_COUNT=1
INVOCATION_ONLY_CREATE_PASS=YES/NO
INVOCATION_ONLY_USED_AS_TITLE=YES/NO
PREFIXED_ARABIC_CREATE_PASS=YES/NO
NON_CREATE_REGRESSION_PASS=YES/NO
BLOCKED_USER_SMART_TASK_OPENED=YES/NO
BLOCKED_USER_REASON_VISIBLE=YES/NO
UTF8_ARABIC_VERIFIED=YES/NO
FRONTEND_BUILD=PASS/FAIL
LIVE_DEPLOY=PASS/FAIL
LIVE_HTTP_STATUS=<code>
PRODUCTION_MATCHES_R1_COMMIT=YES/NO
WORKTREE_CLEAN=YES/NO
SERVER_RBAC_CHANGED=NO
PROJECT_RBAC_CHANGED=NO
APPROVAL_LOGIC_CHANGED=NO
FILES_CHANGED=<paths>
ERROR=<NONE or exact error>
