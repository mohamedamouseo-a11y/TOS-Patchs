# TOS → TCRM Team Directory: Account Management Opt-In V1

## Purpose

Fix the TOS integration team-directory contract used by TCRM Account Management Handover so TCRM can explicitly request Account Management employees without exposing that department to every existing team-directory consumer.

## Repository / Runtime

- TOS local repository: `/var/www/TOS`
- GitHub repository: `mohamedamouseo-a11y/TOS`
- Target backend route currently lives in: `backend/src/routes/crmProjectsIntegration.routes.js`
- Existing integration endpoint: `GET /team-directory` under the existing CRM projects integration router.
- The existing endpoint is protected by `requireIntegrationKey`.
- Current source explicitly reports `excludedDepartment: "Account Manager"` and the default behavior must remain backward-compatible.

## Hard Rules

- Work ONLY in `/var/www/TOS`.
- Read the existing `/team-directory` implementation completely before editing.
- DO NOT reset, rebase, amend, force, merge, pull, stash, or rewrite history.
- DO NOT push.
- DO NOT deploy.
- DO NOT restart PM2.
- DO NOT modify Nginx.
- DO NOT change Prisma schema or migrations.
- DO NOT change auth/session architecture or integration-key storage.
- DO NOT globally expose Account Management in the default `/team-directory` response.
- Preserve all existing consumers when the new opt-in parameter is absent.
- Keep the existing integration-key authentication requirement.
- Do not create a second team-directory authority or duplicate endpoint unless the existing routing architecture absolutely requires it.

## 1. Verify the Real Current Contract First

Before modifying code, trace the existing `/team-directory` route and verify its current production response through the same trusted integration configuration used by TCRM.

Sanitize secrets from output.

Prove:

- exact endpoint URL/path used by TCRM,
- whether the Account Management / Account Manager department is currently omitted,
- whether its employees are omitted,
- relevant returned identity fields for employees (`id`/`tosUserId`, `email`, `centralEmail`, department, role where present).

Do not assume frontend code can restore users omitted by TOS.

## 2. Backward-Compatible Opt-In Contract

Extend the EXISTING `/team-directory` endpoint with an explicit opt-in request flag:

`includeAccountManagement=true`

Contract:

- flag absent / false → current behavior remains unchanged; Account Management stays excluded exactly as today.
- flag true → include the canonical Account Management department and its active eligible employees in the directory response.
- existing project-membership information and all unrelated departments remain unchanged.
- existing integration-key authorization remains required.
- do not expose clients, former employees, disabled/inactive users, or records already excluded by the existing eligibility rules.

Use the canonical department identity/name already present in TOS data. The existing response metadata currently uses `"Account Manager"`; inspect the real department records and do not invent a second department name.

## 3. Response Metadata

Keep the response backward-compatible.

When opt-in is not active, preserve the existing `excludedDepartment` behavior/value.

When opt-in is active, make the response truthful. Do not claim Account Management is excluded when it was included. Add only minimal non-breaking metadata if useful, for example an `accountManagementIncluded` boolean.

Do not remove or rename existing response fields.

## 4. Security / Scope

The change is an explicit opt-in on the already protected integration endpoint.

It MUST NOT alter the default directory returned to existing consumers.

It MUST NOT weaken `requireIntegrationKey`.

It MUST NOT add a public unauthenticated route.

It MUST NOT broaden any unrelated role, project, task, or employee permissions.

## 5. Focused Tests

Add or update the narrowest existing backend test(s) for this route/service contract.

Required cases:

1. default request → Account Management excluded (backward compatibility).
2. `includeAccountManagement=false` → Account Management excluded.
3. `includeAccountManagement=true` → Account Management included with active eligible employees.
4. unrelated departments remain present/unchanged.
5. inactive/client/former-employee exclusions remain enforced.
6. request without a valid integration key remains unauthorized exactly as before.

Do NOT run the full repository test suite unless the project has no narrower supported test command.

## 6. Validation

Run the narrowest relevant backend syntax/type/test commands available in the repository and wait for final exit codes.

Then run the project's actual backend/build validation needed for this backend-only change. Do not report a command as successful until it exits 0.

No deployment is allowed in this patch.

## 7. Commit

Create exactly ONE new local commit for this patch:

`fix(tos): add scoped account management team-directory opt-in`

DO NOT PUSH.

## Final Report

Return real values only:

```text
BASE_SHA=
ORIGIN_MAIN=
FILES_CHANGED=
TEAM_DIRECTORY_ROUTE=
PRODUCTION_DEFAULT_AM_PRESENT=
PRODUCTION_DEFAULT_AM_EMPLOYEES_PRESENT=
DEFAULT_BEHAVIOR_PRESERVED=
OPT_IN_PARAMETER=includeAccountManagement=true
OPT_IN_AM_INCLUDED=
INACTIVE_EXCLUSIONS_PRESERVED=
INTEGRATION_AUTH_PRESERVED=
TARGETED_TEST_COMMAND=
TARGETED_TEST_EXIT=
BUILD_OR_CHECK_COMMAND=
BUILD_OR_CHECK_EXIT=
COMMIT_SHA=
WORKTREE=
PUSH_PERFORMED=NO
DEPLOY_PERFORMED=NO
BLOCKER=
```

Do not use invented PASS/YES values. If something cannot be proven, use `NOT_VERIFIED` and explain it in `BLOCKER`.