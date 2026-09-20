# RAMZY PERMISSIONS — PHASE 3/3
# Final Role Matrix Rollout + End-to-End Authorization QA + Cleanup

Baseline TOS:
`d1f675cb95918d8694646bff85936ef42057e482`

Goal:
Finish the Ramzy permissions project with a deliberate production role matrix, end-to-end authorization QA for every internal role, and small cleanup/hardening only where QA proves necessary.

This is the FINAL phase.
Do not add new Ramzy features.
Do not redesign Smart Task.
Do not change AI/provider/model/memory/intent.

Security invariant remains:

`Ramzy permission ∩ native TOS RBAC ∩ project/workspace scope = effective access`

Ramzy must never expand native TOS access.

---

# A) Apply the recommended production Ramzy role matrix

Use the existing RolePermission system / permission management service.
Do NOT hardcode bypasses in routes.

Target live matrix:

| Permission | SUPER_ADMIN | ADMIN | MANAGER | PROJECT_MANAGER | TEAM_MEMBER |
|---|---|---|---|---|---|
| ramzy.use | ON | ON | ON | ON | ON |
| ramzy.tasks.create | ON | ON | ON | ON | ON |
| ramzy.tasks.comment | ON | ON | ON | ON | ON |
| ramzy.tasks.checklist | ON | ON | ON | ON | ON |
| ramzy.tasks.change_due | ON | ON | ON | ON | OFF |
| ramzy.tasks.assign | ON | ON | ON | ON | OFF |
| ramzy.tasks.multi_step | ON | ON | ON | ON | OFF |
| ramzy.analytics.team | ON | ON | ON | ON | OFF |
| ramzy.settings.manage | ON | OFF | OFF | OFF | OFF |

Important:
- SUPER_ADMIN remains implicit/locked ON.
- TEAM_MEMBER create/comment/checklist are still limited by native project/task RBAC.
- TEAM_MEMBER checklist must remain restricted by current assigned/native task rules.
- MANAGER / PROJECT_MANAGER change_due and assign only work where native TOS role/scope allows them.
- multi_step still requires permission for every included concrete action.
- analytics still requires native performance/project scope.
- settings management remains SUPER_ADMIN only in final production matrix.

Do not change unrelated permissions.

---

# B) Legacy compatibility permission

`ramzy.execute_actions` remains compatibility-only.

Final behavior:
- role default ALLOW/OFF must NOT be required for granular actions.
- explicit ACTIVE USER DENY continues to block all Ramzy mutation.
- do not create any new legacy ALLOW overrides.
- keep the legacy permission hidden from normal Ramzy role matrix.
- if shown in temporary overrides because an old record exists, label it clearly as legacy global block.

Do not delete historical RolePermission/UserPermissionOverride rows in this phase.

---

# C) Approval policy final production state

Keep:
- `lowRiskDirectActionsEnabled = false` in production after QA.
- CREATE_TASK = approval required
- CHANGE_ASSIGNEE = approval required
- CHANGE_DUE_DATE = approval required
- ADD_CHECKLIST = approval required
- MULTI_STEP = approval required
- ADD_COMMENT = approval required while lowRiskDirectActionsEnabled=false

During QA you MAY temporarily enable low-risk direct actions only long enough to verify that:
- ADD_COMMENT can become direct
- nothing else becomes direct

Then set it back to FALSE before completion.

Confirm final live value:
`lowRiskDirectActionsEnabled=false`

Emergency lock final state:
- preserve the user's existing production value.
- do NOT toggle it permanently just for QA.
- if testing requires a temporary toggle, restore the exact original value.

---

# D) Permissions UI cleanup

Inspect the live Permissions Dashboard.

Required final UX:

1. Dedicated `Ramzy / AI & Automation` section appears once.
2. Granular `ramzy.*` rows must NOT be duplicated again in the generic permission matrix below.
   - generic matrix should exclude:
     - ramzy.use
     - ramzy.tasks.*
     - ramzy.analytics.team
     - ramzy.settings.manage
     - ramzy.execute_actions
3. Legacy `ramzy.execute_actions` hidden from normal role matrix.
4. SUPER_ADMIN Ramzy cells visibly locked ON.
5. Role toggles reflect actual persisted RolePermission values after reload.
6. Dependency warnings remain visible where relevant.
7. Temporary override UI can select granular Ramzy permissions.
8. New override UI must NOT offer legacy `ramzy.execute_actions` as a grant.
9. Existing legacy DENY records, if present, remain visible/readable for cleanup awareness.
10. No duplicate or contradictory settings controls.

