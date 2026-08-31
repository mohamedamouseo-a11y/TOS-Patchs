# TOS ↔ TCRM Team Directory AM Opt-in V1.2 — Shared Policy Test Integrity

## Repository / Runtime
- TOS repository: `mohamedamouseo-a11y/TOS`
- Production path: `/var/www/TOS`
- Required local HEAD before this task:
  `6d5757869b769944dc5858e87c32920574a78eac`
- Required `origin/main` before this task:
  `f45f1a2aa42ded3071b77e2dc6353751cf173fab`

## Confirmed Problem
The V1.1 production predicate was corrected, but the focused tests still duplicate the route predicate locally. Therefore the tests do not consume the same policy code as production and cannot prove they would catch the original inversion bug.

Current test integrity findings:
- `TEST_USES_SHARED_PRODUCTION_POLICY=NO`
- `TEST_DUPLICATES_PREDICATE=YES`
- `FAILS_ON_F45F1A2=NOT_PROVEN`

## Goal
Make the route and tests consume ONE shared, side-effect-free Account Management team-directory policy implementation.

The production route must not carry a second copy of the AM inclusion/exclusion predicate, and the tests must not define their own duplicate predicate.

## Required Design
Use the narrowest safe implementation.

Preferred approach:
1. Add a small pure helper module near the route, for example:
   `backend/src/routes/crmProjectsIntegration.teamDirectoryPolicy.js`
2. Move ONLY the pure AM team-directory policy into that module, including helpers needed to decide:
   - query opt-in parsing (`true`, `1`, `yes`, case-insensitive)
   - whether an Account Management department/user/project member is included
3. Import and consume that helper from:
   - `backend/src/routes/crmProjectsIntegration.routes.js`
   - `backend/src/routes/crmProjectsIntegration.routes.test.js`
4. The test file MUST NOT reimplement those predicates locally.

Do not move unrelated route/business logic.

## Required Contract
Default, no opt-in:
- AM department excluded
- AM user excluded
- AM projectMember excluded
- `excludedDepartment = "Account Manager"`
- `accountManagementIncluded = false`

Explicit opt-in (`true`, `1`, or `yes`):
- AM department allowed
- AM user allowed
- AM projectMember allowed
- `excludedDepartment = null`
- `accountManagementIncluded = true`

Non-AM departments/users/projectMembers must remain unchanged.

## Required Test Integrity
Tests must import the exact shared production helper used by the route.

Prove all four required AM cases through the shared helper:
1. default AM department excluded
2. opt-in AM department included
3. default AM projectMember excluded
4. opt-in AM projectMember included

Also test truthy query parsing and non-AM behavior.

Add a guard that proves the route actually imports/uses the shared helper and does not retain a duplicate inline AM projectMembers predicate.

### Regression proof
Provide a negative-control proof that the corrected tests would detect the old inverted projectMembers behavior. Do this without changing git history or the production worktree.

Acceptable method:
- create temporary copies under `/var/tmp`,
- substitute ONLY the shared project-member policy in the temporary copy with the old buggy expression equivalent to:
  `!includeAccountManagement || !isAccountManagementDepartment(...)`,
- run the same focused test against that temporary mutated helper,
- require non-zero exit,
- remove temporary files.

Do NOT checkout/reset/rebase the main worktree.

Report:
- `NEGATIVE_CONTROL_EXIT` must be non-zero
- `CURRENT_TEST_EXIT` must be 0

## Scope / Safety
- Work only in `/var/www/TOS` except temporary negative-control files under `/var/tmp`.
- Start only if local HEAD is exactly `6d5757869b769944dc5858e87c32920574a78eac`.
- `origin/main` must still equal `f45f1a2aa42ded3071b77e2dc6353751cf173fab`.
- Worktree must be clean.
- No reset, rebase, amend, force, history rewrite.
- No Prisma/schema/migration/DB changes.
- No auth changes.
- No Nginx changes.
- No TNC/Phase10 changes.
- Do not deploy.
- Do not restart PM2.
- Do not push.
- Do not print or read integration API keys.

## Validation
Run the actual focused test to completion.
Run backend syntax/import check appropriate to changed files.
Verify final diff against `6d5757869b769944dc5858e87c32920574a78eac` contains only the files needed for shared policy/test integrity.

Expected changed files should normally be only:
- `backend/src/routes/crmProjectsIntegration.routes.js`
- `backend/src/routes/crmProjectsIntegration.routes.test.js`
- `backend/src/routes/crmProjectsIntegration.teamDirectoryPolicy.js` (new)

If more files are required, explain exactly why; otherwise STOP if unrelated files appear.

## Commit
Create exactly one local commit on top of V1.1:

`test(tos): share AM team-directory policy with route tests`

DO NOT PUSH.

## Final Report
Return real values only:

```text
BASE_HEAD=
ORIGIN_MAIN=
FILES_CHANGED=
SHARED_POLICY_FILE=
ROUTE_USES_SHARED_POLICY=YES/NO
TEST_USES_SHARED_POLICY=YES/NO
TEST_DUPLICATES_PREDICATE=YES/NO
DEFAULT_AM_DEPARTMENT=
OPTIN_AM_DEPARTMENT=
DEFAULT_AM_PROJECT_MEMBER=
OPTIN_AM_PROJECT_MEMBER=
NEGATIVE_CONTROL_EXIT=
CURRENT_TEST_COMMAND=
CURRENT_TEST_EXIT=
BACKEND_CHECK=
COMMIT_SHA=
WORKTREE=
DEPLOY_PERFORMED=NO
PM2_RESTARTED=NO
PUSH_PERFORMED=NO
API_KEY_PRINTED=NO
BLOCKER=
```