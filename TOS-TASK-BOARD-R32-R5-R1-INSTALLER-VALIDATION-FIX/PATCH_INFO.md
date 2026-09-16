# TOS Task Board R32_R5_R1 — Installer Validation Fix

VERSION=TOS_TASK_BOARD_R32_R5_R1
PATCH=TOS-TASK-BOARD-R32-R5-R1-INSTALLER-VALIDATION-FIX
BASE_PATCH_COMMIT=bfac9dbc1f756c707eb59b27defb385e37cee436
REQUIRES=R32_R3 + R32_R4 already applied on live source; prior R32_R5 attempt rolled back on validation failure

Purpose: fix only the R32_R5 installer guard that incorrectly expected the token `taskWindowGeometryR32R5` to occur exactly once, even though the valid transformed JSX references it multiple times.

Behavioral payload remains the original R32_R5 payload unchanged:
- Normal desktop window ~84% x 82% viewport.
- Real 64px minimize.
- Real maximize with 12px viewport inset.
- Restore keeps normal size/position.
- Drag/resize preserved.
- New localStorage key preserved.
- Mobile <=900px stays fullscreen.

No manual source fallback. No backend/API/database changes. No source push.