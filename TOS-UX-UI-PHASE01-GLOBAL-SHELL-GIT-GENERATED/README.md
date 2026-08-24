# TOS UX/UI Phase 01 — Global Shell

Approved baseline: `mohamedamouseo-a11y/TOS@32c6931336d8f0cf10b80cd772d1b53ed391c6b8`

This generator creates a deterministic frontend-only patch for the shared TOS application shell.

## Scope

- `frontend/src/App.jsx`
- `frontend/src/components/layout/Sidebar.jsx`
- `frontend/src/components/layout/Topbar.jsx`

## Design goals

- Reduce oversized navigation chrome and excessive card/pill density.
- Establish a cleaner, more professional global frame before page-level redesign phases.
- Improve sidebar hierarchy and navigation density without changing routes or permissions.
- Refine topbar hierarchy and utility controls.
- Replace blank text-only lazy-loading screens with a shared skeleton loading state.
- Preserve RTL/LTR, dark mode, mobile sidebar behavior, notification behavior, and all business logic.

## Safety

The generator refuses to run unless:

- branch is `main`;
- HEAD is the approved baseline;
- all three target blobs exactly match the approved source;
- generated patch scope contains exactly the three files above;
- `git apply --check` succeeds.

It does not commit, push, deploy, restart services, or run migrations.
