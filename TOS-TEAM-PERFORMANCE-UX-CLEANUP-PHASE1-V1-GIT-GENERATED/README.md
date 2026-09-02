# TOS — Team Performance UX Cleanup — Phase 1 V1

## Purpose

Make `/team-performance` much shorter and easier to scan without deleting any Phase 3–12 capability.

This is the first phase of the new Team Performance UX roadmap.

## Baseline

Expected TOS HEAD:

`8b29fd2ec2c96ce422b927711310b35fe6c52c61`

The runner accepts either:

1. a clean working tree, or
2. the exact approved, uncommitted Premium Dark Mode state:
   - `M frontend/src/pages/TeamPerformanceDashboard.jsx`
   - `?? frontend/src/components/performance/teamPerformancePremiumDark.css`

No other dirty state is accepted.

## What Phase 1 changes

### Always visible

- Existing page header and current date/filter controls.
- Exactly the existing five top management KPI cards.
- Phase 12 Executive Workforce Command Center.
- Team Performance employee table/mobile list.
- Existing employee drawer and all drill-down details.

### Page-length reduction

The following are kept in the page but collapsed until requested:

1. Goals & Targets.
2. Performance Intelligence.
3. Deep Dive group containing:
   - Performance Reviews.
   - Workforce Planning.
   - Skills & Development.
   - Talent & Succession.
   - Recognition & Rewards.

### Employee table

- Shows the first 8 filtered employees initially.
- `Show all N employees` reveals the complete list.
- `Show fewer employees` returns to the focused 8-row view.
- Search, filters, sorting, ranking, status and employee drawer behavior are preserved.

## Files created/changed by Phase 1

Required Phase 1 paths:

- `frontend/src/pages/TeamPerformanceDashboard.jsx`
- `frontend/src/components/performance/PerformanceDisclosure.jsx`

If Premium Dark Mode is already applied locally, its existing stylesheet remains present and untouched:

- `frontend/src/components/performance/teamPerformancePremiumDark.css`

## Explicitly NOT part of Phase 1

- No professional period comparison yet — Phase 2.
- No Help Center yet — later phase.
- No Ramzy integration yet — later phases.
- No backend/API/RBAC/database/schema/migration changes.
- No changes to Phase 3 performance score semantics.
- No removal of any Phase 3–12 feature.

## Apply

```bash
cd /var/www/TOS-Patchs/TOS-TEAM-PERFORMANCE-UX-CLEANUP-PHASE1-V1-GIT-GENERATED
bash run_team_performance_phase1_v1.sh
```

The runner builds the frontend but does not deploy, commit, or push.

## Expected success markers

- `TEAM_PERFORMANCE_UX_CLEANUP_PHASE1_V1_APPLIED=YES`
- `CORE_KPIS_VISIBLE=5`
- `EXECUTIVE_COMMAND_CENTER_ALWAYS_VISIBLE=YES`
- `COLLAPSIBLE_SECTIONS=3`
- `TEAM_TABLE_INITIAL_ROWS=8`
- `SHOW_ALL_EMPLOYEES_AVAILABLE=YES`
- `EMPLOYEE_DRAWER_PRESERVED=YES`
- `DETAILS_REMOVED=NO`
- `FRONTEND_BUILD=PASS`
- `NO_GIT_COMMIT_OR_PUSH_PERFORMED=YES`

## Deployment reminder

TOS production nginx serves the frontend from:

`/opt/apps/tamiyouz-front/build`

After a successful build, deploy `frontend/dist/` to that directory and reload only `tamiyouz-frontend`.

Do not commit or push from OpenHands. Final TOS push remains a manual Developer Hub action.
