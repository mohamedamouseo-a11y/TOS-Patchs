# TCS — One-Shot Production Completion V1

Repository: `mohamedamouseo-a11y/TOS`
Branch: `main` ONLY
Production root: `/var/www/TOS`
Product: **TCS — Tamayouz Chat System**

## Operating model

This is a ONE-SHOT completion run. Manus owns implementation, testing, commit creation, push from the TOS server, production deployment, and the final evidence report. ChatGPT will review the resulting GitHub commits after the push.

Do not split the work into more phases unless a hard external blocker makes completion impossible.

## Current preserved local lineage

The TOS server is expected to already contain these three validated local Phase 2 commits on `main`, in this exact order:

1. `860e2f25621f3eb6ab5fa39bc7a96737743df3bd` — global unread/background realtime implementation
2. `321784f9b54a3dd27f7d8f352659a0a3db47e56a` — exact chat-scope unread/notification reconciliation
3. `2a19c70f4614826986a2ec30c49254877649ca38` — lifecycle hardening for stale toast + reconnect/visibility rehydrate

Expected last verified remote base before these local commits:
`ecc88cb10c4741437f65f0788888bd9fcc9c5de0`

Dedicated TOS deploy-key private key already exists only on the server at:
`/root/.ssh/tos_main_deploy_ed25519`

Never print, copy, archive, or expose the private key.

## Hard rules

1. NO new branch. `main` only.
2. Work only in the canonical production stack:
   - `/var/www/TOS/frontend`
   - `/var/www/TOS/backend`
3. Do NOT touch obsolete root `client/`, root `server/`, `drizzle/`, or `drizzle.config.ts`.
4. Preserve the three existing Phase 2 commits exactly. Do NOT amend, squash, reset, cherry-pick, recreate, or discard them.
5. Do not reimplement a feature that already exists. Audit first, then implement only real gaps/defects.
6. Do not weaken auth, CSRF, project membership, direct-chat membership, private-channel rules, role permissions, upload restrictions, or moderation controls.
7. Do not expose tokens, cookies, credentials, session IDs, database URLs, private keys, or secret environment values.
8. No force push.
9. No database migration unless an objectively missing capability cannot be completed with the existing Prisma schema. The current TCS already has rich chat models, so migration should normally be unnecessary. If a migration appears necessary, inspect it first and only proceed if it is additive, TCS-specific, and non-destructive.
10. Preserve unrelated work and tolerated pre-existing untracked ZIP artifacts.
11. Product naming is `TCS` / `Tamayouz Chat System`. Never introduce `TACS`.
12. Use the official production deploy script only.

# STEP 0 — Repository and authentication gate

```bash
set -Eeuo pipefail
set +x
cd /var/www/TOS

test "$(git branch --show-current)" = "main"
test "$(git rev-parse HEAD)" = "2a19c70f4614826986a2ec30c49254877649ca38"
test "$(git rev-parse 2a19c70f4614826986a2ec30c49254877649ca38^)" = "321784f9b54a3dd27f7d8f352659a0a3db47e56a"
test "$(git rev-parse 321784f9b54a3dd27f7d8f352659a0a3db47e56a^)" = "860e2f25621f3eb6ab5fa39bc7a96737743df3bd"

git diff --check
```

Verify the dedicated key exists with safe permissions. Do not print it.

Then verify repository access using the deploy key without changing `origin` yet:

```bash
GIT_SSH_COMMAND='ssh -i /root/.ssh/tos_main_deploy_ed25519 -o IdentitiesOnly=yes -o BatchMode=yes -o StrictHostKeyChecking=accept-new' \
  git ls-remote git@github.com:mohamedamouseo-a11y/TOS.git refs/heads/main
```

If this fails because the public key has not been added to GitHub as a WRITE-ENABLED deploy key, STOP before changing code and return only:

- `AUTH_BLOCKER=DEPLOY_KEY_NOT_REGISTERED_OR_NOT_WRITE_ENABLED`
- the public key from `/root/.ssh/tos_main_deploy_ed25519.pub`
- its fingerprint

Never return the private key.

If auth works, continue the entire run without asking for more confirmation.

Verify remote `main` still points to the expected base before doing further work. If remote moved, do NOT blindly merge/rebase. Inspect the remote changes and only continue if they are already equivalent/compatible; otherwise stop with exact sanitized evidence.

# STEP 1 — Full TCS production audit

Audit the current canonical production implementation before writing code. At minimum inspect:

Frontend:
- `frontend/src/App.jsx`
- `frontend/src/components/ChatPanel.jsx`
- `frontend/src/components/layout/Sidebar.jsx`
- `frontend/src/hooks/useChat.js`
- `frontend/src/hooks/useGlobalTcsUnread.js`
- `frontend/src/lib/api.js`
- `frontend/src/lib/socket.js`
- `frontend/src/lib/realtimeStateSync.js`
- chat-related permission helpers and routing helpers

