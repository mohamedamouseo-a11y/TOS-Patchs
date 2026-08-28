# TNC Phase 4 — Analytics + Admin Governance V1

## Execution target

Implementation repository: `mohamedamouseo-a11y/TOS`
Branch: `main`
Server working tree: `/var/www/TOS`
Prompt repository: `mohamedamouseo-a11y/TOS-Patchs`
Prompt local path: `/var/www/TOS-Patchs/TNC/Phase4/OPENHANDS_TNC_PHASE4_ANALYTICS_ADMIN_GOVERNANCE_V1.md`
Prompt GitHub URL: `https://github.com/mohamedamouseo-a11y/TOS-Patchs/blob/main/TNC/Phase4/OPENHANDS_TNC_PHASE4_ANALYTICS_ADMIN_GOVERNANCE_V1.md`

Current remote TOS main observed when this prompt was authored: `618e25d6837144cf34582bdf01d74f0ddd172adf`.
This is informational only. Before editing, inspect the actual current `/var/www/TOS` HEAD and preserve every newer unrelated commit/change.

## Workflow rules — mandatory

You are OpenHands running through server/terminal commands.

- Work only in `/var/www/TOS` for implementation.
- Read this full specification before editing.
- Do NOT push to GitHub from OpenHands.
- Do NOT use `git push`, `gh`, SSH push, deploy keys, or Developer Hub Push.
- The user will Push TOS manually from inside the TOS system after review.
- You ARE responsible for deploying the completed local implementation on the server.
- Do not perform browser/UI testing because this OpenHands session has server/terminal access only.
- Preserve all TCS/TNC/TOS work already present. Do not reset, hard-reset, force checkout old revisions, or revert unrelated work.
- Implement first. Do not repeatedly run large test suites during editing.
- At the end, run one focused server-side validation pass. If a check fails, fix the specific failure and rerun only the affected checks.
- Create local implementation commit(s) only after validation. Prefer one clean implementation commit unless a small follow-up test/fix commit is objectively clearer.
- Deploy after successful server-side validation/local commit.
- Generate the final report in the PATCHES repository path specified at the end, never in the TOS repository root.

---

# Mission

Build **TNC Phase 4 — Analytics + Admin Governance V1** on top of the existing TNC Phase 1/2/3 architecture.

Phase 4 must add operational visibility and safe administrator governance without creating a second notification platform.

The existing canonical sources must remain:

- `Notification`
- `ChatNotification`
- `NotificationPreference`
- `NotificationAutomationState`
- `NotificationAutomationLease`
- existing TNC realtime events and hooks
- `OperationsSettings.notificationSettings` as the global/admin policy upper-bound

Do NOT introduce a second inbox, unread truth, notification event bus, socket channel, or preference system.

No LLM/AI dependency is required for Phase 4.

---

# 1. Admin authorization boundary

All cross-user analytics and governance functions must be server-authorized.

Use the existing administrator roles/patterns already used by TOS. At minimum preserve compatibility with the current TNC admin gate (`ADMIN`, `SUPER_ADMIN`, `SYSTEM_ADMIN`, `OWNER`) unless the repository has a stronger central permission helper that should be reused.

Requirements:

- Normal users must never query organization-wide notification analytics.
- Normal users must never read or mutate global notification governance settings.
- Never trust frontend role checks as authorization.
- Recipient/user IDs from request data must never allow horizontal access.
- Admin endpoints must validate ranges, enums, dates, pagination and limits server-side.

---

# 2. TNC Analytics — backend authoritative

Add an admin analytics service using the existing notification data, not copied analytics tables unless objectively required.

Default windows:

- 7 days
- 30 days
- 90 days
- bounded custom range

Recommended maximum custom range for V1: 180 days unless an existing repository convention suggests a safer value.

Analytics should include, where the source data objectively supports them:

## Core KPIs

- total notifications created
- total unread
- total read
- read rate
- median time-to-read
- p90 time-to-read
- Attention backlog
- unread IMPORTANT count
- unread URGENT count
- escalated notification count
- currently active escalation count
- digest generations
- users with Digest enabled
- users with Escalation enabled

