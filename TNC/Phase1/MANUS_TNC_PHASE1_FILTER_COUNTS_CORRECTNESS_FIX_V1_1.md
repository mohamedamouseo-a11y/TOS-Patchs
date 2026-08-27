# Manus — TNC Phase 1 Filter/Counts Correctness Fix V1.1

## Scope
Fix a correctness defect found during review of TNC Phase 1 after commit `645c48fc99944d250035d173510f09c5fabf2362` in `mohamedamouseo-a11y/TOS`.

Work only in the canonical production repository/worktree:
- Workdir: `/var/www/TOS`
- Repository: `mohamedamouseo-a11y/TOS`
- Branch: `main`
- Required base SHA: `645c48fc99944d250035d173510f09c5fabf2362`

Do not touch the legacy root `client/`, `server/`, or `drizzle/` stack.

## Confirmed defect
`backend/src/services/notificationCenter.service.js` computes `categoryUnreadCounts` for generic notifications from only the newest `MAX_LIMIT` (100) unread rows. This makes category counts wrong when a user has more than 100 unread generic notifications. Live Phase 1 QA already exposed this: unified unread count was 237 while TASKS showed 100.

The same service also fetches at most 100 generic rows and applies the requested category filter after retrieval. Therefore a category feed may omit valid older matching notifications if newer rows from other categories consume the bounded fetch window. `genericWhereForCategory()` exists but the current fetch path does not use category-aware retrieval. `hasMore` can consequently be inaccurate for category-filtered feeds.

## Required result
Make TNC category counts and category-filtered feed semantics correct independently of the 100-item response/display cap.

### 1. Exact unread category counts
- `ALL` / `UNREAD` must remain the exact total unread count across generic Notification + ChatNotification.
- `TCS` must remain the exact unread ChatNotification count.
- `TASKS`, `TWS`, and `SYSTEM` must reflect ALL unread generic notifications for the authenticated user, not only the newest 100.
- Do not silently cap category counts at 100.
- Preserve the existing `categoryForGenericNotification()` classification contract unless a clearly equivalent refactor is needed.

### 2. Correct category feed retrieval
For `TASKS`, `TWS`, and `SYSTEM`, the returned newest-first feed must be able to find matching generic notifications even when the newest 100 generic rows contain mostly other categories.

Implement a bounded, production-safe strategy. Preferred approaches:
- database-side category candidate filtering where it is semantically equivalent; and/or
- chunked/paginated newest-first scanning until enough matching rows are collected or the source is exhausted.

Do NOT solve correctness by returning an unbounded full notification payload to the browser.

### 3. Correct `hasMore`
`hasMore` must represent whether more matching items exist for the active filter, rather than whether the pre-filter source fetch happened to exceed the UI limit.

### 4. Preserve architecture
- No new notification table.
- No Prisma schema migration unless objectively unavoidable; this fix should not require one.
- Preserve both source tables: `Notification` and `ChatNotification`.
- Preserve `tnc:notification` and existing `chat:notification` realtime architecture.
- Preserve legacy `api.users.notifications()` compatibility for Design Request alerts.
- Preserve TCS global unread behavior.
- Do not redesign the TNC UI in this fix.

## Mandatory tests
Extend `backend/src/services/notificationCenter.service.test.js` with deterministic regression cases that would fail before this fix, including at minimum:
1. More than 100 unread generic TASKS notifications => TASKS count is exact (>100), not capped at 100.
2. Mixed categories where matching TASKS/TWS/SYSTEM notifications fall beyond the first 100 newest generic rows => requested category feed still returns the correct matching items in newest-first order.
3. Category-specific `hasMore` true when additional matching rows exist and false when exhausted.
4. Existing recipient scoping / cross-user mutation protections remain passing.
5. Existing mark-read / mark-unread / mark-all behavior remains passing.
6. Existing chatUnreadScope regression tests remain passing.

Run:
- focused TNC backend tests
- existing chatUnreadScope tests
- Prisma validation
- Node syntax checks for changed backend files
- frontend build if any frontend file changes (prefer backend-only for this fix)
- `git diff --check`

## Live QA
After deploy, verify with the currently authenticated production account if safe:
- unified unread count remains correct
- TASKS/TWS/SYSTEM counts are no longer truncated to 100
- switching filters returns matching rows without obvious omissions
- read/unread still reconciles badge and category counts

Do not bulk mark all production notifications merely for QA.

## Commit / Push / Deploy
- Commit locally in `/var/www/TOS`.
- DO NOT use terminal `git push`.
- DO NOT use SSH push, GH CLI push, or Deploy Key push.
- Push ONLY through the running TOS Developer Hub / GitHub integration.
- Push to `mohamedamouseo-a11y/TOS` branch `main`.
- Verify GitHub remote SHA equals the local approved commit before deployment.
- Deploy backend only if frontend is unchanged; otherwise deploy the minimum required canonical scope.
- Run canonical runtime preflight after deployment.

## Deliverable
Return:
`TNC_PHASE1_FILTER_COUNTS_CORRECTNESS_FIX_V1_1_REPORT.zip`

The report must include:
- START_SHA / FINAL_SHA / remote SHA
- exact changed files
- regression test output
- proof no schema migration was added
- Developer Hub in-system push confirmation/evidence
- deployment + preflight result
- live count/filter QA observations
- any blocked gate stated explicitly without fabricating PASS.