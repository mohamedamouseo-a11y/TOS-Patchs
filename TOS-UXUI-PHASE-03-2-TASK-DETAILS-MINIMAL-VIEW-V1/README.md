# Phase 03.2 — Task Details Minimal View V1

Second declutter pass for Task Details after Phase 03.1.

Default view now keeps only the essential layer visible:
- Task title
- Status
- Priority
- Due date
- Assignee summary
- Description workspace
- Overview + Checklist tabs

A compact **More details** control reveals the secondary operational layer:
- Start date
- Actual execution time
- Task Progress
- Project / Activity side information
- Comments / Files / Time Tracking / Activity tabs
- Task ID and header context

The existing side rail stays collapsed by default. In minimal mode, expanding it shows assignee detail only; Project and Activity remain behind **More details**.

Light + Dark are supported. No task data, save behavior, permissions, workflow, timer, editor behavior, APIs or business logic are changed.

The script requires the approved Phase 03.1 semantic hooks, allows only the known Phase 03 tracked files, builds `frontend/dist`, deploys to `/opt/apps/tamiyouz-front/build`, validates live assets, and does not commit or push TOS.

Run:

```bash
bash TOS-UXUI-PHASE-03-2-TASK-DETAILS-MINIMAL-VIEW-V1/apply_phase03_2_task_details_minimal_view_v1.sh /var/www/TOS
```
