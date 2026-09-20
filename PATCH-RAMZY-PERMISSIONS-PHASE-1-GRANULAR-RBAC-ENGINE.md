# RAMZY PERMISSIONS — PHASE 1/3
# Granular Server-Side Permission Engine (Safe Migration)

Baseline TOS:
`70572dd1def2d7a2c4124f25aa2a18053b1c64e9`

Goal:
Introduce a professional granular Ramzy permission engine without expanding anyone's current effective privileges by accident.

This phase is BACKEND / RBAC ENGINE ONLY.
Do NOT redesign the Permissions UI yet.
Do NOT change Smart Task UX/UI.
Do NOT change provider/model/memory/intent logic.

The existing security invariant must remain:

`Ramzy permission ∩ native TOS RBAC ∩ project/workspace scope = effective access`

Ramzy must NEVER become a bypass around TOS permissions.

---

## 0) Three-phase rollout

This patch is PHASE 1 only.

Phase 1 — Granular permission engine + safe defaults + execution re-check.
Phase 2 — Permissions Dashboard UI + role matrix controls + approval policy controls.
Phase 3 — Role-by-role QA, live migration validation, audit/rollout.

Do not implement Phase 2 or 3 in this patch.

---

# A) Add granular Ramzy permission keys

Extend `PERMISSION_DEFINITIONS` in:
`backend/src/services/permissions.service.js`

Add:

1. `ramzy.use`
   - label: استخدام رمزي
   - category: AI & Automation
   - meaning: user may open/chat with Ramzy and use non-mutating AI assistance.

2. `ramzy.tasks.create`
   - label: إنشاء المهام عبر رمزي
   - mutating permission for CREATE_TASK.

3. `ramzy.tasks.comment`
   - label: إضافة التعليقات عبر رمزي
   - maps to ADD_COMMENT.

4. `ramzy.tasks.checklist`
   - label: إدارة Checklist عبر رمزي
   - maps to ADD_CHECKLIST.

5. `ramzy.tasks.change_due`
   - label: تعديل مواعيد المهام عبر رمزي
   - maps to CHANGE_DUE_DATE.

6. `ramzy.tasks.assign`
   - label: تغيير منفذ المهمة عبر رمزي
   - maps to CHANGE_ASSIGNEE.

7. `ramzy.tasks.multi_step`
   - label: تنفيذ عمليات متعددة الخطوات عبر رمزي
   - maps to MULTI_STEP_TASK_OPERATION.

8. `ramzy.analytics.team`
   - label: تحليلات الفريق عبر رمزي
   - controls team-level operational/performance intelligence through Ramzy.

9. `ramzy.settings.manage`
   - label: إدارة إعدادات رمزي
   - intended for Ramzy settings administration.
   - SUPER_ADMIN only by default in Phase 1.

Keep existing:
`ramzy.execute_actions`

but mark it clearly in description/code comments as:
`LEGACY / compatibility permission`

Do NOT delete it in Phase 1 because live RolePermission/UserPermissionOverride records may exist.

No Prisma schema migration is needed because permissions are catalog rows.

---

# B) SAFE DEFAULTS — do not silently widen live privileges

Important migration rule:
Phase 1 must preserve current effective mutation access by default.

Use these Phase 1 defaults:

### SUPER_ADMIN
All Ramzy permissions = ON.

### ADMIN
- ramzy.use = ON
- ramzy.tasks.create = ON
- ramzy.tasks.comment = ON
- ramzy.tasks.checklist = ON
- ramzy.tasks.change_due = ON
- ramzy.tasks.assign = ON
- ramzy.tasks.multi_step = ON
- ramzy.analytics.team = ON
- ramzy.settings.manage = OFF
- existing ramzy.execute_actions stays ON

### MANAGER
- ramzy.use = ON
- ALL new mutating ramzy.tasks.* = OFF in Phase 1
- ramzy.analytics.team = OFF in Phase 1
- ramzy.settings.manage = OFF
- legacy ramzy.execute_actions stays OFF

### PROJECT_MANAGER
same safe defaults as MANAGER in Phase 1.

