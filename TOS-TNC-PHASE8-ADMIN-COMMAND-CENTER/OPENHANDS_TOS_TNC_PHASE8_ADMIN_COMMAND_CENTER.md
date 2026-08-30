# TOS TNC Phase 8 — Admin Command Center + Contract Cleanup

## Baseline
- Canonical repo: `mohamedamouseo-a11y/TOS`
- Branch: `main`
- Required remote baseline at task start: `73cc8417fc2afa6e7852b5fe5df8db72375baf00`
- Server target: `/var/www/TOS`

## Goal
Complete the next TNC phase by exposing the already-existing Phase 4 admin analytics/governance backend in the TNC frontend, while cleaning the remaining Phase 5 frontend contract defects. Do not redesign unrelated screens.

## Hard safety contract
- No new Prisma models.
- No DB migrations.
- No new scheduler, cron, interval, worker, PM2 process, lease authority, or background loop.
- Do not touch Auth.
- Do not touch GitHub Sync UI.
- Do not change existing notification backend behavior unless a concrete frontend/backend contract mismatch is proven.
- Prefer frontend-only changes; existing admin endpoints are already present.
- Preserve Phase 1–7 behavior.
- No archives, backups, ZIPs, `.bak` files, or unrelated changes.
- Local commit only. DO NOT PUSH.

## Phase 8A — contract cleanup
1. In `frontend/src/hooks/useTncNotifications.jsx` add `ACTION_CENTER` to the canonical `FILTERS` list so the existing Action Center UI can be selected through the provider contract.
2. In `frontend/src/components/TncNotificationCenter.jsx` remove the duplicated definitions of:
   - `toggleSelect`
   - `bulkMarkRead`
   - `bulkMarkUnread`
   Keep exactly one implementation of each.
3. Fix the existing TNC action refresh bug: the component-level `executeAction()` currently calls an undeclared `onRefresh?.()`. Replace that with the existing TNC `refresh()` contract after a successful action. Do not add a new prop just for this.
4. Keep the existing max bulk selection of 50.
5. Preserve Saved Views, Action Center, Rules, Acknowledgements, Digest, Preferences, Delivery, Templates, grouping, snooze, quiet hours, realtime and all existing filters.

## Phase 8B — frontend admin API wiring
Add these methods to `api.notificationCenter` in `frontend/src/lib/api.js`, using the already-existing backend routes exactly:
- `adminAnalytics(range = "30d", page = 1, limit = 50)` -> `GET /api/notification-center/admin/analytics`
- `adminRiskAnalytics(range = "30d", page = 1, limit = 50)` -> `GET /api/notification-center/admin/analytics/risk`
- `adminGovernance()` -> `GET /api/notification-center/admin/governance`
- `updateAdminGovernance(patch)` -> `PATCH /api/notification-center/admin/governance`
- `adminGovernanceAudit(limit = 50)` -> `GET /api/notification-center/admin/governance/audit`

Do not invent new route paths.

## Phase 8C — Admin Command Center UI
Create a focused admin panel for TNC, preferably as a small dedicated component such as `frontend/src/components/TncAdminCommandCenter.jsx`, and integrate it into the existing TNC preferences/admin area without rewriting `TncNotificationCenter.jsx`.

The panel must include:

### Analytics
- Range selector: 7d / 30d / 90d / 180d.
- KPI cards using existing response keys when present:
  - totalCreated
  - totalUnread
  - readRate
  - attentionBacklog
  - unreadUrgent
  - unreadImportant
  - activeEscalationCount / escalatedCount
  - digestGenerations
- Small breakdown summaries for source/category/priority if data exists.
- Do not add a charting dependency. Use compact native UI only.

### Operational Risk
- Show risk total.
- Render a compact risk list using the existing `risk.items` response.
- Show severity, type, title, priority, escalation level and created time when available.
- Empty state must be clean and explicit.

### Governance
Expose the existing governance settings as toggles/inputs, grouped logically:
- Automation: automationEnabled, digestEnabled, escalationEnabled, maxEscalationLevel, allowUrgentQuietHoursBypass
- Analytics: analyticsEnabled, analyticsMaxWindowDays
- Action Center: actionCenterEnabled, workflowActionsEnabled, bulkActionsEnabled, savedViewsEnabled
- Rules: rulesEngineEnabled, criticalAcknowledgementEnabled, roleDepartmentRoutingEnabled, ruleSimulationEnabled
- Delivery: deliveryOrchestrationEnabled, emailDeliveryEnabled, deliveryRetryEnabled, templateManagementEnabled, deliveryMonitorEnabled

Saving a governance change must use `PATCH /admin/governance` through the new API method and refresh local admin data after success.

### Audit
- Load `/admin/governance/audit`.
- Show recent governance changes with timestamp, action, actor metadata if present, and a compact before/after summary.
- Do not expose secrets or raw connection data.

## Authorization behavior
Backend is authoritative.
- Admin routes already return 403 for non-admin roles.
- Handle 403 cleanly in the UI with an admin-only state; do not loop requests and do not leak data.
- Do not weaken backend authorization.

## UX contract
- Reuse the current TNC visual language.
- Dark and Light modes must both work.
- Arabic/English labels must be supported for new visible UI.
- Responsive inside the existing TNC overlay.
- No page-level redesign.
- No overflow outside the TNC frame.

## Validation
Keep this phase focused. Maximum target time: 10–15 minutes.

Before commit:
1. Confirm baseline SHA and clean working tree.
2. Verify only intended TNC frontend files changed, unless a proven route contract blocker requires one minimal backend fix.
3. Run one focused frontend build.
4. Run the existing focused TNC frontend/unit test(s) if available; do not run a whole-repo test suite.
5. Smoke-check TNC open/close, normal feed, Action Center selection, Admin panel, governance load/save, analytics load, and Light/Dark rendering.
6. If backend route mismatch or schema issue appears, STOP and report blocker instead of broad changes.

## Commit
Create exactly one local commit:
`feat(tnc): add phase 8 admin command center`

DO NOT PUSH.
Deploy frontend only if the existing TOS workflow requires it for browser smoke verification. Do not restart backend unless an actual backend file was changed and validated.

## Return
Return only:

BASE_SHA=
FILES_CHANGED=
ACTION_CENTER_FILTER_FIXED=
DUPLICATE_FUNCTIONS_REMOVED=
ACTION_REFRESH_FIXED=
ADMIN_API_WIRED=
ANALYTICS_UI=
RISK_UI=
GOVERNANCE_UI=
AUDIT_UI=
ADMIN_403_HANDLED=
LIGHT_MODE=
DARK_MODE=
FRONTEND_BUILD=
TARGETED_TEST=
DEPLOYMENT=
COMMIT_SHA=
WORKTREE=
PUSH_PERFORMED=NO
BLOCKER=
