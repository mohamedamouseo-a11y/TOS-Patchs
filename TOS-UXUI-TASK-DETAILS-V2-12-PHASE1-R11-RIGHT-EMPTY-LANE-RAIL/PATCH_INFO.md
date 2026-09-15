# TOS Task Details V2.12 Phase 1 R11 — Right Empty Lane Rail

VERSION=TOS_TASK_DETAILS_V2_12_PHASE1_R11_RIGHT_EMPTY_LANE_RAIL
PATCH=TOS-UXUI-TASK-DETAILS-V2-12-PHASE1-R11-RIGHT-EMPTY-LANE-RAIL
BASELINE=LIVE_R9
PATCH_SCOPE=KEEP_TASK_CARD_IN_PLACE_AND_USE_EXISTING_RIGHT_EMPTY_LANE

## User-confirmed target
- Do NOT move or shrink the Task/Hero card.
- Put the existing Overview rail cards only in the already-empty area on the physical RIGHT.
- Do not place the rail below the task content.
- Do not overlay the task content.
- Keep one Task Details scrollbar only.

## Exact layout
Desktop:
- `.tos-task-main-column` returns to full width.
- `.tos-task-summary-compact` stays full width and in its current position.
- Tabs + Description reserve the canonical 390px right lane.
- `.tos-task-reference-v2-rail` is 370px wide and occupies that lane on the physical RIGHT.
- Rail starts below the Hero where the empty Overview lane begins: 238px for 1180–1439, 258px for >=1440.
- R9 single-scroll ownership is preserved unchanged.

## Frozen
- App.jsx
- Sidebar.jsx
- previous Phase1 styles
- backend / database / APIs
- task business logic
- TCS / Chat System
- Ramzy

## QA policy
NO_BROWSER_QA=YES
NO_SCREENSHOTS=YES
NO_VISUAL_QA=YES
PUSH=NO
