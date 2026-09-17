# PATCH-RAMZY-SMART-TASK-V3-PHASE-3-R2-CLEANUP

Baseline: ff8dbb7e3865693da78064bdfc9d043fa998ae42

Fix Phase 3 only:

1. backend/src/routes/agent.routes.js
- Expected authorization denial check must use `err?.status === 403`, not `err.code`.
- Keep current settings + `settings.allowedWorkspaceIds` behavior.
- Prefer existing static imports; no RBAC logic duplication.

2. frontend/src/components/RamzyAssistant.jsx
Remove remaining archived-project and AUTO-project code from Smart Task:
- `projectPickerShowArchived` state/usages
- archived filtering/badges/toggle
- `setProjectPickerShowArchived`
- `item === "AUTO"` branch in `chooseSmartTaskProject`
- AUTO project button

Project picker must contain only exact projects returned by `api.agent.taskCreateProjects()` and preserve exact `projectId`.

Do not change assignee logic, RBAC, approval flow, Phase 4+.

Build, deploy, commit, push.
