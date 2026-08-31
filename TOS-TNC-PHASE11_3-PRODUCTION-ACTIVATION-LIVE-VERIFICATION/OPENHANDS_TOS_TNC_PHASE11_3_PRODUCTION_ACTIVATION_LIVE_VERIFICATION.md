# TNC Phase 11.3 — Production Activation & Live Verification

## Baseline
- Repository: `mohamedamouseo-a11y/TOS`
- Working path: `/var/www/TOS`
- Required local HEAD: `42371fe064353a45c04d2d9334955ef75f212b54`
- Required `origin/main`: `42371fe064353a45c04d2d9334955ef75f212b54`
- Public URL: `https://tos.tamiyouz.com`
- Canonical production deploy entrypoint: `scripts/tos-production-deploy.sh`
- Runtime manifest: `deployment/tos-production-runtime.json`

## Goal
Activate the already-reviewed Phase 11 code on production and prove the live runtime matches the pushed release. This phase is deployment + live verification only; no source changes are allowed.

## Hard rules
- Stop if local HEAD or `origin/main` differs from the required SHA.
- Stop if the working tree is not clean.
- Do not modify source code.
- Do not create a commit or push.
- Do not reset, rebase, amend, or rewrite history.
- Do not run database migrations.
- Do not manually restart application processes or reload the reverse proxy outside the canonical deployment entrypoint.
- Do not expose credentials, tokens, cookies, environment values, or secrets in output.
- If any production gate fails, stop and report the exact blocker instead of improvising a repair.

## A — Pre-activation verification
Before activation, prove:
- HEAD = required SHA
- origin/main = required SHA
- worktree clean
- static production preflight passes
- focused Operations snapshot tests pass
- focused incident classifier tests pass
- focused incident route/tamper tests pass

Do not run the whole repository test suite.

## B — Canonical activation
Use only the existing canonical TOS production deployment entrypoint with scope `both`, because this release contains backend and frontend production changes.

Do not request dependency installation or Prisma generation unless the canonical process explicitly proves they are required. If either becomes necessary, stop and report instead of automatically changing the deployment procedure.

No manual restart or reverse-proxy reload outside the canonical deployment path.

## C — Live runtime verification
After successful activation, prove:
- live production preflight passes
- backend health is successful
- public site responds successfully
- public `tos-release.json` exists and is valid JSON
- public release `sourceSha` equals the required SHA
- public release `mainJs` exists and returns HTTP 200
- the public homepage references the same normalized main JS asset

Normalize asset identity by removing one leading slash before comparison.

## D — Shared Operations release identity
Use the real shared Operations snapshot implementation from `backend/src/services/notificationOperations.service.js` against the live runtime.

Return only safe fields:
- generatedAt
- release.manifestSourceSha
- release.manifestMainJs
- release.publicMainJs
- release.identityMatch
- bounded scheduler status fields
- bounded delivery summary counts

Required:
- `release.identityMatch === true`
- `release.manifestSourceSha` equals the required SHA

## E — Incident verification
Use the real Phase 11 incident service against the live Operations snapshot and return only:
- overallStatus
- incidentCount
- incident codes and severities

Required:
- `RELEASE_IDENTITY_MISMATCH` is absent after successful activation.
- A temporary telemetry-unknown incident immediately after restart may be rechecked once after the normal scheduler has had time to run.
- A scheduler stale/failed CRITICAL incident must not remain after the normal scheduler interval and one bounded recheck.
- Any genuine delivery incident should be reported as a live operational condition, not hidden or mutated away.

## F — HTTP route smoke
Verify the production routes exist and are protected:
- `/api/notification-center/admin/operations`
- `/api/notification-center/admin/incidents`

Without authentication, 401 or 403 is acceptable. A 404 or frontend HTML fallback is not acceptable.

Do not print authentication credentials.

## G — Post-activation integrity
After verification, prove:
- HEAD still equals the required SHA
- origin/main still equals the required SHA
- no source drift was introduced
- no new commit was created
- no push occurred
- no manual process restart or reverse-proxy reload occurred outside the canonical deployment path

Generated release/runtime artifacts are acceptable only when they are part of the existing deployment design and do not modify tracked source unexpectedly.

## Acceptance
Phase 11.3 is PASS only when all are true:
- canonical activation succeeds
- live preflight succeeds
- backend health succeeds
- public release SHA is exact
- manifest/public main JS identities match
- shared Operations identity is true
- release mismatch incident is absent
- Operations and Incidents routes are protected and not 404
- no source drift exists

## Final report
Return exactly:

```text
HEAD=
ORIGIN_MAIN=
WORKTREE_BEFORE=
STATIC_PREFLIGHT_EXIT=
OPS_TEST_EXIT=
CLASSIFIER_TEST_EXIT=
ROUTE_TEST_EXIT=
ACTIVATION_METHOD=CANONICAL_TOS_DEPLOY
ACTIVATION_EXIT=
LIVE_PREFLIGHT_EXIT=
BACKEND_HEALTH_HTTP=
BACKEND_HEALTH_OK=
PUBLIC_SITE_HTTP=
PUBLIC_RELEASE_HTTP=
PUBLIC_RELEASE_SOURCE_SHA=
PUBLIC_RELEASE_MAIN_JS=
PUBLIC_INDEX_MAIN_JS=
PUBLIC_MAIN_JS_HTTP=
PUBLIC_RELEASE_IDENTITY_MATCH=YES/NO
OPERATIONS_MANIFEST_SOURCE_SHA=
OPERATIONS_MANIFEST_MAIN_JS=
OPERATIONS_PUBLIC_MAIN_JS=
OPERATIONS_IDENTITY_MATCH=YES/NO
INCIDENT_OVERALL_STATUS=
INCIDENT_CODES=
RELEASE_IDENTITY_MISMATCH_PRESENT=YES/NO
SCHEDULER_INCIDENT_AFTER_RECHECK=YES/NO/NOT_PRESENT
OPERATIONS_ROUTE_HTTP=
INCIDENTS_ROUTE_HTTP=
ROUTES_PROTECTED_NOT_404=YES/NO
HEAD_AFTER=
ORIGIN_MAIN_AFTER=
WORKTREE_AFTER=
SOURCE_DRIFT=YES/NO
MANUAL_PROCESS_RESTART=NO
MANUAL_PROXY_RELOAD=NO
NEW_COMMIT=NO
PUSH_PERFORMED=NO
PHASE_11_3_STATUS=PASS/FAIL
BLOCKER=
```