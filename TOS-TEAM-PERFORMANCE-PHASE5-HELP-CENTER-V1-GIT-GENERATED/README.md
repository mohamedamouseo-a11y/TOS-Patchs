# TOS Team Performance — Phase 5 Help Center V1

Baseline TOS HEAD:

`4fa7ad74489f1e09e16dd63292c240d8a7e6f726`

## Purpose

Add a real Help Center inside Team Performance without making the page longer and without changing any calculation, API, database rule, RBAC rule, or Ramzy behavior.

## UX

- New `Help Center` button in the Team Performance page header.
- Opens a modal/drawer over the current page; no persistent page-height increase.
- Searchable help topics.
- Each topic contains four required explanations:
  - What it means
  - How it is calculated
  - Source
  - How to use it
- Supports current EN/AR language choice.
- Escape key and backdrop close behavior.
- Responsive dark/light UI.

## Covered topics

- Team Performance scope and ACTIVE / DISABLED / PENDING behavior
- Reporting Period & Comparison
- Average Score
- Top Performer
- Completed Tasks
- Overdue Tasks
- Logged Hours
- Performance Score, component weights, normalization, confidence and status bands
- Management Summary
- Drill-down & Navigation
- Executive Command Center
- Goals & Targets
- Performance Intelligence
- Team Performance table
- Archived Members
- Deep Dive modules

## Score explanation matches current backend logic

- Completion: 35%
- On-time / Overdue: 25%
- Time Efficiency: 20%
- Workflow Quality: 10%
- Consistency: 10%
- Missing eligible components are skipped and available weights are normalized back to 100.
- Confidence: High = 4–5 covered components, Medium = 3, Low = 0–2.
- Status bands: Excellent >= 85, On Track >= 70, Needs Attention >= 50, otherwise At Risk. No meaningful activity returns No Activity with no score/rank.

## Safety

Phase 5 is explanation-only.

It must NOT:

- change backend code
- add API endpoints
- change score formulas
- change UserStatus behavior
- change RBAC
- change schema/migrations
- change packages/lockfiles
- change App routing
- integrate Ramzy yet (that starts in Phase 6)

## Expected TOS git status after apply

```text
 M frontend/src/pages/TeamPerformanceDashboard.jsx
?? frontend/src/components/performance/TeamPerformanceHelpCenter.jsx
```

Run:

```bash
bash run_phase5_help_center_v1.sh
```
