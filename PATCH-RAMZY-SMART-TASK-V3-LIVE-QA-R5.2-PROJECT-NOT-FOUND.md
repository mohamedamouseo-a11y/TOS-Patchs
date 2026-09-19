# Ramzy Smart Task V3 — Live QA R5.2: Project Picker "Project not found"

Baseline TOS:
`a3b571ba956e8b35c71a015baa16ba9efd45f679`

Live symptom:
Smart Task project section shows:
`Project not found`
and the picker cannot load.

Root cause in current `GET /api/agent/task-create/projects`:
R5 intentionally queries archived projects so the ARCHIVED filter can display them, but the loop calls `assertAgentTaskCreateAccess()` for every row.
That helper resolves projects with `archivedAt: null`, so an archived visible project throws 404 `Project not found`.
The route only skips 403, therefore one archived project aborts the whole project list.

Fix ONLY this defect.

Required behavior:
- Continue returning visible archived projects so the ARCHIVED filter works.
- Archived projects remain `selectable: false`.
- Do NOT call task-create authorization for an archived project as if it were creatable.
- For non-archived projects, keep existing `assertAgentTaskCreateAccess` exactly as the create permission gate.
- Preserve project visibility scope from `buildProjectVisibilityWhere`.
- Do not widen permissions.
- Do not change project lifecycle/status rules.
- No DB migration.

Preferred route logic:
1. Fetch permission-visible projects, including archived metadata.
2. If `proj.archivedAt != null`: include it as visible + disabled/non-selectable.
3. Else: require `assertAgentTaskCreateAccess`; skip only expected forbidden rows.
4. One archived project must never make the entire endpoint return `Project not found`.

Add a focused regression test that proves a mixed set of active + archived visible projects returns 200 and the archived item is disabled.

Verify:
- backend Ramzy tests PASS
- frontend build only if frontend changed
- authenticated live smoke: `GET /api/agent/task-create/projects` => 200
- picker loads and default ACTIVE filter renders
- restart backend if backend source changed
- commit + push TOS main

Return only:
```
PATCH=RAMZY-SMART-TASK-V3-LIVE-QA-R5.2
PASS/FAIL=
ROOT_CAUSE=
PROJECTS_API_LIVE=
ARCHIVED_VISIBLE_DISABLED=PASS/FAIL
ACTIVE_PICKER=PASS/FAIL
BACKEND_TEST=PASS/FAIL
FRONTEND_BUILD=PASS/FAIL/NOT_NEEDED
LIVE_DEPLOY=PASS/FAIL
COMMIT=
PUSH=YES/NO
ERROR=
```