## Breakdowns

- by source: generic Notification / TCS ChatNotification
- by TNC category: TCS / TASKS / TWS / SYSTEM
- by effective priority: NORMAL / IMPORTANT / URGENT
- by notification type
- daily trend for the selected period

## Operational risk / missed-critical view

Provide a bounded admin view for notifications that need operational attention, such as:

- unread URGENT older than the configured urgent escalation delay
- unread IMPORTANT actionable items older than configured important delay
- overdue / SLA breach reasons
- active escalation state

This view must be read-only operational visibility in V1. Do not create new source notifications to represent analytics rows.

## Correctness

- Analytics must use the existing backend-authoritative smart priority/intelligence logic where priority classification is needed.
- Do not reproduce a separate priority evaluator in React.
- Do not mark notifications read while computing analytics.
- Digest generation must not be triggered by analytics reads.
- Analytics must never mutate source rows.

---

# 3. Analytics performance and bounded queries

Do not load the complete Notification and ChatNotification tables into Node memory for organization analytics.

Requirements:

- Prefer Prisma/SQL aggregation at the database layer.
- Bound date windows.
- Bound top notification types and risk-list rows.
- Paginate operational/risk lists.
- Avoid N+1 user loops for organization metrics.
- Reuse existing indexes where possible.
- If a missing index objectively causes unsafe full scans for the new common query patterns, add only the minimal additive index migration and explain it in the final report.
- Never add destructive migrations.

Exact count semantics are required for KPI totals inside the selected bounded range; do not cap KPI counts at 100/999.

---

# 4. Admin Governance — one global policy system

Extend the existing global notification policy under `OperationsSettings.notificationSettings`.

Do NOT add a parallel global settings table just for TNC.

Preserve existing fields and backward compatibility:

- `inAppEnabled`
- `realtimeUpdatesEnabled` if currently used
- `soundEnabled`
- `desktopNotifications`
- `systemAlertsEnabled`

Add/normalize a governance section only where needed. Recommended V1 shape:

```json
{
  "governance": {
    "automationEnabled": true,
    "digestEnabled": true,
    "escalationEnabled": true,
    "maxEscalationLevel": 5,
    "allowUrgentQuietHoursBypass": true,
    "analyticsEnabled": true,
    "analyticsMaxWindowDays": 180
  }
}
```

Treat the global settings as an **upper-bound**, not a replacement for per-user preferences.

Examples:

- If global Digest is disabled, a user preference cannot re-enable scheduled Digest.
- If global Escalation is disabled, user escalation preference cannot re-enable it.
- Global max escalation level caps the user's selected max level.
- If global urgent quiet-hours bypass is disabled, a user cannot bypass Quiet Hours for URGENT presentation.
- Global disabling of intrusive presentation must not delete or hide inbox data.

Use safe normalization with backward-compatible defaults so existing deployments behave the same immediately after migration/deploy unless an admin changes the new governance controls.

Do NOT silently change current production behavior through new defaults.

---

# 5. Governance audit trail

Every administrator mutation to notification governance must be auditable.

First inspect the repository for an existing general audit/activity log that safely supports:

- actor user ID
- action/type
- before state
- after state
- timestamp
- optional metadata/source

If an existing safe audit mechanism exists, reuse it.

Only if no suitable reusable audit persistence exists, add one minimal additive TNC governance audit model/table.

Never store secrets, tokens, cookies, authorization headers, connection strings or full sensitive request objects in audit payloads.

Admin analytics should be able to show a bounded recent governance-change history (for example latest 50 entries) if implementation is safe and simple.

---

# 6. API design

Extend the existing `/api/notification-center` route family. Do not create a parallel notification API namespace.

Recommended endpoints (names may be adjusted to existing conventions):

