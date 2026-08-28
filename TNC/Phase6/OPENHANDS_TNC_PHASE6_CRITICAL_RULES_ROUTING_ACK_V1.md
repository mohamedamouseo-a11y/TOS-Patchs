# TNC Phase 6 — Critical Alerts + Rules + Recipient Routing + Acknowledgement V1

## 0. EXECUTION CONTRACT — FOLLOW LITERALLY

Implementation repository: `/var/www/TOS`
Implementation GitHub repository: `mohamedamouseo-a11y/TOS`
Branch: `main`
Prompt repository: `mohamedamouseo-a11y/TOS-Patchs`
Prompt local path: `/var/www/TOS-Patchs/TNC/Phase6/OPENHANDS_TNC_PHASE6_CRITICAL_RULES_ROUTING_ACK_V1.md`
Prompt GitHub URL: `https://github.com/mohamedamouseo-a11y/TOS-Patchs/blob/main/TNC/Phase6/OPENHANDS_TNC_PHASE6_CRITICAL_RULES_ROUTING_ACK_V1.md`

Expected remote TOS base when this prompt was authored:
`c908497e768328b7016f88c209323d17b140f72f`

The local server tree is authoritative. Before changing anything, verify the actual local `main` and preserve every newer local commit if one exists.

MANDATORY:
- Work only in `/var/www/TOS` for implementation.
- Do NOT push TOS or TOS-Patchs.
- Do NOT run `git push`, `gh`, SSH push, deploy-key push, or Developer Hub Push.
- The user performs Push manually from TOS Developer Hub after review.
- You ARE responsible for production deployment after validation.
- You have server/terminal access only. Do NOT claim browser QA.
- Implement first. Do NOT repeatedly run broad tests while editing.
- Run one focused validation pass at the end.
- Create local commit only after validation succeeds.
- Deploy after the local commit.
- Final report must be Markdown in TOS-Patchs, never in TOS.
- Do NOT create ZIP/TAR/GZ/7Z/RAR/archive files anywhere in `/var/www/TOS` or outgoing Git history.
- Do NOT reset/rebase/rewrite history.
- Do NOT change unrelated TCS/TWS/THRS/TCRM code.

The existing TNC visual panel shown by the user is the required host UI. DO NOT redesign TNC, DO NOT create a separate page, and DO NOT create a second notification center.

---

# 1. MANDATORY PHASE 5 INTEGRITY GATE — FIX BEFORE PHASE 6

The current `TOS/main` has three known Phase 5 integration defects. Fix them first. Do not skip this section.

## 1.1 Governance normalization defect

File:
`backend/src/services/notificationGovernance.service.js`

Current defaults already include:
- `actionCenterEnabled`
- `workflowActionsEnabled`
- `bulkActionsEnabled`
- `savedViewsEnabled`

But `normalizeGovernanceSettings()` and `updateGovernanceSettings()` do not fully preserve/update these fields.

Required exact behavior:
- Add all four booleans to `normalizeGovernanceSettings()`.
- Default each to `true` unless explicitly `false`.
- Add all four booleans to the accepted patch fields in `updateGovernanceSettings()`.
- Preserve all Phase 4 fields unchanged.
- Add tests proving values survive GET -> PATCH -> GET normalization.

## 1.2 Non-existent `tncNotification` source defect

Files:
- `backend/src/routes/tncAction.routes.js`
- `backend/src/services/tncAction.service.js`

The canonical notification sources are ONLY:
- Prisma `Notification` for source `GENERAL`
- Prisma `ChatNotification` for source `TCS`

There is no canonical `TncNotification` source of truth.