If duplication exists, fix only the filtering/presentation.
Do not redesign the whole Permissions page.

---

# E) Exact action authorization QA by role

Use real/test users for:
- SUPER_ADMIN
- ADMIN
- MANAGER
- PROJECT_MANAGER
- TEAM_MEMBER

Choose controlled test projects/tasks where scope is known.

For EACH role verify both:
1. Ramzy granular permission
2. native TOS scope

## SUPER_ADMIN
Expected:
- Ramzy use YES
- all task actions YES
- team analytics YES
- settings manage YES

## ADMIN
Expected:
- use YES
- create/comment/checklist/due/assign/multi-step YES
- analytics YES
- settings manage NO
- emergency lock modification still NO unless route is SUPER_ADMIN

## MANAGER
Expected granular:
- use YES
- create/comment/checklist/due/assign/multi-step YES
- analytics YES
- settings NO

Must prove:
- allowed action inside a project where native TOS scope permits it succeeds/proposes
- same action outside native project scope is denied

## PROJECT_MANAGER
Same granular action profile as MANAGER.

Must prove:
- only project/workspace scope available to that user is accessible
- no company-wide bypass

## TEAM_MEMBER
Expected:
- use YES
- create YES where native create-work permits
- comment YES where native task access permits
- checklist YES only where existing native assigned/task rule permits
- change_due NO
- assign NO
- multi_step NO
- analytics.team NO
- settings NO

Must prove a TEAM_MEMBER cannot elevate through prompt wording or multi-step.

---

# F) Project / workspace scope QA

Test at least:

1. User is project member:
   allowed read/use according to normal scope.

2. User is not project member and has no system-admin bypass:
   project/task must remain invisible/403.

3. Workspace-limited Ramzy setting:
   if `allowedWorkspaceIds` is configured, action outside allowed workspace must fail.

4. Archived project:
   visible only where current UI intentionally shows archived option;
   cannot create task.

5. Assignee:
   user cannot assign a target that `canActorAssignTargetUser` rejects.

No Ramzy permission may change these results.

---

# G) Proposal-time AND execution-time recheck

For these actions verify permission is checked:
- CREATE_TASK
- CHANGE_ASSIGNEE
- CHANGE_DUE_DATE
- ADD_CHECKLIST
- ADD_COMMENT
- MULTI_STEP

Test revocation scenario:

1. create a pending approval while permission is allowed
2. revoke the granular permission
3. attempt approval/execution
4. execution MUST fail server-side
5. restore intended matrix

Also test:
1. pending approval created while project scope allowed
2. remove relevant project/task access or use a controlled equivalent
3. execution recheck must fail

Do not leave test permissions/access modified after QA.

---

# H) Multi-step escalation tests

Must prove all of these fail:

1. TEAM_MEMBER attempts multi-step directly.
2. User has `ramzy.tasks.multi_step` but lacks `ramzy.tasks.assign`, operation contains CHANGE_ASSIGNEE.
3. User has multi_step + assign but native TOS scope rejects target task/project.
4. Unknown/unmapped action inside multi-step.

Must prove valid Manager/Project Manager multi-step succeeds/proposes only when every step passes:
- granular permission
- native TOS RBAC
- scope
- approval policy

---

# I) Read-only assistant behavior

Verify:

- `ramzy.use=ON`, all action permissions OFF:
  Ramzy chat still opens and answers permitted read-only questions.

- CREATE_TASK OFF:
  create-task intent must NOT open Smart Task.
  show existing controlled permission feedback.

- readOnlyMode/emergency lock ON:
  chat/read-only use remains available when `ramzy.use` is allowed.
  all mutations blocked.

Restore emergency lock to original state after QA.

---

# J) Analytics security QA

For `ramzy.analytics.team`:

MANAGER / PROJECT_MANAGER:
- may get team analytics only within native performance/project scope.
- cannot see unrelated teams/projects.

TEAM_MEMBER:
- denied team analytics.
- own information remains available only according to existing native self permissions.

ADMIN / SUPER_ADMIN:
- preserve native distinction:
  `performance.view_all` still determines company-wide performance access.
