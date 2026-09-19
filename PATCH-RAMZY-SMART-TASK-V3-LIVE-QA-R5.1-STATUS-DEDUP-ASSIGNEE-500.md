# Ramzy Smart Task V3 — Live QA R5.1: Status UI Dedup + Assignee 500 Runtime Fix

Baseline TOS:
`e742c4209413787ee0eef29807ab7d1038a938cb`

R5 is NOT live-approved. Two live defects remain:

1) Project status UI is visually duplicated (e.g. Active / On Hold appears more than once because the new canonical filter is rendered together with legacy grouping/status presentation).
2) Smart Task Assignees still returns Internal Server Error on live.

Fix ONLY these two defects.

## A) Project status UI — one clean canonical filter

Keep canonical TOS lifecycle:
- All
- Active
- Planning
- On hold
- Delayed
- Completed
- Cancelled
- Archived

Default = Active.

Requirements:
- Exactly ONE filter chip per lifecycle option. No duplicates.
- Remove the legacy group headings:
  - Active projects
  - Other projects
  - Closed projects
  from the picker result list. They are redundant now that the canonical status filter exists.
- Preserve search + keyboard navigation.
- Preserve project status badge in ALL view.
- When a specific status filter is selected, do not repeat that same status text on every row; the active filter already communicates it.
- For ARCHIVED, show only one Archived indication per row/filter context.
- Do not invent Active/Not Active.
- Do not change project permissions or task-create rules.

## B) Assignees — fix the ACTUAL live 500

Do NOT assume the previous missing import was the only cause.

The user has already reproduced the live 500. Use the most recent backend/PM2 logs for:
`GET /api/agent/task-create/assignees?projectId=...`

Find the exact exception/stack from that existing failed request. Do not ask for another browser reproduction first.

Then apply the smallest root-cause fix.

Mandatory:
- endpoint must return HTTP 200 for a valid visible project
- preserve existing assignment scope/permissions
- ACTIVE users only
- no permission widening
- AUTO recommendation preserved
- no DB migration/data changes

Add/strengthen regression test so it executes the assignee handler/service path sufficiently to catch the runtime exception; a regex/import-presence assertion alone is NOT acceptable.

## Verify
- npm --prefix frontend run build
- npm --prefix backend run test:ramzy
- live API smoke for assignees using authorized existing session/token or safe server-side authenticated test
- deploy only after tests pass
- commit + push exact fix to TOS main

Return only:
```
PATCH=RAMZY-SMART-TASK-V3-LIVE-QA-R5.1
PASS/FAIL=
STATUS_UI_DEDUP=PASS/FAIL
ASSIGNEE_ROOT_CAUSE=<exact exception>
ASSIGNEE_API_LIVE=<status>
FRONTEND_BUILD=PASS/FAIL
BACKEND_TEST=PASS/FAIL
LIVE_DEPLOY=PASS/FAIL
COMMIT=
PUSH=YES/NO
ERROR=
```
