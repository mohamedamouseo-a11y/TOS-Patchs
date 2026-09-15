# TOS Task Details V2.12 Phase 1 R7 — Inner Grid + Right Rail Containment

VERSION=TOS_TASK_DETAILS_V2_12_PHASE1_R7_INNER_GRID_RIGHT_RAIL_CONTAINMENT
PATCH=TOS-UXUI-TASK-DETAILS-V2-12-PHASE1-R7-INNER-GRID-RIGHT-RAIL-CONTAINMENT
BASELINE=LIVE_R5_PLUS_SERVER_R6
PATCH_SCOPE=TASK_DETAILS_VIEWPORT_CONTAINMENT_ONLY

## Production issue
Manual QA after R6 still shows:
- the canonical Overview right rail clipped outside the physical right edge;
- the Due-date / Hero edge clipping;
- Description toolbar controls clipped/stacked at the right edge.

## Root geometry addressed
- Task Details is rendered inside `.tos-premium-main-shell`, while the earlier R4 overlay uses viewport-sized fixed geometry.
- Canonical V2 also forces `.tos-task-details-layout` to `display:block` and positions `.tos-task-reference-v2-rail` absolutely, while separately shrinking Description/Tabs.
- R7 gives Task Details a bounded main-shell containing block and replaces the Overview absolute-rail composition with an explicit two-column grid.

## Exact behavior
Desktop >=1180px:
- main = `minmax(0,1fr)`
- rail = `clamp(280px,24%,340px)`
- rail is in normal grid flow at physical right
- Tabs/Description use 100% of the main column instead of subtracting rail width again

Also:
- Task Details overlay is contained to the main shell rather than `100vw`
- Description toolbar wraps safely in both Arabic and English
- Hero/main children receive min-width/max-width containment

## Frozen
- App.jsx source
- Sidebar.jsx source
- all earlier Phase1 CSS files including any server-created R6
- backend / database / APIs
- task business logic
- TCS / Chat System
- Ramzy

## QA policy
NO_BROWSER_QA=YES
NO_SCREENSHOTS=YES
NO_VISUAL_QA=YES
PUSH=NO
