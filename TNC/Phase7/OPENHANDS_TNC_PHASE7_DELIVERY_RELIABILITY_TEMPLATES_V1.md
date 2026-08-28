# TNC Phase 7 — Delivery Reliability + Email Channel + Templates V1

## 0. EXECUTION CONTRACT — FOLLOW LITERALLY

Implementation repository: `/var/www/TOS`
Implementation GitHub repository: `mohamedamouseo-a11y/TOS`
Branch: `main`
Prompt repository: `mohamedamouseo-a11y/TOS-Patchs`
Prompt local path: `/var/www/TOS-Patchs/TNC/Phase7/OPENHANDS_TNC_PHASE7_DELIVERY_RELIABILITY_TEMPLATES_V1.md`
Prompt URL: `https://github.com/mohamedamouseo-a11y/TOS-Patchs/blob/main/TNC/Phase7/OPENHANDS_TNC_PHASE7_DELIVERY_RELIABILITY_TEMPLATES_V1.md`

Expected remote base when authored:
`5c1ba64e0260ccae0dad3a46e250dc4f23d3074e`

Local server tree is authoritative. Preserve any newer local commit.

MANDATORY:
- Work only in `/var/www/TOS` for implementation.
- Do NOT push TOS or TOS-Patchs.
- User performs Push manually from TOS Developer Hub.
- You ARE responsible for production deploy after validation.
- Server/terminal only. Do NOT claim browser QA.
- Implement first, then run ONE focused final validation pass.
- Create local commit only after validation succeeds.
- Do NOT reset/rebase/rewrite history.
- Do NOT create ZIP/TAR/GZ/7Z/RAR/archive files.
- Do NOT redesign TNC or create a standalone page.
- Do NOT create another notification source, unread system, socket namespace, scheduler, or generic workflow engine.
- Do NOT modify unrelated TCS/TWS/THRS/TCRM code.

The existing topbar-bell TNC panel is the host UI.

---

# 1. MANDATORY PRE-PHASE-7 INTEGRITY GATE

File:
`backend/src/services/notificationPreferences.service.js`

The current file contains invalid/stale governance handling that Phase 7 must not build on.

Required exact fixes:

1. Remove every invalid use of `value.governance` in functions where `value` is not defined.
2. `defaultNotificationPreferenceDocument()` must return a deterministic object and must NOT reference an undefined variable.
3. `normalizeCategorySettings()` must NOT inject governance into each category object.
4. `evaluateNotificationPolicy()` must NOT reference an undefined `value` and must return only the intended presentation fields.
5. `getEffectiveNotificationPreferences()` must NOT reference an undefined `value`.
6. Keep ONE module-level governance defaults object aligned with the current governance service, including Phase 3–6 flags:
   - automationEnabled
   - digestEnabled
   - escalationEnabled
   - maxEscalationLevel
   - allowUrgentQuietHoursBypass
   - analyticsEnabled
   - analyticsMaxWindowDays
   - actionCenterEnabled
   - workflowActionsEnabled
   - bulkActionsEnabled
   - savedViewsEnabled
   - rulesEngineEnabled
   - criticalAcknowledgementEnabled
   - roleDepartmentRoutingEnabled
   - ruleSimulationEnabled
7. `normalizeGlobalNotificationPolicy()` must reuse the module-level defaults; do not create a stale second defaults object.
8. Add focused regression tests proving defaults/normalize/save/evaluate functions do not throw and preserve existing Phase 2–6 behavior.

Do not continue to Phase 7 if this gate fails.

---

# 2. PHASE 7 V1 SCOPE

Build delivery reliability on top of canonical TNC.

V1 supports exactly:
- `IN_APP` delivery tracking using the existing canonical TNC/in-app notification architecture.
- `EMAIL` secondary delivery using the EXISTING SMTP configuration and Nodemailer infrastructure.

V1 does NOT implement real Web Push because no verified VAPID/Web Push provider exists in the current architecture.
Do not fake Web Push delivery.
Do not add browser push permission flows.

Canonical notification sources remain ONLY:
- `Notification` => source `GENERAL`
- `ChatNotification` => source `TCS`

---

# 3. ADDITIVE PRISMA MODELS — EXACTLY TWO

Add exactly two Phase 7 models unless an equivalent model already exists locally.

## 3.1 TncDeliveryOutbox

Conceptual schema:

