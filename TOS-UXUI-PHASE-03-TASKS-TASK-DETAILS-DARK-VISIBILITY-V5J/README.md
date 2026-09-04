# Phase 03 — Tasks / Task Details Dark Visibility V5J

Final screenshot-driven Dark Mode visibility sweep after V5I.

V5J fixes the remaining low-contrast elements visible in the latest Task Details screenshot:
- Due date and Start date values.
- Native date/calendar controls.
- Status / Priority native select text and popup options.
- Save Description primary action, which was nearly black-on-black.
- Muted helper copy across Assignee, Project, Activity and editor footer.
- Placeholder/disabled states remain readable.

Light Mode is unchanged. No business logic, permissions, workflow, timer, editor behavior or save behavior changes.

The script requires the exact successful V5I state reported by the user, then appends only scoped CSS, builds `frontend/dist`, deploys to `/opt/apps/tamiyouz-front/build`, validates runtime markers, and does not commit or push TOS.

Run from a separate TOS-Patchs checkout:

```bash
bash TOS-UXUI-PHASE-03-TASKS-TASK-DETAILS-DARK-VISIBILITY-V5J/apply_phase03_tasks_task_details_dark_visibility_v5j.sh /var/www/TOS
```
