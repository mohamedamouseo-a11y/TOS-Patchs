# TOS ← TCRM Client Identity Duplicate Guard V1

MODE=IMPLEMENTATION_WITH_VERIFICATION

You are already inside the live TOS project on the server, normally `/var/www/TOS`.

## Goal
Apply the prepared patch runner only. This is the first prevention step for TCRM → TOS project duplicates.

Contract for this phase:
- One TCRM `crmClientId` = one TOS operational project.
- Existing delivery mapping must continue to update the same project.
- If no mapping exists and an unlinked legacy/manual TOS project matches the inbound project/client name, block automatic creation with HTTP 409 `TCRM_LEGACY_PROJECT_LINK_REQUIRED`.
- Do NOT auto-adopt, merge, archive, delete, or clean existing projects.
- Do NOT change Prisma schema or existing project data.

## Hard restrictions
Do NOT:
- use git fetch/pull/push/reset/checkout/clean/rebase/merge;
- modify TCRM;
- run a real TCRM sync;
- call production POST/PUT/PATCH/DELETE endpoints;
- modify database rows manually;
- run migrations;
- deploy or restart services;
- expose secrets, tokens, API keys, or `.env` values.

## Step 1 — Confirm live baseline first

From the real TOS project:

```bash
cd /var/www/TOS
pwd
git rev-parse HEAD 2>/dev/null || true
git status --short 2>/dev/null || true
```

Inspect these files only:

- `backend/src/routes/crmProjectsIntegration.routes.js`
- `backend/prisma/schema.prisma`

Confirm current `handleTcrmProjectUpsert` still behaves like this:
1. reads `crmClientId` from `crmClientId || clientPoolId || crmClientNumber || clientId`;
2. looks up `tos_crm_project_deliveries` by `source_key OR crm_client_id`;
3. updates the mapped project if found;
4. otherwise reaches `tx.project.create()`;
5. has no legacy reconciliation guard before create.

If that is not true, STOP and report `BASELINE_MISMATCH`. Do not apply anything.

## Step 2 — Download the prepared patch runner

Use this pinned public raw file only:

```bash
curl -fsSL \
https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/f6cb4bb90ab3cf32d217abc65fbd98dbd0fce352/TOS-TCRM-CLIENT-IDENTITY-DUPLICATE-GUARD-V1-GIT-GENERATED/apply_patch.py \
-o /tmp/tos_tcrm_client_identity_duplicate_guard_v1.py
```

Do not clone any repository.

## Step 3 — Apply to the live TOS project

```bash
TOS_REPO=/var/www/TOS python3 /tmp/tos_tcrm_client_identity_duplicate_guard_v1.py
```

The runner is anchor-guarded. If it prints `STATUS=ABORT` or `REASON=BASELINE_ANCHOR_MISMATCH`, STOP immediately and do not hand-edit around the failure.

## Step 4 — Verify source change only

Run:

```bash
cd /var/www/TOS
git diff -- backend/src/routes/crmProjectsIntegration.routes.js
node --check backend/src/routes/crmProjectsIntegration.routes.js
```

Then verify by source inspection only:
- mapped-client path still updates the same project;
- `crmClientId` is now required;
- no-mapping + legacy candidate returns 409 before `project.create()`;
- no-mapping + zero candidate still reaches the existing create flow;
- no Prisma schema change happened;
- no existing project data was changed.

Do NOT call the live endpoint.
Do NOT deploy.
Do NOT restart.
Do NOT push.

## Final report

Return this in chat:

```text
PATCH=TOS-TCRM-CLIENT-IDENTITY-DUPLICATE-GUARD-V1-GIT-GENERATED
MODE=IMPLEMENTATION_WITH_VERIFICATION
PROJECT_PATH=...
LOCAL_HEAD=...

BASELINE_CONFIRMED=YES|NO
PATCH_RUNNER_STATUS=APPLIED|ALREADY_APPLIED|ABORT
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

Also include the full `git diff -- backend/src/routes/crmProjectsIntegration.routes.js` output after the report so it can be reviewed before any deploy.