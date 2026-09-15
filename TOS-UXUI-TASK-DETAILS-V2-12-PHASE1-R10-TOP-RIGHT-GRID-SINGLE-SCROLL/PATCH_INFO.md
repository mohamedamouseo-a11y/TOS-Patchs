# TOS Task Details V2.12 Phase 1 R10 — Top Right Grid + Single Scroll

VERSION=TOS_TASK_DETAILS_V2_12_PHASE1_R10_TOP_RIGHT_GRID_SINGLE_SCROLL
PATCH=TOS-UXUI-TASK-DETAILS-V2-12-PHASE1-R10-TOP-RIGHT-GRID-SINGLE-SCROLL
BASELINE=LIVE_R9
PATCH_SCOPE=RIGHT_RAIL_TOP_RIGHT_NO_OVERLAP_PLUS_SINGLE_TASK_SCROLL

## Manual QA after R9
The production video shows two remaining geometry defects:
- Quick Actions / Task Information / Tags / TCS rail is at the physical LEFT and overlaps the Task hero/tabs/Description.
- Task Details still presents nested/double vertical scrolling.

## R10 behavior
Desktop >=1180px:
- `.tos-task-details-layout` becomes one explicit physical LTR grid: `minmax(0,1fr) 304px`.
- Main task content is fixed to grid column 1.
- Existing right rail is fixed to grid column 2, row 1, so it begins at the TOP beside the Task hero card.
- Rail returns to normal grid flow; no absolute positioning and no overlap.
- Internal rail content keeps its own semantic RTL/LTR direction.

Scroll ownership:
- browser/body/app page viewport/task shell are non-scrolling while Task Details is open.
- the existing Task Details body is the ONE vertical scroll owner.
- rail cards never create a second vertical scroller.

## Frozen
- App.jsx source
- Sidebar.jsx source
- backend / database / APIs
- task business logic
- TCS / Chat System behavior
- Ramzy
- all earlier Phase1 patch files

## QA policy
NO_BROWSER_QA=YES
NO_SCREENSHOTS=YES
NO_VISUAL_QA=YES
PUSH=NO