- `GET /api/notification-center/admin/analytics?range=30d`
- `GET /api/notification-center/admin/analytics/risk?...`
- `GET /api/notification-center/admin/governance`
- `PATCH /api/notification-center/admin/governance`
- `GET /api/notification-center/admin/governance/audit`

Requirements:

- admin-only server authorization
- bounded query inputs
- strict normalization
- no arbitrary dynamic SQL from request values
- no recipient data leakage
- deterministic response schemas
- clear empty-state responses

Do not expose raw internal metadata if it contains information unnecessary for analytics presentation.

---

# 7. TNC UI — Analytics + Governance

Add admin-only Phase 4 UI inside the existing TNC experience rather than building a separate unrelated admin application.

Recommended design:

- an admin-only `Analytics` view/tab
- an admin-only `Governance` view/tab
- keep the existing All / Unread / Attention / Digest / TCS / Tasks / TWS / System experience unchanged for normal users

Analytics UI should include:

- KPI cards
- period selector (7d / 30d / 90d; custom only if cleanly implementable)
- compact daily trend visualization without adding a heavy chart library unless one already exists
- category/source/priority breakdown
- operational risk/missed-critical list with safe pagination

Governance UI should include:

- current global policy state
- Phase 4 governance controls
- clear explanation that global controls cap user preferences
- recent governance audit history if available

Requirements:

- Arabic + English
- Light + Dark
- responsive desktop/mobile layout
- accessible labels/buttons
- preserve current TNC visual language
- no browser-specific QA claims from OpenHands

Do not duplicate backend policy logic in React. Frontend only displays authoritative backend values and sends validated intent.

---

# 8. Realtime and cache behavior

Phase 4 must not create a new socket channel.

Analytics does not need per-event realtime streaming in V1.

Use explicit refresh and/or existing TNC rehydrate mechanisms where appropriate.

Governance changes that affect presentation/automation must become effective server-side without requiring a frontend-only rule update.

If the backend caches OperationsSettings/global policy, use the existing safe invalidation/reload mechanism.

---

# 9. Scheduler integration

Phase 3 Scheduler Hardening must remain intact.

Governance must integrate with the existing hardened scheduler:

- global `automationEnabled=false` safely skips scheduled automation work
- global `digestEnabled=false` prevents scheduled digest generation
- global `escalationEnabled=false` prevents escalation actions
- global max escalation level caps escalation behavior
- global policy must be read efficiently (once per sweep where possible, not once per notification)
- preserve durable `NotificationAutomationLease`
- preserve batching and idempotency
- do not weaken the multi-instance lease

Manual `Generate Now` Digest behavior must be explicitly defined and tested when global Digest is disabled. Preferred V1 behavior: admin/global disable is authoritative, so Generate Now returns a clear policy-disabled result rather than bypassing governance.

---

# 10. Data integrity / migration policy

- No destructive schema changes.
- No copied Notification/ChatNotification analytics table in V1.
- No second unread truth.
- No historical backfill job unless objectively necessary.
- Reuse `OperationsSettings.notificationSettings` JSON for governance configuration.
- One minimal additive migration is allowed only for a missing audit facility and/or objectively required analytics indexes.
- Every migration must be safe on existing production data and documented.

---

# 11. Mandatory server-side tests — run at final validation only

Do not repeatedly execute the whole suite during implementation.

At the end run focused tests covering at minimum:

## Analytics

- admin can access organization analytics
- normal user receives 403
- bounded date-range validation
- exact counts across Notification + ChatNotification fixtures
- read rate correctness
- median/p90 time-to-read correctness
- Attention/URGENT/IMPORTANT backlog correctness
- category/source/priority breakdown correctness
- risk list recipient/data isolation and pagination
- analytics reads do not mutate source notifications

## Governance

- admin read/update allowed
- normal user forbidden
- invalid governance values normalized/rejected safely
- backward-compatible defaults
- global policy remains upper-bound over user preference
- global digest disable blocks scheduled + Generate Now behavior as specified
- global escalation disable skips escalation
- global max escalation level caps user max
- global urgent quiet-hours bypass restriction is enforced server-side
- audit event written on successful admin mutation
- audit does not contain secrets

