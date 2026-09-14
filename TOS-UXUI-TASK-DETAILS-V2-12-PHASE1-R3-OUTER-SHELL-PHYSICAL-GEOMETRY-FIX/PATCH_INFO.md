# TOS Task Details V2.12 Phase 1 R3 — Outer Shell Physical Geometry Fix

VERSION=TOS_TASK_DETAILS_V2_12_PHASE1_R3_OUTER_SHELL_PHYSICAL_GEOMETRY
PATCH=TOS-UXUI-TASK-DETAILS-V2-12-PHASE1-R3-OUTER-SHELL-PHYSICAL-GEOMETRY-FIX
BASELINE=TOS_TASK_DETAILS_V2_12_PHASE1_R2_RTL_TABS_DESCRIPTION
BASELINE_PATCH_COMMIT=540fe7dda0733fb1698ce0737396f2519f9142c1
PATCH_SCOPE=OUTER_FULLSCREEN_GEOMETRY_HOTFIX

## Why R3 exists
A real production screenshot after R2 showed a severe regression: opening a Task Details page could leave the normal TOS sidebar visible while the Task Details workspace itself was pushed off-canvas to the physical right.

The cause is the fullscreen positioning boundary receiving `dir={modalDirection}` from R1, plus R2 reinforcing RTL direction on that same outer root. The fullscreen shell is geometry, not semantic content, and must remain physically LTR/stable.

## Exact fix
`frontend/src/components/ProfessionalTaskBoard.jsx`

Only the outer Task Details fullscreen root changes:

- FROM: `dir={modalDirection} data-content-dir={modalDirection}`
- TO:   `dir="ltr" data-content-dir={modalDirection}`

The inner Task Details layout remains:

- `dir={modalDirection}`

One new stylesheet import is added after R2:

- `taskDetailsV2_12_Phase1R3OuterShellPhysicalGeometryFix.css`

## CSS contract
- Outer fullscreen shell is forced to physical LTR geometry and `inset:0`.
- Modal frame remains width 100% with no RTL physical drift/transform.
- Semantic RTL is re-applied to actual content surfaces only: topbar/header, main content, Hero, tabs, Description, canonical rail, More Details rail.
- Existing R1 Assignee geometry is preserved.
- Existing R2 Tabs/Description styling is preserved.
- TCS/Chat System and Ramzy are untouched.

## Frozen / unchanged
- Backend
- Database
- APIs
- Authentication
- Permissions
- Task business logic
- `taskBoardParts.jsx`
- `App.jsx`
- `taskDetailsCanonicalReferenceV2.css`
- Phase 1 CSS
- R1 CSS
- R2 CSS
- Assignee R1 geometry
- More Details R1 geometry
- TCS / Chat System
- Ramzy

## Apply

```bash
python3 \
  /var/www/TOS-Patchs/TOS-UXUI-TASK-DETAILS-V2-12-PHASE1-R3-OUTER-SHELL-PHYSICAL-GEOMETRY-FIX/apply_tos_task_details_v2_12_phase1_r3_outer_shell_physical_geometry_fix.py \
  /var/www/TOS
```

## QA policy
OpenHands must NOT use a browser, take screenshots, or perform visual QA.
It must only apply/build/deploy and return technical verification.
Manual visual QA is performed by the user + ChatGPT.

NO_BROWSER_QA=YES
NO_SCREENSHOTS=YES
PUSH=NO
