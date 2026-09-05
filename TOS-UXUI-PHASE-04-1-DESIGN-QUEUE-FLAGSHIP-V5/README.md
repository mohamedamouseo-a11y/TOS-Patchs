# Phase 04.1 — Design Queue Flagship V5

Screenshot-driven single-screen refinement for **Design Queue only**.

V4 was technically correct but still visually too flat. V5 pushes the screen further toward an executive flagship product without changing behavior.

Main refinements:
- KPI area becomes six horizontal executive tiles with stronger status identity and less empty space.
- Designer Capacity is compressed into a tighter premium rail.
- Filters become a denser integrated command strip.
- Board header is cleaner and removes the harsh line feel in Dark.
- Each workflow column owns its status accent and subtle surface tint.
- Request cards inherit their column status accent instead of using gold everywhere.
- Dark uses layered Black Titanium / Obsidian surfaces; Light uses restrained porcelain/ivory.

Safety:
- Visual CSS layer only.
- `DesignQueuePage.jsx` remains byte-identical to the verified V4 worktree.
- THRS, Team Members and Team Performance are SHA-pinned and must remain unchanged.
- No API, permissions, calculations, workflow state, save behavior or business logic changes.
- Build and live deploy are validated.
- No commit or push is performed in TOS.

Run:

```bash
bash TOS-UXUI-PHASE-04-1-DESIGN-QUEUE-FLAGSHIP-V5/apply_phase04_1_design_queue_flagship_v5.sh /var/www/TOS
```
