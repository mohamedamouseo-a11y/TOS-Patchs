# TOS Phase 8 — Predictive Performance & Workforce Planning V1

Baseline TOS commit:

`125b92e5779294cb23d057d5017e8b1b288d8c7b`

Phase 8 adds a transparent forward-looking workforce planning layer inside the existing `/team-performance` experience.

It does **not** create a new Performance Score and does **not** use a black-box ML prediction.

It preserves:

- Phase 3 Performance Score and primary-assignee semantics
- Phase 4 management dashboard and exports
- Phase 5 Performance Intelligence
- Phase 6 Goals & Targets / Target Achievement
- Phase 7 Reviews, Coaching & Action Plans

## TOS files changed/generated

- `backend/prisma/schema.prisma`
- `backend/prisma/migrations/202609020120_phase8_workforce_capacity_plans/migration.sql`
- `backend/src/routes/tasks.routes.js`
- `frontend/src/lib/api.js`
- `frontend/src/components/performance/WorkforcePlanning.jsx` (new)
- `frontend/src/pages/TeamPerformanceDashboard.jsx`

## Workforce capacity model

Adds `WorkforceCapacityPlan`:

- employeeId
- weeklyCapacityHours
- effectiveFrom
- effectiveTo optional
- note
- isActive
- createdById / updatedById
- createdAt / updatedAt

Active capacity plans for the same employee are not allowed to overlap. Overlap returns HTTP `409`.

Capacity resolution at forecast start is explicit:

1. Active `WorkforceCapacityPlan`
2. Existing `User.designWeeklyCapacityHours` when available
3. Visible default of `40h/week`

The fallback source is returned in every employee forecast row.

## Forecast methodology

This is a deterministic operational forecast.

### Horizon

API supports 1–90 days.

UI presets:

- Next 7 days
- Next 14 days
- Next 30 days

### Business days

Uses the TOS/SLA convention:

- Sunday through Thursday
- JavaScript day numbers `0..4`

### Demand

Forecast demand includes open primary-assignee tasks due on or before the end of the forecast horizon.

Already-overdue open work remains forecast demand because it still consumes future delivery capacity.

Open tasks without a due date are reported separately as `unscheduledOpenTasks` and are **not** assigned invented deadline demand.

### Remaining work

For tasks with estimates:

`remainingHours = max(estimatedHours - actualHours, 0)`

Tasks without an estimate remain visible as `unestimatedDueTasks`.

Phase 8 never invents hours for unestimated work.

### Utilization

`utilization = plannedRemainingHours / availableCapacityHours * 100`

### Capacity risk

- `< 85%` → HEALTHY
- `>= 85%` → WATCH
- `> 100%` → HIGH
- `>= 125%` → CRITICAL

Overdue concentration can raise risk even when estimated utilization is low.

If due work exists but none of it has estimates, capacity risk can be `UNKNOWN` rather than pretending the load is zero.

### Forecast confidence

Based on estimate coverage of due work:

- HIGH: all due tasks estimated
- MEDIUM: up to 25% unestimated
- LOW: more than 25% unestimated
- NO_DEMAND: no due tasks in the horizon

### Performance outlook

Outlook is a management signal, not a new score:

- AT_RISK
- WATCH
- POSITIVE
- STABLE
- INSUFFICIENT_DATA

It combines visible signals only:

- capacity risk
- recent Phase 3 performance score/trend
- recent Phase 6 target achievement
- overdue open Phase 7 coaching actions

A No Activity/null Performance Score remains null and is never silently converted to zero.

## Reallocation suggestions

Phase 8 can suggest possible capacity movement when:

- one employee has estimated demand over 100% capacity
- another employee has estimated load below 70%

Same-department spare capacity is preferred first.

Recommendations contain suggested hours only.

**No task is automatically reassigned.**

## Department planning

Returns department-level:

- total capacity hours
- planned estimated hours
- utilization
- capacity gap
- due tasks
- overdue tasks
- unestimated demand
- employees at high/critical risk

