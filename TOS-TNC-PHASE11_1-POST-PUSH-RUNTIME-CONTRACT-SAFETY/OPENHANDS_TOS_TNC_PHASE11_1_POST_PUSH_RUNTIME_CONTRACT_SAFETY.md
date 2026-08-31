# TNC Phase 11.1 — Post-Push Runtime Contract & Recovery Safety Correction

## Canonical baseline
- Repository: `mohamedamouseo-a11y/TOS`
- Branch: `main`
- Required local HEAD and `origin/main` before implementation:
  `59e77a7d28c7934f504f35c8e9604e8159946a79`
- Target server path: `/var/www/TOS`

## Goal
Correct confirmed post-push runtime and safety defects in Phase 11 without redesigning TNC or adding new features.

This is a focused integrity correction for Phase 11 and the Phase 10 Operations dependency it reuses.

## Confirmed defects at `59e77a7`

### 1. Incident route is mounted with a duplicated prefix
`backend/src/app.js` mounts:
```js
app.use(`${API}/notification-center/admin/incidents`, incidentRoutes);
```

But `backend/src/routes/incident.routes.js` defines:
```js
router.get("/admin/incidents", ...)
router.post("/admin/incidents/:code/actions/:action", ...)
```

Therefore the real registered path becomes duplicated, while the frontend calls:
```text
/api/notification-center/admin/incidents
/api/notification-center/admin/incidents/:code/actions/:action
```

Required correction:
- Preserve the exact mount in `app.js` unless a clearly safer equivalent is proven.
- Make the incident router relative to that mount:
  - `GET /`
  - `POST /:code/actions/:action`
- The frontend API paths must work exactly as documented in Phase 11.

### 2. Recovery sweep bypasses the canonical scheduler lease
`incident.routes.js` currently calls:
```js
runNotificationAutomationSweep(prisma, { skipLease: true })
```

The automation service explicitly treats `skipLease` as a test bypass (`SKIPPED_FOR_TEST`). It must not be used from a production HTTP action.

The existing Phase 10 Operations sweep route also currently uses the same unsafe bypass.

Required correction:
- No production/admin HTTP route may pass `skipLease: true`.
- Both the Phase 10 Operations sweep and Phase 11 incident `trigger-sweep` must call the canonical sweep with lease enforcement enabled.
- Do not create another scheduler/worker/lease authority.
- Do not manually call `updateSchedulerTelemetry` after a successful sweep if `runNotificationAutomationSweep` already owns that update.
- If the lease cannot be acquired, return a clear bounded non-success response (prefer clean 409 for `LEASE_HELD` / equivalent) and do not report recovery success.
- Do not audit a lease-rejected sweep as a successful recovery.

### 3. Incident HTTP path shells out to Git and duplicates release telemetry
`incidentClassifier.service.js` currently imports `child_process` and runs `git rev-parse HEAD` from a service executed by the incidents HTTP endpoint.

This violates Phase 11 hard safety rules and duplicates Phase 10 release/Operations logic.

Required correction:
- No `child_process`, `execSync`, Git, PM2, Nginx, deploy, or OS command execution from the Operations/Incidents HTTP request path.
- Create/reuse one canonical safe Operations snapshot service for Phase 10 + Phase 11 rather than maintaining a second release-health implementation.
- Preferred small service:
  `backend/src/services/notificationOperations.service.js`
- It should expose a bounded snapshot from existing sources:
  - release
  - delivery
  - scheduler
  - generated/timestamp
- `notificationAdmin.routes.js` Operations endpoint and `incidentClassifier.service.js` must consume the same service/snapshot.

### 4. RELEASE_IDENTITY_MISMATCH cannot be produced from real Phase 11 runtime data
The classifier expects `manifestSourceSha`, but the Phase 11 `getReleaseInfo()` does not return that field.
It also receives `mainJs` and `manifestMainJs` but does not compare them.

Required correction:
- Derive release identity only from safe real runtime/deploy artifacts.
- Read bounded files only; no shell.
- Reuse `deployment/tos-production-runtime.json` to derive the canonical published frontend directory instead of hardcoding an alternate publish path when possible.
- Read the existing `tos-release.json` produced by the deployment path.
- Read the canonical published `index.html` and extract its actual `assets/index-*.js` reference.
- Normalize the release snapshot to expose at minimum:
  - `sourceSha` from the release manifest (informational)
  - `manifestMainJs`
  - `publicMainJs` (or canonical equivalent)
  - deterministic `identityMatch` when both asset identities are available
- Do not fabricate an independent source SHA.
- `RELEASE_IDENTITY_MISMATCH` must trigger when the real manifest main JS and real published index main JS disagree.
- Missing/unknown data must remain explicit unknown/null; do not fabricate a mismatch.

