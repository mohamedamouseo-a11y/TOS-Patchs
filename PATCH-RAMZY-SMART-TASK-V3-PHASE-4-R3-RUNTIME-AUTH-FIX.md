# PATCH-RAMZY-SMART-TASK-V3-PHASE-4-R3-RUNTIME-AUTH-FIX

Baseline: 0cd3bdccddac531e2a1a34649349d67dbc76d1c7

Fix only:
- canActorAssignTargetUser must come from ../services/projectAccessScope.service.js, not agentAccess.service.js
- use existing top-level prisma; remove local prisma import
- do not catch/swallow errors from canActorAssignTargetUser; false => skip, thrown error => propagate
- remove users from smartTaskOptions state shape/fallbacks
- when no project selected, assignee placeholder = "Select a project first" / "اختر المشروع أولاً"
- keep smartTaskAssignees, loading/error, AUTO/NONE, project-member + SUPER_ADMIN dedupe

No RBAC policy/taskCommands/approval/Phase5+ changes.

Build/test/deploy/commit/push.
