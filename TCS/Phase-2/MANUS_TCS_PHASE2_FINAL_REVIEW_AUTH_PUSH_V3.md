# TCS Phase 2 — Final Review Fix + Persistent Push Auth V3

Repository: `mohamedamouseo-a11y/TOS`
Branch: `main` ONLY
Product: `TCS — Tamayouz Chat System`

## Reviewed continuation state

The production server currently has two validated local commits that MUST be preserved exactly:

1. Phase 2 implementation:
   `860e2f25621f3eb6ab5fa39bc7a96737743df3bd`
2. Exact-scope stale-unread reconciliation fix:
   `321784f9b54a3dd27f7d8f352659a0a3db47e56a`

Expected local HEAD at start:
`321784f9b54a3dd27f7d8f352659a0a3db47e56a`

Expected remote `TOS/main` before push:
`ecc88cb10c4741437f65f0788888bd9fcc9c5de0`

Do NOT amend, squash, recreate, reset, cherry-pick, or discard either local commit.

## Operating model

Manus writes the code, tests it, commits it, pushes from the TOS production server to `TOS/main`, and deploys it. ChatGPT will review GitHub after the push.

## Hard rules

1. NO new branch.
2. Work on `main` only.
3. Canonical production stack only: `frontend/` + `backend/`.
4. Never touch obsolete root `client/`, root `server/`, `drizzle/`, or `drizzle.config.ts`.
5. No Prisma migration and no new database table.
6. Never print/expose/save GitHub tokens, passwords, private keys, cookies, session IDs, or DATABASE_URL.
7. No force push.
8. Preserve the three tolerated pre-existing untracked `TOS_V1.15.*.zip` files.
9. Product naming remains TCS only; no TACS.
10. Do not weaken auth, CSRF, project/channel/conversation access, or chat authorization.

---

# STEP 1 — Verify immutable starting state

From `/var/www/TOS`:

- branch must be `main`
- HEAD must be `321784f9b54a3dd27f7d8f352659a0a3db47e56a`
- HEAD^ must be `860e2f25621f3eb6ab5fa39bc7a96737743df3bd`
- HEAD^^ must be `ecc88cb10c4741437f65f0788888bd9fcc9c5de0`
- tracked worktree/index must be clean
- remote `main` must still equal `ecc88cb10c4741437f65f0788888bd9fcc9c5de0`

If remote has moved, STOP and report the remote SHA. Do not rebase or merge automatically.

---

# STEP 2 — Final frontend review fix (third commit)

ChatGPT reviewed the Phase 2 global hook and found two remaining frontend lifecycle issues in `frontend/src/hooks/useGlobalTcsUnread.js`.

## A. Prevent stale toast from reappearing

Current behavior can retain `alert` while `activePage === "chat"`. If the user enters TCS using the Sidebar instead of the toast button, the toast is merely hidden by the App render condition. When the user later leaves TCS, that old alert can reappear.

Fix requirements:

- When `activePage` becomes `"chat"`, clear the global TCS alert state immediately.
- When a `messages:read` socket event belongs to the current user, clear the alert and schedule an unread hydrate.
- Do not clear or mark unrelated server notifications as read just to hide the toast.
- Keep the Sidebar badge server-reconciled through the existing unread hydrate.

## B. Rehydrate after socket reconnect / browser resume

The global unread layer must recover notifications missed while the socket/browser was disconnected or suspended.

Fix requirements:

- Listen for Socket.IO `connect` on the same singleton socket and call the existing debounced hydrate.
- Remove that listener during effect cleanup.
- Add a lightweight browser visibility recovery: when `document.visibilityState` becomes `visible`, schedule hydrate.
- Remove the visibility listener during cleanup.
- Do not create another socket instance.
- Do not poll continuously.

Keep all existing duplicate-notification guards and state-sync behavior.

## Third commit

Make only the minimum code changes needed for these reviewed lifecycle fixes. Prefer changing only:

`frontend/src/hooks/useGlobalTcsUnread.js`

If you add any deterministic helper/test, keep it narrowly scoped and explain why.

Commit separately as:

`fix(tcs): harden global unread lifecycle`

Do NOT amend the first two commits.

---

# STEP 3 — Validate all three commits together

Required gates:

- `git diff --check`
- no `TACS` under `frontend/src` or `backend/src`
- `node --check backend/src/routes/chat.routes.js`
- `node --check backend/src/services/chatUnreadScope.js`
- run `backend/src/services/chatUnreadScope.test.js` and require all tests PASS
- backend Prisma validation PASS
- canonical frontend `npm run build` PASS
- production preflight PASS before push
- no Prisma schema/migration change

Also inspect the full combined diff from remote base `ecc88cb...` to local HEAD and verify Phase 2 tracked scope is only intentional production TCS files.

---

# STEP 4 — Recover non-interactive GitHub authentication safely

V11 previously pushed successfully using a GitHub CLI authentication path, but the latest session reported `gh` absent and SSH unauthorized. Do a more complete SAFE credential discovery before declaring auth unavailable.

Disable shell tracing:

`set +x`

Never print secret values.

