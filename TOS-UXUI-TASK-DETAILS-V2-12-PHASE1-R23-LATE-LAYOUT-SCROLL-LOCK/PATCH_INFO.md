# TOS Task Details V2.12 Phase 1 R23 — Late Layout Scroll Lock

VERSION=TOS_TASK_DETAILS_V2_12_PHASE1_R23_LATE_LAYOUT_SCROLL_LOCK
PATCH=TOS-UXUI-TASK-DETAILS-V2-12-PHASE1-R23-LATE-LAYOUT-SCROLL-LOCK
BASELINE=LIVE_R22_ON_R20

## QA finding
Manual video after R22 still shows newly opened Task Details starting around Overview/Description instead of the Hero/top.

R22 removed focus-induced scrolling, so the remaining behavior is consistent with a late layout/scroll-anchor restore after the first reset window.

## Fix
- Preserve the current R20 keyed body and R22 focus behavior.
- Mark the Task Details scroll owner explicitly.
- Disable browser scroll anchoring on Task Details scroll surfaces.
- Keep the Task Details view pinned to top during initial async layout stabilization.
- Watch size changes with ResizeObserver while the user has not interacted yet.
- Stop the lock immediately on user interaction so normal scrolling is never blocked.
- Preserve layout, Right Rail geometry, backend, DB, TCS, and Ramzy.

NO_BROWSER_QA=YES
NO_SCREENSHOTS=YES
NO_VISUAL_QA=YES
PUSH=NO