```prisma
model TncDeliveryOutbox {
  id            String   @id @default(cuid())
  recipientId   String
  source        String
  nativeId      String
  channel       String
  status        String   @default("PENDING")
  templateKey   String?
  locale        String   @default("ar")
  attemptCount  Int      @default(0)
  nextAttemptAt DateTime?
  acceptedAt    DateTime?
  deliveredAt   DateTime?
  failedAt      DateTime?
  lastErrorCode String?
  metadata      Json?
  createdAt     DateTime @default(now())
  updatedAt     DateTime @updatedAt

  @@unique([recipientId, source, nativeId, channel])
  @@index([status, nextAttemptAt])
  @@index([recipientId, createdAt])
  @@index([channel, status, createdAt])
  @@index([source, nativeId])
}
```

Allowed channels in V1: `IN_APP`, `EMAIL`.

Allowed statuses:
- `PENDING`
- `PROCESSING`
- `DELIVERED`
- `SENT`
- `RETRYING`
- `FAILED`

Semantics:
- IN_APP may reach `DELIVERED` because the canonical notification exists in TNC.
- EMAIL may reach `SENT` when SMTP accepts the message. Do NOT claim mailbox delivery because SMTP acceptance does not prove end-user delivery.

`metadata` must be bounded and secret-free. Never store SMTP password, auth headers, cookies, tokens, raw request bodies, or full stack traces.

## 3.2 TncNotificationTemplate

```prisma
model TncNotificationTemplate {
  id              String   @id @default(cuid())
  key             String
  channel         String
  locale          String
  subjectTemplate String?
  bodyTemplate    String
  isActive        Boolean  @default(true)
  createdById     String?
  createdAt       DateTime @default(now())
  updatedAt       DateTime @updatedAt

  @@unique([key, channel, locale])
  @@index([channel, isActive])
  @@index([key, isActive])
  @@index([updatedAt])
}
```

Allowed channels for templates in V1: `EMAIL` only.
Allowed locales: `ar`, `en`.

Create ONE additive migration for both models.
Suggested directory:
`backend/prisma/migrations/20260829_tnc_phase7_delivery_templates/`

No destructive migration.

---

# 4. GOVERNANCE — EXTEND EXISTING SERVICE ONLY

Extend `backend/src/services/notificationGovernance.service.js`.

Add exactly:

```js
deliveryOrchestrationEnabled: true,
emailDeliveryEnabled: false,
deliveryRetryEnabled: true,
templateManagementEnabled: true,
deliveryMonitorEnabled: true,
```

Rules:
- `deliveryOrchestrationEnabled` default true.
- `emailDeliveryEnabled` default false for safety. Admin must explicitly enable it.
- `deliveryRetryEnabled` default true.
- `templateManagementEnabled` default true.
- `deliveryMonitorEnabled` default true.
- Include all in normalize + PATCH/update handling.
- Existing governance audit remains canonical.
- No new governance model/table.

Also align the Phase 7 governance defaults inside `notificationPreferences.service.js` with these flags after Section 1 is fixed.

---

# 5. USER DELIVERY PREFERENCES — EXTEND NotificationPreference JSON

Extend existing `NotificationPreference.settings` document only. No new preference table.

Add normalized section:

```json
{
  "delivery": {
    "emailEnabled": false,
    "emailMinimumPriority": "URGENT",
    "emailCategories": ["TCS", "TASKS", "TWS", "SYSTEM"],
    "respectQuietHours": true
  }
}
```

Validation:
- emailEnabled boolean
- emailMinimumPriority `NORMAL|IMPORTANT|URGENT`
- emailCategories allowlist only, max 4
- respectQuietHours boolean

Defaults:
- emailEnabled false
- minimum URGENT
- all categories allowed
- respectQuietHours true

Global governance always overrides user preferences.
If `emailDeliveryEnabled=false`, no email enqueue/send occurs regardless of user preference.

Quiet Hours:
- if `respectQuietHours=true`, email delivery waits until quiet hours end.
- URGENT may bypass only if existing policy/governance already allows urgent quiet-hours bypass.
- do not invent a second quiet-hours implementation; reuse existing helpers.

---

# 6. TEMPLATE ENGINE — STRICT AND SAFE

Create:
`backend/src/services/notificationTemplate.service.js`

Allowed template variables ONLY:
- `recipientName`
- `title`
- `body`
- `category`
- `priority`
- `actorName`
- `targetUrl`

Syntax: simple `{{variableName}}` replacement only.

Forbidden:
- JS expressions
- loops
- conditionals
- function calls
- arbitrary object paths
- eval/new Function
- HTML script tags
- raw unsanitized secret metadata

