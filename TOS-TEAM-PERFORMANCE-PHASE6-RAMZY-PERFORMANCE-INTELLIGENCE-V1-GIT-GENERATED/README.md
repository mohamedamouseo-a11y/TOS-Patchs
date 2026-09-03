# TOS Team Performance — Phase 6 — Ramzy Performance Intelligence V1

Baseline: `7e8ec8c7856ce41724f493886ebe050381ecc4d8`

## Goal

Make Ramzy understand Team Performance using the same server-side Team Performance and Workforce read models already used by TOS.

Ramzy can answer, with live authorized data:

- Team Performance summary for a reporting period.
- Why an employee is `At Risk`, `Needs Attention`, `On Track`, or `Excellent`.
- Performance Score, Score Breakdown and Confidence.
- Completed / Total / Completion Rate / Overdue / Logged Hours.
- Performance Score methodology and normalization.
- Workforce / Capacity Risk and its live signals.

## Safety / Architecture

- No new Performance Score.
- No client-supplied performance dataset.
- No new API endpoint.
- No Prisma/schema/migration changes.
- Ramzy uses the authenticated user already attached to the agent run.
- The existing `buildTeamPerformanceExportDataset` enforces Team Performance scope before data reaches Ramzy.
- The existing `buildWorkforceForecast` enforces Workforce scope before data reaches Ramzy.
- Live Team Performance remains ACTIVE-only; DISABLED/PENDING are not added to live Ramzy results.
- Ambiguous employee names return numbered authorized candidates; Ramzy must ask for clarification.
- Employee-not-visible results must not be bypassed using another tool.
- The tool is read-only and creates no approval/action.

## Files changed in TOS

Expected exactly:

```text
 M backend/src/agency-operator/agents/ramzyAgencyOperator.js
 M backend/src/agency-operator/agents/specialistAgents.js
 M backend/src/agency-operator/prompts/ramzyPrompt.js
 M backend/src/agency-operator/tools/createRamzyTools.js
 M backend/src/routes/tasks.routes.js
?? backend/src/agency-operator/services/ramzyTeamPerformance.service.js
```

## Apply

```bash
cd /var/www/TOS-Patchs/TOS-TEAM-PERFORMANCE-PHASE6-RAMZY-PERFORMANCE-INTELLIGENCE-V1-GIT-GENERATED
bash run_phase6_ramzy_team_performance_v1.sh
```

The runner does not commit, push, reload PM2, or deploy. Reload and authenticated Ramzy verification must be done explicitly after the patch passes.
