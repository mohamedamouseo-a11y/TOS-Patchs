# TOS Phase 5 — Performance Intelligence & Alerts V1

Baseline TOS commit:

`d17484fa0b54b127ff7fab00d933973f63b233df`

This patch adds deterministic management intelligence on top of the Phase 3 scoring and Phase 4 management dashboard.

It **does not create a second performance formula**. All intelligence is derived from the existing `buildTeamPerformanceExportDataset()` dataset, which itself uses the Phase 3 `calculatePeriodMetrics()` and `calculateTrend()` logic.

## Changed files

- `backend/src/routes/tasks.routes.js`
- `frontend/src/lib/api.js`
- `frontend/src/pages/TeamPerformanceDashboard.jsx`

## Backend

Adds:

`GET /api/tasks/reports/team-performance/intelligence`

The endpoint reuses the existing RBAC-scoped Phase 4 dataset and returns:

- Top Improver
- Biggest Drop
- At Risk employees
- Needs Attention employees
- No Activity alerts
- Overdue concentration alerts
- Workload imbalance detection
- Department performance comparison
- Management brief
- Critical / warning alert counts

All calculations happen in memory after the existing bulk dataset is built. No Prisma query is added inside employee/department loops.

### Alert rules

- `AT_RISK`: score < 50
- `NEEDS_ATTENTION`: score 50–69
- `SCORE_DROP`: decline >= 10 points; critical at >= 20 points
- `OVERDUE_CONCENTRATION`: 3+ overdue tasks; critical at 5+
- `NO_ACTIVITY`: no meaningful Phase 3 data; warning if previously active
- `TOP_IMPROVER`: positive trend >= 5 points
- `DEPARTMENT_PERFORMANCE`: department average < 70
- `DEPARTMENT_OVERDUE`: department overdue >= 5
- `WORKLOAD_IMBALANCE`: highest active workload >= 1.75x team average; critical at >= 2.25x

Workload uses logged hours when hours data exists; otherwise it falls back to task count.

## Frontend

Adds a new **Performance Intelligence** section to the existing `/team-performance` page without creating another route.

The section includes:

- Top Improver card
- Biggest Drop card
- Attention summary
- Workload Balance card
- Live Management Alerts
- Management Brief
- Department Performance comparison

Employee-specific alerts are clickable and open the existing Phase 4 Employee Drawer.

The intelligence request follows the selected date range and current employee/department management scope.

## Apply

```bash
rm -rf /tmp/TOS-Patchs
git clone https://github.com/mohamedamouseo-a11y/TOS-Patchs.git /tmp/TOS-Patchs
bash /tmp/TOS-Patchs/TOS-PHASE5-PERFORMANCE-INTELLIGENCE-ALERTS-V1-GIT-GENERATED/run_phase5_performance_intelligence_alerts_v1.sh /var/www/TOS
```

The generator:

1. Requires the exact baseline HEAD.
2. Refuses to overwrite dirty target files.
3. Inserts the backend intelligence endpoint.
4. Adds the frontend API wrapper.
5. Adds the Intelligence UI to the existing Team Performance dashboard.
6. Runs `node --check` on the backend route.
7. Runs the frontend production build.
8. Runs `git diff --check`.
9. Does **not** commit or push.

## Runtime verification after applying

Use an authenticated session and verify:

- Main Team Performance API = HTTP 200
- Intelligence API = HTTP 200
- Intelligence uses the same authorized users/projects as the dashboard
- Top Improver and Biggest Drop match real trend data
- No Activity users keep `performanceScore=null`
- Cross-project data is not leaked for Manager / Project Manager
- No new Prisma queries are inside per-employee loops
- `/team-performance` = HTTP 200
- Light/dark/mobile rendering is clean

## Git workflow

Do not commit or push from OpenHands.

After server verification, use the TOS Developer Hub to review and push the final source changes.
