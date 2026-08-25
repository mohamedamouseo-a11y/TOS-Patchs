# TCS Phase 1 — Continue V7 (Drizzle dotenv + guarded migration)

Repository: `mohamedamouseo-a11y/TOS`
Branch: `main` ONLY
Pinned baseline HEAD: `03a61b7bc84baa8e801ec40f33d24bbaf0969894`

## Context

V6 proved:

- TCS source patches are already applied and must NOT be reapplied.
- Logout test-harness fix is already applied.
- Full tests PASS: 6 files / 24 tests.
- Production build PASS.
- TCS source-specific TypeScript gate PASS.
- TCS branding gate PASS.
- The only blocker was `pnpm db:push` failing because the Manus shell did not expose `DATABASE_URL`.

Root cause confirmed by ChatGPT from repository source:

- `server/_core/index.ts` imports `dotenv/config`, so the running application can load `.env`.
- `drizzle.config.ts` did not import `dotenv/config`, so Drizzle CLI did not load `.env` when `DATABASE_URL` was absent from the parent shell.
- `.env` is gitignored.

ChatGPT authored one narrow configuration patch:

`TCS/Phase-1/V2/TCS_PHASE_1_DRIZZLE_DOTENV_FIX_V1.patch`

It adds only:

```ts
import "dotenv/config";
```

to `drizzle.config.ts`.

## Strict rules

1. Do NOT create a branch.
2. Do NOT run `git pull`.
3. Do NOT reapply TCS feature patches.
4. Do NOT reapply the logout test patch.
5. Do NOT rewrite TCS or unrelated production code.
6. Apply ONLY the Drizzle dotenv patch supplied by ChatGPT.
7. Do NOT print, log, copy, upload, or include the value of `DATABASE_URL` in any report/evidence.
8. Do NOT commit `.env` or any secret file.
9. Preserve the three existing untracked production ZIPs exactly.
10. Before applying a migration, inspect newly generated SQL and STOP if it contains unrelated or destructive schema changes.
11. Never enter GitHub credentials interactively.
12. Product name is `TCS — Tamayouz Chat System`; no TACS branding.

## Step 1 — verify current worktree

From `/var/www/TOS`:

```bash
set -euo pipefail

git branch --show-current
git rev-parse HEAD
git diff --check
git status --short
```

Required:

- branch = `main`
- HEAD = `03a61b7bc84baa8e801ec40f33d24bbaf0969894`
- existing intended TCS changes remain present
- existing test harness changes remain present
- the three `TOS_V1.15.*.zip` artifacts remain untouched

Do NOT reset or clean this validated worktree.

## Step 2 — verify production dotenv source WITHOUT revealing secrets

Run only presence checks:

```bash
if [ ! -f .env ]; then
  echo 'TCS_V7_DOTENV_FILE=ABSENT'
  exit 71
fi

if ! grep -q '^DATABASE_URL=' .env; then
  echo 'TCS_V7_DATABASE_URL_IN_DOTENV=ABSENT'
  exit 72
fi

echo 'TCS_V7_DOTENV_FILE=PRESENT'
echo 'TCS_V7_DATABASE_URL_IN_DOTENV=PRESENT'
```

Do NOT run `cat .env`, `grep DATABASE_URL .env` without `-q`, `printenv DATABASE_URL`, or any command that prints the value.

## Step 3 — obtain and pre-check the ChatGPT Drizzle patch

```bash
rm -rf /tmp/TOS-Patchs-TCS-P1-V7
git clone --depth 1 https://github.com/mohamedamouseo-a11y/TOS-Patchs.git /tmp/TOS-Patchs-TCS-P1-V7

DB_ENV_PATCH=/tmp/TOS-Patchs-TCS-P1-V7/TCS/Phase-1/V2/TCS_PHASE_1_DRIZZLE_DOTENV_FIX_V1.patch

git apply --check "$DB_ENV_PATCH"
```

If pre-check fails, STOP and report exact evidence only.

## Step 4 — apply only the Drizzle dotenv patch

```bash
git apply "$DB_ENV_PATCH"
git diff --check
```

Verify the change is exactly one added import in `drizzle.config.ts`:

```bash
git diff -- drizzle.config.ts
```

The diff must contain only:

```ts
import "dotenv/config";
```

No secret value may appear.

## Step 5 — prove Drizzle now sees DATABASE_URL without printing it

