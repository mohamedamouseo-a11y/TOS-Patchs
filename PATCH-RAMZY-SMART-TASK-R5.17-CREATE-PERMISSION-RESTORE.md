# PATCH — RAMZY SMART TASK R5.17
# Restore Smart Task Create Permission For Internal Roles

Baseline TOS:
`62507dbb7270501d42ebdd071b5df01c76f3e7bc`

Scope: restore the missing role-level permission that currently prevents the Daily Smart Task bubble from becoming eligible for normal employees.

## Confirmed current-code root cause

The bubble requires:
`status.permissions.actions.CREATE_TASK === true`

That maps to:
`ramzy.tasks.create`

But current `backend/src/services/permissions.service.js` defaults only give `ramzy.tasks.create` to SUPER_ADMIN / ADMIN.

Current defaults for:
- MANAGER
- PROJECT_MANAGER
- TEAM_MEMBER

contain `ramzy.use` but NOT `ramzy.tasks.create`.

Therefore those users resolve to:
`NO_CREATE_PERMISSION`
and the Daily Smart Task bubble never shows.

Also, simply changing `DEFAULT_ROLE_PERMISSIONS` is not enough for production because `ensurePermissionCatalog()` uses rolePermission upsert with `update: {}`, so existing persisted false role-permission rows remain false.

## Required fix

### 1) Canonical role defaults
In `backend/src/services/permissions.service.js`, add:
`ramzy.tasks.create`

to:
- MANAGER
- PROJECT_MANAGER
- TEAM_MEMBER

Do not change unrelated permissions.

### 2) Safe production reconciliation
Create an idempotent one-time reconciliation script for the existing DB.

Target permission only:
`ramzy.tasks.create`

Target roles only:
- MANAGER
- PROJECT_MANAGER
- TEAM_MEMBER

For each role:
- ensure permission catalog row exists
- upsert the RolePermission row to `enabled=true`

Do NOT touch:
- SUPER_ADMIN
- ADMIN
- any other permission
- any UserPermissionOverride rows
- any explicit per-user DENY

Explicit active user DENY must continue to win through existing `hasPermission()` precedence.

The script must be safe to rerun.

### 3) Preserve security / native scope
This change only enables use of Ramzy Smart Task for those internal roles.

Do NOT bypass native TOS scope:
- project visibility remains enforced
- `assertAgentTaskCreateAccess` remains enforced
- workspace/project membership remains enforced
- archived/non-creatable projects remain non-creatable
- approval flow remains unchanged
- legacy explicit DENY remains respected

### 4) Verification
After DB reconciliation, verify effective `ramzy.tasks.create` for one active user from each available role:
- MANAGER
- PROJECT_MANAGER
- TEAM_MEMBER

For users with no explicit DENY, expect `true`.

Then verify the equivalent status values:
- `permissions.use=true`
- `permissions.actions.CREATE_TASK=true`
- `executionControl.globalExecutionAllowed=true` when system execution settings are enabled

Confirm R5.16 bubble eligibility reaches `ELIGIBLE` for a fresh eligible user.

Do not fake browser verification. If authenticated browser QA is unavailable, report it separately.

### 5) Build/deploy
- backend tests relevant to permissions/Ramzy
- frontend build only if frontend changed (frontend should not need changes)
- restart/deploy backend safely
- verify health/agent status path
- commit locally
- user handles push from TOS system

Return ONLY:
```
PATCH=RAMZY-SMART-TASK-R5.17-CREATE-PERMISSION-RESTORE
PASS/FAIL=
ROOT_CAUSE_CONFIRMED=
ROLE_DEFAULTS_FIXED=
DB_RECONCILIATION=
MANAGER_CREATE=
PROJECT_MANAGER_CREATE=
TEAM_MEMBER_CREATE=
EXPLICIT_DENY_PRESERVED=
PROJECT_SCOPE_PRESERVED=
RAMZY_STATUS_VERIFIED=
BUBBLE_ELIGIBILITY=
BACKEND_TEST=
DEPLOY=
COMMIT=
PUSH=USER_HANDLES
ERROR=
```
