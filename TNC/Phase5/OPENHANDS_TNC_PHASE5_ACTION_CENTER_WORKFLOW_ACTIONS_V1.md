# TNC Phase 5 — Action Center + Safe Workflow Actions V1

## Execution target

Implementation repository: `mohamedamouseo-a11y/TOS`
Branch: `main`
Server working tree: `/var/www/TOS`
Prompt repository: `mohamedamouseo-a11y/TOS-Patchs`
Prompt local path: `/var/www/TOS-Patchs/TNC/Phase5/OPENHANDS_TNC_PHASE5_ACTION_CENTER_WORKFLOW_ACTIONS_V1.md`
Prompt GitHub URL: `https://github.com/mohamedamouseo-a11y/TOS-Patchs/blob/main/TNC/Phase5/OPENHANDS_TNC_PHASE5_ACTION_CENTER_WORKFLOW_ACTIONS_V1.md`

Remote TOS/main may intentionally lag behind the server working tree because the user performs Push manually after review. Do NOT reset the local working tree to remote.

Expected prerequisite on the server: TNC Phase 4 Analytics + Admin Governance is already implemented locally (`feat(tnc): add analytics and admin governance`, reported local SHA beginning `ac22f19`). Verify the actual local history and code before editing. If Phase 4 is not present locally, STOP and report BLOCKED instead of reimplementing or resetting.

## Mandatory workflow

You are OpenHands running with server/terminal access.

- Implement only in `/var/www/TOS`.
- Read this full specification before editing.
- Do NOT push TOS or TOS-Patchs to GitHub.
- Do NOT run `git push`, `gh`, SSH push, deploy-key push, or Developer Hub Push.
- The user will Push TOS manually from inside the system after review.
- You ARE responsible for deploying the completed implementation on the server.
- Browser/UI testing is unavailable in this OpenHands session. Do not pretend to perform browser QA.
- Preserve all existing TCS/TNC/TOS code and all newer local commits.
- Do NOT hard-reset, force-checkout old revisions, or revert unrelated work.
- Implement first. Avoid repeatedly running broad test suites while editing.
- At the end, perform one focused server-side validation pass. If something fails, fix only the specific issue and rerun affected checks.
- Create a local implementation commit only after validation.
- Deploy after successful validation/local commit.
- Final report must be written in the TOS-Patchs Phase 5 path, never in the TOS repository root.

---

# Mission

Build **TNC Phase 5 — Action Center + Safe Workflow Actions V1** on top of the existing Phase 1–4 architecture.

Phase 5 turns TNC from a passive notification inbox into a safe, auditable action surface without creating a second task/workflow engine.

The implementation must reuse existing domain services/routes and TNC models whenever possible. TNC must not become an alternate source of truth for Tasks, TCS, TWS, approvals, CRM entities, or any other business object.

---

# 1. Action Center

Add an **Action Center** view inside TNC for notifications that require or support a user action.

Requirements:

- Add normalized backend-authoritative action metadata to eligible TNC feed items.
- Add an `ACTIONS` / Action Center filter or tab in TNC.
- Show only actionable items in this view.
- Preserve existing All, Unread, Attention, Digest, TCS, Tasks, TWS, System views.
- Action Center must work with the existing unified Notification + ChatNotification feed; do not create a second feed.
- Action availability must be calculated on the backend, not trusted from arbitrary client metadata.

Each action descriptor should expose only safe presentation fields, for example:

```json
{
  "key": "...",
  "label": "...",
  "kind": "PRIMARY|SECONDARY|DESTRUCTIVE",
  "requiresConfirmation": true,
  "available": true,
  "reasonUnavailable": null
}
```

Do not expose arbitrary internal service names, SQL, raw backend routes, shell commands, or executable client-supplied payloads.

---

# 2. Safe action execution gateway

Create one TNC action execution API that is only a controlled gateway to existing authorized domain operations.

Suggested shape:

`POST /api/notification-center/:source/:notificationId/actions/:actionKey`

Exact route naming may differ if current route conventions require it.

Mandatory safety rules:

- Authenticate every request.
- Verify the notification belongs to the current recipient.
- Re-resolve the notification from the canonical source before execution.
- Recalculate action availability server-side at execution time.
- Verify domain-level authorization using the existing canonical permission/service path.
- Never execute a client-provided URL, function name, SQL, route path, model operation, or arbitrary payload.
- Never add a generic "execute anything" action engine.
- Return a stable normalized result.
- After a successful domain action, refresh/resolve the notification state naturally through existing source logic.

