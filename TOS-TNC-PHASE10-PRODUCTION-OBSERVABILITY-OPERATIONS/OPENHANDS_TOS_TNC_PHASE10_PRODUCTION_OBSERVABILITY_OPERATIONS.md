# TNC Phase 10 — Production Observability & Operations

## Canonical baseline
- Repository: `mohamedamouseo-a11y/TOS`
- Branch: `main`
- Required remote baseline: `28af5799c3bcba5cc9548ca68f16485ec7c803c6`
- Target server path: `/var/www/TOS`
- Public URL: `https://tos.tamiyouz.com`
- Canonical frontend publish dir: `/opt/apps/tamiyouz-front/build`
- Canonical deploy: `scripts/tos-production-deploy.sh`
- Canonical runtime manifest: `deployment/tos-production-runtime.json`

## Goal
Turn TNC from a feature-complete notification center into an operationally observable production subsystem.

Phase 10 must give administrators a trustworthy answer to:
- Is TNC healthy right now?
- Is delivery working?
- Is the existing scheduler/lease authority healthy?
- What exact frontend release is production serving?
- Are production HTML and hashed assets from the same release?
- Are there stale/failed deliveries that need action?

This phase is **operations + observability**, not a feature redesign.

## Hard safety rules
- STOP if `origin/main` is not exactly the required baseline.
- STOP if working tree is dirty before implementation.
- No reset, rebase, force push, history rewrite, or push.
- No Prisma schema changes.
- No migrations.
- No DB table additions.
- No Auth/session changes.
- Do not create a new scheduler, cron, PM2 worker, queue worker, or polling daemon.
- The existing scheduler/lease authority remains the only automation authority.
- Do not edit Nginx configuration in this phase.
- Do not create backups inside `/etc/nginx/sites-enabled`.
- Do not touch GitHub Sync UI or its CSS contracts.
- Preserve TNC Phases 1–9.1 behavior.
- No new charting/monitoring dependency.
- Never report placeholders such as `<sha>`, `<hash>`, `SUCCESS`, or `YES` when an exact value can be printed.

---

## 10A — Delivery Health Snapshot

Existing canonical code:
- `backend/src/routes/notificationDelivery.routes.js`
- `backend/src/services/notificationDelivery.service.js`
- Existing outbox: `tncDeliveryOutbox`
- Existing admin delivery list/summary/retry routes must be reused.

Required:
- Extend delivery observability using the existing outbox only.
- Add a canonical operational summary that reports at minimum:
  - total records in the requested window/channel
  - `PENDING`
  - `DELIVERED`
  - `FAILED`
  - `EXPIRED`
  - retrying count (`PENDING` with `attemptCount > 0`)
  - stale pending count
  - oldest pending timestamp
  - latest delivered timestamp
  - latest failed timestamp
  - delivered rate / failure rate when total > 0
- Keep payload bounded; do not scan unlimited history.
- Default to EMAIL if channel is omitted, while keeping the service shape extensible for additional channels.
- Sanitize error details; never expose credentials, SMTP password, cookies, tokens, or raw secrets.

Acceptance:
- Admin can distinguish healthy delivery from retry backlog and terminal failures without reading server logs.
- Existing list/summary/retry contracts continue to work.

---

## 10B — Existing Scheduler / Lease Telemetry

Required:
1. Find the existing TNC scheduler/lease execution path already responsible for automation/delivery work.
2. Do **not** create another timer or worker.
3. Add process-local telemetry to that existing path only if equivalent telemetry does not already exist.
4. Expose actual observed state, never invented state.

Expose at minimum when available:
- authority name
- enabled/running state
- lease ownership state
- last run started at
- last run finished at
- last successful run at
- last failed run at
- sanitized last error code/message
- last run processed/delivered/failed/expired summary
- configured/derived expected interval

If the process has just restarted and no run has occurred yet, return explicit `null`/`unknown`; do not fabricate timestamps.

