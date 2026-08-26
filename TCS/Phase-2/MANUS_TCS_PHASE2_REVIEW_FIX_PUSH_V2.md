# TCS Phase 2 — Review Fix + Push V2

Repository: `mohamedamouseo-a11y/TOS`
Branch: `main` ONLY
Canonical production stack: `frontend/` + `backend/`
Product: `TCS — Tamayouz Chat System`

## Context

Phase 2 V1 was implemented by Manus and committed locally on the TOS production host.

Validated local commit:
`860e2f25621f3eb6ab5fa39bc7a96737743df3bd`

Its parent and current remote `TOS/main` are both:
`ecc88cb10c4741437f65f0788888bd9fcc9c5de0`

V1 build/syntax/Prisma/preflight gates passed, but push failed because the current execution environment did not find a usable non-interactive GitHub auth path. Do NOT discard or recreate the V1 commit.

ChatGPT review found one semantic defect that MUST be fixed before push:

- Global TCS unread is now sourced from unread `ChatNotification` rows.
- The V1 change in `POST /api/chat/messages/read` marks notifications read only when their `messageId` is in `recentMessages`, which is capped at 100.
- If a user has more than 100 unread messages/notifications in the same TCS target, `ChatReadState.lastReadAt` can clear the chat target while older unread `ChatNotification` rows remain unread, leaving a stale global TCS badge.

## Operating model

Manus owns implementation, testing, commit, push from the TOS server, production deployment, and the final evidence report. ChatGPT will review the pushed GitHub commits afterward.

## Hard rules

1. Do NOT create a branch.
2. Work on `main` only.
3. Do NOT reset, amend, squash, recreate, or discard local commit `860e2f25621f3eb6ab5fa39bc7a96737743df3bd`.
4. Make the review correction as a NEW second commit on top of V1.
5. Do NOT touch obsolete root `client/`, root `server/`, `drizzle/`, or `drizzle.config.ts`.
6. Do NOT create new chat tables and do NOT run a Prisma migration.
7. Preserve unrelated source and tolerated pre-existing ZIP artifacts.
8. Do NOT introduce `TACS`; product naming is TCS only.
9. Never expose credentials, GitHub tokens, cookies, session IDs, SSH private keys, or `DATABASE_URL`.
10. Do not weaken auth, CSRF, conversation membership, project/channel access, or permissions.

## Step 1 — verify exact continuation state

From `/var/www/TOS` verify:

- branch = `main`
- HEAD = `860e2f25621f3eb6ab5fa39bc7a96737743df3bd`
- HEAD parent = `ecc88cb10c4741437f65f0788888bd9fcc9c5de0`
- tracked worktree/index clean before the review fix
- the V1 commit contains exactly the intended Phase 2 files:
  - `backend/src/routes/chat.routes.js`
  - `frontend/src/App.jsx`
  - `frontend/src/components/layout/Sidebar.jsx`
  - `frontend/src/hooks/useGlobalTcsUnread.js`

Fetch/inspect remote non-interactively and require remote `main` to still be `ecc88cb10c4741437f65f0788888bd9fcc9c5de0`. If remote moved, STOP and report; do not force-push and do not rebase automatically.

## Step 2 — fix the reviewed stale-unread defect

Manus must write the correction.

In the authorized `POST /api/chat/messages/read` flow, when a target is marked read:

- keep the existing `ChatReadState`, `MessageRead`, `MessageDelivery`, and `messages:read` behavior.
- do NOT decide which `ChatNotification` rows to mark read from the capped `recentMessages` array.
- mark unread `ChatNotification` rows for the CURRENT USER and the EXACT CURRENT CHAT TARGET/SCOPE.
- scope rules must be exact:
  - direct/group conversation: same `conversationId` only.
  - project channel: same `projectId` + same `channelId` only.
  - project general chat: same `projectId` with no channel and no conversation only.
- include a time boundary so a notification created after the current read action is not accidentally consumed. Use the current read timestamp as an upper bound (`createdAt <= readAt`) or an equivalently safe server-side boundary.
- never mark another project/channel/conversation's notifications as read.
- keep the returned `notificationsMarked` count if useful.

The intended result is that opening/reading a TCS scope produces one authoritative state: message unread and global notification unread both reconcile to zero for that scope, even when there were more than 100 historical unread messages.

Do not change Prisma schema.

## Step 3 — review the rest of V1 before committing

Re-review the V1 global hook and sidebar implementation for:

- one global background socket subscription through the existing singleton socket client.
- no duplicate listeners after page navigation/unmount.
- notification-id dedupe.
- authoritative hydration/reconciliation after read/state-sync events.
- no navigation blocking if notifications API fails.
- desktop, collapsed sidebar, and mobile unread badge.
- `99+` cap.
- alert only outside the active TCS page.
- Arabic/English accessible labels.
- no secrets/logged payloads.

