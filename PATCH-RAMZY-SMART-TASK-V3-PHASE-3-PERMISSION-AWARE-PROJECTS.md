# PATCH-RAMZY-SMART-TASK-V3-PHASE-3-PERMISSION-AWARE-PROJECTS

## Baseline

TOS source baseline: `a707c2ea427bb1852bc267b0301ea4361e6e8b41`

## Scope

Phase 3 ONLY: make the Smart Task project picker server-authoritative for CREATE_TASK eligibility.

Do not start Phase 4+.

## Verified current state

- Smart Task currently loads projects with `api.projects.list({ summary: true })`.
- `/api/projects?summary=1` uses `buildProjectVisibilityWhere(...)`, so it answers project VISIBILITY, not whether Ramzy CREATE_TASK is authorized in that project.
- The authoritative task-create policy already exists in `assertAgentTaskCreateAccess(user, projectId, allowedWorkspaceIds, db)`.
- `assertAgentTaskCreateAccess` also honors the Ramzy allowed workspace scope and non-archived project requirement.
- Global Ramzy execution permission already exists in `assertRamzyActionExecutionAllowed` / `executionControl`.
- The current Smart Task loader fetches projects + users with one `Promise.all`, so a `/api/users` failure can blank the project picker. Phase 3 must isolate project loading from the existing assignee load without redesigning assignee permissions yet.

## Goal

The project picker must show ONLY projects for which the current actor can enter the existing Ramzy CREATE_TASK flow under CURRENT server-side rules.

No client-side role guessing.
No duplicated RBAC matrix.
No permission broadening.
No archived create targets.

## Backend

Add a dedicated authenticated Ramzy endpoint under the existing agent router, for example:

`GET /api/agent/task-create/projects`

Exact route name may follow current conventions, but keep it Ramzy/task-create specific.

### Endpoint authorization

Before returning candidates:

1. Load the existing agent settings.
2. Call `assertRamzyActionExecutionAllowed(req.user, { settings })`.
3. Do not create a new permission key.

### Candidate discovery

Start from ACTIVE/NON-ARCHIVED project visibility using the existing project visibility scope. Reuse `buildProjectVisibilityWhere(req.user, { archivedAt: null }, prisma)` or an equivalent existing server helper.

Do not query or return arbitrary global project names to unauthorized users.

### CREATE_TASK eligibility

For every candidate project, reuse the existing authoritative policy:

`assertAgentTaskCreateAccess(req.user, project.id, settings.allowedWorkspaceIds, prisma)`

Only projects that PASS this policy may be returned.

Expected denied project checks should be filtered out, not surfaced as a 500.
Unexpected database/system errors must still fail normally.

Do NOT copy the policy into the route with role if/else logic.

### Response

Return a minimal payload only, e.g.:

```json
{
  "projects": [
    {
      "id": "...",
      "name": "...",
      "clientName": "...",
      "status": "ACTIVE"
    }
  ]
}
```

`clientName` should use existing project client metadata when available (`project.clientName` and/or the existing client relation name).

Do not include sensitive project detail fields.

## Frontend API

Add one focused API helper under `api.agent`, e.g.:

`api.agent.taskCreateProjects()`

It must call the new server endpoint.

Do not use `/api/projects?summary=1` for the Smart Task project picker after this phase.

## Smart Task loader

Update `loadSmartTaskOptions()` so project candidates come from the new permission-aware endpoint.

Important: do NOT let the existing users-list request failure blank valid project candidates.

Project loading and assignee loading must be isolated.

Acceptable pattern:
- load project candidates authoritatively;
- load current assignee options separately/best-effort;
- if the current `/api/users` request fails, keep projects visible and leave the current AUTO/NONE assignee choices available;
- Phase 4 will replace the assignee source properly.

Do not broaden `/api/users` access in Phase 3.

## Picker UX

Keep the Phase 2 single-card architecture.

Project picker requirements:
- only server-returned CREATE_TASK-eligible projects;
- Arabic/English search by project name;
- search by client name if present;
- exact selected `project.id` retained in Smart Task state;
- selected project row continues showing project name + subtle client name when present;
- changing project preserves title, description, due, priority and assignee.

### Archived projects

Remove the Smart Task archived-project toggle from the CREATE_TASK picker.

Archived projects are not valid create targets under current `resolveAgentProjectAccess` / `assertAgentTaskCreateAccess` behavior.

Do not show archived projects as selectable.
Do not change global project screens or general project APIs.

### AUTO project option

Remove `AUTO` / "Let Ramzy suggest the best project" from the project picker in Phase 3.

Reason: Phase 3 is establishing an exact permission-aware project selection and current AUTO project submission does not carry an exact permission-approved project ID. AI project suggestion can be reintroduced later only if it is constrained to the server-approved candidate set.

This does NOT apply to assignee AUTO yet.

## Empty and error states

If the endpoint returns zero eligible projects:
- show a compact empty state such as `لا توجد مشاريع متاحة لإنشاء مهمة` / `No projects are available for task creation`;
- submit remains disabled because project is null.

If the permission-aware project request fails:
- show a project-specific load error;
- do not silently fall back to the general `/api/projects` list.

## Security invariants

Must remain unchanged:
- `ramzy.execute_actions`
- `assertRamzyActionExecutionAllowed`
- `assertAgentTaskCreateAccess`
- `resolveAgentProjectAccess`
- project/workspace/board RBAC semantics
- approval requirement
- action execution revalidation

The new endpoint is a picker/capability projection only. It must NOT become the final authorization boundary. Existing proposal/execution authorization remains authoritative.

## Explicitly out of scope

Do NOT implement:
- Phase 4 permission-aware assignee endpoint/filtering
- workload-based assignee suggestion
- Phase 5 AI description/smart suggestions
- Phase 6 advanced details
- Phase 7 structured CREATE_TASK submission
- visual/runtime QA (full QA is intentionally deferred until all phases are complete)

## Expected files

Likely:
- `backend/src/routes/agent.routes.js`
- `frontend/src/lib/api.js`
- `frontend/src/components/RamzyAssistant.jsx`
- optional Smart Task CSS only if needed for empty/error state

Do not modify unrelated files.

## Source/build verification

Verify from source/tests:

1. Smart Task no longer calls `api.projects.list({ summary: true })` for project choices.
2. New project endpoint calls existing server execution control.
3. Each returned project passes existing `assertAgentTaskCreateAccess` under current `allowedWorkspaceIds`.
4. Archived projects are not returned/selectable.
5. AUTO project option is removed.
6. Exact project ID survives selection.
7. User-list failure cannot erase already-valid project candidates.
8. Backend and frontend builds/tests pass.
9. Deploy, commit, push, clean worktree.

No authenticated browser QA in this phase.
