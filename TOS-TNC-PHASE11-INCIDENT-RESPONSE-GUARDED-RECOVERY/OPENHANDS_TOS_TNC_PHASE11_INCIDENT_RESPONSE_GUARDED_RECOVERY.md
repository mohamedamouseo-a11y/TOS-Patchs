# TNC Phase 11 — Incident Response & Guarded Recovery

## Canonical baseline
- Repository: `mohamedamouseo-a11y/TOS`
- Branch: `main`
- Required remote baseline: `5b6207a276385f1a608b1de333ce964280b5af5b`
- Target server path: `/var/www/TOS`
- Public URL: `https://tos.tamiyouz.com`
- Existing Operations source of truth: TNC Phase 10 Operations endpoint + delivery/scheduler/release telemetry

## Goal
Turn Phase 10 observability into a controlled incident-response workflow for administrators.

Phase 11 must answer:
- What operational incident is happening?
- Why is it happening?
- How severe is it?
- What evidence supports it?
- What is the safest next action?
- Which recovery actions are safe to execute from the application itself?

This phase is **incident response + guarded recovery**, not autonomous self-healing.

## Hard safety rules
- STOP if local HEAD or `origin/main` is not exactly the required baseline.
- STOP if working tree is dirty before implementation.
- No reset, rebase, force push, history rewrite, or push.
- No Prisma schema changes or migrations unless the existing architecture absolutely requires persistence; default to no DB changes.
- No Auth/session changes.
- No Nginx changes.
- No new scheduler, cron, queue worker, PM2 worker, polling daemon, or duplicate lease authority.
- Do not shell out from HTTP requests to Git, PM2, Nginx, deployment scripts, or OS commands.
- Do not expose secrets, environment variables, integration keys, cookies, SMTP credentials, or tokens.
- Preserve TNC Phases 1–10 behavior.
- Preserve the existing Operations endpoint contract; extend backward-compatibly only.
- Reuse existing delivery retry / acknowledgement / governance / audit mechanisms where they already exist.
- No automatic destructive recovery action.
- Every write action must be explicit, admin-only, bounded, auditable, and idempotent where practical.
- Do not touch GitHub Sync UI or unrelated TOS modules.

---

## 11A — Canonical Incident Classification

Create one canonical backend incident classifier fed by the existing Phase 10 operations snapshot.

Minimum incident families:
- `RELEASE_IDENTITY_MISMATCH`
- `SCHEDULER_STALE_OR_FAILED`
- `DELIVERY_FAILURE_BACKLOG`
- `DELIVERY_RETRY_BACKLOG`
- `DELIVERY_STALE_PENDING`
- `TELEMETRY_UNKNOWN_AFTER_RESTART`

Each incident should expose a bounded safe shape similar to:

```json
{
  "code": "DELIVERY_FAILURE_BACKLOG",
  "severity": "INFO|WARNING|CRITICAL",
  "status": "OPEN|RECOVERING|RESOLVED",
  "title": "...",
  "summary": "...",
  "evidence": {},
  "recommendedActions": [],
  "autoRecoverable": false
}
```

Rules:
- Derive incidents only from real Phase 10 signals.
- Never invent timestamps or evidence.
- Keep severity rules deterministic and documented in code.
- Unknown telemetry after a fresh restart is not silently healthy.
- Avoid duplicate incidents representing the same root cause.
- Do not add a second health engine; reuse the existing canonical Operations status function where possible.

Acceptance:
- The same operational snapshot always produces the same incident set.
- Healthy state returns an empty incident list.

---

## 11B — Root-Cause Evidence

Each incident must carry a small, safe evidence payload sufficient for an admin to understand why it exists.

Examples:

### Release mismatch
- release source SHA
- public main JS
- manifest main JS
- mismatch boolean

### Scheduler stale/failed
- authority name
- lease state
- last run / last success / last failure
- derived expected interval
- sanitized last error

### Delivery backlog
- failed count
- retrying count
- stale pending count
- oldest pending timestamp
- bounded recent affected delivery IDs only

Rules:
- Never return raw email bodies, passwords, access tokens, credentials, cookies, or full environment state.
- Reuse existing sanitization helpers when available.

Acceptance:
- Admin can understand the incident without reading server logs.

---

## 11C — Guarded Runbook Catalog

Add a small canonical runbook catalog in backend code.

Each incident code should map to:
- human-readable explanation
- safe diagnostic checklist
- supported application-level recovery actions
- manual-only actions that must never be executed from HTTP

Examples:

`DELIVERY_FAILURE_BACKLOG`
- allowed application action: retry one selected failed delivery using the existing retry service
- optional bounded retry of selected IDs only if an equivalent safe batch service already exists
- never retry all history automatically

`DELIVERY_RETRY_BACKLOG`
- diagnostic: inspect retrying count / oldest pending
- recovery: explicit selected retry only

`SCHEDULER_STALE_OR_FAILED`
- diagnostic: show lease/run telemetry
- if a safe existing in-process admin trigger already exists, it may be reused only after proving it does not create a second authority
- otherwise recovery remains manual-only; do not create a new trigger

`RELEASE_IDENTITY_MISMATCH`
- diagnostic only in the application
- deployment/restart/Nginx/Git actions remain manual-only
- do not expose shell/deploy actions through HTTP

Acceptance:
- Runbook text and actions are generated from one canonical backend catalog, not duplicated independently in frontend.

