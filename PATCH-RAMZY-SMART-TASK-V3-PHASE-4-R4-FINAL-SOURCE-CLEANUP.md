# PATCH-RAMZY-SMART-TASK-V3-PHASE-4-R4-FINAL-SOURCE-CLEANUP

Baseline: a3532cb126cc725c007f965295688ffd5312164c

Fix only:
- remove users:[] from loadSmartTaskOptions fallback
- when no project selected, assignee placeholder must be "Select a project first" / "اختر المشروع أولاً"
- assignee endpoint must not convert task-create 403 into HTTP 200; let assertAgentTaskCreateAccess error propagate
- reuse existing top-level assertAgentTaskCreateAccess import; no redundant dynamic import
- keep correct canActorAssignTargetUser from projectAccessScope.service.js
- preserve current project-member + SUPER_ADMIN dedupe, loading/error, AUTO/NONE, approval/RBAC behavior

No Phase5+ changes.

Build/test/deploy/commit/push.
