# TOS Phase 10 — Talent Matrix & Succession Planning V1

Baseline TOS commit:

`20aa559dfcf397aa8ea31453e2ea911b26ddb2b4`

Phase 10 adds a manager-only talent and succession planning layer inside the existing `/team-performance` experience.

It preserves Phases 3–9 and does not create a replacement Performance Score.

## Design principles

- Phase 3 Performance Score remains the only performance score.
- Potential is explicitly entered by an authorized manager/admin.
- Succession readiness is explicitly entered by an authorized manager/admin.
- Skills / development data from Phase 9 is context only.
- TOS does not infer potential or readiness from protected/sensitive personal attributes.
- No automatic promotion, demotion, termination, compensation, or reassignment.
- 9-box is a management discussion aid, not an employment decision engine.
- Talent/succession data is manager-only and hidden from Team Members.

## Files changed/generated

- `backend/prisma/schema.prisma`
- `backend/prisma/migrations/202609021410_phase10_talent_matrix_succession_planning/migration.sql`
- `backend/src/routes/tasks.routes.js`
- `frontend/src/lib/api.js`
- `frontend/src/components/performance/TalentSuccession.jsx` (new)
- `frontend/src/pages/TeamPerformanceDashboard.jsx`

## Data model

### TalentAssessment

One current manager assessment per employee:

- employeeId
- potentialLevel: `LOW | MEDIUM | HIGH`
- evidence
- managerNote
- isActive
- assessedById / assessedAt
- updatedById
- timestamps

A new assessment upserts the current record. Deactivation preserves the record and audit trail.

### SuccessionRole

Admin-configured succession role:

- title
- optional department
- criticality: `NORMAL | HIGH | CRITICAL`
- optional incumbentEmployeeId
- description
- active state
- audit creator/updater fields

Exact active title + department duplicates are blocked at application level.

### SuccessionCandidate

Candidate nomination for a succession role:

- roleId
- employeeId
- readiness:
  - `DEVELOPING`
  - `READY_3_PLUS_YEARS`
  - `READY_1_2_YEARS`
  - `READY_NOW`
- bench priority 1–5
- rationale
- optional Phase 9 developmentPlanId
- active state
- nomination/update audit IDs

One record exists per role + employee; re-nomination updates/reactivates the existing record.

## 9-Box methodology

### Performance axis

Uses the existing Phase 3 score only:

- HIGH = 85–100
- MEDIUM = 70–84
- LOW = below 70
- No Activity / null score = `NO_DATA` and remains unclassified

### Potential axis

Explicit manager/admin assessment only:

- HIGH
- MEDIUM
- LOW

No potential assessment = unclassified.

### 9 cells

- HIGH potential + HIGH performance → Future Leader
- HIGH potential + MEDIUM performance → Emerging Talent
- HIGH potential + LOW performance → Untapped Potential
- MEDIUM potential + HIGH performance → High Performer
- MEDIUM potential + MEDIUM performance → Core Talent
- MEDIUM potential + LOW performance → Development Focus
- LOW potential + HIGH performance → Expert Contributor
- LOW potential + MEDIUM performance → Solid Contributor
- LOW potential + LOW performance → Performance Support

The labels are planning categories only. They do not trigger an automated HR action.

## Succession coverage

For active HIGH/CRITICAL roles, the dashboard shows:

- role count
- covered roles with at least one active candidate
- succession gaps with no active candidate
- Ready Now candidate count
- bench depth
- incumbent
- candidate readiness and priority

Readiness is never derived from performance, 9-box position, skill coverage, or any hidden model.

## RBAC

### SUPER_ADMIN / ADMIN

Can:

- view all accessible talent planning data
- assess employee potential
- create/update/deactivate Succession Roles
- nominate/update/deactivate succession candidates

### MANAGER / PROJECT_MANAGER

Can:

- view talent data for project-reachable employees
- assess potential for project-reachable employees
- view succession roles for departments represented in their accessible employee scope
- nominate/update/deactivate candidates only when the employee is in their accessible scope

Cannot:

- create/update/deactivate company succession-role definitions
- manage out-of-scope employees

### TEAM_MEMBER

Cannot access Phase 10 talent/succession endpoints or UI.

Potential and succession nominations are intentionally management-private.

## Backend APIs

### Overview

`GET /api/tasks/reports/team-performance/talent/overview`

Filters:

- start
- end
- employeeId
- department

Returns:

- methodology
- summary
- 9-box cells
- employee talent rows
- Phase 3 performance band
- Phase 9 skill coverage context
- succession nominations
- succession-role coverage

### Potential assessment

- `POST /api/tasks/reports/team-performance/talent/assessments`
- `DELETE /api/tasks/reports/team-performance/talent/assessments/:employeeId`

### Succession roles

- `GET /api/tasks/reports/team-performance/talent/succession-roles`
- `POST /api/tasks/reports/team-performance/talent/succession-roles`
- `PATCH /api/tasks/reports/team-performance/talent/succession-roles/:roleId`
- `DELETE /api/tasks/reports/team-performance/talent/succession-roles/:roleId`

Role configuration writes are Admin-only.

### Succession candidates

- `POST /api/tasks/reports/team-performance/talent/succession-roles/:roleId/candidates`
- `PATCH /api/tasks/reports/team-performance/talent/succession-roles/:roleId/candidates/:candidateId`
- `DELETE /api/tasks/reports/team-performance/talent/succession-roles/:roleId/candidates/:candidateId`

## Audit events

Awaited WorkspaceAuditLog events:

- `talent_assessment_created`
- `talent_assessment_updated`
- `talent_assessment_deactivated`
- `succession_role_created`
- `succession_role_updated`
- `succession_role_deactivated`
- `succession_candidate_nominated`
- `succession_candidate_updated`
- `succession_candidate_deactivated`