```bash
node --input-type=module <<'NODE'
import 'dotenv/config';
if (!process.env.DATABASE_URL) process.exit(73);
console.log('TCS_V7_DATABASE_URL_LOAD=PASS');
NODE
```

Then verify Drizzle config can initialize:

```bash
pnpm exec drizzle-kit --version
```

Do not print the connection string.

## Step 6 — regression gates before DB mutation

The V6 gates already passed, but rerun after the one-line config change:

```bash
pnpm test 2>&1 | tee /tmp/tcs-v7-test.txt
pnpm build 2>&1 | tee /tmp/tcs-v7-build.txt
pnpm check > /tmp/tcs-v7-check.txt 2>&1 || true
```

Required:

- full tests PASS
- build PASS
- ZERO TS errors in:
  - `client/src/components/TcsChat.tsx`
  - `server/tcsRouter.ts`
  - `server/auth.logout.test.ts`
  - `server/tos.test.ts`
  - `drizzle.config.ts`

Use:

```bash
if grep -Ei 'client/src/components/TcsChat\.tsx\([0-9]+,[0-9]+\): error TS|server/tcsRouter\.ts\([0-9]+,[0-9]+\): error TS|server/auth\.logout\.test\.ts\([0-9]+,[0-9]+\): error TS|server/tos\.test\.ts\([0-9]+,[0-9]+\): error TS|drizzle\.config\.ts\([0-9]+,[0-9]+\): error TS' /tmp/tcs-v7-check.txt; then
  echo 'TCS_V7_SOURCE_TYPECHECK=FAIL'
  exit 74
fi

echo 'TCS_V7_SOURCE_TYPECHECK=PASS'
```

Branding gate:

```bash
if git diff -- . ':!*.zip' | grep -n 'TACS'; then
  echo 'TCS_V7_BRANDING=FAIL'
  exit 75
fi

echo 'TCS_V7_BRANDING=PASS'
```

## Step 7 — guarded migration generation

Do NOT use the combined `pnpm db:push` yet. Generate first so SQL can be inspected before database mutation.

Record current Drizzle files:

```bash
find drizzle -maxdepth 2 -type f -printf '%P\n' | sort > /tmp/tcs-v7-drizzle-before.txt
```

Generate:

```bash
pnpm exec drizzle-kit generate 2>&1 | tee /tmp/tcs-v7-db-generate.txt
```

Record after state and identify generated files:

```bash
find drizzle -maxdepth 2 -type f -printf '%P\n' | sort > /tmp/tcs-v7-drizzle-after.txt
comm -13 /tmp/tcs-v7-drizzle-before.txt /tmp/tcs-v7-drizzle-after.txt | tee /tmp/tcs-v7-new-drizzle-files.txt
```

Identify the newly generated `.sql` migration file. If no new SQL migration is generated, STOP and report the exact generator output and Drizzle state; do not guess.

## Step 8 — SQL safety inspection BEFORE migrate

Inspect ONLY the newly generated SQL migration.

It may create only the TCS Phase 1 schema:

- `tcs_conversations`
- `tcs_conversation_members`
- `tcs_messages`
- their indexes
- their foreign keys to each other and existing `users.id`

Allowed operations are limited to creation of those new TCS tables/indexes/constraints.

STOP before migration if the SQL includes any of the following against pre-existing non-TCS schema:

- `DROP`
- `TRUNCATE`
- `DELETE`
- destructive rename
- `ALTER TABLE` for any non-`tcs_*` table
- creation/modification of unrelated tables
- data updates/inserts unrelated to Drizzle migration metadata

Record a redacted-safe SQL review summary. Do not include credentials (migration SQL should contain none).

If safe:

```bash
echo 'TCS_V7_MIGRATION_SQL_SAFETY=PASS'
```

Otherwise STOP:

```bash
echo 'TCS_V7_MIGRATION_SQL_SAFETY=FAIL'
exit 76
```

## Step 9 — apply migration

Only after SQL safety PASS:

```bash
pnpm exec drizzle-kit migrate 2>&1 | tee /tmp/tcs-v7-db-migrate.txt
```

## Step 10 — verify TCS tables directly without exposing connection details

Run:

