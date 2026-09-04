# Phase 03 — Tasks / Projects Premium Reference V1

Priority screen: Tasks.

Reference: approved Phase 02 Projects premium design language.

Before/after visual review location:
- Open TOS → Tasks from the sidebar (`/tasks`).
- Review the project gateway state before selecting a project.
- Open any project and review the active task-board state.
- Compare the same two states after applying this patch.

Visual direction:
- Light: Porcelain / Ivory / Champagne with stronger readable contrast.
- Dark: Obsidian / Black Titanium / Platinum / Champagne.
- Gold remains an accent, not a large background treatment.
- Stronger hierarchy for project gateway, controls, cards, task board and metadata.

Scope: presentation only. No task business logic, permissions, drag/drop, filters, realtime, Ramzy, TCS or Help Center behavior changes.

Apply:

```bash
bash TOS-UXUI-PHASE-03-TASKS-PROJECTS-PREMIUM-REFERENCE-V1/apply_phase03_tasks_projects_premium_reference_v1.sh /var/www/TOS
```

The script builds and deploys to `/opt/apps/tamiyouz-front/build` and does not commit or push TOS changes.
