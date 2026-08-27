# Manus Execution Prompt — TNC Phase 2: Preferences + Smart Control V1

## Mission
Implement **TNC Phase 2 — Preferences + Smart Control V1** in the canonical production TOS stack.

This phase must build on the existing TNC unified inbox/realtime architecture. Do **not** create a second notification system, second socket system, or parallel inbox.

## Repositories / working location
- Prompt repository only: `mohamedamouseo-a11y/TOS-Patchs`
- Actual implementation repository: `mohamedamouseo-a11y/TOS`
- Branch: `main` only
- Work inside: `/var/www/TOS`
- Current known remote base at prompt creation: `645c48fc99944d250035d173510f09c5fabf2362`

## Mandatory prerequisite gate — Phase 1.1 correctness
Before Phase 2 work, verify whether TOS/main already contains the requirements of:
`TNC/Phase1/MANUS_TNC_PHASE1_FILTER_COUNTS_CORRECTNESS_FIX_V1_1.md`

At prompt creation time the remote head still does **not** contain that fix. Therefore, if the current working/remote head is still based on `645c48fc99944d250035d173510f09c5fabf2362`, implement the Phase 1.1 correctness fix FIRST.

Phase 1.1 prerequisite acceptance:
1. TASKS / TWS / SYSTEM unread counts are exact beyond 100 items.
2. Category feeds do not miss older matching generic notifications because of a pre-filter limit.
3. `hasMore` is correct for the requested category.
4. Add regression tests with >100 notifications.
5. Preserve existing Notification + ChatNotification architecture.
6. Prefer backend-only changes for this prerequisite.

Keep the prerequisite as a separate local commit when practical, e.g.:
`fix(tnc): correct category counts and filtered feeds`

Do not proceed to Phase 2 feature implementation until the Phase 1.1 tests pass.

---

# Phase 2 Product Goal
Turn TNC from a unified feed into a controllable personal notification workspace.

Users must be able to control **how notifications surface** without deleting, hiding, or losing the underlying notification records.

Inbox correctness always wins:
- Muted notifications still exist in TNC.
- Snoozed notifications still exist in TNC.
- Quiet-hours notifications still exist in TNC.
- Realtime state/unread counts still update while alerts are suppressed.
- Preferences control alert presentation, not data creation/history.

## Existing architecture that MUST be reused
- Prisma `Notification` model for general/system/work/task/TWS notifications.
- Prisma `ChatNotification` model for TCS notifications.
- Existing `/api/notification-center` unified feed/read APIs.
- Existing `chat:notification` TCS realtime event.
- Existing `tnc:notification` generic realtime rehydration event.
- Existing `TncNotificationsProvider` / hook and Topbar Bell launcher.
- Existing TNC component/UI and safe deep-link target resolution.
- Existing `OperationsSettings.notificationSettings` is **global/operator policy**, not per-user preference storage.

Do not repurpose `OperationsSettings.notificationSettings` as a single user's settings.

---

# 1. Per-user preference persistence
First inspect the current Prisma schema and backend for any existing suitable per-user notification preference store.

If none exists (expected), add ONE minimal additive model for TNC user preferences, for example:

```prisma
model NotificationPreference {
  id        String   @id @default(cuid())
  userId    String   @unique
  settings  Json     @default("{}")
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt

  user User @relation(fields: [userId], references: [id], onDelete: Cascade)

  @@index([updatedAt])
}
```

Use naming consistent with the existing schema. Add the matching optional relation on `User` only if required by Prisma.

A minimal additive Prisma migration is allowed for this phase **only if no suitable store already exists**.

Migration safety:
- No destructive schema changes.
- No table resets.
- No dropping existing data.
- No production `prisma migrate reset`.
- Validate schema and migration status.
- Use established production deployment/migration procedure.

## Preference document schema
Store a versioned JSON preference document so future TNC settings do not require a migration for every toggle.

Use an explicit normalized server-side schema similar to:

```json
{
  "version": 1,
  "categories": {
    "TCS":    { "alertsEnabled": true, "priorityThreshold": "NORMAL", "soundEnabled": false, "desktopEnabled": false },
    "TASKS":  { "alertsEnabled": true, "priorityThreshold": "NORMAL", "soundEnabled": false, "desktopEnabled": false },
    "TWS":    { "alertsEnabled": true, "priorityThreshold": "NORMAL", "soundEnabled": false, "desktopEnabled": false },
    "SYSTEM": { "alertsEnabled": true, "priorityThreshold": "IMPORTANT", "soundEnabled": false, "desktopEnabled": false }
  },
  "mutedTypes": [],
  "snoozeUntil": null,
  "quietHours": {
    "enabled": false,
    "start": "22:00",
    "end": "08:00",
    "timezone": "Africa/Cairo",
    "allowUrgent": false
  },
  "grouping": {
    "enabled": true,
    "windowMinutes": 10
  }
}
```

This is a behavior contract, not a requirement to copy these exact field names if the existing codebase has a stronger convention.

Server must sanitize/normalize all values. Do not trust arbitrary JSON from the client.

---

# 2. Global policy vs user preference
Treat existing `OperationsSettings.notificationSettings` as the global policy/default layer.

