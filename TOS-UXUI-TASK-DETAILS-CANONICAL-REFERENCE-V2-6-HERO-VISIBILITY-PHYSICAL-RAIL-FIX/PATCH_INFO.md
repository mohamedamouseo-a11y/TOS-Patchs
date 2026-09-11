# TOS Task Details — Canonical Reference V2.6

Patch entrypoint:

`apply_tos_uxui_task_details_canonical_reference_v2_6_hero_visibility_physical_rail_fix.py`

## Purpose

V2.6 is a narrow visual correction on top of the successfully deployed V2.5 runtime.

The V2.5 screenshot confirmed:

- exact four Hero primary controls are present;
- the V2.4 duplicate Assignees card is removed;
- App Shell / Topbar / breadcrumb/actions / mountain / quote / tabs remain intact.

The remaining visible defects are:

1. the four Hero controls are clipped by the compact Hero boundary;
2. the Overview physical composition still renders the rail on the left and Description/editor on the right because older runtime CSS still wins over JSX/Tailwind geometry;
3. the right-rail stack is too vertically loose for the existing TCS Assistant card to remain visible in the 1664×936 reference viewport.

## V2.6 strategy

This patch is CSS-only.

- It does **not** mutate `ProfessionalTaskBoard.jsx`.
- It locks the internal Task Details composition using a physical `direction:ltr` flex row under `.tos-task-details-fullpage`:
  - Main / Description = LEFT
  - Right Rail = RIGHT at 304px
- It keeps the approved compact Hero container and only:
  - lifts the four-control row slightly;
  - compacts the visible control-card height;
  - compacts select/date control internals so all four cards remain fully visible.
- It leaves Start date advanced-only through the existing More path.
- It slightly compacts right-rail spacing/padding without removing or rewriting any rail content.
- It does not create or wire a TCS action; existing TCS content and the global floating launcher remain untouched.

## Required predecessor lineage

The installer refuses to run unless the canonical stylesheet contains all runtime markers through V2.5:

- V2
- V2.1
- V2.2
- V2.3
- V2.4
- V2.5

It also requires the V2.5 JSX state:

- `xl:grid-cols-[minmax(0,1fr)_304px]`
- Main `xl:order-1`
- Right Rail `xl:order-2`
- no `tos-task-assignees-hero-card`

## Safety

- no Git in `/var/www/TOS`;
- source stylesheet backup before mutation;
- build before live swap;
- staged live deployment;
- runtime marker verification;
- rollback on failure;
- no API / database / permission / task-business-logic / upload / TWS / Ramzy / TCS logic changes.

## Visual acceptance

At exactly `1664 × 936` in Light Mode:

- Sidebar remains LEFT.
- Search remains LEFT / profile RIGHT.
- Hero title / mountain / quote remain unchanged.
- Exactly four Hero controls are fully visible:
  `Assignees | Status | Priority | Due date`.
- Tabs remain unchanged.
- Overview physically renders:
  `Description/editor LEFT | Right Rail RIGHT`.
- Right Rail preserves:
  `Quick actions | Task information | Tags | TCS Assistant`.
- Global floating TCS launcher remains separate.

Do not push TOS until screenshot-based visual QA passes.
