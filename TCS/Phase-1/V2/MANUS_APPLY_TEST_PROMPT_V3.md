# TCS Phase 1 — Apply & Test V3 (VALID PATCH SET)

Repository: `mohamedamouseo-a11y/TOS`
Branch: `main` ONLY
Required baseline HEAD: `03a61b7bc84baa8e801ec40f33d24bbaf0969894`

The previous V1 patch was malformed (`patch with only garbage at line 4`). DO NOT use any legacy TACS patch or the old branding correction patch. Use ONLY the V2 patch set below.

## Strict rules

1. Do NOT create a branch.
2. Do NOT write or redesign code yourself.
3. Do NOT edit unrelated files.
4. Do NOT run `git pull`; ChatGPT verified the required baseline is still current `TOS/main`.
5. Preserve the three existing untracked production ZIPs exactly; do not move/delete/stash/add them.
6. Pre-check ALL four V2 patches before applying ANY patch.
7. If any patch pre-check fails, STOP with evidence and apply nothing.
8. Run typecheck/build before database migration.
9. If any validation fails, DO NOT push.
10. User-facing/internal new module naming is TCS/tcs. No new TACS naming is allowed.
11. Never enter GitHub credentials interactively.

## Step 1 — baseline

From `/var/www/TOS`:

```bash
set -euo pipefail

git branch --show-current
git rev-parse HEAD
git diff --quiet && echo TRACKED_WORKTREE_CLEAN
git diff --cached --quiet && echo INDEX_CLEAN
git status --short
```

Required:
- branch exactly `main`
- HEAD exactly `03a61b7bc84baa8e801ec40f33d24bbaf0969894`
- tracked worktree/index clean
- only the known untracked ZIP artifacts may remain

## Step 2 — obtain approved patch set

```bash
rm -rf /tmp/TOS-Patchs-TCS-P1-V2
git clone --depth 1 https://github.com/mohamedamouseo-a11y/TOS-Patchs.git /tmp/TOS-Patchs-TCS-P1-V2
```

ONLY these four patches are approved, in this order:

1. `TCS/Phase-1/V2/TCS_PHASE_1_DB_V2.patch`
2. `TCS/Phase-1/V2/TCS_PHASE_1_SERVER_V2.patch`
3. `TCS/Phase-1/V2/TCS_PHASE_1_CLIENT_COMPONENT_V2.patch`
4. `TCS/Phase-1/V2/TCS_PHASE_1_LAYOUT_V2.patch`

## Step 3 — pre-check every patch BEFORE applying

```bash
P=/tmp/TOS-Patchs-TCS-P1-V2/TCS/Phase-1/V2

git apply --check "$P/TCS_PHASE_1_DB_V2.patch"
git apply --check "$P/TCS_PHASE_1_SERVER_V2.patch"
git apply --check "$P/TCS_PHASE_1_CLIENT_COMPONENT_V2.patch"
git apply --check "$P/TCS_PHASE_1_LAYOUT_V2.patch"

echo ALL_PATCH_PRECHECKS_PASS
```

If any command fails: STOP. Do not apply any patch.

## Step 4 — apply exact patch set

```bash
git apply "$P/TCS_PHASE_1_DB_V2.patch"
git apply "$P/TCS_PHASE_1_SERVER_V2.patch"
git apply "$P/TCS_PHASE_1_CLIENT_COMPONENT_V2.patch"
git apply "$P/TCS_PHASE_1_LAYOUT_V2.patch"

git diff --check
git status --short
```

Expected source changes:
- `drizzle/schema.ts`
- `server/tcsRouter.ts` NEW
- `server/routers.ts`
- `client/src/components/TcsChat.tsx` NEW
- `client/src/components/DashboardLayout.tsx`

Verify no new TACS naming exists:

```bash
if git diff -- drizzle/schema.ts server/tcsRouter.ts server/routers.ts client/src/components/TcsChat.tsx client/src/components/DashboardLayout.tsx | grep -n 'TACS'; then
  echo 'ERROR: TACS branding found in new diff'
  exit 1
fi
```

## Step 5 — code validation BEFORE DB migration

```bash
pnpm check
pnpm build
```

Both must pass before touching the database.

## Step 6 — database migration and verification

```bash
pnpm db:push
```

Then verify all three tables exist using the existing `DATABASE_URL` without printing credentials:

```bash
node --input-type=module <<'NODE'
import 'dotenv/config';
import mysql from 'mysql2/promise';
const db = await mysql.createConnection(process.env.DATABASE_URL);
const expected = ['tcs_conversations','tcs_conversation_members','tcs_messages'];
const [rows] = await db.query("SHOW TABLES LIKE 'tcs_%'");
const found = new Set(rows.flatMap(r => Object.values(r).map(String)));
for (const name of expected) {
  if (!found.has(name)) throw new Error(`Missing table: ${name}`);
}
console.log('TCS_TABLES_OK=' + expected.join(','));
await db.end();
NODE
```

Record any generated migration filenames.

## Step 7 — tests

```bash
pnpm test
```

Must pass.

## Step 8 — two-user functional smoke test

Use two real authenticated TOS users/sessions:

1. User A opens TCS.
2. User A can search/find User B.
3. User A creates/opens direct chat.
4. User A sends a message.
5. User B sees the conversation and unread badge.
6. User B opens it and unread clears.
7. User B replies.
8. User A receives the reply through polling without full page reload.
9. Refresh both sessions; history persists.
10. UI displays `TCS` / `Tamayouz Chat System`, never TACS.
11. Ramzy / existing AI Assistant still works.
12. Help Center assistant still works.
13. Operational Inbox still works.
14. TWorkspace still works.

Authorization checks:
- cannot read a conversation unless current user is a member
- cannot send to a conversation unless current user is a member
- cannot start direct chat with self

All checks must pass before commit/push.

## Step 9 — commit and push

```bash
git diff --check
git add drizzle server client
git commit -m "feat(tcs): add phase 1 direct messaging"
LOCAL_SHA=$(git rev-parse HEAD)
echo "LOCAL_SHA=$LOCAL_SHA"
GIT_TERMINAL_PROMPT=0 git push origin main
```

If push succeeds, report the final remote SHA.

If push fails ONLY because GitHub authentication is unavailable:
- do not enter credentials
- do not reset the validated local commit
- create an export artifact for ChatGPT:

```bash
git format-patch -1 --stdout HEAD > /tmp/TCS_PHASE1_VALIDATED_COMMIT.patch
```

Include that `.patch` in the final report ZIP so ChatGPT can continue from the validated commit evidence.

## Final report ZIP required

Return a concise report ZIP containing:
- baseline branch/HEAD
- tracked cleanliness evidence
- confirmation the three existing ZIPs were untouched
- each of the 4 `git apply --check` results
- each apply result
- exact changed-file list
- TACS-string check result
- `pnpm check`
- `pnpm build`
- migration filename(s)
- TCS table verification
- `pnpm test`
- two-user functional test results
- authorization test results
- regression checks for Ramzy, Help Center, Operational Inbox, TWorkspace
- local commit SHA
- push result / remote SHA
- exact blocker output if any
- `/tmp/TCS_PHASE1_VALIDATED_COMMIT.patch` included if push authentication fails

If any gate fails: DO NOT PUSH.