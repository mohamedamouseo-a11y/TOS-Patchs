# Phase 03.4 — Task Title Auto-Fit + First-Time Coach Cue V2

Recovery for the failed V1 build.

Root cause: the installed `lucide-react` package does not export `HandPointer`.

V2 preserves all Phase 03.4 behavior and only replaces that unsupported icon dependency with an inline dependency-free vector hand inside the existing coach bubble.

Preserved behavior:
- auto-growing wrapped task title;
- first-time coach cues for **More details** and **Side details**;
- maximum three impressions;
- cue disappears immediately once the user opens that disclosure;
- learned state persists in localStorage;
- Light + Dark and reduced-motion support;
- no task/server data, permissions, workflow, save semantics, APIs or business logic changes.

The recovery script expects the partial V1 state left by the failed build, validates Phase 03.1/03.2/03.3/03.4 semantic hooks, removes `HandPointer`, installs the inline vector, builds, deploys, validates live assets, and never commits or pushes TOS.

Run:

```bash
bash TOS-UXUI-PHASE-03-4-TASK-TITLE-COACH-CUE-V2/apply_phase03_4_task_title_coach_cue_v2.sh /var/www/TOS
```
