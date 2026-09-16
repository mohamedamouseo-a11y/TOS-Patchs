# TOS_TASK_BOARD_R32_R4

PATCH=TOS-TASK-BOARD-R32-R4-WINDOW-STATE-SPECIFICITY-FIX
BASE_TOS_MAIN_REVIEWED=3bb74d81ab67db42da9d435b391c6530bf29c96d
REQUIRES_LIVE_R32_R3=YES

Purpose: fix R32_R3 desktop window state CSS specificity so Minimize and Maximize visibly override the normal draggable/resizable window geometry.

Scope:
- CSS specificity/state override only.
- Minimize becomes a real 64px compact task bar.
- Maximize fills the viewport with 12px margins.
- Restore returns to the existing R32_R3 size/position variables.
- Drag/resize logic, localStorage persistence, R32/R1/R2/R3 navigation and modal behavior are preserved.
- Mobile behavior remains unchanged.

No backend/API/database/storage/permission changes.
No TOS source push.
