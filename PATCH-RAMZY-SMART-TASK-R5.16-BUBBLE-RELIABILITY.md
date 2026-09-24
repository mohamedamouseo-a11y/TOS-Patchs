# PATCH — RAMZY SMART TASK R5.16
# Per-User Daily Bubble Reliability Fix

Baseline TOS:
`61c5c59989d95613d0dbe469a6f79e16255ca8f3`

Scope: Smart Task awareness bubble reliability only.
Do NOT touch Smart Task builder UX, date/time pickers, AI writing, backend RBAC behavior, DB/schema, provider/model, or task payloads.

## Confirmed root issue

`RamzyAssistant.jsx` initializes:
`smartTaskAwareness`
from:
`tos.ramzy.smart-task-awareness.v1.<userId>`

but that initializer runs only when the React component is created.

If the authenticated `user.id` changes while the same component instance survives, the next user can inherit the previous user's in-memory:
- `completed`
- `lastShownDate`
- `shownDays`

The same component-local `hidden` state can also remain true after a previous user hid Ramzy.

Result: an otherwise eligible user may not get the daily Smart Task bubble.

## Fix

### 1) Centralize awareness loading
Add a small helper, e.g.:
`loadSmartTaskAwareness(userId)`

It must:
- return default state for missing user
- read only `tos.ramzy.smart-task-awareness.v1.<userId>`
- safely parse JSON
- normalize:
  - `lastShownDate: string|null`
  - `shownDays: non-negative integer`
  - `completed: boolean`

Use it for initial state and user-switch reload.

### 2) Reset per-user awareness when user changes
Add a focused `useEffect` keyed by `user?.id`.

On user change:
- clear all bubble timers
- hide current bubble
- reset bubble step/popping
- load awareness state for the NEW user id
- reset `hidden=false` so a previous user's launcher-close state does not hide Ramzy for the next logged-in user
- do NOT clear or overwrite the previous user's localStorage
- do NOT reset a user's valid own `completed/shownDays/lastShownDate`

Do not mark a user complete during switching.

### 3) Keep intended eligibility explicit
Create one small helper/computed reason for bubble eligibility so failures are deterministic.

Eligible only when:
- `status.enabled === true`
- `status.allowed === true`
- `status.permissions.use === true`
- `status.permissions.actions.CREATE_TASK === true`
- `status.executionControl.globalExecutionAllowed === true`
- no active Smart Task
- `completed !== true`
- not shown today
- `shownDays < 10`

Do not weaken security or grant permissions.

### 4) Diagnostic reason (dev-safe)
Add a compact internal eligibility reason helper, with values such as:
- ELIGIBLE
- NO_USER
- RAMZY_DISABLED
- ROLE_NOT_ALLOWED
- NO_RAMZY_USE
- NO_CREATE_PERMISSION
- EXECUTION_DISABLED
- SMART_TASK_OPEN
- COMPLETED
- SHOWN_TODAY
- TEN_DAY_LIMIT

Use this only for debugging/tests (console debug in non-production is acceptable).
Do NOT show technical permission errors to normal users.

### 5) Timer reliability
Ensure only one eligibility timer is active.
On dependency/user change:
- clear previous eligibility timer before scheduling another
- keep ~2 second delay
- no duplicate `shownDays` increments from React effect reruns

`showThoughtBubble()` remains the only place that increments `shownDays`.

### 6) Preserve current R5.14 behavior
Keep:
- once per LOCAL calendar day
- max 10 shown days
- X/auto-hide hides for current day only
- click opens Smart Task directly
- successful `createTaskProposal` marks awareness completed
- completed user never sees bubble again
- failed/cancelled/opened-only flow does not complete onboarding

## Verification

Focused tests:
1. User A completed=true; switch in same SPA to fresh User B => B loads B's own state and can see bubble.
2. User A hidden launcher; switch to User B => Ramzy launcher/bubble is not inherited hidden.
3. User B already shown today => does not duplicate.
4. User B completed => does not show.
5. Fresh eligible user => bubble shows after ~2s.
6. no ramzy.use => no bubble.
7. no CREATE_TASK => no bubble.
8. execution disabled => no bubble.
9. repeated React effect rerender does not increment shownDays twice.
10. existing 10-day and successful-completion behavior still passes.

Frontend build + live QA with at least two test accounts in same browser/session.
Deploy frontend.
Commit locally.
User handles push through TOS system.

Return ONLY:
```
PATCH=RAMZY-SMART-TASK-R5.16-BUBBLE-RELIABILITY
PASS/FAIL=
USER_SWITCH_STATE_ISOLATION=
HIDDEN_STATE_RESET=
ELIGIBILITY_REASON=
NO_DUPLICATE_TIMER=
FRESH_USER_SHOWS=
SHOWN_TODAY_BLOCKS=
COMPLETED_BLOCKS=
TEN_DAY_LIMIT=
RBAC_PRESERVED=
FRONTEND_BUILD=
LIVE_MULTI_USER_QA=
LIVE_DEPLOY=
COMMIT=
PUSH=USER_HANDLES
ERROR=
```
