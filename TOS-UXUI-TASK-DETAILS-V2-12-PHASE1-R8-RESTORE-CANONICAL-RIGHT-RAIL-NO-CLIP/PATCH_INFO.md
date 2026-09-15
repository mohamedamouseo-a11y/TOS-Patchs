# TOS Task Details V2.12 Phase 1 R8 — Restore Canonical Right Rail, No Clip

VERSION=TOS_TASK_DETAILS_V2_12_PHASE1_R8_RESTORE_CANONICAL_RIGHT_RAIL_NO_CLIP
PATCH=TOS-UXUI-TASK-DETAILS-V2-12-PHASE1-R8-RESTORE-CANONICAL-RIGHT-RAIL-NO-CLIP
BASELINE=LIVE_R7
PATCH_SCOPE=RESTORE_OLD_RIGHT_RAIL_POSITION_WITHOUT_CLIPPING

## Production QA finding
R7 solved the outer shell clipping, but changed the approved Overview composition by placing the canonical right rail into a new grid flow. Manual QA showed the rail cards pushed below the Description instead of remaining in their old physical right-side lane.

## R8 behavior
- Preserve R7 main-shell containment so Task Details no longer extends beyond the available app viewport.
- Override only R7's inner Overview grid conversion.
- Restore `.tos-task-reference-v2-rail` to the canonical physical RIGHT absolute lane.
- Restore the canonical reserved width beside Tabs/Description: 370px rail / 390px lane on wide desktop, 330px rail / 348px lane at 1180–1280.
- Restore canonical rail vertical start: 298px desktop, 310px at >=1440 via the existing V2.10D variable.
- Preserve R7 Description toolbar containment/wrapping.
- Preserve R5 Sidebar behavior.

## Frozen
- App.jsx
- Sidebar.jsx
- all earlier Phase1 CSS including R7
- backend / database / APIs
- task business logic
- TCS / Chat System
- Ramzy

## QA policy
NO_BROWSER_QA=YES
NO_SCREENSHOTS=YES
NO_VISUAL_QA=YES
PUSH=NO
