# TOS Phase 11 — Recognition, Rewards & Performance Cycles V1

Baseline TOS commit:

`7cefa3ef82cad91a90b184fc1f8e4e12ec670a47`

Phase 11 adds structured recognition cycles, manager nominations, human approval, published recognition history and non-payroll reward tracking inside the existing `/team-performance` experience.

It preserves Phases 3–10.

## Core principles

- Phase 3 Performance Score remains unchanged.
- Performance Score and Phase 6 target achievement are stored only as nomination context snapshots.
- TOS never auto-nominates, auto-approves, auto-rejects or auto-issues a reward.
- Reward data is explicitly non-payroll.
- No salary, bonus, commission, payroll or compensation calculation is introduced.
- Human Admin approval is required before a nomination becomes an award.
- Cycle opening/closing never creates HR decisions automatically.

## Files changed/generated

- `backend/prisma/schema.prisma`
- `backend/prisma/migrations/202609021430_phase11_recognition_rewards_performance_cycles/migration.sql`
- `backend/src/routes/tasks.routes.js`
- `frontend/src/lib/api.js`
- `frontend/src/components/performance/RecognitionRewards.jsx` (new)
- `frontend/src/pages/TeamPerformanceDashboard.jsx`

## Data model

### RecognitionPerformanceCycle

Performance/recognition cycle metadata:

- name
- cycle type: `MONTHLY | QUARTERLY | ANNUAL | CUSTOM`
- optional department scope
- start/end dates
- optional nomination window
- lifecycle: `DRAFT → OPEN → CLOSED`
- soft active state
- audit creator/updater fields

Cycles may overlap because annual, quarterly and department cycles can legitimately coexist.

### RecognitionCategory

Admin-configured recognition/reward framework:

- name
- category type: `RECOGNITION | REWARD`
- description / criteria
- non-payroll reward type:
  - `NONE`
  - `BADGE`
  - `CERTIFICATE`
  - `GIFT`
  - `EXPERIENCE`
  - `OTHER`
- optional default non-payroll reward description
- soft active state

Exact active category-name duplicates are blocked at application level.

### RecognitionNomination

Manager nomination record:

- cycle
- category
- nominated employee
- nominating manager/admin
- reason
- lifecycle: `PENDING | APPROVED | REJECTED`
- review note / reviewer / reviewed timestamp
- snapshot Phase 3 Performance Score
- snapshot Phase 3 status
- snapshot Phase 6 target achievement

Only one nomination for the same employee + category + cycle is allowed.

The snapshot fields are decision context only.

### RecognitionAward

Award created only after explicit Admin approval:

- cycle
- category
- employee
- source nomination
- recognition title/message
- non-payroll reward type/description
- issuer
- issue timestamp
- published/unpublished state

One nomination can produce at most one award.

## RBAC

### SUPER_ADMIN / ADMIN

Can:

- view all accessible recognition data
- configure cycles
- open/close/deactivate cycles
- configure recognition categories
- submit nominations
- approve/reject nominations
- issue/publish/unpublish recognition awards

### MANAGER / PROJECT_MANAGER

Can:

- view recognition overview for project-reachable employees
- see company cycles plus department cycles represented by their accessible scope
- nominate project-reachable employees during an OPEN nomination window
- view nomination and recognition status inside their scope

Cannot:

- configure cycles/categories
- approve/reject nominations
- issue rewards
- nominate themselves
- nominate out-of-scope employees

### TEAM_MEMBER

Cannot access the management overview or management controls.

A Team Member can read their own published recognition history through the employee-recognition endpoint. Internal nominations and unpublished awards are hidden.

## Performance context semantics

At nomination time TOS snapshots:

- Phase 3 Performance Score
- Phase 3 performance status
- Phase 6 target achievement

These values are displayed to Admins reviewing the nomination.

They are **not eligibility rules**.

There is no rule such as:

- score >= X → award
- top rank → reward
- target exceeded → bonus
- 9-box position → recognition

