# Phase 04.1 — Design Queue Structural Flagship V6

Single-screen structural visual redesign for **Design Queue only**.

Why V6 exists:
- V4/V5 improved styling, but the screenshots showed the screen was still materially using the same visual structure.
- V6 stops stacking CSS-only illusions and introduces explicit Design Queue markup hooks so the premium layout is deterministic.

What changes:
- KPI summary becomes real horizontal executive cards: compact orbit + value + label/note, with status-specific identity.
- Designer Capacity becomes a compact executive rail.
- Filters become a tighter command bar.
- Board gets a dedicated flagship shell/header.
- Kanban columns get explicit per-status structural hooks and accent ownership.
- Request cards get explicit premium hooks and inherit the status accent of their column.
- Dark uses layered Obsidian / Black Titanium surfaces; Light uses Porcelain / Ivory.

Safety:
- Only `frontend/src/pages/DesignQueuePage.jsx` markup/classes and `frontend/src/index.css` visual layer are changed.
- No API calls, state, calculations, assignments, permissions, workflow status logic, saves, or backend behavior are changed.
- THRS, Team Members, and Team Performance are SHA-pinned and must stay byte-identical.
- Script requires the exact reviewed V5 hashes, builds, deploys, validates live assets, and performs no commit/push/reset/stash.

Run:

```bash
bash TOS-UXUI-PHASE-04-1-DESIGN-QUEUE-STRUCTURAL-V6/apply_phase04_1_design_queue_structural_v6.sh /var/www/TOS
```
