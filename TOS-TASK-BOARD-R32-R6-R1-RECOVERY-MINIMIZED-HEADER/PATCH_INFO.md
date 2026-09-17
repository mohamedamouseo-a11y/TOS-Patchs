# TOS Task Board R32_R6_R1 — Recovery Minimized Header

VERSION=TOS_TASK_BOARD_R32_R6_R1
PATCH=TOS-TASK-BOARD-R32-R6-R1-RECOVERY-MINIMIZED-HEADER
REQUIRES=R32_R5 + R32_R6 currently applied on live source

Purpose: recover the Tasks page from the R32_R6 runtime regression while keeping the requested minimized-task experience.

Changes:
- Remove the R32_R6 injected mini-window JSX and its stylesheet import.
- Restore the proven R32_R5 render path.
- Reuse the existing R32_R3 header/title/restore/close controls as the minimized 64px bar.
- Strengthen minimized CSS only; no new render-time JSX.
- Allow pointer interaction with the board behind while minimized, while keeping the minimized bar interactive.
- Preserve normal window, maximize, restore, drag, resize, URL/back navigation, prefetch, and mobile fullscreen behavior.

No backend/API/database changes. No source push.