Required exports equivalent to:
- `normalizeTemplatePayload(payload)`
- `renderNotificationTemplate(template, variables)`
- `listNotificationTemplates(prisma, options)`
- `createNotificationTemplate(prisma, { actorId, payload })`
- `updateNotificationTemplate(prisma, { actorId, templateId, patch })`
- `setNotificationTemplateActive(prisma, { actorId, templateId, isActive })`
- `resolveNotificationTemplate(prisma, { key, channel, locale })`

Use existing governance audit service for:
- `TNC_TEMPLATE_CREATED`
- `TNC_TEMPLATE_UPDATED`
- `TNC_TEMPLATE_ENABLED`
- `TNC_TEMPLATE_DISABLED`

Seed/fallback behavior:
- Do NOT require destructive seed scripts.
- If no DB template exists, use a small deterministic built-in EMAIL fallback template in service code for `ar` and `en`.

Email body must be safe basic HTML/text generated from allowed variables only.

---

# 7. DELIVERY SERVICE

Create:
`backend/src/services/notificationDelivery.service.js`

Reuse:
- canonical Notification / ChatNotification
- existing notification normalization/intelligence/rulePolicy
- existing user preferences
- existing governance
- existing SMTP service: `getSmtpConfig()` and `createEmailTransporter()` from `emailSettings.service.js`

Do NOT create a second SMTP settings system.
Do NOT log SMTP credentials.

Required exports equivalent to:
- `ensureDeliveryRowsForRecipient(prisma, { recipientId, items, governance, preferences, now })`
- `listDeliveryOutbox(prisma, options)`
- `getDeliverySummary(prisma, options)`
- `processDeliveryBatch(prisma, options)`
- `processDeliveryRow(prisma, row, options)`
- `retryDelivery(prisma, { actorId, deliveryId })`

## 7.1 IN_APP tracking

For a canonical item considered by the delivery sweep:
- upsert unique IN_APP row
- mark `DELIVERED`
- deliveredAt should reflect bounded current processing time, not alter canonical notification read state

Do not create another in-app notification.

## 7.2 EMAIL eligibility

EMAIL row may be created only if ALL true:
- governance.deliveryOrchestrationEnabled
- governance.emailDeliveryEnabled
- user preference delivery.emailEnabled
- canonical recipient has a non-empty email
- item category is in user delivery.emailCategories
- effective priority meets emailMinimumPriority
- existing presentation/rule policy does not suppress the alert in a way that should prevent external delivery
- not currently blocked by quiet hours unless urgent bypass is already allowed

Critical rule-matched item requiring acknowledgement may still be email-eligible according to the same preference/governance rules; do not bypass explicit admin/user channel disable.

Use unique `(recipientId, source, nativeId, channel)` to prevent duplicate sends.

## 7.3 Retry behavior — EXACT

Maximum attempts: 5.

Backoff after failures:
1. 1 minute
2. 5 minutes
3. 15 minutes
4. 60 minutes
5. terminal FAILED

Before send:
- atomically transition eligible row to PROCESSING
- increment attemptCount once per actual send attempt

Success:
- EMAIL SMTP accepted => status `SENT`, acceptedAt now, clear nextAttemptAt/lastErrorCode

Transient failure:
- if attempts remain and deliveryRetryEnabled=true => `RETRYING`, set nextAttemptAt according to backoff

Terminal/non-retry failure or retries disabled => `FAILED`, failedAt now

Use bounded safe error codes, e.g.:
- SMTP_NOT_CONFIGURED
- SMTP_AUTH_FAILED
- SMTP_CONNECTION_FAILED
- SMTP_TIMEOUT
- SMTP_TLS_FAILED
- SMTP_RECIPIENT_REJECTED
- SMTP_MESSAGE_REJECTED
- UNKNOWN_SEND_ERROR

Do not store raw sensitive SMTP errors.

Manual admin retry:
- only FAILED/RETRYING EMAIL rows
- set PENDING and nextAttemptAt=now without resetting attemptCount
- audit using existing governance audit service action `TNC_DELIVERY_RETRY_REQUESTED`

---

# 8. USE EXISTING AUTOMATION SCHEDULER — NO NEW TIMER

Modify:
`backend/src/services/notificationAutomation.service.js`

Do NOT add another `setInterval`, cron, worker process, or scheduler.

Integrate delivery processing into the existing scheduler/lease flow.