### 5. Required Phase 11 route/tamper validation was not implemented
The current test file only tests `classifyIncidents()` with synthetic snapshots.
Phase 11 explicitly required route authorization/tamper validation.

Required correction:
Add the narrowest real tests using existing project test style. They must cover at minimum:
1. Intended incidents endpoint is actually registered at:
   `/api/notification-center/admin/incidents`
   and is not a 404 because of duplicated routing.
2. Non-admin incident list = 403.
3. Non-admin incident action = 403.
4. Unknown incident code/action rejected.
5. Oversized `selectedIds` (>50) rejected.
6. Valid retry delegates to the existing canonical `retryDelivery` contract; do not duplicate retry business logic.
7. `trigger-sweep` does not bypass the scheduler lease.
8. Release mismatch classifier test uses the same normalized release shape produced by the shared Operations service and proves `manifestMainJs !== publicMainJs` => CRITICAL `RELEASE_IDENTITY_MISMATCH`.

If direct Express integration requires dependency injection, extract the smallest pure/controller helper necessary. Do not create a parallel application architecture.

## Safety / scope
- Start only if local HEAD and `origin/main` both equal `59e77a7d28c7934f504f35c8e9604e8159946a79` and worktree is clean.
- No reset, rebase, amend, force push, or history rewrite.
- No Prisma schema changes or migrations.
- No Auth/session redesign.
- No Nginx changes.
- No new scheduler, cron, queue, PM2 worker, polling daemon, or lease authority.
- No deployment in this correction task.
- No PM2 restart.
- No push.
- No secret/environment output.
- Preserve TNC Phases 1–10 and Phase 11 UI/incident families.
- Do not touch GitHub Sync UI or unrelated modules.

## Required source gates
Before finalizing, prove:
```text
NO_INCIDENT_ROUTE_DOUBLE_PREFIX
NO_HTTP_SKIP_LEASE
NO_HTTP_CHILD_PROCESS
SHARED_OPERATIONS_SNAPSHOT
RELEASE_MISMATCH_REAL_SIGNAL
```

At minimum confirm there is no `skipLease: true` remaining in:
- `backend/src/routes/incident.routes.js`
- `backend/src/routes/notificationAdmin.routes.js`

And no `child_process` / `execSync` in the HTTP-path Operations/Incident source files.

## Validation
Do NOT run the whole repository suite.

Required:
1. Existing focused incident classifier tests, updated to real normalized release contract.
2. New focused route/tamper tests.
3. Backend syntax/import check for touched files.
4. Frontend build to completion (because API/UI contract must remain valid).
5. `bash scripts/tos-production-preflight.sh --static`.
6. Confirm exact intended frontend API paths match the backend route registration.

All commands must finish; report literal exit codes.

## Commit
If every gate passes, create exactly one local commit on top of `59e77a7`:

`fix(tnc): harden phase 11 runtime contracts and recovery safety`

DO NOT PUSH.
DO NOT DEPLOY.
DO NOT RESTART PM2.

## Final report
Return real values only:

```text
BASE_SHA=
ORIGIN_MAIN=
FILES_CHANGED=
INCIDENT_GET_ROUTE=
INCIDENT_ACTION_ROUTE=
ROUTE_PREFIX_FIXED=YES/NO
OPERATIONS_SHARED_SNAPSHOT=YES/NO
HTTP_CHILD_PROCESS_REMOVED=YES/NO
INCIDENT_SWEEP_LEASE_ENFORCED=YES/NO
OPERATIONS_SWEEP_LEASE_ENFORCED=YES/NO
MANUAL_TELEMETRY_DOUBLE_UPDATE_REMOVED=YES/NO
RELEASE_MANIFEST_MAIN_JS=
RELEASE_PUBLIC_MAIN_JS=
RELEASE_IDENTITY_SIGNAL=REAL/NOT_REAL
NON_ADMIN_LIST_403=
NON_ADMIN_ACTION_403=
UNKNOWN_ACTION_REJECTED=
OVERSIZED_IDS_REJECTED=
RETRY_DELEGATES_EXISTING_SERVICE=
SWEEP_LEASE_TEST=
INCIDENT_TEST_COMMAND=
INCIDENT_TEST_EXIT=
ROUTE_TEST_COMMAND=
ROUTE_TEST_EXIT=
BACKEND_CHECK=
FRONTEND_BUILD_EXIT=
STATIC_PREFLIGHT_EXIT=
COMMIT_SHA=
WORKTREE=
DEPLOY_PERFORMED=NO
PM2_RESTARTED=NO
PUSH_PERFORMED=NO
BLOCKER=
```