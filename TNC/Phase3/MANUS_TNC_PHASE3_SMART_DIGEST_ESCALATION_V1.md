# TNC Phase 3 — Smart Notifications + Digest + Escalation V1

## Mission
Implement Phase 3 of Tamayouz Notification Center (TNC) on top of the existing Phase 1 + Phase 2 architecture in the real production repository.

This phase MUST NOT create a second notification system, second socket system, or second inbox. It must extend the existing unified TNC built on `Notification` + `ChatNotification`, existing realtime (`tnc:notification` + `chat:notification`), Phase 2 per-user preferences, and the backend-authoritative presentation policy.

## Repositories / environment
- Prompt repository only: `mohamedamouseo-a11y/TOS-Patchs`
- Implementation repository: `mohamedamouseo-a11y/TOS`
- Branch: `main` only
- Worktree: `/var/www/TOS`
- Expected starting SHA: `0f5182dd7c6aa36a021ea87f8199e8149eed2494`
- Before editing, verify local HEAD and remote `main`. If remote `main` moved forward, inspect the delta and use the latest compatible `main`; never overwrite newer work.

## Existing architecture to preserve
- Generic notifications: existing `Notification`
- TCS notifications: existing `ChatNotification`
- Per-user TNC preferences: existing `NotificationPreference.settings` JSON
- Backend authoritative presentation policy: `evaluateNotificationPolicy()` / server-decorated `presentation`
- Unified TNC feed + unread/category counts
- Existing read/unread and grouped read actions
- Existing realtime event listeners; exactly one listener per event
- Existing safe target/deep-link resolution
- Existing Arabic/English, Light/Dark, desktop/mobile behavior
- Existing TCS unread behavior and Design Request notifications

# Scope

## 1. Smart Priority Engine
Create ONE backend-authoritative deterministic priority/attention engine.

The engine must classify each normalized TNC item using existing source/type/metadata/target/deadline/SLA information into at least:
- `NORMAL`
- `IMPORTANT`
- `URGENT`

Also return explainable machine-readable reasons, for example:
- `MENTION`
- `DIRECT_MESSAGE`
- `ASSIGNED_TO_ME`
- `DUE_SOON`
- `OVERDUE`
- `SLA_RISK`
- `SLA_BREACH`
- `APPROVAL_REQUIRED`
- `BLOCKER`
- `SECURITY_SYSTEM_ALERT`
- `REPEATED_ACTIVITY`

Requirements:
- Deterministic rules only in V1. Do NOT introduce an LLM dependency.
- Prefer explicit metadata/type/deadline/SLA evidence over title/body keyword guessing.
- Keyword fallback may exist only for legacy notifications with weak metadata and must be tested.
- Never downgrade an explicitly URGENT notification.
- Preserve the original notification row. Computed intelligence should be additive in the normalized TNC object, e.g. `intelligence: { priority, attentionRequired, reasons, dueAt, escalationLevel }`.
- The Phase 2 presentation policy must consume the effective smart priority where appropriate so user thresholds remain authoritative.
- One backend source of truth; do NOT reimplement smart priority rules in React.

## 2. Attention Center
Add an `ATTENTION` view/filter inside the existing TNC UI.

Attention contains items that require actual user action or time-sensitive awareness, such as:
- unread URGENT
- unread IMPORTANT with an actionable/deadline condition
- overdue/due-soon task/workflow notification
- pending approval requiring this user
- SLA risk/breach relevant to this user
- escalated unread item

UX requirements:
- Add clear `Attention` / `يحتاج انتباه` filter with exact count.
- Count must be exact and not capped by feed limit.
- Show reason chips (e.g. Overdue, Mention, Approval, SLA risk) without clutter.
- Sort attention intelligently: highest escalation/priority first, then nearest overdue/due time, then newest.
- Normal All/Unread/TCS/Tasks/TWS/System flows must remain unchanged.
- Do NOT auto-mark attention items read merely by opening the Attention filter.

## 3. Smart Deduplication + Entity Grouping
Improve grouping beyond only adjacent matching items.

Group semantically related notifications when they refer to the same real entity/context, for example:
- same conversation/thread
- same task
- same document/share
- same project/channel
- same approval/workflow request

Requirements:
- Grouping is presentation-only. Never merge/delete source notification rows.
- Preserve exact unread count semantics across grouped children.
- Group key must be deterministic from source/category/type/target/entity metadata.
- Respect existing per-user grouping enabled/window settings from Phase 2.
- Add safe limits so one group cannot create an unbounded payload.
- Group actions such as mark group read must continue to act on the real underlying rows.

## 4. Digest
Add an in-app Digest capability integrated into TNC.

### Digest modes
Support at least:
- `OFF`
- `DAILY`
- `WEEKDAYS`
- `WEEKLY`

Extend the existing per-user `NotificationPreference.settings` JSON for digest preferences; do not create a separate settings system.

