# TNC Phase 5.1 — Frontend + Integration Completion V1

## Execution target

Implementation repository: `mohamedamouseo-a11y/TOS`
Branch: `main`
Server working tree: `/var/www/TOS`
Prompt repository: `mohamedamouseo-a11y/TOS-Patchs`
Prompt local path: `/var/www/TOS-Patchs/TNC/Phase5/OPENHANDS_TNC_PHASE5_1_FRONTEND_INTEGRATION_COMPLETION_V1.md`

## Context

TNC Phase 5 backend work has already been implemented locally on the server in commit beginning `f98b0bf`.
Do NOT reimplement or reset that work.
The previous report explicitly left Frontend UI and integration validation incomplete, although the Phase 5 specification required them.

Remote GitHub may intentionally lag because the user performs Push manually. The local server working tree is authoritative.

## Mandatory workflow

- Work only in `/var/www/TOS`.
- Verify local Phase 4 and Phase 5 backend commits are present before editing.
- Do NOT reset/rebase to remote or discard local commits.
- Do NOT push TOS or TOS-Patchs.
- Do NOT use `git push`, `gh`, SSH push, deploy-key push, or Developer Hub Push.
- The user will Push manually later.
- You ARE responsible for deployment on the server.
- Browser/UI testing is unavailable. Do NOT claim browser QA.
- Implement first, then run one focused validation pass at the end.
- Create a new local completion commit only after validation.
- Deploy after successful validation.
- Final report goes in TOS-Patchs, never TOS root.

---

# Mission

Complete ONLY the missing Phase 5 requirements and verify the already-implemented backend safely.

Do not redesign or rewrite the Phase 5 backend unless a concrete integration/test failure proves a focused fix is necessary.

## 1. Frontend Action Center integration — REQUIRED

Integrate Phase 5 into the existing TNC UI and hook/API architecture.

Required:

- Add `ACTIONS` / Action Center tab/filter inside existing `TncNotificationCenter`.
- Show actionable notifications only in Action Center.
- Preserve All, Unread, Attention, Digest, TCS, Tasks, TWS, System.
- Render backend-authoritative action descriptors on eligible notification items.
- Support TNC-native actions exposed by backend such as OPEN, MARK_READ, MARK_UNREAD, MUTE_TYPE, SNOOZE where actually available.
- Any verified domain workflow action returned by backend may be shown; do not invent frontend-only actions.
- Per-action loading state.
- Prevent rapid duplicate submissions.
- Confirmation UI for actions marked `requiresConfirmation` or destructive/high-impact.
- Show normalized success / failed / noop / no-longer-available feedback.
- Refresh through current TNC hook/realtime state; do not add a second socket architecture.

## 2. Bulk selection UI — REQUIRED

Add bounded bulk selection mode in existing TNC UI:

- select/deselect notification rows
- selected count
- bulk MARK_READ
- bulk MARK_UNREAD
- use the existing Phase 5 backend bulk endpoint
- no bulk domain workflow actions in V1
- disable/clear selection safely after operation or filter changes as appropriate

## 3. Saved Views UI — REQUIRED

Add Saved Views to existing TNC UX:

- list saved views
- create from allowed current TNC filters
- select/apply saved view
- update/rename when supported by backend
- delete
- no arbitrary query language
- user-owned only
- respect global `savedViewsEnabled` governance

If the backend chose the additive `TncSavedView` model rather than `NotificationPreference.settings`, inspect and document the technical reason. Do not migrate it merely for stylistic consistency if it is bounded, user-owned, indexed, and safe.

## 4. Governance UI behavior — REQUIRED

Respect Phase 4/5 governance returned by backend:

- `actionCenterEnabled`
- `workflowActionsEnabled`
- `bulkActionsEnabled`
- `savedViewsEnabled`

Frontend must hide/disable unavailable capabilities consistently, but backend remains authoritative.

Do not create another governance store.

## 5. Localization/responsive code — REQUIRED

Phase 5 frontend additions must support:

