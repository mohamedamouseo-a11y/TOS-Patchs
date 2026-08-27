# Manus Execution Prompt — TNC Phase 1: Core + Unified Inbox + Realtime V1

## Mission

Implement **TNC — Tamayouz Notification Center Phase 1** in the canonical production TOS stack.

TNC must become the single user-facing notification center for TOS while **reusing the existing production notification infrastructure** instead of creating a parallel notification system.

This phase is specifically:

- TNC Core
- Unified Inbox
- Global unread count
- Realtime delivery/reconciliation
- Read / unread lifecycle
- Mark all read
- Source/category filters
- Safe deep-link navigation
- Premium responsive UX/UI

Do not implement advanced notification preferences, snooze, digest scheduling, email/push delivery policies, or escalation configuration in this phase.

---

## Repository / workflow rules

Implementation workdir:

`/var/www/TOS`

Actual implementation repository:

`mohamedamouseo-a11y/TOS`

Branch:

`main`

Required starting production SHA at prompt creation:

`d324e59098734463e908b454f328a8d12bfa5956`

Before editing, verify current `TOS/main`. If it has advanced beyond this SHA, inspect intervening commits and rebase the plan onto the current production HEAD. Do not overwrite newer work.

Prompt repository only:

`mohamedamouseo-a11y/TOS-Patchs`

**Never push implementation code to TOS-Patchs.**

---

# 1. Production architecture — mandatory

Use only the canonical production stack:

- `frontend/`
- `backend/`
- PostgreSQL + Prisma

Do not implement TNC in the obsolete root stack:

- `client/`
- `server/`
- `drizzle/`

Do not create a second frontend/backend notification application.

---

# 2. Existing production notification infrastructure — preserve and reuse

The current Prisma production schema already contains a generic `Notification` model with at least:

- `id`
- `recipientId`
- `actorId`
- `type`
- `title`
- `body`
- `metadata`
- `readAt`
- `createdAt`

The current TCS implementation already contains a separate `ChatNotification` model and working chat notification lifecycle.

Current existing APIs include:

- `GET /api/users/notifications`
- `PATCH /api/users/notifications/:notificationId/read`
- TCS notification APIs under `/api/chat/notifications`

Current Topbar already has a Bell dropdown that loads `api.users.notifications()`.

Current App also uses `api.users.notifications()` for Design Request completion/login alert behavior.

### Critical compatibility rule

Do **not** delete or break these existing APIs in Phase 1.

They may remain as compatibility endpoints while the new TNC API is introduced.

Do not break:

- Design Request alerts
- TCS global unread logic
- TCS floating launcher badge
- existing task/design/SLA notifications
- any existing direct consumer of `api.users.notifications()`

---

# 3. Phase 1 architecture

Build TNC as a **normalized aggregation layer**, not a replacement database.

Preferred architecture:

- new notification-center backend service/normalizer
- new authenticated TNC route(s)
- new shared frontend TNC hook/state owner
- new `TncNotificationCenter` UI
- existing Topbar Bell becomes the launcher for TNC

Do not add a TNC Sidebar navigation item in Phase 1.

Do not repurpose the existing SLA Inbox page as TNC.

The TNC Inbox is the notification feed inside the TNC surface.

---

# 4. No database migration unless objectively necessary

Phase 1 should be implementable using the existing:

- `Notification`
- `ChatNotification`
- existing metadata fields

Do not create another notification table.

Do not duplicate TCS notification rows into generic Notification rows.

Do not copy existing notifications between tables.

If you believe a schema migration is unavoidable, stop and document the exact blocker before making it. The preferred outcome is **NO MIGRATION**.

---

# 5. Unified TNC DTO

Create one normalized server response shape for both generic Notification and TCS ChatNotification records.

Each TNC item should expose a safe shape similar to:

```js
{
  id,                // stable TNC identity, preferably source-prefixed
  nativeId,
  source,            // GENERAL | TCS
  category,          // TCS | TASKS | TWS | SYSTEM | OTHER
  type,
  title,
  body,
  actor: {
    id,
    name,
    avatarUrl
  } | null,
  metadata,
  target,
  priority,
  readAt,
  createdAt
}
```

Exact naming may vary if a cleaner existing project convention exists, but the frontend must not need to know Prisma table-specific shapes.

Recipient identity must always come from authenticated `req.user.id`.

Never accept arbitrary recipient IDs from the browser for inbox reads.

---

# 6. Unified categories

Phase 1 categories:

1. `ALL`
2. `UNREAD`
3. `TCS`
4. `TASKS`
5. `TWS`
6. `SYSTEM`

