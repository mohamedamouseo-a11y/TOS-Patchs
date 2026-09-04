# Phase 03 — Tasks / My Workspace Dark Select Visibility V5F

Robust replacement for failed V5E.

Why V5E failed:
- Its regex stopped at the `>` character inside JSX arrow functions such as `onChange={(event) => ...}`, so it detected zero workspace filter selects.

V5F avoids that brittle selector counting entirely:
- Adds one semantic root hook: `tos-my-workspace`.
- Applies Dark Mode native select styling to every select under My Workspace, including Project, Day, Month, Status, and Priority.
- Forces `color-scheme: dark` and explicit dark option backgrounds / light text for Windows/Chrome native dropdown popups.
- Preserves the already-applied V5D tracked changes.
- Light Mode unchanged.
- No business logic changes.
- Builds `frontend/dist` and deploys to `/opt/apps/tamiyouz-front/build`.
- No local port 80 health check.
- No commit or push to TOS.

Run from a separate TOS-Patchs checkout:

```bash
bash TOS-UXUI-PHASE-03-TASKS-MY-WORKSPACE-DARK-SELECT-VISIBILITY-V5F/apply_phase03_tasks_my_workspace_dark_select_visibility_v5f.sh /var/www/TOS
```
