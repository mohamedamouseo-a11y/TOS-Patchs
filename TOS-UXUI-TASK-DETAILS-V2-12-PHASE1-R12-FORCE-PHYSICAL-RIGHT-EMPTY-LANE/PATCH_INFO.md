# TOS Task Details V2.12 Phase 1 R12 — Force Physical Right Empty Lane

VERSION=TOS_TASK_DETAILS_V2_12_PHASE1_R12_FORCE_PHYSICAL_RIGHT_EMPTY_LANE
PATCH=TOS-UXUI-TASK-DETAILS-V2-12-PHASE1-R12-FORCE-PHYSICAL-RIGHT-EMPTY-LANE
BASELINE=LIVE_R11
PATCH_SCOPE=HORIZONTAL_RAIL_ANCHOR_ONLY

## QA finding after R11
- The correct empty lane exists on the physical RIGHT.
- The Task/Hero card is correctly preserved full width.
- The rail cards are still anchored on the physical LEFT and overlap Description.

## R12 exact behavior
- Keep Task/Hero size and position unchanged.
- Keep Tabs/Description width reservation unchanged.
- Keep rail vertical start unchanged.
- Keep single-scroll behavior unchanged.
- Move ONLY the rail horizontally into the already-empty physical right lane.
- Use `left: calc(100% - 370px)` instead of relying on `right`, logical insets, or RTL ordering.

## Frozen
- App.jsx
- Sidebar.jsx
- all previous Phase1 styles
- backend / database / APIs
- task business logic
- TCS / Chat System
- Ramzy

NO_BROWSER_QA=YES
NO_SCREENSHOTS=YES
NO_VISUAL_QA=YES
PUSH=NO
