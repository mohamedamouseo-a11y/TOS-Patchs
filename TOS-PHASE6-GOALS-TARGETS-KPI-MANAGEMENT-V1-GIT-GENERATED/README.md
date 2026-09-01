# TOS Phase 6 — Goals, Targets & KPI Management V1

Baseline TOS commit:

`9773ffa21fabe90c87823081984ebb6bb55999e1`

This patch adds historical employee/department performance targets on top of the existing Phase 3 score, Phase 4 management dashboard, and Phase 5 intelligence layer.

**Phase 3 Performance Score is not changed.** Target Achievement is a separate management measurement.

## Changed/generated TOS files

- `backend/prisma/schema.prisma`
- `backend/prisma/migrations/202609011600_phase6_performance_targets/migration.sql`
- `backend/src/routes/tasks.routes.js`
- `frontend/src/lib/api.js`
- `frontend/src/pages/TeamPerformanceDashboard.jsx`

## Data model

Adds `PerformanceTarget` with historical effective dates and these KPI targets:

- Target Score
- Target Completion %
- Target Completed Tasks
- Target Logged Hours
- Maximum Overdue Tasks
- Optional JSON custom targets
- Weekly / Monthly / Quarterly / Yearly / Custom period type
- Employee or Department scope
- Active/inactive history
- Created/updated actor IDs and timestamps

Employee targets take precedence over department targets.

## Backend APIs

Adds:

- `GET /api/tasks/reports/team-performance/targets/summary`
- `GET /api/tasks/reports/team-performance/targets`
- `POST /api/tasks/reports/team-performance/targets`
- `POST /api/tasks/reports/team-performance/targets/bulk`
- `PATCH /api/tasks/reports/team-performance/targets/:targetId`
- `DELETE /api/tasks/reports/team-performance/targets/:targetId`
- `POST /api/tasks/reports/team-performance/targets/:targetId/copy`

All target reads/writes use the existing Team Performance RBAC scope. Admins can manage authorized company targets. Managers/Project Managers are limited to employees/departments visible through their authorized project membership scope.

Every target mutation writes to the existing `workspaceAuditLog` architecture.

## Target achievement

Configured KPI components are averaged without changing Performance Score.

Status:

- `Exceeded`: >= 110%
- `On Target`: >= 90% and < 110%
- `Behind Target`: < 90%
- `No Data`: target exists but no meaningful period data
- `No Target`: no effective employee/department target

For Maximum Overdue, lower is better.

## Team Performance UI

Adds to the existing `/team-performance` page:

- Goals & Targets management section
- Employees On Target
- Employees Behind Target
- Employees Exceeding Target
- Average Target Achievement
- Departments On Target
- Target achievement column in Team table
- Goals & Targets section in Employee Drawer
- Admin/Manager target management modal
- Employee target creation
- Department target creation
- Bulk apply to currently filtered employees
- Copy an existing target to the selected period
- Deactivate targets while preserving history

## Phase 5 Intelligence integration

Adds target-aware intelligence using the same RBAC-scoped dataset:

- `TARGET_MISSED`
- `TARGET_AT_RISK`
- `TARGET_EXCEEDED`
- `DEPARTMENT_TARGET_MISSED`

These do not recalculate or replace the Phase 3 score.

## Migration

The runner executes the existing backend Prisma deployment workflow:

- Prisma validation
- Prisma deploy
- Prisma generate

The migration creates only the new `PerformanceTarget` table and indexes.

## Apply

```bash
rm -rf /tmp/TOS-Patchs
git clone https://github.com/mohamedamouseo-a11y/TOS-Patchs.git /tmp/TOS-Patchs
bash /tmp/TOS-Patchs/TOS-PHASE6-GOALS-TARGETS-KPI-MANAGEMENT-V1-GIT-GENERATED/run_phase6_goals_targets_kpi_management_v1.sh /var/www/TOS
```

Expected core output:

- `BASELINE_CHECK=PASS`
- `TARGETS_CLEAN=PASS`
- `PRISMA_TARGET_MODEL=PASS`
- `PRISMA_MIGRATION_CREATED=PASS`
- `BACKEND_TARGET_CRUD=PASS`
- `BACKEND_TARGET_SUMMARY=PASS`
- `INTELLIGENCE_TARGET_ALERTS=PASS`
- `FRONTEND_TARGET_API=PASS`
- `FRONTEND_TARGET_SUMMARY_UI=PASS`
- `FRONTEND_TARGET_MANAGER_UI=PASS`
- `FRONTEND_TARGET_DRAWER=PASS`
- `PRISMA_VALIDATE=PASS`
- `PRISMA_DEPLOY=PASS`
- `PRISMA_GENERATE=PASS`
- `BACKEND_SYNTAX=PASS`
- `PHASE3_SCORE_FORMULA_REGRESSION=PASS`
- `FRONTEND_BUILD=PASS`
- `GIT_DIFF_CHECK=PASS`
- `PHASE6_GOALS_TARGETS_KPI_MANAGEMENT_V1_APPLIED=YES`
- `NO_GIT_COMMIT_OR_PUSH_PERFORMED=YES`

## Required runtime QA

After applying, verify with authenticated sessions:

1. Admin can create employee and department targets.
2. Manager cannot create a target outside authorized project scope.
3. Employee target overrides department target.
4. Effective date overlap resolves the most recent active target.
5. Target Achievement changes while Phase 3 Performance Score stays identical.
6. No Activity remains `performanceScore=null` and target status becomes `No Data` when appropriate.
7. Bulk apply respects the filtered authorized employee list.
8. Copy preserves KPI values but uses the new selected period.
9. Deactivation preserves historical records.
10. Target mutation audit entries are present.
11. Intelligence shows target missed/at-risk/exceeded alerts.
12. Team table, mobile UI, drawer, light/dark modes remain clean.

## Git workflow

OpenHands must not commit or push TOS.

After server QA, use the TOS Developer Hub to Review + Push manually. Then review the new TOS commit on GitHub before closing Phase 6.
