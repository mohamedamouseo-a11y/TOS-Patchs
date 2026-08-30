# TNC Phase 9.1 — Post-Push Correction

## Required baseline
`ef216815b6ea6ea947e8a87be9a4691a6a03581a`

Target: `/var/www/TOS`

This is a narrow correction after fresh GitHub review of Phase 9. Do not add features.

## Scope
Only these files may change:
- `frontend/src/components/TncNotificationCenter.jsx`
- `frontend/src/components/TncAdminCommandCenter.jsx`
- `frontend/src/hooks/useTncNotifications.jsx`

## Fix 1 — duplicate bulk/select functions
In `TncNotificationCenter.jsx`, there are still two definitions each of:
- `toggleSelect`
- `bulkMarkRead`
- `bulkMarkUnread`

Keep exactly one canonical implementation of each. Preserve the 50-item selection cap and current behavior.

After edit, static assertion must find exactly one definition of each function.

## Fix 2 — Analytics breakdown normalization
Backend contract is mixed:
- `breakdowns.bySource` is an object such as `{ GENERAL: n, TCS: n }`
- `breakdowns.byPriority` is already an array such as `[{ priority: "URGENT", count: n }, ...]`

In `TncAdminCommandCenter.jsx`, add/use a safe normalizer:
- if value is already an array, return it unchanged
- if value is an object, convert `Object.entries(value)` into `{ type, count }[]`
- otherwise return `[]`

Use the safe normalizer for both `bySource` and `byPriority`.
Do NOT call `Object.entries()` directly on an already-array response.

Also ensure the Analytics priority breakdown label is defined in both Arabic and English (`priority`).

## Fix 3 — ACTION_CENTER canonical feed/realtime contract
In `useTncNotifications.jsx`:
- when `nextFilter === "ACTION_CENTER"`, request backend feed category `ALL` (same pattern as DIGEST)
- do not send unsupported `ACTION_CENTER` as backend category
- for realtime `itemMatchesFilter(..., "ACTION_CENTER")`, match the same actionable contract used by the UI: item has both `source` and `nativeId`
- SYSTEM notifications must not be excluded merely because category is SYSTEM
- preserve ALL/UNREAD/ATTENTION/TCS/TASKS/TWS/SYSTEM behavior

## Safety
- No backend changes
- No Prisma/schema/migration/DB/Auth changes
- No scheduler changes
- Do not touch GitHub Sync UI or global CSS
- Preserve TNC Phase 1–9

## Validation
1. Confirm exact baseline SHA and clean worktree before editing.
2. Run one no-write static regression check asserting:
   - exactly one `toggleSelect`
   - exactly one `bulkMarkRead`
   - exactly one `bulkMarkUnread`
   - safe breakdown normalizer preserves arrays and converts objects
   - ACTION_CENTER feedCategory resolves to ALL
   - ACTION_CENTER realtime predicate uses source + nativeId and does not exclude SYSTEM
3. Run one frontend build only.
4. Deploy frontend only after validation.
5. Create one local commit:
   `fix(tnc): correct phase 9 post-push regressions`
6. DO NOT PUSH.

## Return only
BASE_SHA=
FILES_CHANGED=
DUPLICATES_REMOVED=
ANALYTICS_ARRAY_SAFE=
ANALYTICS_OBJECT_SAFE=
PRIORITY_LABEL_FIXED=
ACTION_CENTER_FEED_ALL=
ACTION_CENTER_REALTIME_FIXED=
SYSTEM_ACTIONABLE_PRESERVED=
STATIC_REGRESSION_TEST=
FRONTEND_BUILD=
DEPLOYMENT=
COMMIT_SHA=
WORKTREE=
PUSH_PERFORMED=NO
BLOCKER=
