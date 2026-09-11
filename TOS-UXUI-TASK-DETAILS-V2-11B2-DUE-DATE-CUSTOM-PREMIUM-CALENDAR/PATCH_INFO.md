# TOS Task Details V2.11B2

VERSION=TOS_TASK_DETAILS_V2_11B2
MICRO_STEP=DUE_DATE_CUSTOM_PREMIUM_CALENDAR
BASELINE_CHAIN=TOS_TASK_DETAILS_V2_11B1

Scope is intentionally limited to the primary Due Date control.

Replace the native browser date picker with a TOS-owned premium portal calendar while preserving the existing `savePatch({ dueDate })` contract.

Calendar requirements:
- custom trigger inside the approved Due Date card;
- portal popover rendered to `document.body` so Hero overflow cannot clip it;
- month navigation;
- 6-week day grid;
- selected date state;
- today state;
- Today and Clear actions;
- outside-click and Escape close behavior;
- locale-aware month/day labels;
- no backend/API/data-contract changes.

Frozen: Hero shell, Task identity, four-card geometry, Assignees, V2.11B1 Status/Priority custom dropdowns, Start Date advanced path, tabs, Description/Editor, Right Rail, Ramzy AI Assistant, TCS System Chat, APIs, DB, permissions, upload logic, TWS.

Ramzy = AI Assistant. TCS = System Chat.