User preferences may make notifications quieter, but must not enable a capability that global policy disables.

Examples:
- If global `inAppEnabled` is false, do not surface optional in-app TNC alerts.
- If global `soundEnabled` is false, a user sound preference cannot force sound on.
- If global `desktopNotifications` is false, a user desktop preference cannot force it on.
- Existing global type gates such as task/SLA/project/system notification settings must remain authoritative where applicable.

Do not break the existing admin Settings page or its current notification configuration.

Create a single policy evaluation function/service so mute, snooze, quiet-hours, category controls and global policy are not reimplemented differently across components.

Expected output concept:

```js
{
  inbox: true,
  alert: boolean,
  sound: boolean,
  desktop: boolean,
  suppressedBy: null | "MUTED_CATEGORY" | "MUTED_TYPE" | "SNOOZE" | "QUIET_HOURS" | "PRIORITY_THRESHOLD" | "GLOBAL_POLICY"
}
```

`inbox` should remain true for normal authenticated TNC records.

---

# 3. Preferences API
Add authenticated, user-scoped endpoints under the existing notification center route family.

Minimum capabilities:
- GET current effective personal preferences.
- PATCH personal preferences with strict validation.
- Snooze until a supplied future timestamp.
- Clear snooze / resume notifications.
- Reset personal preferences to defaults.

Recommended route shape (adapt to project conventions if needed):
- `GET /api/notification-center/preferences`
- `PATCH /api/notification-center/preferences`
- `POST /api/notification-center/preferences/snooze`
- `DELETE /api/notification-center/preferences/snooze`
- `POST /api/notification-center/preferences/reset`

Every endpoint must operate only on `req.user.id`.

No endpoint may accept a userId to modify another user's preferences in this phase.

---

# 4. Mute controls
Support category-level alert mute for:
- TCS
- Tasks
- TWS
- System

Also support exact notification-type mute via `mutedTypes`.

From notification item actions, provide a useful action such as:
- Mute this notification type

Muted items:
- remain in feed;
- remain counted unread;
- remain deep-linkable;
- do not trigger intrusive toast/sound/desktop presentation while muted.

Unmute must be available from TNC Preferences.

---

# 5. Snooze
Add user snooze controls:
- 1 hour
- Until tomorrow / next workday start if a strong existing date utility exists; otherwise use a clear tomorrow option
- Custom date/time
- Resume now

Snooze must suppress intrusive alert presentation only. It must NOT stop realtime hydration or unread counts.

Expired snooze must automatically cease affecting policy without requiring a data rewrite.

---

# 6. Quiet Hours
Add per-user Quiet Hours:
- Enabled toggle
- Start time
- End time
- Timezone
- Allow Urgent during Quiet Hours toggle

Must correctly support windows that cross midnight, e.g. `22:00 -> 08:00`.

Default timezone: `Africa/Cairo` unless an existing user/system timezone source should be reused.

When Quiet Hours are active:
- TNC inbox and unread counts continue normally.
- Suppress alert/sound/desktop according to policy.
- If `allowUrgent` is enabled, only `URGENT` may bypass.

Add deterministic unit tests for normal and overnight windows.

---

# 7. Priority control
Reuse Phase 1 priority normalization (`URGENT`, `IMPORTANT`, `NORMAL`). Do not invent a second priority classifier in the frontend.

Per category, let the user choose an alert threshold:
- All (`NORMAL` and above)
- Important + Urgent
- Urgent only

This affects alert presentation only, not inbox visibility.

---

# 8. Grouping / notification bundling
Add UI grouping for similar notifications while preserving individual source rows.

Grouping is a view concern; do not merge/delete database notifications.

Use a deterministic grouping key based on available context, e.g. category + type + target identity, within the configured grouping window.

Examples:
- 8 task comment notifications for the same task may appear as one grouped card with count `8`.
- Multiple TCS messages from the same conversation may group when appropriate.

Grouped cards must:
- show count;
- show useful latest title/body/actor context;
- expand or reveal children;
- support opening the latest relevant target;
- support marking the grouped children read.

If needed, add a secure batch-read endpoint using `{ source, nativeId }` pairs rather than exposing raw model selection.

Grouping must not produce incorrect unread totals.

---

# 9. TNC Preferences UX/UI
Add a clear settings entry inside the TNC experience (gear/settings action). Do not force ordinary users into the global Admin Settings page.

The TNC preference surface should be polished but compact.

Recommended structure:
- General status / snooze banner
- Categories
  - TCS
  - Tasks
  - TWS
  - System
- Per-category: Alerts, Priority threshold, Sound, Desktop
- Quiet Hours
- Muted Types
- Grouping
- Reset to defaults

Requirements:
- Arabic RTL and English LTR
- Light and Dark mode
- Desktop and mobile
- Keyboard accessible
- Proper labels/tooltips
- No horizontal overflow
- No dense admin-style wall of toggles

The global Admin notification settings page must remain distinct and operational.

---

# 10. Desktop notifications and sound safety
If desktop notifications are supported:
- Never request browser Notification permission automatically on page load.
- Permission request must happen only from an explicit user action.
- Gracefully handle denied/default/unsupported states.
- Never expose notification content to unauthorized browser contexts.

