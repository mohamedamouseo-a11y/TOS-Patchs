# TOS Team Performance — Phase 4 Drill-down & Navigation V1

## Goal

Add an on-demand navigation path inside the existing Team Performance page:

**Company → Department → Employee → Task**

The feature is intentionally compact and collapsed by default so the daily management view does not become long again.

## Behavior

- Uses the existing filtered Team Performance employee scope.
- ACTIVE employees only; Phase 2 archived-member rules remain unchanged.
- Company level groups the current scope by department.
- Department level lists employees.
- Employee level loads tasks for the selected reporting period using the same existing `api.tasks.userDashboard` source already used by the Employee Drawer.
- Task action reuses the existing `onOpenTask` navigation passed by `App.jsx`.
- Employee action reuses the existing Employee Drawer.
- Search is available at Department, Employee, and Task levels.
- Pagination limits:
  - Departments: 6/page
  - Employees: 8/page
  - Tasks: 6/page

## Safety

- Frontend only.
- No backend endpoint.
- No schema or migration.
- No score/formula change.
- No RBAC widening.
- No duplicate task screen.
- No duplicate employee detail screen.
- Existing Phase 1, Phase 2, Phase 3, Executive Command Center, Archived Members and premium dark/light behavior remain intact.

## Expected TOS file scope after apply

```text
 M frontend/src/pages/TeamPerformanceDashboard.jsx
?? frontend/src/components/performance/PerformanceDrilldownNavigator.jsx
```

## Apply

```bash
bash run_phase4_drilldown_navigation_v1.sh
```

The runner validates the exact baseline, requires a clean working tree, builds the frontend, and validates the exact file scope. It does not commit or push TOS.
