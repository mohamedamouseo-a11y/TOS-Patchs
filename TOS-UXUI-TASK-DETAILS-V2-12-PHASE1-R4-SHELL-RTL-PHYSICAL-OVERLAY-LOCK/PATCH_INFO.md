# TOS Task Details V2.12 Phase 1 R4 — Shell RTL + Physical Overlay Lock

VERSION=TOS_TASK_DETAILS_V2_12_PHASE1_R4_SHELL_RTL_PHYSICAL_OVERLAY_LOCK
PATCH=TOS-UXUI-TASK-DETAILS-V2-12-PHASE1-R4-SHELL-RTL-PHYSICAL-OVERLAY-LOCK
BASELINE=TOS_TASK_DETAILS_V2_12_PHASE1_R3_OUTER_SHELL_PHYSICAL_GEOMETRY
BASELINE_PATCH_COMMIT=05115625deffa7e7c045c2650c453236525fd605
PATCH_SCOPE=FRONTEND_SHELL_DIRECTION_REGRESSION_FIX

## Why R4 exists
Production video after R3 showed that opening Task Details moved the TOS sidebar from the right side to the left side.

R3 solved the off-canvas Task Details issue by forcing the Task Details outer shell to `dir="ltr"`, but that introduced a shell-direction regression in the Arabic interface.

R4 separates semantic direction from physical overlay geometry:

- Task Details outer shell returns to `dir={modalDirection}`.
- Arabic UI remains RTL, so the application/sidebar direction is not flipped by Task Details.
- Physical overlay placement is locked with explicit top/right/bottom/left/inset/width/height rules instead of relying on LTR direction.
- Inner Task Details layout remains `dir={modalDirection}`.

## Exact source change
`frontend/src/components/ProfessionalTaskBoard.jsx`

FROM:
`dir="ltr" data-content-dir={modalDirection}`

TO:
`dir={modalDirection} data-content-dir={modalDirection}`

Add one stylesheet import after R3:
`taskDetailsV2_12_Phase1R4ShellRtlPhysicalOverlayLock.css`

## Preserved
- R1 Assignee zero-overlap geometry
- R2 Tabs/Description RTL fixes
- R3 physical anti-drift intent
- More Details geometry
- Backend / DB / API
- TCS / Chat System
- Ramzy

## QA policy
NO_BROWSER_QA=YES
NO_SCREENSHOTS=YES
PUSH=NO