If sound is supported:
- Respect browser autoplay rules.
- Prefer an existing TOS notification sound mechanism if one exists.
- No repeated sound storm for grouped bursts.

If no safe existing sound mechanism exists, the UI preference may be implemented with a disabled/explanatory state rather than adding fragile media code.

---

# 11. Realtime behavior
Do NOT unsubscribe from `chat:notification` or `tnc:notification` because a user muted/snoozed alerts.

Realtime must continue to:
- hydrate inbox;
- keep counts correct;
- reconcile on reconnect;
- reconcile on browser visibility restore;
- preserve Phase 1 behavior.

Policy evaluation decides only whether to surface intrusive alerts.

Avoid duplicate socket listeners and duplicate unread increments.

---

# 12. Existing workflows must remain intact
Preserve:
- Design Request notification flows and login alerts.
- TCS global unread mechanics and chat read reconciliation.
- Existing generic `/api/users/notifications` endpoints for legacy consumers.
- Existing Topbar Bell entry point.
- Existing safe notification deep links.
- Existing TNC unified read/unread actions.
- Existing app routing.
- Existing admin `notificationSettings` configuration.

Do not touch legacy root `client/`, `server/`, or `drizzle/` implementation stack.

Canonical stack only:
- `frontend/`
- `backend/`

---

# 13. Tests / verification
Mandatory automated checks:
1. Phase 1.1 >100 notification category count/feed regression tests pass.
2. Preference normalization/validation tests.
3. User ownership/auth tests for preference endpoints.
4. Policy tests for:
   - category mute;
   - exact type mute;
   - snooze active/expired;
   - quiet hours normal window;
   - quiet hours crossing midnight;
   - urgent bypass enabled/disabled;
   - priority threshold;
   - global policy override.
5. Grouping tests for deterministic keys/counts without unread corruption.
6. Prisma validate.
7. Prisma migration status and migration verification if a migration is needed.
8. Backend test suite relevant to TNC.
9. Frontend production build.

Mandatory live QA where browser access is available:
- Bell opens TNC.
- ALL / UNREAD / TCS / TASKS / TWS / SYSTEM remain correct.
- Mark read/unread and mark category/all read.
- Mute category and verify new item remains in inbox but no intrusive alert.
- Mute exact type and unmute.
- Snooze 1 hour and Resume now.
- Quiet Hours UI and policy behavior.
- Priority threshold behavior.
- Grouped notifications expand and mark read correctly.
- Arabic/English.
- Light/Dark.
- Desktop/mobile.
- No horizontal overflow.
- TCS realtime and generic realtime still update counts/feed.
- Browser console free of new errors.

If browser QA is blocked by environment/authentication, state the exact limitation in the report; do not fabricate PASS evidence.

---

# 14. Commit / Push / Deploy policy
Work locally in `/var/www/TOS`.

Prefer two implementation commits if Phase 1.1 is still missing:
1. `fix(tnc): correct category counts and filtered feeds`
2. `feat(tnc): add notification preferences and smart controls`

If Phase 1.1 is already present remotely, only the Phase 2 commit is needed.

CRITICAL PUSH RULES:
- DO NOT use terminal `git push`.
- DO NOT use SSH push.
- DO NOT use GH CLI push.
- DO NOT use Deploy Key push.
- Push ONLY from inside the running TOS system using Developer Hub / GitHub integration.
- Push to `mohamedamouseo-a11y/TOS` branch `main`.
- Verify the final remote SHA after the in-system push.

Deploy only after successful in-system push.

Deployment:
- If a Prisma migration was required, use the established safe production migration/deploy flow and capture evidence.
- Deploy minimum required scope, but because Phase 2 is expected to include backend + frontend (and possibly additive migration), ensure both affected runtime scopes are actually refreshed.
- Run production preflight/health checks after deployment.

---

# 15. Report package
Return exactly:
`TNC_PHASE2_PREFERENCES_SMART_CONTROL_V1_REPORT.zip`

The report ZIP must include:
- executive summary;
- starting SHA(s);
- Phase 1.1 prerequisite status and whether it required a commit;
- final local commit SHA(s);
- Developer Hub in-system push receipt;
- verified remote `TOS/main` SHA;
- changed-file list;
- Prisma migration file/name if created;
- migration/Prisma validation evidence;
- backend test evidence;
- frontend build evidence;
- deployment receipt;
- production health/preflight evidence;
- live QA evidence/screenshots when available;
- explicit remaining limitations/blockers;
- statement confirming no duplicate notification/socket system was created.

## Final acceptance
Phase 2 is PASS only when:
- Phase 1.1 correctness is resolved;
- user preferences persist per user;
- global policy remains authoritative;
- mute/snooze/quiet-hours/priority suppress alerts without losing inbox data;
- grouping preserves underlying notifications and unread correctness;
- realtime remains reliable;
- admin global notification settings remain intact;
- TNC settings work in Arabic/English and Light/Dark;
- remote GitHub main is verified after in-system push;
- deployment and health checks pass.
