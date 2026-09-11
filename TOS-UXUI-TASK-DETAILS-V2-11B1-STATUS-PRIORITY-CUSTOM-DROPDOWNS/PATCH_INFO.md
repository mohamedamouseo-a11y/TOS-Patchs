# TOS Task Details V2.11B1

VERSION=TOS_TASK_DETAILS_V2_11B1
MICRO_STEP=STATUS_PRIORITY_CUSTOM_DROPDOWNS
BASELINE_CHAIN=TOS_TASK_DETAILS_V2_11B

Scope is intentionally limited to the two openable Hero controls:

1. Status
2. Priority

The native browser `<select>` UI is replaced with a custom premium popover/listbox while preserving the exact existing values and save handlers.

Implementation notes:
- trigger stays inside the approved V2.11B control card;
- opened menu is rendered with `createPortal` to `document.body` so the approved Hero `overflow:hidden` cannot clip it;
- supports outside click, Escape, ArrowUp/ArrowDown and Enter/Space selection;
- no API, data-contract, permission, task-status, priority, or persistence logic changes.

Frozen and out of scope: Hero shell, Task identity, four-card geometry, Assignees, Due Date calendar, Start Date advanced path, tabs, Description/Editor, Right Rail, Ramzy AI Assistant, TCS System Chat, APIs, DB, permissions, upload logic, TWS.

Ramzy = AI Assistant. TCS = System Chat.
