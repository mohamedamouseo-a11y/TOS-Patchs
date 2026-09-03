# TOS UX/UI Phase 02 — Projects Ultra Premium Black Titanium V6

Screen scope: **Projects only** (`.tos-projects-ui03`).

Dark-first refinement built on the reviewed V4 server state. This patch does not change business logic or Projects JSX. It appends presentation CSS only, rebuilds the frontend, verifies a runtime custom-property sentinel in compiled assets, and deploys the built frontend to `/opt/apps/tamiyouz-front/build` with a timestamped backup.

## Visual goals

- Black Titanium canvas and three clear dark surface levels.
- Champagne Gold limited to CTA, selection, focus, and key accents.
- Higher contrast for labels, metadata, dates, controls, pagination, and buttons.
- Selected project row changed from gold slab to graphite + champagne rail/glow.
- Selected-project inspector upgraded to near-black navy / titanium glass.
- KPI cards refined with metallic edge depth and restrained semantic halos.
- Command bar and filter tray separated into stronger visual layers.
- Black-glass search/select/input controls with explicit focus treatment.
- Secondary actions remain titanium; primary actions use champagne metal.
- Light mode remains porcelain/ivory and removes heavy mustard selection.

## Expected current TOS state

- `frontend/src/main.jsx` modified only by the Phase 02 Projects stylesheet import.
- `frontend/src/styles/projects-github-reference.css` untracked and currently at the reviewed V4 SHA256:
  `1de7ff873d62958aaad7d66ba945a5918de515cd1fe9b0ffe0980bc2a91a5454`
- V4 runtime sentinel present.
- No staged changes.

## Run

```bash
bash TOS-UXUI-PHASE-02-PROJECTS-ULTRA-PREMIUM-BLACK-TITANIUM-V6/apply_phase02_projects_ultra_premium_v6.sh /var/www/TOS
```

Do not reset, stash, commit, or push from OpenHands. Visual review must happen before the user pushes from inside TOS.