Required:
- existing lease remains the single cross-process authority
- delivery work skipped when `deliveryOrchestrationEnabled=false`
- obtain recipient set using existing bounded batching pattern
- for each recipient, reuse current canonical notification item retrieval rather than creating another full unbounded scan
- create/ensure outbox rows in bounded chunks
- process due `PENDING|RETRYING` delivery rows in bounded batches
- suggested maximum send batch per scheduler cycle: 100 rows
- do not hold DB transaction open during SMTP network request
- use atomic claim/status transition before SMTP send
- scheduler failure must not corrupt existing Phase 3/6 automation state

No duplicate send across two PM2 instances under the same scheduler lease.

---

# 9. ADMIN ROUTES — SAME TNC ROUTE FAMILY

Create:
`backend/src/routes/notificationDelivery.routes.js`

Mount once under existing TNC prefix before generic API 404 fallback:
`app.use(`${API}/notification-center`, notificationDeliveryRoutes);`

Use auth and existing admin role pattern.

Required admin endpoints:
- `GET /api/notification-center/admin/delivery?status=&channel=&range=7d&page=1&limit=50`
- `GET /api/notification-center/admin/delivery/summary?range=7d`
- `POST /api/notification-center/admin/delivery/:deliveryId/retry`
- `GET /api/notification-center/admin/templates?channel=EMAIL&locale=`
- `POST /api/notification-center/admin/templates`
- `PATCH /api/notification-center/admin/templates/:templateId`
- `POST /api/notification-center/admin/templates/:templateId/enable`
- `POST /api/notification-center/admin/templates/:templateId/disable`

Limits:
- page size max 100
- range allowlist 7d/30d/90d
- no secret fields in responses
- non-admin => 403

User delivery preferences continue through the existing notification preferences route/API. Do not create a second user preferences endpoint unless the existing route cannot safely accept the delivery patch; if needed, extend the existing route only.

---

# 10. ANALYTICS — EXTEND EXISTING SERVICE

Extend `backend/src/services/notificationAnalytics.service.js`.

Add bounded delivery metrics:
- `deliveryTotal`
- `inAppDelivered`
- `emailSent`
- `emailFailed`
- `emailRetrying`
- `emailAcceptanceRate`
- `averageEmailAcceptanceMinutes`
- `deliveryByChannel`
- `topDeliveryFailureCodes` max 10

Semantics:
- emailAcceptanceRate is SMTP acceptance, NOT mailbox delivery rate.

Honor analytics governance/range limits.
No unbounded scan.

---

# 11. FRONTEND API — EXISTING CLIENT ONLY

Modify `frontend/src/lib/api.js`.

Add methods inside existing TNC/notification API structure for:
- admin delivery list
- delivery summary
- retry delivery
- template list/create/update/enable/disable
- saving delivery preferences through existing notification preferences API

No second API client.

---

# 12. FRONTEND UI — PRESERVE EXISTING TNC PANEL

Modify:
`frontend/src/components/TncNotificationCenter.jsx`

Do NOT redesign TNC.
Do NOT create a new page.

Inside existing Settings/Admin area add compact Phase 7 sections.

## 12.1 User delivery preferences

Visible to normal user:
- Email notifications toggle
- Minimum email priority select: Normal / Important / Urgent
- Category checkboxes: TCS / Tasks / TWS / System
- Respect Quiet Hours toggle

If global email delivery is disabled:
- controls show disabled state + small admin-disabled explanation
- do not pretend email is active

## 12.2 Admin Delivery Monitor

Admin only:
- summary counters: Email Sent / Failed / Retrying / In-App Delivered
- table/list of recent delivery rows
- filters status/channel/range
- bounded pagination
- retry button only on eligible failed/retrying email rows
- show safe error code only, not raw SMTP details

## 12.3 Template Manager

Admin only:
- template list
- locale ar/en
- key
- subject
- body
- active toggle
- Save
- show allowed variable chips exactly:
  `recipientName`, `title`, `body`, `category`, `priority`, `actorName`, `targetUrl`

Required UI support:
- Arabic/English
- RTL/LTR
- Light/Dark
- narrow responsive code

Browser QA = `BLOCKED_NO_BROWSER_ACCESS` unless an already-installed headless browser is used only to verify fatal runtime errors. Do not install a browser.

Frontend build mandatory.

---

# 13. DO NOT IMPLEMENT IN V1

Explicitly forbidden:
- real Web Push/VAPID
- SMS
- WhatsApp
- third-party marketing providers
- notification cloning/fan-out
- another SMTP settings table
- another notification source
- another scheduler
- arbitrary template code/eval
- template loops/conditions/scripts
- mailbox-delivery/open/read tracking pixels
- browser permission prompts