```bash
node --input-type=module <<'NODE'
import 'dotenv/config';
import mysql from 'mysql2/promise';
const expected = ['tcs_conversations','tcs_conversation_members','tcs_messages'];
const conn = await mysql.createConnection(process.env.DATABASE_URL);
try {
  const [rows] = await conn.query(
    `SELECT TABLE_NAME AS name
       FROM information_schema.TABLES
      WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME IN ('tcs_conversations','tcs_conversation_members','tcs_messages')
      ORDER BY TABLE_NAME`
  );
  const found = rows.map(r => r.name).sort();
  console.log('TCS_TABLES_FOUND=' + found.join(','));
  if (found.length !== expected.length || expected.some(x => !found.includes(x))) process.exit(77);
  console.log('TCS_V7_TABLE_VERIFICATION=PASS');
} finally {
  await conn.end();
}
NODE
```

No database URL may be printed.

## Step 11 — functional + authorization validation

Perform the previously required two-real-user validation:

1. TCS launcher renders.
2. UI says TCS, never TACS.
3. User A finds User B.
4. Direct conversation opens/creates.
5. User A sends a message.
6. User B sees unread conversation/badge.
7. Opening clears unread.
8. User B replies.
9. User A receives reply via polling without full page reload.
10. Refresh preserves history.
11. Ramzy / AI assistant still works.
12. Help Center assistant still works.
13. Operational Inbox still works.
14. TWorkspace still works.

Authorization:

- non-member cannot read another conversation
- non-member cannot send to another conversation
- user cannot start a direct chat with themselves

If runtime validation requires a service restart/reload, first identify the existing production process manager and perform only its normal graceful restart/reload mechanism. Do NOT invent a new process manager, change ports, or create a second production service. Record the exact service/process manager used. Any runtime regression = STOP before commit/push.

## Step 12 — final scope safety

```bash
git diff --check
git status --short
```

Expected tracked scope only:

TCS Phase 1:
- `drizzle/schema.ts`
- `server/routers.ts`
- `server/tcsRouter.ts`
- `client/src/components/TcsChat.tsx`
- `client/src/components/DashboardLayout.tsx`
- generated Drizzle migration/meta files

Independent test harness fix:
- `server/auth.logout.test.ts`
- `server/tos.test.ts`

Drizzle environment fix:
- `drizzle.config.ts`

Plus the three existing untracked production ZIPs, untouched.

No `.env` file may be staged.

## Step 13 — three atomic commits, then push once

Only after every gate passes:

```bash
# 1) Independent test harness fix
git add server/auth.logout.test.ts server/tos.test.ts
git commit -m "test(auth): support response append in logout mocks"
TEST_FIX_SHA="$(git rev-parse HEAD)"

# 2) Drizzle CLI env loading fix
git add drizzle.config.ts
git commit -m "fix(db): load dotenv in drizzle config"
DB_ENV_FIX_SHA="$(git rev-parse HEAD)"

# 3) TCS Phase 1 + generated migration
git add drizzle server/tcsRouter.ts server/routers.ts client/src/components/TcsChat.tsx client/src/components/DashboardLayout.tsx
git commit -m "feat(tcs): add phase 1 direct messaging"
TCS_SHA="$(git rev-parse HEAD)"

printf 'TEST_FIX_SHA=%s\n' "$TEST_FIX_SHA"
printf 'DB_ENV_FIX_SHA=%s\n' "$DB_ENV_FIX_SHA"
printf 'TCS_SHA=%s\n' "$TCS_SHA"

GIT_TERMINAL_PROMPT=0 git push origin main
```

Before each commit, verify `.env` is not staged:

```bash
git diff --cached --name-only | grep -E '^\.env($|\.)' && exit 78 || true
```

If push fails only because authentication is unavailable, retain all successful local commits and report exact error + all three SHAs. Do not reset and do not enter credentials interactively.

## Final report ZIP required

Return one ZIP containing Markdown report + evidence for:

- starting branch + HEAD
- TCS/test-fix preservation
- `.env` presence checks only (never value)
- Drizzle dotenv patch pre-check/apply
- tests/build/source typecheck/branding
- migration generation output
- exact new migration filename(s)
- migration SQL safety decision
- migration apply output
- TCS table verification
- production process manager/restart evidence if used
- two-user functional matrix
- authorization matrix
- test fix SHA
- DB env fix SHA
- TCS Phase 1 SHA
- push result + remote SHA
- exact final changed files
- confirmation `.env` was never printed/staged/committed
- confirmation the three production ZIPs were untouched