Acceptance:
- Admin Operations can tell whether the existing automation authority has recently run successfully.
- No second scheduler/cron/worker exists after the patch.

---

## 10C — Production Release Identity

Files expected to be involved:
- `scripts/tos-production-deploy.sh`
- `scripts/tos-production-preflight.sh`
- optionally one small backend operations service/route if needed

Required:
- During a successful frontend build/deploy, generate a small public release manifest inside the built/published frontend.
- Suggested filename: `tos-release.json`.
- It must contain only non-secret operational metadata:
  - exact source Git SHA
  - UTC build timestamp
  - exact main `assets/index-*.js` filename referenced by built `index.html`
  - deploy scope
  - release schema/version identifier
- Generate it from real command output; never hardcode a hash.
- Ensure `rsync --delete` publishes it with the same release as `index.html`.
- Do not commit generated release manifests into source control.

Acceptance:
- `https://tos.tamiyouz.com/tos-release.json` identifies the exact published frontend release.
- Its `mainJs` matches the JS referenced by production `index.html`.

---

## 10D — Production Preflight Hardening

Extend the existing guarded preflight; do not replace it.

Live preflight must additionally validate:
1. Exactly one effective HTTPS TOS server block serves `tos.tamiyouz.com`.
   - The normal HTTP redirect block is allowed.
   - Duplicate/stale HTTPS blocks must fail preflight.
2. The effective HTTPS root is exactly the canonical published frontend directory from `deployment/tos-production-runtime.json`.
3. Public `index.html` references the same main JS as the canonical published `index.html`.
4. The referenced public main JS returns HTTP 200.
5. The public release manifest exists and agrees with the public document/main JS.
6. A stale generated source build directory must never become the Nginx production root.

Important:
- This phase may **detect** Nginx problems but must not rewrite `/etc/nginx`.
- Any Nginx blocker must stop deployment and be reported for explicit remediation.

Acceptance:
- The stale-build/duplicate-server-block incident class is caught by preflight before a deploy is declared healthy.

---

## 10E — Admin Operations API

Preferred location:
- extend the canonical notification admin route/service structure rather than creating a parallel API family.

Add an admin-only Operations endpoint under the existing notification-center admin namespace.

Suggested contract:
`GET /api/notification-center/admin/operations`

Response should compose existing sources into one bounded snapshot:

```json
{
  "status": "HEALTHY|DEGRADED|CRITICAL",
  "generatedAt": "ISO_DATE",
  "release": {},
  "delivery": {},
  "scheduler": {},
  "warnings": []
}
```

Rules:
- Reuse the same admin authorization contract as existing TNC admin endpoints.
- Non-admin must receive clean 403.
- No secrets.
- Do not shell out from an HTTP request to run deployment commands, `nginx -T`, `pm2`, or Git.
- Runtime endpoint must read safe runtime/release telemetry already produced by the application/deploy path.
- Operational `status` must be derived from real conditions and documented in code.
- An unknown scheduler state after restart is not silently converted to healthy.

Acceptance:
- One request gives the Admin Center a truthful operational snapshot without privileged shell execution.

---

## 10F — Admin Command Center: Operations Tab

File:
- `frontend/src/components/TncAdminCommandCenter.jsx`
- `frontend/src/lib/api.js` only as needed for canonical API methods

Add a fifth tab: **Operations** / **العمليات**.

Show compact production cards for:
- Overall status: Healthy / Degraded / Critical
- Published source SHA (short display, full value in title/details)
- Build timestamp
- Main JS asset filename
- Delivery health:
  - delivered
  - pending
  - retrying
  - failed
  - expired
- Scheduler/lease health:
  - authority
  - lease/running state
  - last success
  - last failure
- Operational warnings

Also show a bounded recent failed/retrying delivery table using the existing delivery list endpoint.

Retry action:
- Reuse the existing admin delivery retry endpoint.
- Retry must be explicit per record; no automatic mass retry.
- After a successful retry, refresh Operations data.

