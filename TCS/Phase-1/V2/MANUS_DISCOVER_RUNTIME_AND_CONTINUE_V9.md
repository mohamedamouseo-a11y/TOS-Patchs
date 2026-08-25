# TCS Phase 1 — V9 Runtime Discovery + Safe DB Continuation

Repository: `mohamedamouseo-a11y/TOS`
Branch: `main` ONLY
Pinned baseline HEAD: `03a61b7bc84baa8e801ec40f33d24bbaf0969894`

## Context

V8 stopped because its process detector required a Node process whose CWD was exactly `/var/www/TOS` and whose command line contained `dist/index.js` or `server/_core/index.ts`. Candidate count was zero.

That does NOT prove TOS is not running. TOS may be launched through systemd, PM2, Supervisor, Docker, a shell wrapper, a different working directory, or another process layout.

Previously validated state must remain intact:

- TCS V2 feature changes are already applied and must NOT be reapplied.
- Logout test-harness fix is already applied.
- Full tests previously PASS: 6 files / 24 tests.
- Production build previously PASS.
- TCS source-specific TypeScript gate previously PASS.
- TCS branding gate previously PASS.
- No TCS DB migration has run.
- No commit or push has occurred.

## Strict rules

1. Do NOT create a branch.
2. Do NOT run `git pull`.
3. Do NOT reapply any TCS feature patch.
4. Do NOT reapply the logout test patch.
5. Do NOT apply the V7 Drizzle dotenv patch.
6. Do NOT modify TCS source or unrelated production code.
7. Do NOT create `.env`.
8. Never print, echo, log, persist, upload, or include any secret value, especially `DATABASE_URL`.
9. Disable shell tracing before all runtime/environment work: `set +x`.
10. Preserve the three existing untracked `TOS_V1.15.*.zip` files exactly.
11. Before migration, generated SQL must be inspected and must contain ONLY the three new TCS tables plus TCS indexes/foreign keys. Any unrelated or destructive SQL means STOP.
12. Never enter GitHub credentials interactively.
13. Product name is `TCS — Tamayouz Chat System`; no TACS branding.

## Step 1 — verify worktree

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
- TCS source changes still present:
  - `drizzle/schema.ts`
  - `server/routers.ts`
  - `server/tcsRouter.ts`
  - `client/src/components/TcsChat.tsx`
  - `client/src/components/DashboardLayout.tsx`
- test-harness changes still present:
  - `server/auth.logout.test.ts`
  - `server/tos.test.ts`
- the 3 pre-existing ZIP files untouched

## Step 2 — discover how TOS is actually running

Discovery is READ-ONLY. Do not restart or stop anything.

Collect safe metadata only:

```bash
printf '%s\n' '=== LISTENERS ==='
ss -lntp 2>/dev/null | grep -E 'node|pm2|docker|3000|3001|3002|3003|3004|3005|3006|3007|3008|3009' || true

printf '%s\n' '=== NODE-LIKE PROCESSES ==='
ps -eo pid,ppid,user,comm,args --sort=pid | grep -E '[n]ode|[p]m2|[n]pm|[p]npm|[t]sx' || true

printf '%s\n' '=== SYSTEMD CANDIDATES ==='
systemctl list-units --type=service --state=running --no-pager 2>/dev/null | grep -Ei 'tos|tamiyouz|node|pm2' || true

printf '%s\n' '=== PM2 CANDIDATES ==='
command -v pm2 >/dev/null 2>&1 && pm2 ls || true

printf '%s\n' '=== SUPERVISOR CANDIDATES ==='
command -v supervisorctl >/dev/null 2>&1 && supervisorctl status || true

printf '%s\n' '=== DOCKER CANDIDATES ==='
command -v docker >/dev/null 2>&1 && docker ps --format '{{.ID}} {{.Names}} {{.Image}} {{.Ports}}' || true
```

Do NOT call commands that dump environment values such as `systemctl show -p Environment`, `pm2 env`, `docker inspect` environment arrays, `env`, or `printenv`.

Then identify the process/service/container that actually serves the TOS application using evidence from:

- process command/parentage
- listening port
- service name / PM2 app name / container name
- `/proc/<PID>/cwd` symlink when accessible
- Nginx/Apache reverse-proxy upstream config if needed, but only print upstream host/port and config path — never secrets

If multiple plausible TOS instances remain and cannot be safely disambiguated, STOP and report candidates instead of guessing.

## Step 3 — acquire DATABASE_URL without exposing it

Preferred method: use the confirmed live TOS process PID and `/proc/<PID>/environ`.

Do NOT print the value. Use a Python wrapper that reads the environment internally and launches child commands with that environment inherited.

Create a TEMPORARY helper outside the repo, e.g. `/tmp/tcs-v9-with-runtime-db.py`, with permissions 700. The helper must:

