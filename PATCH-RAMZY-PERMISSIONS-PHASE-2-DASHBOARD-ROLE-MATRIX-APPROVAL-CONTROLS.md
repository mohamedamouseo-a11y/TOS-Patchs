# RAMZY PERMISSIONS — PHASE 2/3
# Permissions Dashboard UX + Granular Role Matrix + Safe Approval Controls

Baseline TOS:
`1a9060bf203fbd1f43abe20f652a2d45b6229368`

Goal:
Make the Phase 1 granular Ramzy permissions professionally manageable from the existing TOS Permissions area, while preserving native TOS RBAC and safe approval behavior.

This is PHASE 2 only.
Phase 3 will be role-by-role QA/rollout.

Core invariant:
`Ramzy permission ∩ TOS RBAC ∩ project/workspace scope = effective access`

Never let Ramzy permissions bypass native TOS permissions.

---

# 0) IMPORTANT Phase 1 correction before UI

Phase 1 currently still makes `resolveRamzyExecutionControl()` depend on effective legacy `ramzy.execute_actions` ALLOW.

That would make the new granular UI misleading:
a Manager could be granted `ramzy.tasks.create` but remain blocked because legacy execute_actions is OFF by role default.

Fix this in Phase 2.

Required behavior:

- legacy `ramzy.execute_actions` is compatibility only.
- an ACTIVE EXPLICIT USER DENY on legacy remains a global per-user mutation kill switch.
- absence/default OFF of legacy must NOT block granular permissions.
- system `readOnlyMode` remains the strongest mutation kill switch.
- `approvalActionsEnabled=false` remains a global action-execution block.
- `canExecute` means:
  global execution gates pass
  AND no explicit legacy DENY
  AND user has at least one granular mutating permission.

Do NOT require legacy ALLOW.

Keep legacy permission hidden from the normal Phase 2 UI.

Add regression test proving:
MANAGER + granular `ramzy.tasks.create=ALLOW` + legacy role default OFF => Ramzy CREATE_TASK global execution gate can pass, subject to native TOS RBAC.

---

# A) Existing Permissions Dashboard — add dedicated Ramzy section

Use the EXISTING Permissions Dashboard and existing:
- GET /api/permissions/matrix
- PATCH /api/permissions/roles/:role/:permissionKey
- existing permission catalog / RolePermission

Do not build a second permissions system.

Add a dedicated section/tab/card:

`Ramzy / AI & Automation`

Professional TOS-native UI:
- cream/off-white/champagne/gold
- same typography/radius/spacing as current admin UI
- responsive table/card fallback
- dark mode
- no purple styling

SUPER_ADMIN only, consistent with current permissions routes.

---

# B) Granular Ramzy role matrix

Render these permissions in a focused matrix:

1. `ramzy.use`
   Label: Use Ramzy / استخدام رمزي

2. `ramzy.tasks.create`
   Create tasks / إنشاء المهام

3. `ramzy.tasks.comment`
   Add comments / إضافة التعليقات

4. `ramzy.tasks.checklist`
   Manage checklist / إدارة Checklist

5. `ramzy.tasks.change_due`
   Change due date / تعديل موعد المهمة

6. `ramzy.tasks.assign`
   Change assignee / تغيير المنفذ

7. `ramzy.tasks.multi_step`
   Multi-step actions / عمليات متعددة الخطوات

8. `ramzy.analytics.team`
   Team analytics / تحليلات الفريق

9. `ramzy.settings.manage`
   Manage Ramzy settings / إدارة إعدادات رمزي

Columns:
- SUPER_ADMIN
- ADMIN
- MANAGER
- PROJECT_MANAGER
- TEAM_MEMBER

Rules:
- SUPER_ADMIN: show locked ON, not editable.
- other roles: toggle through existing RolePermission endpoint.
- no optimistic fake success: rollback toggle on API failure and show error.
- refresh/reconcile matrix after mutation.
- legacy `ramzy.execute_actions` MUST NOT be shown as an ordinary role permission.

Add concise helper text:
`Ramzy permissions never give access beyond the user's normal TOS/project permissions.`

Arabic equivalent.

---

# C) Recommended visual grouping

Inside Ramzy permissions:

### Access
- Use Ramzy

### Task actions
- Create task
- Add comment
- Checklist
- Change due date
- Change assignee
- Multi-step

### Intelligence
- Team analytics

### Administration
- Manage Ramzy settings

Each row should show:
- human label
- short one-line description
- permission key optionally in subtle monospace/detail text
- role toggles

Avoid a giant generic permission wall.

---

# D) Dependency UX — prevent confusing configurations

UI warnings only; server remains authoritative.

Rules:

1. If a role has `ramzy.use = OFF` but any Ramzy action permission = ON:
   - allow saving the granular value
   - show warning: action will remain unavailable until Use Ramzy is enabled.
   - do NOT silently auto-enable permissions.

2. If `ramzy.tasks.multi_step = ON`:
   - explain that each step still needs its individual Ramzy permission + TOS RBAC.
   - do NOT auto-enable create/assign/due/etc.

