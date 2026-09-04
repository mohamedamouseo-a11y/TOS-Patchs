# Phase 03.4 — Task Title Auto-Fit + First-Time Coach Cue V1

Final UX polish for the Phase 03.2/03.3 Minimal Task Details view.

Changes:
- Replaces the one-line task title input with an auto-growing title field that can wrap naturally for long Arabic/English titles while keeping the existing draft/save-on-blur behavior.
- Prevents Enter from creating title line breaks; wrapping is visual only.
- Adds a clear vector hand-pointer coach cue to **More details** and **Side details**.
- Each cue animates three times, and is shown on at most the first three Task Details openings.
- Opening a disclosure once marks that cue as learned in localStorage, so it disappears immediately and does not return.
- Keeps the older button pulse disabled after the cue is learned.
- Supports Light + Dark and `prefers-reduced-motion`.
- No task/server data, permissions, APIs, workflow, save semantics or business logic are changed.

The apply script requires the existing Phase 03.1, 03.2 and 03.3 semantic runtime hooks, allows only the known Phase 03 tracked files, builds `frontend/dist`, deploys to `/opt/apps/tamiyouz-front/build`, validates live assets, and never commits or pushes TOS.

Run:

```bash
bash TOS-UXUI-PHASE-03-4-TASK-TITLE-COACH-CUE-V1/apply_phase03_4_task_title_coach_cue_v1.sh /var/www/TOS
```
