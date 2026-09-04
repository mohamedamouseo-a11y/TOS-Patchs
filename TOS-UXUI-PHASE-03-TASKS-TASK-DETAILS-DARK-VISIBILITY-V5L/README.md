# Phase 03 — Tasks / Task Details Dark Visibility V5L

Final screenshot-driven Dark Mode visibility repair after V5K.

The latest screenshot still showed two concrete issues:
- Due date / Start date values were effectively invisible in Chromium/Windows Dark Mode even though the input parent had a light color.
- Save Description still lacked strong visual contrast against the editor footer.

V5L fixes those exact controls:
- Adds semantic hooks to the two Task Details date inputs and the Save Description button.
- Styles Chromium/WebKit native date sub-parts explicitly (`::-webkit-datetime-edit-*`) so month/day/year values stay visible.
- Keeps the calendar picker visible.
- Gives Save Description a clear Champagne hardware treatment with dark ink.
- Keeps Task Details selects/options explicitly readable in Dark Mode.
- Light Mode unchanged.
- No business logic, permissions, workflow, editor, timer or save behavior changes.

The apply script validates the current V5G + V5I + V5K runtime state semantically, preserves the same three tracked Phase 03 files, builds `frontend/dist`, deploys to `/opt/apps/tamiyouz-front/build`, validates runtime/hooks in built/live assets, and does not commit or push TOS.

Run from a separate TOS-Patchs checkout:

```bash
bash TOS-UXUI-PHASE-03-TASKS-TASK-DETAILS-DARK-VISIBILITY-V5L/apply_phase03_tasks_task_details_dark_visibility_v5l.sh /var/www/TOS
```