---

## 11D — Incident Response API

Extend the existing TNC admin namespace; do not create a parallel admin subsystem.

Preferred endpoints:

`GET /api/notification-center/admin/incidents`

Response:
```json
{
  "generatedAt": "ISO_DATE",
  "overallStatus": "HEALTHY|DEGRADED|CRITICAL",
  "incidents": []
}
```

Optional action endpoint only for safe existing application-level actions:

`POST /api/notification-center/admin/incidents/:code/actions/:action`

Requirements:
- Admin-only using the same canonical admin authorization as Phase 10.
- Non-admin gets clean 403.
- Allowlist actions by incident code.
- Reject unknown action/code combinations with 400/404.
- No arbitrary command names from client.
- No shell execution.
- No environment access.
- No Git/PM2/Nginx/deploy execution.
- Every successful write action must use the existing audit mechanism if available.
- Return bounded post-action state or instruct frontend to refresh.

Acceptance:
- A manipulated request cannot execute an unregistered action.
- Existing TNC routes stay backward-compatible.

---

## 11E — Recovery Action Safety

For every write action that Phase 11 exposes:
- prove authorization
- prove target ownership/scope when applicable
- enforce bounded input size
- enforce existing domain validation
- prevent duplicate/unsafe mass execution
- return a clear success/failure contract

At minimum include tamper tests for:
- non-admin incident list = 403
- non-admin incident action = 403
- unknown incident code/action = rejected
- oversized selected-ID list = rejected if batch selection exists
- valid retry of one existing retryable delivery = allowed
- retry of non-retryable/already-terminal-invalid target = rejected according to existing delivery contract

Do not create a new generic "execute command" endpoint.

---

## 11F — Admin Command Center: Incidents Tab

File expected:
- `frontend/src/components/TncAdminCommandCenter.jsx`
- `frontend/src/lib/api.js` only as needed

Add an **Incidents / الحوادث** tab next to Operations.

Show:
- overall status
- active incident count by severity
- incident cards with code, severity, summary, evidence, recommended actions
- clear distinction between:
  - safe in-app action
  - manual-only runbook step

For safe actions:
- explicit button per incident/action
- confirmation before mutation
- show loading/result state
- refresh incidents + Operations after success

UX rules:
- no automatic aggressive polling
- load on tab open + manual Refresh
- no modal explosion
- keep light/dark styles
- responsive without horizontal overflow
- no secrets or raw stack traces in UI

Acceptance:
- Admin can move from "something is wrong" to "here is why and what I can safely do" in one place.

---

## 11G — Recovery Verification

After a successful safe action:
- refresh Operations snapshot
- refresh incident list
- recalculate incident state from real telemetry
- never mark an incident resolved only because the action endpoint returned 200
- `RESOLVED` requires the underlying operational condition to actually clear

Acceptance:
- UI cannot falsely show a resolved incident while the underlying Phase 10 signal remains unhealthy.

---

## 11H — Focused Validation

Do NOT run the whole repository test suite.

Required:
1. Focused backend incident-classifier test:
   - healthy snapshot => no incidents
   - release mismatch => critical release incident
   - retry backlog => warning/degraded incident
   - scheduler hard failure/stale => critical incident
2. Focused route authorization/tamper test:
   - admin allowed
   - non-admin 403
   - unknown action rejected
3. If a retry action is exposed, focused test proving it delegates to the existing canonical retry contract rather than duplicating retry logic.
4. Frontend build to completion.
5. Backend syntax/import check for touched files.
6. `scripts/tos-production-preflight.sh --static`.
7. If deploying on production, use only `scripts/tos-production-deploy.sh` with the narrowest correct scope.
8. Live smoke after deploy:
   - Operations still works
   - Incidents tab opens
   - incident list reflects real Operations state
   - one safe action works if a valid test target exists
   - non-admin remains blocked
   - light/dark render cleanly

---

## Commit / deploy

If all gates pass:
- Create exactly one local commit:
  `feat(tnc): add phase 11 incident response and guarded recovery`
- Deploy only through the canonical TOS production deploy path if required.
- DO NOT PUSH.

## Evidence discipline

OpenHands must return real command/API evidence.
Do not invent PASS/YES values.
Do not expose credentials or integration keys.
Do not report a recovery as successful unless the underlying Phase 10 signal proves it recovered.

## Final report

Return exactly:

```text
BASE_SHA=
FILES_CHANGED=
INCIDENT_CLASSIFIER=
INCIDENT_CODES=
INCIDENTS_ENDPOINT=
ACTION_ENDPOINT=
RUNBOOK_CATALOG=
ADMIN_AUTH=
NON_ADMIN_403=
UNKNOWN_ACTION_REJECTED=
RETRY_DELEGATES_EXISTING_SERVICE=
HEALTHY_SNAPSHOT_TEST=
RELEASE_MISMATCH_TEST=
DELIVERY_BACKLOG_TEST=
SCHEDULER_FAILURE_TEST=
TARGETED_ROUTE_TEST=
BACKEND_CHECK=
FRONTEND_BUILD=
PREFLIGHT_STATIC=
INCIDENTS_UI=
OPERATIONS_REGRESSION=
DARK_MODE=
LIGHT_MODE=
DEPLOYMENT=
COMMIT_SHA=
WORKTREE=
PUSH_PERFORMED=NO
BLOCKER=
```
