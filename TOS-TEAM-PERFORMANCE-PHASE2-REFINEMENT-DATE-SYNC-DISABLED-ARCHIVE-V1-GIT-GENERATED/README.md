# TOS Team Performance — Phase 2 Refinement V1

## Purpose

This patch refines the already-applied Team Performance Phase 2 and adds the disabled-member archive behavior requested for live reporting.

## Scope

### Date / Compare refinement

- Preset periods now populate the visible **From** and **To** date inputs.
- Editing either date switches the reporting period to **Custom** while preserving the other boundary.
- Current-period and comparison-period labels always reflect the actual calculated ranges.
- The selected preset has a stronger visual active state.
- Existing comparison modes remain: Previous period, Previous month, Previous year, Custom comparison, Off.

### Disabled members

`UserStatus.DISABLED` employees are historical only.

They are excluded from:

- live Team Performance employee list
- ranking
- the 5 live KPIs
- comparison cohort
- Performance Intelligence
- Targets live summary/config scope
- Reviews live scope
- Workforce Planning live scope
- Skills live scope
- Talent/Succession live scope
- Recognition live management scope
- Executive Command Center aggregation
- standard Team Performance exports

Their records are **not deleted**. The main Team Performance endpoint calculates their historical metrics for the selected period and returns them as `archivedByUser`.

The frontend shows a separate **Archived Members** disclosure, collapsed by default, with historical score/tasks/hours/overdue/disabled date. Archived rows have no live rank and do not affect any live management metric.

`PENDING` users also do not participate in live performance reporting; they are not treated as archived employees.

## Data safety

- No schema change.
- No migration.
- No user deletion.
- No performance history deletion.
- No score-formula change.
- No RBAC widening.

## Expected TOS file scope after apply

```text
 M backend/src/routes/tasks.routes.js
 M frontend/src/components/layout/Topbar.jsx
 M frontend/src/components/performance/ExecutiveCommandCenter.jsx
 M frontend/src/pages/TeamPerformanceDashboard.jsx
?? frontend/src/components/layout/premiumHeaderDark.css
?? frontend/src/components/performance/ArchivedPerformanceMembers.jsx
?? frontend/src/components/performance/PerformanceDisclosure.jsx
?? frontend/src/components/performance/PerformancePeriodControl.jsx
?? frontend/src/components/performance/teamPerformancePremiumDark.css
```

## Apply

```bash
bash run_phase2_refinement_v1.sh
```

The runner builds the frontend and validates the exact working-tree scope. It does **not** commit or push TOS.
