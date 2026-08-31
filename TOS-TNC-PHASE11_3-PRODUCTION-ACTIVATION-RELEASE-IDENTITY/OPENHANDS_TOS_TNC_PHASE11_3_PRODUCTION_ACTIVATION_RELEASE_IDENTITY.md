# TNC Phase 11.3 — Production Activation & Release Identity Closure

## Canonical baseline
- Repository: `mohamedamouseo-a11y/TOS`
- Branch: `main`
- Required local HEAD and `origin/main` at start:
  `f30b2aad64fd03178199499af0daa2a2a662e6b8`
- Target server path: `/var/www/TOS`
- Public URL: `https://tos.tamiyouz.com`
- Canonical runtime manifest: `deployment/tos-production-runtime.json`
- Canonical deploy script: `scripts/tos-production-deploy.sh`

## Goal
Close Phase 11 on production safely.

This phase has two responsibilities:
1. Make the release-identity signal read the **actual canonical published frontend**, not the source build directory.
2. Activate the completed Phase 11 backend/frontend on production and prove the live runtime is serving one coherent release.

This is **production activation + release identity closure**, not a new product feature phase.

## Confirmed readiness gap at baseline
The current runtime manifest declares:
- build output: `/var/www/TOS/frontend/dist`
- published production frontend: `/opt/apps/tamiyouz-front/build`

But current `notificationOperations.service.js` reads:
- `/var/www/TOS/frontend/dist/index.html`

That is source build output, not the canonical published production directory.

Also the current deploy script generates `tos-release.json` at `/var/www/TOS/tos-release.json` instead of making the manifest part of the same published frontend release as `index.html` and hashed assets.

Phase 11 must not be declared production-complete while its release incident detector can compare the wrong filesystem target.

---

## Hard safety rules
- STOP if local HEAD or `origin/main` is not exactly the required baseline.
- STOP if worktree is dirty before implementation.
- No reset, rebase, amend, force push, history rewrite, or push.
- No Prisma schema changes or migrations.
- No Auth/session changes.
- No new scheduler, worker, cron, queue, or lease authority.
- No arbitrary HTTP shell execution.
- No Nginx config edits.
- No direct manual PM2 restart before the canonical deploy stage.
- Do not expose cookies, credentials, API keys, SMTP secrets, environment values, or integration keys.
- Preserve TNC Phases 1–11.2.1 behavior.
- Use only the canonical TOS production paths from `deployment/tos-production-runtime.json`.

---

## 11.3A — Canonical published release identity

File:
- `backend/src/services/notificationOperations.service.js`

Required:
1. Stop hardcoding `/var/www/TOS/frontend/dist/index.html` as the runtime release identity source.
2. Read `deployment/tos-production-runtime.json` safely using bounded file reads.
3. Derive `frontend.publishedBuildDir` from that manifest.
4. Read the production identity from:
   - `<publishedBuildDir>/index.html`
   - `<publishedBuildDir>/tos-release.json`
5. Keep source build output separate from published runtime identity.
6. No `child_process`, Git, PM2, Nginx, or shell execution from this service.

Release snapshot must expose at minimum:
```json
{
  "sourceSha": "...",
  "manifestMainJs": "assets/index-....js",
  "publicMainJs": "assets/index-....js",
  "identityMatch": true,
  "deployedAt": "..."
}
```

### Asset normalization
Normalize both asset names before comparison:
- remove one leading `/` if present
- preserve the exact `assets/index-*.js` filename

For example these must compare equal:
- `/assets/index-abc123.js`
- `assets/index-abc123.js`

Do not report `RELEASE_IDENTITY_MISMATCH` because of a leading-slash formatting difference.

Acceptance:
- `identityMatch` represents the actual published frontend release.
- Source `frontend/dist` can differ without causing a false production release incident.

---

## 11.3B — Publish `tos-release.json` atomically with frontend

File:
- `scripts/tos-production-deploy.sh`

Required:
1. Keep using runtime-manifest values:
   - `frontend.buildOutputDir`
   - `frontend.publishedBuildDir`
