# Phase 04 — Core Daily Screens Premium Batch V2

Screenshot-driven polish on top of the already-applied Phase 04 V1 worktree.

Fixes:
- **Design Queue / Dark:** removes the white outer Capacity, Filters and Board islands and restores native Obsidian / Black Titanium surfaces with readable controls.
- **Team Members / Dark:** fixes the Departments & Managers table body/header contrast so rows are dark and text is readable.
- **Employee Work Hub (THRS) / Dark:** restores strong heading hierarchy and input readability without changing disabled/action semantics.
- **Team Performance:** intentionally unchanged because Light + Dark were visually accepted in the V1 review.

Light mode remains unchanged except for inherited focus behavior already present in V1.

No APIs, permissions, workflow, team, attendance, performance calculations, save behavior or business logic are changed.

Run:

```bash
bash TOS-UXUI-PHASE-04-CORE-DAILY-SCREENS-BATCH-V2/apply_phase04_core_daily_screens_batch_v2.sh /var/www/TOS
```

The script requires the exact reviewed V1 worktree hashes, appends only the V2 visual layer to `frontend/src/index.css`, builds, deploys, validates live assets, and never commits or pushes TOS.
