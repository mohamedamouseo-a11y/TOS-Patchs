# TOS Task Details Canonical Reference V2.7

Patch: `TOS-UXUI-TASK-DETAILS-CANONICAL-REFERENCE-V2-7-REAL-OVERVIEW-RAIL-PHYSICAL-LOCK`

Baseline: pushed TOS `main` commit `f4be538dbf92996c4eb8325a133513f4db31df81`.

## Confirmed root cause

The visible Quick actions / Task information / Tags / TCS Assistant rail is not the legacy `.tos-task-side-rail` targeted by V2.5/V2.6. The real canonical Overview rail is `.tos-task-reference-v2-rail`.

That rail uses `inset-inline-end: 0` while its own content direction is RTL, which resolves to the physical LEFT edge. The Description/editor reduced-width block also lacked an explicit physical margin lock, so the two-column Overview stayed mirrored.

## Scope

CSS-only visual correction:

- `.tos-task-reference-v2-rail` -> physical RIGHT.
- `.tos-task-description-panel` -> physical LEFT.
- `.tos-task-detail-tabs` follows the same physical left column alignment.
- Compact only the real rail's vertical spacing so the existing Task Details TCS Assistant card can fit in the `1664x936` QA viewport.

## Frozen / untouched

- App shell, sidebar, topbar, breadcrumb/actions.
- Hero, mountain, quote.
- Exactly four Hero controls: Assignees / Status / Priority / Due date.
- Start date advanced More path.
- Tab order and tab logic.
- Task APIs, DB contracts, permissions, task business logic, uploads.
- TWS, Ramzy, TCS logic.
- Global floating TCS launcher.
- `ProfessionalTaskBoard.jsx` is guarded unchanged by SHA256 during installation.

## Execution

```bash
cd /var/www/TOS-Patchs
git fetch origin main
git reset --hard origin/main
python3 \
TOS-UXUI-TASK-DETAILS-CANONICAL-REFERENCE-V2-7-REAL-OVERVIEW-RAIL-PHYSICAL-LOCK/apply_tos_uxui_task_details_canonical_reference_v2_7_real_overview_rail_physical_lock.py \
/var/www/TOS
```

No Git commands are allowed inside `/var/www/TOS`.

## Visual QA

Light mode, exact viewport `1664x936`.

Expected:

- Description/editor physically LEFT.
- Canonical rail physically RIGHT.
- Rail retains Quick actions / Task information / Tags / TCS Assistant.
- Existing TCS Assistant card is visible in the rail if viewport density permits.
- Global floating TCS launcher remains separate.
- Hero and four controls remain unchanged.

Screenshot name:

`TOS__TASK-DETAILS__V2-7__LIGHT__1664x936__VISUAL-QA.png`

No push until ChatGPT visual approval.