## Domain actions

Inspect existing TOS domain services and APIs first.

Expose workflow actions only where a canonical, already-authorized domain operation exists and can be safely reused. Examples may include existing task/approval/workflow operations if they actually exist in TOS.

Do NOT invent a fake task/approval mutation just to satisfy this phase.

If a business notification has no verified safe canonical action, expose only non-destructive TNC-native actions and/or `OPEN` deep-link behavior.

---

# 3. TNC-native actions

At minimum, normalize these existing safe TNC capabilities as actions where applicable:

- OPEN target/deep-link
- MARK_READ
- MARK_UNREAD
- MUTE_TYPE (where valid)
- SNOOZE notifications using the existing preference system

Do not duplicate the existing read/preferences implementation; call/reuse it.

---

# 4. Action idempotency and audit

Action execution must be auditable and safe against accidental duplicate submissions.

Requirements:

- Use a deterministic action identity derived from recipient + source + notification/native ID + action key + relevant target revision/state when available.
- Repeated identical requests must not perform the same irreversible domain mutation twice.
- If the canonical domain service already provides idempotency/state checks, reuse them.
- Persist a lightweight TNC action audit only if necessary for reliable idempotency/audit. Prefer a small additive Prisma model rather than overloading notification metadata.
- Never store secrets, passwords, access tokens, cookies, full request headers, or sensitive arbitrary payloads in audit records.

If a new model is required, it must be additive only. Suggested conceptual fields:

- id
- recipientId
- actorId
- source
- nativeId
- actionKey
- idempotencyKey (unique where appropriate)
- status (`STARTED|SUCCEEDED|FAILED|NOOP`)
- resultCode / safe metadata JSON
- createdAt / updatedAt

Use existing naming/style conventions after inspecting the Prisma schema.

---

# 5. Bulk inbox actions

Add safe bulk operations for selected TNC items without creating a separate bulk-processing architecture.

Required bulk operations:

- Mark selected notifications read
- Mark selected notifications unread

Optional only if safely supported by existing preference semantics:

- Mute the selected notification type(s)

Rules:

- Every selected item must be recipient-owned.
- Use bounded request sizes; do not accept unlimited IDs.
- Prefer one backend endpoint with a strict maximum batch size.
- Return per-item result summary where partial failures are possible.
- Do not make bulk destructive domain workflow actions in V1.

---

# 6. Saved Views

Allow users to save useful TNC filter presets without adding a new heavy subsystem.

Examples:

- Urgent Tasks
- TCS Mentions
- Unread TWS
- Attention Only

Requirements:

- Reuse `NotificationPreference.settings` JSON unless there is a strong technical reason not to.
- Store only bounded user-owned view definitions.
- Saved view schema must use allowed TNC filters only; no arbitrary query language or raw database filters.
- Support create/update/delete/select saved views.
- Respect existing Phase 2 user preferences and Phase 4 global governance.

---

# 7. Governance integration

Phase 5 must respect Phase 4 governance.

Add governance switches only if truly needed; do not create a second governance model.

Recommended capabilities inside the existing global notification governance document:

- `actionCenterEnabled`
- `workflowActionsEnabled`
- `bulkActionsEnabled`
- `savedViewsEnabled`

The server is authoritative.

If a capability is disabled globally:

- backend endpoints must reject/disable it safely
- frontend must present it as unavailable/hidden according to the existing Phase 4 pattern

Admin changes remain auditable through the existing Phase 4 governance audit mechanism.

---

# 8. Analytics integration

Extend Phase 4 analytics only with bounded, useful action metrics. Do not create another analytics system.

Add metrics such as:

- actionable notifications count
- action executions
- success / noop / failed counts
- top action keys (bounded)
- median/average time from notification creation to successful action where safely measurable

Respect the existing Phase 4 range limits (7d/30d/90d or current canonical ranges) and `analyticsEnabled` governance.

Queries must remain bounded and indexed where persistent action audit is introduced.

---

# 9. Frontend UX

Integrate Phase 5 into the existing `TncNotificationCenter` design language.

Requirements:

- Action Center tab/filter
- clear action buttons on eligible items
- confirmation for destructive/high-impact domain actions
- loading state per action; prevent duplicate rapid submission
- success/failure/no-longer-available feedback
- bulk selection mode with selected count
- bulk mark read/unread
- Saved Views UI
- Arabic + English
- RTL + LTR
- Light + Dark
- desktop + narrow responsive CSS/code support

Do not redesign TNC from scratch.

