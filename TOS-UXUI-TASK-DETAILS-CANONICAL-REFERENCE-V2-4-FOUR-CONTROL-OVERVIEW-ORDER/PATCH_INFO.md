# TOS Task Details — Canonical Reference V2.4

Status: **READY FOR CONTROLLED APPLICATION**

Patch entrypoint:
`apply_tos_uxui_task_details_canonical_reference_v2_4_four_control_overview_order.py`

## Why V2.4 exists

V2.3 successfully preserved the approved outer App Shell and corrected normal Hero height, but Visual QA at `1664×936` still showed two material mismatches against locked Canonical Reference V2:

1. The Hero did not contain the required four primary controls. The existing source actually contained Status / Priority / Due date / Start date, so Assignees could not be created by CSS alone.
2. Overview still rendered the side rail physically on the left and the Description/editor on the right because older higher-specificity layout/order rules were still winning.

## Scope

V2.4 changes only:
- adds a compact Assignees Hero control using existing `currentAssigneeIds` state and existing Side Details path
- keeps primary Hero order: `Assignees → Status → Priority → Due date`
- preserves Start date as advanced functionality exposed when the existing More state is open
- forces Overview physical order: `Description LEFT → Right Rail RIGHT`
- preserves right-rail content: Quick actions / Task information / Tags / TCS Assistant

## Explicitly preserved

- V2.2 App Shell and structural LTR lock
- Arabic content direction
- V2.3 normal Hero height
- Mountain / quote treatment
- Primary Tabs and their order/logic
- global floating TCS launcher
- APIs, data contracts, permissions, task business logic, upload logic, TWS, Ramzy and TCS logic

## Required predecessors

The installer requires runtime lineage for:
- Canonical V2
- V2.1 RTL Structural Geometry
- V2.2 App Shell Canonical Grid Lock
- V2.3 Internal Hero/Grid Fidelity

## Visual QA

After technical PASS, capture Light Mode at exact browser viewport `1664×936` and save to Google Drive as:

`TOS__TASK-DETAILS__V2-4__LIGHT__1664x936__VISUAL-QA.png`

Do not push TOS until that screenshot receives Visual PASS.