### TEAM_MEMBER
- ramzy.use = ON
- ALL new mutating ramzy.tasks.* = OFF in Phase 1
- ramzy.analytics.team = OFF
- ramzy.settings.manage = OFF
- legacy ramzy.execute_actions stays OFF

Reason:
Phase 2 will intentionally configure the richer role matrix.
Phase 1 must not grant new production mutation rights merely because new permission keys were deployed.

SUPER_ADMIN remains implicit allow as existing `hasPermission()` behavior.

---

# C) Split "Use Ramzy" from "Execute action"

Current `assertRamzyActionExecutionAllowed()` is used by several non-mutating endpoints such as Smart Task suggestion/context APIs.
That conflates using AI with executing mutations.

Create a clean distinction in:
`backend/src/agency-operator/services/ramzyExecutionControl.service.js`

## 1. Use control

Add:
`resolveRamzyUseControl(user, { settings })`
and
`assertRamzyUseAllowed(user, { settings })`

Use is allowed only when:
- Agent enabled
- role is in allowedRoles
- `hasPermission(user, "ramzy.use")` is true

Use control must NOT depend on:
- readOnlyMode
- approvalActionsEnabled
- any mutation permission

Meaning:
Emergency lock may stop mutations while Ramzy can still answer/read where existing read access permits.

## 2. Execution global control

Keep execution-wide conditions:
- agent enabled
- allowed role
- readOnlyMode must be false
- approvalActionsEnabled must be true

Do NOT use the legacy `ramzy.execute_actions` as the only mutation authorization anymore.

Instead execution of each action must pass its granular action permission.

Expose a helper:
`resolveRamzyActionPermission(user, actionType)`

and assertion:
`assertRamzyActionPermission(user, actionType)`

---

# D) Canonical action → permission map

Create one canonical mapping, exported and reused everywhere:

```js
CREATE_TASK                -> ramzy.tasks.create
ADD_COMMENT                -> ramzy.tasks.comment
ADD_CHECKLIST              -> ramzy.tasks.checklist
CHANGE_DUE_DATE            -> ramzy.tasks.change_due
CHANGE_ASSIGNEE            -> ramzy.tasks.assign
MULTI_STEP_TASK_OPERATION  -> ramzy.tasks.multi_step
```

Do not duplicate string mappings across routes/services.

Unknown mutating Ramzy action:
- fail closed
- 403 or controlled 400 according to existing conventions
- never default allow

For MULTI_STEP_TASK_OPERATION:
1. user must have `ramzy.tasks.multi_step`
2. EACH concrete step must ALSO pass its own granular permission
3. existing native TOS RBAC/scope must still pass for each target/action

Example:
Having multi_step does NOT let a user change assignee unless `ramzy.tasks.assign` is also allowed.

---

# E) Legacy ramzy.execute_actions compatibility

Do not delete or ignore existing legacy overrides blindly.

Implement a safe compatibility rule:

1. A current explicit/effective legacy ALLOW must NOT grant an action when its new granular permission is DENY.
2. A granular permission is the authoritative permission for its action once Phase 1 catalog exists.
3. Existing explicit user DENY on legacy `ramzy.execute_actions` must remain a GLOBAL mutation kill-switch for that user during Phase 1.
4. Existing system-wide readOnlyMode remains the strongest global mutation kill-switch.

If the current permissions service cannot distinguish an explicit user DENY from role/default result, add a focused helper such as:
`hasActiveUserPermissionDeny(userId, permissionKey)`
or equivalent.

Do not change generic `hasPermission()` semantics for unrelated permissions.

This allows safe migration without a privilege regression.

---

# F) Enforce BOTH Ramzy granular permission and native TOS RBAC

For every mutating action, authorization order should effectively be:

1. authenticated user
2. Ramzy enabled + allowed role
3. emergency/readOnly/approval global execution gates
4. granular Ramzy action permission
5. existing TOS project/workspace/task access
6. existing action-specific TOS RBAC
7. proposal/approval policy
8. RE-CHECK 3–6 immediately before execution

Do not rely on frontend hiding.
Do not rely only on proposal-time authorization.