All nomination and approval decisions remain explicit human actions.

## Backend APIs

### Overview

`GET /api/tasks/reports/team-performance/recognition/overview`

Manager/Admin only.

Filters:

- employeeId
- department

Returns:

- methodology
- summary KPIs
- cycles
- categories
- nominations
- awards

### Performance cycles

- `GET /api/tasks/reports/team-performance/recognition/cycles`
- `POST /api/tasks/reports/team-performance/recognition/cycles`
- `PATCH /api/tasks/reports/team-performance/recognition/cycles/:cycleId`
- `POST /api/tasks/reports/team-performance/recognition/cycles/:cycleId/open`
- `POST /api/tasks/reports/team-performance/recognition/cycles/:cycleId/close`
- `DELETE /api/tasks/reports/team-performance/recognition/cycles/:cycleId`

Writes are Admin-only.

### Recognition categories

- `GET /api/tasks/reports/team-performance/recognition/categories`
- `POST /api/tasks/reports/team-performance/recognition/categories`
- `PATCH /api/tasks/reports/team-performance/recognition/categories/:categoryId`
- `DELETE /api/tasks/reports/team-performance/recognition/categories/:categoryId`

Writes are Admin-only.

### Nominations

- `POST /api/tasks/reports/team-performance/recognition/nominations`
- `POST /api/tasks/reports/team-performance/recognition/nominations/:nominationId/approve`
- `POST /api/tasks/reports/team-performance/recognition/nominations/:nominationId/reject`

Manager/Admin can nominate.

Approval/rejection is Admin-only.

### Awards / recognition history

- `PATCH /api/tasks/reports/team-performance/recognition/awards/:awardId`
- `GET /api/tasks/reports/team-performance/recognition/feed`
- `GET /api/tasks/reports/team-performance/recognition/employee/:employeeId`

Published feed is authenticated read-only.

Own employee history exposes published awards only for a non-manager employee.

## Audit events

Awaited WorkspaceAuditLog events include:

- `performance_cycle_created`
- `performance_cycle_updated`
- `performance_cycle_opened`
- `performance_cycle_closed`
- `performance_cycle_deactivated`
- `recognition_category_created`
- `recognition_category_updated`
- `recognition_category_deactivated`
- `recognition_nomination_created`
- `recognition_nomination_approved`
- `recognition_nomination_rejected`
- `recognition_award_issued`
- `recognition_award_updated`

## UI

Inside the same `/team-performance` page for Manager/Admin:

### Recognition, Rewards & Performance Cycles

KPIs:

- Open Cycles
- Pending Nominations
- Approved Nominations
- Published Recognitions
- Non-payroll Rewards

Sections:

- Performance Cycles
- Recognition Nominations
- Recognition & Rewards History
- Nominate Employee
- Admin Cycle / Category framework
- Admin human approval flow

Nomination cards expose the Phase 3 score/status and Phase 6 target-achievement snapshot as context.

### Employee Drawer

Adds:

`Recognition & Rewards / Recognition History`

It shows:

- award count
- reward count
- pending nomination count for managers
- awards
- published/internal state for managers
- non-payroll reward descriptor
- nomination history for managers

Existing sections from Phases 3–10 remain intact.

## Apply

```bash
rm -rf /tmp/TOS-Patchs
git clone https://github.com/mohamedamouseo-a11y/TOS-Patchs.git /tmp/TOS-Patchs
bash /tmp/TOS-Patchs/TOS-PHASE11-RECOGNITION-REWARDS-PERFORMANCE-CYCLES-V1-GIT-GENERATED/run_phase11_recognition_rewards_performance_cycles_v1.sh /var/www/TOS
```

Expected core output includes:

