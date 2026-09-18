# PATCH-RAMZY-SMART-TASK-V3-PHASE-5-R8-LAST-COPY-PROMPT-FIX

Baseline local commit: bc1658f587523b320053aa43000c60cafd259271

Tiny acceptance correction only.

## 1) Dynamic AI button copy
Frontend button text must depend on whether the current description is empty after trim.

If description is empty:
- EN: Write with Ramzy
- AR: صياغة الوصف مع رمزي

If description is non-empty:
- EN: Improve with Ramzy
- AR: تحسين الوصف مع رمزي

Keep the existing loading icon/state and existing disable rules.
Do not use combined "Write/Improve" or "اكتب/حسّن" wording.

## 2) Complete AI prompt restrictions
Keep the current restrictions and explicitly include:
- people
- dates
- acceptance criteria

Final prompt restrictions must cover:
people, assignee, dates/due date, priority, IDs, credentials/secrets, acceptance criteria, unsupported facts.

No other behavior changes.

## Preserve
- title/description/output bounds
- current model/provider
- no tools
- no template fallback
- visible-task workload scope
- recommendedAssigneeId
- CUSTOM local date handling
- URGENT
- Phase 1-4 RBAC
- approval + prompt-based submit
- no Phase 6/7
- backup files unstaged

## Verify
- frontend build PASS
- backend Ramzy tests PASS
- dynamic button wording exact
- prompt restrictions complete
- ONE NEW COMMIT
- COMMIT ONLY, DO NOT PUSH

## Return only
PATCH=RAMZY-SMART-TASK-V3-PHASE-5-R8-LAST-COPY-PROMPT-FIX
PASS/FAIL=
BASELINE_COMMIT=bc1658f
R8_NEW_COMMIT=
EMPTY_COPY_EXACT=
NONEMPTY_COPY_EXACT=
PROMPT_RESTRICTIONS_COMPLETE=
FRONTEND_BUILD=
BACKEND_TEST=
UNTRACKED_BACKUPS_UNSTAGED=
ERROR=