## Scheduler regression

- durable lease still prevents concurrent sweep ownership
- lease recovery still works
- batching preserved
- duplicate digest bucket prevention preserved
- escalation repeat/idempotency preserved

## Existing TNC regressions

Run the existing focused TNC Phase 2/3 notification-center, preferences, intelligence and automation tests relevant to changed modules.

Run relevant TCS unread/realtime regression tests if shared notification-center code was touched.

Also run:

- Prisma validate
- Prisma generate if schema changed
- backend syntax/import validation
- frontend production build because Phase 4 adds frontend UI

Do NOT claim browser QA; browser QA is outside this OpenHands server-only execution.

---

# 12. Local commit and deployment

After final validation passes:

1. Review `git diff` and changed-file list.
2. Ensure no unrelated files were modified.
3. Create local TOS commit(s).

Suggested primary commit message:

`feat(tnc): add analytics and admin governance`

4. DO NOT PUSH.
5. Deploy from the server using the repository's existing production deployment procedure/script.
6. Verify after deployment using server-side checks only:
   - PM2/process health
   - backend startup without migration/runtime errors
   - database connectivity
   - migration status if a migration was added
   - relevant HTTP/API health endpoint if safely callable locally

Do not run browser/UI automation.

---

# 13. Final report — mandatory and must live in TOS-Patchs

Do NOT put the execution report in the TOS repository.

Create this normal Markdown file:

`/var/www/TOS-Patchs/TNC/Phase4/TNC_PHASE4_ANALYTICS_ADMIN_GOVERNANCE_V1_REPORT.md`

This is the required report location.

If `/var/www/TOS-Patchs` is a git checkout, leave the report there ready for the user to sync/push separately. Do NOT push the patches repository yourself.

The report must contain:

## Status

- `IMPLEMENTATION=PASS|FAIL`
- `FINAL_VALIDATION=PASS|FAIL`
- `LOCAL_COMMIT=PASS|FAIL`
- `DEPLOYMENT_PERFORMED=YES|NO`
- `PUSH_PERFORMED=NO`
- `BROWSER_QA=NOT_PERFORMED_SERVER_ONLY`

## Git

- TOS START_SHA
- TOS FINAL_LOCAL_SHA
- local commit message(s)
- exact changed files
- `git diff --stat` summary
- final TOS working tree status

## Analytics implementation

- metrics implemented
- formulas/semantics for read rate, median, p90, backlog and risk
- date window limits
- pagination/bounds
- DB query strategy
- indexes added or explicitly `NONE`

## Governance implementation

- existing global policy fields preserved
- new governance fields/defaults
- how upper-bound behavior is enforced
- Digest global-disable behavior
- Escalation global-disable behavior
- max escalation cap behavior
- urgent quiet-hours governance behavior
- admin authorization

## Audit

- reused existing audit mechanism OR new minimal model
- exact persistence used
- proof that secrets are excluded

## Validation

For every final check include command + PASS/FAIL + concise result.

## Deployment

- deployment command/script
- migration deployment result
- PM2/process result
- backend health result
- any warnings/blockers

## Explicit next action

Include exactly:

`PUSH_PERFORMED=NO`

`USER_ACTION_REQUIRED=Review this report and the local TOS commit, then Push TOS manually from inside the TOS system. After Push, ask ChatGPT to verify mohamedamouseo-a11y/TOS main.`

---

# Final OpenHands response

When complete, return only a concise execution summary containing:

- IMPLEMENTATION result
- FINAL_VALIDATION result
- TOS FINAL_LOCAL_SHA
- changed file count
- migration status
- DEPLOYMENT_PERFORMED
- PUSH_PERFORMED=NO
- exact report path:
  `/var/www/TOS-Patchs/TNC/Phase4/TNC_PHASE4_ANALYTICS_ADMIN_GOVERNANCE_V1_REPORT.md`

Do not say the work is remotely complete because Push is intentionally the user's responsibility.