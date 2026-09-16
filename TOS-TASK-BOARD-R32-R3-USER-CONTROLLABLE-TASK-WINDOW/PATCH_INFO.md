# TOS Task Board R32_R3 — User Controllable Task Window

Incremental production patch on top of R32 + R32_R1 + R32_R2.

## Goal
Keep the approved Trello-like task overlay, but let the user control the task window instead of forcing one near-full-screen size.

## UX
- Drag the task window from its canonical header.
- Resize from the physical right edge, bottom edge, or bottom-right corner.
- Minimize / restore from the header.
- Maximize / restore from the header.
- Preserve the user's normal window size and position in localStorage.
- Clamp the window inside the viewport.
- Mobile/tablet <= 900px stays full-screen and disables desktop drag/resize controls.
- Minimized mode becomes a compact floating header and exposes more of the board.

## Scope
Presentation/window interaction only. Task data, permissions, APIs, backend, database, R32 prefetch, URL/back behavior, previous/next navigation, R31 chat, and existing Task Details business logic remain unchanged.

## Required live baseline
- R32 marker: `--tos-task-board-r32-trello-card-modal-runtime`
- R32_R1 marker: `--tos-task-board-r32-r1-modal-visibility-runtime`
- R32_R2 marker: `--tos-task-board-r32-r2-body-portal-runtime`
- R32_R2 body portal host: `tos-task-r32-r2-portal-host`

## Source baseline reviewed
`3bb74d81ab67db42da9d435b391c6530bf29c96d`

R32_R1/R2 are runtime incremental patches after that source commit, so the installer verifies those live markers before applying R32_R3.

No source push is performed by the installer.