Derive categories from trusted server-side data.

### TCS

All `ChatNotification` rows map to TCS.

### Tasks

Map generic Notification types / metadata related to tasks, assignments, approvals, design requests, SLA task activity, due dates, task comments, task completion, etc. after inventorying real current producers.

Do not invent notification producers that do not currently exist.

### TWS

Map existing notification types / metadata related to TWS/TGWS/workspace/documents/files/sharing if such generic Notification producers already exist.

If Phase 1 currently has no TWS notification producer, the TWS filter may correctly show an empty state. Do not fabricate fake events.

### System

Use for account, permissions, team/admin/system notifications and other appropriate generic system events.

Unknown generic notification types must still remain visible under `ALL` and should fall back safely to `OTHER` or `SYSTEM` according to a documented mapping.

---

# 7. Backend TNC API

Implement a dedicated authenticated TNC API. A recommended contract is:

### Feed

`GET /api/notification-center`

Support at minimum:

- category/filter
- unread-only
- bounded limit
- optional cursor pagination if consistent with current backend patterns

Return:

- normalized merged items
- total unified unread count
- category unread counts where practical

The merged feed must be sorted deterministically newest-first across both database sources.

Do not fetch unlimited history.

### Mark one read/unread

Provide a recipient-scoped endpoint that can safely target the underlying source.

For example:

`PATCH /api/notification-center/:source/:notificationId/read`

Body:

```json
{ "read": true }
```

and allow `read:false` for explicit Mark Unread.

For ChatNotification, update only rows belonging to the authenticated recipient.

For Notification, update only rows belonging to the authenticated recipient.

Cross-user IDs must return not-found/forbidden safely without information leakage.

### Mark all read

Provide:

`PATCH /api/notification-center/read-all`

It must mark the authenticated user's currently unread rows in **both** supported sources as read.

If a category is supplied, scope it correctly.

Return useful counts by source and total.

### Compatibility

Keep existing `/api/users/notifications` and `/api/chat/notifications` behavior working.

---

# 8. TCS notification semantics

Do not alter the TCS message unread/read database architecture.

TNC may update `ChatNotification.readAt` for TNC notification lifecycle.

Opening a TCS notification must navigate/open the correct TCS target using the existing production chat routing/window behavior.

Do not invent query parameters. Inspect the existing `App.jsx`, TCS desktop window, ChatPanel, and routing logic and use the actual supported target contract.

Do not create a second TCS unread hook.

If TNC marks a ChatNotification read/unread, ensure the existing TCS global unread state reconciles correctly through the existing hydration/realtime mechanism.

---

# 9. Safe deep-link target resolution

TNC item click must navigate to the real source when possible.

Examples:

- TCS conversation/channel/project chat
- Task / Design Request
- Project
- TWS/TGWS document/workspace
- relevant internal system page

Do not trust arbitrary external URLs from `metadata.url` blindly.

Implement a safe internal target resolver using known application routes / metadata.

Use SPA navigation/current TOS page routing when possible instead of forcing a full browser reload.

If a legacy notification only has an internal metadata URL, validate/normalize it before use.

If no valid destination exists, opening the notification should still mark it read and keep the user in TNC without error.

---

# 10. Realtime — mandatory

TNC must update without a manual page refresh.

### TCS

Reuse the already-working `chat:notification` socket event.

Do not add a duplicate TCS socket notification event only for TNC.

The shared TNC client state should normalize incoming `chat:notification` payloads and deduplicate by stable source/native ID.

### Generic Notification

Inventory all current production generic Notification producers (`prisma.notification.create`, `createMany`, helpers such as `notifyUser`, and any service wrappers).

Implement one safe reusable generic notification emit path for new generic Notification rows, ideally via a notification-center service that can emit to:

`user:<recipientId>`

with a TNC-specific event such as:

`tnc:notification`

Do not expose private data in socket payloads.

Where practical, migrate existing production generic Notification producers to the reusable helper without changing their business behavior.

If an existing producer cannot safely be migrated in this phase, the existing realtime state-sync invalidation must still cause TNC to rehydrate quickly after the relevant mutation.

### Reconciliation

The frontend TNC state must rehydrate on:

- initial authenticated load
- socket reconnect
- browser tab visibility restore
- relevant realtime state-sync invalidation

Do not depend only on a 60-second poll.

A slow fallback poll may remain as resilience, but realtime is primary.

---

# 11. Shared frontend TNC state

Do not let Topbar, TNC window, and other surfaces each create independent notification fetch loops.

