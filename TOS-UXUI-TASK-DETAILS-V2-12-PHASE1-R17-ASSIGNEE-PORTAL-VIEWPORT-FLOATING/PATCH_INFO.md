# TOS Task Details V2.12 Phase 1 R17 — Assignee Portal Viewport Floating

VERSION=TOS_TASK_DETAILS_V2_12_PHASE1_R17_ASSIGNEE_PORTAL_VIEWPORT_FLOATING
PATCH=TOS-UXUI-TASK-DETAILS-V2-12-PHASE1-R17-ASSIGNEE-PORTAL-VIEWPORT-FLOATING
BASELINE=LIVE_R16

## Video-confirmed issue
Opening Assignees makes the picker behave as if it is trapped inside the Task/Hero frame: the Hero reserves space, the picker drops into the tabs area, and part of the member list can appear cut off.

## Required behavior
- Assignee picker is a real `document.body` floating portal.
- It never expands/pushes the Task/Hero, Tabs, Description, or right rail.
- It chooses below or above the trigger based on real viewport space.
- Its outer popover is always bounded inside the viewport.
- If many members exist, only the member list scrolls internally; the popover itself remains fully visible.
- High portal z-index keeps it above the Task Details frame.

## Implementation
- Remove the old R1 Hero space-reservation behavior when Assignees is open.
- Replace the fixed 300px position estimate with viewport-aware available-height positioning.
- Pass the calculated available viewport height through a CSS custom property.
- Keep the portal fixed to the viewport with a high z-index.

## Frozen
Task/Hero layout, R13/R16 right rail geometry, single-scroll behavior, App.jsx, Sidebar.jsx, backend, database, APIs, task business logic, TCS/Chat System, Ramzy.

NO_BROWSER_QA=YES
NO_SCREENSHOTS=YES
NO_VISUAL_QA=YES
PUSH=NO
