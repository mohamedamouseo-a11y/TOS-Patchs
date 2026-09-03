# TOS — Admin Performance Visibility Permissions V1

## Goal

Remove the implicit `ADMIN => company-wide Team Performance` behavior from Team Performance visibility without changing the global `isSystemAdmin()` semantics used by other TOS domains.

This patch is intentionally applied on top of the current uncommitted Phase 6 Ramzy Team Performance work.

## New dynamic permission keys

- `performance.view_self`
- `performance.view_team`
- `performance.view_all`

These use the existing `Permission`, `RolePermission`, and `UserPermissionOverride` tables. No Prisma schema change or migration is required.

## Default role behavior

- `SUPER_ADMIN`: full access, including `performance.view_all`.
- `ADMIN`: `view_self` + `view_team`; `view_all` is **disabled by default**.
- `MANAGER`: `view_self` + `view_team`.
- `PROJECT_MANAGER`: `view_self` + `view_team`.
- `TEAM_MEMBER`: `view_self` only.

`performance.view_team` follows the existing project-membership team scope. `performance.view_all` gives company-wide performance visibility.

The Super Admin can toggle `performance.view_all` for the `ADMIN` role from the existing Permissions Matrix. That role setting applies to current and future Admin users. Individual permanent Admin presets are not introduced in this V1; existing temporary user overrides remain separate.

## Backend scope changes

The same permission-driven read scope is reused by:

- Team Performance main report
- Team Performance export dataset
- Ramzy Phase 6 Team Performance tool (indirectly through the reused dataset)
- Targets visibility
- Performance Review visibility
- Workforce visibility
- Skills/Talent/Recognition paths that already reuse Workforce scope
- Talent succession role visibility guard

Target write authorization keeps the existing Admin/Manager management roles, but an Admin without `performance.view_all` cannot manage an employee target outside the Admin's visible Team Performance scope.

## Explicit non-goals

- Do **not** change the global meaning of `isSystemAdmin()`.
- Do **not** change project-domain Admin authority.
- Do **not** change user-management Admin authority.
- Do **not** create schema changes or migrations.
- Do **not** commit or push TOS.
- Do **not** replace the existing permissions system.

## Expected TOS git status after apply

```text
 M backend/src/agency-operator/agents/ramzyAgencyOperator.js
 M backend/src/agency-operator/agents/specialistAgents.js
 M backend/src/agency-operator/prompts/ramzyPrompt.js
 M backend/src/agency-operator/tools/createRamzyTools.js
 M backend/src/routes/tasks.routes.js
 M backend/src/services/permissions.service.js
?? backend/src/agency-operator/services/ramzyTeamPerformance.service.js
 M frontend/src/pages/PermissionsPage.jsx
```

## Deployment note

The runner syncs only the existing permission catalog rows so the new keys become available immediately. This is configuration data, not a schema migration. After verification, reload the existing backend `tamiyouz-system`, deploy the current frontend build to `/opt/apps/tamiyouz-front/build`, and reload `tamiyouz-frontend`.
