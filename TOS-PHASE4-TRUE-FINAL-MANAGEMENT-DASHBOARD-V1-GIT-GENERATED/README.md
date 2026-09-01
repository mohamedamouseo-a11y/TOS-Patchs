# TOS Phase 4 True Final Management Dashboard V1

Baseline TOS commit:

`c19ac5e54384c2a00f0b81be6ab5de01154c1a96`

This patch corrects the actual Phase 4 implementation after GitHub review.

## Why this patch exists

The pushed Phase 4 code still had the old employee-centric dashboard and the newer team section on the same page. It also recalculated export scores with a separate ad-hoc formula, so exported scores could disagree with the Phase 3 dashboard. The Excel Score Breakdown lookup used `Object.values()` on a `Map`, leaving the sheet effectively empty.

## What it changes

### Frontend

`frontend/src/pages/TeamPerformanceDashboard.jsx`

- Replaces the mixed old/new page with one management dashboard.
- One date/filter bar: Today, Yesterday, Week, Month, Year, Custom + Employee + Department + search.
- Five management KPIs.
- Attention/status quick filters.
- Sortable team performance table.
- Mobile cards.
- Employee details drawer with score breakdown, previous-period context, one history chart, period tasks, and paginated activity timeline.
- Excel/PDF export menu and real download handling.
- Removes the old always-visible employee/project/time/status/priority/task dashboard sections.

`frontend/src/lib/api.js`

- Adds Team Performance, activities, history, and export API wrappers.
- Uses the existing authenticated/CSRF-aware request helpers.

### Backend

`backend/src/routes/tasks.routes.js`

- Replaces the Phase 4 Excel/PDF export implementation.
- Reuses the existing Phase 3 `calculatePeriodMetrics()` and `calculateTrend()` instead of recalculating a second score.
- Includes No Activity users with `performanceScore=null` and `rank=null`.
- Bulk-fetches tasks/activities/current/previous periods with no per-employee DB queries.
- Uses primary-assignee attribution and existing project RBAC.
- Produces Excel sheets: Team Performance, Task Details, Score Breakdown.
- Score Breakdown is sourced directly from Phase 3 breakdown values.
- PDF uses the same Phase 3 dataset.
- Audit writes are awaited and include report type, format, period, filters, filename, row count and timestamp.

## Apply

```bash
rm -rf /tmp/TOS-Patchs
git clone https://github.com/mohamedamouseo-a11y/TOS-Patchs.git /tmp/TOS-Patchs
bash /tmp/TOS-Patchs/TOS-PHASE4-TRUE-FINAL-MANAGEMENT-DASHBOARD-V1-GIT-GENERATED/run_phase4_true_final_management_dashboard_v1.sh /var/www/TOS
```

The runner verifies the exact baseline, refuses to overwrite dirty target files, runs backend syntax validation, frontend build, and `git diff --check`.

It does **not** commit or push.