Recommended preference shape (adapt as needed while preserving backwards compatibility):
```json
{
  "digest": {
    "mode": "DAILY",
    "time": "09:00",
    "timezone": "Africa/Cairo",
    "includeCategories": ["TCS", "TASKS", "TWS", "SYSTEM"],
    "minimumPriority": "NORMAL"
  }
}
```

Digest requirements:
- Digest is a summary of real notifications, not a replacement for source rows.
- Never mark underlying notifications read simply because they appeared in a digest.
- Generate concise grouped sections: Urgent, Needs attention, Tasks/approvals, TCS, TWS, System.
- Show counts plus a short list of the most relevant items and safe deep links.
- Provide `Digest` / `الملخص` view in the TNC UI.
- Provide `Generate now` / `إنشاء الملخص الآن` for deterministic on-demand QA.
- Scheduled generation/delivery must be idempotent and timezone-aware.
- Quiet Hours/Snooze can suppress intrusive presentation, but the digest itself must still preserve the underlying inbox data.
- No email/push/SMS delivery in V1 unless a production notification delivery abstraction already exists and can be reused safely. In-app Digest is mandatory; external channels are out of scope by default.

## 5. Escalation Engine
Implement safe, idempotent escalation for unread attention-worthy notifications.

### Default policy
Use configurable sensible defaults in existing per-user TNC settings, with admin/global policy allowed to constrain them:
- URGENT unread: first escalation after ~15 minutes
- IMPORTANT actionable unread: escalation after ~2 hours
- overdue/SLA breach: immediate attention state; escalation cadence must be bounded

Do not hardcode these as irreversible product constants; normalize/store policy in preference/global settings so they can evolve.

Escalation requirements:
- Escalation MUST NOT duplicate the original source notification row on every sweep.
- Track escalation state separately and idempotently.
- A minimal additive persistence model is allowed if objectively required, e.g. one compact `NotificationAutomationState` / `NotificationEscalationState` keyed by recipient + source + native notification ID.
- Do not mutate or fork `Notification` / `ChatNotification` architecture.
- Escalation must stop when the original notification becomes read or its actionable condition is resolved when that state can be safely proven.
- Escalation must respect ownership and authorization.
- Respect Phase 2 Mute/Snooze/Quiet Hours for intrusive alerts. The item may still appear in Attention while muted; no data should disappear.
- Urgent bypass may occur only according to the existing user/global policy.
- Bound retries/levels; no infinite alert loop.
- Server process restart must not duplicate escalations.

### Scheduler / sweep
Reuse an existing backend scheduler/job infrastructure if present.
If none exists, add the smallest production-safe idempotent sweep mechanism with clear startup/shutdown behavior and a conservative interval (for example one minute). Do not create a second process unless necessary.

Expose a development/QA-safe authenticated/manual sweep endpoint only if needed for deterministic testing; it must not be broadly dangerous and must enforce authorization.

## 6. Actionable Notifications
Expose safe actions on Attention/Digest cards where the target operation already exists in production and authorization can be enforced.

Examples:
- Open conversation/task/document
- Mark notification read/unread
- Open approval/task action screen
- Mark task done ONLY if an existing authorized task completion endpoint exists and the notification unambiguously targets that task
- Approve/reject ONLY if an existing authorized workflow endpoint exists and the user has permission

Rules:
- Do NOT invent generic mutation endpoints.
- Never execute arbitrary action descriptors from notification metadata.
- Whitelist action types server-side.
- Reuse existing domain endpoints/services and their permission checks.
- If a safe direct action cannot be proven, show only `Open` deep-link.
- Successful direct action should reconcile TNC state without refresh where possible.

## 7. Preference UI extensions
Extend the existing TNC Preferences panel, not a new settings page/system.

Add controls for:
- Digest mode/time/timezone/categories/minimum priority
- Escalation enable/disable
- Urgent escalation delay
- Important actionable escalation delay
- Maximum escalation level/repeat bound

Requirements:
- Normalize/validate all values server-side.
- Backwards-compatible defaults for existing users.
- Preserve Phase 2 mute/snooze/quiet-hours/grouping/threshold controls.
- Arabic + English labels.
- Light + Dark.
- Responsive within the current internal TNC window.

## 8. API design
Extend the current `/api/notification-center` family; do not create a parallel top-level notification API.

Possible endpoints (adapt to project conventions):
- `GET /api/notification-center?category=ATTENTION`
- `GET /api/notification-center/attention`
- `GET /api/notification-center/digest`
- `POST /api/notification-center/digest/generate`
- `POST /api/notification-center/actions/:actionId` only if server-side whitelisted actions are implemented
- existing preferences PATCH for new digest/escalation settings

All endpoints:
- authenticated
- recipient-scoped
- safe input validation
- no cross-user data leakage
- deterministic response shape

## 9. Realtime integration
Preserve exactly the existing socket listeners.

