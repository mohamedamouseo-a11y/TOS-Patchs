# TCS Phase 1 — Production Alignment V10

Repository: `mohamedamouseo-a11y/TOS`
Branch: `main` ONLY
Pinned starting HEAD: `03a61b7bc84baa8e801ec40f33d24bbaf0969894`

## Critical architecture correction

V9 discovered the canonical production runtime and proved the earlier root-stack TCS implementation targeted the wrong application stack.

Canonical production runtime is defined by `deployment/tos-production-runtime.json`:

- backend source: `/var/www/TOS/backend`
- backend PM2 app: `tamiyouz-system`
- backend entrypoint: `/var/www/TOS/backend/src/server.js`
- frontend source: `/var/www/TOS/frontend`
- frontend build output: `/var/www/TOS/frontend/dist`
- published frontend: `/opt/apps/tamiyouz-front/build`
- frontend PM2 app: `tamiyouz-frontend`

The root `client/`, root `server/`, `drizzle/schema.ts`, and `drizzle.config.ts` stack is NOT the canonical production TOS runtime for this feature.

The production backend already has a mature PostgreSQL + Prisma chat system with direct conversations, group conversations, channels, unread/read state, notifications, files, reactions, replies, presence, voice/video huddles, and audit logging. Therefore TCS Phase 1 must ALIGN and BRAND the existing production chat system instead of creating duplicate MySQL/Drizzle chat tables.

NO DATABASE MIGRATION is allowed in V10.

## ChatGPT-authored production patch

Patch repository: `mohamedamouseo-a11y/TOS-Patchs`
Patch path:

`TCS/Phase-1/Production/TCS_PHASE_1_PRODUCTION_BRANDING_ALIGNMENT_V1.patch`

This patch changes ONLY:

`frontend/src/i18n/translations.js`

It brands the existing production chat surface as `TCS — Tamayouz Chat System` / `TCS` in Arabic and English UI labels.

## Strict rules

1. Do NOT create a branch.
2. Do NOT run `git pull`.
3. Do NOT write, redesign, or reimplement TCS code.
4. Do NOT create any new chat database table.
5. Do NOT run Drizzle commands.
6. Do NOT run Prisma migrations.
7. Do NOT restart the backend PM2 app.
8. Do NOT modify `backend/prisma/schema.prisma`.
9. Do NOT modify `backend/src/routes/chat.routes.js` or `frontend/src/components/ChatPanel.jsx` in V10.
10. Preserve the three existing `TOS_V1.15.*.zip` files exactly.
11. Clean up ONLY the exact failed root-stack changes listed below. Do not use `git clean`, broad reset, broad checkout, or stash.
12. Apply ONLY the ChatGPT-authored production branding patch.
13. Push only after validation passes.
14. Deploy frontend only through the canonical repository deployment script.
15. Never enter GitHub credentials interactively.
16. Product name is `TCS — Tamayouz Chat System`; never TACS.

## Step 1 — verify starting state

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
- the only tracked modifications must be the seven failed-root-attempt paths below:
  - `client/src/components/DashboardLayout.tsx`
  - `drizzle/schema.ts`
  - `server/auth.logout.test.ts`
  - `server/routers.ts`
  - `server/tos.test.ts`
  - untracked `client/src/components/TcsChat.tsx`
  - untracked `server/tcsRouter.ts`
- plus the three pre-existing untracked ZIPs.

If ANY other changed/untracked source file exists, STOP and report it. Do not clean anything.

Capture the pre-cleanup diff/status as evidence.

## Step 2 — surgically remove the failed root-stack attempt

Run ONLY:

```bash
git restore -- \
  client/src/components/DashboardLayout.tsx \
  drizzle/schema.ts \
  server/auth.logout.test.ts \
  server/routers.ts \
  server/tos.test.ts

rm -- client/src/components/TcsChat.tsx server/tcsRouter.ts
```

Do NOT touch the three ZIP files.

Then verify:

