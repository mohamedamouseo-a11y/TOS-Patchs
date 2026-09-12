# TOS ← TCRM Client Identity Duplicate Guard V1

MODE=IMPLEMENTATION_WITH_VERIFICATION

You are already inside the live TOS project on the server. Do **not** use GitHub and do not fetch/pull/push anything.

## Goal
Implement the first small prevention step only:

- One TCRM `crmClientId` = one TOS operational project.
- `crmClientId` must be present on inbound `POST /projects`.
- If an existing delivery mapping is found, preserve the current update behavior.
- If there is no delivery mapping, do **not** immediately create a new project when an unlinked legacy/manual TOS project looks like the same client/project.
- In that case return HTTP `409` with code `TCRM_LEGACY_PROJECT_LINK_REQUIRED` and do not create or modify any project.
- Do **not** auto-adopt, merge, archive, or delete anything in this phase.
- Do **not** change database schema in this phase.

## Confirm current live code first

From the real TOS project, inspect:

- `backend/src/routes/crmProjectsIntegration.routes.js`
- `backend/prisma/schema.prisma`

Confirm that current `handleTcrmProjectUpsert`:

1. reads `crmClientId` from `crmClientId || clientPoolId || crmClientNumber || clientId`;
2. looks up `tos_crm_project_deliveries` by `source_key OR crm_client_id`;
3. updates the mapped project when a row is found;
4. otherwise immediately calls `tx.project.create()`;
5. has no legacy reconciliation before create.

If this is not true, STOP and report the difference. Do not guess.

## Required code change

Target only:

`backend/src/routes/crmProjectsIntegration.routes.js`

### A. Require CRM client identity

Change the `crmClientId` read from `normalizedText(...)` to `requiredText(..., "crmClientId")` using the existing fallback chain.

### B. Add a read-only legacy candidate helper

Add a helper that searches active, unarchived TOS `Project` rows that:

- have **no** row in `tos_crm_project_deliveries`;
- exactly match the inbound `projectName` case-insensitively after trim, OR exactly match inbound `clientName` case-insensitively after trim;
- returns at most 10 rows;
- returns only non-sensitive fields: `id`, `name`, `clientName`, `status`, `stage`, `archivedAt`, `createdAt`, `updatedAt`.

Use parameterized Prisma SQL only. No string-built SQL.

### C. Guard before create

Immediately before the current create transaction:

- call the legacy candidate helper;
- if one or more candidates exist, **do not create anything**;
- return HTTP 409 JSON:

```json
{
  "success": false,
  "code": "TCRM_LEGACY_PROJECT_LINK_REQUIRED",
  "message": "An unlinked legacy TOS project may already represent this TCRM client. Automatic project creation was blocked to prevent a duplicate.",
  "crmClientId": "...",
  "projectName": "...",
  "candidateCount": 1,
  "candidates": [],
  "requiredAction": "LINK_EXISTING_PROJECT_OR_CONFIRM_NEW_CLIENT_PROJECT",
  "projectCreated": false
}
```

Do not expose phone, email, website, notes, tokens, or secrets in candidates.

### D. Version marker

Change:

`TCRM_AUTHORITATIVE_PROJECT_RESYNC_ADD_ONLY_TEAM_V1`

to:

`TCRM_CLIENT_IDENTITY_DUPLICATE_GUARD_V1`

## Explicitly out of scope

Do NOT:

- auto-link a legacy project;
- add unique DB constraints yet;
- change Prisma schema;
- clean duplicates;
- archive/delete/merge projects;
- change brief/services/team mapping;
- change TCRM code;
- run a real TCRM sync;
- make POST/PUT/PATCH/DELETE requests to production endpoints;
- git pull/fetch/push/reset/checkout/clean/rebase/merge.

## Verification

After editing:

1. Show `git diff -- backend/src/routes/crmProjectsIntegration.routes.js`.
2. Run:
   `node --check backend/src/routes/crmProjectsIntegration.routes.js`
3. Verify by source inspection only:
   - existing mapped-client path still updates same project;
   - no-mapping + legacy candidate path returns 409 before `project.create()`;
   - no-mapping + zero candidate path still reaches existing create flow;
   - no schema/data cleanup occurred.
4. Do not call the live integration endpoint.
5. Do not restart/deploy unless the user separately approves after reviewing the diff/report.

## Final report

Return exactly the important results:

```text
PATCH=TOS-TCRM-CLIENT-IDENTITY-DUPLICATE-GUARD-V1-GIT-GENERATED
MODE=IMPLEMENTATION_WITH_VERIFICATION
PROJECT_PATH=...
LOCAL_HEAD=...

CURRENT_FLOW_CONFIRMED=YES|NO
CRM_CLIENT_ID_REQUIRED=YES|NO
LEGACY_CANDIDATE_GUARD=YES|NO
LEGACY_MATCH_RULE=...
AUTO_ADOPT=NO
AUTO_CREATE_BLOCKED_WHEN_LEGACY_CANDIDATE_EXISTS=YES|NO
MAPPED_CLIENT_UPDATE_PATH_PRESERVED=YES|NO
ZERO_CANDIDATE_CREATE_PATH_PRESERVED=YES|NO

FILES_CHANGED=...
NODE_CHECK=PASS|FAIL
DATABASE_SCHEMA_CHANGED=NO
PROJECT_DATA_CHANGED=NO
CLEANUP_EXECUTED=NO
SYNC_EXECUTED=NO
DEPLOY=NOT_RUN
SERVICE_RESTART=NO
GIT_PUSH=NO

FINAL_STATUS=PASS|FAIL
```
