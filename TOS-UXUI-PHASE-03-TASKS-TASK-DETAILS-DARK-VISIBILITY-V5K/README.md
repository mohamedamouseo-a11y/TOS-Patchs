# Phase 03 — Tasks / Task Details Dark Visibility V5K

Recovery for the V5J false stop caused by an exact full-file stylesheet checksum guard.

V5K preserves the same visual intent as V5J but validates the real Phase 03 state semantically:
- exactly the three expected tracked files are modified;
- Task Details root hook exists once;
- My Workspace hook exists once;
- V5G and V5I runtime markers exist once;
- V5I rich-editor contrast selectors are still present;
- V5J/V5K runtime markers are absent before apply.

Then V5K appends only the scoped Dark Mode visibility CSS for native date/select controls, Save Description CTA, muted helper text, placeholders and disabled states. Light Mode and business logic are unchanged.

It builds `frontend/dist`, deploys to `/opt/apps/tamiyouz-front/build`, validates runtime markers in built/live assets, does not use a local port 80 health check, and does not commit or push TOS.

Run from a separate TOS-Patchs checkout:

```bash
bash TOS-UXUI-PHASE-03-TASKS-TASK-DETAILS-DARK-VISIBILITY-V5K/apply_phase03_tasks_task_details_dark_visibility_v5k.sh /var/www/TOS
```