Try these methods in order:

## Method A — existing GH CLI anywhere on server

Check PATH plus common safe executable locations such as:

- `/usr/bin/gh`
- `/usr/local/bin/gh`
- `/snap/bin/gh`
- `$HOME/.local/bin/gh`
- shallow executable search under `/opt`, `$HOME/.local`, and `/home/*/.local`

If an executable `gh` is found and `gh auth status` succeeds, run `gh auth setup-git` and push non-interactively.

Do not display `gh auth token`.

## Method B — existing environment token WITHOUT printing it

Check only whether these variable NAMES contain a non-empty value:

- `GH_TOKEN`
- `GITHUB_TOKEN`

Do not echo the values.

If one exists, use a temporary `GIT_ASKPASS` helper that reads the token from the environment at runtime. The helper file must contain no literal token. It should return `x-access-token` for the username request and the environment token for the password request.

Use it only for:

`GIT_TERMINAL_PROMPT=0 git push origin main`

Then securely remove the temporary helper.

Never put a token into the remote URL, shell command arguments, report, logs, or Git config.

## Method C — existing Git credential source

Check non-secret metadata only:

- local/global/system `credential.helper`
- existence of `$HOME/.git-credentials`
- existence of a configured `GIT_ASKPASS`

If a credential source exists, test it without printing the returned username/password. If it can satisfy GitHub credentials, use normal non-interactive `git push origin main`.

Do not copy credential contents into files or evidence.

## Method D — existing SSH / agent

Test existing SSH/ssh-agent identities in BatchMode. If GitHub confirms successful authentication, use a temporary push URL or host configuration without permanently changing the repository remote.

## If A-D all fail

Do NOT keep retrying and do NOT request interactive username/password.

Prepare a permanent repository-scoped SSH deploy key for future Manus pushes:

- create a dedicated ED25519 key only if one does not already exist at a clearly TOS-specific path such as `$HOME/.ssh/tos_main_deploy_ed25519`
- empty passphrase is allowed because this is an automation deploy key; file permissions must be strict
- DO NOT print or include the private key anywhere
- output ONLY the public key to a safe evidence file named `TOS_MAIN_DEPLOY_KEY_PUBLIC.txt`
- do NOT alter `origin` yet
- STOP before push/deploy and return the report + public key so the owner can add it to GitHub as a write-enabled Deploy Key once

This deploy-key fallback is preferred over repeatedly failing authentication in future phases.

---

# STEP 5 — Push

Only after all validation passes and a non-interactive authenticated method is available:

- verify remote `main` is still `ecc88cb10c4741437f65f0788888bd9fcc9c5de0`
- push the three local Phase 2 commits to `TOS/main`
- no force push
- verify remote SHA equals the new local HEAD

Record all three SHAs in order:

1. `860e2f25621f3eb6ab5fa39bc7a96737743df3bd`
2. `321784f9b54a3dd27f7d8f352659a0a3db47e56a`
3. new lifecycle-fix SHA

---

# STEP 6 — Production deployment

Only after successful push and remote-SHA verification:

`cd /var/www/TOS`
`./scripts/tos-production-deploy.sh --scope both`

No migration.

Required:

- backend syntax/Prisma validation passes inside official deploy
- backend PM2 `tamiyouz-system` returns online and health endpoint passes
- frontend build/publish succeeds
- frontend PM2 `tamiyouz-frontend` online
- final live preflight PASS

---

# STEP 7 — Live Phase 2 verification

Verify at minimum:

1. TCS nav label still correct.
2. Global TCS unread badge renders in expanded Sidebar.
3. Badge renders correctly in collapsed Sidebar.
4. Mobile Sidebar receives same badge value.
5. Background TCS toast does not render while already on TCS.
6. Entering TCS via Sidebar clears any prior global toast so it does NOT reappear after leaving TCS.
7. Socket reconnect triggers unread rehydrate.
8. Returning a hidden tab to visible triggers unread rehydrate.
9. Backend `/api/chat/notifications` remains protected.
10. No TACS branding.
11. No unrelated regression in Dashboard/Tasks/TWS navigation.

If two authorized user sessions are available, also verify new-message -> background badge/toast -> open TCS -> unread clears. Do not fabricate or weaken this test if user B is unavailable.

---

# STEP 8 — Report

Return:

`TCS_PHASE2_FINAL_REVIEW_AUTH_PUSH_V3_REPORT.zip`

Include:

- starting branch/local/remote SHAs
- preservation of V1 and V2 commits
- third lifecycle-fix commit SHA and exact scope
- combined Phase 2 changed-file list
- diff/branding/syntax/Prisma/test/build/preflight results
- auth methods checked, with NO secrets
- auth method used OR `DEPLOY_KEY_REQUIRED`
- push result
- remote final SHA
- deploy result and PM2/health/preflight status
- live Phase 2 verification matrix
- two-user QA result if available
- no migration confirmation
- preserved ZIP confirmation

If deploy-key fallback is required, include `TOS_MAIN_DEPLOY_KEY_PUBLIC.txt` in the ZIP and stop safely without push/deploy.