---

# G) CREATE_TASK

At Smart Task proposal creation and final execution:

Require:
- `ramzy.tasks.create`
- existing `assertAgentTaskCreateAccess`
- existing workspace/project restrictions
- existing approval flow

Do not widen which projects appear.

Read-only Smart Task helper endpoints:
- projects list
- writing-context
- suggest-title
- suggest-description
- analyze-intent

should require `ramzy.use` plus their existing project visibility/access checks.
They must NOT require a mutation permission merely to generate/read suggestions.

Creating/proposing the task DOES require `ramzy.tasks.create`.

---

# H) ADD_COMMENT / ADD_CHECKLIST / CHANGE_DUE_DATE / CHANGE_ASSIGNEE

Before proposal creation and again before execution:

ADD_COMMENT:
- ramzy.tasks.comment
- existing `assertAgentTaskActionAccess(..., "ADD_COMMENT")`

ADD_CHECKLIST:
- ramzy.tasks.checklist
- existing native action access

CHANGE_DUE_DATE:
- ramzy.tasks.change_due
- existing manager/native action access

CHANGE_ASSIGNEE:
- ramzy.tasks.assign
- existing manager/native action access
- existing assignee target validation

No permission may widen project membership or target-user assignability.

---

# I) Analytics permission

Use `ramzy.analytics.team` only for TEAM-LEVEL intelligence exposed by Ramzy.

Do NOT gate:
- user's own task information
- user's own performance where native permission allows
- ordinary project/task information already visible to the user

Gate operations that aggregate or summarize OTHER users/team performance.

The helper must still apply native TOS:
- performance.view_team
- performance.view_all
- project scope
as applicable.

`ramzy.analytics.team` is an additional Ramzy gate, never a replacement for TOS reporting permissions.

If identifying all analytics tool entry points is too broad for this patch:
- implement the permission helper and enforce it at known Ramzy team-intelligence entry points
- add tests
- report any intentionally deferred entry point in ERROR instead of silently leaving it unguarded

---

# J) Ramzy settings permission

Introduce `ramzy.settings.manage`, but preserve current hard safety rules:

- SUPER_ADMIN may manage all Ramzy settings.
- ADMIN must NOT gain readOnlyMode/emergency-lock control.
- Integration/API-secret restrictions remain unchanged.
- In Phase 1, default ramzy.settings.manage is SUPER_ADMIN only.

Do not weaken existing `requireRole("SUPER_ADMIN", "ADMIN")` protections.
Use the new permission as an additional gate where appropriate, not as a bypass.

Phase 2 will expose this cleanly in UI.

---

# K) Status API

Enhance `GET /api/agent/status` without breaking current frontend consumers.

Keep existing fields.

Add a compact permission object, e.g.:

```json
{
  "permissions": {
    "use": true,
    "actions": {
      "CREATE_TASK": true,
      "ADD_COMMENT": true,
      "ADD_CHECKLIST": true,
      "CHANGE_DUE_DATE": true,
      "CHANGE_ASSIGNEE": true,
      "MULTI_STEP_TASK_OPERATION": true
    },
    "analyticsTeam": true,
    "settingsManage": false
  }
}
```

Do not expose sensitive implementation details.

Keep `executionControl`, but redefine/document:
- `canExecute` = global execution gates pass AND user has at least one granular action permission
- include `globalExecutionAllowed`
- include `allowedActionCount`

Frontend behavior must not break.

---

# L) Approval behavior in Phase 1

DO NOT introduce direct execution yet.

Preserve current approval behavior for all current mutating actions.

All existing actions that currently require approval still require approval.

Phase 2 will add approval-policy controls.

No schema migration for approval policies in Phase 1.

---

# M) Audit

When an action is denied due to a granular Ramzy permission:
- return controlled 403
- do not leak hidden entity details
- use existing audit infrastructure where denial auditing already exists
- add permission key/action type to safe audit metadata if appropriate

When execution succeeds, existing audit must remain unchanged.

Do not log secrets or full sensitive payloads.

---

# N) Files likely involved

