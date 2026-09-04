# Phase 03 — Tasks / My Workspace Dark Select Visibility V5H

Post-V5G finalizer for the exact state left after V5G successfully applied, built, and deployed but failed only on an overly-strict final git-status assertion.

V5H:
- Requires the V5G My Workspace root hook and dark-select runtime to already be present exactly once.
- Requires V5/V5D flagship runtime markers and the three semantic board hooks.
- Accepts `ProfessionalTaskBoard.jsx` being either already committed/clean or still modified; it validates hook presence instead of requiring the file to appear in `git diff`.
- Requires `MyTaskWorkspace.jsx` and the premium Tasks stylesheet to remain modified, with no unexpected tracked files.
- Rebuilds `frontend/dist` and redeploys to `/opt/apps/tamiyouz-front/build`.
- Validates live assets by runtime sentinels; no local port 80 check.
- No commit or push to TOS.

Run from a separate TOS-Patchs checkout:

```bash
bash TOS-UXUI-PHASE-03-TASKS-MY-WORKSPACE-DARK-SELECT-VISIBILITY-V5H/apply_phase03_tasks_my_workspace_dark_select_visibility_v5h.sh /var/www/TOS
```
