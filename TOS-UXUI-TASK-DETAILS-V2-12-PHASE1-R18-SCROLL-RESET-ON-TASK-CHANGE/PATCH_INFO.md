# TOS Task Details V2.12 Phase 1 R18 — Scroll Reset On Task Change

VERSION=TOS_TASK_DETAILS_V2_12_PHASE1_R18_SCROLL_RESET_ON_TASK_CHANGE
PATCH=TOS-UXUI-TASK-DETAILS-V2-12-PHASE1-R18-SCROLL-RESET-ON-TASK-CHANGE
BASELINE=LIVE_R16_WITH_OPTIONAL_R17

## QA finding
When a user leaves one Task Details view after scrolling down and opens another task, the next task can open at the previous internal scroll position instead of at the top Hero.

## Corrected baseline
The first R18 installer incorrectly required R17. R18 does not need R17 to reset Task Details scroll.
This corrected installer requires R16 only and preserves R17 automatically if R17 is already present.
Do not apply R17 just to satisfy R18.

## Fix
- Reset the existing Task Details scroll owner (`taskDetailsBodyRef`) to top on initial mount and whenever `task.id` changes.
- Reset both `scrollTop` and `scrollLeft`.
- Repeat the reset on the next animation frame so the final rendered task layout cannot restore the stale position.
- Do not change Task Details layout, Right Rail geometry, Assignee portal behavior, Sidebar, backend, DB, TCS, or Ramzy.

NO_BROWSER_QA=YES
NO_SCREENSHOTS=YES
NO_VISUAL_QA=YES
PUSH=NO
