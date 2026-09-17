# TOS-TASK-BOARD-R32-R7-R1-R1-CONTRACT-RECOVERY

Recovery for the R32_R7_R1 installer contract mismatch.

## Scope
- Requires live R32_R7.
- Applies the intended R32_R7_R1 desktop-window proportion tuning.
- Uses context-aware normalization for minimized geometry/drag width instead of assuming exactly two identical source expressions.
- Normal default: ~65% viewport width x 70% viewport height.
- Desktop minimum: 620x420.
- Minimized floating width: 380-440px.
- Keeps 4 edge + 4 corner resize, drag, maximize/restore, board interaction and mobile fullscreen behavior.
- Changes frontend source + one additive stylesheet only.
- No backend/API/database changes.
- No source push.

## Failure behavior
Guard/build/deploy failure stops and rolls back. No manual fallback.