---

# 14. FINAL VALIDATION — RUN ONCE AT END

Implement first. Then execute and record all relevant checks.

Minimum required validation:

### Integrity gate
1. default preferences no undefined-variable crash
2. normalize preferences preserves Phase 2–7 structure
3. evaluate policy no undefined-variable crash
4. save/merge preferences preserves delivery section
5. Phase 5/6 governance flags remain normalized

### Delivery eligibility
6. global email disabled => no email row/send
7. user email disabled => no email row/send
8. minimum priority enforced
9. category allowlist enforced
10. missing recipient email => no email send
11. quiet hours delay email
12. allowed urgent bypass behavior preserved
13. unique delivery row prevents duplicates
14. GENERAL canonical notification supported
15. TCS canonical notification supported
16. foreign recipient isolation

### Templates
17. unknown template variable rejected
18. script/expression content cannot execute
19. ar/en rendering deterministic
20. DB template resolution + fallback template behavior
21. non-admin template mutations rejected

### Retry/concurrency
22. SMTP accepted => SENT exactly once
23. transient failure => RETRYING with 1m backoff
24. subsequent retry backoffs 5m/15m/60m
25. fifth failure => FAILED
26. retries disabled => FAILED without scheduling next retry
27. manual retry authorization + audit
28. two scheduler instances under lease cannot duplicate send
29. existing scheduler lease/batching tests remain green
30. SMTP request occurs outside long DB transaction

### Regression
31. Phase 6 rules/ack tests
32. Phase 5 action tests
33. Phase 4 governance/analytics tests
34. core notification-center tests
35. relevant TCS unread/realtime tests
36. Prisma validate
37. Prisma generate
38. migration status
39. backend syntax/import/startup
40. frontend build
41. `git diff --check`
42. `git status` and changed-file scope
43. no archive files in outgoing local commits

Do not claim PASS without actual command evidence.
Do not run unrelated full-system suites unless a focused failure requires it.

---

# 15. LOCAL COMMIT

After required validation passes, create ONE local commit.

Suggested message:
`feat(tnc): add reliable email delivery and templates`

Do NOT push.

Record START_SHA and FINAL_LOCAL_SHA.

---

# 16. DEPLOY

After successful local commit:
- use canonical existing TOS production deployment flow
- verify actual nginx/frontend serving directory, do not assume
- ensure built frontend is actually copied/published to the serving directory

Verify:
- tamiyouz-system ONLINE
- frontend process ONLINE if applicable
- actual backend port health 200
- public `https://tos.tamiyouz.com` HTTP 200
- current JS/CSS assets referenced by production index exist and return 200
- no 502/5xx
- migration applied
- no backend startup/import errors

If an already-installed headless browser exists, verify application root renders and no fatal runtime exception. Do not install one.

---

# 17. FINAL REPORT — MARKDOWN ONLY

Create exactly:

`/var/www/TOS-Patchs/TNC/Phase7/TNC_PHASE7_DELIVERY_RELIABILITY_TEMPLATES_V1_REPORT.md`

No ZIP/archive.
Do not place report inside `/var/www/TOS`.
Do not push TOS-Patchs.

Report must include:
- `IMPLEMENTATION=PASS|FAIL|BLOCKED`
- `FINAL_VALIDATION=PASS|FAIL|BLOCKED`
- START_SHA
- FINAL_LOCAL_SHA
- commit message
- exact files changed/count
- integrity gate fixes
- Prisma models/migration
- governance flags
- user delivery preference schema
- delivery eligibility behavior
- IN_APP vs EMAIL status semantics
- retry/backoff behavior
- SMTP reuse confirmation
- template variable allowlist
- admin routes
- analytics additions
- frontend additions
- exact validation commands + pass/fail counts
- frontend build result
- actual production serving directory
- PM2/backend/public/assets health
- `BROWSER_QA=BLOCKED_NO_BROWSER_ACCESS` if no existing headless browser
- `PUSH_PERFORMED=NO`
- `DEPLOYMENT_PERFORMED=YES|NO`
- exact report path

Final OpenHands response must contain only:
- IMPLEMENTATION
- FINAL_VALIDATION
- FINAL_LOCAL_SHA
- changed file count
- migration status
- FRONTEND_BUILD
- DEPLOYMENT_PERFORMED
- PUSH_PERFORMED=NO
- BROWSER_QA status
- exact report path
