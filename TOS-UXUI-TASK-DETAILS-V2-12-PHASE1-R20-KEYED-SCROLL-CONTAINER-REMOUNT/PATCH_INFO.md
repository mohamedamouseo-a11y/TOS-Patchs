# TOS Task Details V2.12 Phase 1 R20 — Keyed Scroll Container Remount

VERSION=TOS_TASK_DETAILS_V2_12_PHASE1_R20_KEYED_SCROLL_CONTAINER_REMOUNT
PATCH=TOS-UXUI-TASK-DETAILS-V2-12-PHASE1-R20-KEYED-SCROLL-CONTAINER-REMOUNT
BASELINE=LIVE_R19

## QA finding
R19 resets all known scroll owners, but a newly opened task can still reuse the previous Task Details body's retained scroll state.

## Fix
- Key the actual Task Details overflow container by `task.id`.
- React must remount that scroll container whenever the task changes, giving it a fresh native scroll position.
- Preserve the R19 multi-owner reset as a fallback.
- Do not change Task Details layout, Right Rail, Assignee behavior, Sidebar, backend, DB, TCS, or Ramzy.

NO_BROWSER_QA=YES
NO_SCREENSHOTS=YES
NO_VISUAL_QA=YES
PUSH=NO
