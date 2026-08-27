# Manus — TNC Phase 2 Policy Sync Fix V1

## Objective
Fix the TNC Phase 2 presentation-policy architecture and startup race without changing the delivered UX or notification data model.

## Repositories
Prompt repository only: `mohamedamouseo-a11y/TOS-Patchs`

Implementation repository: `mohamedamouseo-a11y/TOS`

Branch: `main`

Work inside: `/var/www/TOS`

Current verified remote base SHA: `d98214837846b92797b47709006f0980d2794b04`

## Confirmed issue
Phase 2 currently has the policy rules duplicated in two places:
- backend: `evaluateNotificationPolicy(...)` in `backend/src/services/notificationPreferences.service.js`
- frontend: an independent `policyFor(...)` implementation in `frontend/src/hooks/useTncNotifications.jsx`

This violates the intended single server-side presentation-policy source of truth and creates drift risk.

There is also a startup race: preferences are hydrated asynchronously while the inbox feed hydrates at the same time. The first feed hydration can evaluate new/unread items with frontend default preferences before the user's persisted mute/snooze/quiet-hours settings arrive, which can surface an intrusive alert that should have been suppressed.

## Required fix
1. Make the backend `evaluateNotificationPolicy(...)` the single authoritative evaluator for presentation decisions.
2. Remove the duplicated frontend policy implementation and any duplicated priority/quiet-hours/snooze presentation decision logic that exists only to decide whether to show an alert.
3. Ensure feed items used by TNC can carry a server-evaluated presentation result, for example:
   - `inbox`
   - `alert`
   - `sound`
   - `desktop`
   - `suppressedBy`
   Use the existing evaluator and the authenticated user's persisted preferences plus `OperationsSettings.notificationSettings` global policy.
4. For raw `chat:notification` realtime events, do NOT trust a duplicated client evaluator. Before showing the intrusive global alert, obtain the authoritative backend presentation decision through the cleanest minimal path. Acceptable patterns include a small authenticated presentation-evaluate endpoint or another server-derived result that reuses the same evaluator. Do not create a second policy engine.
5. For generic `tnc:notification`, keep the current feed rehydrate flow, but the resulting alert decision must come from server-evaluated presentation data.
6. Eliminate the startup race completely. A muted/snoozed/quiet-hours user must never get an intrusive alert during initial page/provider hydration merely because the frontend temporarily had default preferences.
7. Preserve all inbox rows, unread counts, category counts, realtime hydration, reconnect/visibility recovery, deep links, TCS unread/launcher behavior, grouping, grouped-read action, and all Phase 2 preference controls.
8. Muting/snoozing/quiet hours/priority thresholds affect intrusive presentation only; they must not delete or hide the notification from the TNC inbox and must not decrement unread counts.
9. Preserve existing `Notification` + `ChatNotification` models and `chat:notification` + `tnc:notification` events.
10. No new notification database, no duplicate socket system, no destructive DB changes, and no new Prisma migration for this fix unless absolutely unavoidable. Prefer zero schema changes.
11. Do not implement automatic browser notification permission requests or fragile sound behavior. Existing sound/desktop capability policy can remain safely unsupported/disabled where currently unsupported.
12. Preserve Arabic/English, Light/Dark, Desktop/Mobile.

## Validation
Add/extend deterministic tests proving at minimum:
- category mute suppresses alert but keeps inbox/unread.
- exact type mute suppresses alert but keeps inbox/unread.
- snooze suppresses alert but keeps inbox/unread.
- quiet hours including overnight windows suppress correctly.
- urgent bypass works only when configured.
- priority threshold works.
- global admin policy remains authoritative.
- feed presentation result is server-evaluated for the authenticated user.
- initial hydration cannot alert using default preferences before persisted preferences are known.
- realtime TCS/chat alert path uses the backend-authoritative policy result.
- generic TNC realtime rehydrate uses backend-authoritative policy result.
- no duplicate listeners / no unread double counting.

Run the relevant backend/TNC tests, existing chat unread-scope tests, Prisma validation/status, frontend production build, and production preflight.

## Push and deploy policy
- Commit locally.
- DO NOT use terminal `git push`.
- DO NOT use SSH / GH CLI / Deploy Key.
- Push ONLY from inside the running TOS system via Developer Hub / GitHub integration.
- Push to `mohamedamouseo-a11y/TOS` → `main`.
- Verify the final remote SHA and `AHEAD 0 / BEHIND 0 / REMOTE ✓` before deployment.
- Deploy both backend and frontend only after successful in-system push because this fix affects policy API/backend and frontend consumption.

## Guardrails
Do not touch legacy root stacks: `client/`, `server/`, `drizzle/`.
Do not refactor unrelated TCS/TWS/TNC code.
Do not remove Phase 2 functionality that already passed.

## Deliverable
Return:
`TNC_PHASE2_POLICY_SYNC_FIX_V1_REPORT.zip`

The report must include:
- final remote SHA
- changed files
- test/build results
- Developer Hub push receipt
- deploy/preflight evidence
- explicit proof that frontend no longer owns a duplicated presentation-policy evaluator
- explicit proof that muted/snoozed startup hydration cannot surface a false alert
