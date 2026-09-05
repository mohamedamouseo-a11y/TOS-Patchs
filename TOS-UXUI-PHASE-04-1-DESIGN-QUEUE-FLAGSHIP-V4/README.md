# Phase 04.1 — Design Queue Flagship V4

Screenshot-driven visual refinement for **Design Queue only**.

This V4 replaces the still-flat V3 appearance with a stronger flagship executive treatment while preserving all behavior.

Changes:
- Six KPI metrics become distinct executive tiles instead of floating rings.
- Designer Capacity becomes a tighter premium rail instead of a large empty slab.
- Filters become a compact integrated command bar.
- Board frame gains cleaner editorial hierarchy and restrained metallic framing.
- Every workflow column gets its own status identity: amber, blue, violet, orange, emerald.
- Request cards inherit the status accent instead of using gold everywhere.
- Dark mode uses true Black Titanium / Obsidian layered surfaces with restrained depth.
- Light mode uses porcelain/ivory with quieter premium contrast.

Scope and safety:
- `frontend/src/pages/DesignQueuePage.jsx` is validated and remains byte-identical.
- Only a new Design Queue visual layer is appended to `frontend/src/index.css`.
- THRS, Team Members, Team Performance and all other screens are not modified by V4.
- No APIs, permissions, calculations, state transitions or business logic are changed.
- Script pins the exact verified V3 hashes, builds, deploys, validates runtime markers, and never commits/pushes TOS.

Run:

```bash
bash TOS-UXUI-PHASE-04-1-DESIGN-QUEUE-FLAGSHIP-V4/apply_phase04_1_design_queue_flagship_v4.sh /var/www/TOS
```