## Backend APIs

### Forecast

`GET /api/tasks/reports/team-performance/workforce/forecast`

Query options:

- `horizonDays`
- `employeeId`
- `department`

### Capacity plans

- `GET /api/tasks/reports/team-performance/workforce/capacity-plans`
- `POST /api/tasks/reports/team-performance/workforce/capacity-plans`
- `PATCH /api/tasks/reports/team-performance/workforce/capacity-plans/:planId`
- `DELETE /api/tasks/reports/team-performance/workforce/capacity-plans/:planId`

Delete is a soft deactivation (`isActive=false`).

## RBAC

Forecast visibility follows Team Performance project scope:

- Admin/System Admin: company-authorized users/projects
- Manager/Project Manager: employees reachable through projects the manager belongs to
- Team member: own visible planning scope only

Capacity writes:

- Admin/System Admin: authorized company employees
- Manager/Project Manager: only employees in their project scope
- Team members/clients: no capacity-plan mutation

Managers cannot create plans for out-of-scope employees.

## Audit

Awaited `WorkspaceAuditLog` events:

- `workforce_capacity_plan_created`
- `workforce_capacity_plan_updated`
- `workforce_capacity_plan_deactivated`

## UI

Inside the same `/team-performance` route, Phase 8 adds:

### Forward Outlook & Capacity

- 7 / 14 / 30 day horizon
- Available Capacity
- Planned Demand
- Capacity Gap
- At Risk employees
- Upcoming Deadlines
- Employee outlook table/cards
- Capacity risk
- Forecast confidence
- Recent score/trend context
- Target achievement context
- Reallocation Opportunities
- Department Capacity
- Upcoming Deadlines

### Capacity Management

Admin/authorized managers can:

- assign weekly employee capacity
- choose effective start/end
- add planning note
- view capacity history
- deactivate a capacity plan

### Employee Drawer

Adds a `Forward Outlook / Workforce Planning` section inside the existing employee drawer with:

- Outlook
- Capacity risk
- Load %
- Planned demand
- Available capacity
- Due / overdue work
- Visible risk signals

Existing Phase 6 Goals & Targets and Phase 7 Reviews & Action Plans remain intact.

## Apply

```bash
rm -rf /tmp/TOS-Patchs
git clone https://github.com/mohamedamouseo-a11y/TOS-Patchs.git /tmp/TOS-Patchs
bash /tmp/TOS-Patchs/TOS-PHASE8-PREDICTIVE-PERFORMANCE-WORKFORCE-PLANNING-V1-GIT-GENERATED/run_phase8_predictive_performance_workforce_planning_v1.sh /var/www/TOS
```

Expected core output:

- `BASELINE_CHECK=PASS`
- `TARGETS_CLEAN=PASS`
- `PHASE7_BASELINE_PRESENT=PASS`
- `PRISMA_WORKFORCE_CAPACITY_MODEL=PASS`
- `PRISMA_WORKFORCE_CAPACITY_MIGRATION=PASS`
- `BACKEND_WORKFORCE_FORECAST=PASS`
- `BACKEND_CAPACITY_CRUD=PASS`
- `WORKFORCE_RBAC_GUARDS=PASS`
- `WORKFORCE_TRANSPARENT_FORECAST=PASS`
- `WORKFORCE_ACCESS_HARDENING=PASS`
- `NO_ACTIVITY_OUTLOOK_HARDENING=PASS`
- `FRONTEND_WORKFORCE_API=PASS`
- `FRONTEND_WORKFORCE_COMPONENT=PASS`
- `FRONTEND_WORKFORCE_DASHBOARD=PASS`
- `FRONTEND_WORKFORCE_DRAWER=PASS`
- `PRISMA_VALIDATE=PASS`
- `PRISMA_DEPLOY=PASS`
- `PRISMA_GENERATE=PASS`
- `BACKEND_SYNTAX=PASS`
- `BACKEND_WORKFORCE_CONTRACT=PASS`
- `WORKFORCE_CAPACITY_OVERLAP_GUARD=PASS`
- `WORKFORCE_BULK_AGGREGATION=PASS`
- `FRONTEND_WORKFORCE_INTEGRATION=PASS`
- `PHASE3_SCORE_FORMULA_REGRESSION=PASS`
- `PHASE6_TARGET_REGRESSION=PASS`
- `PHASE7_REVIEW_REGRESSION=PASS`
- `FRONTEND_BUILD=PASS`
- `GIT_DIFF_CHECK=PASS`
- `EXPECTED_FILE_SCOPE=PASS`
- `PHASE8_PREDICTIVE_PERFORMANCE_WORKFORCE_PLANNING_V1_APPLIED=YES`
- `NO_GIT_COMMIT_OR_PUSH_PERFORMED=YES`

