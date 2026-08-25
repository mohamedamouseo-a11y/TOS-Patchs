# TCS Phase 1 — Push + Frontend Deploy V11

Repository: `mohamedamouseo-a11y/TOS`
Branch: `main` ONLY
Expected local HEAD: `ecc88cb10c4741437f65f0788888bd9fcc9c5de0`
Expected parent: `03a61b7bc84baa8e801ec40f33d24bbaf0969894`

## Context

V10 is code-complete and validated. The failed root-stack TCS attempt was removed, the canonical production chat architecture was verified, the approved production branding patch was applied only to `frontend/src/i18n/translations.js`, live preflight passed, frontend build passed, backend syntax checks passed, and the local commit exists.

V10 stopped ONLY because the production repository HTTPS remote had no non-interactive Git credential helper configured:

`fatal: could not read Username for 'https://github.com': terminal prompts disabled`

No source code changes are needed in V11.

## Strict rules

1. Do NOT create a branch.
2. Do NOT rewrite, amend, squash, cherry-pick, or recreate the validated local commit.
3. Do NOT modify any source file.
4. Do NOT run any database migration.
5. Do NOT restart the backend PM2 app `tamiyouz-system`.
6. Preserve the three existing untracked `TOS_V1.15.*.zip` files exactly.
7. Never print, echo, upload, or include any GitHub token, credential, SSH private key, or secret in evidence.
8. Never enter credentials interactively.
9. Only deploy after a successful push of the validated local commit.
10. Product name is `TCS — Tamayouz Chat System`.

## Step 1 — verify immutable local state

From `/var/www/TOS`:

```bash
set -euo pipefail
cd /var/www/TOS

test "$(git branch --show-current)" = "main"
test "$(git rev-parse HEAD)" = "ecc88cb10c4741437f65f0788888bd9fcc9c5de0"
test "$(git rev-parse HEAD^)" = "03a61b7bc84baa8e801ec40f33d24bbaf0969894"
git diff --quiet
git diff --cached --quiet
git diff-tree --no-commit-id --name-only -r HEAD | grep -Fx 'frontend/src/i18n/translations.js'
test "$(git diff-tree --no-commit-id --name-only -r HEAD | wc -l)" -eq 1
```

Verify the only untracked production artifacts remain the same three tolerated ZIP files. If tracked state differs, STOP.

## Step 2 — re-run fast validation

```bash
./scripts/tos-production-preflight.sh --live
cd /var/www/TOS/frontend
npm run build
cd /var/www/TOS
node --check backend/src/server.js
node --check backend/src/app.js
node --check backend/src/routes/chat.routes.js
```

All must pass.

## Step 3 — establish NON-INTERACTIVE GitHub authentication

Disable command tracing before auth discovery:

```bash
set +x
```

Try methods in this order. Do not expose credentials.

### Method A — existing GitHub CLI auth

If `gh` exists:

```bash
if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
  gh auth setup-git >/dev/null 2>&1
  GIT_TERMINAL_PROMPT=0 git push origin main
fi
```

If push succeeds, go to Step 4.

### Method B — existing SSH GitHub auth

If Method A did not push successfully, test SSH without prompts:

```bash
if ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new -T git@github.com </dev/null 2>&1 | grep -qi 'successfully authenticated'; then
  GIT_TERMINAL_PROMPT=0 git -c remote.origin.pushurl=git@github.com:mohamedamouseo-a11y/TOS.git push origin main
fi
```

Do not permanently change the configured remote URL.

### If neither method works

STOP. Do not deploy. Report only which non-secret auth methods were available/unavailable and the sanitized push errors. Keep local commit intact.

## Step 4 — verify remote main contains the exact validated commit

After push:

```bash
REMOTE_SHA="$(git ls-remote origin refs/heads/main | awk '{print $1}')"
test "$REMOTE_SHA" = "ecc88cb10c4741437f65f0788888bd9fcc9c5de0"
echo "V11_REMOTE_SHA=$REMOTE_SHA"
```

If remote SHA differs, STOP and do not deploy.

## Step 5 — frontend-only production deployment

Run ONLY the canonical deploy script:

```bash
cd /var/www/TOS
./scripts/tos-production-deploy.sh --scope frontend
```

Required:

- frontend build succeeds
- frontend published build updates successfully
- PM2 app `tamiyouz-frontend` is online
- live preflight passes after deployment
- backend PM2 app `tamiyouz-system` remains running and is NOT restarted

Capture backend PID before and after deployment and require it to remain identical.

## Step 6 — live branding verification

Verify the deployed frontend source/build represents:

- nav label: `TCS`
- chat subtitle/branding: `TCS — Tamayouz Chat System`
- no added `TACS` branding

Do not rely only on source grep; confirm the live browser/UI if available.

## Step 7 — two-user direct-chat smoke test

Using two existing authorized staff users A and B, do not create test accounts.

Required:

1. A opens TCS.
2. A opens or starts a direct conversation with B.
3. A sends one clearly identifiable V11 smoke message.
4. B receives it without full-page refresh/relogin.
5. B unread state/badge reflects the new message.
6. B opens the conversation and unread clears.
7. B replies.
8. A receives the reply without full-page refresh/relogin.
9. Refresh both users and confirm conversation history persists.
10. Confirm existing group/channel chat surface still loads.
11. Confirm TCS branding is visible.

If safe cleanup tooling exists for smoke messages, remove only the two V11 smoke messages after evidence is recorded. Otherwise leave them and identify them in the report.

## Step 8 — final report

Return `TCS_PHASE1_PRODUCTION_V11_REPORT.zip` containing a Markdown report and safe evidence.

Report exactly:

- starting branch and local SHA
- immutable one-file commit scope verification
- tolerated ZIP preservation
- preflight result
- frontend build result
- backend syntax result
- auth method used (`GH_CLI`, `SSH`, or `NONE`) WITHOUT secrets
- push result and sanitized error if any
- remote main SHA
- frontend deploy result
- frontend PM2 status
- backend PID before/after and explicit confirmation no backend restart
- live TCS branding verification
- two-user direct-chat smoke results item by item
- history persistence result
- group/channel load result
- database migration = NOT RUN
- database modification = NONE
- exact blockers if any

Phase 1 is COMPLETE only if push, frontend deployment, branding verification, and the full two-user smoke test all PASS.