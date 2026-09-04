# Phase 03 — Tasks Active Board Premium V3

Screenshot-driven refinement of the active Tasks board after the V2 gateway review.

Review location:
- TOS → Tasks (`/tasks`)
- Open any project
- Compare the active task board in Light and Dark before/after V3

V3 targets:
- Fix faint KPI ring numbers in Dark Mode.
- Remove muddy gold/brown treatment from Workspace Tools selected surfaces.
- Rebuild board columns as Obsidian/Titanium in Dark Mode.
- Refine board columns in Light Mode using Porcelain/Ivory/Champagne depth.
- Convert the column primary `Add task` action to restrained Champagne Gold.
- Improve empty-column and metadata contrast.

Reference: approved Phase 02 Projects premium design language.

Presentation only. No task business logic, permissions, drag/drop, realtime, Ramzy, TCS, or Help Center behavior changes.

Apply:

```bash
bash TOS-UXUI-PHASE-03-TASKS-ACTIVE-BOARD-PREMIUM-V3/apply_phase03_tasks_active_board_premium_v3.sh /var/www/TOS
```

The script builds, deploys to `/opt/apps/tamiyouz-front/build`, and does not commit or push TOS changes.