2. For a frontend deployment:
   - run the frontend build first
   - extract the exact main JS from the newly built `index.html`
   - generate `tos-release.json` **inside the build output directory** before publishing
   - then publish the full build output with existing `rsync --delete`
3. The manifest therefore lands in the published directory in the same release as `index.html` and the hashed JS asset.
4. Do not depend on a repo-root generated `tos-release.json` for runtime health.
5. Do not commit generated release manifests.

Required manifest fields, keeping backward compatibility where useful:
```json
{
  "version": "1.0.0",
  "releaseSchema": 1,
  "sourceSha": "EXACT_REAL_GIT_SHA",
  "deployedAt": "UTC_TIMESTAMP",
  "scope": "frontend|both",
  "mainJs": "assets/index-EXACT.js"
}
```

Rules:
- exact SHA comes from real deploy-time Git output inside the deploy script; no placeholder.
- `mainJs` must come from the newly built `index.html`, not the previous published release.
- fail deployment if main JS cannot be extracted.
- fail deployment if SHA is empty/unknown.

Acceptance:
- `<publishedBuildDir>/tos-release.json` exists after publish.
- `https://tos.tamiyouz.com/tos-release.json` returns that same release manifest.

---

## 11.3C — Release identity focused tests

Add/extend the narrowest focused test for `notificationOperations.service.js`.

Must prove:
1. runtime manifest `publishedBuildDir` is used for release identity.
2. source build directory is not the production identity authority.
3. leading slash normalization works.
4. same manifest/public JS => `identityMatch=true`.
5. different manifest/public JS => `identityMatch=false` and classifier produces `RELEASE_IDENTITY_MISMATCH` CRITICAL.
6. missing files => explicit `null/unknown`, not fabricated healthy or mismatch.

Use temporary fixtures/injected path helper where practical; do not mutate production paths from tests.

---

## 11.3D — Pre-activation validation

Before any deployment, run only focused checks:
- incident classifier test
- incident route/tamper test
- new release identity/operations test
- backend import/syntax check for touched files
- frontend build
- `bash scripts/tos-production-preflight.sh --static`

Also prove source gates:
```text
OPERATIONS_USES_PUBLISHED_BUILD_DIR=YES
RUNTIME_IDENTITY_READS_SOURCE_DIST=NO
RELEASE_MANIFEST_PUBLISHED_WITH_BUILD=YES
ASSET_NORMALIZATION=YES
HTTP_CHILD_PROCESS_COUNT=0
HTTP_SKIP_LEASE_COUNT=0
```

---

## 11.3E — Commit gate before production activation

If source changes were required, create exactly ONE local commit:

`fix(tnc): close phase 11 production release identity contract`

Then STOP.

Do NOT deploy that unpushed commit.
Do NOT push.
Do NOT restart PM2.

Return `ACTIVATION_STATE=WAITING_FOR_PUSH`.

The user will push the commit manually. After that, rerun this same Phase 11.3 patch.

---

## 11.3F — Production activation mode

Only enter activation mode when all are true:
- local HEAD == `origin/main`
- worktree clean
- the canonical release identity source gates already pass
- focused tests pass
- static preflight passes

Then:

1. Run canonical live preflight **before** deployment:
```bash
bash scripts/tos-production-preflight.sh --live
```

2. Deploy backend + frontend only through:
```bash
bash scripts/tos-production-deploy.sh --scope both
```

Do not use manual rsync, manual PM2 restart, alternate deploy scripts, or direct Nginx edits.

3. Run canonical live preflight **after** deployment:
```bash
bash scripts/tos-production-preflight.sh --live
```

---

## 11.3G — Exact public release verification

After deployment, print real values from:

```bash
curl -fsS https://tos.tamiyouz.com/tos-release.json
curl -fsS https://tos.tamiyouz.com/ -o /tmp/tos-phase11-3-index.html
grep -o 'assets/index-[^" ]*\.js' /tmp/tos-phase11-3-index.html | head -1
```

