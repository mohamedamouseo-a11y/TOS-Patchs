# PATCH-RAMZY-SMART-TASK-V3-PHASE-3-R1-ACTUAL-INTEGRATION-FIX

Baseline: `5318572d5d83f6855dcb89498770a2242f30eb24`

## Scope
Correction only. Do not start Phase 4.

## Verified defects in current source

### Backend endpoint defects
`backend/src/routes/agent.routes.js` currently adds `/task-create/projects`, but:

1. It dynamically imports `assertRamzyActionExecutionAllowed` as a **default export** even though the service exports it as a **named export**. The route can fail at runtime.
2. It dynamically re-imports `assertAgentTaskCreateAccess` even though that function is already statically imported in this file.
3. It calls `assertRamzyActionExecutionAllowed(req.user, { settings: null })` instead of resolving settings once and reusing them.
4. It calls `assertAgentTaskCreateAccess(req.user, proj.id, [], prisma)`, so `settings.allowedWorkspaceIds` is NOT respected.
5. It catches `err?.code === 403`, but `AppError` uses `err.status`, not `err.code`. Expected authorization failures therefore are not filtered correctly.

### Frontend integration defects
At this baseline, `frontend/src/components/RamzyAssistant.jsx` still:

- uses `api.projects.list({ summary: true })` for Smart Task project choices;
- uses `Promise.all([projects, users])`, so user-list failure can still wipe project choices;
- retains archived-project filtering/toggle state;
- retains AUTO project selection.

`frontend/src/lib/api.js` has `api.agent.taskCreateProjects()`, but RamzyAssistant is not actually using it.

## Required backend correction

Use existing static imports where already available.

Add only the missing static import:

```js
import { buildProjectVisibilityWhere } from "../services/projectAccessScope.service.js";
```

Inside `GET /api/agent/task-create/projects`:

```js
const settings = await getAgentSettings();
await assertRamzyActionExecutionAllowed(req.user, { settings });

const where = await buildProjectVisibilityWhere(
  req.user,
  { archivedAt: null },
  prisma,
);

const projects = await prisma.project.findMany({
  where,
  select: {
    id: true,
    name: true,
    clientName: true,
    status: true,
  },
  orderBy: { name: "asc" },
});

const allowed = [];
for (const project of projects) {
  try {
    await assertAgentTaskCreateAccess(
      req.user,
      project.id,
      settings.allowedWorkspaceIds,
      prisma,
    );
    allowed.push({
      id: project.id,
      name: project.name,
      clientName: project.clientName || null,
      status: project.status,
    });
  } catch (error) {
    if (error?.status === 403) continue;
    throw error;
  }
}

res.json({ projects: allowed });
```

Do not add new role logic. Do not weaken existing authorization.

## Required frontend correction

### `loadSmartTaskOptions()`
Stop using `api.projects.list({ summary: true })` for Smart Task project choices.

Load projects from:

```js
api.agent.taskCreateProjects()
```

Project loading and user loading MUST be independent.

Recommended behavior:

```js
async function loadSmartTaskOptions() {
  setSmartTaskOptions((current) => ({ ...current, loading: true, error: "" }));

  const projectPromise = api.agent.taskCreateProjects();
  const userPromise = api.users.list({ summary: true });

  const [projectResult, userResult] = await Promise.allSettled([
    projectPromise,
    userPromise,
  ]);

  if (projectResult.status === "rejected") {
    setSmartTaskOptions({
      projects: [],
      users: userResult.status === "fulfilled"
        ? parsedUsers
        : [],
      loading: false,
      error: project-specific localized error,
    });
    return;
  }

  const projects = smartTaskCollection(projectResult.value, ["projects", "items"])
    .filter(valid id/name);

  const users = userResult.status === "fulfilled"
    ? smartTaskCollection(userResult.value, ["users", "items"]).filter(valid id/name)
    : [];

  sort projects/users as before;
  setSmartTaskOptions({ projects, users, loading: false, error: "" });
}
```