1. accept the confirmed PID and a command argv after `--`;
2. read `/proc/<PID>/environ` as bytes;
3. parse NUL-separated entries;
4. confirm a non-empty `DATABASE_URL` exists;
5. never print its value;
6. copy the current shell environment, inject only the runtime `DATABASE_URL`, and execute the requested command via `subprocess.run`;
7. print only safe status such as `DATABASE_URL_PRESENT=YES` and child return code;
8. delete itself after the workflow.

If the confirmed TOS service/container does not expose a readable host PID environment, use its manager-specific secret source ONLY if you can read it internally without printing the value and inject it directly into a child command. Never persist the secret to a file.

If DATABASE_URL still cannot be safely obtained, STOP with runtime-discovery evidence.

## Step 4 — rerun validation gates

From `/var/www/TOS`:

```bash
pnpm test
pnpm build
```

Both must PASS.

Run the previously established TCS-specific TypeScript gate. Existing unrelated baseline TypeScript debt is allowed only if TCS introduces ZERO new semantic errors.

Branding gate:

```bash
grep -RIn --exclude-dir=node_modules --exclude-dir=.git 'TACS' client/src/components/TcsChat.tsx server/tcsRouter.ts drizzle/schema.ts server/routers.ts || true
```

No TACS branding may be present in new TCS source.

## Step 5 — generate migration without applying it

Use the secure runtime-DB wrapper so `DATABASE_URL` is present to Drizzle without being printed.

Before generation, record the current migration directory listing and git status.

Run:

```bash
/tmp/tcs-v9-with-runtime-db.py <PID> -- pnpm exec drizzle-kit generate
```

Do NOT run `pnpm db:push` because that combines generate + migrate.

Identify ONLY newly generated migration files.

## Step 6 — inspect generated SQL before DB write

Read the newly generated SQL.

Allowed schema targets only:

- `tcs_conversations`
- `tcs_conversation_members`
- `tcs_messages`
- their TCS indexes / foreign keys

STOP immediately if SQL contains any of these against unrelated tables:

- DROP TABLE
- DROP COLUMN
- RENAME unrelated table/column
- ALTER unrelated existing table
- TRUNCATE
- DELETE/UPDATE data
- CREATE or ALTER any unrelated table

Foreign keys from TCS tables to existing `users` are allowed.

Record a sanitized summary of the generated SQL without any DB credentials.

## Step 7 — apply migration

Only after SQL safety PASS:

```bash
/tmp/tcs-v9-with-runtime-db.py <PID> -- pnpm exec drizzle-kit migrate
```

Then verify the three TCS tables exist using a temporary Python/Node script that reads `DATABASE_URL` internally from `/proc/<PID>/environ`, connects to MySQL, and prints ONLY table names/existence booleans — never credentials or connection strings.

Required:

```text
tcs_conversations=YES
tcs_conversation_members=YES
tcs_messages=YES
```

Delete all temporary helpers afterward.

## Step 8 — functional and authorization tests

Complete the previously required real two-user smoke test:

1. User A opens TCS.
2. User A finds User B.
3. User A opens/creates direct chat.
4. User A sends a text message.
5. User B sees conversation + unread badge.
6. User B opens it; unread clears.
7. User B replies.
8. User A receives reply via polling without full reload.
9. Refresh both browsers; history persists.
10. UI says TCS, never TACS.
11. Ramzy / AI Assistant still works.
12. Help Center assistant still works.
13. Operational Inbox still works.
14. TWorkspace still works.

Authorization tests:

- non-member cannot read another conversation
- non-member cannot send to another conversation
- user cannot start direct chat with self

All must PASS.

## Step 9 — commits

Only after every gate passes.

Keep commits atomic.

First commit the logout test harness fix only:

```bash
git add server/auth.logout.test.ts server/tos.test.ts
git commit -m "test(auth): align logout response mocks"
```

Then commit TCS feature + generated migration files only:

```bash
git add drizzle/schema.ts drizzle server/tcsRouter.ts server/routers.ts client/src/components/TcsChat.tsx client/src/components/DashboardLayout.tsx
git commit -m "feat(tcs): add phase 1 direct messaging"
```

Before each commit inspect staged files. Do NOT add the three ZIPs, `.env`, temporary helpers, reports, or unrelated files.

## Step 10 — push

Only after all gates PASS:

```bash
GIT_TERMINAL_PROMPT=0 git push origin main
```

If push auth fails, keep successful local commits and report exact safe error + local SHAs. Do not enter credentials interactively.

## Final report required

Return `TCS_PHASE1_V9_REPORT.zip` containing a concise Markdown report with:

- starting branch/HEAD
- worktree integrity
- runtime discovery evidence: manager type, service/app/container name, PID, cwd/port if safe
- DATABASE_URL presence: YES/NO only; never value
- tests result
- build result
- TCS semantic typecheck result
- branding result
- generated migration filename(s)
- migration SQL safety result and table-only summary
- migration result
- three-table verification
- two-user functional test result
- authorization result
- logout test-fix commit SHA
- TCS commit SHA
- push result / remote SHA
- exact committed files
- blocker evidence if stopped
- confirmation secrets were never printed/persisted

If any required gate fails: DO NOT PUSH.