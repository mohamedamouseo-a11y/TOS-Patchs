# TOS ← TCRM Client Brief Mapping V1 — Receiver

MODE=IMPLEMENTATION_WITH_VERIFICATION

You are already inside the live TOS project on the TOS server at `/var/www/TOS`.
Do not use GitHub except to download the public patch runner below. Do not fetch/pull/push the TOS repo.

## Goal
Prepare TOS to receive and persist the structured, sanitized TCRM Client Handover Brief.

This phase changes TOS only:
- add `Project.crmHandoverBrief Json?`;
- add a Prisma migration file for a JSONB column;
- accept a root/nested `crmHandoverBrief` object from TCRM;
- store it on create/update of the already-linked project;
- keep existing project Description/Notes/Tasks/Boards/Files/Memberships behavior unchanged.

Important: this phase MUST NOT execute the migration or deploy. It only applies source/schema/migration files and verifies them.

## 1. Pre-check

From `/var/www/TOS` inspect:

- `backend/src/routes/crmProjectsIntegration.routes.js`
- `backend/prisma/schema.prisma`

Confirm before applying:

1. V1+R1 duplicate prevention is present.
2. `crmClientId` remains required.
3. delivery matching still prioritizes `crm_client_id` before `source_key`.
4. `buildProjectDataFromCrmPayload` exists.
5. `Project` currently has no `crmHandoverBrief` field.
6. `STRUCTURED_PROJECT_SYNC_VERSION` is still `TCRM_TOS_STRUCTURED_PROJECT_SYNC_V1C_NOTES_SUMMARY`.

If the baseline differs materially, STOP and report `BASELINE_MISMATCH`.

## 2. Download patch runner

```bash
cd /var/www/TOS
curl -fsSL \
https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/efc73adc50cce75027431c371349205513fe6171/TOS-TCRM-CLIENT-BRIEF-MAPPING-V1-RECEIVER-GIT-GENERATED/apply_patch.py \
-o /tmp/tos_tcrm_client_brief_mapping_v1_receiver.py
```

## 3. Apply

```bash
TOS_REPO=/var/www/TOS python3 /tmp/tos_tcrm_client_brief_mapping_v1_receiver.py
```

If the runner prints `STATUS=ABORT`, stop immediately. Do not edit manually to bypass anchors.

## 4. Verification

Run:

```bash
cd /var/www/TOS
node --check backend/src/routes/crmProjectsIntegration.routes.js
cd backend && npm run prisma:validate
cd /var/www/TOS
git diff -- backend/src/routes/crmProjectsIntegration.routes.js backend/prisma/schema.prisma backend/prisma/migrations/202609131300_add_crm_handover_brief/migration.sql
```

Verify by source inspection:

- `Project.crmHandoverBrief` is `Json?`.
- migration adds JSONB column only.
- `crmHandoverBrief` accepts object or null only.
- payload larger than 50KB is rejected.
- on update, missing brief does not erase existing brief.
- explicit `crmHandoverBrief: null` can clear it.
- current project Description mapping remains unchanged.
- duplicate guard and crmClientId-first matching remain unchanged.
- no project/task/member cleanup or mutation happened.

## 5. Do not do

Do NOT:
- run Prisma migration/deploy;
- build/deploy/restart;
- run TCRM sync;
- call production POST/PUT/PATCH/DELETE endpoints;
- modify project data;
- edit TCRM;
- git fetch/pull/push/reset/checkout/clean/rebase/merge.

## 6. Final report

Return:

```text
PATCH=TOS-TCRM-CLIENT-BRIEF-MAPPING-V1-RECEIVER-GIT-GENERATED
MODE=IMPLEMENTATION_WITH_VERIFICATION
PROJECT_PATH=...
LOCAL_HEAD=...

BASELINE_CONFIRMED=YES|NO
PATCH_RUNNER_STATUS=APPLIED|ALREADY_APPLIED|ABORT
CRM_HANDOVER_BRIEF_FIELD=crmHandoverBrief|NO
CRM_HANDOVER_BRIEF_TYPE=JSON|NO
RECEIVER_ACCEPTS_OBJECT_OR_NULL=YES|NO
MAX_BRIEF_SIZE_GUARD=50000|NO
DESCRIPTION_MAPPING_PRESERVED=YES|NO
DUPLICATE_GUARD_PRESERVED=YES|NO
CRM_CLIENT_ID_FIRST_PRESERVED=YES|NO

FILES_CHANGED=...
NODE_CHECK=PASS|FAIL
PRISMA_VALIDATE=PASS|FAIL
MIGRATION_FILE_CREATED=YES|NO
MIGRATION_EXECUTED=NO
PROJECT_DATA_CHANGED=NO
TCRM_CODE_CHANGED=NO
DEPLOY=NOT_RUN
SERVICE_RESTART=NO
GIT_PUSH=NO
FINAL_STATUS=PASS|FAIL
```

Then include the full git diff for the three target paths.
