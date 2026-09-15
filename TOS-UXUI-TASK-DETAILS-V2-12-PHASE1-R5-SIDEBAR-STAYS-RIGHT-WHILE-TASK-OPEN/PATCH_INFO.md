# TOS Task Details V2.12 Phase 1 R5 — Sidebar Stays Right While Task Open

VERSION=TOS_TASK_DETAILS_V2_12_PHASE1_R5_SIDEBAR_STAYS_RIGHT
PATCH=TOS-UXUI-TASK-DETAILS-V2-12-PHASE1-R5-SIDEBAR-STAYS-RIGHT-WHILE-TASK-OPEN
BASELINE=TOS_TASK_DETAILS_V2_12_PHASE1_R4_SHELL_RTL_PHYSICAL_OVERLAY_LOCK
BASELINE_PATCH_COMMIT=4a44dc7cfc2f3acbd63a84fb06e45e21f77d184e
PATCH_SCOPE=DESKTOP_APP_SHELL_DIRECTION_LOCK

## Goal
Production video after R4 confirmed that opening Task Details still makes the desktop TOS sidebar appear on the physical left. R5 locks the desktop application frame itself so Arabic keeps the Sidebar on the physical right regardless of Task Details overlay direction.

## Fix
No App.jsx logic change.

A final R5 stylesheet is imported after R4 from ProfessionalTaskBoard.jsx. On desktop it explicitly locks:

- Arabic app frame: `direction: rtl` + `flex-direction: row`.
- Sidebar: first flex item / order 0 => physical right in RTL.
- Main shell: order 1 => physical left of the sidebar.
- English remains LTR with the sidebar on the left.

This is a shell geometry lock only. It does not redesign Task Details.

## Preserved
- R1 Assignee overlap fix
- R2 Tabs / Description fixes
- R3 physical geometry fix
- R4 RTL overlay fix
- App.jsx unchanged
- Sidebar.jsx unchanged
- backend / DB / APIs unchanged
- TCS / Chat System unchanged
- Ramzy unchanged

NO_BROWSER_QA=YES
NO_SCREENSHOTS=YES
PUSH=NO
