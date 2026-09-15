# TOS Task Details V2.12 Phase 1 R14 — Right Rail Bottom Scroll Extent

VERSION=TOS_TASK_DETAILS_V2_12_PHASE1_R14_RIGHT_RAIL_BOTTOM_SCROLL_EXTENT
PATCH=TOS-UXUI-TASK-DETAILS-V2-12-PHASE1-R14-RIGHT-RAIL-BOTTOM-SCROLL-EXTENT
BASELINE=LIVE_R13

## QA finding
R13 placed the Overview rail correctly in the physical right empty lane, but the lower rail content is cut off at the bottom.

## Root cause
R13 intentionally uses an absolutely-positioned zero-height wrapper (`.tos-task-reference-v2-rail-slot`). Because it does not contribute to normal document flow, the rail's full height is not guaranteed to contribute to Task Details scrollHeight.

## Fix
- Preserve R13 horizontal and vertical rail placement unchanged.
- Preserve the full-width Task/Hero unchanged.
- Preserve the existing single Task Details scroll owner.
- Give the Task Details layout a safe minimum vertical extent so the complete right rail is reachable by scrolling.
- Do not add a second scrollbar.

## Frozen
App.jsx, Sidebar.jsx, backend, DB, APIs, task logic, TCS and Ramzy.

NO_BROWSER_QA=YES
NO_SCREENSHOTS=YES
NO_VISUAL_QA=YES
PUSH=NO
