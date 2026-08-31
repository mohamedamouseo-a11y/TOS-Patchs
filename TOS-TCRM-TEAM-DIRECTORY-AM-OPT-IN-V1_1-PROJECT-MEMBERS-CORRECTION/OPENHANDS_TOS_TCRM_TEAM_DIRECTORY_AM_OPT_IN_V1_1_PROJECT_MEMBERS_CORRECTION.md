# TOS ↔ TCRM Team Directory AM Opt-in V1.1 — Project Members Correction

## Repository / Runtime
- TOS repository: `mohamedamouseo-a11y/TOS`
- Production path: `/var/www/TOS`
- Required baseline on GitHub/main and local HEAD before correction:
  `f45f1a2aa42ded3071b77e2dc6353751cf173fab`

## Confirmed Post-Push Defect
Fresh review of `backend/src/routes/crmProjectsIntegration.routes.js` at `f45f1a2` found the `projectMembers` Account Management filter inverted.

Current wrong code:
```js
const projectMembers = projectMembershipRows
  .filter((membership) => !includeAccountManagement || !isAccountManagementDepartment(membership.user.department))
```

This produces the opposite contract for project members:
- `includeAccountManagement=false` => condition starts with `true`, so Account Management project members are NOT excluded.
- `includeAccountManagement=true` => Account Management project members are filtered OUT.

This breaks backward compatibility and makes the opt-in behavior inconsistent between `departments[].members` and `projectMembers`.

The existing test file is also insufficient because it asserts against hard-coded synthetic response objects instead of executing the real filtering logic, so it could pass while the production implementation is wrong.

## Required Contract
For the team-directory endpoint:

### Default — no opt-in
`GET /api/integrations/crm/team-directory`
- Account Management MUST remain excluded from `departments`.
- Account Management MUST remain excluded from `projectMembers`.
- `excludedDepartment = "Account Manager"`
- `accountManagementIncluded = false`

### Explicit opt-in
`GET /api/integrations/crm/team-directory?includeAccountManagement=true`
- Account Management MAY appear in `departments`.
- Account Management project members MUST also be allowed in `projectMembers`.
- `excludedDepartment = null`
- `accountManagementIncluded = true`

The same behavior applies to the already accepted truthy values `true`, `1`, `yes` case-insensitively.

## Required Fix
Correct the actual `projectMembers` predicate so it means:
- include the row when opt-in is enabled, OR
- when opt-in is disabled, include only non-Account-Management rows.

Expected policy equivalent:
```js
includeAccountManagement || !isAccountManagementDepartment(membership.user.department)
```

Do not introduce a global Account Management exposure. Do not change the integration-key authorization model.

## Required Tests
Replace or strengthen `backend/src/routes/crmProjectsIntegration.routes.test.js` so the focused tests exercise the ACTUAL policy/route logic used by production.

Hard requirement: the tests must fail against commit `f45f1a2` before the correction and pass after the correction.

At minimum prove all four cases:
1. default: AM department member excluded
2. opt-in: AM department member included
3. default: AM `projectMembers` row excluded
4. opt-in: AM `projectMembers` row included

Also preserve the truthy query parsing checks and backward-compatible default behavior.

Do NOT use hard-coded response objects that merely describe the expected result without executing the production filtering policy.

Use the narrowest existing test mechanism available. If extracting a tiny pure policy helper is the safest way to test the exact production predicate, keep it narrowly scoped and make the route consume that same helper.

## Scope / Safety
- Work only in `/var/www/TOS`.
- Start only if local HEAD and `origin/main` both equal `f45f1a2aa42ded3071b77e2dc6353751cf173fab` and worktree is clean.
- No reset, rebase, amend, force push, history rewrite.
- No Prisma schema/migrations/DB changes.
- No Auth changes.
- No Nginx changes.
- No scheduler/worker changes.
- No TNC/Phase10 changes.
- Do not touch GitHub Sync UI.
- Do not expose or print any integration API key.
- Do not deploy or restart PM2 in this correction task.
- Do not push.

## Validation
Run the focused AM team-directory test to completion and show the literal command and exit code.

Then run a syntax/import check appropriate to the changed backend files if available.

Verify final diff against `f45f1a2` contains only the files genuinely required for this correction.

## Commit
Create exactly one new local commit on top of `f45f1a2`:

`fix(tos): correct AM opt-in project-members filtering`

DO NOT PUSH.

## Final Report
Return real values only:

```text
BASE_HEAD=
ORIGIN_MAIN=
FILES_CHANGED=
DEFAULT_AM_DEPARTMENT=
OPTIN_AM_DEPARTMENT=
DEFAULT_AM_PROJECT_MEMBER=
OPTIN_AM_PROJECT_MEMBER=
TEST_COMMAND=
TEST_EXIT=
BACKEND_CHECK=
COMMIT_SHA=
WORKTREE=
DEPLOY_PERFORMED=NO
PM2_RESTARTED=NO
PUSH_PERFORMED=NO
API_KEY_PRINTED=NO
BLOCKER=
```
