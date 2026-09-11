# TOS Task Details V2.11B3

VERSION=TOS_TASK_DETAILS_V2_11B3
MICRO_STEP=ASSIGNEES_CUSTOM_SELECTOR
BASELINE_CHAIN=TOS_TASK_DETAILS_V2_11B2

Scope is intentionally limited to the Assignees Hero control.

Target:
- replace the current simple assignee card interaction with a custom premium portal selector;
- preserve the approved V2.11B four-card geometry;
- provide search, selected state, avatars, add/remove affordance and saving/error feedback;
- reuse the existing `toggleTaskAssignee()` / queued optimistic assignment flow without changing API, permission, or task assignment business logic.

Frozen and out of scope: Hero shell/identity/art/quote, Status/Priority custom dropdowns from B1, Due Date custom calendar from B2, Start Date advanced path, tabs, Description/Editor, Right Rail, Ramzy AI Assistant, TCS System Chat, APIs, DB, permissions, upload logic, TWS.

Ramzy = AI Assistant. TCS = System Chat.