```bash
git diff --quiet && echo ROOT_TRACKED_CLEAN
git diff --cached --quiet && echo INDEX_CLEAN
git status --short
```

Required status after cleanup: ONLY the three pre-existing ZIP files are untracked.

If not, STOP.

## Step 3 — verify canonical production architecture

Read-only checks:

```bash
node -e 'const m=require("./deployment/tos-production-runtime.json"); console.log({backend:m.backend.sourceDir,backendPm2:m.backend.pm2App,frontend:m.frontend.sourceDir,frontendPm2:m.frontend.pm2App,published:m.frontend.publishedBuildDir})'

grep -F 'provider = "postgresql"' backend/prisma/schema.prisma
grep -F 'model Conversation {' backend/prisma/schema.prisma
grep -F 'model ConversationMember {' backend/prisma/schema.prisma
grep -F 'model Message {' backend/prisma/schema.prisma
grep -F 'model ChatReadState {' backend/prisma/schema.prisma
grep -F 'model ChatNotification {' backend/prisma/schema.prisma

test -f backend/src/routes/chat.routes.js
test -f frontend/src/components/ChatPanel.jsx
```

Also confirm the existing code contains direct/group functionality:

```bash
grep -F 'createDirect' frontend/src/components/ChatPanel.jsx
grep -F 'createGroup' frontend/src/components/ChatPanel.jsx
grep -F 'unreadCount' backend/src/routes/chat.routes.js
```

These are evidence only. Do NOT edit those files.

## Step 4 — obtain and pre-check the branding patch

Clone the patch repository OUTSIDE production:

```bash
rm -rf /tmp/TOS-Patchs-TCS-Production-V10
git clone --depth 1 https://github.com/mohamedamouseo-a11y/TOS-Patchs.git /tmp/TOS-Patchs-TCS-Production-V10
```

Patch:

```bash
PATCH=/tmp/TOS-Patchs-TCS-Production-V10/TCS/Phase-1/Production/TCS_PHASE_1_PRODUCTION_BRANDING_ALIGNMENT_V1.patch

test -f "$PATCH"
git apply --check "$PATCH"
```

If pre-check fails: STOP. Do not manually reproduce the changes.

## Step 5 — apply ONLY the production branding patch

```bash
git apply "$PATCH"
git diff --check
git status --short
git diff -- frontend/src/i18n/translations.js
```

Required source diff:

- ONLY `frontend/src/i18n/translations.js`
- plus the three untouched untracked ZIPs in status.

Verify branding:

```bash
grep -F 'chat: "TCS"' frontend/src/i18n/translations.js
grep -F 'TCS — Tamayouz Chat System' frontend/src/i18n/translations.js
```

Verify no new `TACS` string:

```bash
if git diff -- frontend/src/i18n/translations.js | grep -F '+TACS'; then
  echo 'TACS_BRANDING_FOUND'
  exit 1
fi
```

## Step 6 — canonical live preflight BEFORE build/commit

Run:

```bash
scripts/tos-production-preflight.sh --live
```

Must PASS. If not, STOP and report. Do not deploy.

## Step 7 — frontend build gate

```bash
cd /var/www/TOS/frontend
npm run build
cd /var/www/TOS
```

Required:

- exit 0
- `frontend/dist/index.html` exists.

Do NOT restart services yet.

## Step 8 — backend read-only syntax safety

No backend source was changed, but confirm canonical runtime files still parse:

```bash
cd /var/www/TOS/backend
node --check src/server.js
node --check src/app.js
node --check src/routes/chat.routes.js
cd /var/www/TOS
```

Do NOT run migrations and do NOT restart backend.

## Step 9 — commit ONLY the production branding alignment

Verify staged scope first:

```bash
git status --short
git diff --check
```

Then:

```bash
git add frontend/src/i18n/translations.js
git diff --cached --name-only
```

Required staged file list EXACTLY:

```text
frontend/src/i18n/translations.js
```

Then commit:

```bash
git commit -m "feat(tcs): align production chat branding"
```