3. `ramzy.analytics.team`:
   - explain it still requires native performance/project scope.

4. `ramzy.settings.manage`:
   - explain it does not override Super Admin-only security/integration restrictions.

No hidden permission mutations.

---

# E) Effective permission preview

Add a compact read-only explainer card below the matrix:

`Effective access = Ramzy permission + TOS permission + project/workspace access`

Show examples:
- Create task: Ramzy Create Task + native create-work access in that project
- Change assignee: Ramzy Change Assignee + native manager permission + valid target
- Team analytics: Ramzy Team Analytics + native performance scope

This is documentation UI only, not a separate engine.

---

# F) Approval controls — safe and simple

Do NOT make every action directly executable.

Keep safe policy:

- CREATE_TASK => approval required, locked
- CHANGE_ASSIGNEE => approval required, locked
- CHANGE_DUE_DATE => approval required, locked
- ADD_CHECKLIST => approval required, locked
- MULTI_STEP => approval required, locked
- ADD_COMMENT => low-risk; may optionally allow direct execution

Add ONE global setting for low-risk direct actions:

`lowRiskDirectActionsEnabled Boolean @default(false)`

in AgentSettings.

Migration required: YES, small additive migration only.

UI in Ramzy Permissions/Admin section:

`Allow direct execution for eligible low-risk actions`

Default OFF.

Helper:
Currently only Add Comment is eligible.
All native RBAC and granular permissions are still checked server-side.

SUPER_ADMIN only.

When OFF:
- ADD_COMMENT requires confirmation/approval as today safe default.

When ON:
- only actions already marked `directExecutionEligible=true` by `actionConfirmation.service.js` may execute directly.
- currently ADD_COMMENT only.
- NEVER make CREATE_TASK / ASSIGNEE / DUE / CHECKLIST / MULTI_STEP direct through this toggle.

Update `getActionConfirmationPolicy()`:
- directExecutionEnabled requires:
  - riskLevel LOW
  - directExecutionEligible
  - `settings.lowRiskDirectActionsEnabled === true`
  - readOnlyMode !== true
  - approvalActionsEnabled !== false

Do not depend on a deployment env flag as the user-facing control.
If retaining `RAMZY_LOW_RISK_DIRECT_ACTIONS` for backward compatibility:
- treat it only as fallback when DB settings are absent
- DB setting is authoritative once AgentSettings row exists.

Expose setting only in admin public settings.

Audit changes through existing settings/audit path if present.

---

# G) Global safety controls presentation

In the Ramzy section, clearly show current global controls without duplicating logic:

1. Ramzy enabled
2. Emergency lock / readOnlyMode
3. Action execution / approvalActionsEnabled
4. Low-risk direct actions

Important:
- Emergency lock must be visually prominent.
- only SUPER_ADMIN can change emergency lock.
- do not weaken existing route restrictions.
- API keys/provider controls remain in their existing settings area, not moved into permissions.

If the Permissions Dashboard does not currently own AgentSettings updates, add a small dedicated backend endpoint or reuse the existing protected AgentSettings endpoint; do not expose secrets.

---

# H) Frontend behavior must use ACTION permission, not generic canExecute

Audit Ramzy frontend gates.

Smart Task CREATE flow must be gated by:
`status.permissions.actions.CREATE_TASK === true`
plus existing use/global state,
NOT merely `executionControl.canExecute`.

Reason:
A user may have Comment permission but not Create permission.

Likewise:
- hide/disable mutation affordances according to their exact action permission where the frontend already exposes those actions.
- frontend is UX only; backend checks remain mandatory.

Do not hide Ramzy chat if `ramzy.use` is allowed merely because the user has zero mutation actions.

Expected states:
- use=true, no actions => chat/read-only assistant works.
- use=true, create=false => Smart Task creation intent should explain no permission instead of opening an unusable composer.
- use=false => Ramzy unavailable.

---

# I) Role matrix defaults after Phase 2

Do NOT silently overwrite current live RolePermission values during deployment.

The Phase 1 safe defaults remain only fallback/default catalog values.

Phase 2 UI allows Super Admin to intentionally configure the richer matrix.

No automatic mass-enable for Manager / Project Manager / Team Member.

Optional:
Add a non-destructive `Recommended matrix` preview, but DO NOT apply it automatically.

If adding an Apply Recommended Matrix button:
- require explicit confirmation
- show exact changed permissions
- SUPER_ADMIN only
- audit every role permission change
- otherwise omit this feature to keep scope small.

Preferred: omit for now.

---

# J) User-level temporary overrides

Existing UserPermissionOverride system should automatically support the new `ramzy.*` keys.

In the existing temporary permission UI:
- group/filter Ramzy permissions under AI & Automation
- human labels
- ALLOW/DENY behavior unchanged
- start/end/reason unchanged
- Super Admin only
- explicit legacy `ramzy.execute_actions DENY` remains visible if it already exists, labeled:
  `Legacy global Ramzy action block`
  and warning that it blocks all Ramzy mutations during compatibility period.

