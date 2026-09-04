# Phase 03 — Tasks Flagship Signature V5C

Clean recovery for the V5 flagship Tasks board after V5/V5R/V5RR execution-path and stale-baseline failures.

Key fixes:
- Run from a real, separate `TOS-Patchs` checkout instead of copying patch folders into `/var/www/TOS`.
- Validate the exact reviewed V4 worktree by blob content, not stale committed-baseline assumptions.
- Ignore only harmless untracked recovery folders left by previous failed attempts.
- Apply the V5 semantic KPI/Kanban hooks and flagship CSS on top of the exact V4 state.
- Build `frontend/dist`, deploy to `/opt/apps/tamiyouz-front/build`, and validate live assets by runtime sentinel.
- Does not depend on local port 80 being open.
- No commit or push to TOS.

Run from a separate TOS-Patchs checkout:

```bash
bash TOS-UXUI-PHASE-03-TASKS-FLAGSHIP-SIGNATURE-V5C/apply_phase03_tasks_flagship_signature_v5c.sh /var/www/TOS
```
