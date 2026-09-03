# TOS Team Performance — Phase 3 Management Summary V1

## Purpose

Add a compact management-first summary to `/team-performance` so a manager can answer quickly:

- Who is doing well?
- Who needs intervention?
- Who is carrying overdue pressure?
- What are the most important management signals right now?

## Placement

The summary appears after the existing five KPI cards and before the existing Executive Command Center.

It does **not** replace or duplicate the Executive Command Center. The Phase 3 summary is employee/action focused; the Executive Command Center remains the broader cross-domain executive view.

## Data source

No new API and no new database model are introduced.

The component uses the existing filtered live Team Performance rows plus the existing Target summary. Therefore it automatically respects:

- selected reporting period
- employee filter
- department filter
- status filter
- search filter
- Phase 2 ACTIVE-only rule

DISABLED and PENDING users do not enter the live management summary.

## Sections

1. **Doing well** — up to the top 3 Excellent / On Track employees.
2. **Needs attention** — up to 3 At Risk / Needs Attention employees, critical first.
3. **Overdue pressure** — up to 3 employees with the most overdue work.
4. **Focus now** — up to 3 deterministic management signals from at-risk, overdue, attention, target-behind and no-activity counts.

Employee rows are clickable and open the existing Employee Drawer.

## Guardrails

- No new performance score.
- No hidden composite score.
- No automated HR decision.
- No backend change.
- No schema or migration.
- No package change.
- Existing Phase 1, Phase 2, Executive Snapshot, Premium Dark and Header behavior remain unchanged.

## Expected TOS file scope

```text
 M frontend/src/pages/TeamPerformanceDashboard.jsx
?? frontend/src/components/performance/ManagementSummary.jsx
```

## Apply

```bash
bash run_phase3_management_summary_v1.sh
```

The runner validates the exact baseline, requires a clean working tree, builds the frontend and validates the exact file scope. It does not commit or push TOS.