If you find another actual Phase 2 bug while reviewing, fix it in the same review-fix commit and document it precisely. Do not expand product scope.

## Step 4 — validation before commit/push

Run from the canonical production repo:

1. `git diff --check`
2. bounded source scan proving no new `TACS` under `frontend/src` or `backend/src`.
3. `./scripts/tos-production-preflight.sh --live`
4. backend:
   - `node --check backend/src/server.js`
   - `node --check backend/src/app.js`
   - `node --check backend/src/routes/chat.routes.js`
   - from backend: `npm run prisma:validate`
5. frontend: `npm run build`
6. deterministic regression evidence proving the notification-read predicate is target-scoped and is NOT limited by the `recentMessages take: 100` list.
7. verify no Prisma schema/migration change.

All gates must pass.

## Step 5 — create the second commit

Create a NEW commit on top of V1, for example:

`fix(tcs): reconcile global unread by chat scope`

Do not amend V1.

Capture:

- `V1_COMMIT=860e2f25621f3eb6ab5fa39bc7a96737743df3bd`
- `FIX_COMMIT=<new SHA>`
- changed files in the fix commit.

## Step 6 — restore the existing non-interactive GitHub CLI path used successfully in V11

Important historical evidence: on the SAME production host, TCS Phase 1 V11 successfully pushed using `AUTH_METHOD=GH_CLI`. Therefore do not immediately conclude GitHub auth is absent merely because `gh` is missing from the current PATH.

Do not print secrets. Disable shell tracing around auth discovery.

Safely check for the GitHub CLI binary using:

- `command -v gh`
- `/usr/bin/gh`
- `/usr/local/bin/gh`
- `/snap/bin/gh`
- any executable path referenced by an existing Git credential helper configuration.

Do not dump credential files.

Also check existence only (never contents) of the expected root GitHub CLI config directory/file, such as `/root/.config/gh/hosts.yml`, when running as root. If the binary exists and the existing config is available, use that same config context.

For a discovered GH binary, run auth status with output suppressed/sanitized. If authenticated:

- run `gh auth setup-git` using that exact binary/config context.
- push non-interactively: `GIT_TERMINAL_PROMPT=0 git push origin main`.

If GitHub CLI still cannot authenticate, try existing SSH authentication non-interactively as a fallback. Never prompt for or invent credentials. Do not install a new credential or paste a token.

If neither existing auth path works, STOP before deployment and preserve both local commits.

## Step 7 — verify GitHub after push

After successful push, require remote `main` to equal the new `FIX_COMMIT` and verify both commits are present in order:

`ecc88cb... -> 860e2f... -> FIX_COMMIT`

No force push.

## Step 8 — deploy canonical production stack

Because Phase 2 changes both frontend and backend, deploy ONLY after successful push using the official script:

`./scripts/tos-production-deploy.sh --scope both`

No Prisma migration flags are needed because schema did not change.

Capture backend/frontend PM2 PID before and after and expected restart behavior from the official deploy script. Require post-deploy preflight and backend health to pass.

## Step 9 — live Phase 2 verification

With an authenticated staff session, verify at minimum:

- TCS navigation label is present.
- global unread badge renders outside TCS.
- receiving a `chat:notification` while on another TOS page updates the badge without full-page reload.
- background alert appears outside TCS and Open TCS navigates correctly.
- opening/reading the exact target reconciles the badge/read state.
- other chat scopes remain unread when only one target is read.
- project/channel/direct chat still load.
- no global navigation regression.

Use two existing authorized users if available. Do not create users or guess/reset passwords solely for QA. If second-user auth remains unavailable, mark the true two-user portion `SECOND_AUTHORIZED_USER_REQUIRED`, but still complete all safe single-session/live structural checks.

## Step 10 — final report

Return `TCS_PHASE2_REVIEW_FIX_PUSH_V2_REPORT.zip` with Markdown report and safe evidence including:

- starting branch/HEAD/parent
- remote start SHA
- V1 commit scope verification
- reviewed defect and exact correction
- fix commit SHA and changed files
- diff/TACS/preflight/syntax/Prisma/frontend build results
- proof no migration/schema change
- auth discovery result (`GH_CLI`, `SSH`, or `NONE`) without secrets
- push result
- remote final SHA
- official deploy result, scope `both`
- PM2/health/preflight results
- live global unread/background alert checks
- target-scoped read reconciliation check
- two-user QA status if available
- exact blockers if any

Do not claim Phase 2 complete unless the fix is pushed and production deployment passes.