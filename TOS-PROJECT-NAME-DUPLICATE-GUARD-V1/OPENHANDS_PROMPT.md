# Apply TOS Project Name Duplicate Guard V1

Work on live TOS only: `/var/www/TOS`.

Goal: apply the prepared backend duplicate-name guard. Keep credit/tool usage minimal.

Rules:
- Do NOT git pull/fetch/reset/checkout/merge.
- Do NOT change DB rows or run migrations.
- Do NOT create/archive/delete projects for testing.
- Do NOT modify TCRM.
- Do NOT push.
- Only target `backend/src/routes/projects.routes.js`.

Run:

```bash
cd /var/www/TOS

curl -fsSL \
https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/1b23360ab5fd8a81b65b767de4c8bca367f1c346/TOS-PROJECT-NAME-DUPLICATE-GUARD-V1/apply_patch.py \
-o /tmp/tos_project_name_duplicate_guard_v1.py

TOS_REPO=/var/www/TOS python3 /tmp/tos_project_name_duplicate_guard_v1.py

node --check backend/src/routes/projects.routes.js

grep -nE "normalizeProjectNameForDuplicateGuard|assertNoActiveProjectNameDuplicate|pg_advisory_xact_lock" backend/src/routes/projects.routes.js

pm2 restart tamiyouz-system
pm2 status tamiyouz-system
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5006/
```

Verification:
- Create guard exists before `tx.project.create()`.
- Rename guard runs when `name` is updated.
- Restore guard runs before unarchiving.
- Arabic normalization includes `ة→ه`, `ؤ→و`, Alef variants, diacritics/whitespace cleanup.
- Same normalized-name concurrent operations use PostgreSQL advisory transaction lock.
- No Prisma schema/migration change.
- No project data changed.

Do not hand-edit if patch prints `STATUS=ABORT`; stop and report the mismatch.

Return only:

```text
PATCH=
PATCH_STATUS=
NODE_CHECK=
CREATE_GUARD=
RENAME_GUARD=
RESTORE_GUARD=
ARABIC_NORMALIZATION=
CONCURRENT_LOCK=
PM2=
HTTP=
FILES_CHANGED=
DB_CHANGED=NO
MIGRATION=NO
PUSH=NO
ERROR=
```
