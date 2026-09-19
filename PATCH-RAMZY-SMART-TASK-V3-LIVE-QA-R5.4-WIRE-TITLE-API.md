# Ramzy Smart Task V3 — Live QA R5.4: Wire Missing Title API Client

Baseline TOS:
`48fa99202a2c753f445115650636815910342293`

Live error:
`h.agent.suggestTaskTitle is not a function`

Confirmed source cause:
`frontend/src/components/RamzyAssistant.jsx` calls:
`api.agent.suggestTaskTitle(...)`

but `frontend/src/lib/api.js` does NOT define `suggestTaskTitle`.

The backend route already exists:
`POST /api/agent/task-create/suggest-title`

Fix ONLY this wiring defect.

Required change in `frontend/src/lib/api.js` inside `api.agent`:
```js
suggestTaskTitle: (params) => request("/api/agent/task-create/suggest-title", {
  method: "POST",
  body: JSON.stringify(params),
}),
```

Keep existing:
`suggestTaskDescription`
unchanged.

Do NOT touch:
- backend route/service
- project picker
- assignees
- approval flow
- AI provider/model configuration
- feature tip
- unrelated API methods

Verify:
- frontend build PASS
- focused Ramzy tests PASS
- live click on Write/Improve title reaches the endpoint (no "is not a function")
- deploy via existing atomic frontend process
- commit + push TOS main

Return only:
```
PATCH=RAMZY-SMART-TASK-V3-LIVE-QA-R5.4
PASS/FAIL=
ROOT_CAUSE=
API_CLIENT_WIRED=PASS/FAIL
FRONTEND_BUILD=PASS/FAIL
BACKEND_TEST=PASS/FAIL
LIVE_TITLE_CLICK=PASS/FAIL
LIVE_DEPLOY=PASS/FAIL
COMMIT=
PUSH=YES/NO
ERROR=
```
