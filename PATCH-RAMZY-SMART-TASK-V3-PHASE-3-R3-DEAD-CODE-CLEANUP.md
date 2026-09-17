# PATCH RAMZY SMART TASK V3 — PHASE 3 R3 DEAD CODE CLEANUP

Baseline: ce52fd0

Fix ONLY `frontend/src/components/RamzyAssistant.jsx`:

- remove `projectPickerShowArchived` state and every `setProjectPickerShowArchived(...)` reference
- remove AUTO-project branch from `chooseSmartTaskProject`; it must accept only a real project object and retain exact project id
- do NOT remove assignee AUTO
- no RBAC/backend/approval/Phase4 changes

Build, deploy, commit, push.

Return:
PASS/FAIL
R3_NEW_COMMIT
ARCHIVED_PROJECT_CODE_PRESENT
AUTO_PROJECT_BRANCH_PRESENT
FRONTEND_BUILD
LIVE_DEPLOY
PUSH
ERROR
