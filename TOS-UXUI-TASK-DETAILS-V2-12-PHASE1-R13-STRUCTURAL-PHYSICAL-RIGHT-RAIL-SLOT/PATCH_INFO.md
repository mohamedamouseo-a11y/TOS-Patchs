# TOS Task Details V2.12 Phase 1 R13 — Structural Physical Right Rail Slot

VERSION=TOS_TASK_DETAILS_V2_12_PHASE1_R13_STRUCTURAL_PHYSICAL_RIGHT_RAIL_SLOT
PATCH=TOS-UXUI-TASK-DETAILS-V2-12-PHASE1-R13-STRUCTURAL-PHYSICAL-RIGHT-RAIL-SLOT
BASELINE=LIVE_R12
PATCH_SCOPE=STRUCTURAL_RIGHT_RAIL_PLACEMENT_ONLY

## Production QA finding
R12 deployed successfully but manual QA still showed the Overview rail cards on the physical LEFT while the intended empty lane remained on the physical RIGHT.

## R13 approach
Stop relying on the rail element's own left/right/inset rules.
R13 adds one structural wrapper around the existing rail. The wrapper spans the full Task Details canvas and uses forced LTR flex-end alignment, so the existing rail is physically docked to the RIGHT regardless of RTL/logical-inset interactions.

## Preserved
- Task/Hero card position and full width
- existing right empty lane beside Tabs/Description
- existing rail cards/content/actions
- R9/R11 single-scroll behavior
- Sidebar
- backend/database/APIs/task logic
- TCS / Chat System
- Ramzy

## QA policy
NO_BROWSER_QA=YES
NO_SCREENSHOTS=YES
NO_VISUAL_QA=YES
PUSH=NO
