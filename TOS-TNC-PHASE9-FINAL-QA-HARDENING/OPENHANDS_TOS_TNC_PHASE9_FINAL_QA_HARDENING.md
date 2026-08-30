# TNC Phase 9 — Final QA & Hardening

## Canonical baseline
- Repository: `mohamedamouseo-a11y/TOS`
- Branch: `main`
- Required remote baseline: `de5a98b62b44080ae2840f3065786840ace37e26`
- Target server path: `/var/www/TOS`

## Goal
Close the known runtime/contract defects across TNC Phases 5–8 without adding new product features.

This is a focused integrity/hardening phase, not a redesign.

## Hard safety rules
- STOP if `origin/main` is not exactly the required baseline.
- STOP if working tree is dirty before implementation.
- No reset, rebase, force push, history rewrite, or push.
- No Prisma schema changes.
- No migrations.
- No DB changes.
- No Auth/session changes.
- No scheduler/cron/worker changes.
- Do not touch GitHub Sync UI or its CSS contracts.
- Preserve TNC Phase 1–8 behavior unless this spec explicitly fixes a defect.
- Keep scope limited to the files required below plus one focused regression test if needed.

---

## 9A — Fix Phase 6 frontend API namespace

File:
- `frontend/src/components/TncNotificationCenter.jsx`

Known defect:
Phase 6 critical/rules code still calls legacy `api.notification.*` methods while the canonical namespace is `api.notificationCenter.*`.

Required:
- Replace all TNC Phase 6 notification API calls with the canonical `api.notificationCenter` namespace.
- Confirm rules list, unacknowledged critical list, and acknowledge calls use methods that actually exist in `frontend/src/lib/api.js`.
- Do not create a second API namespace.

Acceptance:
- No `api.notification.` calls remain in `TncNotificationCenter.jsx`.
- Existing canonical `api.notificationCenter` calls remain intact.

---

## 9B — Repair Rules route Prisma/service contract

File:
- `backend/src/routes/notificationRules.routes.js`

Known defect:
The route passes Express `req` as the first argument to service functions that expect Prisma.

Required:
- Import canonical `prisma` from `../prisma.js`.
- Call `listRules`, `createRule`, `updateRule`, `deleteRule`, and `simulateRule` with `prisma` as the first argument.
- Preserve route paths and response shapes.
- Preserve existing auth behavior; do not redesign permissions in this phase unless required to match an already-existing canonical admin guard.

Acceptance:
- No rules service receives Express `req` as its Prisma argument.

---

## 9C — Repair Acknowledgement route Prisma/service contract

File:
- `backend/src/routes/notificationAcknowledgement.routes.js`

Known defect:
The route passes Express `req` as the first argument to acknowledgement services that expect Prisma.

Required:
- Import canonical `prisma` from `../prisma.js`.
- Pass `prisma` to:
  - `acknowledgeNotification`
  - `listUnacknowledgedCritical`
  - `getAcknowledgementStatus`
- Preserve route paths and response shapes.
- Preserve recipient ownership checks.

Acceptance:
- No acknowledgement service receives Express `req` as its Prisma argument.

---

## 9D — Fix Admin Governance persistence

File:
- `frontend/src/components/TncAdminCommandCenter.jsx`

Known defect:
Governance inputs mutate local `governance` state, but Save currently calls `handleSaveGovernance({})`, causing no edited values to be persisted.

Required:
- Save the current edited governance values to `updateAdminGovernance(...)`.
- Backend already validates/normalizes allowed governance keys; do not create a second schema client-side.
- After successful save:
  - reload governance,
  - reload analytics if needed,
  - reload audit so the new audit entry appears immediately.
- Keep the current save/loading/error UX.

Acceptance:
- Toggle/number change → Save → reload keeps the new value.
- Audit tab can show the corresponding governance change.

---

## 9E — Fix Admin Analytics + Audit response normalization

File:
- `frontend/src/components/TncAdminCommandCenter.jsx`

