# TOS Task Details V2.12 Phase 1 R9 — Top Right Rail + Single Scroll

VERSION=TOS_TASK_DETAILS_V2_12_PHASE1_R9_TOP_RIGHT_RAIL_SINGLE_SCROLL
PATCH=TOS-UXUI-TASK-DETAILS-V2-12-PHASE1-R9-TOP-RIGHT-RAIL-SINGLE-SCROLL
BASELINE=LIVE_R8
PATCH_SCOPE=RIGHT_RAIL_TOP_PLACEMENT_AND_SINGLE_SCROLL_ONLY

## Production QA finding
Manual QA after R8 showed that the right-side cards were no longer clipped, but they were still vertically positioned far below the Task/Hero card. The Task Details view also exposed two vertical scroll surfaces at the same time.

## R9 behavior
- Keep the right rail on the physical RIGHT.
- Move the rail to `top:0` of the Task Details body so Quick Actions / Task Information / Tags remain beside the Task/Hero card at the top.
- Use the original component rail width: 304px.
- Reserve one matching lane across the whole main column, not only Tabs/Description.
- Preserve R7/R8 shell containment so nothing is clipped outside the main shell.
- Disable the outer `.tos-premium-page-viewport` scrollbar only while Task Details is open.
- Keep the existing Task Details body as the single vertical scroll owner.
- Do not create any rail-internal vertical scroll.

## Frozen
- App.jsx
- Sidebar.jsx
- all earlier Phase1 styles
- backend / database / APIs
- task business logic
- TCS / Chat System
- Ramzy

## QA policy
NO_BROWSER_QA=YES
NO_SCREENSHOTS=YES
NO_VISUAL_QA=YES
PUSH=NO
