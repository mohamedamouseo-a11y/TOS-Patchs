# TCS Phase 2 — Global Unread + Background Realtime Notifications

Repository: `mohamedamouseo-a11y/TOS`
Branch: `main` ONLY
Reviewed production baseline commit: `ecc88cb10c4741437f65f0788888bd9fcc9c5de0`
Product: `TCS — Tamayouz Chat System`

## Operating model for this phase

Manus is now responsible for writing the implementation code, testing it, committing it, pushing it from the TOS server to `TOS/main`, and deploying it. ChatGPT will review the resulting GitHub commit after the push.

## Hard rules

1. Do NOT create a branch.
2. Work on `main` only.
3. Do NOT touch the obsolete root-stack TCS experiment under root `client/`, root `server/`, `drizzle/`, or `drizzle.config.ts`.
4. Canonical production stack only:
   - `/var/www/TOS/frontend`
   - `/var/www/TOS/backend`
5. Do NOT create new chat database tables.
6. Do NOT run a Prisma schema migration for this phase unless absolutely unavoidable. The intended implementation must reuse the existing chat models/read-state/notification models.
7. Preserve unrelated tracked changes and the tolerated pre-existing untracked ZIP artifacts.
8. Product naming is TCS only. Do not introduce `TACS` anywhere.
9. Do not weaken authentication, authorization, CSRF, chat membership checks, project access rules, or private-channel/direct-chat restrictions.
10. Do not print, save, or expose credentials, tokens, cookies, session IDs, or DATABASE_URL.

## Why this is the next phase

The production TCS already has direct conversations, group conversations, channels, typing indicators, delivery/read receipts, reactions, replies, edit/delete, attachments, voice recording, meetings, search, chat notifications, moderation, insights, decisions, tasks, and presence.

The remaining product gap is global awareness outside the TCS page. Today the chat hook and chat notification listener live inside `ChatPanel`, while the main `Sidebar` has no TCS unread badge. Therefore users can miss new TCS activity while working elsewhere in TOS.

## Phase 2 objective

Implement a production-grade global TCS unread and background realtime notification layer that stays active while the user is anywhere inside TOS.

### Required behavior

1. **Global TCS unread badge**
   - Show a numeric unread badge next to `TCS` in the desktop sidebar.
   - Show the same unread state in the mobile sidebar.
   - `99+` display cap is acceptable for very large counts.
   - Badge disappears at zero.

2. **Initial unread hydration**
   - On authenticated app load, hydrate the global unread count from existing backend chat data.
   - Prefer existing models and endpoints.
   - If a small aggregate endpoint is needed, add a minimal authenticated `/api/chat/...` endpoint using existing `ChatReadState`, `ChatNotification`, `Message`, conversation, channel, and project access rules.
   - No new tables.

3. **Background realtime listener**
   - The realtime listener must be mounted at the authenticated App/shell level, not only inside `ChatPanel`.
   - Listen for existing `chat:notification` events while the user is on Dashboard, Tasks, TWS, Team, SLA, Settings, etc.
   - Do not create duplicate socket connections or duplicate event subscriptions.
   - Reuse the existing socket client and user-room behavior.

4. **Live count updates**
   - New qualifying TCS messages/mentions/replies increment the global unread state in realtime.
   - Do not double-increment for duplicate socket delivery or remounts.
   - When the relevant conversation/channel/project chat is marked read, the global badge must reduce/clear correctly.
   - If existing chat notification rows are not currently synchronized with the normal chat `markRead` action, fix that synchronization using the existing notification model instead of inventing another unread system.

5. **Background in-app alert**
   - When the user is outside TCS and receives a new TCS event, show a compact non-blocking in-app notification/toast using the existing TOS visual system.
   - Include sender/title and a short safe preview when available.
   - Never expose hidden/private data to a user who lacks access.
   - Do not show duplicate alerts for the same notification id.

6. **Open TCS from alert**
   - Clicking the alert should navigate to TCS.
   - Where safely supported by existing routing/state, open the relevant direct conversation, channel, or project context.
   - If deep-link context is not safely supported, open TCS root without inventing brittle routing.

7. **TCS page compatibility**
   - Existing `ChatPanel` unread counts, notifications, typing, delivery/read receipts, attachments, group/channel controls, direct conversations, search, calls/meetings, and message actions must continue working.
   - Avoid two independent sources of truth fighting each other. Create a small shared global TCS state/hook/provider if that is the cleanest production approach.