Required exact fix:
- Remove every runtime dependency on `prisma.tncNotification`.
- Resolve a notification by `source + nativeId + recipientId`.
- `GENERAL` -> `prisma.notification.findFirst({ where: { id: nativeId, recipientId } })`.
- `TCS` -> `prisma.chatNotification.findFirst({ where: { id: nativeId, recipientId } })`.
- Reject unknown source with 400.
- Reject notification not owned by current recipient with 404/403 using existing error conventions.
- Reuse helpers from `notificationCenter.service.js` where possible for normalization/targeting.
- Do NOT create a `TncNotification` Prisma model.
- Do NOT copy canonical notification rows into a new TNC table.

Action descriptors must be backend-authoritative.
Do not expose fake domain workflow actions. If there is no verified canonical authorized domain operation, expose only existing safe TNC-native actions / OPEN navigation.

## 1.3 Missing action-route mount defect

File:
`backend/src/app.js`

`tncActionRoutes` is imported but is not mounted before the API 404 fallback.

Required exact fix:
Mount it once:
`app.use(`${API}/notification-center/actions`, tncActionRoutes);`

It must be mounted before the generic `${API}` 404 fallback.
Do not mount it twice.

Phase 5 integrity gate must have focused tests before Phase 6 is considered valid.

---

# 2. PHASE 6 MISSION

Build **TNC Phase 6 — Critical Alerts + Rules + Recipient Routing + Acknowledgement V1** on top of the existing Phase 1–5 architecture.

Phase 6 adds:
1. deterministic notification rules
2. role/department recipient targeting
3. critical alert acknowledgement
4. unacknowledged critical alert handling
5. admin rule management + simulation
6. rule/ack auditability
7. Phase 3 escalation integration
8. Phase 4 analytics/governance integration

Do NOT create another notification source, another unread system, another socket namespace, another scheduler, or another workflow engine.

Canonical sources remain:
- `Notification`
- `ChatNotification`

---

# 3. V1 ROUTING SEMANTICS — IMPORTANT

For Phase 6 V1, **routing means recipient-targeted rule application**, NOT cloning notifications to arbitrary new users.

This is mandatory for safety.

A rule may target:
- System roles
- Departments

The rule is applied only when the canonical notification already belongs to that recipient AND the recipient matches the configured audience.

Examples:
- `roles=[MANAGER,ADMIN]` -> the rule affects only matching recipients.
- `departments=[SALES]` -> the rule affects only matching recipients.

Do NOT fan-out/clone TCS notifications to additional users.
Do NOT create notification copies for users who were not canonical recipients.
Do NOT bypass project/chat/task permissions.

This still allows administrators to define rules such as “Sales urgent alerts require acknowledgement” without creating a second distribution system.

---

# 4. ADDITIVE PRISMA MODELS

Add exactly two focused models unless an equivalent Phase 6 model already exists locally.

## 4.1 `TncNotificationRule`

Use this conceptual shape, adapting relation syntax only as required by the existing schema:

```prisma
model TncNotificationRule {
  id          String   @id @default(cuid())
  name        String
  description String?
  isActive    Boolean  @default(true)
  sortOrder   Int      @default(0)
  conditions  Json     @default("{}")
  actions     Json     @default("{}")
  createdById String?
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt

  @@index([isActive, sortOrder])
  @@index([createdById])
  @@index([updatedAt])
}
```

Do not add arbitrary script/code fields.

## 4.2 `TncAcknowledgement`

```prisma
model TncAcknowledgement {
  id             String   @id @default(cuid())
  recipientId    String
  actorId        String
  source         String
  nativeId       String
  ruleId         String?
  acknowledgedAt DateTime @default(now())
  metadata       Json?
  createdAt      DateTime @default(now())

  @@unique([recipientId, source, nativeId])
  @@index([recipientId, acknowledgedAt])
  @@index([source, nativeId])
  @@index([ruleId])
  @@index([createdAt])
}
```

`metadata` must contain only bounded safe values. Never store tokens, cookies, passwords, Authorization headers, raw request bodies, or secrets.

Create ONE additive migration for both models.
Suggested migration directory:
`backend/prisma/migrations/20260828_tnc_phase6_rules_ack/`

No destructive schema changes.

---

