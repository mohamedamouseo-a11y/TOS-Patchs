# TCS Phase 1 — Continue V4 (Baseline-Delta Typecheck Gate)

Repository: `mohamedamouseo-a11y/TOS`
Branch: `main` ONLY
Baseline HEAD: `03a61b7bc84baa8e801ec40f33d24bbaf0969894`

## Context

The V3 run successfully prechecked and applied all four approved TCS V2 patches. `git diff --check` passed and no new `TACS` branding was present. V3 stopped only because the repository-wide `pnpm check` returned existing TypeScript errors in unrelated legacy areas. The captured failure output contained no TypeScript error in `client/src/components/TcsChat.tsx`, `server/tcsRouter.ts`, or `drizzle/schema.ts`.

This V4 run must prove whether the TypeScript failures are baseline debt by comparing the exact baseline commit against the current patched worktree. Do not repair unrelated TypeScript debt.

## Strict rules

1. Do NOT create any Git branch.
2. Do NOT write or redesign TCS code.
3. Do NOT repair unrelated legacy TypeScript errors.
4. Do NOT run `git pull`.
5. Preserve the three existing untracked ZIP files exactly.
6. Do NOT reapply patches if the expected V3 TCS diff is already present.
7. If the TCS diff is absent and tracked source is otherwise clean at the baseline HEAD, apply ONLY the four V2 patches from `TOS-Patchs/main` in the V3 order.
8. If the worktree is partial/mixed or contains unrelated tracked edits, STOP.
9. Database changes are forbidden until the baseline-delta TypeScript gate, build, and tests pass.
10. Never enter GitHub credentials interactively.

## Step 1 — production worktree state

From `/var/www/TOS`:

```bash
set -euo pipefail

git branch --show-current
git rev-parse HEAD
git status --short
git diff --check
```

Required:

- branch = `main`
- HEAD = `03a61b7bc84baa8e801ec40f33d24bbaf0969894`
- the only intended tracked/new-source changes are:
  - `drizzle/schema.ts`
  - `server/routers.ts`
  - `server/tcsRouter.ts`
  - `client/src/components/TcsChat.tsx`
  - `client/src/components/DashboardLayout.tsx`
- the three old untracked ZIPs remain untouched

Confirm no TACS branding in the TCS diff:

```bash
git diff -- . ':!*.zip' | grep -n 'TACS' && exit 41 || true
```

### If the four V2 patches are already applied

Continue directly to Step 2. Do NOT apply them again.

### If the TCS source diff is completely absent

Only if HEAD is still the pinned baseline and there are no unrelated tracked changes, clone the patch repo to `/tmp/TOS-Patchs-TCS-P1-V2` and precheck/apply ONLY these four patches in order:

1. `TCS/Phase-1/V2/TCS_PHASE_1_DB_V2.patch`
2. `TCS/Phase-1/V2/TCS_PHASE_1_SERVER_V2.patch`
3. `TCS/Phase-1/V2/TCS_PHASE_1_CLIENT_COMPONENT_V2.patch`
4. `TCS/Phase-1/V2/TCS_PHASE_1_LAYOUT_V2.patch`

Precheck all four before applying any. If any fails, STOP.

## Step 2 — create an isolated baseline worktree

This is a detached temporary worktree for comparison only. It is NOT a branch and MUST NOT modify production.

```bash
rm -rf /tmp/TOS-TCS-P1-BASELINE

git worktree add --detach /tmp/TOS-TCS-P1-BASELINE 03a61b7bc84baa8e801ec40f33d24bbaf0969894

if [ -d /var/www/TOS/node_modules ]; then
  ln -s /var/www/TOS/node_modules /tmp/TOS-TCS-P1-BASELINE/node_modules
else
  echo 'BLOCKER: production node_modules missing'
  exit 42
fi
```

Do not copy `.env`, credentials, database files, or production artifacts into the baseline worktree. Typecheck does not require database access.

## Step 3 — baseline-delta TypeScript gate

Run the same typecheck on baseline and patched source. `pnpm check` is allowed to exit non-zero because the purpose here is comparison.

```bash
(
  cd /tmp/TOS-TCS-P1-BASELINE
  pnpm check > /tmp/tcs-baseline-check.txt 2>&1 || true
)

(
  cd /var/www/TOS
  pnpm check > /tmp/tcs-patched-check.txt 2>&1 || true
)
```

Extract normalized TypeScript error signatures, intentionally removing line/column numbers because the TCS router import can shift legacy line positions:

```bash
grep -E '^[^[:space:]].*\([0-9]+,[0-9]+\): error TS[0-9]+:' /tmp/tcs-baseline-check.txt \
  | sed -E 's/\([0-9]+,[0-9]+\): /: /' \
  | sort -u > /tmp/tcs-baseline-errors.txt || true

grep -E '^[^[:space:]].*\([0-9]+,[0-9]+\): error TS[0-9]+:' /tmp/tcs-patched-check.txt \
  | sed -E 's/\([0-9]+,[0-9]+\): /: /' \
  | sort -u > /tmp/tcs-patched-errors.txt || true

comm -13 /tmp/tcs-baseline-errors.txt /tmp/tcs-patched-errors.txt > /tmp/tcs-new-errors.txt

printf '\n=== BASELINE ERRORS ===\n'
cat /tmp/tcs-baseline-errors.txt
printf '\n=== PATCHED ERRORS ===\n'
cat /tmp/tcs-patched-errors.txt
printf '\n=== NEW ERRORS INTRODUCED BY TCS ===\n'
cat /tmp/tcs-new-errors.txt
```

Mandatory gate:

```bash
if [ -s /tmp/tcs-new-errors.txt ]; then
  echo 'TCS_DELTA_TYPECHECK=FAIL'
  exit 43
fi

echo 'TCS_DELTA_TYPECHECK=PASS'
```

Also explicitly prove no TCS source path appears in TypeScript errors:

```bash
if grep -Ei 'client/src/components/TcsChat\.tsx|server/tcsRouter\.ts|drizzle/schema\.ts.*error TS' /tmp/tcs-patched-check.txt; then
  echo 'TCS_SOURCE_TYPECHECK=FAIL'
  exit 44
fi

echo 'TCS_SOURCE_TYPECHECK=PASS'
```

A non-zero repository-wide `pnpm check` is acceptable ONLY when `TCS_DELTA_TYPECHECK=PASS` and `TCS_SOURCE_TYPECHECK=PASS`. This documents pre-existing technical debt rather than hiding it.

## Step 4 — build and test before database

From `/var/www/TOS`:

```bash
pnpm build
pnpm test
```

Both must pass. If either fails, STOP. Do not touch the database.

## Step 5 — database migration

Only after Step 4 passes:

```bash
pnpm db:push
```

Verify the three TCS tables exist:

- `tcs_conversations`
- `tcs_conversation_members`
- `tcs_messages`

Capture generated migration filename(s), if any. Do not hand-edit historical migrations.

## Step 6 — functional smoke test with two real TOS users

Perform and record PASS/FAIL for each:

1. TCS launcher renders and says TCS, never TACS.
2. User A opens TCS.
3. User A can search/find User B.
4. User A starts a direct conversation with User B.
5. User A sends a text message.
6. User B gets the conversation/unread badge.
7. User B opens it and unread clears.
8. User B replies.
9. User A receives the reply through polling without full-page reload.
10. Refresh both sessions and confirm message history persists.
11. Ramzy / existing AI assistant still works.
12. Help Center assistant still works.
13. Operational Inbox still works.
14. TWorkspace still works.

Authorization checks:

- a non-member cannot read another conversation
- a non-member cannot send to another conversation
- a user cannot open a direct chat with their own user ID

If any functional or authorization gate fails, STOP and do not push.

## Step 7 — final source safety check

```bash
git diff --check
git status --short
git diff -- . ':!*.zip' | grep -n 'TACS' && exit 45 || true
```

Ensure no unrelated tracked file was edited.

## Step 8 — commit and push

Only after all V4 gates pass:

```bash
git add drizzle server client
git commit -m "feat(tcs): add phase 1 direct messaging"
LOCAL_SHA="$(git rev-parse HEAD)"
echo "LOCAL_SHA=$LOCAL_SHA"
GIT_TERMINAL_PROMPT=0 git push origin main
```

If push fails only due missing GitHub authentication, keep the successful local commit and report the exact push error. Do not reset it and do not enter credentials interactively.

## Cleanup

After evidence is captured:

```bash
git worktree remove --force /tmp/TOS-TCS-P1-BASELINE || true
```

Do not delete or alter production ZIP artifacts.

## Final report required in this session

Return a ZIP containing one concise Markdown report plus raw evidence files. Include:

- starting branch + HEAD
- production worktree state
- whether patches were already present or reapplied
- baseline `pnpm check` output
- patched `pnpm check` output
- normalized baseline errors
- normalized patched errors
- `tcs-new-errors.txt`
- `TCS_DELTA_TYPECHECK` result
- `TCS_SOURCE_TYPECHECK` result
- `pnpm build` result
- `pnpm test` result
- `pnpm db:push` result
- migration filename(s)
- TCS table verification
- two-user functional test matrix
- authorization test matrix
- final changed-file list
- local commit SHA
- push result / remote SHA
- exact blocker evidence if anything fails

Do NOT push if any TCS-specific delta, build, test, migration, functional, authorization, or branding gate fails.