UX rules:
- No automatic aggressive polling.
- Load on tab open and provide a Refresh button.
- Keep current dark/light visual language.
- No modal explosion and no separate monitoring application.
- Admin-only handling must remain clean.

Acceptance:
- Admin can identify a stale release, delivery backlog, failed delivery, or scheduler issue from the existing TNC Admin Command Center.

---

## 10G — Operational Status Rules

Use deterministic, explainable status rules.

Minimum behavior:
- `CRITICAL` when a confirmed hard failure exists, for example:
  - release/public asset identity mismatch
  - scheduler is known failed/stale beyond a derived safe interval
  - terminal failed deliveries exceed a bounded critical threshold
- `DEGRADED` for non-terminal operational warnings, for example:
  - retry backlog exists
  - isolated failed deliveries exist below critical threshold
  - scheduler telemetry is temporarily unknown immediately after restart
- `HEALTHY` only when all required signals are positively healthy.

Do not hardcode scheduler staleness to an arbitrary number if the existing scheduler interval/config can be derived.

Keep status calculation in one canonical backend function and add a focused unit test for it.

---

## 10H — Focused Validation

Do NOT run the whole repository test suite.

Required validation:
1. One focused backend test for Operations status/summary logic.
2. One focused admin authorization check proving non-admin 403.
3. One frontend build.
4. `scripts/tos-production-preflight.sh --static`.
5. If deploying on the production server, run canonical live preflight before and after deploy.
6. Deploy only with `scripts/tos-production-deploy.sh` using the narrowest correct scope.
7. After deploy, verify exact public release identity with real command output.

Required production evidence after frontend deploy:

```bash
curl -fsS https://tos.tamiyouz.com/tos-release.json
curl -fsS https://tos.tamiyouz.com/ -o /tmp/tos-phase10-index.html
grep -o 'assets/index-[^" ]*\.js' /tmp/tos-phase10-index.html
```

The filename printed by public `index.html` must exactly equal `mainJs` in `tos-release.json`.

Then verify that exact JS URL returns 200.

Browser smoke:
- Main TNC opens.
- Admin Center opens.
- Operations tab opens.
- No console ReferenceError.
- Operations endpoint returns real data.
- Failed/retrying delivery list renders when data exists.
- Retry action refreshes state.
- Light + Dark render without overflow.

---

## Commit / deploy

If all gates pass:
- Create exactly one local commit:
  `feat(tnc): add phase 10 production observability`
- Deploy only through the canonical production deploy script.
- DO NOT PUSH.

## Evidence discipline

OpenHands must not claim a check passed based only on its own summary.

For every SHA/hash/asset name requested in the final report:
- print the exact real value,
- no placeholders,
- no `<new-hash>`, `NEW_COMMIT_SHA`, `verified`, or invented checksum strings.

If an exact value cannot be obtained, set `BLOCKER` and stop.

## Report only

Return exactly:

```text
BASE_SHA=
FILES_CHANGED=
OPERATIONS_ENDPOINT=
DELIVERY_HEALTH=
SCHEDULER_AUTHORITY=
SCHEDULER_TELEMETRY=
RELEASE_MANIFEST_PATH=
SOURCE_SHA_IN_RELEASE=
PUBLISHED_MAIN_JS=
PUBLIC_MAIN_JS=
PUBLIC_MAIN_JS_HTTP=
HTTPS_TOS_SERVER_BLOCK_COUNT=
CANONICAL_NGINX_ROOT=
PREFLIGHT_STATIC=
PREFLIGHT_LIVE_BEFORE=
TARGETED_BACKEND_TEST=
ADMIN_403_TEST=
FRONTEND_BUILD=
DEPLOYMENT=
PREFLIGHT_LIVE_AFTER=
OPERATIONS_UI=
DARK_MODE=
LIGHT_MODE=
COMMIT_SHA=
WORKTREE=
PUSH_PERFORMED=NO
BLOCKER=
```
