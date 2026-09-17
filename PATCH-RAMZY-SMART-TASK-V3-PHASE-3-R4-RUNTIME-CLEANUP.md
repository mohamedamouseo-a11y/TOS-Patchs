# Phase 3 R4 — Runtime Cleanup

Baseline: `e76796e25d4af9e1f50c1e428eefcc2c40136969`

Fix only `frontend/src/components/RamzyAssistant.jsx`.

Current verified defects:
- `projectPickerShowArchived` state was removed but JSX still reads it.
- `setProjectPickerShowArchived(false)` still exists.
- archived toggle JSX / `isArchived` badge/class logic still exists.
- project endpoint failure is swallowed and shown as an empty project list instead of a project-specific error.

Required:
1. Remove every remaining `projectPickerShowArchived` / `setProjectPickerShowArchived` reference.
2. Remove archived toggle JSX and all `isArchived`, archived badge/class logic from Smart Task picker.
3. Keep exact-project selection only; no AUTO project.
4. If `api.agent.taskCreateProjects()` fails, preserve users independently but set a visible Smart Task project error; do not fall back to `/api/projects`.
5. Do not change RBAC, approval, assignee logic, backend, or Phase 4+.

Source/build only; no browser QA. Build, deploy, commit, push.
