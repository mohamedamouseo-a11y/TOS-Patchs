# TOS Task Details — Canonical Reference V2.5

Patch entrypoint:
`apply_tos_uxui_task_details_canonical_reference_v2_5_exact_four_controls_physical_grid_lock.py`

## Purpose

Final surgical correction after V2.4 visual QA.

V2.4 visually confirmed two remaining material mismatches:

1. The Hero showed five visible controls because V2.4 inserted an extra Assignees card (`tos-task-assignees-hero-card`) while the canonical Task Details already had its original assignee control.
2. The Overview body still rendered physically as Right Rail LEFT / Description RIGHT because legacy JSX/Tailwind geometry remained `320px + main`, `main xl:order-2`, `rail xl:order-1`.

## V2.5 surgery

- Remove only the exact V2.4-injected duplicate Assignees Hero button.
- Preserve the pre-existing canonical assignee control.
- Preserve Status / Priority / Due date.
- Preserve Start date as V2.4 advanced More-only functionality.
- Change Task Details desktop JSX grid to `minmax(0,1fr) + 304px`.
- Change main column to `xl:order-1`.
- Change side rail to `xl:order-2`.
- Add CSS physical grid lock that covers normal ancestry and portal-rendered Task Details.

Expected visible primary Hero controls at 1664×936:
`Assignees → Status → Priority → Due date`

Expected Overview geometry:
`Description/Editor LEFT → Right Rail RIGHT`

## Preserved

- V2 canonical reference contract
- V2.2 App Shell / structural LTR lock
- Arabic content/editor RTL
- V2.3 Hero height
- V2.3 Tabs placement
- Mountain / quote
- Primary tab order / behavior
- V2.4 Start date advanced path
- Quick actions / Task information / Tags / TCS Assistant content
- Global floating TCS launcher
- API / DB / permissions / task business logic / uploads / TWS / Ramzy / TCS logic

## Safety

- Exact V2.4 duplicate JSX block must match once or the installer stops.
- Legacy layout/main/rail class tokens must each match exactly once or the installer stops.
- Full source/live backup and rollback on failure.
- No Git action is performed inside `/var/www/TOS`.
- Do not push TOS before visual QA.

Visual QA viewport: `1664×936`, Light Mode.