- Arabic + English
- RTL + LTR
- Light + Dark
- desktop + narrow responsive code

Do NOT claim visual/browser QA; only code/build validation is possible.

## 6. Backend integration verification — REQUIRED

Backfill focused automated/server-side tests for Phase 5 backend where missing.

At minimum verify:

1. action resolver exposes only allowed normalized descriptors
2. recipient ownership rejection
3. stale/unavailable action rejection
4. invalid/arbitrary action key rejection
5. idempotent duplicate execution behavior
6. action audit status/result remains safe and contains no secrets
7. bulk read/unread has strict bounded batch size and per-item ownership
8. Saved Views validation, ownership, limits, CRUD
9. governance disables action center/workflow/bulk/saved views server-side
10. Phase 5 action analytics remain bounded and respect analytics governance/range policy
11. notification-center core regressions
12. Phase 4 governance/analytics regressions
13. Phase 3 scheduler regressions
14. relevant TCS unread/realtime regressions

Do not require browser or real-user UI integration tests. Use deterministic service/route tests/mocks/fixtures consistent with the repository.

## 7. API client/hook integration — REQUIRED

Use current frontend API client and `useTncNotifications` architecture.

Add only the required methods/state for:

- action descriptors/execution
- Action Center feed/filter
- bulk actions
- Saved Views CRUD/select
- governance capability availability

Do not create a parallel TNC store or second notification fetch stack.

## 8. Final validation

After implementation is complete, run one focused pass:

- Phase 5 focused backend tests listed above
- relevant TNC Phase 3/4 regression tests
- relevant TCS unread/realtime regression tests
- Prisma validate/generate if schema was touched (avoid new migration unless objectively required)
- backend syntax/import/startup validation
- frontend build — REQUIRED
- `git diff --check`
- inspect changed-file scope and git status

Browser QA must be reported exactly as:

`BROWSER_QA=BLOCKED_NO_BROWSER_ACCESS`

## 9. Local commit + deploy

After validation passes:

Create a local commit in `/var/www/TOS`.

Suggested commit:

`feat(tnc): complete phase 5 frontend integration`

Do NOT push.

Deploy using the canonical production deployment flow.

After deploy verify:

- PM2 required process(es) online
- backend localhost health reachable
- public TOS endpoint not returning 5xx/502
- no startup/import errors
- frontend publication/build succeeded
- Phase 5 migrations remain applied

If deployment fails, diagnose/fix before completion.

## 10. Final report — mandatory

Create one Markdown file here:

`/var/www/TOS-Patchs/TNC/Phase5/TNC_PHASE5_1_FRONTEND_INTEGRATION_COMPLETION_V1_REPORT.md`

Do NOT create ZIP.
Do NOT put report in `/var/www/TOS`.
Do NOT push TOS or TOS-Patchs.

Report must include:

- `IMPLEMENTATION=PASS|FAIL|BLOCKED`
- `FINAL_VALIDATION=PASS|FAIL|BLOCKED`
- START_SHA
- PREVIOUS_PHASE5_SHA (expected beginning `f98b0bf`, verify actual full SHA)
- FINAL_LOCAL_SHA
- commit message
- exact changed files/count
- frontend Action Center implementation
- action execution UX
- bulk selection/actions implementation
- Saved Views UI implementation
- governance UI behavior
- API/hook integration
- exact backend tests added/run and counts
- frontend build result
- Prisma/migration status
- deployment result
- PM2/backend/public health
- `BROWSER_QA=BLOCKED_NO_BROWSER_ACCESS`
- `PUSH_PERFORMED=NO`
- `DEPLOYMENT_PERFORMED=YES|NO`
- exact report path

Final OpenHands response must be concise and include:

- IMPLEMENTATION result
- FINAL_VALIDATION result
- FINAL_LOCAL_SHA
- changed file count
- migration status
- FRONTEND_BUILD result
- DEPLOYMENT_PERFORMED
- PUSH_PERFORMED=NO
- exact report path
