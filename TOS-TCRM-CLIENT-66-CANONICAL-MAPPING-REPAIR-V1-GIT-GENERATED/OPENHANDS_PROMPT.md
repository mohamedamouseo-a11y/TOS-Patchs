# TOS — Client 66 Canonical Mapping Repair V1

PROJECT_PATH=/var/www/TOS
MODE=CONTROLLED_DATABASE_REPAIR

## Context

Read-only reconciliation already established:

- CRM client: `66`
- Client name: `Modern House Furniture`
- Canonical operational project: `cmqgbwzwp0003iml9dtnuaafk`
  - 27 tasks, 10 members, 3 files, 157 activity rows, 2 task services
- Stale near-empty shell: `cmsusfbox007gmxl9y1lubgwe`
- Current `tos_crm_project_deliveries` mapping incorrectly points client 66 to the stale shell.
- TCRM already stores the canonical project id `cmqgbwzwp0003iml9dtnuaafk`.

Goal: re-point ONLY the existing CRM delivery mapping row for client 66 from the stale shell to the canonical operational project.

Do NOT archive, merge, delete, or modify either Project row in this phase.

## Safety rules

Forbidden:

- source code edits
- Project row updates
- task/member/file/activity changes
- archiving or deleting either project
- migrations/schema changes
- TCRM sync
- API writes
- deploy/restart
- git pull/fetch/push/reset/checkout/clean/rebase/merge
- printing database credentials or secrets

## 1. Confirm project

```bash
cd /var/www/TOS
pwd
git rev-parse HEAD
git status --short
```

Must be `/var/www/TOS`.

## 2. Read-only precheck

Before applying the repair, independently verify through the current database:

- both project IDs exist
- both names are `Modern House Furniture`
- canonical project is not archived
- exactly ONE mapping row exists for `crm_client_id=66`
- that row currently points to `cmsusfbox007gmxl9y1lubgwe`
- ZERO mapping rows currently point to canonical project `cmqgbwzwp0003iml9dtnuaafk`

If any condition differs, STOP. Do not repair manually.

## 3. Download controlled repair

```bash
curl -fsSL \
https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/70c68ada79442cc1b08d8572a28b2f43e9f96cc8/TOS-TCRM-CLIENT-66-CANONICAL-MAPPING-REPAIR-V1-GIT-GENERATED/reconcile_client_66.mjs \
-o /tmp/tos_client66_mapping_repair.mjs
```

## 4. Execute once

```bash
TOS_REPO=/var/www/TOS node /tmp/tos_client66_mapping_repair.mjs
```

The script performs strict prechecks again, locks the mapping row in a transaction, updates exactly one delivery mapping row, and performs postchecks before commit.

If it prints `STATUS=ABORT`, STOP immediately.

## 5. Independent post-verification

Read-only verify after the script:

- `crm_client_id=66` mapping count = 1
- mapped project id = `cmqgbwzwp0003iml9dtnuaafk`
- stale project `cmsusfbox007gmxl9y1lubgwe` mapping count = 0
- canonical project still exists and is not archived
- stale project still exists and was NOT archived
- no Project row, Task, ProjectMember, File, Activity, TaskService, or source file was changed by this phase

Do NOT run TCRM sync yet.

## Final report

```text
PHASE=TOS_CLIENT_66_CANONICAL_MAPPING_REPAIR
PROJECT_PATH=
LOCAL_HEAD=

PRECHECK=PASS|FAIL
PATCH_STATUS=APPLIED|ABORT

CRM_CLIENT_ID=66
MAPPING_COUNT_BEFORE=
MAPPED_PROJECT_BEFORE=

CANONICAL_PROJECT_ID=cmqgbwzwp0003iml9dtnuaafk
STALE_PROJECT_ID=cmsusfbox007gmxl9y1lubgwe

ROWS_UPDATED=1|0
MAPPING_COUNT_AFTER=
MAPPED_PROJECT_AFTER=
STALE_PROJECT_MAPPING_COUNT_AFTER=

CANONICAL_PROJECT_EXISTS=YES|NO
CANONICAL_PROJECT_ARCHIVED=NO|YES
STALE_PROJECT_EXISTS=YES|NO
STALE_PROJECT_ARCHIVED=NO|YES

PROJECT_ROWS_CHANGED=NO
OPERATIONAL_DATA_CHANGED=NO
SOURCE_CODE_CHANGED=NO
DATABASE_SCHEMA_CHANGED=NO
SYNC_EXECUTED=NO
API_WRITE_EXECUTED=NO
DEPLOY=NOT_RUN
SERVICE_RESTART=NO
GIT_PUSH=NO
SECRETS_EXPOSED=NO

FINAL_STATUS=PASS|FAIL
```
