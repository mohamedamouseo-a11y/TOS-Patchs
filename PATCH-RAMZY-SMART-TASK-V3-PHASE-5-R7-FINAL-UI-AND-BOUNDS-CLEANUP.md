# PATCH-RAMZY-SMART-TASK-V3-PHASE-5-R7-FINAL-UI-AND-BOUNDS-CLEANUP

Baseline local commit: bc1e468eee082462c229b43f733433a852d09c41

This is a final acceptance cleanup only. Do not alter Phase 5 architecture.

## 1) Bound AI inputs/output
In POST /api/agent/task-create/suggest-description:
- title = trimmed and capped to 180 chars
- description = trimmed and capped to 4000 chars
- language remains normalized to ar/en

In generateTaskDescription:
- final model text must be trimmed and capped to 4000 chars
- empty text still causes the existing non-2xx route error

Frontend:
- send trimmed title
- keep current description and language

## 2) Make prompt restrictions match Phase 5 contract
The description prompt/instructions must explicitly forbid inventing:
- people/assignee
- dates/due date
- priority
- internal IDs
- credentials/secrets
- acceptance criteria
- unsupported facts

Keep no-tools/no-side-effects behavior.

## 3) Final user-facing labels
Use the intended Phase 5 wording:
- CUSTOM AR: "تاريخ آخر"
- CUSTOM EN: "Custom date"
- empty description AI button:
  - AR: "صياغة الوصف مع رمزي"
  - EN: "Write with Ramzy"
- non-empty description AI button:
  - AR: "تحسين الوصف مع رمزي"
  - EN: "Improve with Ramzy"
- workload recommendation:
  - AR: "اقتراح حسب ضغط العمل: <name>"
  - EN: "Workload suggestion: <name>"

Keep the existing explicit Use/استخدم button and never auto-assign.

## Preserve
- visible-task workload scope
- recommendedAssigneeId contract
- custom local date helpers
- local 17:00 -> ISO
- URGENT
- Phase 1-4 RBAC
- approval/prompt submission
- no Phase 6/7
- no backup files staged

## Verify
- frontend build PASS
- backend Ramzy tests PASS
- AI output cannot exceed 4000 chars
- title sent/generated from trimmed input
- labels above are exact
- only intended Phase 5 files staged

## Workflow
Implement against local commit bc1e468.
Create ONE NEW commit.
COMMIT ONLY. DO NOT PUSH.

## Return only
PATCH=RAMZY-SMART-TASK-V3-PHASE-5-R7-FINAL-UI-AND-BOUNDS-CLEANUP
PASS/FAIL=
BASELINE_COMMIT=bc1e468
R7_NEW_COMMIT=
AI_TITLE_CAPPED_180=
AI_DESCRIPTION_CAPPED_4000=
AI_OUTPUT_CAPPED_4000=
PROMPT_RESTRICTIONS_COMPLETE=
CUSTOM_LABEL_EXACT=
AI_BUTTON_LABELS_EXACT=
WORKLOAD_LABEL_EXACT=
AUTO_ASSIGNS=NO
FRONTEND_BUILD=
BACKEND_TEST=
UNTRACKED_BACKUPS_UNSTAGED=
ERROR=
