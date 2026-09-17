# PATCH — RAMZY SMART TASK V3 — PHASE 2 R1 SOURCE CORRECTIONS

## Baseline
TOS commit: `635140273f558ea114b8a9208361e989e659f931`

## Scope
Correction-only follow-up to Phase 2. Do not start Phase 3.

## Verified gaps

### 1. Title readiness must use trimmed value
Current submit readiness checks `!smartTask.title`, so whitespace-only text is truthy and can enable submission.

Required:
- Treat title as valid only when `String(smartTask.title || "").trim()` is non-empty.
- `smartTaskPrompt()` must use the trimmed title for the task title line.
- Do not silently destroy meaningful internal spaces.
- Keep the editable field value unchanged while typing; normalize only for readiness/submission.

### 2. Preserve existing project client metadata in selected row
Current `chooseSmartTaskProject(item)` stores only `{ id, name, auto }`, so `clientName` already available from the project result is lost after selection.

Required:
- For manual project selection preserve `clientName` when already present in the project option.
- Selected project row should show project name and a subtle client name when available.
- AUTO project behavior stays unchanged.
- Changing project must preserve all other task draft fields.

## Do not change
- Phase 1 intent parser
- Project/data permissions
- Assignee data source or authorization
- Approval behavior
- Backend routes/business logic
- Smart Task single-card architecture
- Phase 3+

## Verification
- whitespace-only title => submit disabled
- title with leading/trailing spaces => readiness uses trimmed title and submitted prompt uses trimmed title
- normal title => unchanged behavior
- manual project with clientName => selected row shows clientName
- project without clientName => no empty/placeholder client label
- Change project => title/description/due/priority/assignee preserved
- frontend build PASS
- commit + push main
- clean worktree

## Return
PATCH=RAMZY-SMART-TASK-V3-PHASE-2-R1-SOURCE-CORRECTIONS
PASS/FAIL=<result>
BASELINE_COMMIT=6351402
R1_NEW_COMMIT=<sha>
WHITESPACE_ONLY_TITLE_BLOCKED=YES/NO
SUBMITTED_TITLE_TRIMMED=YES/NO
PROJECT_CLIENT_METADATA_PRESERVED=YES/NO
SELECTED_PROJECT_CLIENT_VISIBLE=YES/NO
DRAFT_PRESERVED_ON_PROJECT_CHANGE=YES/NO
PHASE1_INTENT_CHANGED=NO
PROJECT_RBAC_CHANGED=NO
ASSIGNEE_RBAC_CHANGED=NO
APPROVAL_LOGIC_CHANGED=NO
BACKEND_CHANGED=NO
FRONTEND_BUILD=PASS/FAIL
LIVE_DEPLOY=PASS/FAIL
PUSH=YES/NO
WORKTREE_CLEAN=YES/NO
FILES_CHANGED=<paths>
ERROR=<NONE or exact error>
