# Smart Task V3 — Live QA R1: Project Picker UI / Overflow

Baseline main:
fe2bbebe81659fbc199d717718a8b95e8b8452fd

The attached live recording exposed a visual/runtime UX defect in the Smart Task project picker. The JSX already uses ramzy-project-picker* classes, but ramzySmartTaskComposerV1.css has no styles for those classes.

Fix only frontend Smart Task visual behavior.

## Required
Edit:
frontend/src/components/ramzySmartTaskComposerV1.css

1. Prevent horizontal overflow in the Smart Task card/body:
- min-width: 0 where needed
- overflow-x: hidden on card body
- long URLs/project names must never create a horizontal scrollbar

2. Style existing project picker classes:
- .ramzy-project-picker
- .ramzy-project-picker-input
- .ramzy-project-picker-list
- .ramzy-project-picker-item
- .ramzy-project-picker-item-name
- .ramzy-project-picker-item-client
- .ramzy-project-picker-empty

3. Project list behavior:
- bounded height around 180–220px
- internal vertical scroll
- no horizontal scroll
- overscroll containment
- each project is a distinct clickable row/card
- clear hover/focus/selected state
- long names/URLs wrap safely with overflow-wrap:anywhere / word-break as appropriate
- client name secondary/subtle
- light + dark mode
- preserve keyboard focus class is-focused and is-selected

4. Do not change project filtering, permission logic, selection behavior, task logic, backend, or API.

5. Preserve current Smart Task card max-height and footer visibility.

## Verify
- frontend build PASS
- backend test:ramzy PASS
- no horizontal scrollbar with very long project names/URLs
- project list has its own vertical scroll
- selecting an item still closes picker and loads assignees
- ONE NEW COMMIT
- COMMIT ONLY
- DO NOT PUSH

Return:
PATCH=SMART-TASK-V3-LIVE-QA-R1-PROJECT-PICKER-UI
PASS/FAIL=
NEW_COMMIT=
FILES_CHANGED=
PROJECT_PICKER_STYLED=
PROJECT_LIST_BOUNDED=
HORIZONTAL_OVERFLOW_FIXED=
LIGHT_DARK=
FRONTEND_BUILD=
BACKEND_TEST=
ERROR=
