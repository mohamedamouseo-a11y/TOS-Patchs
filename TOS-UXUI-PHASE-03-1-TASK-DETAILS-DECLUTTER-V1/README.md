# Phase 03.1 — Task Details Declutter V1

Visual declutter pass for Task Details after Phase 03 approval.

Changes:
- Keeps Title / Status / Priority / Dates / execution time visible in a tighter executive summary.
- Compresses the large Task Progress block into a compact instrument strip.
- Uses the existing Task Details tabs as the primary information architecture.
- Collapses Assignee / Project / Activity into a compact side rail by default, expandable with one click.
- Keeps Description as the default work area and reduces editor minimum height.
- Adds a `decluttered` advanced editor variant: everyday tools stay visible; block/font/alignment/color controls sit behind **More** while fullscreen remains available.
- Keeps Save Description sticky and reachable.
- Light + Dark supported.
- No business logic, permissions, workflow, task data, timer or save behavior changes.

The script accepts the current approved V5L Phase 03 worktree whether it is still pre-push or has just been committed through the TOS Push flow. It only allows the expected Phase 03 tracked files, validates V5G/V5I/V5K/V5L semantic runtime markers, builds, deploys, validates live assets, and never commits or pushes TOS.

Run from a separate `TOS-Patchs` checkout:

```bash
bash TOS-UXUI-PHASE-03-1-TASK-DETAILS-DECLUTTER-V1/apply_phase03_1_task_details_declutter_v1.sh /var/www/TOS
```