Backend:
- `backend/src/routes/chat.routes.js`
- chat/socket wiring
- chat sanitize helpers
- auth/access middleware used by chat
- Prisma chat models/read state/notification models
- existing Phase 2 helper/tests

Create a concise audit matrix with `EXISTS / GAP / DEFECT / NOT_NEEDED` for the production capabilities below.

## TCS completion capabilities

A. Navigation and product identity
- TCS label/branding in sidebar/page
- unread badge visible globally
- no stale badge after read
- no stale toast after read or entering TCS
- deep-link/open behavior to the relevant TCS scope where current architecture supports it

B. Realtime and resilience
- one shared Socket.IO client only
- background realtime notifications outside TCS page
- reconnect recovery
- visibility/tab-resume recovery
- no continuous global polling loop
- no duplicate listeners after remount

C. Messaging
- direct 1:1 conversations
- group conversations
- project general chat
- project channels/private channels
- replies
- edit/delete
- reactions
- typing indicators
- delivery receipts
- read receipts
- unread counters/read state
- presence

D. Collaboration
- attachments/file upload/download/delete
- file type/size protections
- voice recording if supported by current UI
- meeting links/calls if already part of current product
- message-to-task flow
- pinned messages / decisions / notes where already supported
- mentions
- search

E. Notifications
- persisted chat notifications
- global unread count
- exact-scope notification reconciliation on read
- mentions/replies/messages correctly classified
- no unrelated notification read side effects
- notifications created after a read action remain unread

F. Security and permissions
- direct chat restricted to authorized internal users
- conversation membership enforced
- project/channel access enforced
- private channel membership enforced
- role permissions preserved
- CSRF/auth protections preserved
- upload restrictions preserved
- deleted/disabled users handled safely

G. UX quality
- Arabic/English behavior remains valid
- light/dark mode remains valid
- mobile/narrow layout remains usable
- loading/empty/error states are not broken
- keyboard/focus behavior remains reasonable
- TCS failures do not crash the full TOS shell

H. Operational quality
- no new schema unless truly necessary
- no duplicate chat system
- no obsolete root-stack changes
- bounded backend queries for list/render paths
- no obvious N+1 introduced by this completion run
- no secret logging

# STEP 2 — Implement all real gaps found

After the audit, implement ALL real gaps/defects needed for a production-complete TCS in this run.

Rules for implementation:
- Prefer minimal extensions to the existing production architecture.
- Reuse existing Prisma models and API routes where possible.
- Reuse the shared socket and realtime-state infrastructure.
- Do not create a second notification system.
- Do not create duplicate direct/group/channel models.
- Do not move TCS into the obsolete root stack.
- Keep changes bounded to TCS-related production files unless a small shared-shell change is objectively required.
- If a gap is already fully supported, record `EXISTS` and do not touch it.

If you discover a defect that could cause data loss, unauthorized access, destructive DB behavior, or cross-user notification leakage, prioritize fixing it before UX polish.

# STEP 3 — Required validation gates

Run all applicable gates before commit/push.

Backend minimum:

```bash
cd /var/www/TOS
node --check backend/src/routes/chat.routes.js
node --check backend/src/services/chatUnreadScope.js
node --test backend/src/services/chatUnreadScope.test.js
cd backend
npm run prisma:validate
cd ..
```

If you add/change other backend JS files, run `node --check` on each changed backend JS file and add deterministic tests for non-trivial logic.

Frontend minimum:

```bash
cd /var/www/TOS/frontend
npm run build
cd /var/www/TOS
```

Repository gates:

```bash
git diff --check
! grep -Rni --exclude-dir=node_modules --exclude-dir=dist --exclude-dir=.git 'TACS' frontend/src backend/src
./scripts/tos-production-preflight.sh --live
```

Also verify:
- no Prisma schema/migration drift unless intentionally required
- no changes under obsolete root `client/`, root `server/`, `drizzle/`, `drizzle.config.ts`
- only intended TCS/shared-shell files changed
- the three tolerated ZIP artifacts remain untracked and untouched

# STEP 4 — TCS functional QA

Do as much functional verification as can be safely automated from the server without inventing credentials.

Required behavior coverage:
1. Open TCS from navigation.
2. Global unread badge is available outside the TCS page.
3. New realtime chat notification updates global state while user is elsewhere in TOS.
4. Entering/reading the exact chat scope clears only the appropriate unread state.
5. Notifications created after the read timestamp remain unread.
6. Reconnect triggers authoritative hydrate.
7. Visibility restore triggers authoritative hydrate.
8. No old toast reappears after reading/entering TCS.
9. Direct chat send/receive/history remains intact.
10. Group/channel behavior remains intact.
11. Replies/reactions/edit/delete remain intact.
12. Attachments remain intact.
13. Read/delivery/typing/presence behavior remains intact.
14. Search/mentions/task/decision features that already existed still work.
15. Ramzy, Tasks, TWS/TGWS, Sidebar, Settings, and the main TOS shell still render after the TCS changes.

