# TCS Phase 1 — Continue V8 (Use running TOS process DB environment)

Repository: `mohamedamouseo-a11y/TOS`
Branch: `main` ONLY
Pinned baseline HEAD: `03a61b7bc84baa8e801ec40f33d24bbaf0969894`

## Context

V7 stopped only because `/var/www/TOS/.env` does not exist. Do NOT treat the missing `.env` file as a blocker.

The TOS application is already running in production and database-backed functionality exists, so V8 must source `DATABASE_URL` from the environment of the currently running TOS Node process, without ever printing or persisting the secret.

The V7 Drizzle dotenv patch was NOT applied and is NOT needed in V8. Do NOT apply it.

Previously validated state that must remain intact:

- TCS V2 feature changes are already applied.
- Logout test-harness fix is already applied.
- Full test suite passed: 6 files / 24 tests.
- Production build passed.
- TCS source-specific TypeScript gate passed.
- TCS branding gate passed.
- No migration has run yet.

## Strict rules

1. Do NOT create a branch.
2. Do NOT run `git pull`.
3. Do NOT reapply any TCS feature patch.
4. Do NOT reapply the logout test patch.
5. Do NOT apply `TCS_PHASE_1_DRIZZLE_DOTENV_FIX_V1.patch`.
6. Do NOT create `.env` and do NOT write `DATABASE_URL` to any file.
7. Never print, echo, log, upload, report, or expose the value of `DATABASE_URL`.
8. Disable shell tracing before touching process environment: `set +x`.
9. Preserve the three existing untracked `TOS_V1.15.*.zip` files exactly.
10. Before migration, generated SQL must be inspected and must contain ONLY the three new TCS tables plus their TCS indexes/foreign keys. Any unrelated/destructive SQL means STOP.
11. Never enter GitHub credentials interactively.
12. Product name is `TCS — Tamayouz Chat System`; no TACS branding.

## Step 1 — verify existing worktree

From `/var/www/TOS`:

```bash
set -euo pipefail
set +x

git branch --show-current
git rev-parse HEAD
git diff --check
git status --short
```

Required:

- branch = `main`
- HEAD = `03a61b7bc84baa8e801ec40f33d24bbaf0969894`
- existing intended changed source files remain:
  - `drizzle/schema.ts`
  - `server/routers.ts`
  - `server/tcsRouter.ts`
  - `client/src/components/TcsChat.tsx`
  - `client/src/components/DashboardLayout.tsx`
  - `server/auth.logout.test.ts`
  - `server/tos.test.ts`
- `drizzle.config.ts` must still be unchanged at this point.
- the three existing untracked ZIPs remain untouched.

If state differs materially, STOP and report exact evidence.

## Step 2 — locate the running TOS application process without guessing a service name

Do not use `env`, `printenv`, `systemctl show -p Environment`, or any command that could dump secrets.

Find Node/tsx processes whose current working directory is exactly `/var/www/TOS` and whose command line contains either `dist/index.js` or `server/_core/index.ts`:

```bash
mapfile -t TOS_PIDS < <(
  for proc in /proc/[0-9]*; do
    pid="${proc##*/}"
    cwd="$(readlink -f "$proc/cwd" 2>/dev/null || true)"
    [ "$cwd" = "/var/www/TOS" ] || continue
    cmd="$(tr '\0' ' ' < "$proc/cmdline" 2>/dev/null || true)"
    case "$cmd" in
      *dist/index.js*|*server/_core/index.ts*) printf '%s\n' "$pid" ;;
    esac
  done
)

printf 'TCS_V8_TOS_PROCESS_CANDIDATES=%s\n' "${#TOS_PIDS[@]}"
```

Required: exactly one matching application process.

If zero or more than one candidates are found, STOP and report only candidate PIDs and sanitized command names; do not print any environment values.

Set:

```bash
TOS_PID="${TOS_PIDS[0]}"
```

## Step 3 — verify and import DATABASE_URL from `/proc` without exposing it

First verify key presence only:

```bash
if tr '\0' '\n' < "/proc/$TOS_PID/environ" | grep -q '^DATABASE_URL='; then
  echo 'TCS_V8_RUNTIME_DATABASE_URL=PRESENT'
else
  echo 'TCS_V8_RUNTIME_DATABASE_URL=ABSENT'
  exit 41
fi
```

Then import the value into the current shell only. Do NOT echo it:

```bash
DATABASE_URL="$(tr '\0' '\n' < "/proc/$TOS_PID/environ" | sed -n 's/^DATABASE_URL=//p' | head -n 1)"
export DATABASE_URL
[ -n "$DATABASE_URL" ]
echo 'TCS_V8_DATABASE_URL_IMPORTED=YES'
```

Never write this variable to disk. Never include it in report output.

## Step 4 — rerun validated code gates

```bash
pnpm test
pnpm build
```

Required:

- all tests PASS
- build PASS

Run the same TCS source-specific TypeScript gate used successfully in V6/V7. It must report zero errors from:

- `server/tcsRouter.ts`
- `client/src/components/TcsChat.tsx`
- TCS additions in `drizzle/schema.ts`
- TCS registration in `server/routers.ts`
- TCS layout integration

Also verify branding:

```bash
if grep -RIn --exclude-dir=node_modules --exclude-dir=.git --exclude='*.zip' 'TACS' \
  server/tcsRouter.ts client/src/components/TcsChat.tsx client/src/components/DashboardLayout.tsx drizzle/schema.ts; then
  echo 'TCS_V8_BRANDING=FAIL'
  exit 42
else
  echo 'TCS_V8_BRANDING=PASS'
fi
```