Required:
- `sourceSha` in public release manifest == deployed Git HEAD.
- `mainJs` in public release manifest == main JS referenced by public `index.html`.
- exact public JS URL returns HTTP 200.
- canonical published filesystem `index.html` references the same main JS.

Do not accept "similar", "latest", or placeholder values. Exact match only.

---

## 11.3H — Live backend / incidents smoke

After backend restart via canonical deploy:

1. Backend health returns healthy from the runtime-manifest health URL.
2. Public incidents route is registered:
   - unauthenticated GET may return auth-required response, but MUST NOT be 404.
3. Public Operations route is registered and MUST NOT be 404.
4. Run one safe read-only server-side snapshot using the actual Phase 11 services (no shell from the HTTP service):
   - Operations release `identityMatch=true`
   - `manifestMainJs == publicMainJs` after normalization
5. Incident snapshot must NOT contain `RELEASE_IDENTITY_MISMATCH` after a successful coherent deployment.
6. Immediately after restart, scheduler telemetry may temporarily be INFO/unknown. Do not fabricate healthy.
7. Allow the existing scheduler one normal execution opportunity, then re-read telemetry. Do not trigger a parallel scheduler and do not use `skipLease`.

Do not execute a destructive recovery action just to prove the endpoint exists.

---

## 11.3I — UI smoke

Verify after deployment:
- TNC opens.
- Admin Command Center opens for an authorized admin session if a safe existing session is available.
- Operations tab loads without frontend error.
- Incidents tab loads without frontend error.
- no duplicate route 404.
- no console `ReferenceError` from Phase 11 code.
- light and dark mode have no horizontal overflow in the new tabs.

If no safe authenticated browser/admin session is available to OpenHands, report that UI authenticated smoke as `NOT_RUN_NO_SAFE_SESSION`; do not create credentials or print session material.

---

## No new feature work
Do not add Phase 12 functionality here.
Do not add incident persistence, assignment, SLO dashboards, postmortems, new notifications, or new monitoring dependencies.
This patch exists only to make Phase 11 production-truthful and activate it.

---

## Final report
Return only real values:

```text
BASE_SHA=
ORIGIN_MAIN=
MODE=READINESS|ACTIVATION
FILES_CHANGED=
OPERATIONS_USES_PUBLISHED_BUILD_DIR=
RUNTIME_IDENTITY_READS_SOURCE_DIST=
RELEASE_MANIFEST_PUBLISHED_WITH_BUILD=
ASSET_NORMALIZATION=
HTTP_CHILD_PROCESS_COUNT=
HTTP_SKIP_LEASE_COUNT=
INCIDENT_CLASSIFIER_TEST_EXIT=
ROUTE_TAMPER_TEST_EXIT=
OPERATIONS_IDENTITY_TEST_EXIT=
BACKEND_CHECK=
FRONTEND_BUILD_EXIT=
STATIC_PREFLIGHT_EXIT=
COMMIT_SHA=
WORKTREE=
ACTIVATION_STATE=WAITING_FOR_PUSH|ACTIVATED|BLOCKED
PREFLIGHT_LIVE_BEFORE=
DEPLOY_COMMAND=
DEPLOY_EXIT=
PREFLIGHT_LIVE_AFTER=
DEPLOYED_HEAD=
PUBLIC_RELEASE_SOURCE_SHA=
PUBLIC_RELEASE_MAIN_JS=
PUBLIC_INDEX_MAIN_JS=
PUBLISHED_INDEX_MAIN_JS=
PUBLIC_MAIN_JS_HTTP=
RELEASE_IDENTITY_MATCH=
RELEASE_MISMATCH_INCIDENT_PRESENT=YES/NO
BACKEND_HEALTH=
INCIDENT_ROUTE_HTTP=
OPERATIONS_ROUTE_HTTP=
SCHEDULER_TELEMETRY_AFTER_WAIT=
OPERATIONS_UI=
INCIDENTS_UI=
DARK_MODE=
LIGHT_MODE=
DEPLOY_PERFORMED=YES/NO
PM2_RESTARTED_BY_CANONICAL_DEPLOY=YES/NO
PUSH_PERFORMED=NO
BLOCKER=
```