## UI

Inside existing `/team-performance`:

### Talent Matrix & Succession Planning

- manager-only badge
- 9-Box Talent & Succession Bench
- Potential Assessed KPI
- 9-Box Classified KPI
- High Potential KPI
- Critical Roles KPI
- Succession Gaps KPI
- Ready Now KPI
- interactive 9-box employee chips
- succession coverage cards
- Assess Potential modal
- Succession Bench modal

### Admin Succession Role management

- role title
- department
- criticality
- incumbent
- description
- deactivate role

### Candidate nomination

- succession role
- employee
- readiness
- bench priority
- rationale
- removal/deactivation

### Employee drawer

Manager-only section:

`Talent & Succession`

Shows:

- Phase 3 performance band
- manager-assessed potential
- 9-box position
- Phase 9 skill coverage context
- critical skill gaps context
- active succession nominations
- readiness and priority

Existing Goals, Reviews, Workforce, Skills, Score, History, Tasks and Activity remain unchanged.

## Apply

```bash
rm -rf /tmp/TOS-Patchs
git clone https://github.com/mohamedamouseo-a11y/TOS-Patchs.git /tmp/TOS-Patchs
bash /tmp/TOS-Patchs/TOS-PHASE10-TALENT-MATRIX-SUCCESSION-PLANNING-V1-GIT-GENERATED/run_phase10_talent_matrix_succession_planning_v1.sh /var/www/TOS
```

Expected checks include:

- `BASELINE_CHECK=PASS`
- `TARGETS_CLEAN=PASS`
- `PHASE9_BASELINE_PRESENT=PASS`
- `PRISMA_TALENT_MODELS=PASS`
- `PRISMA_TALENT_MIGRATION=PASS`
- `BACKEND_TALENT_OVERVIEW=PASS`
- `BACKEND_TALENT_ASSESSMENTS=PASS`
- `BACKEND_SUCCESSION_ROLES=PASS`
- `BACKEND_SUCCESSION_CANDIDATES=PASS`
- `TALENT_DECISION_SUPPORT_GUARD=PASS`
- `PRISMA_VALIDATE=PASS`
- `PRISMA_DEPLOY=PASS`
- `PRISMA_GENERATE=PASS`
- `BACKEND_SYNTAX=PASS`
- `PRISMA_TALENT_CONTRACT=PASS`
- `BACKEND_TALENT_CONTRACT=PASS`
- `TALENT_HUMAN_DECISION_GUARD=PASS`
- `FRONTEND_TALENT_API=PASS`
- `FRONTEND_TALENT_COMPONENT=PASS`
- `FRONTEND_TALENT_DASHBOARD=PASS`
- `FRONTEND_TALENT_DRAWER=PASS`
- `PHASE3_SCORE_FORMULA_REGRESSION=PASS`
- `PHASE5_INTELLIGENCE_REGRESSION=PASS`
- `PHASE6_TARGET_REGRESSION=PASS`
- `PHASE7_REVIEW_REGRESSION=PASS`
- `PHASE8_WORKFORCE_REGRESSION=PASS`
- `PHASE9_SKILLS_REGRESSION=PASS`
- `FRONTEND_BUILD=PASS`
- `GIT_DIFF_CHECK=PASS`
- `EXPECTED_FILE_SCOPE=PASS`
- `PHASE10_TALENT_MATRIX_SUCCESSION_PLANNING_V1_APPLIED=YES`
- `NO_GIT_COMMIT_OR_PUSH_PERFORMED=YES`

## Runtime deployment

After build, deploy the fresh frontend output to the live runtime directory to prevent the stale-build issue already observed in TOS:

```bash
rm -rf /opt/apps/tamiyouz-front/build/*
cp -a /var/www/TOS/frontend/dist/. /opt/apps/tamiyouz-front/build/
pm2 reload tamiyouz-frontend
```

Do not create a second PM2 frontend service.

## Final QA policy for this phase

Per current project workflow, comprehensive authenticated runtime QA is deferred to the final end-to-end test after all planned phases.

The final E2E gate must later verify at minimum:

1. Admin potential assessment create/update/deactivate.
2. Manager in-scope potential assessment allowed.
3. Manager out-of-scope blocked.
4. Team Member talent overview blocked and Phase 10 UI hidden.
5. Null Phase 3 score remains unclassified.
6. Performance band thresholds: <70 / 70–84 / 85+.
7. Potential is never inferred automatically.
8. 9-box cell resolution for all 9 combinations.
9. Skill data does not alter potential/readiness.
10. Admin role creation and exact duplicate 409.
11. Manager role creation blocked 403.
12. Invalid department/incumbent validation.
13. Candidate nomination / update / deactivation.
14. Incumbent cannot be their own successor.
15. Readiness validation.
16. Priority validation 1–5.
17. Optional developmentPlanId belongs to candidate employee.
18. Critical-role coverage counts.
19. Ready Now counts.
20. Audit trail.
21. No Prisma query inside employee/candidate matrix loops.
22. Phase 3–9 regression suite.
23. Desktop/mobile/light/dark UI.
24. QA cleanup.

## Expected final Git status after apply

```text
 M backend/prisma/schema.prisma
 M backend/src/routes/tasks.routes.js
 M frontend/src/lib/api.js
 M frontend/src/pages/TeamPerformanceDashboard.jsx
?? backend/prisma/migrations/202609021410_phase10_talent_matrix_succession_planning/
?? frontend/src/components/performance/TalentSuccession.jsx
```

OpenHands must not commit or push TOS. Final TOS push remains manual through Developer Hub after the apply/build/deployment report is reviewed.
