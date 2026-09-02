# TOS Team Performance — Phase 1 Executive Snapshot Refinement V1

This patch is a **UI-only refinement** layered on top of:

1. the approved Team Performance Premium Dark Mode local changes, and
2. Team Performance UX Cleanup Phase 1 local changes.

It does not change backend, Prisma, API contracts, RBAC, score logic, date logic, Help Center, or Ramzy.

## Goal

Make the always-visible Executive Workforce Command Center behave like a compact executive snapshot instead of a long embedded dashboard.

## Default snapshot

Always visible:

- Existing Executive Command Center header and 7/14/30 horizon controls.
- Existing five executive KPIs.
- Executive Brief limited to the first two lines.
- Executive Priority Queue limited to the top three priorities.
- `View executive details` toggle.

Hidden by default:

- Secondary Pending Recognition / Overdue Coaching mini metrics.
- Priority items 4–10.
- Decision Domains.
- Department Health Signals.

When the user opens executive details, the existing detailed content reappears. No information is deleted.

## Expected TOS baseline

Git HEAD:

`8b29fd2ec2c96ce422b927711310b35fe6c52c61`

Expected pre-existing local files before applying:

- `frontend/src/pages/TeamPerformanceDashboard.jsx`
- `frontend/src/components/performance/PerformanceDisclosure.jsx`
- `frontend/src/components/performance/teamPerformancePremiumDark.css`

The patch adds one additional modified tracked file:

- `frontend/src/components/performance/ExecutiveCommandCenter.jsx`

## Apply

```bash
cd /var/www/TOS-Patchs/TOS-TEAM-PERFORMANCE-PHASE1-EXECUTIVE-SNAPSHOT-REFINEMENT-V1-GIT-GENERATED
bash run_phase1_executive_snapshot_refinement_v1.sh
```

The runner validates baseline and file scope, applies the generator, runs `git diff --check`, and builds the frontend. It does not deploy, commit, or push.

## Expected final working tree

```text
 M frontend/src/components/performance/ExecutiveCommandCenter.jsx
 M frontend/src/pages/TeamPerformanceDashboard.jsx
?? frontend/src/components/performance/PerformanceDisclosure.jsx
?? frontend/src/components/performance/teamPerformancePremiumDark.css
```

## Explicit exclusions

- No Phase 2 date comparison.
- No Help Center.
- No Ramzy work.
- No backend/database/schema changes.
- No package changes.
- No feature deletion.
