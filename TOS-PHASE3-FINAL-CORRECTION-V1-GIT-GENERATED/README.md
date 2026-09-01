# TOS Phase 3 Final Correction V1

Baseline TOS commit: `63f59932776e29e32bacdf5214744d2662a3b8e3`

This patch is intentionally generated from exact source blobs and refuses to run on a different baseline or dirty target files.

## Fixes

1. Team Performance activity attribution is task-assignee based, not actor based.
2. Activity queries select `task.assigneeId` / `task.projectId` and remain project-scoped bulk queries.
3. On-Time scoring uses `eligibleOnTimeCompleted` as the denominator and skips the component when no eligible task exists.
4. The temporary `/reports/team-performance/test-ontime` verification endpoint is removed.
5. Legacy date presets `all`, `7d`, `30d`, and `quarter` are restored without removing Team Performance presets.
6. Weekly/monthly history periods are clamped to the requested end date so future days cannot affect historical overdue/score calculations.
7. `/backend/.pm2/` is added to `.gitignore` and the two generated PM2 files are removed from Git tracking only.

## Assignment convention

Phase 3 Team Performance remains **primary-assignee-only**. This matches the existing reporting queries and aggregation, which use `Task.assigneeId`. The separate `TaskAssignee[]` relation is not used to duplicate score/task credit across secondary assignees in this patch.

## Run

```bash
git clone https://github.com/mohamedamouseo-a11y/TOS-Patchs.git /tmp/TOS-Patchs
bash /tmp/TOS-Patchs/TOS-PHASE3-FINAL-CORRECTION-V1-GIT-GENERATED/run_phase3_final_correction_v1.sh /var/www/TOS
```

The runner:

- does **not** commit;
- does **not** push;
- leaves PM2 runtime files on disk;
- runs backend syntax validation;
- runs the frontend build;
- prints final `git status --short`.

After execution, run authenticated Phase 3 smoke tests and restart/reload the live PM2 services as appropriate. The final TOS push must be performed from the normal Developer Hub/system workflow, not from this patch runner.