Record local SHA.

The three ZIPs must remain untracked and untouched.

## Step 10 — push main non-interactively

```bash
GIT_TERMINAL_PROMPT=0 git push origin main
```

If push fails due authentication:

- do NOT enter credentials
- keep the local commit
- do NOT deploy
- report local SHA and exact push error.

If push succeeds, verify remote SHA equals local SHA.

## Step 11 — deploy FRONTEND ONLY using canonical script

Only after successful push:

```bash
cd /var/www/TOS
scripts/tos-production-deploy.sh --scope frontend
```

This is the only allowed deployment path.

Required:

- production preflight passes inside script
- frontend build passes
- `frontend/dist` is rsynced to `/opt/apps/tamiyouz-front/build`
- only `tamiyouz-frontend` is restarted
- final live preflight passes
- `tamiyouz-system` backend remains online and is NOT restarted.

Capture the deployment backup root printed by the script.

## Step 12 — live TCS Phase 1 functional smoke

Use TWO existing non-test production users with permission to use direct chat. Do not create users.

Validate on live `tos.tamiyouz.com`:

1. Sidebar/page identifies chat as `TCS`.
2. TCS page subtitle/name shows `TCS — Tamayouz Chat System` where the translated page label is rendered.
3. User A opens direct conversations and selects User B.
4. User A sends one clearly prefixed harmless smoke message, e.g. `[TCS-PHASE1-SMOKE] A -> B`.
5. User B sees the incoming message without a full browser reload (Socket.IO/realtime).
6. User B sees unread indication before opening the conversation.
7. User B opens the conversation and the unread state clears/updates.
8. User B replies `[TCS-PHASE1-SMOKE] B -> A`.
9. User A receives the reply without a full browser reload.
10. Refresh both browsers and confirm conversation history persists.
11. Confirm User A cannot access a direct conversation that does not include User A, using the existing authorization route behavior if a safe test target is available.
12. Confirm existing project chat / group/channel UI is still present and not regressed.

Do not delete existing business messages. The two smoke messages may remain as explicit test evidence unless the existing UI provides a safe delete action and both messages can be removed without affecting other data.

## Step 13 — final source/runtime verification

```bash
cd /var/www/TOS
git branch --show-current
git rev-parse HEAD
git status --short
scripts/tos-production-preflight.sh --live
pm2 describe tamiyouz-system | grep -E 'status|online' || true
pm2 describe tamiyouz-frontend | grep -E 'status|online' || true
```

Required final status:

- main
- local HEAD = pushed remote HEAD
- only three original ZIPs untracked
- backend PM2 online
- frontend PM2 online
- no MySQL/Drizzle TCS tables/migrations created
- no backend restart performed by this V10 workflow

## Required final report

Return `TCS_PHASE1_PRODUCTION_V10_REPORT.zip` containing a markdown report and evidence for:

1. starting branch/SHA
2. pre-cleanup failed-root diff/status
3. exact cleanup commands/results
4. proof only three ZIPs remained after cleanup
5. canonical runtime manifest evidence
6. proof production DB stack = PostgreSQL + Prisma
7. proof existing Conversation/ConversationMember/Message/ChatReadState/ChatNotification models exist
8. proof existing direct/group/unread chat code exists
9. branding patch `git apply --check` result
10. exact branding diff
11. pre-deploy live preflight
12. frontend build result
13. backend syntax checks
14. commit SHA
15. push result + remote SHA
16. frontend-only deploy result + backup root
17. proof backend PM2 was not restarted
18. two-user direct chat smoke results
19. unread/realtime/history results
20. authorization result
21. TCS branding result Arabic + English
22. final git status
23. final PM2/live preflight
24. explicit confirmation: `NO_TCS_DB_MIGRATION=YES`
25. explicit confirmation: `FAILED_ROOT_STACK_REMOVED=YES`
26. blockers, if any, with exact evidence.

If any mandatory gate fails, stop at that gate and do not improvise code changes.
