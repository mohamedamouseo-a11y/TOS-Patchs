# TNC Phase 3 — Automation Scheduler Hardening V1.1

## Goal
Harden the already-implemented TNC Phase 3 Smart Notifications + Digest + Escalation automation for production-scale execution without changing the existing TNC architecture or behavior.

## Repositories
- Prompt repository only: `mohamedamouseo-a11y/TOS-Patchs`
- Implementation repository: `mohamedamouseo-a11y/TOS`
- Branch: `main`
- Worktree: `/var/www/TOS`
- Required starting point: verify current remote `main` first. Known current head at prompt creation: `1adcddb782e80c2233460916e0e9b6815aab830d`.
- Phase 3 implementation commits that must remain preserved: `883390a64b75bc11987e1dc545447c0bcdb6c070` and `cd7455579f9a6ef1015eedca18df93d6b7134ca8`.

## Why this hardening is required
The current `startNotificationAutomationScheduler()` guard (`sweepTimer` / `sweepRunning`) is process-local. It prevents overlap only inside one Node process, not across multiple PM2/backend instances. The current sweep also enumerates up to 10,000 users independently for escalation and digest every minute. This is acceptable for a tiny single-process deployment but is not a robust production scheduler contract.

## Required outcomes

### 1. One active automation scheduler across backend instances
Implement a production-safe leader/lease/lock mechanism so only one backend instance can execute the scheduled TNC automation sweep at a time.

Requirements:
- Must work if PM2/backend is scaled to multiple processes.
- Must prevent duplicate escalation realtime alerts and concurrent scheduler sweeps.
- Must recover automatically if the active scheduler process dies.
- Do not rely only on module globals.
- Avoid long-lived database transactions if possible.
- Prefer existing production infrastructure / a minimal durable lease mechanism if available.
- A minimal additive migration is allowed only if objectively required for a robust lease and no existing safe mechanism exists.
- Never create a second notification, unread, socket, digest, or escalation system.

### 2. Bound scheduler work
Refactor the scheduled sweep so it does not blindly enumerate the full user population twice every minute.

Requirements:
- Resolve the recipient set once per sweep when practical.
- Skip digest work before notification scans when digest mode is `OFF` or not due.
- Skip escalation notification scans when escalation is disabled.
- Batch/paginate recipients; no unbounded in-memory user list.
- Keep per-cycle work bounded and observable.
- Preserve recipient isolation.
- Preserve exact current digest bucket/idempotency behavior.
- Preserve escalation levels, repeat cadence, resolution, unread-only/attention-only semantics and Phase 2 presentation policy.

### 3. Concurrency/idempotency safety
Add deterministic automated coverage for:
- two scheduler instances attempting the same sweep -> only one active runner;
- scheduler lease/lock recovery after owner failure/expiry;
- no duplicate escalation alert for the same level;
- no duplicate digest bucket;
- digest `OFF` avoids notification feed scan;
- escalation disabled avoids notification feed scan;
- batched recipients process correctly;
- existing timezone/configured-time WEEKDAYS/WEEKLY tests remain green.

### 4. Observability
Add concise scheduler result/log fields sufficient to diagnose production behavior, including at minimum:
- runner/lease acquired or skipped;
- recipients considered/processed;
- escalation escalated/resolved/skipped;
- digest generated/idempotent/skipped;
- execution duration;
- errors without secrets.

Do not log notification bodies, auth/session data, tokens, cookies, DB URLs or sensitive user data.

### 5. Regression preservation
Must preserve:
- `Notification` + `ChatNotification` as source systems;
- `chat:notification` + `tnc:notification` realtime architecture;
- backend-authoritative presentation policy;
- Smart Priority / intelligence;
- Attention Center exact counts;
- Digest OFF/DAILY/WEEKDAYS/WEEKLY + Generate Now;
- escalation semantics;
- Phase 2 mute/snooze/quiet-hours/priority preferences;
- TCS launcher and all later TCS commits already on current `main`;
- Arabic/English and Light/Dark frontend behavior.

Do not touch unrelated TCS UX files unless a proven integration regression requires it.

## QA
Run:
- focused TNC automation tests;
- full existing TNC regression suite;
- Prisma validate/generate and migration status;
- frontend build if any frontend file changes (prefer backend-only);
- backend build/start validation;
- production preflight.

If an authenticated browser is available, also finish the two Phase 3 live-QA gaps from the prior report:
1. preference value mutation -> reload -> persistence;
2. narrow/mobile TNC viewport with Attention, Digest and Preferences, verifying no horizontal overflow.

If browser access is unavailable, report those gates as BLOCKED; do not fabricate evidence and do not create code changes solely because browser QA is unavailable.

## Push / Deploy policy
- Commit locally in `/var/www/TOS`.
- DO NOT use terminal `git push`.
- DO NOT use SSH, GH CLI, Deploy Key or alternate push path.
- Push ONLY from inside the running TOS system using Developer Hub / GitHub integration.
- Push to `mohamedamouseo-a11y/TOS` -> `main`.
- Verify the exact remote SHA after push.
- Deploy only after successful in-system push.
- Use the minimum required deploy scope; backend-only if frontend is unchanged.

## Deliverable
Return:
`TNC_PHASE3_AUTOMATION_SCHEDULER_HARDENING_V1_1_REPORT.zip`

The report must clearly separate code/test PASS from any browser QA that remains BLOCKED.