Equivalent implementation is acceptable.

Important:
- If users fail, keep projects.
- AUTO/NONE assignee must remain usable.
- Do not broaden `/api/users` authorization.

### Project picker cleanup
Remove Smart Task archived UI/state/logic:
- remove archived toggle from picker;
- remove `projectPickerShowArchived` if only used by Smart Task;
- no archived filtering branch is needed because server endpoint already returns only non-archived eligible projects.

Remove project AUTO option entirely:
- no `item === "AUTO"` branch in project selection;
- no “Let Ramzy suggest project” button;
- Smart Task must retain an exact approved project ID.

`chooseSmartTaskProject(item)` should keep:
- `id`
- `name`
- `clientName`
- `auto: false` may remain if harmless, but there must be no AUTO project path.

Keep Phase 2 draft preservation when changing project.

### Empty/error state
Zero eligible projects:
- AR: `لا توجد مشاريع متاحة لإنشاء مهمة`
- EN: `No projects are available for task creation`

Endpoint failure:
- show a project-specific error;
- do not fall back to `/api/projects`.

## Do not change
- Phase 1 intent parser
- `ramzy.execute_actions`
- `assertRamzyActionExecutionAllowed`
- `assertAgentTaskCreateAccess`
- project/workspace/board RBAC logic
- approval logic
- assignee authorization/data source (Phase 4)
- backend task creation logic
- Phase 4+

## Verification
Source/build only. No browser QA now.

Verify:
1. Route has no dynamic default import for `assertRamzyActionExecutionAllowed`.
2. Route resolves settings once.
3. Route passes `settings.allowedWorkspaceIds` to `assertAgentTaskCreateAccess`.
4. Expected auth denial checks `error.status === 403`.
5. RamzyAssistant project loader uses `api.agent.taskCreateProjects()`.
6. RamzyAssistant no longer uses `api.projects.list()` for Smart Task projects.
7. User-list failure cannot erase valid projects.
8. Archived project toggle absent from Smart Task.
9. AUTO project option absent.
10. Exact project ID preserved.
11. Frontend build passes.
12. Backend tests/build passes.
13. Atomic deploy.
14. New commit after `5318572`.
15. Push main.
16. Worktree clean.

## Return exactly

```text
PATCH=RAMZY-SMART-TASK-V3-PHASE-3-R1-ACTUAL-INTEGRATION-FIX
PASS/FAIL=<result>
BASELINE_COMMIT=5318572
R1_NEW_COMMIT=<sha>
DYNAMIC_DEFAULT_IMPORT_REMOVED=YES/NO
SETTINGS_RESOLVED_ONCE=YES/NO
ALLOWED_WORKSPACE_IDS_PASSED=YES/NO
AUTH_FAILURE_CHECKS_ERROR_STATUS=YES/NO
SMART_TASK_USES_DEDICATED_PROJECT_ENDPOINT=YES/NO
GENERAL_PROJECT_LIST_USED_FOR_SMART_TASK=YES/NO
USER_LIST_FAILURE_BREAKS_PROJECTS=YES/NO
ARCHIVED_PROJECT_TOGGLE_PRESENT=YES/NO
AUTO_PROJECT_OPTION_PRESENT=YES/NO
EXACT_PROJECT_ID_RETAINED=YES/NO
PROJECT_RBAC_CHANGED=NO
WORKSPACE_RBAC_CHANGED=NO
BOARD_RBAC_CHANGED=NO
APPROVAL_LOGIC_CHANGED=NO
ASSIGNEE_LOGIC_CHANGED=NO
FRONTEND_BUILD=PASS/FAIL
BACKEND_TESTS=PASS/FAIL
LIVE_DEPLOY=PASS/FAIL
PUSH=YES/NO
WORKTREE_CLEAN=YES/NO
FILES_CHANGED=<paths>
ERROR=<NONE or exact error>
```