If two authenticated browser sessions are already available, use them for A→B→A live QA.

If a second browser session is unavailable, do NOT create/reset users or passwords and do NOT modify real users. Instead, supplement with safe backend/integration tests using existing application service boundaries and isolated TCS test data only. Any temporary test data created by the smoke must have a unique `TCS_E2E_` marker and be cleaned up after the test. Never delete or alter unrelated real messages/conversations/users.

A missing second browser session is not by itself a reason to discard otherwise validated code; report clearly which UI-only observations could not be visually verified.

# STEP 5 — Commit strategy

Keep the three existing commits untouched.

Create one or more NEW commits only for the remaining completion work. Prefer logical commits, for example:

- `fix(tcs): complete realtime unread lifecycle`
- `feat(tcs): complete production collaboration gaps`
- `test(tcs): add production regression coverage`

Do not commit generated build output unless it is already tracked by repository policy.

Before push, print only the safe commit graph:

```bash
git --no-pager log --oneline --decorate -8
```

# STEP 6 — Push from the TOS server

Push using the dedicated repository-scoped deploy key. Do not change global SSH configuration.

Preferred push:

```bash
cd /var/www/TOS
GIT_SSH_COMMAND='ssh -i /root/.ssh/tos_main_deploy_ed25519 -o IdentitiesOnly=yes -o BatchMode=yes -o StrictHostKeyChecking=accept-new' \
  git push git@github.com:mohamedamouseo-a11y/TOS.git main:main
```

No force push.

After push, verify:

```bash
LOCAL_FINAL_SHA="$(git rev-parse HEAD)"
REMOTE_FINAL_SHA="$(GIT_SSH_COMMAND='ssh -i /root/.ssh/tos_main_deploy_ed25519 -o IdentitiesOnly=yes -o BatchMode=yes -o StrictHostKeyChecking=accept-new' git ls-remote git@github.com:mohamedamouseo-a11y/TOS.git refs/heads/main | awk '{print $1}')"
test "$LOCAL_FINAL_SHA" = "$REMOTE_FINAL_SHA"
```

# STEP 7 — Production deploy

Only after successful push and SHA equality:

```bash
cd /var/www/TOS
./scripts/tos-production-deploy.sh --scope both
```

Do NOT run a DB migration unless this run intentionally added a reviewed safe migration.

After deploy:
- run live preflight again
- verify backend health
- verify frontend serves successfully
- verify PM2 apps are online
- inspect only bounded recent logs for TCS/runtime errors; do not dump secrets
- perform the post-deploy TCS QA items possible with available sessions

# STEP 8 — Final evidence and report

Return one ZIP in this session named:

`TCS_COMPLETE_END_TO_END_V1_REPORT.zip`

The ZIP must include:
- `TCS_COMPLETE_END_TO_END_V1_REPORT.md`
- audit matrix
- final changed-file list
- final commit graph/SHAs
- validation outputs or concise receipts
- production preflight receipt
- deploy receipt
- post-deploy QA matrix
- SHA256SUMS

Do not include secrets or private keys.

Final report must explicitly state:

```text
BRANCH=
REMOTE_START_SHA=
PRESERVED_V1_SHA=860e2f25621f3eb6ab5fa39bc7a96737743df3bd
PRESERVED_V2_SHA=321784f9b54a3dd27f7d8f352659a0a3db47e56a
PRESERVED_V3_SHA=2a19c70f4614826986a2ec30c49254877649ca38
NEW_COMPLETION_COMMITS=
LOCAL_FINAL_SHA=
REMOTE_FINAL_SHA=
AUTH_METHOD=DEPLOY_KEY
PUSH=
DEPLOYMENT=
DEPLOY_SCOPE=both
BACKEND_HEALTH=
FRONTEND_HEALTH=
PRISMA_SCHEMA_CHANGED=
MIGRATION_RUN=
TACS_SCAN=
FRONTEND_BUILD=
BACKEND_SYNTAX=
TCS_TESTS=
GLOBAL_UNREAD=
BACKGROUND_REALTIME=
RECONNECT_RECOVERY=
VISIBILITY_RECOVERY=
STALE_TOAST_FIXED=
DIRECT_CHAT=
GROUP_CHAT=
CHANNEL_CHAT=
READ_DELIVERY_RECEIPTS=
TYPING_PRESENCE=
REACTIONS_REPLIES_EDIT_DELETE=
ATTACHMENTS=
SEARCH_MENTIONS=
TASK_DECISION_INTEGRATION=
AUTHORIZATION_REGRESSION=
TOS_SHELL_REGRESSION=
PHASE2_AND_TCS_COMPLETION_STATUS=
```

`PHASE2_AND_TCS_COMPLETION_STATUS=PASS` is allowed only when push succeeded, remote SHA equals local SHA, production deployment succeeded, all mandatory validation gates passed, and no unresolved critical/high-severity TCS defect remains.