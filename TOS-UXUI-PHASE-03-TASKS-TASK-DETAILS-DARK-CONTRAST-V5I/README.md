# Phase 03 — Tasks / Task Details Dark Contrast V5I

Screenshot-driven Dark Mode readability repair for the full-screen Task Details view.

Fixes:
- Task title contrast in Dark Mode.
- Long rich-text task description that becomes almost invisible because saved Light Mode inline colors override the editor parent color.
- Headings, paragraphs, lists, links, code and blockquotes receive readable Dark Mode contrast.
- Light Mode is unchanged.
- No task logic, permissions, workflow, timer, editor behavior or save behavior changes.
- Preserves the already-applied V5H/V5G My Workspace state.
- Builds `frontend/dist` and deploys to `/opt/apps/tamiyouz-front/build`.
- No local port 80 health check.
- No commit or push to TOS.

Run from a separate TOS-Patchs checkout:

```bash
bash TOS-UXUI-PHASE-03-TASKS-TASK-DETAILS-DARK-CONTRAST-V5I/apply_phase03_tasks_task_details_dark_contrast_v5i.sh /var/www/TOS
```
