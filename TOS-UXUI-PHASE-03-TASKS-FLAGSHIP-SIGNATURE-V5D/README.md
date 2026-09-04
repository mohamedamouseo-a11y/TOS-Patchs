# Phase 03 — Tasks Flagship Signature V5D

Clean V5 recovery after V5/V5R/V5RR/V5C failed on stale or nonexistent task-card guards.

V5D:
- Validates the exact reviewed V4 tracked files by content.
- Ignores harmless untracked recovery folders left in `/var/www/TOS`.
- Does not depend on `.tos-modern-task-card` or `data-tos-task-card-layout-polish` checks.
- Adds only the semantic KPI/Kanban hooks needed for the flagship layout.
- Uses structural `article` selectors inside Kanban columns as a task-card fallback.
- Applies the original V5 flagship CSS plus the V5D fallback.
- Builds `frontend/dist` and deploys to `/opt/apps/tamiyouz-front/build`.
- Validates deployment by runtime sentinels in the live assets, not by local port 80.
- No commit or push to TOS.

Run from a separate TOS-Patchs checkout:

```bash
bash TOS-UXUI-PHASE-03-TASKS-FLAGSHIP-SIGNATURE-V5D/apply_phase03_tasks_flagship_signature_v5d.sh /var/www/TOS
```
