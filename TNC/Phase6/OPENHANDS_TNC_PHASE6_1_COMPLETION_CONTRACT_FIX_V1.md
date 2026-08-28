# TNC Phase 6.1 — Completion + Contract Fix V1

## Execution contract — follow literally

Implementation repository: `/var/www/TOS`
Branch: `main`
Previous local Phase 6 commit reported by OpenHands: `ab2e7dc`
Prompt repository: `mohamedamouseo-a11y/TOS-Patchs`

DO NOT PUSH.
DO NOT REBASE/RESET/REWRITE HISTORY.
DO NOT CREATE ARCHIVES.
DO NOT REDESIGN TNC.
DO NOT CREATE A SECOND FEED, SCHEDULER, ANALYTICS SYSTEM, OR NOTIFICATION SOURCE.
You ARE responsible for deploy after successful validation.
Browser QA is unavailable; report `BROWSER_QA=BLOCKED_NO_BROWSER_ACCESS`.

This task is a strict completion/verification pass over Phase 6. Do not redo working code. Fix only missing or contract-incompatible items.

---

# 1. Verify Phase 6 local prerequisite

Before editing, verify local `main` contains commit `ab2e7dc` or an equivalent/newer Phase 6 commit with the reported implementation.
If not present, STOP and report BLOCKED.

Record START_SHA.

---

# 2. Route contract — fix exactly

The original Phase 6 contract requires the user acknowledgement endpoint:

`POST /api/notification-center/:source/:notificationId/acknowledge`

Required behavior:
- source allowlist: `GENERAL|TCS`
- authenticated user only
- resolve canonical `Notification` or `ChatNotification` by `nativeId + recipientId`
- evaluate current Phase 6 rule policy server-side
- reject if `criticalAcknowledgementEnabled=false`
- reject if `requiresAcknowledgement=false`
- idempotent acknowledgement
- return normalized acknowledgement + refreshed rule state

Admin rule endpoints must exist under:
- `GET /api/notification-center/admin/rules`
- `POST /api/notification-center/admin/rules`
- `PATCH /api/notification-center/admin/rules/:ruleId`
- `POST /api/notification-center/admin/rules/:ruleId/enable`
- `POST /api/notification-center/admin/rules/:ruleId/disable`
- `POST /api/notification-center/admin/rules/simulate`

Do NOT use a conflicting parallel `/acknowledgements/*` API as the primary public contract.
If `notificationAcknowledgement.routes.js` exists, either make it internal/unused or remove duplicate routing and keep ONE canonical route family.
Mount routes once before generic API 404 fallback.

---

# 3. Feed integration — mandatory

Modify/reuse `backend/src/services/notificationCenter.service.js`.
Do not create a second feed.

Every normalized returned TNC item must expose:

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

Exact requirements:
- load recipient role/department once per feed request
- load active rules once per request
- evaluate rules server-side
- load acknowledgements in one bounded query for returned item keys
- no N+1 recipient lookup
- no N+1 rule lookup
- if `priorityOverride` exists, expose effective overridden priority without mutating source rows
- preserve existing presentation policy
- preserve unread/category counts

Add/verify `CRITICAL` filter in the SAME TNC feed.
`CRITICAL` means:
- `rulePolicy.critical === true`
- and when acknowledgement is required, acknowledgement is still missing

Preserve ALL/UNREAD/ATTENTION/DIGEST/TCS/TASKS/TWS/SYSTEM/ACTIONS.

---

# 4. Phase 3 escalation integration — mandatory

Modify only existing `backend/src/services/notificationAutomation.service.js`.
Do NOT create another scheduler/timer.

Required:
- preserve existing lease/batching behavior
- if `rulesEngineEnabled=false`, skip Phase 6 rule work
- unacknowledged critical items requiring acknowledgement are escalation candidates
- use rule `escalateAfterMinutes` when present
- acknowledged items stop acknowledgement-based escalation
- no duplicate escalation for same level

Do not change unrelated automation semantics.

---

# 5. Analytics integration — mandatory

Extend existing `backend/src/services/notificationAnalytics.service.js` only.
Do NOT create another analytics service.

Add bounded metrics:
- `criticalAlerts`
- `acknowledgementRequired`
- `acknowledged`
- `unacknowledged`
- `acknowledgementRate`
- `averageAcknowledgementMinutes`
- `topMatchedRules` max 10

Respect existing analytics governance and 7d/30d/90d/current allowed range behavior.
No unbounded scans.

---

# 6. Rule audit — mandatory

Rule create/update/enable/disable must use the EXISTING governance audit service/table.
Required audit action keys:
- `TNC_RULE_CREATED`
- `TNC_RULE_UPDATED`
- `TNC_RULE_ENABLED`
- `TNC_RULE_DISABLED`