Create a single shared TNC state owner/hook mounted at the authenticated App level, for example:

`useTncNotifications`

or an equivalent context/service aligned with the project style.

It should own:

- feed
- unified unread count
- loading/error state
- active filter
- hydration
- socket event reconciliation
- mark read
- mark unread
- mark all read
- refresh/reconnect handling

Topbar should receive/use the unified state rather than retaining a separate generic-only notification array.

Do not break Design Request alert logic in App; its legacy API use may remain independent until a later migration.

---

# 12. Topbar Bell behavior

Keep the current Bell location in the premium Topbar.

Replace the tiny current 8-item generic-only dropdown behavior with TNC launcher behavior.

The Bell badge must show the **unified unread count** across generic Notification + ChatNotification.

Use a sensible cap such as `99+`.

The button must remain accessible with Arabic/English aria labels.

Do not add another duplicate Bell elsewhere.

---

# 13. TNC UX/UI

Build a premium TOS-native Notification Center surface.

Desktop expectation:

- wide enough to read notification content comfortably
- opened from the Topbar Bell
- contained inside the TOS application frame
- must not escape the visible TOS frame
- must not become a Sidebar navigation item

Mobile/narrow expectation:

- use the available TOS frame width cleanly
- no horizontal overflow
- filter controls remain usable
- primary actions remain reachable

### Header

Show:

- `TNC`
- `Tamayouz Notification Center` / Arabic equivalent
- unified unread count
- Mark all read action
- close action

### Filters

Provide clean filter chips/tabs:

- All
- Unread
- TCS
- Tasks
- TWS
- System

### Notification row/card

Each item should communicate clearly:

- actor/avatar or source icon
- title
- concise body/preview
- source/category badge
- relative/absolute timestamp
- unread state
- priority where meaningful
- quick Mark read / unread action

Unread rows should have clear but restrained emphasis.

### Grouping

Group by useful date sections such as:

- Today
- Yesterday
- Earlier

or an equivalent clean date grouping.

### States

Implement polished:

- loading state
- empty state
- filter-empty state
- transient error/retry state

### Visual system

Respect existing TOS design tokens and premium shell.

Support:

- Arabic RTL
- English LTR
- Light mode
- Dark mode
- keyboard focus
- reduced motion

Do not use excessive animation.

---

# 14. Inbox semantics

The feed inside TNC is the Phase 1 **Unified Inbox**.

Do not build a second independent Inbox database.

Do not rename or repurpose `SlaInboxPage`.

TNC Inbox should simply aggregate the user's existing notification streams into one normalized personal feed.

---

# 15. Priority

Do not add a DB column in Phase 1 solely for priority.

Derive presentation priority from existing type/metadata where possible, e.g.:

- urgent SLA/escalation/security/blocker -> high/urgent
- mention/reply/task assignment -> important
- routine system/update -> normal

Unknown items default safely to normal.

Priority is presentation metadata, not a new workflow engine in this phase.

---

# 16. Security / privacy

Mandatory:

- authenticated recipient scoping on every TNC read/write endpoint
- no cross-user notification reads
- no cross-user mark-read/unread
- no raw internal user objects in normalized DTOs
- actor exposure limited to safe fields only
- no cookies/tokens/secrets in report artifacts
- safe internal target URLs only
- no arbitrary redirect behavior

---

# 17. Tests

Add deterministic backend tests for the new TNC normalization/aggregation layer.

At minimum verify:

1. generic Notification normalization
2. ChatNotification normalization
3. deterministic merged newest-first ordering
4. recipient scoping
5. unread-only filtering
6. category filtering
7. unified unread count
8. mark one read
9. mark one unread
10. mark all read across both sources
11. cross-user notification IDs cannot be mutated
12. safe target resolution rejects/ignores unsafe external targets
13. unknown types still normalize safely

If frontend unit/component test infrastructure is practical, cover key TNC state reconciliation and deduplication logic.

Always run:

- relevant backend tests
- Prisma validation
- frontend build
- backend startup/preflight or repository-standard backend validation
- `git diff --check`

---

# 18. Live QA

After deployment, perform authenticated live QA.

Required gates where environment permits:

### Bell / center

- Bell visible in Topbar
- unified badge correct
- TNC opens/closes
- no old generic-only dropdown remains

### Feed

- generic notifications visible
- TCS notifications visible
- global newest-first ordering correct
- filters work
- unread count changes correctly

### Lifecycle

- mark read
- mark unread
- mark all read
- reload persistence

### Realtime