- Ramzy analytics permission must not substitute for `performance.view_all`.

No prompt may bypass this.

---

# K) Settings management QA

Verify:
- SUPER_ADMIN can access Ramzy settings.
- ADMIN cannot access because final matrix has `ramzy.settings.manage=OFF`.
- MANAGER / PROJECT_MANAGER / TEAM_MEMBER cannot.
- API keys/integration restrictions unchanged.
- emergency lock remains SUPER_ADMIN-controlled.

Do not broaden provider/API-secret access.

---

# L) Temporary override QA

Using a controlled non-SUPER_ADMIN test user:

1. Add temporary DENY for one granular Ramzy permission with start/end/reason.
2. effective access becomes denied.
3. remove/expire it, role permission becomes effective again.

Then:
1. Add temporary ALLOW for a granular permission that role normally lacks.
2. Ramzy granular gate becomes allowed.
3. native TOS RBAC must STILL block access outside normal scope.

Also:
- explicit legacy `ramzy.execute_actions DENY` must block ALL mutation.
- remove any QA-created legacy deny afterward.
- do not create legacy ALLOW.

Audit events must exist for changes.

---

# M) Security / regression

Run:
- backend Ramzy tests
- permission/RBAC tests
- frontend build
- Prisma validate
- migration status

No new migration expected in Phase 3.

Add focused regression tests if any final bug is fixed.

Do not mark PASS from static grep only.
Use behavioral/API tests for permission boundaries.

---

# N) Live final matrix verification

After applying the recommended matrix, fetch/read the live permission matrix and verify persisted values exactly.

Return a compact machine-readable snapshot in logs during execution, but final PATCH CONTRACT only.

Final live state must have:
- recommended matrix from Section A
- lowRiskDirectActionsEnabled=false
- no QA temporary overrides left behind
- no QA data pollution
- original emergency lock state restored
- HTTPS 200
- frontend/backend healthy

---

# O) Deployment

If code cleanup/fixes were required:
- backend build/test
- frontend build
- apply only needed deploy
- atomic frontend deploy if frontend changed
- backend restart if backend changed

If only role data changed:
- do not rebuild unnecessarily

Commit + push any code changes.

If no code changes are needed:
- do not create an empty commit
- return `COMMIT=NO_CODE_CHANGE`
- `PUSH=NO_CODE_CHANGE`

---

# P) Return contract

Return ONLY:

```
PATCH=RAMZY-PERMISSIONS-PHASE-3
PASS/FAIL=
RECOMMENDED_MATRIX_APPLIED=PASS/FAIL
SUPER_ADMIN=PASS/FAIL
ADMIN=PASS/FAIL
MANAGER=PASS/FAIL
PROJECT_MANAGER=PASS/FAIL
TEAM_MEMBER=PASS/FAIL
PROJECT_SCOPE=PASS/FAIL
WORKSPACE_SCOPE=PASS/FAIL
ASSIGNEE_SCOPE=PASS/FAIL
PROPOSAL_RECHECK=PASS/FAIL
EXECUTION_RECHECK=PASS/FAIL
MULTI_STEP_NO_ESCALATION=PASS/FAIL
READ_ONLY_CHAT=PASS/FAIL
ANALYTICS_SCOPE=PASS/FAIL
SETTINGS_SCOPE=PASS/FAIL
TEMP_OVERRIDE_ALLOW=PASS/FAIL
TEMP_OVERRIDE_DENY=PASS/FAIL
LEGACY_DENY_KILLSWITCH=PASS/FAIL
APPROVAL_POLICY=PASS/FAIL
LOW_RISK_FINAL_OFF=PASS/FAIL
PERMISSIONS_UI_NO_DUPLICATES=PASS/FAIL
AUDIT=PASS/FAIL
QA_CLEANUP=PASS/FAIL
DB_MIGRATION=NO/YES
BACKEND_TEST=PASS/FAIL
FRONTEND_BUILD=PASS/FAIL/NOT_NEEDED
LIVE_MATRIX_VERIFY=PASS/FAIL
LIVE_SMOKE=PASS/FAIL
LIVE_DEPLOY=PASS/FAIL/NOT_NEEDED
COMMIT=
PUSH=YES/NO/NO_CODE_CHANGE
ERROR=
```