# 5. GOVERNANCE — EXACT NEW FLAGS

Extend the existing `notificationGovernance.service.js` only.
Do NOT create another governance table/model.

Add exactly these Phase 6 settings:

```js
rulesEngineEnabled: true,
criticalAcknowledgementEnabled: true,
roleDepartmentRoutingEnabled: true,
ruleSimulationEnabled: true,
```

Required:
- Include them in defaults.
- Include them in normalization.
- Include them in PATCH/update handling.
- Defaults are `true` unless explicitly `false`.
- Existing Phase 3/4/5 governance fields must remain intact.
- Governance changes remain audited using existing `TncGovernanceAudit`; do not create a second governance audit table.

---

# 6. RULE DOCUMENT FORMAT — STRICT ALLOWLIST

`conditions` may contain ONLY:

```json
{
  "sources": ["GENERAL", "TCS"],
  "categories": ["TCS", "TASKS", "TWS", "SYSTEM"],
  "types": ["EXACT_NOTIFICATION_TYPE"],
  "priorities": ["NORMAL", "IMPORTANT", "URGENT"],
  "roles": ["SUPER_ADMIN", "ADMIN", "MANAGER", "PROJECT_MANAGER", "TEAM_MEMBER", "FORMER_EMPLOYEE", "CLIENT"],
  "departments": ["CONTENT", "DESIGN", "DEVELOPMENT", "SEO", "ACCOUNT_MANAGER", "OPERATION", "SALES", "CLIENT", "OTHER"]
}
```

Empty array means “no restriction for this field”.

No regex.
No SQL.
No JS expressions.
No arbitrary query language.
No user-supplied function names.
No dynamic code.

`actions` may contain ONLY:

```json
{
  "critical": true,
  "requiresAcknowledgement": true,
  "escalateAfterMinutes": 30,
  "priorityOverride": "URGENT"
}
```

Validation:
- `critical`: boolean
- `requiresAcknowledgement`: boolean
- `escalateAfterMinutes`: integer 5..10080 or null
- `priorityOverride`: `NORMAL|IMPORTANT|URGENT|null`

Hard maximum active rules evaluated per request/sweep: 100.
Hard maximum rule list page size: 100.

---

# 7. BACKEND SERVICES — CREATE THESE FILES

Create:

1. `backend/src/services/notificationRules.service.js`
2. `backend/src/services/tncAcknowledgement.service.js`
3. `backend/src/services/notificationRules.service.test.js`

Do not create additional generic engines.

## 7.1 `notificationRules.service.js`

Must export focused functions equivalent to:

- `normalizeRuleConditions(value)`
- `normalizeRuleActions(value)`
- `listNotificationRules(prisma, options)`
- `createNotificationRule(prisma, { actorId, payload })`
- `updateNotificationRule(prisma, { actorId, ruleId, patch })`
- `setNotificationRuleActive(prisma, { actorId, ruleId, isActive })`
- `evaluateNotificationRules(prisma, { item, recipient, governance, rules? })`
- `simulateNotificationRule(prisma, { actorId, payload, range })`

Rule evaluation order:
1. governance `rulesEngineEnabled`; if false -> no rule effects
2. only active rules
3. ascending `sortOrder`, then stable id
4. match source
5. match category
6. match exact type
7. match effective priority
8. if `roleDepartmentRoutingEnabled`, match recipient role/department
9. merge effects deterministically

Merge behavior:
- `critical`: true if any matched rule sets true
- `requiresAcknowledgement`: true if any matched rule sets true
- `escalateAfterMinutes`: minimum non-null matched value
- `priorityOverride`: highest severity matched value (`URGENT > IMPORTANT > NORMAL`)
- return bounded `matchedRuleIds` max 20

The evaluator must not mutate DB rows.

Admin rule create/update/enable/disable must write an entry through the existing governance audit service with actions such as:
- `TNC_RULE_CREATED`
- `TNC_RULE_UPDATED`
- `TNC_RULE_ENABLED`
- `TNC_RULE_DISABLED`

