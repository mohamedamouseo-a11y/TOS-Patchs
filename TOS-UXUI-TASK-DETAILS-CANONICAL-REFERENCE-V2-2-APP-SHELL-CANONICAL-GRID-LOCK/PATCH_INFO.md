# TOS Task Details Canonical Reference V2.2 — App Shell + Canonical Grid Lock

Status: corrective patch for the locked Canonical Reference V2 after V2.1 technical PASS / visual FAIL.

## Confirmed root cause

The Arabic application shell still carries an explicit RTL `dir` attribute, and the Task Details root also retained `dir={modalDirection}`. CSS-only direction overrides from V2.1 could not disable structural selectors that explicitly match `[dir="rtl"]`. Those branches continued to mirror the app shell / hero / task grid.

## V2.2 strategy

1. Convert only the Task Details root from structural `dir={modalDirection}` to `dir="ltr"`.
2. Preserve the current content language in `data-content-dir={modalDirection}`.
3. Lock the outer TOS app frame to physical LTR geometry only while RTL Task Details is open.
4. Keep the sidebar on the physical left and the main shell on its right.
5. Keep topbar Search/identity on the left and profile/actions on the right.
6. Prevent RTL auto-placement from mirroring the Hero, tabs, main column, or right rail.
7. Preserve Arabic direction for rich-text/data-entry content.

## Canonical target

- Sidebar: LEFT
- Workspace: RIGHT OF SIDEBAR
- Topbar: Search LEFT / Profile RIGHT
- Hero: task identity LEFT / quote treatment RIGHT
- Tabs: Overview → Checklist → Attachments → Activity → Subtasks
- Overview: Description LEFT / right rail RIGHT
- Reference viewport: `1664 × 936`

## Safety

- Presentation/geometry correction only.
- No API changes.
- No database changes.
- No permission changes.
- No task business-logic changes.
- No TWS internals changes.
- No Ramzy changes.
- No TCS logic changes.
- Installer requires the already-applied V2 + V2.1 runtime markers.
- Source + live build rollback on failure.
- No Git operation inside `/var/www/TOS`.

Entrypoint:
`apply_tos_uxui_task_details_canonical_reference_v2_2_app_shell_canonical_grid_lock.py`

Do not push TOS until visual QA passes against the locked V2 reference.