8. **Language and accessibility**
   - Arabic and English UI text where new text is introduced.
   - Badge/alert controls must have accessible labels and keyboard interaction.
   - Preserve RTL/LTR behavior.

## Implementation guidance

First inspect the current production code before editing, especially:

- `frontend/src/App.jsx`
- `frontend/src/components/layout/Sidebar.jsx`
- `frontend/src/components/ChatPanel.jsx`
- `frontend/src/hooks/useChat.js`
- `frontend/src/lib/api.js`
- `frontend/src/lib/socket.js`
- `backend/src/routes/chat.routes.js`
- existing Prisma chat models in `backend/prisma/schema.prisma`

Prefer the smallest coherent implementation. Do not rewrite ChatPanel.

A reasonable architecture is an authenticated app-level TCS notification/unread hook/provider that:

- performs initial unread hydration,
- subscribes once to `chat:notification`,
- deduplicates notification IDs,
- exposes unread count to Sidebar/MobileSidebar,
- exposes a transient in-app TCS alert,
- refreshes/reconciles after read-state mutations.

Use existing backend notifications/read-state behavior wherever possible. If backend synchronization is incomplete, make the minimal production fix there.

## Validation gates before commit

Run all relevant validation for the files you change.

Mandatory minimum:

```bash
cd /var/www/TOS
./scripts/tos-production-preflight.sh --live
```

If frontend changes:

```bash
cd /var/www/TOS/frontend
npm run build
```

If backend JavaScript changes:

```bash
cd /var/www/TOS/backend
node --check src/server.js
node --check src/app.js
node --check src/routes/chat.routes.js
npm run prisma:validate
```

Run any existing relevant automated tests/scripts discovered in the repo for chat/socket/sidebar behavior. Do not skip a relevant existing test just because it was not named above.

Also verify:

- no `TACS` introduced,
- no root-stack files changed,
- no Prisma schema migration created,
- no unrelated files changed,
- `git diff --check` passes.

## Functional QA before push

At minimum, with the existing authorized User A session:

1. TOS loads normally.
2. Sidebar shows TCS.
3. TCS badge initial state loads without console/runtime errors.
4. Opening TCS still loads direct/project/group/channel UI.
5. Returning to another page leaves global TCS listener active.
6. Ramzy, Tasks, TWS, Team, SLA and Settings navigation still loads normally.

If a second already-authorized User B session is available, also test:

1. User A stays outside TCS.
2. User B sends one message to A.
3. A receives background alert without reload.
4. TCS sidebar badge increments.
5. A clicks the alert and opens TCS.
6. A opens the target chat; unread state clears/reduces.
7. B replies again; A receives it realtime.
8. Refresh preserves correct unread state from backend.

If no valid second session is available, do NOT create/reset/impersonate a user just for QA. Record `TWO_USER_LIVE_QA_PENDING`, but this alone must not block an otherwise validated Phase 2 implementation/push/deploy.

## Commit and push

Only after validation passes:

```bash
git status --short
git diff --check
git add <only the intentional Phase 2 files>
git commit -m "feat(tcs): add global unread and realtime alerts"
GIT_TERMINAL_PROMPT=0 git push origin main
```

Use the existing non-interactive GitHub authentication method that succeeded for the V11 push. Never open an interactive credential prompt.

Confirm remote `main` points to the new commit after push.

## Deploy

Use the official production deploy script only.

If frontend-only:

```bash
cd /var/www/TOS
./scripts/tos-production-deploy.sh --scope frontend
```

If backend and frontend both changed:

```bash
cd /var/www/TOS
./scripts/tos-production-deploy.sh --scope both
```

Do not deploy root-stack code.

After deploy, rerun live preflight and basic HTTP health checks.

## Final evidence report

Return one ZIP in the current Manus session named:

`TCS_PHASE2_GLOBAL_UNREAD_REALTIME_REPORT.zip`

It must contain a Markdown report with:

- start branch and SHA,
- final local SHA,
- final remote SHA,
- exact changed files,
- architecture summary,
- whether backend changed,
- confirmation no DB migration/table was added,
- build/test/preflight results,
- functional QA matrix,
- two-user QA result or `TWO_USER_LIVE_QA_PENDING`,
- deployment scope and result,
- live HTTP/health result,
- any blocker or known limitation.

Do not start Phase 3 in the same run. Stop after Phase 2 report is complete.