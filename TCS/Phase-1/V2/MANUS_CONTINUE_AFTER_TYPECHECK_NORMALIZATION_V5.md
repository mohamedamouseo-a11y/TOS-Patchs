# TCS Phase 1 — Continue V5 (Stable Baseline-Delta Typecheck Gate)

Repository: `mohamedamouseo-a11y/TOS`
Branch: `main` ONLY
Pinned baseline HEAD: `03a61b7bc84baa8e801ec40f33d24bbaf0969894`

## Why V4 stopped

V4 proved the four TCS V2 patches are already applied cleanly and that the production worktree contains only the five intended TCS source changes plus the three pre-existing untracked ZIP artifacts.

The V4 delta gate reported one apparent new TypeScript error in `client/src/pages/AISettingsPage.tsx`, but the raw evidence proves this is the SAME pre-existing TS2339 error already present on the baseline. The only textual difference is TypeScript's expanded router summary changing from `... 22 more ...` on baseline to `... 23 more ...` after adding one new `tcs` router key. This is expected type-printer drift, not a new semantic error.

V5 fixes ONLY the validation normalization. Do NOT modify TCS source and do NOT repair unrelated TypeScript debt.

## Strict rules

1. Do NOT create a branch.
2. Do NOT run `git pull`.
3. Do NOT reapply TCS patches if the five expected TCS source changes are already present.
4. Do NOT write, redesign, or repair TCS code.
5. Do NOT repair unrelated baseline TypeScript errors.
6. Preserve the three existing untracked production ZIP files exactly.
7. Database changes remain forbidden until the corrected TypeScript delta gate, build, and tests pass.
8. Never enter GitHub credentials interactively.
9. Product name is `TCS — Tamayouz Chat System`; no TACS branding may be introduced.
10. Push to `main` only after all required V5 gates pass.

## Step 1 — verify current production state

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
- expected TCS source diff only:
  - `drizzle/schema.ts`
  - `server/routers.ts`
  - `server/tcsRouter.ts`
  - `client/src/components/TcsChat.tsx`
  - `client/src/components/DashboardLayout.tsx`
- the three existing `TOS_V1.15.*.zip` files remain untouched

Confirm branding:

```bash
if git diff -- . ':!*.zip' | grep -n 'TACS'; then
  echo 'TCS_BRANDING_GATE=FAIL'
  exit 51
fi

echo 'TCS_BRANDING_GATE=PASS'
```

Do NOT reapply any patch if this expected source state is already present.

## Step 2 — detached clean baseline worktree

```bash
rm -rf /tmp/TOS-TCS-P1-BASELINE
git worktree add --detach /tmp/TOS-TCS-P1-BASELINE 03a61b7bc84baa8e801ec40f33d24bbaf0969894

if [ -d /var/www/TOS/node_modules ]; then
  ln -s /var/www/TOS/node_modules /tmp/TOS-TCS-P1-BASELINE/node_modules
else
  echo 'BLOCKER: production node_modules missing'
  exit 52
fi
```

Do not copy `.env`, secrets, credentials, databases, or production ZIPs into the baseline worktree.

## Step 3 — rerun baseline and patched typecheck

```bash
(
  cd /tmp/TOS-TCS-P1-BASELINE
  pnpm check > /tmp/tcs-v5-baseline-check.txt 2>&1 || true
)

(
  cd /var/www/TOS
  pnpm check > /tmp/tcs-v5-patched-check.txt 2>&1 || true
)
```

## Step 4 — stable semantic normalization

The previous normalization removed line/column positions but failed to normalize TypeScript's router summary count (`... 22 more ...` vs `... 23 more ...`). V5 MUST normalize that unstable printer text before comparison.

Run exactly:

```bash
normalize_ts_errors() {
  grep -E '^[^[:space:]].*\([0-9]+,[0-9]+\): error TS[0-9]+:' "$1" \
    | sed -E 's/\([0-9]+,[0-9]+\): /: /' \
    | sed -E 's/\.\.\. [0-9]+ more \.\.\./... N more .../g' \
    | sort -u
}

normalize_ts_errors /tmp/tcs-v5-baseline-check.txt > /tmp/tcs-v5-baseline-errors.txt || true
normalize_ts_errors /tmp/tcs-v5-patched-check.txt > /tmp/tcs-v5-patched-errors.txt || true

comm -13 /tmp/tcs-v5-baseline-errors.txt /tmp/tcs-v5-patched-errors.txt > /tmp/tcs-v5-new-errors.txt

printf '\n=== V5 BASELINE ERRORS ===\n'
cat /tmp/tcs-v5-baseline-errors.txt
printf '\n=== V5 PATCHED ERRORS ===\n'
cat /tmp/tcs-v5-patched-errors.txt
printf '\n=== V5 NEW ERRORS ===\n'
cat /tmp/tcs-v5-new-errors.txt
```

