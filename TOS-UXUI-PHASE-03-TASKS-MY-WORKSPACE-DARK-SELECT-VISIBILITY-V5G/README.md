# Phase 03 — Tasks / My Workspace Dark Select Visibility V5G

Consolidated recovery after V5E/V5F execution confusion.

Important:
- Prints `RUNNING=V5G_CONSOLIDATED` immediately so the executed script is unmistakable.
- Contains no `workspace filter select count` logic.
- If the TOS worktree is clean and V5D source changes are missing, it reapplies V5D first from the separate TOS-Patchs checkout.
- Then adds a single `tos-my-workspace` root hook and Dark Mode native-select styling for all selects under My Workspace.
- Fixes Project / Day / Month and editor Status / Priority dropdown visibility.
- Uses `color-scheme: dark` plus explicit option/optgroup foreground and background colors.
- Preserves Light Mode visual intent and does not change task/filter business logic.
- Builds `frontend/dist`, deploys to `/opt/apps/tamiyouz-front/build`, and validates via runtime sentinels rather than local port 80.
- No commit or push to TOS.

Run from a separate TOS-Patchs checkout:

```bash
bash TOS-UXUI-PHASE-03-TASKS-MY-WORKSPACE-DARK-SELECT-VISIBILITY-V5G/apply_phase03_tasks_my_workspace_dark_select_visibility_v5g.sh /var/www/TOS
```
