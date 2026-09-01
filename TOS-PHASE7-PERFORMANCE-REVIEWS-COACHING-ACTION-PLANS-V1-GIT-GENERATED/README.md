# TOS Phase 7 — Performance Reviews, Coaching & Action Plans V1

Baseline TOS commit:

`230559f2ba936466ea6b0246c2a7f2108138e9a5`

This patch turns the existing performance data into a management follow-through workflow inside the same `/team-performance` page.

It preserves:

- Phase 3 Performance Score and formulas
- Phase 4 management dashboard and exports
- Phase 5 Intelligence alerts
- Phase 6 Goals & Targets and Target Achievement
- Existing primary-assignee semantics and RBAC scope

## TOS files changed/generated

- `backend/prisma/schema.prisma`
- `backend/prisma/migrations/202609020030_phase7_performance_reviews/migration.sql`
- `backend/src/routes/tasks.routes.js`
- `frontend/src/lib/api.js`
- `frontend/src/components/performance/PerformanceReviews.jsx` (new)
- `frontend/src/pages/TeamPerformanceDashboard.jsx`

## Data model

### PerformanceReview

Stores historical coaching reviews with:

- employee and reviewer IDs
- review period
- status: `DRAFT`, `SHARED`, `IN_PROGRESS`, `COMPLETED`
- reason/trigger
- strengths
- improvement areas
- manager notes
- employee comment and acknowledgment timestamp
- follow-up date
- score/status snapshot
- target achievement snapshot
- completed/total tasks, overdue and hours snapshot
- audit-friendly creator/updater fields and timestamps

### PerformanceActionItem

Stores action plans linked to a review:

- title and description
- due date
- priority
- status: `OPEN`, `IN_PROGRESS`, `COMPLETED`, `CANCELLED`
- completion timestamp
- creator/updater fields

The database migration creates a foreign key from action items to reviews with cascade delete semantics.

## Review triggers

Supported reasons:

- `PERIODIC`
- `TARGET_MISSED`
- `TARGET_AT_RISK`
- `SCORE_DROP`
- `OVERDUE`
- `NO_ACTIVITY`
- `WORKLOAD_ISSUE`
- `MANAGER_INITIATED`

These reasons link the coaching workflow to Phase 5/6 findings without changing any score.

## Backend APIs

Adds:

- `GET /api/tasks/reports/team-performance/reviews/summary`
- `GET /api/tasks/reports/team-performance/reviews`
- `GET /api/tasks/reports/team-performance/reviews/:reviewId`
- `POST /api/tasks/reports/team-performance/reviews`
- `PATCH /api/tasks/reports/team-performance/reviews/:reviewId`
- `POST /api/tasks/reports/team-performance/reviews/:reviewId/share`
- `POST /api/tasks/reports/team-performance/reviews/:reviewId/acknowledge`
- `POST /api/tasks/reports/team-performance/reviews/:reviewId/complete`
- `POST /api/tasks/reports/team-performance/reviews/:reviewId/actions`
- `PATCH /api/tasks/reports/team-performance/reviews/:reviewId/actions/:actionId`
- `DELETE /api/tasks/reports/team-performance/reviews/:reviewId/actions/:actionId`

## RBAC

- System Admin/Admin: company-authorized review scope.
- Manager/Project Manager: only employees reachable through projects the manager belongs to, identical to Team Performance/Targets scope.
- Employees: can read their own non-draft reviews, acknowledge/comment on their own review, and update the status of their own action items.
- Employees cannot see manager drafts.
- Employees cannot edit manager review fields or cancel action items.

## Review lifecycle

`DRAFT → SHARED → IN_PROGRESS → COMPLETED`

- Manager creates a draft.
- Manager shares it with the employee.
- Employee acknowledgment moves a shared review into `IN_PROGRESS`.
- Review completion is blocked while open/in-progress action items remain.

## Review snapshots

At creation time, the review stores a snapshot from the same Phase 3/4/6 reporting stack:

- Performance Score
- Performance status
- Target Achievement
- Target status
- Completed/total tasks
- Overdue
- Actual hours

