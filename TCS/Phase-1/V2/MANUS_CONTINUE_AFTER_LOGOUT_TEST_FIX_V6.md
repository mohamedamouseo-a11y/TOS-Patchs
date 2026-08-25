# TCS Phase 1 — Continue V6 (Logout Test Harness Fix)

Repository: `mohamedamouseo-a11y/TOS`
Branch: `main` ONLY
Pinned baseline HEAD: `03a61b7bc84baa8e801ec40f33d24bbaf0969894`

## Context

V5 proved all of the following:

- The five intended TCS source changes are already present and must NOT be reapplied.
- TCS introduces zero new semantic TypeScript errors.
- TCS-source-specific TypeScript gate passes.
- Production build passes.
- Full test suite has only two failures, both in pre-existing `auth.logout` tests.
- The failure is `ctx.res.append is not a function` because the test response mocks implement `clearCookie` but not Express `res.append`, while the baseline production logout implementation already calls `res.append` for TWorkspace cookie cleanup.

ChatGPT authored a test-only harness patch. Apply that patch only. Do not modify production logout behavior and do not rewrite TCS.

Patch repository: `mohamedamouseo-a11y/TOS-Patchs`
Patch path: `TCS/Phase-1/V2/TCS_PHASE_1_AUTH_LOGOUT_TEST_HARNESS_FIX_V1.patch`

## Strict rules

1. Do NOT create a branch.
2. Do NOT run `git pull`.
3. Do NOT reapply any TCS V2 source patch.
4. Do NOT modify TCS source manually.
5. Do NOT modify production logout code.
6. Apply only the supplied test-harness patch.
7. Preserve the three existing untracked production ZIPs exactly.
8. If the test patch pre-check fails, STOP with evidence.
9. If tests still fail after the test patch, STOP and report exact failures; do not invent fixes.
10. Never enter GitHub credentials interactively.
11. Product name is `TCS — Tamayouz Chat System`; no TACS branding.

## Step 1 — verify current state

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
- existing TCS changes remain exactly:
  - `drizzle/schema.ts`
  - `server/routers.ts`
  - `server/tcsRouter.ts`
  - `client/src/components/TcsChat.tsx`
  - `client/src/components/DashboardLayout.tsx`
- three existing `TOS_V1.15.*.zip` files remain untouched

Do NOT reapply the TCS source patches.

## Step 2 — obtain and pre-check the test harness patch

Use the public patch repository outside production:

```bash
rm -rf /tmp/TOS-Patchs-TCS-P1-V6
git clone --depth 1 https://github.com/mohamedamouseo-a11y/TOS-Patchs.git /tmp/TOS-Patchs-TCS-P1-V6

TEST_PATCH=/tmp/TOS-Patchs-TCS-P1-V6/TCS/Phase-1/V2/TCS_PHASE_1_AUTH_LOGOUT_TEST_HARNESS_FIX_V1.patch

git apply --check "$TEST_PATCH"
```

If the check fails, STOP and report the exact hunk/file error.

## Step 3 — apply test harness patch only

```bash
git apply "$TEST_PATCH"
git diff --check
git status --short
```

The ONLY newly modified files beyond the already-present five TCS source files must be:

- `server/auth.logout.test.ts`
- `server/tos.test.ts`

The test patch must only add `append: () => {}` to the authenticated response mocks. No production source behavior may change.

## Step 4 — full tests

```bash
pnpm test 2>&1 | tee /tmp/tcs-v6-test.txt
```

Required: all test files and all tests PASS.

If any test still fails, STOP. Do not touch the database and do not write a new fix.

## Step 5 — build + TCS regression checks

```bash
pnpm build 2>&1 | tee /tmp/tcs-v6-build.txt
pnpm check > /tmp/tcs-v6-check.txt 2>&1 || true
```

The repository-wide TypeScript command may retain the same legacy baseline debt established in V5. However these files must have ZERO TypeScript error lines:

