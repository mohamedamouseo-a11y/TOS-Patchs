# Phase 04.1 — Design Queue Flagship V3

Single-screen premium redesign for **Design Queue only**, layered on top of the already-applied Phase 04 V2 worktree.

Goals:
- Push the screen from merely clean/dark into a flagship executive board.
- Stronger KPI hierarchy, command-bar controls, richer column identity, premium compact request cards, and deeper Obsidian / Black Titanium surfaces.
- Preserve the existing Design Queue structure and all business behavior.
- Keep Light mode elegant while making Dark mode the flagship reference.

Visual direction:
- Obsidian / Black Titanium foundation.
- Champagne-gold framing and restrained metallic highlights.
- Status-specific column accents: amber / blue / violet / orange / emerald.
- Layered cards, subtle spotlights, refined borders, compact metadata and controlled hover elevation.
- No noisy glow, no heavy gradients, no business-logic changes.

Scope:
- `frontend/src/pages/DesignQueuePage.jsx` is validated but not modified.
- `frontend/src/index.css` receives the V3 visual layer only.
- Team Members, THRS, Team Performance and every other screen remain untouched.

Run:

```bash
bash TOS-UXUI-PHASE-04-1-DESIGN-QUEUE-FLAGSHIP-V3/apply_phase04_1_design_queue_flagship_v3.sh /var/www/TOS
```

The script requires the exact reviewed Phase 04 V2 worktree hashes, appends only the V3 Design Queue visual layer, builds, deploys, validates live assets, and never commits or pushes TOS.
