# Phase 7 R5 Runtime Closure

Baseline local commit: 6d7398f651ba3a96cb487add10ca06b6379d334f

Fix only these blockers found in the exact R4 diff.

1. Import readable date helpers
RamzyAssistant.jsx now calls smartTaskReadableDate and smartTaskReadableDateTime but R4 did not add them to the import from ../lib/smartTaskDueDate.
Add both imports. No runtime ReferenceError allowed.

2. Release structured-submit lock on success too
Current smartTaskSubmitLockRef is set true before submit but reset only in catch.
That permanently blocks every later Smart Task after one successful submit because RamzyAssistant stays mounted.

Use try/catch/finally (or equivalent):
- if locked return
- set true before any await
- on success close Smart Task
- on failure preserve review/draft
- ALWAYS set smartTaskSubmitLockRef.current = false in finally
Retry after failure and a second Smart Task after success must both work.

3. Due review value
For every non-NONE due kind, render the actual smartTask.dueDate with smartTaskReadableDateTime(..., isEnglish).
Do not show only Today/Tomorrow/In 2 days labels in final review.
NONE stays No due date / بدون موعد.
No raw ISO or input-control datetime.

4. Real focused tests
Do not test duplicated slice expressions only.
Move/export the pure structured payload builder to a small frontend lib helper if needed, and import it in RamzyAssistant and the Node test.

Assert actual builder output:
- title trimmed/capped 180
- description capped 4000
- exact conversationId/projectId
- assigneeId null for NONE input
- estimatedHours numeric/null
- due/start/reminder values preserved as ISO/null
- no display names in payload

Assert actual readable helpers return non-raw values.
Add source assertion that submit lock is released in finally (or equivalent success+failure path).
Keep route enabled/owner/no-create/no-chat/runless assertions.

Preserve all Phase 1-7 behavior, exact R2 copy, PENDING approval only, no direct task execution, no migration/scheduler/unrelated refactor.

Run frontend build and backend test:ramzy.
ONE NEW COMMIT.
COMMIT ONLY.
DO NOT PUSH.
