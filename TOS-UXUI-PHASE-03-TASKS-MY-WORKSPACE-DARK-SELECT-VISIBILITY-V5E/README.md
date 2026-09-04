# Phase 03 — Tasks / My Workspace Dark Select Visibility V5E

Focused screenshot-driven visibility fix for `/my-workspace` after the V5D flagship review.

Fixes:
- Project filter dropdown text/options in Dark Mode.
- Day dropdown text/options in Dark Mode.
- Month dropdown text/options in Dark Mode.
- Status and Priority native dropdowns in the task editor use the same visibility lock.
- Forces the browser native select popup to use a dark color scheme plus explicit zinc background / light text.
- Light Mode visual intent remains unchanged.
- No task logic, filtering logic, permissions, Ramzy, TCS, or Help Center behavior changes.
- Preserves the already-applied V5D Tasks board tracked changes.
- Build target: `frontend/dist`; live target: `/opt/apps/tamiyouz-front/build`.
- No local port 80 health check. No commit or push to TOS.

Run from a separate TOS-Patchs checkout:

```bash
bash TOS-UXUI-PHASE-03-TASKS-MY-WORKSPACE-DARK-SELECT-VISIBILITY-V5E/apply_phase03_tasks_my_workspace_dark_select_visibility_v5e.sh /var/www/TOS
```
