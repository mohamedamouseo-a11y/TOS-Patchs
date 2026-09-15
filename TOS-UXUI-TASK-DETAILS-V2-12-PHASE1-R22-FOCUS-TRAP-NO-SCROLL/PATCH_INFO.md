# TOS Task Details V2.12 Phase 1 R22 — Focus Trap No Scroll

VERSION=TOS_TASK_DETAILS_V2_12_PHASE1_R22_FOCUS_TRAP_NO_SCROLL
PATCH=TOS-UXUI-TASK-DETAILS-V2-12-PHASE1-R22-FOCUS-TRAP-NO-SCROLL
BASELINE=LIVE_R20

## Corrected baseline
The first R22 installer incorrectly required R21. Production is currently on R20, so R22 now applies directly on top of R20 and does not require R21.

## Root cause targeted
The Task Details scroll resets can be overwritten by modal focus management. `useModalFocusTrap` re-runs when `task.id` changes and calls `.focus()` without `preventScroll`, including restoring the previously focused element during effect cleanup.

## Fix
- Keep the Task Details focus-trap lifecycle stable while navigating between tasks.
- Use `focus({ preventScroll: true })` for focus-trap initial focus and focus restoration.
- Preserve the current R20 Task Details baseline and geometry.
- No backend, DB, TCS, Ramzy, or layout redesign.

NO_BROWSER_QA=YES
NO_SCREENSHOTS=YES
NO_VISUAL_QA=YES
PUSH=NO
