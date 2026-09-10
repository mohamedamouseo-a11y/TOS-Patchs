# TOS Task Details Canonical Reference V2.1 — RTL Structural Geometry Fix

Status: corrective patch for the locked Canonical Reference V2.

## Problem confirmed by visual QA

In Arabic/RTL mode the whole Task Details composition was mirrored structurally instead of only changing text direction. This moved the TOS sidebar to the right, reversed the topbar/header composition, flipped the hero, moved the right rail to the left, and broke the approved two-column geometry.

## Scope

This patch is CSS/geometry only. It does not introduce API, database, permission, task-business-logic, TWS, Ramzy, or TCS changes.

At desktop widths the approved V2 structural geometry is locked to LTR while Arabic text/data-entry remains RTL:

- Sidebar: left
- Task workspace: right of sidebar
- Topbar: search left / profile right
- Header: breadcrumb left / actions right
- Hero: identity left / quote treatment right
- Hero controls: Assignees / Status / Priority / Due date
- Tabs: Overview / Checklist / Attachments / Activity / Subtasks
- Overview body: Description left / right rail right

## Implementation

Entrypoint:
`apply_tos_uxui_task_details_canonical_reference_v2_1_rtl_structural_geometry_fix.py`

The installer dynamically locates the already-applied V2 source stylesheet, appends the guarded V2.1 overlay, runs the production frontend build, deploys through the existing TOS runtime manifest, verifies runtime markers, and rolls back source/live build on failure.

No Git operation is performed inside `/var/www/TOS`.

Do not push TOS until visual QA passes against the locked V2 reference at `1664×936`.
