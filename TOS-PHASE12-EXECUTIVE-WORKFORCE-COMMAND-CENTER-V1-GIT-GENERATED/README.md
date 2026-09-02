# TOS Phase 12 — Executive Workforce Command Center V1

Baseline TOS commit:

`91f569c31087421b069d3ac4ab5ce87fb6b61a7f`

Phase 12 is the final functional phase of the TOS Performance & Workforce Management program.

It adds a read-only Executive Workforce Command Center inside the existing `/team-performance` page. It does **not** create a second reporting page and it does **not** add a new database model or migration.

## Executive objective

Give an Admin/Super Admin a fast answer to:

- Where does leadership attention need to go now?
- Which employees have performance or capacity risk?
- Which departments are behind targets?
- Where are critical skills gaps?
- Which critical succession roles are uncovered?
- Which coaching/review commitments are overdue?
- Which recognition decisions are waiting?

## Core guardrails

- Phase 3 Performance Score remains the only performance score.
- No Phase 12 employee score, department score, talent score, workforce score, or hidden risk score is created.
- Priority items are ordered only by transparent severity buckets: `critical`, `warning`, `info`.
- No automatic promotion, demotion, termination, compensation, reassignment, recognition approval, or succession selection.
- No new payroll or compensation logic.
- No new database table.
- No data is copied into a Phase 12 snapshot model.
- Existing Phase 3–11 domain methodologies remain authoritative.

## Files changed/generated

- `backend/src/routes/tasks.routes.js`
- `frontend/src/lib/api.js`
- `frontend/src/components/performance/ExecutiveCommandCenter.jsx` (new)
- `frontend/src/pages/TeamPerformanceDashboard.jsx`

No Prisma schema change and no migration are expected.

## Backend API

### GET

`/api/tasks/reports/team-performance/executive-command-center`

Query parameters:

- `start`
- `end`
- optional `employeeId`
- optional `department`
- `horizonDays` (1–90; UI uses 7 / 14 / 30)

Access:

- `SUPER_ADMIN`: allowed
- `ADMIN`: allowed
- `MANAGER`: blocked
- `PROJECT_MANAGER`: blocked
- `TEAM_MEMBER`: blocked

The Executive Command Center is intentionally company-executive/admin only because it combines talent, succession and recognition management signals.

## Source domains

Phase 12 aggregates existing source-of-truth logic from:

- Phase 3 — Performance Score, status, trend and task delivery
- Phase 5 — Performance Intelligence alerts
- Phase 6 — Goals & Targets
- Phase 7 — Reviews, follow-ups and coaching actions
- Phase 8 — Workforce capacity, utilization and operational risk
- Phase 9 — Skills, competencies, critical gaps and development plans
- Phase 10 — Talent, succession coverage and Ready Now bench
- Phase 11 — Recognition cycles and pending human decisions

## Primary executive KPIs

The UI intentionally keeps five headline KPIs:

1. Average Performance
2. Needs Attention
3. Critical Capacity
4. Critical Skill Gaps
5. Succession Gaps

Additional decision counters are shown as context, not as another score.

## Executive Brief

Rule-based brief lines summarize material signals such as:

- employees needing performance attention
- critical/high capacity risk
- critical skills gaps
- uncovered critical/high succession roles
- overdue review/coaching commitments
- pending recognition nominations

This is deterministic decision support, not an AI-generated employment recommendation.

## Executive Priority Queue

Priority queue sources include:

- Performance At Risk / Needs Attention / No Activity
- Critical / High workforce capacity risk
- Behind Target employees
- Critical competency gaps
- Overdue coaching/review actions
- Uncovered Critical/High succession roles
- Pending recognition decisions

Ordering is only:

1. Critical
2. Warning
3. Info

There is no hidden weighted formula and no executive risk score.

Each item keeps its original source phase and a review suggestion. A suggestion is not an automated action.

## Department Health Signals

Department rows combine counts for:

- average Phase 3 score
- employees needing attention
- behind-target employees
- critical/high capacity risk
- critical skill gaps
- succession gaps
- overdue coaching actions
- pending recognition decisions

`attentionSignals` is only a count used for display ordering. It is not a score, rating or employment decision metric.

## UI

Same route:

`/team-performance`

Phase 12 appears near the top of the dashboard, after the existing top-level performance KPIs and before the detailed Phase 6–11 sections.

Sections:

- Company Workforce Decision View
- five executive KPIs
- Executive Brief
- Executive Priority Queue
- Decision Domains
- Department Health Signals

Employee-linked priority cards can open the existing Employee Drawer. No duplicate employee detail UI is created.

## Performance / query design

- No Prisma query is executed inside Phase 12 employee/department/priority loops.
- Review records/actions are bulk-loaded once.
- Existing domain builders keep their established bulk-loading behavior.
- Phase 12 is read-only and creates no audit mutation events.

## Final program QA

Authenticated full E2E QA remains intentionally deferred while applying this patch.

After Phase 12 is pushed and reviewed, run one final end-to-end release gate across Phases 1–12 covering:

- RBAC and privacy
- Performance Score semantics
- Targets
- Reviews/coaching
- Workforce capacity
- Skills/development
- Talent/succession
- Recognition human approval
- Executive Command Center
- mobile / desktop / light / dark
- production build deployment
- service health
- final Git scope

During patch application report:

`FINAL_E2E_QA=DEFERRED_BY_PLAN`

## Patch application

Run:

```bash
bash TOS-PHASE12-EXECUTIVE-WORKFORCE-COMMAND-CENTER-V1-GIT-GENERATED/run_phase12_executive_workforce_command_center_v1.sh /var/www/TOS
```

Do not commit or push from OpenHands.
