# TOS TASK BOARD R32_R1 — Modal Visibility Recovery

Patch: `TOS-TASK-BOARD-R32-R1-MODAL-VISIBILITY-RECOVERY`

Purpose: recover the R32 Trello-like task-details modal when the backdrop renders but the dialog remains invisible.

Scope:
- keep the board visible behind the modal
- keep R32 immediate open/prefetch/URL/back behavior
- keep previous/next task navigation
- remove the conflicting Framer Motion entrance state from the dialog
- add a small CSS-only dialog entrance animation with forced visible/flex/position/z-index contracts

No backend/API/database/storage/permissions changes.
No source push.
