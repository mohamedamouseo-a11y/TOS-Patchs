# PATCH-RAMZY-SMART-TASK-V3-PHASE-7-R2-FINAL-CONTRACT-ALIGNMENT

Baseline local commit:
2e869a087a88621c73a484f566bb5358c3df6a60

Final Phase 7 cleanup. Keep logic unchanged unless required to satisfy the exact contract below.

## 1) Exact AUTO assignee validation copy
Use ONE exact message whenever AUTO assignee cannot resolve to a current authorized recommended user (missing OR stale recommendation):

EN:
No unique workload suggestion is available. Choose an assignee or Unassigned.

AR:
لا يوجد اقتراح فريد حسب ضغط العمل. اختر منفذًا أو بدون تحديد.

Do not keep shorter alternatives such as:
- No workload recommendation available.
- Recommended assignee is no longer available.

## 2) Exact AUTO priority validation copy
EN:
Choose a specific priority before review.

AR:
اختر أولوية محددة قبل المراجعة.

## 3) Exact review action labels
EN:
- Back to edit
- Submit for approval

AR:
- رجوع للتعديل
- إرسال للاعتماد

## 4) Preserve Phase 7 R1 behavior
Do NOT regress:
- current conversationId reused
- route creates NO AgentConversation
- assigneeId nullable / Unassigned => null
- AUTO assignee valid only when recommended ID exists in current authorized assignee list
- real same-card read-only review summary
- structured payload includes conversationId
- explicit runless CREATE_TASK only with !runId && !toolExecutionId
- conditional AgentRun lookup
- PENDING approval only
- no direct task execution
- no sendMessage/streamMessage/runRamzyTurn final submission
- failed submit preserves draft/review
- Phase 1-6 behavior

## 5) Regression tests
Update/add focused tests asserting:
- exact AUTO assignee EN/AR strings
- exact AUTO priority EN/AR strings
- exact review button EN/AR strings
- route does not call agentConversation.create
- supplied conversationId is used
- nullable assigneeId accepted
- stale/missing AUTO recommendation blocks
- NONE maps to null
- runless gate requires !runId && !toolExecutionId
- structured submit path contains no chat/model submission

No DB migration.
No scheduler.
No unrelated refactor.
Do not stage backups.

## Verify
- frontend build PASS
- backend test:ramzy PASS
- ONE NEW COMMIT
- COMMIT ONLY
- DO NOT PUSH

## Return only
PATCH=RAMZY-SMART-TASK-V3-PHASE-7-R2-FINAL-CONTRACT-ALIGNMENT
PASS/FAIL=
BASELINE_COMMIT=2e869a0
R2_NEW_COMMIT=
AUTO_ASSIGNEE_COPY_EXACT=
AUTO_PRIORITY_COPY_EXACT=
REVIEW_BUTTON_COPY_EXACT=
CURRENT_CONVERSATION_REUSED=
UNASSIGNED_NULL_SUPPORTED=
AUTO_STALE_BLOCKED=
RUNLESS_GATE_EXPLICIT=
CHAT_MODEL_SUBMIT=NO
DIRECT_TASK_EXECUTION=NO
APPROVAL_PENDING_ONLY=
FRONTEND_BUILD=
BACKEND_TEST=
UNTRACKED_BACKUPS_UNSTAGED=
ERROR=
