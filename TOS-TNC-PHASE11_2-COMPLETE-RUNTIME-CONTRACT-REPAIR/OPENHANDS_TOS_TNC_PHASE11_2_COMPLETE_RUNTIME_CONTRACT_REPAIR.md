# TNC Phase 11.2 — Complete Runtime Contract Repair

## Baseline
- Repository: `mohamedamouseo-a11y/TOS`
- Target: `/var/www/TOS`
- Required local HEAD: `7286cdb62be026685cdf68ad58ed85cf5b640332`
- Required origin/main: `59e77a7d28c7934f504f35c8e9604e8159946a79`

## Goal
Finish the Phase 11.1 correction exactly. The previous attempt did not satisfy the required runtime/safety contract.

## Mandatory fixes

### 1. Fix incident route registration
Current app mount remains:
`/api/notification-center/admin/incidents`

Therefore incident router paths MUST be relative:
- `GET /`
- `POST /:code/actions/:action`

Prove the final effective endpoints are exactly:
- `/api/notification-center/admin/incidents`
- `/api/notification-center/admin/incidents/:code/actions/:action`

### 2. Remove all shell/Git execution from HTTP Operations/Incidents path
Do NOT wrap `execSync`; REMOVE it.
No `child_process`, `execSync`, Git, PM2, Nginx, deploy or OS commands from:
- incident classifier/service HTTP path
- shared Operations snapshot path
- notification admin Operations route

Create/reuse ONE safe shared service, preferably:
`backend/src/services/notificationOperations.service.js`

It must build a bounded snapshot from files/runtime telemetry only:
- release
- delivery
- scheduler
- generatedAt

Both Phase 10 Operations endpoint and Phase 11 incidents MUST consume this same service.

### 3. Real release identity signal
Read safe bounded files only:
- `deployment/tos-production-runtime.json`
- existing `tos-release.json`
- canonical published `index.html`

Derive:
- `sourceSha` from release manifest only
- `manifestMainJs`
- `publicMainJs` from published index.html
- `identityMatch` only when both asset identities are known

`RELEASE_IDENTITY_MISMATCH` triggers ONLY when:
`manifestMainJs !== publicMainJs`

Do not fabricate source SHA and do not shell out to Git.

### 4. Enforce scheduler lease on HTTP sweeps
Remove `skipLease: true` from BOTH:
- Phase 11 incident `trigger-sweep`
- Phase 10 Operations sweep

Use canonical `runNotificationAutomationSweep(prisma)` with lease enforcement.
Do not manually call `updateSchedulerTelemetry` if the sweep already does it.
If lease is held, return bounded non-success (prefer 409) and do not audit success.

### 5. Real route/tamper tests
Add focused tests that execute the real route/controller contract. Must cover:
- intended incident GET endpoint registered and not 404
- non-admin list = 403
- non-admin action = 403
- unknown incident/action rejected
- >50 selected IDs rejected
- valid retry delegates to existing `retryDelivery`
- trigger-sweep cannot bypass lease
- release mismatch uses normalized shared Operations release shape

Classifier-only tests are NOT sufficient.

### 6. Do not introduce unrelated changes
Do not change `expireStaleDeliveries` service signature unless strictly needed by this spec. If already changed by 7286cdb, verify the change is safe and included in the exact diff report.

## Required source gates
All MUST be true:
- NO_INCIDENT_ROUTE_DOUBLE_PREFIX
- NO_HTTP_SKIP_LEASE
- NO_HTTP_CHILD_PROCESS
- SHARED_OPERATIONS_SNAPSHOT
- RELEASE_MISMATCH_REAL_SIGNAL
- ROUTE_TAMPER_TESTS_REAL

## Validation
Run only focused tests + frontend build + static preflight.

Required literal commands/results:
- incident classifier tests
- route/tamper tests
- backend import/syntax check
- frontend build
- `bash scripts/tos-production-preflight.sh --static`

## Commit
Create exactly one new local commit on top of `7286cdb62be026685cdf68ad58ed85cf5b640332`:

`fix(tnc): complete phase 11 runtime contract repair`

DO NOT PUSH.
DO NOT DEPLOY.
DO NOT RESTART PM2.
DO NOT reset/rebase/amend.

## Final report
Return exactly:

```text
BASE_SHA=
ORIGIN_MAIN=
FILES_CHANGED=
CHANGED_FILES=
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
INCIDENT_TEST_EXIT=
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