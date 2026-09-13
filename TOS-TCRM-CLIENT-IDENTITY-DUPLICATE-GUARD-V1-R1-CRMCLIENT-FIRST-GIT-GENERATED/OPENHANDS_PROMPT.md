# TOS ← TCRM Client Identity Duplicate Guard V1 R1 — crmClientId First

MODE=IMPLEMENTATION_WITH_VERIFICATION

You are already inside the live TOS project on the server at `/var/www/TOS`.
Do not use GitHub except to download the public patch runner URL below. Do not fetch/pull/push the TOS repo.

## Goal
Apply one tiny follow-up only:

- `crmClientId` is the primary identity for TCRM→TOS project matching.
- Existing `sourceKey` remains as secondary fallback.
- Preserve the V1 legacy duplicate guard exactly as-is.
- No schema change, no cleanup, no deploy, no restart.

## Pre-check
From `/var/www/TOS`, verify the V1 patch is currently present in `backend/src/routes/crmProjectsIntegration.routes.js`:

- `TCRM_CLIENT_IDENTITY_DUPLICATE_GUARD_V1`
- `crmClientId` is required with `requiredText(...)`
- `findUnlinkedLegacyProjectCandidates` exists
- `TCRM_LEGACY_PROJECT_LINK_REQUIRED` exists
- current delivery lookup still orders `source_key` ahead of `crm_client_id`

If any of these are not true, STOP and report `BASELINE_MISMATCH`.

## Apply

```bash
cd /var/www/TOS

curl -fsSL \
https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/b783c093bbb6793317ba17cdfc016e07ec98ee75/TOS-TCRM-CLIENT-IDENTITY-DUPLICATE-GUARD-V1-R1-CRMCLIENT-FIRST-GIT-GENERATED/apply_patch.py \
-o /tmp/tos_tcrm_duplicate_guard_v1_r1.py

TOS_REPO=/var/www/TOS python3 /tmp/tos_tcrm_duplicate_guard_v1_r1.py
```

If the runner prints `STATUS=ABORT`, stop immediately. Do not edit manually to bypass the guard.

## Verification

Run only:

```bash
node --check backend/src/routes/crmProjectsIntegration.routes.js
git diff -- backend/src/routes/crmProjectsIntegration.routes.js
```

Confirm by source inspection:

1. Delivery lookup still uses both `source_key` and `crm_client_id`.
2. Matching priority is now:
   - FIRST: `crm_client_id = crmClientId`
   - SECONDARY: `source_key = sourceKey`
3. Mapped-client update path is unchanged.
4. V1 legacy candidate 409 guard is unchanged.
5. Zero-candidate create path is unchanged.
6. No schema/data changes occurred.

## Do not do

Do NOT:
- deploy
- restart services
- build
- run migrations
- run sync
- call production POST/PUT/PATCH/DELETE endpoints
- change database data
- clean/archive/delete/merge projects
- git fetch/pull/push/reset/checkout/clean/rebase/merge

## Final report

Return:

```text
PATCH=TOS-TCRM-CLIENT-IDENTITY-DUPLICATE-GUARD-V1-R1-CRMCLIENT-FIRST-GIT-GENERATED
MODE=IMPLEMENTATION_WITH_VERIFICATION
PROJECT_PATH=...
LOCAL_HEAD=...

BASELINE_CONFIRMED=YES|NO
PATCH_RUNNER_STATUS=APPLIED|ALREADY_APPLIED|ABORT
CRM_CLIENT_ID_MATCH_PRIORITY=FIRST|NO
SOURCE_KEY_MATCH_PRIORITY=SECONDARY|NO
LEGACY_DUPLICATE_GUARD_PRESERVED=YES|NO
MAPPED_CLIENT_UPDATE_PATH_PRESERVED=YES|NO
ZERO_CANDIDATE_CREATE_PATH_PRESERVED=YES|NO
FILES_CHANGED=...
NODE_CHECK=PASS|FAIL
DATABASE_SCHEMA_CHANGED=NO
PROJECT_DATA_CHANGED=NO
DEPLOY=NOT_RUN
SERVICE_RESTART=NO
GIT_PUSH=NO
FINAL_STATUS=PASS|FAIL
```

Then include the full `git diff` for `backend/src/routes/crmProjectsIntegration.routes.js`.
