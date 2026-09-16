# TOS Task Board R32_R5 — Inline Window Geometry Fix

VERSION=TOS_TASK_BOARD_R32_R5
PATCH=TOS-TASK-BOARD-R32-R5-INLINE-WINDOW-GEOMETRY-FIX
BASE_TOS_MAIN_REVIEWED=3bb74d81ab67db42da9d435b391c6530bf29c96d
REQUIRES=R32_R3 + R32_R4 already applied on live source

Purpose: make the desktop Task Details window geometry state-driven instead of relying on competing legacy CSS geometry rules.

Changes:
- Normal desktop window defaults to ~84% viewport width / ~82% viewport height, clamped safely.
- Minimize becomes a real 64px task bar.
- Maximize becomes a true viewport-filling window with 12px inset.
- Restore returns to the preserved normal size and position.
- Drag/resize continue to update the normal geometry.
- A new localStorage key avoids inheriting oversized R32_R3 geometry.
- Mobile <=900px stays fullscreen.
- Tiny R5 CSS bridge only gives the inline state variables authority over prior `!important` geometry rules.

No backend/API/database changes. No source push.