Browser QA cannot be performed by this OpenHands session. Build/compile frontend and document browser QA as BLOCKED, never PASS.

---

# 10. Realtime consistency

After an action changes the underlying notification/domain state:

- reuse current TNC/notification realtime mechanisms where appropriate
- do not introduce a second socket namespace
- do not emit duplicate unread events
- make UI refresh through current hooks/state architecture
- preserve TCS unread behavior

---

# 11. Performance and security

Mandatory:

- bounded lists and batch sizes
- recipient ownership checks
- backend-authoritative action resolution
- no arbitrary action execution
- no arbitrary query language for saved views
- no sensitive audit payloads
- no unbounded analytics scans
- no N+1 expansion that loads full domain entities for every notification if avoidable
- preserve Phase 3 scheduler lease/batching behavior
- preserve Phase 4 analytics/governance behavior

---

# 12. Expected implementation areas

Inspect actual local code before deciding exact files.

Likely areas include:

- `backend/src/routes/notificationCenter.routes.js`
- `backend/src/services/notificationCenter.service.js`
- new focused action service if appropriate
- `backend/src/services/notificationAnalytics.service.js` or current Phase 4 analytics service
- Phase 4 governance service
- Prisma schema/migration only if action audit is objectively required
- `frontend/src/hooks/useTncNotifications.jsx`
- `frontend/src/components/TncNotificationCenter.jsx`
- frontend API client

Do not modify unrelated TCS presentation/workflow code unless a regression fix is directly necessary and explained.

---

# 13. Focused final validation

Run once after implementation is complete.

Required server-side validation:

1. Phase 5 action resolver tests
2. recipient ownership/authorization rejection
3. stale/unavailable action rejection
4. duplicate/idempotent execution protection
5. no arbitrary client action execution
6. bulk read/unread bounded batch tests
7. Saved Views validation and ownership
8. governance disables action center/workflow/bulk/saved views server-side
9. Phase 4 governance/analytics regressions
10. Phase 3 automation/scheduler regressions
11. notification-center core regression tests
12. TCS unread/realtime regression tests relevant to TNC
13. Prisma validate/generate if schema changed
14. migration status if migration added
15. backend syntax/import/startup validation
16. frontend build
17. `git diff --check`
18. inspect `git status` and changed-file scope

Do not claim browser QA.

---

# 14. Local commit and deploy

After focused validation passes:

- Create local commit in `/var/www/TOS`.

Suggested message:

`feat(tnc): add action center and safe workflow actions`

- Do NOT push.
- Deploy using the canonical TOS production deployment flow already present on the server.
- Verify after deploy:
  - required PM2 process(es) online
  - backend local health/API reachable
  - public TOS HTTP endpoint no longer returns gateway/server errors
  - no startup/import errors caused by Phase 5
  - migration applied if required

If deploy fails, diagnose/fix before completing the task. Do not leave production in a known broken state.

---

# 15. Final report — mandatory

Create one normal Markdown report, NOT a ZIP, here:

`/var/www/TOS-Patchs/TNC/Phase5/TNC_PHASE5_ACTION_CENTER_WORKFLOW_ACTIONS_V1_REPORT.md`

Do NOT put this report in `/var/www/TOS`.
Do NOT push TOS-Patchs.

Report must include:

- `IMPLEMENTATION=PASS|FAIL|BLOCKED`
- `FINAL_VALIDATION=PASS|FAIL|BLOCKED`
- TOS START_SHA
- TOS FINAL_LOCAL_SHA
- local commit message
- exact changed files/count
- prerequisite Phase 4 verification
- action resolver design
- supported TNC-native actions
- verified domain workflow actions actually exposed (list exactly; do not fabricate)
- unsupported domain actions and why
- authorization/ownership design
- idempotency design
- action audit design/status
- bulk action design and batch limit
- Saved Views storage/schema
- governance integration
- analytics integration
- realtime behavior
- migration status
- exact test/check results
- frontend build result
- browser QA=`BLOCKED_NO_BROWSER_ACCESS`
- deployment commands/result
- PM2/backend/public health verification
- `PUSH_PERFORMED=NO`
- `DEPLOYMENT_PERFORMED=YES|NO`
- exact report path

Final OpenHands response must be concise and include:

- IMPLEMENTATION result
- FINAL_VALIDATION result
- FINAL_LOCAL_SHA
- changed file count
- migration status
- DEPLOYMENT_PERFORMED
- PUSH_PERFORMED=NO
- exact report path

The user will review and Push TOS manually after this task.