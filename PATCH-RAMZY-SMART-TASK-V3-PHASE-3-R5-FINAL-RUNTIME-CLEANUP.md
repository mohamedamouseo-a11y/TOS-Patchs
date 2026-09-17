# PATCH — RAMZY SMART TASK V3 — PHASE 3 R5 FINAL RUNTIME CLEANUP

Baseline: `02a67e272b5bfc4105b5f234c1e907ac6aab1603`

Fix only `frontend/src/components/RamzyAssistant.jsx`:

1. Remove the remaining JSX archived toggle that references undefined `projectPickerShowArchived` / `setProjectPickerShowArchived`.
2. Remove remaining `setProjectPickerShowArchived(false)` from `chooseSmartTaskProject()`.
3. No archived-project references may remain in Smart Task JS/JSX.
4. Keep exact-project selection only; no AUTO project.
5. Keep current permission-aware endpoint, assignee behavior, RBAC and approval logic unchanged.

Verify source grep has zero references to `projectPickerShowArchived` and `setProjectPickerShowArchived`.

Build, deploy, commit, push.