## Required runtime QA before TOS push

1. Admin forecast 7/14/30 days returns HTTP 200.
2. `methodology.type` equals `RULE_BASED_OPERATIONAL_FORECAST`.
3. Verify Sunday–Thursday business-day count for known horizon dates.
4. Verify a task with `estimatedHours=10`, `actualHours=4` contributes exactly `6h` remaining demand.
5. Verify unestimated task contributes zero invented hours and increments `unestimatedDueTasks`.
6. Verify unscheduled task increments `unscheduledOpenTasks` but is not silently placed in the horizon demand.
7. Verify already-overdue open task remains demand and increments `overdueOpenTasks`.
8. Verify primary assignee only — secondary TaskAssignee does not receive duplicate workload credit.
9. Verify capacity fallback hierarchy: explicit plan → design capacity → 40h fallback.
10. Create capacity plan for real employee → 201.
11. Exact/overlapping active capacity plan → 409.
12. Different non-overlapping period → allowed.
13. Invalid employee as Admin → 404.
14. Authorized Manager capacity write → allowed.
15. Real out-of-scope Manager capacity write → 403.
16. Team member capacity write → 403.
17. Deactivate plan → `isActive=false`, history retained.
18. Verify audit entries for create/update/deactivate.
19. Verify null/No Activity score stays null and does not become an automatic At Risk signal.
20. Verify HIGH/CRITICAL/WATCH thresholds against controlled test demand/capacity.
21. Verify forecast confidence HIGH/MEDIUM/LOW using controlled estimate coverage.
22. Verify reallocation suggestions prefer same department when spare capacity exists.
23. Verify recommendations do not mutate/reassign Task rows.
24. Verify department totals equal employee-row totals.
25. Verify recent Phase 3 score is not changed by forecast/capacity operations.
26. Verify Phase 5 Intelligence remains intact.
27. Verify Phase 6 Targets remain intact.
28. Verify Phase 7 Reviews/Actions remain intact.
29. Verify `/team-performance` contains one Forward Outlook section and one existing Team Performance dashboard only.
30. Verify employee drawer includes Forward Outlook plus Goals & Targets plus Reviews & Action Plans.
31. Verify desktop/mobile/light/dark rendering.
32. Verify forecast/list endpoints use bulk queries — no Prisma query inside employee/task/action loops.
33. Record 7/14/30-day response times and confirm no timeout.
34. Clean only proven Phase 8 QA capacity-plan records after testing.
35. Restart existing PM2 services only and verify `/team-performance` HTTP 200.
36. Final Git status must contain only Phase 8 expected files.

## Expected final Git status

```text
 M backend/prisma/schema.prisma
 M backend/src/routes/tasks.routes.js
 M frontend/src/lib/api.js
 M frontend/src/pages/TeamPerformanceDashboard.jsx
?? backend/prisma/migrations/202609020120_phase8_workforce_capacity_plans/
?? frontend/src/components/performance/WorkforcePlanning.jsx
```

OpenHands must not commit or push TOS.

Final TOS push remains manual through Developer Hub after QA passes.