Do not let the UI create NEW legacy ALLOW overrides.
For new grants use granular permissions.

---

# K) Backend response/status cleanup

`GET /api/agent/status` should return coherent fields:

```
permissions.use
permissions.actions.CREATE_TASK
permissions.actions.ADD_COMMENT
permissions.actions.ADD_CHECKLIST
permissions.actions.CHANGE_DUE_DATE
permissions.actions.CHANGE_ASSIGNEE
permissions.actions.MULTI_STEP_TASK_OPERATION
permissions.analyticsTeam
permissions.settingsManage

executionControl.globalExecutionAllowed
executionControl.canExecute
executionControl.allowedActionCount
executionControl.emergencyLocked
executionControl.approvalActionsEnabled
```

Definitions:
- globalExecutionAllowed = agent/role/readOnly/approval global gates pass and no explicit legacy DENY.
- allowedActionCount = granular actions granted, before native per-target RBAC.
- canExecute = globalExecutionAllowed && allowedActionCount > 0.

Do NOT report legacy role-default OFF as PERMISSION_DENIED.

---

# L) Tests

Must add behavior tests for:

1. Matrix API returns all new ramzy permissions.
2. SUPER_ADMIN locked behavior remains server-side immutable via role update endpoint.
3. ADMIN granular toggle persists.
4. MANAGER granular create toggle persists.
5. Phase 1 legacy role default OFF no longer blocks granular permission.
6. explicit USER legacy DENY still blocks all mutation.
7. ramzy.use OFF + action ON => backend use denied.
8. Smart Task frontend checks CREATE_TASK specifically.
9. use=true + all actions=false => Ramzy chat remains usable.
10. multi-step UI copy does not imply bypass.
11. lowRiskDirectActionsEnabled default false.
12. direct low-risk OFF => ADD_COMMENT approval required.
13. direct low-risk ON => only eligible ADD_COMMENT can be direct.
14. CREATE_TASK stays approval-required even when low-risk toggle ON.
15. CHANGE_ASSIGNEE stays approval-required.
16. CHANGE_DUE_DATE stays approval-required.
17. ADD_CHECKLIST stays approval-required.
18. MULTI_STEP stays approval-required.
19. native TOS RBAC regression passes.
20. permission audit still recorded.

Run full Ramzy regression suite.

---

# M) Live QA

As SUPER_ADMIN:

Permissions Dashboard:
- open Ramzy section
- verify all granular rows
- toggle one MANAGER permission ON then OFF and confirm persistence
- verify SUPER_ADMIN cells locked
- verify legacy permission hidden from normal role matrix
- verify temporary override UI groups Ramzy permissions

Ramzy behavior:
- test a role with use ON + create OFF => chat works, Smart Task creation blocked
- test role after explicit create ON => Smart Task may open ONLY if native project create access also allows
- test emergency lock => all mutations blocked
- test explicit legacy user DENY => all mutations blocked
- verify normal TOS permissions unchanged

Approval:
- low-risk direct toggle default OFF
- if toggled ON, only ADD_COMMENT becomes eligible direct
- all other actions still approval required

Build/deploy:
- apply additive Prisma migration
- prisma validate
- backend tests
- frontend build
- restart backend
- atomic frontend deploy
- HTTPS 200
- commit + push

---

# N) Do NOT touch

- Smart Task visual redesign R5.10/R5.11 except permission-aware gating if required
- project picker logic
- assignee picker logic
- AI provider/model
- R5.6 input language
- writing memory
- intent analysis
- project/workspace native RBAC
- integration/API secret permissions
- TWS permissions
- unrelated role permissions

---

# O) Return contract

Return ONLY:

```
PATCH=RAMZY-PERMISSIONS-PHASE-2
PASS/FAIL=
PHASE1_LEGACY_GATE_FIX=PASS/FAIL
RAMZY_PERMISSION_UI=PASS/FAIL
ROLE_MATRIX=PASS/FAIL
SUPER_ADMIN_LOCKED=PASS/FAIL
GRANULAR_TOGGLES=PASS/FAIL
DEPENDENCY_WARNINGS=PASS/FAIL
TEMP_OVERRIDE_UI=PASS/FAIL
SMART_TASK_CREATE_GATE=PASS/FAIL
READ_ONLY_CHAT=PASS/FAIL
LOW_RISK_POLICY_SETTING=PASS/FAIL
COMMENT_DIRECT_POLICY=PASS/FAIL
HIGH_MEDIUM_APPROVAL_LOCKED=PASS/FAIL
EMERGENCY_LOCK_PRESERVED=PASS/FAIL
NATIVE_TOS_RBAC_PRESERVED=PASS/FAIL
PERMISSION_AUDIT=PASS/FAIL
DB_MIGRATION=PASS/FAIL
BACKEND_TEST=PASS/FAIL
FRONTEND_BUILD=PASS/FAIL
LIVE_VISUAL_SMOKE=PASS/FAIL
LIVE_ROLE_SMOKE=PASS/FAIL
LIVE_DEPLOY=PASS/FAIL
COMMIT=
PUSH=YES/NO
ERROR=
```