Do not store secrets in audit metadata.

## 7.2 `tncAcknowledgement.service.js`

Must export focused functions equivalent to:

- `getAcknowledgement(prisma, { recipientId, source, nativeId })`
- `acknowledgeNotification(prisma, { recipientId, actorId, source, nativeId, ruleId, metadata })`
- `decorateAcknowledgements(prisma, recipientId, items)`

Acknowledgement rules:
- authenticate
- canonical notification ownership must be checked BEFORE acknowledgement
- only allow acknowledgement if backend rule evaluation says `requiresAcknowledgement=true`
- acknowledgement is idempotent due to unique recipient/source/nativeId
- repeated request returns existing acknowledgement, no duplicate row
- acknowledgement does NOT mark notification read automatically unless existing UX explicitly already does so; keep read state separate

---

# 8. BACKEND ROUTES — EXACT ROUTE FAMILY

Create:
`backend/src/routes/notificationRules.routes.js`

Mount in `backend/src/app.js` exactly once:

`app.use(`${API}/notification-center`, notificationRulesRoutes);`

Mount before generic API 404 fallback.

Use existing `auth` middleware.
Use the same admin role guard pattern already used by `notificationAdmin.routes.js`.

Required endpoints:

### User endpoint

`POST /api/notification-center/:source/:notificationId/acknowledge`

Behavior:
1. source must be GENERAL or TCS
2. resolve canonical notification with recipient ownership
3. normalize item using existing TNC normalization
4. load governance
5. evaluate rules against current recipient role/department
6. reject if acknowledgement governance disabled
7. reject if item does not require acknowledgement
8. create/get idempotent acknowledgement
9. return normalized acknowledgement + refreshed rule state

### Admin endpoints

- `GET /api/notification-center/admin/rules`
- `POST /api/notification-center/admin/rules`
- `PATCH /api/notification-center/admin/rules/:ruleId`
- `POST /api/notification-center/admin/rules/:ruleId/enable`
- `POST /api/notification-center/admin/rules/:ruleId/disable`
- `POST /api/notification-center/admin/rules/simulate`

Simulation:
- admin only
- governance `ruleSimulationEnabled` required
- default range 7d
- allowed ranges 7d/30d/90d
- scan max 5000 canonical notifications total
- return counts only/bounded summary, not full sensitive notification bodies
- include matched count, by source, by category, by priority, estimated acknowledgement-required count
- no writes during simulation

---

# 9. FEED INTEGRATION — NO SECOND FEED

Modify the existing notification center feed path; do not create a second feed.

Use:
`backend/src/services/notificationCenter.service.js`

Required normalized item additions:

```json
{
  "rulePolicy": {
    "critical": false,
    "requiresAcknowledgement": false,
    "escalateAfterMinutes": null,
    "priorityOverride": null,
    "matchedRuleIds": []
  },
  "acknowledgement": null,
  "acknowledged": false
}
```

Requirements:
- evaluate rules server-side after canonical normalization/intelligence
- recipient role and department must be loaded in a bounded way
- avoid N+1 user queries: one recipient lookup per feed request, not one per notification
- load active rules once per request, not once per item
- load acknowledgements in one bounded query for returned item keys
- if `priorityOverride` exists, expose the overridden effective priority in final item without mutating the source row
- existing presentation policy still applies
- existing unread/category counts must not regress

Add category/filter:
`CRITICAL`

`CRITICAL` returns items where:
- `rulePolicy.critical === true`
AND
- if acknowledgement is required, acknowledgement is still missing

Preserve:
ALL, UNREAD, ATTENTION, DIGEST, TCS, TASKS, TWS, SYSTEM, ACTIONS/current Phase 5 behavior.

---

# 10. PHASE 3 ESCALATION INTEGRATION

Modify existing Phase 3 automation only; do NOT create another scheduler.

File:
`backend/src/services/notificationAutomation.service.js`