```bash
if grep -Ei 'client/src/components/TcsChat\.tsx\([0-9]+,[0-9]+\): error TS|server/tcsRouter\.ts\([0-9]+,[0-9]+\): error TS|server/auth\.logout\.test\.ts\([0-9]+,[0-9]+\): error TS|server/tos\.test\.ts\([0-9]+,[0-9]+\): error TS' /tmp/tcs-v6-check.txt; then
  echo 'TCS_V6_SOURCE_TYPECHECK=FAIL'
  exit 61
fi

echo 'TCS_V6_SOURCE_TYPECHECK=PASS'
```

Also confirm branding:

```bash
if git diff -- . ':!*.zip' | grep -n 'TACS'; then
  echo 'TCS_V6_BRANDING=FAIL'
  exit 62
fi

echo 'TCS_V6_BRANDING=PASS'
```

## Step 6 — database migration

Only after tests + build + source-specific typecheck gates pass:

```bash
pnpm db:push 2>&1 | tee /tmp/tcs-v6-db-push.txt
```

Verify these tables exist:

- `tcs_conversations`
- `tcs_conversation_members`
- `tcs_messages`

Capture generated migration filename(s), if any. Do not hand-edit historical migrations.

## Step 7 — two-user functional validation

Test with two real authenticated TOS users and record PASS/FAIL evidence:

1. TCS launcher renders and says TCS, never TACS.
2. User A opens TCS.
3. User A searches/finds User B.
4. User A opens/creates direct conversation with User B.
5. User A sends text message.
6. User B sees conversation + unread badge.
7. User B opens it; unread clears.
8. User B replies.
9. User A receives reply through polling without full page reload.
10. Refresh both sessions; history persists.
11. Ramzy / existing AI assistant still works.
12. Help Center assistant still works.
13. Operational Inbox still works.
14. TWorkspace still works.

Authorization checks:

- non-member cannot read another conversation
- non-member cannot send to another conversation
- user cannot start direct chat with their own user ID

Any failure = STOP; do not commit/push.

## Step 8 — final source safety

```bash
git diff --check
git status --short
```

Expected tracked scope before commits:

TCS feature:
- `drizzle/schema.ts`
- `server/routers.ts`
- `server/tcsRouter.ts`
- `client/src/components/TcsChat.tsx`
- `client/src/components/DashboardLayout.tsx`
- newly generated Drizzle migration files, if any

Test harness fix:
- `server/auth.logout.test.ts`
- `server/tos.test.ts`

No other tracked files may be changed.

## Step 9 — commit in two atomic commits, then push once

Only after every gate passes:

```bash
# Commit the independent baseline test-harness repair first.
git add server/auth.logout.test.ts server/tos.test.ts
git commit -m "test(auth): support response append in logout mocks"
TEST_FIX_SHA="$(git rev-parse HEAD)"

# Commit TCS Phase 1 source + generated migration files.
git add drizzle server/tcsRouter.ts server/routers.ts client/src/components/TcsChat.tsx client/src/components/DashboardLayout.tsx
git commit -m "feat(tcs): add phase 1 direct messaging"
TCS_SHA="$(git rev-parse HEAD)"

printf 'TEST_FIX_SHA=%s\n' "$TEST_FIX_SHA"
printf 'TCS_SHA=%s\n' "$TCS_SHA"

GIT_TERMINAL_PROMPT=0 git push origin main
```

If push fails only due authentication, keep both local commits and report exact error + both SHAs. Do not reset and do not enter credentials interactively.

## Final report ZIP required

Return a ZIP containing a concise Markdown report plus evidence for:

- starting branch + HEAD
- pre-existing TCS source state
- test harness patch `git apply --check` result
- test harness patch apply result
- exact changed-file scope
- full `pnpm test` result
- `pnpm build` result
- TCS V6 source-specific typecheck result
- branding gate
- `pnpm db:push` result
- generated migration filename(s)
- TCS table verification
- two-user functional matrix
- authorization matrix
- test-fix commit SHA
- TCS commit SHA
- push result + remote SHA
- confirmation the three production ZIPs remained untouched
