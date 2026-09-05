# TOS UX/UI — Phase 04.1 Design Queue Flagship V6

Screenshot-driven visual refinement for **Workspace → Design Queue** only.

## Goals
- Reduce oversized vertical dead space in collapsed capacity and filter areas.
- Strengthen KPI hierarchy while keeping the six-tile executive summary.
- Make the board frame, column identity, cards, and typography feel more flagship/premium.
- Improve Light contrast with crisp Porcelain/Ivory surfaces.
- Deepen Dark mode using Obsidian / Black Titanium / Platinum / Champagne.
- Force capacity/filter rails to static positioning to avoid inherited sticky/fixed capture duplication.

## Scope
- Visual CSS layer only.
- No business logic, API, data flow, permissions, or JSX changes.
- Requires the exact verified V5 worktree state.
- Builds and deploys `/var/www/TOS/frontend/dist` to `/opt/apps/tamiyouz-front/build` with backup/rollback safeguards.

## Run
```bash
bash TOS-UXUI-PHASE-04-1-DESIGN-QUEUE-FLAGSHIP-V6/apply_phase04_1_design_queue_flagship_v6.sh /var/www/TOS
```

Do not reset, stash, commit, or push the TOS repository while applying this patch.