Required behavior:
- existing lease/batching remains untouched
- when `rulesEngineEnabled=false`, Phase 6 rule work is skipped
- critical rule-matched items that require acknowledgement and remain unacknowledged become escalation candidates
- use matched rule `escalateAfterMinutes` when present; otherwise preserve existing escalation delay behavior
- acknowledged critical items must not continue escalating for acknowledgement reason
- do not duplicate escalation events for same level
- do not introduce another timer/setInterval/scheduler

Add tests proving scheduler lease/batching remains green.

---

# 11. ANALYTICS INTEGRATION

Extend existing:
`backend/src/services/notificationAnalytics.service.js`

Do NOT create another analytics service.

Add bounded Phase 6 metrics:
- `criticalAlerts`
- `acknowledgementRequired`
- `acknowledged`
- `unacknowledged`
- `acknowledgementRate`
- `averageAcknowledgementMinutes`
- `topMatchedRules` max 10

Honor existing analytics governance and range limits.
No unbounded table scans.

---

# 12. FRONTEND API METHODS

Modify existing:
`frontend/src/lib/api.js`

Add methods inside the existing notification/TNC API structure; do not create another API client.

Required operations:
- acknowledge notification
- admin list rules
- admin create rule
- admin update rule
- admin enable rule
- admin disable rule
- admin simulate rule

Use existing `request()` helper and existing CSRF/session behavior.

---

# 13. FRONTEND TNC UI — PRESERVE CURRENT PANEL

Modify:
`frontend/src/components/TncNotificationCenter.jsx`

The screenshot supplied by the user is the visual baseline.

Do NOT redesign the panel.
Do NOT create a new page.
Do NOT move TNC out of the topbar bell flow.

Add exactly:

## 13.1 Critical filter/tab

Label:
- English: `Critical`
- Arabic: `حرج`

Show count if available using existing tab/badge style.

## 13.2 Critical notification treatment

For items with `rulePolicy.critical=true`:
- show compact critical badge
- if `requiresAcknowledgement=true` and not acknowledged, show button:
  - EN: `Acknowledge`
  - AR: `تم الاطلاع`
- per-item loading state
- disable duplicate clicks while request is pending
- after success update/refresh using current TNC hook/state pattern
- do not automatically navigate away

Acknowledged item may show compact state:
- EN: `Acknowledged`
- AR: `تم التأكيد`

## 13.3 Admin Rules UI

Only render for admin-capable users using current admin/governance authorization data.
Place inside the existing TNC Settings/Admin area; do not create a standalone route.

Required V1 controls:
- rules list
- active toggle
- rule name
- source multi-select
- category multi-select
- priority multi-select
- role multi-select
- department multi-select
- critical toggle
- requires acknowledgement toggle
- escalation minutes numeric input
- priority override select
- Save
- Simulate

Simulation result UI displays bounded counts only.

Required UI support:
- Arabic + English
- RTL + LTR
- Light + Dark
- desktop + narrow responsive code

Browser QA must be reported as `BLOCKED_NO_BROWSER_ACCESS`.
Frontend build is mandatory.

---

# 14. DO NOT IMPLEMENT THESE IN V1

Explicitly forbidden:
- no notification cloning/fan-out to new recipients
- no email/SMS/WhatsApp/push-provider integration
- no arbitrary rule scripting
- no regex rules
- no SQL/query-language rules
- no new socket namespace
- no new scheduler
- no new notification source table
- no generic workflow engine
- no browser automation
- no archive report files

---

# 15. TESTS — RUN ONLY AT FINAL VALIDATION

Implement first. Then run one focused final validation pass.

Required tests/checks:

### Phase 5 integrity gate
1. governance Phase 5 flags normalize and update correctly
2. tncAction GENERAL resolves canonical Notification owned by recipient
3. tncAction TCS resolves canonical ChatNotification owned by recipient
4. foreign recipient rejected
5. unknown source rejected
6. action routes are mounted and do not fall into API HTML/404 fallback