## Step 5 — generate migration only, then inspect it before any DB write

Capture current migration SQL list:

```bash
before_sql="$(mktemp)"
after_sql="$(mktemp)"
new_sql="$(mktemp)"
find drizzle -maxdepth 1 -type f -name '*.sql' -printf '%f\n' | sort > "$before_sql"
```

Generate only:

```bash
pnpm exec drizzle-kit generate
```

Then identify only newly generated SQL files:

```bash
find drizzle -maxdepth 1 -type f -name '*.sql' -printf '%f\n' | sort > "$after_sql"
comm -13 "$before_sql" "$after_sql" > "$new_sql"
cat "$new_sql"
```

Required: at least one new SQL migration file.

For each new SQL file, inspect its contents. It is allowed to:

- create `tcs_conversations`
- create `tcs_conversation_members`
- create `tcs_messages`
- add indexes/unique indexes/foreign keys belonging to those TCS tables

It must NOT:

- DROP/TRUNCATE/DELETE any table/data
- ALTER/DROP/RENAME unrelated existing tables or columns
- create unrelated non-TCS tables
- modify existing AI `chat_messages`

If any SQL is unrelated or destructive: STOP BEFORE MIGRATE and report the filename and offending SQL lines only (never secrets).

Record the safe generated migration filename(s).

## Step 6 — apply migration

Only after SQL safety PASS:

```bash
pnpm exec drizzle-kit migrate
```

Required: exit code 0.

## Step 7 — verify the three tables using the imported runtime DATABASE_URL

Use mysql2 without printing the connection string:

```bash
node --input-type=module <<'NODE'
import mysql from 'mysql2/promise';
const conn = await mysql.createConnection(process.env.DATABASE_URL);
const [rows] = await conn.query(`
  SELECT TABLE_NAME
  FROM information_schema.TABLES
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME IN ('tcs_conversations','tcs_conversation_members','tcs_messages')
  ORDER BY TABLE_NAME
`);
await conn.end();
const names = rows.map(r => r.TABLE_NAME);
console.log('TCS_V8_TABLES=' + names.join(','));
if (names.length !== 3) process.exit(43);
NODE
```

Required exactly:

- `tcs_conversations`
- `tcs_conversation_members`
- `tcs_messages`

## Step 8 — functional validation

Use two existing real TOS users. Do not create fake production accounts unless the environment already has a documented disposable QA account.

Validate:

1. User A can open TCS.
2. User A can find User B.
3. User A can create/open the direct conversation.
4. User A can send a text message.
5. User B sees unread count > 0.
6. User B can read and mark the conversation read; unread clears.
7. User B replies.
8. User A receives the reply through TCS refresh/polling without full TOS page reload.
9. Conversation history survives refresh/re-query.
10. UI displays TCS, never TACS.
11. Ramzy/AI Assistant still works.
12. Help Center still works.
13. Operational Inbox still works.
14. TWorkspace still works.

Authorization validation:

- a non-member cannot read a conversation
- a non-member cannot send into a conversation
- a user cannot start a direct conversation with themself

If browser credentials for two real users are unavailable, do NOT invent credentials. Use the existing authenticated sessions if available. If neither two authenticated sessions nor approved QA credentials are available, STOP after successful DB/table verification and report `TCS_V8_FUNCTIONAL_BLOCKER=NO_TWO_USER_AUTH_SESSION` with all prior gates preserved.

## Step 9 — final diff safety

```bash
git diff --check
git status --short
```

Expected tracked changes are limited to:

- TCS Phase 1 source files
- the two logout test harness files
- newly generated Drizzle migration metadata/SQL

`drizzle.config.ts` must NOT be changed in V8.

Do not stage the three untracked ZIPs.

## Step 10 — commit only after every gate passes

Create atomic commits on `main` only.

First test harness fix:

```bash
git add server/auth.logout.test.ts server/tos.test.ts
git commit -m "test(auth): complete logout response mocks"
TEST_FIX_SHA="$(git rev-parse HEAD)"
```

Then TCS feature + generated migration:

```bash
git add drizzle/schema.ts drizzle server/tcsRouter.ts server/routers.ts client/src/components/TcsChat.tsx client/src/components/DashboardLayout.tsx
git commit -m "feat(tcs): add phase 1 direct messaging"
TCS_SHA="$(git rev-parse HEAD)"
```

Ensure `.env`, ZIP artifacts, and unrelated files are not staged.

## Step 11 — push

Only after all gates pass:

```bash
GIT_TERMINAL_PROMPT=0 git push origin main
```

If push authentication alone fails, keep the local commits and report exact SHAs plus sanitized push error. Do not reset successful commits.

## Final report required

Return one concise ZIP/report containing:

- branch + starting HEAD
- exact pre-existing worktree state
- running TOS process detection result (PID allowed; no environment values)
- `DATABASE_URL` presence/import markers only, never value
- tests result
- build result
- TCS TypeScript gate
- branding gate
- generated migration filename(s)
- SQL safety inspection result
- migration result
- exact TCS table verification result
- two-user functional results
- authorization results
- final changed-file list
- test-fix commit SHA
- TCS commit SHA
- push result / remote SHA
- any blocker with exact sanitized evidence

Under no circumstances include `DATABASE_URL` or any secret value in the report.