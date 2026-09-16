# TOS Task Board R32_R6 — Dedicated Minimized Window

VERSION=TOS_TASK_BOARD_R32_R6
PATCH=TOS-TASK-BOARD-R32-R6-DEDICATED-MINIMIZED-WINDOW
REQUIRES=R32_R5 already applied on live source

Purpose: fix the broken minimized state by giving it a dedicated compact UI instead of relying on legacy Task Details sections to collapse correctly.

Changes:
- Adds a dedicated 64px minimized task bar inside the existing R32_R5 window.
- Minimized bar shows task title + Restore + Close only.
- While minimized, all normal Task Details direct children are hidden with a high-specificity R6 rule.
- Restore returns to the existing R32_R5 normal geometry/state.
- Dragging the minimized bar continues to use the existing R32_R3 drag handler.
- Normal, maximize, resize, URL navigation, task logic and mobile behavior remain unchanged.

No backend/API/database/storage changes. No source push.