On new `tnc:notification` / `chat:notification`:
- rehydrate/reconcile the unified feed/counts as today
- use server-authoritative presentation/intelligence
- update Attention count immediately
- do not create a second socket channel merely for Phase 3
- if an escalation or digest snapshot causes an in-app state change, prefer the existing TNC/state-sync mechanisms rather than adding duplicate listeners

## 10. Database rules
Prefer extending `NotificationPreference.settings` JSON for user configuration.

A single minimal additive Prisma migration is allowed only for durable escalation/digest automation state if required.

Forbidden:
- destructive migrations
- copying Notification/ChatNotification into a new inbox table
- dropping or rewriting existing notification data
- creating a second unread/read source of truth

## 11. Tests — mandatory
Add strong automated tests covering at least:

### Smart priority
- explicit urgent remains urgent
- mention/direct assignment/action-required rules
- due soon/overdue/SLA risk/breach
- weak legacy fallback is bounded
- no frontend duplicate evaluator

### Attention
- exact counts beyond 100 items
- correct ordering
- read items leave attention when appropriate
- muted/snoozed item remains in inbox/attention data but intrusive alert is suppressed

### Grouping/dedup
- same entity groups correctly
- different entity never groups accidentally
- unread counts remain exact
- mark-group-read updates real rows

### Digest
- daily/weekday/weekly normalization
- timezone handling
- generate-now output
- idempotent scheduled generation for same time bucket
- digest does not mark source notifications read
- category/priority preferences respected

### Escalation
- urgent/important timing
- overdue/SLA immediate attention
- stop after read/resolved
- restart/idempotency/no duplicate escalation for same level
- max level/retry bound
- mute/snooze/quiet-hours suppression of intrusive alert while preserving attention/inbox state
- recipient isolation

### Actions
- unauthorized/cross-user action rejected
- unsupported arbitrary metadata action rejected
- safe deep link remains fallback

### Regression
- existing Phase 1 counts/filters/read/unread
- Phase 2 preferences/presentation-policy tests
- one socket listener per existing event
- TCS realtime/unread behavior
- frontend build
- Prisma validation if schema changed

## 12. Live QA matrix
After push/deploy, verify in production with an authenticated session where available:
- Bell opens existing TNC
- Attention filter/count
- All/Unread/TCS/Tasks/TWS/System still work
- Smart priority/reason chips
- Digest generate now
- Digest preference persistence after reload
- escalation preference persistence after reload
- grouped notifications + group read
- safe Open action
- one real safe direct action only if supported
- Arabic/English
- Light/Dark
- desktop/mobile or narrow internal TNC viewport
- browser console free of TNC render/runtime errors
- realtime new notification updates unread + Attention without manual refresh

If browser transport is unavailable, report the live QA gate honestly as blocked. Do NOT invent screenshots or claim PASS.

# Deployment / push policy — mandatory
- Work inside `/var/www/TOS`.
- Commit implementation locally.
- DO NOT use terminal `git push`.
- DO NOT push via SSH, GH CLI, Deploy Key, or any external workaround.
- Push ONLY from inside the running TOS using Developer Hub / GitHub integration.
- Target: `mohamedamouseo-a11y/TOS` → `main`.
- Verify remote `main` SHA after the in-system push.
- Deploy only after successful in-system push.
- Deploy minimum required scope; backend + frontend if both changed.
- If Prisma schema changes, run the production-safe migration path before/with backend deploy according to the existing deployment script/process.
- Run production preflight/health checks after deploy.

# Scope discipline
Do NOT touch legacy root `client/`, `server/`, or `drizzle/` stacks.
Do NOT refactor unrelated TCS/TWS/HR/operations functionality.
Do NOT replace existing TNC UI wholesale unless necessary; extend it coherently.
Do NOT introduce an LLM dependency in V1.
Do NOT create external notification channels by default.

# Required report
Return exactly:
`TNC_PHASE3_SMART_DIGEST_ESCALATION_V1_REPORT.zip`

The ZIP must contain a markdown report plus evidence/receipts and screenshots when live browser QA succeeds.

Report must state:
- START_SHA
- FINAL_SHA
- commits created
- exact files changed
- whether Prisma migration was added and why
- smart-priority rules implemented
- Attention behavior/count QA
- grouping/dedup behavior
- digest behavior and idempotency evidence
- escalation timing/state/idempotency evidence
- direct actions implemented vs deep-link-only fallback
- automated test commands/results
- frontend build result
- Prisma/migration result
- Developer Hub in-system push evidence
- verified remote SHA
- deploy result
- production preflight result
- live QA matrix with PASS/FAIL/BLOCKED per item
- browser limitation if any
- any remaining known risks

Final status must be one of:
- `PASS`
- `PASS_WITH_BLOCKED_LIVE_QA`
- `FAIL`

Do not call the phase PASS if automated correctness, remote push verification, or deployment failed.