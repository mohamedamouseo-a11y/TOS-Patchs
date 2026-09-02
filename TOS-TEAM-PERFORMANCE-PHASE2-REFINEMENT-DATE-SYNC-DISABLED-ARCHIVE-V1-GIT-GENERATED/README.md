# TOS Team Performance — Phase 2 Refinement V1

## Baseline

Expected TOS HEAD:

`495201cfa490f643d9e28252eb523a4e278f385c`

This commit already contains the approved Premium Header, Team Performance Phase 1, Executive Snapshot refinement, Premium Dark Mode, and Phase 2 Professional Date & Comparison work.

The runner also contains a guarded cleanup for the exact residue left by the failed `Phase 01 Dashboard V2` attempt:

- modified `frontend/src/main.jsx` containing only the import of `./styles/dashboard-github-reference.css`
- untracked `frontend/src/styles/dashboard-github-reference.css`

If anything differs from that exact residue, the runner stops instead of deleting or resetting unrelated work.

## Purpose

This patch refines the already-applied Team Performance Phase 2 and adds the disabled-member archive behavior requested for live reporting.

## Scope

### Date / Compare refinement

- Preset periods populate the visible **From** and **To** inputs.
- Editing either date switches to **Custom** while preserving the other boundary.
- Current-period and comparison-period labels reflect the actual ranges.
- Only the selected preset has the premium active state.
- Existing comparison modes remain: Previous period, Previous month, Previous year, Custom comparison, Off.

### Disabled members

`UserStatus.DISABLED` employees are historical only.

They are excluded from live Team Performance, ranking, the five KPIs, comparison, Intelligence, Targets live scope, Reviews live scope, Workforce, Skills, Talent/Succession, Recognition live management, Executive Command Center aggregation, and standard live exports.

Historical records are not deleted. The main Team Performance endpoint returns accessible disabled historical rows separately as `archivedByUser`.

The frontend shows **Archived Members**, collapsed by default. Archived rows have no live rank and do not affect live management metrics.

`PENDING` users are excluded from both live and archived performance cohorts.

## Data safety

- No schema change.
- No migration.
- No user deletion.
- No performance-history deletion.
- No score-formula change.
- No RBAC widening.

## Expected TOS file scope after apply

```text
 M backend/src/routes/tasks.routes.js
 M frontend/src/components/performance/PerformancePeriodControl.jsx
 M frontend/src/pages/TeamPerformanceDashboard.jsx
?? frontend/src/components/performance/ArchivedPerformanceMembers.jsx
```

## Apply

```bash
bash run_phase2_refinement_v1.sh
```

The runner performs the guarded failed-patch cleanup when applicable, builds the frontend, and validates the exact working-tree scope. It does **not** commit or push TOS.