Do not create another governance audit model.
Do not store secrets.

---

# 7. Rule simulation — exact constraints

Admin only.
Governance `ruleSimulationEnabled` required.
Allowed range: 7d / 30d / 90d.
Default: 7d.
Maximum canonical notifications scanned: 5000 total.
Simulation must be read-only.
Return bounded counts only:
- matched count
- by source
- by category
- by priority
- estimated acknowledgement-required count

Do not return full sensitive notification bodies.

---

# 8. Frontend contract — same existing TNC panel

Modify only existing TNC UI/API files as required.
Do not create a standalone page.

Verify the existing TNC panel contains:
- `Critical` / `حرج` tab/filter
- critical badge on critical items
- `Acknowledge` / `تم الاطلاع` button for required unacknowledged items
- per-item loading state
- duplicate-click prevention
- acknowledged state text
- admin Rules Manager inside existing TNC settings/admin area
- rule list
- active toggle
- name
- source/category/priority/role/department controls
- critical toggle
- requires acknowledgement toggle
- escalation minutes
- priority override
- Save
- Simulate
- bounded simulation result counts
- Arabic/English
- RTL/LTR
- Light/Dark
- narrow responsive code

Frontend must call the canonical acknowledgement endpoint from Section 2.

---

# 9. Focused final validation — run once at end

Run and record PASS/FAIL for all of these:

1. Phase 5 governance flags normalize/update
2. Phase 6 governance flags normalize/update
3. GENERAL action resolves canonical recipient-owned Notification
4. TCS action resolves canonical recipient-owned ChatNotification
5. foreign recipient rejected
6. unknown source rejected
7. action route mount works before API fallback
8. rule unknown condition fields rejected
9. invalid rule actions rejected/clamped
10. deterministic rule ordering/merge
11. role match
12. department match
13. `rulesEngineEnabled=false` skips effects
14. `roleDepartmentRoutingEnabled=false` behavior
15. simulation read-only + bounded
16. non-admin rule endpoints rejected
17. recipient-only acknowledgement
18. non-required item acknowledgement rejected
19. duplicate acknowledgement idempotent one row
20. acknowledgement decoration GENERAL + TCS
21. acknowledged critical removed from unacknowledged CRITICAL result
22. unacknowledged critical becomes escalation candidate
23. acknowledged item suppressed from acknowledgement escalation
24. no duplicate escalation level
25. Phase 3 scheduler lease/batching regressions
26. Phase 4 governance/analytics regressions
27. Phase 5 action tests
28. core notification-center tests
29. TCS unread/realtime relevant tests
30. Prisma validate
31. Prisma generate
32. migration status
33. backend syntax/import/startup
34. frontend build
35. `git diff --check`
36. `git status` + changed-file scope

Do not claim PASS without actual command evidence.
Do not run unrelated full-system suites unless required by a focused failure.

---

# 10. Commit + deploy

If fixes were required and all validation passes:
- create ONE local commit
- suggested message: `fix(tnc): complete phase 6 rule and acknowledgement integration`

If absolutely no code changes are required, do not create an unnecessary commit.

DO NOT PUSH.

Deploy using canonical TOS production flow.
Verify:
- `tamiyouz-system` ONLINE
- frontend process ONLINE if applicable
- backend localhost health responds
- public TOS HTTPS 200 and no 502/5xx
- migration status clean/applied
- no startup/import errors

---

# 11. Final report — exact path

Create/update exactly:

`/var/www/TOS-Patchs/TNC/Phase6/TNC_PHASE6_1_COMPLETION_CONTRACT_FIX_V1_REPORT.md`

Markdown only. No ZIP/archive.

Report must include:
- `IMPLEMENTATION=PASS|FAIL|BLOCKED`
- `FINAL_VALIDATION=PASS|FAIL|BLOCKED`
- START_SHA
- FINAL_LOCAL_SHA
- commit message if created
- exact changed files/count
- canonical acknowledgement route verification
- admin rule routes verification
- feed rulePolicy/ack integration
- CRITICAL filter behavior
- escalation integration
- analytics metrics
- rule audit actions
- simulation constraints
- frontend features
- exact validation commands + pass/fail counts
- frontend build result
- migration status
- PM2/backend/public health
- `BROWSER_QA=BLOCKED_NO_BROWSER_ACCESS`
- `PUSH_PERFORMED=NO`
- `DEPLOYMENT_PERFORMED=YES|NO`
- exact report path

Final OpenHands response must be concise and include:
- IMPLEMENTATION
- FINAL_VALIDATION
- FINAL_LOCAL_SHA
- changed file count
- FRONTEND_BUILD
- migration status
- DEPLOYMENT_PERFORMED
- PUSH_PERFORMED=NO
- BROWSER_QA=BLOCKED_NO_BROWSER_ACCESS
- exact report path
