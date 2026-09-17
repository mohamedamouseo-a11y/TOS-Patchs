# TOS-TASK-BOARD-R32-R7-R1-DESKTOP-WINDOW-PROPORTION-TUNING

Purpose: visual recovery/tuning on top of R32_R7 live state.

Changes only the Task Details desktop window behavior:
- fresh storage key so old large saved geometry cannot mask the fix
- default normal window ~65% viewport width x 70% viewport height
- smaller desktop minimum 620x420
- minimized floating bar clamped to 380-440px
- larger resize hit areas on all 4 edges + 4 corners
- preserves drag, maximize/restore, double-click header, board interaction, mobile fullscreen

No backend/API/database changes.
No source push.
Apply with installer only; no manual fallback.