Changing targets later does not rewrite historical review snapshots.

## Management UI

Inside the existing `/team-performance` page, Phase 7 adds:

- Reviews & Coaching card
- Reviews Due
- Open Actions
- Overdue Actions
- Employees Needing Follow-up
- Completed Reviews
- Review History
- Start Review workflow
- Review details/edit modal
- Strengths and improvement areas
- Follow-up date
- Action Plan creation and status management
- Share with Employee
- Employee Acknowledgment/comment
- Complete Review control

## Employee Drawer

Adds `Reviews & Action Plans` inside the existing Employee Details drawer.

Managers can start a review directly from the employee context. Employees can open and acknowledge their own shared review.

## Audit

All mutations write awaited entries to the existing `WorkspaceAuditLog` architecture:

- `performance_review_created`
- `performance_review_updated`
- `performance_review_shared`
- `performance_review_acknowledged`
- `performance_review_completed`
- `performance_action_created`
- `performance_action_updated`
- `performance_action_cancelled`

## Apply

```bash
rm -rf /tmp/TOS-Patchs
git clone https://github.com/mohamedamouseo-a11y/TOS-Patchs.git /tmp/TOS-Patchs
bash /tmp/TOS-Patchs/TOS-PHASE7-PERFORMANCE-REVIEWS-COACHING-ACTION-PLANS-V1-GIT-GENERATED/run_phase7_performance_reviews_coaching_action_plans_v1.sh /var/www/TOS
```

Expected core output:

- `BASELINE_CHECK=PASS`
- `TARGETS_CLEAN=PASS`
- `PRISMA_REVIEW_MODELS=PASS`
- `PRISMA_REVIEW_MIGRATION=PASS`
- `PRISMA_VALIDATE=PASS`
- `PRISMA_DEPLOY=PASS`
- `PRISMA_GENERATE=PASS`
- `BACKEND_SYNTAX=PASS`
- `BACKEND_REVIEW_CONTRACT=PASS`
- `REVIEW_RBAC_GUARDS=PASS`
- `PHASE6_TARGET_REGRESSION=PASS`
- `PHASE3_SCORE_FORMULA_REGRESSION=PASS`
- `FRONTEND_REVIEW_API=PASS`
- `FRONTEND_REVIEW_INTEGRATION=PASS`
- `FRONTEND_BUILD=PASS`
- `GIT_DIFF_CHECK=PASS`
- `PHASE7_PERFORMANCE_REVIEWS_COACHING_ACTION_PLANS_V1_APPLIED=YES`
- `NO_GIT_COMMIT_OR_PUSH_PERFORMED=YES`

## Required runtime QA before TOS push

1. Admin creates a draft review for a real employee.
2. Review snapshot matches Team Performance + Targets for the selected period.
3. Exact duplicate open review for same employee/exact period is blocked with HTTP 409.
4. Authorized manager can review in-scope employee.
5. Manager receives HTTP 403 for real out-of-scope employee.
6. Employee cannot see a DRAFT review.
7. Manager shares review; employee can then see it.
8. Employee acknowledgment stores comment/time and moves SHARED → IN_PROGRESS.
9. Employee cannot edit manager fields or cancel action items.
10. Manager creates action items; employee can move them OPEN → IN_PROGRESS → COMPLETED.
11. Manager cannot complete review while open actions remain.
12. After all actions are completed/cancelled, review can complete.
13. Summary counters match DB state: reviews due, open actions, overdue actions, follow-up employees.
14. Audit entries exist for every tested mutation.
15. Phase 3 score remains unchanged.
16. Phase 5 Intelligence remains intact.
17. Phase 6 Goals & Targets remains intact.
18. `/team-performance` desktop/mobile/light/dark UI remains clean and no duplicate dashboard is introduced.
19. Existing PM2 services only are restarted.
20. Final Git status contains only Phase 7 expected files.

## Git workflow

OpenHands must not commit or push TOS.

After server QA, TOS is pushed manually from Developer Hub, then the resulting GitHub commit must be reviewed before Phase 7 is closed.
