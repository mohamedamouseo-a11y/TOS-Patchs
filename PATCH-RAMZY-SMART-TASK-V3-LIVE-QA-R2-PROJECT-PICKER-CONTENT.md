# Smart Task V3 — Live QA R2: Project Picker Content Hygiene

Baseline local commit:
21e095376a03c0f931647840f72cdf7af1a80c42

The live recording shows the real defect: the picker renders raw project name + clientName content in full. Some records contain very long text/URLs/credential-like content, so even with the R1 scroll CSS the list remains visually cluttered.

Fix ONLY Smart Task project-picker presentation.

## JSX / display rules
File:
frontend/src/components/RamzyAssistant.jsx

1. Add a small pure display helper for project labels:
- normalize whitespace to single spaces
- trim
- cap visible project name to 90 chars
- append ellipsis when capped
- never mutate the underlying project object/id
- do NOT use raw full value in title/tooltip/aria-label

2. Picker result rows:
- render ONLY the sanitized/capped project name as the primary visible label
- DO NOT render raw clientName in each picker row
- keep search/filter behavior unchanged (it may still search raw name/clientName)
- keep selection/permission logic unchanged

3. Selected project row:
- display the same sanitized/capped project name only
- DO NOT append raw clientName

## CSS
File:
frontend/src/components/ramzySmartTaskComposerV1.css

Keep R1 containment/scroll styles and additionally:
- each project row max 2 visible lines
- line-clamp/ellipsis
- row content must never expand vertically into a paragraph dump
- no horizontal overflow
- distinct spacing between rows
- light/dark preserved

## Tests
Add/update focused source test to assert:
- project picker does not render item.clientName
- selected row does not render smartTask.project.clientName
- display helper caps to 90 chars / normalizes whitespace
- filtering still references clientName so search behavior is preserved

Do NOT touch backend/API/database/project data.
Do NOT alter canonical names, IDs, permissions, or selection behavior.

Verify:
- frontend build PASS
- backend test:ramzy PASS
- ONE NEW COMMIT
- COMMIT ONLY
- DO NOT PUSH

Return:
PATCH=SMART-TASK-V3-LIVE-QA-R2-PROJECT-PICKER-CONTENT
PASS/FAIL=
BASELINE=
NEW_COMMIT=
FILES_CHANGED=
RAW_CLIENTNAME_HIDDEN=
PROJECT_LABEL_CAPPED=
PROJECT_ROWS_2_LINES_MAX=
FILTERING_UNCHANGED=
FRONTEND_BUILD=
BACKEND_TEST=
ERROR=