### Phase 6 rules
7. condition normalization rejects unknown fields/values
8. actions normalization clamps/rejects invalid values
9. deterministic rule ordering/merge
10. role matching
11. department matching
12. governance rulesEngineEnabled=false skips rule effects
13. roleDepartmentRoutingEnabled=false skips audience restriction as defined by service contract
14. simulation is read-only and bounded
15. non-admin rule CRUD/simulation rejected

### Acknowledgement
16. only recipient can acknowledge
17. non-critical/non-required item rejected
18. idempotent duplicate acknowledge returns one acknowledgement
19. acknowledgement decoration correct for GENERAL and TCS
20. acknowledged critical item no longer appears as unacknowledged CRITICAL

### Escalation
21. unacknowledged critical item can become escalation candidate
22. acknowledged item is suppressed from acknowledgement escalation
23. no duplicate escalation level regression
24. Phase 3 scheduler lease/batching tests remain green

### Regression
25. Phase 4 governance/analytics tests
26. Phase 5 action tests
27. core notification-center tests
28. TCS unread/realtime relevant tests
29. Prisma validate
30. Prisma generate
31. migration status
32. backend syntax/import/startup check
33. frontend build
34. `git diff --check`
35. `git status`/changed-file scope

Do NOT run unrelated full-system suites unless one of the focused checks demonstrates a dependency failure.

---

# 16. LOCAL COMMIT

After all focused validation passes, create ONE local commit in `/var/www/TOS`.

Suggested exact commit message:

`feat(tnc): add critical notification rules and acknowledgement`

Do NOT push.

Record:
- START_SHA
- FINAL_LOCAL_SHA
- exact files changed
- migration name

Before commit verify no archive files are staged/tracked in outgoing changes.

---

# 17. DEPLOY

After successful local commit:
- deploy using the canonical TOS production deploy flow already present on the server
- do not invent a new deploy script

After deploy verify:
- `tamiyouz-system` ONLINE
- frontend process ONLINE if applicable
- backend localhost health responds
- public TOS HTTPS returns 200 and no 502/5xx
- Prisma migration applied
- no startup/import errors
- production still serves the same TNC topbar-bell panel

No browser QA claims.

---

# 18. FINAL REPORT — MARKDOWN ONLY

Create exactly:

`/var/www/TOS-Patchs/TNC/Phase6/TNC_PHASE6_CRITICAL_RULES_ROUTING_ACK_V1_REPORT.md`

Do NOT create ZIP.
Do NOT create any archive.
Do NOT put report in `/var/www/TOS`.
Do NOT push TOS-Patchs.

Report must include:
- `IMPLEMENTATION=PASS|FAIL|BLOCKED`
- `FINAL_VALIDATION=PASS|FAIL|BLOCKED`
- START_SHA
- FINAL_LOCAL_SHA
- commit message
- changed files/count
- Phase 5 integrity gate fixes/results
- Prisma models + migration status
- exact governance flags
- rule condition/action schema
- rule evaluation merge behavior
- role/department targeting behavior
- acknowledgement ownership/idempotency behavior
- CRITICAL feed behavior
- escalation integration
- analytics additions
- frontend UI additions
- exact test commands and pass/fail counts
- frontend build result
- backend/PM2/public health
- `BROWSER_QA=BLOCKED_NO_BROWSER_ACCESS`
- `PUSH_PERFORMED=NO`
- `DEPLOYMENT_PERFORMED=YES|NO`
- exact report path

Final OpenHands response must contain only a concise completion summary with:
- IMPLEMENTATION
- FINAL_VALIDATION
- FINAL_LOCAL_SHA
- changed file count
- migration status
- FRONTEND_BUILD
- DEPLOYMENT_PERFORMED
- PUSH_PERFORMED=NO
- BROWSER_QA=BLOCKED_NO_BROWSER_ACCESS
- exact report path

The user will perform the GitHub Push manually after review.