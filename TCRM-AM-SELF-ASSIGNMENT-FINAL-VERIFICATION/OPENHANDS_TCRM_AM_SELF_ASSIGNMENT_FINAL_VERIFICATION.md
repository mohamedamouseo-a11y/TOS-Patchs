# TCRM — AM Self-Assignment Final Verification & Scoped TOS Directory Contract

## Objective
Complete the final verification of the Account Management self-assignment patch on TCRM without deployment, and prove that backend authorization uses a trusted TCRM→TOS identity mapping. If the production TOS team-directory API excludes Account Management, stop and report that a separate approved TOS API patch is required before changing TOS.

## Repositories
- TCRM repository: `mohamedamouseo-a11y/TCRM-MAIN-Tamiyouz-CRM-`
- Local TCRM repository: `/var/www/TCRM-MAIN`
- Target branch: `patch/am-self-assign-tos-team-v2`
- Patch/spec repository: `mohamedamouseo-a11y/TOS-Patchs`

## Hard Rules
- DO NOT deploy.
- DO NOT restart PM2.
- DO NOT modify Nginx.
- DO NOT force push.
- DO NOT reset, rebase, or amend existing commits.
- DO NOT invent or assume production API behavior.
- DO NOT assume `TCRM user.id === TOS tosUserId` unless the existing architecture explicitly proves that guarantee.
- Frontend restrictions are UX only. Backend is the source of truth.
- Do not globally expose Account Management through the TOS team-directory API for all consumers.
- If a TOS source-code change is required and there is no already-approved TOS patch covering that exact change, STOP and report `TOS_PATCH_REQUIRED=YES`.

## 1. Verify Local Branch and Existing Commits
Work only in `/var/www/TCRM-MAIN`.

Verify:
- current branch is exactly `patch/am-self-assign-tos-team-v2`
- worktree has no unrelated changes
- resolve the full commit SHAs for:
  - `de8f9fe`
  - `e62b70e`

Required commands:
```bash
git status --short
git branch --show-current
git log -5 --format='%H %P %s'
git rev-parse de8f9fe
git rev-parse e62b70e
```

Stop if the branch is wrong or unrelated worktree changes exist.

## 2. Push Current Branch — No Force
Push exactly:
```bash
git push -u origin patch/am-self-assign-tos-team-v2
```

Then verify:
```bash
git ls-remote --heads origin patch/am-self-assign-tos-team-v2
```

The remote branch SHA must equal local `HEAD`.

## 3. Trace and Verify the Real TOS Team-Directory Contract
Trace the complete implementation path used by:

`accountManagement.getTosProjectTeamDirectory`

Trace:
1. TCRM frontend caller
2. TCRM accountManagement route/service/controller
3. exact HTTP request to TOS
4. exact TOS endpoint/path
5. exact relevant response structure

Test the real production TOS endpoint using the application's existing trusted integration/auth mechanism. Do not print credentials, tokens, cookies, or secrets.

The verification must prove whether the API response actually includes:
- the Account Management department
- Account Management employees
- identity fields available for trusted mapping, where actually returned:
  - TOS user/employee ID
  - email
  - centralEmail
  - department
  - role

Do not assume the frontend can reconstruct employees that the API did not return.

## 4. Scoped TOS API Requirement
If the current TOS team-directory response used by `accountManagement.getTosProjectTeamDirectory` excludes Account Management:

- Do NOT modify TOS directly under this TCRM patch.
- Do NOT globally expose Account Management to every TOS team-directory consumer.
- Report:
  - `TOS_API_CHANGE_REQUIRED=YES`
  - `TOS_PATCH_REQUIRED=YES`
- Stop before implementing TOS changes.

The required future TOS change must be backward-compatible and consumer-scoped, for example an explicit opt-in such as `includeAccountManagement=true` or an equivalent existing request-scope mechanism. Existing consumers must retain current behavior by default.

## 5. Trusted TCRM → TOS Identity Mapping
For a regular `AccountManager`, resolve the currently authenticated TCRM user to exactly one TOS employee identity using a trusted mapping.

