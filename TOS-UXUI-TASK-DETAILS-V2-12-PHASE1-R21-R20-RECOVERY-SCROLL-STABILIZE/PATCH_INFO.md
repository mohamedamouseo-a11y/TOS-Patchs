# TOS Task Details V2.12 Phase 1 R21 — R20 Recovery + Scroll Stabilize

VERSION=TOS_TASK_DETAILS_V2_12_PHASE1_R21_R20_RECOVERY_SCROLL_STABILIZE
PATCH=TOS-UXUI-TASK-DETAILS-V2-12-PHASE1-R21-R20-RECOVERY-SCROLL-STABILIZE
BASELINE=LIVE_R20

## QA finding
R20 keyed remount caused a severe rendering regression: Task Details content disappeared and the main workspace became a blank canvas while the global sidebar remained visible.

## Fix
- Remove only the R20 `key={task.id}` remount from the Task Details scroll container.
- Remove the R20 stylesheet import from the live bundle.
- Preserve R19 multi-owner scroll reset.
- Disable browser scroll anchoring on the real Task Details scroll owner.
- Retry top reset at render time and 60/180/420/800 ms to beat late layout/focus restoration without remounting the Task UI.
- Do not change Task Details geometry, Right Rail, Sidebar, backend, DB, TCS, or Ramzy.

NO_BROWSER_QA=YES
NO_SCREENSHOTS=YES
NO_VISUAL_QA=YES
PUSH=NO