Mandatory semantic delta gate:

```bash
if [ -s /tmp/tcs-v5-new-errors.txt ]; then
  echo 'TCS_V5_DELTA_TYPECHECK=FAIL'
  exit 53
fi

echo 'TCS_V5_DELTA_TYPECHECK=PASS'
```

Expected evidence for the known AISettings baseline debt:

```bash
echo '=== BASELINE AISETTINGS ==='
grep 'AISettingsPage.tsx' /tmp/tcs-v5-baseline-errors.txt || true

echo '=== PATCHED AISETTINGS ==='
grep 'AISettingsPage.tsx' /tmp/tcs-v5-patched-errors.txt || true
```

After V5 normalization those entries must compare equal.

## Step 5 — TCS-source-specific TypeScript gate

Regardless of repository-wide legacy errors, there must be ZERO TypeScript error lines for TCS source paths:

```bash
if grep -Ei 'client/src/components/TcsChat\.tsx\([0-9]+,[0-9]+\): error TS|server/tcsRouter\.ts\([0-9]+,[0-9]+\): error TS|drizzle/schema\.ts\([0-9]+,[0-9]+\): error TS' /tmp/tcs-v5-patched-check.txt; then
  echo 'TCS_V5_SOURCE_TYPECHECK=FAIL'
  exit 54
fi

echo 'TCS_V5_SOURCE_TYPECHECK=PASS'
```

A non-zero repository-wide `pnpm check` is acceptable ONLY if both:

- `TCS_V5_DELTA_TYPECHECK=PASS`
- `TCS_V5_SOURCE_TYPECHECK=PASS`

## Step 6 — build and tests before database

From `/var/www/TOS`:

```bash
pnpm build
pnpm test
```

Both must pass. If either fails, STOP and do not touch the database.

## Step 7 — database migration

Only after build and tests pass:

```bash
pnpm db:push
```

Verify all three TCS tables exist:

- `tcs_conversations`
- `tcs_conversation_members`
- `tcs_messages`

Capture generated migration filename(s), if any. Do not hand-edit historical migrations.

## Step 8 — authenticated two-user functional test

Record PASS/FAIL with evidence for each:

1. TCS launcher renders and says TCS, never TACS.
2. User A opens TCS.
3. User A searches/finds User B.
4. User A opens/creates a direct conversation with User B.
5. User A sends a text message.
6. User B sees the conversation and unread badge.
7. User B opens it and unread clears.
8. User B replies.
9. User A receives the reply through polling without a full page reload.
10. Refresh both sessions and confirm history persists.
11. Ramzy / existing AI assistant still works.
12. Help Center assistant still works.
13. Operational Inbox still works.
14. TWorkspace still works.

Authorization checks:

- non-member cannot read another conversation
- non-member cannot send to another conversation
- user cannot start direct chat with their own user ID

If any functional or authorization check fails, STOP and do not commit/push.

## Step 9 — final source safety

```bash
git diff --check
git status --short

if git diff -- . ':!*.zip' | grep -n 'TACS'; then
  echo 'FINAL_TCS_BRANDING_GATE=FAIL'
  exit 55
fi

echo 'FINAL_TCS_BRANDING_GATE=PASS'
```

Confirm no unrelated tracked files were changed.

## Step 10 — commit and push

Only after all gates pass:

```bash
git add drizzle server client
git commit -m "feat(tcs): add phase 1 direct messaging"
LOCAL_SHA="$(git rev-parse HEAD)"
echo "LOCAL_SHA=$LOCAL_SHA"
GIT_TERMINAL_PROMPT=0 git push origin main
```

If push fails only because GitHub authentication is unavailable, keep the successful local commit and report the exact push error plus local SHA. Do not reset and do not enter credentials interactively.

## Cleanup

```bash
git worktree remove --force /tmp/TOS-TCS-P1-BASELINE || true
```

Never remove or alter the production ZIP artifacts.

## Final report ZIP required in this session

Return a ZIP containing a concise Markdown report plus raw evidence files. Include:

- starting branch + HEAD
- exact source worktree state
- confirmation patches were already present and NOT reapplied
- V5 baseline raw typecheck
- V5 patched raw typecheck
- V5 normalized baseline errors
- V5 normalized patched errors
- `tcs-v5-new-errors.txt`
- explicit AISettings baseline vs patched comparison
- `TCS_V5_DELTA_TYPECHECK`
- `TCS_V5_SOURCE_TYPECHECK`
- build result
- test result
- `pnpm db:push` result
- migration filename(s)
- TCS table verification
- two-user functional matrix
- authorization matrix
- final branding/scope checks
- final local commit SHA
- push result + remote SHA if successful
- exact changed-file list
- exact blocker evidence if anything fails

If any mandatory gate fails, DO NOT PUSH.