# Phase 03.3 — Task Title Fit + Disclosure Cue V1

Final visual polish for the Phase 03.2 Minimal Task Details view.

Changes:
- Reduces the task title size responsively so long mixed Arabic/English titles stay visually inside the summary instead of feeling cropped.
- Adds a subtle premium discoverability cue to **More details** and collapsed **Side details**.
- The cue is a restrained pulse + chevron movement every ~4.8 seconds, not a constant bounce.
- Motion stops immediately when the disclosure is open.
- Respects `prefers-reduced-motion`.
- Light + Dark supported.
- No task data, permissions, workflow, save behavior, APIs or business logic changes.

The apply script requires the approved Phase 03.1 + 03.2 runtime hooks, allows only the known Phase 03 tracked files, builds and deploys the frontend, validates live assets, and never commits or pushes TOS.

Run:

```bash
bash TOS-UXUI-PHASE-03-3-TASK-TITLE-DISCLOSURE-CUE-V1/apply_phase03_3_task_title_disclosure_cue_v1.sh /var/www/TOS
```