- generic notification arrives without manual refresh
- TCS `chat:notification` arrives without manual refresh
- deduplication prevents duplicate rows
- socket reconnect rehydrates
- visibility restore rehydrates

### Navigation

- TCS item opens correct chat target
- task/design item opens correct task/queue target when metadata exists
- TWS item opens correct TWS/TGWS target when a real current notification exists
- targetless notifications fail safely

### Visual

- Arabic RTL
- English LTR
- Light
- Dark
- desktop
- narrow/mobile
- no horizontal overflow

### Regression

- TCS launcher/global unread still works
- Design Request login alerts still work
- Topbar theme/language/profile controls still work
- SLA Inbox remains independent and functional

### Two-user realtime

If two authenticated sessions are available, perform at least one A -> B notification delivery test.

If two sessions are not available, mark only that specific gate `BLOCKED_TWO_SESSION_UNAVAILABLE`. Do not fabricate a pass and do not block unrelated completed gates.

---

# 19. Commit and push workflow — mandatory

After implementation and local validation:

1. Commit implementation changes locally in `/var/www/TOS`.
2. **DO NOT use terminal `git push`.**
3. **DO NOT use SSH push.**
4. **DO NOT use `gh` CLI push.**
5. **DO NOT push implementation code to TOS-Patchs.**
6. Open the running TOS system.
7. Use **Developer Hub / GitHub integration inside TOS**.
8. Review the exact changed files there.
9. Use the in-system **Push** action.
10. Push to:

`mohamedamouseo-a11y/TOS`

branch:

`main`

11. Verify the remote GitHub SHA after push.

---

# 20. Deployment

Because Phase 1 is expected to include frontend + backend changes, deploy using the canonical production deploy workflow after successful in-system push.

Use the repository production script and correct scope, expected to be equivalent to:

`./scripts/tos-production-deploy.sh --scope both`

Do not deploy before the in-system GitHub push succeeds.

Run production preflight/health checks after deploy.

---

# 21. Scope guard

Do not modify unrelated systems.

Especially do not redesign:

- TCS chat UI
- TCS desktop window mechanics
- Ramzy
- Tasks UX
- TWS editor UX
- Developer Hub
- SLA Center/Inbox

except for the minimum integration needed for TNC navigation/realtime compatibility.

Do not perform unrelated cleanup/refactors while touching large files such as `App.jsx`, `Topbar.jsx`, `ChatPanel.jsx`, or backend route files.

---

# 22. Expected implementation footprint

Inspect first; exact filenames may differ.

A reasonable implementation may include:

Backend:

- new `backend/src/routes/notificationCenter.routes.js`
- new `backend/src/services/notificationCenter.service.js`
- route mount in canonical backend app/router
- minimal updates to existing generic Notification producers for realtime emit
- tests

Frontend:

- new `frontend/src/components/TncNotificationCenter.jsx`
- new `frontend/src/hooks/useTncNotifications.js` or equivalent context
- `frontend/src/components/layout/Topbar.jsx`
- `frontend/src/App.jsx`
- `frontend/src/lib/api.js`
- minimal styles/i18n additions

Do not create files merely to match this list; use the cleanest architecture after inspection.

---

# 23. Final report

Return one ZIP named exactly:

`TNC_PHASE1_CORE_UNIFIED_INBOX_REALTIME_V1_REPORT.zip`

Include:

- executive summary
- START_SHA
- FINAL_SHA
- changed files
- architecture explanation
- existing notification producers inventoried
- migration status
- backend test results
- Prisma validation
- frontend build result
- Developer Hub in-system push receipt/evidence
- verified remote SHA
- deployment receipt
- preflight/health result
- live QA matrix
- realtime QA evidence
- Arabic/English screenshots
- Light/Dark screenshots
- desktop/narrow screenshots where possible
- any blocked gates stated precisely
- SHA256SUMS

Do not include credentials, cookies, tokens, private keys, raw DB URLs, or secret environment values.

---

# Final acceptance criteria

Phase 1 is complete only when:

- TNC is the Topbar Bell destination
- TNC feed is unified across existing generic Notification + TCS ChatNotification sources
- unified unread badge works
- read/unread lifecycle works
- mark all read works
- category filters work
- safe deep-link navigation works where source metadata supports it
- realtime updates work without manual refresh
- reconnect/visibility reconciliation works
- no duplicate notification database/system was created
- legacy notification consumers still work
- TCS unread/launcher behavior is not regressed
- Arabic/English and Light/Dark work
- production build/tests pass
- push is performed only through TOS Developer Hub / GitHub integration
- remote `TOS/main` SHA is verified
- production deploy/preflight passes