Inspect and make the smallest cohesive change set:

- `backend/src/services/permissions.service.js`
- `backend/src/agency-operator/services/ramzyExecutionControl.service.js`
- `backend/src/agency-operator/policies/agentAccess.service.js` only if needed
- `backend/src/agency-operator/policies/agentPolicy.service.js` only if needed
- `backend/src/routes/agent.routes.js`
- action proposal/execution services that can bypass route checks
- multi-step execution service
- Ramzy tests

Do NOT modify Prisma schema in Phase 1 unless absolutely required.
Expected DB migration: NONE.

---

# O) Mandatory tests

Add real behavioral tests, not regex-only tests.

Must prove:

1. `ramzy.use` allows non-mutating Ramzy use while mutation permissions are off.
2. readOnlyMode blocks mutations but does not block allowed read-only Ramzy use.
3. ADMIN default can CREATE_TASK.
4. MANAGER default in Phase 1 cannot CREATE_TASK through Ramzy.
5. TEAM_MEMBER default in Phase 1 cannot mutate through Ramzy.
6. granular DENY blocks action even if native TOS role could perform it.
7. granular ALLOW never bypasses native TOS project/task RBAC.
8. CREATE_TASK permission checked proposal-time and execution-time.
9. CHANGE_ASSIGNEE permission checked proposal-time and execution-time.
10. CHANGE_DUE_DATE permission checked proposal-time and execution-time.
11. ADD_COMMENT permission checked.
12. ADD_CHECKLIST permission checked.
13. MULTI_STEP requires multi_step AND every step's granular permission.
14. explicit legacy ramzy.execute_actions user DENY blocks all mutation during migration.
15. unknown action fails closed.
16. SUPER_ADMIN remains allowed.
17. ramzy.analytics.team does not bypass performance/project scope.
18. settings manage does not give ADMIN emergency-lock authority.
19. existing 93+ Ramzy regression tests continue passing.

---

# P) Live verification

Before deploy:
- Prisma validate only if schema touched (should not be)
- backend tests
- frontend build only if frontend had to change (prefer no frontend change)

Authenticated server-side smoke using existing authorized accounts/test fixtures where available:

SUPER_ADMIN:
- use = allowed
- create = allowed

ADMIN:
- use = allowed
- create = allowed

MANAGER:
- use = allowed
- create via Ramzy = denied by Phase 1 safe default

TEAM_MEMBER:
- use = allowed
- mutation = denied by Phase 1 safe default

Verify:
- native project scope remains enforced
- emergency lock blocks all mutation
- approval flow unchanged

Reload backend.
No frontend atomic deploy needed unless frontend actually changed.

Commit + push TOS main.

---

# Q) Return contract

Return ONLY:

```
PATCH=RAMZY-PERMISSIONS-PHASE-1
PASS/FAIL=
GRANULAR_KEYS=PASS/FAIL
RAMZY_USE_SPLIT=PASS/FAIL
ACTION_PERMISSION_MAP=PASS/FAIL
SAFE_DEFAULTS=PASS/FAIL
LEGACY_DENY_COMPAT=PASS/FAIL
CREATE_TASK_GUARD=PASS/FAIL
COMMENT_GUARD=PASS/FAIL
CHECKLIST_GUARD=PASS/FAIL
CHANGE_DUE_GUARD=PASS/FAIL
ASSIGNEE_GUARD=PASS/FAIL
MULTI_STEP_GUARD=PASS/FAIL
ANALYTICS_GUARD=PASS/FAIL
SETTINGS_GUARD=PASS/FAIL
EXECUTION_RECHECK=PASS/FAIL
NATIVE_TOS_RBAC_PRESERVED=PASS/FAIL
APPROVAL_FLOW_UNCHANGED=PASS/FAIL
DB_MIGRATION=YES/NO
BACKEND_TEST=PASS/FAIL
FRONTEND_BUILD=PASS/FAIL/NOT_NEEDED
LIVE_SMOKE=PASS/FAIL
LIVE_DEPLOY=PASS/FAIL
COMMIT=
PUSH=YES/NO
ERROR=
```
