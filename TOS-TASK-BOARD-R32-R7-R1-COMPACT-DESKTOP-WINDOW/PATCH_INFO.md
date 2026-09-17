# TOS-TASK-BOARD-R32-R7-R1-COMPACT-DESKTOP-WINDOW

Small follow-up to R32_R7 after visual QA.

## Goal
- Make the normal Task Details window feel like a real desktop window, not near-fullscreen.
- Fresh default size: ~65% viewport width x ~70% viewport height.
- Smaller safe minimum size: 600x420.
- Keep free drag.
- Make all 4 edge + 4 corner resize hit-zones reliably usable from inside the window bounds.
- Compact minimized bar ~360–420px.
- Preserve maximize/restore, URL/task logic, board interactivity behind the window, mobile fullscreen, backend/API/DB.
- Use a new localStorage key so the old R32_R7 saved 74x76 geometry cannot mask the new default.

## Base contract
Live `/var/www/TOS` must already contain successful R32_R7.
Source repo reviewed base remains `8e13de3b447b1a85e907efc2f1a2ed423c075c36`; R32_R7 itself is not source-pushed yet.

## Safety
Installer only. No manual fallback. No git inside `/var/www/TOS`. No source push.