Allowed mapping priority:
1. an existing explicit linked TOS user/employee ID, if the architecture already has a canonical link
2. canonical normalized email matching between authenticated TCRM email and TOS `email` / `centralEmail`

Email comparison should use the codebase's canonical normalization rules, including case-insensitive comparison where appropriate.

Required failure behavior:
- zero TOS matches → reject self-assignment
- multiple ambiguous TOS matches → reject self-assignment
- do not fall back to matching raw TCRM `user.id` to TOS user ID unless the architecture explicitly proves that equality is guaranteed

Backend validation for a regular AccountManager must allow adding ONLY the resolved own TOS identity.

## 6. Backend Authorization / Tamper Tests
Use the narrowest existing backend test framework and exercise the real authorization path.

Required cases for a regular AccountManager:

### A. Add own resolved TOS identity
Expected: ALLOWED

### B. Add another Account Management employee
Expected: FORBIDDEN

### C. Add employee from another department
Expected: FORBIDDEN

### D. Remove another existing or pending owner
Expected: FORBIDDEN

Also verify:
- Admin existing permissions remain unchanged
- AccountManagerLead existing permissions remain unchanged

Do not count frontend-only restrictions as authorization tests.

## 7. Check and Build to Completion
Inspect the repository package/workspace configuration and run the project's actual supported equivalents of:
- `pnpm check`
- `pnpm build`

Do not report a running process as success. Both commands must finish with exit code `0`.

Report the exact commands and exit codes.

## 8. Final Remote Verification
After push, verify:
```bash
git rev-parse HEAD
git ls-remote --heads origin patch/am-self-assign-tos-team-v2
git diff --name-status origin/main...HEAD
```

Confirm:
- branch is visible on GitHub
- remote SHA equals local HEAD
- changed files are within expected patch scope

## 9. Deployment Prohibition
Do not run deployment scripts.
Do not restart PM2.
Do not rsync production.
Do not modify Nginx.

## READY Gate
`READY_FOR_PRODUCTION=YES` is allowed only if ALL of the following are proven:
- branch push succeeded without force
- full SHAs for `de8f9fe` and `e62b70e` are resolved
- real TOS directory behavior is proven
- Account Management is available to this consumer, or an approved scoped TOS API patch has already been completed
- trusted TCRM→TOS identity mapping is proven
- all four regular-AM tamper tests pass
- Admin permissions remain unchanged
- AccountManagerLead permissions remain unchanged
- check command exits `0`
- build command exits `0`
- remote branch SHA equals local HEAD
- no deployment occurred

If any condition is missing, report `READY_FOR_PRODUCTION=NO`.

## Final Report Format
Return real values only:

```text
REMOTE_BRANCH=
REMOTE_BRANCH_SHA=

DE8F9FE_FULL_SHA=
E62B70E_FULL_SHA=

FILES_CHANGED=

TOS_TEAM_DIRECTORY_ENDPOINT=
TOS_ACCOUNT_MANAGEMENT_DEPARTMENT_PRESENT=
TOS_ACCOUNT_MANAGEMENT_EMPLOYEES_PRESENT=
TOS_DIRECTORY_RELEVANT_RESPONSE=

TOS_API_CHANGE_REQUIRED=
TOS_PATCH_REQUIRED=

IDENTITY_MAPPING_METHOD=
IDENTITY_MAPPING_FIELD=
TCRM_ID_EQUALS_TOS_ID_PROVEN=

TAMPER_OWN_IDENTITY=
TAMPER_OTHER_AM=
TAMPER_OTHER_DEPARTMENT=
TAMPER_REMOVE_OTHER_OWNER=
ADMIN_PERMISSIONS=
AM_LEAD_PERMISSIONS=

CHECK_COMMAND=
CHECK_EXIT=
BUILD_COMMAND=
BUILD_EXIT=

BRANCH_VISIBLE_ON_GITHUB=
DEPLOY_PERFORMED=NO

READY_FOR_PRODUCTION=
BLOCKER=
```

## Evidence Discipline
- Use literal command output for Git SHAs, branch visibility, exit codes, and endpoint verification.
- Do not use narrative claims as proof.
- Do not print secrets.
- If any field cannot be proven, use `NOT_VERIFIED` rather than guessing.