Known defects:
1. Analytics `breakdowns.bySource` is an object like `{ GENERAL, TCS }`, while `BreakdownCard` assumes an array and calls `.map()`.
2. Governance audit backend returns `{ entries, total }`, while the UI currently stores the whole object as if it were an array.
3. Risk total badge uses displayed item count instead of canonical backend total.

Required:
- Normalize breakdown inputs before rendering:
  - arrays stay arrays,
  - object maps convert to `{type/count}` or equivalent rows.
- Normalize audit API response to `data.entries || []`.
- Render risk total from `risk.risk.total` with safe fallback to `items.length`.
- Keep range selector behavior intact.
- No charting library additions.

Acceptance:
- Analytics tab does not throw when `bySource` is present.
- Audit tab renders real entries when backend returns them.
- Risk total reflects canonical total.

---

## 9F — Finish duplicate/dead contract cleanup

Files:
- `frontend/src/components/TncNotificationCenter.jsx`
- `frontend/src/hooks/useTncNotifications.jsx`

Known defects:
- Duplicate definitions of `toggleSelect`, `bulkMarkRead`, and `bulkMarkUnread` still exist in current GitHub source.
- `ACTION_CENTER` is now a frontend filter, but filtering/hydration must be explicit rather than relying on backend normalization fallback.

Required:
- Keep exactly one implementation each of:
  - `toggleSelect`
  - `bulkMarkRead`
  - `bulkMarkUnread`
- Preserve max selection = 50.
- For `ACTION_CENTER` hydration, explicitly request feed category `ALL` and let Action Center presentation filter actionable notification candidates in the frontend.
- Update `itemMatchesFilter` so realtime/socket items behave consistently while `ACTION_CENTER` is active.
- Remove dead `getActionableItems` / `fetchActions` code only if proven unused after checking this component; do not remove live behavior.

Acceptance:
- No duplicate function declarations remain.
- Action Center does not disappear or miss realtime items because of category mismatch.

---

## 9G — Focused regression validation

Do NOT run the whole repository test suite.

Required validation:
1. Add or extend one focused TNC regression test using the existing test style if practical within scope, covering at minimum the repaired service-route contract or Admin response normalization.
2. Run only that targeted TNC test.
3. Run one frontend build.
4. If backend files changed, run the narrowest existing backend syntax/test command needed for the touched TNC routes; do not run broad unrelated suites.
5. Smoke-check the deployed TNC only after all checks pass.

Manual smoke targets:
- Main TNC feed opens.
- Action Center opens.
- Critical acknowledgement call does not 500 from Prisma misuse.
- Admin Analytics opens with bySource data.
- Risk opens.
- Governance edit persists after Save/reload.
- Audit displays entries.
- Non-admin Admin Center gets clean 403/admin-only state.
- Dark + Light render without frame overflow.

---

## Commit / deploy

If all gates pass:
- Create exactly one local commit:
  `fix(tnc): harden phase 9 contracts and admin runtime`
- Deploy using the existing TOS production frontend/backend deployment path only if required by the touched files.
- DO NOT PUSH.

## Report only

Return exactly:

```text
BASE_SHA=
FILES_CHANGED=
LEGACY_API_NAMESPACE_FIXED=
RULES_PRISMA_CONTRACT_FIXED=
ACK_PRISMA_CONTRACT_FIXED=
GOVERNANCE_SAVE_FIXED=
ANALYTICS_SHAPE_FIXED=
AUDIT_SHAPE_FIXED=
RISK_TOTAL_FIXED=
DUPLICATE_FUNCTIONS_REMOVED=
ACTION_CENTER_CONTRACT_FIXED=
TARGETED_TEST=
FRONTEND_BUILD=
BACKEND_VALIDATION=
DARK_MODE=
LIGHT_MODE=
DEPLOYMENT=
COMMIT_SHA=
WORKTREE=
PUSH_PERFORMED=NO
BLOCKER=
```