- `BASELINE_CHECK=PASS`
- `TARGETS_CLEAN=PASS`
- `PHASE10_BASELINE_PRESENT=PASS`
- `PRISMA_RECOGNITION_MODELS=PASS`
- `PRISMA_RECOGNITION_MIGRATION=PASS`
- `BACKEND_RECOGNITION_OVERVIEW=PASS`
- `BACKEND_PERFORMANCE_CYCLES=PASS`
- `BACKEND_RECOGNITION_CATEGORIES=PASS`
- `BACKEND_RECOGNITION_NOMINATIONS=PASS`
- `BACKEND_RECOGNITION_AWARDS=PASS`
- `RECOGNITION_HUMAN_DECISION_GUARD=PASS`
- `NON_PAYROLL_REWARD_GUARD=PASS`
- `PERFORMANCE_CONTEXT_SNAPSHOT=PASS`
- `FRONTEND_RECOGNITION_API=PASS`
- `FRONTEND_RECOGNITION_COMPONENT=PASS`
- `FRONTEND_RECOGNITION_DASHBOARD=PASS`
- `FRONTEND_RECOGNITION_DRAWER=PASS`
- `PRISMA_VALIDATE=PASS`
- `PRISMA_DEPLOY=PASS`
- `PRISMA_GENERATE=PASS`
- `BACKEND_SYNTAX=PASS`
- `PHASE3_SCORE_FORMULA_REGRESSION=PASS`
- `PHASE5_INTELLIGENCE_REGRESSION=PASS`
- `PHASE6_TARGET_REGRESSION=PASS`
- `PHASE7_REVIEW_REGRESSION=PASS`
- `PHASE8_WORKFORCE_REGRESSION=PASS`
- `PHASE9_SKILLS_REGRESSION=PASS`
- `PHASE10_TALENT_REGRESSION=PASS`
- `FRONTEND_BUILD=PASS`
- `PACKAGE_SCOPE_CLEAN=PASS`
- `GIT_DIFF_CHECK=PASS`
- `EXPECTED_FILE_SCOPE=PASS`
- `PHASE11_RECOGNITION_REWARDS_PERFORMANCE_CYCLES_V1_APPLIED=YES`
- `FINAL_E2E_QA=DEFERRED_BY_PLAN`
- `NO_GIT_COMMIT_OR_PUSH_PERFORMED=YES`

## Final E2E QA plan — deferred until all phases are complete

The agreed final test should later verify with real authenticated sessions:

1. Admin creates Monthly/Quarterly/Annual/Custom cycles.
2. Cycle lifecycle DRAFT → OPEN → CLOSED.
3. Manager cannot configure cycles/categories.
4. Manager can nominate only project-reachable employees.
5. Manager cannot nominate self.
6. Team Member cannot access management overview.
7. Nomination outside OPEN window returns 409.
8. Duplicate employee/category/cycle nomination returns 409.
9. Performance and target snapshots are captured correctly.
10. Snapshot values do not auto-approve/reject.
11. Only Admin can approve/reject.
12. Approval creates exactly one award.
13. Reward types remain non-payroll.
14. No salary/bonus/commission fields or calculations exist.
15. Published feed exposes published awards only.
16. Team Member employee history exposes own published awards only.
17. WorkspaceAuditLog contains mutation events.
18. No N+1 query loops.
19. UI works desktop/mobile/light/dark.
20. Phases 3–10 still work.
21. Fresh frontend build is deployed to `/opt/apps/tamiyouz-front/build/`.
22. `tamiyouz-system` and `tamiyouz-frontend` remain ONLINE.

## Expected final Git status after patch application

```text
 M backend/prisma/schema.prisma
 M backend/src/routes/tasks.routes.js
 M frontend/src/lib/api.js
 M frontend/src/pages/TeamPerformanceDashboard.jsx
?? backend/prisma/migrations/202609021430_phase11_recognition_rewards_performance_cycles/
?? frontend/src/components/performance/RecognitionRewards.jsx
```

OpenHands must not commit or push TOS.

Final TOS push remains manual through Developer Hub after the structural/build gate passes.
