# TOS Task Board R32_R7 — True Desktop Window

VERSION=TOS_TASK_BOARD_R32_R7
PATCH=TOS-TASK-BOARD-R32-R7-TRUE-DESKTOP-WINDOW
BASE_TOS_MAIN_REVIEWED=8e13de3b447b1a85e907efc2f1a2ed423c075c36
REQUIRES=R32 through R32_R6_R1 already pushed/applied

Purpose: make Task Details behave like a real desktop window instead of a large modal.

Changes:
- Normal desktop window opens centered at about 74% viewport width / 76% viewport height.
- New storage key resets the old oversized saved geometry once, then persists the user's new size and position.
- Dragging from the Task Details header is preserved; double-clicking the header toggles maximize/restore.
- Resizing works from all 4 edges and all 4 corners: left, right, top, bottom, and every corner.
- Normal resize minimum is 720x480; viewport bounds are enforced.
- Minimize stays a compact floating bar (~340–460px wide), preserving title + Restore + Close.
- Maximize is still full viewport with inset; Restore returns to the exact prior normal size and position.
- Board remains visible and mouse-interactive behind the floating desktop window on desktop.
- Mobile <=900px remains fullscreen and does not expose desktop resize handles.
- Existing task logic, permissions, URL/back navigation, prev/next, backend/API/database are unchanged.

No source push.