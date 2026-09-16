# TOS Task Board R32 — Trello-like Card Modal Navigation

VERSION=TOS_TASK_BOARD_R32
PATCH=TOS-TASK-BOARD-R32-TRELLO-LIKE-CARD-MODAL-NAVIGATION
BASE_TOS_COMMIT=f3671756ba1c49ae7304509276d52eb5cb69d04d

## Goal
Make task-card opening/navigation feel immediate and contextual like Trello while preserving the TOS task-details functionality and approved content design.

## Presentation / interaction changes
- Keep the board mounted and visible behind Task Details.
- Replace the opaque full-screen Task Details page treatment with a large centered overlay modal.
- Add a dim/soft-blur backdrop and close on backdrop click.
- Keep Escape close through the existing focus trap.
- Use an explicit X close control.
- Expose previous/next task controls in the visible canonical header.
- Open the modal immediately from the card using existing card data; hydrate full task details in the background.
- Prefetch full task details on card hover/focus.
- Update the `taskId` query parameter without navigating away from `/tasks`.
- Browser Back closes a task opened from the board and restores the same board context.
- Previous/next navigation replaces the current `taskId` instead of creating noisy history entries.
- Mobile/narrow widths intentionally fall back to a full-height sheet for usability.

## Must remain unchanged
- Task CRUD logic and permissions.
- Backend/API/database schemas.
- Drag/drop and board data.
- Existing Task Details tabs, editors, time tracking, comments, attachments, right rail and R30 styling.
- TCS / Ramzy / Central Chat.
- Source push policy: installer deploys live build only; no git/push in `/var/www/TOS`.
