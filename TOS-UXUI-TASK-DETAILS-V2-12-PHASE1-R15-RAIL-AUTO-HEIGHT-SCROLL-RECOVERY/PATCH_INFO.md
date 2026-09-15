# TOS Task Details V2.12 Phase 1 R15 — Rail Auto Height Scroll Recovery

VERSION=TOS_TASK_DETAILS_V2_12_PHASE1_R15_RAIL_AUTO_HEIGHT_SCROLL_RECOVERY
PATCH=TOS-UXUI-TASK-DETAILS-V2-12-PHASE1-R15-RAIL-AUTO-HEIGHT-SCROLL-RECOVERY
BASELINE=LIVE_R14

## QA finding
After R14, the user landed in a large blank scroll region. R14 had added a fixed `min-height:900px` floor to compensate for R13's zero-height absolute rail slot.

## Fix
- Remove the artificial R14 900px minimum-height floor.
- Remove R14 bottom padding.
- Preserve R13's correct physical-right rail placement.
- Change the absolute rail slot from zero-height to `height:auto`, so it sizes to the real rail content.
- Keep the existing single Task Details scroller.
- Do not move or resize the Task/Hero, Tabs, Description, Sidebar, TCS, or Ramzy.

NO_BROWSER_QA=YES
NO_SCREENSHOTS=YES
NO_VISUAL_QA=YES
PUSH=NO
