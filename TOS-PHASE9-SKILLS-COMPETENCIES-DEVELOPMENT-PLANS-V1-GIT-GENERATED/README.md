# TOS Phase 9 — Skills, Competencies & Development Plans V1

Baseline TOS commit:

`225230b9a79b839b8fc8ee60aa5f5869e8dba9b1`

Phase 9 adds an employee capability and development layer inside the existing `/team-performance` experience.

It does **not** create a new Performance Score and does **not** change the Phase 3 score.

It preserves:

- Phase 3 Performance Score / Ranking
- Phase 4 Management Dashboard / exports
- Phase 5 Performance Intelligence
- Phase 6 Goals & Targets
- Phase 7 Reviews, Coaching & Action Plans
- Phase 8 Predictive Performance & Workforce Planning

## TOS files changed/generated

- `backend/prisma/schema.prisma`
- `backend/prisma/migrations/202609021130_phase9_skills_competencies_development/migration.sql`
- `backend/src/routes/tasks.routes.js`
- `frontend/src/lib/api.js`
- `frontend/src/components/performance/SkillsDevelopment.jsx` (new)
- `frontend/src/pages/TeamPerformanceDashboard.jsx`

## Data model

### SkillDefinition

Company skill catalog:

- name
- category
- description
- active/inactive state
- audit creator/updater fields

### CompetencyRequirement

Defines the required proficiency for a skill by:

- `DEPARTMENT`
- `JOB_TITLE`
- `EMPLOYEE`

Requirement fields:

- skill
- target level 1–5
- importance: `CORE`, `IMPORTANT`, `OPTIONAL`
- active/inactive history

### EmployeeSkillAssessment

Official manager/admin assessment:

- employee
- skill
- current level 1–5
- evidence / manager note
- assessor
- assessment timestamp

One current official assessment exists per employee + skill. Changes remain traceable through Workspace Audit Log.

### EmployeeDevelopmentPlan

Development plan fields:

- employee
- optional primary skill
- optional Phase 7 `sourceReviewId`
- title
- objective
- status
- current-level snapshot
- target level
- start / target date
- completion timestamp

Lifecycle:

`DRAFT → ACTIVE → COMPLETED`

or manager cancellation:

`DRAFT/ACTIVE → CANCELLED`

### EmployeeDevelopmentAction

Trackable action inside a development plan:

- optional skill
- title / description
- due date
- status
- completion timestamp

Lifecycle:

`TODO → IN_PROGRESS → COMPLETED`

Manager can cancel an action. Employee cannot cancel actions or rewrite manager action content.

## Proficiency scale

- `1` Awareness
- `2` Basic
- `3` Working
- `4` Advanced
- `5` Expert

No zero-value assessment is stored. Missing assessment means **Not Assessed**.

## Requirement precedence

When more than one requirement applies to an employee:

1. `EMPLOYEE`
2. `JOB_TITLE`
3. `DEPARTMENT`

This makes employee-specific overrides deterministic.

## Skill-gap semantics

For an effective requirement:

- `MET`: current level >= target
- `NEAR`: exactly one level below target
- `GAP`: more than one level below target for non-core skill
- `CRITICAL_GAP`: CORE skill is unassessed or at least two levels below target
- `UNASSESSED`: required non-core skill has no official assessment
- `ADDITIONAL`: assessed skill with no effective requirement

## Skill Coverage

Skill Coverage is deliberately separate from Performance Score.

`coverage = met effective requirements / total effective requirements * 100`

Unassessed required skills do not count as met.

A skill assessment, requirement, or development plan must never change Phase 3 Performance Score.

## Backend APIs

### Skills matrix

- `GET /api/tasks/reports/team-performance/skills/matrix`

Filters:

- `employeeId`
- `department`

Returns:

- methodology
- company/team summary
- employee rows
- resolved skills
- requirement source
- proficiency gaps
- priority gaps
- development counters

### Skill catalog

- `GET /api/tasks/reports/team-performance/skills/catalog`
- `POST /api/tasks/reports/team-performance/skills/catalog`
- `PATCH /api/tasks/reports/team-performance/skills/catalog/:skillId`
- `DELETE /api/tasks/reports/team-performance/skills/catalog/:skillId`

Delete is soft deactivation.

### Competency requirements

- `GET /api/tasks/reports/team-performance/skills/requirements`
- `POST /api/tasks/reports/team-performance/skills/requirements`
- `PATCH /api/tasks/reports/team-performance/skills/requirements/:requirementId`
- `DELETE /api/tasks/reports/team-performance/skills/requirements/:requirementId`

Delete is soft deactivation.

Exact active duplicate requirement for the same skill + scope subject is blocked with HTTP `409`.

### Skill assessments

- `POST /api/tasks/reports/team-performance/skills/assessments`
- `DELETE /api/tasks/reports/team-performance/skills/assessments/:employeeId/:skillId`

POST performs an official upsert for employee + skill.

### Development plans

- `GET /api/tasks/reports/team-performance/development-plans`
- `POST /api/tasks/reports/team-performance/development-plans`
- `PATCH /api/tasks/reports/team-performance/development-plans/:planId`
- `POST /api/tasks/reports/team-performance/development-plans/:planId/activate`
- `POST /api/tasks/reports/team-performance/development-plans/:planId/complete`
- `DELETE /api/tasks/reports/team-performance/development-plans/:planId`
- `POST /api/tasks/reports/team-performance/development-plans/:planId/actions`
- `PATCH /api/tasks/reports/team-performance/development-plans/:planId/actions/:actionId`
- `DELETE /api/tasks/reports/team-performance/development-plans/:planId/actions/:actionId`

An employee cannot see a manager DRAFT development plan.

Plan completion is blocked while `TODO` / `IN_PROGRESS` actions remain.

## RBAC

### System Admin / Admin

Can:

- manage global Skill Catalog
- manage Department / Job Title / Employee competency requirements
- assess authorized employees
- create/manage development plans and actions

### Manager / Project Manager

Can:

- view skills for project-reachable employees
- assess project-reachable employees
- create/manage development plans for project-reachable employees

Cannot:

- change global skill catalog
- change company-wide competency requirements
- manage out-of-scope employees

### Team Member

Can:

- view own skills and effective requirements
- view own ACTIVE/COMPLETED development plans
- update own development-action status

Cannot:

- see manager DRAFT development plans
- self-assess official proficiency
- edit plan/manager content
- cancel development actions

## Phase 7 linkage

A development plan can optionally store `sourceReviewId` for a Phase 7 Performance Review belonging to the same employee.

This is a traceability link only.

Phase 9 does not modify the source Performance Review or its Action Plans.

## Audit events

Awaited `WorkspaceAuditLog` events include:

- `skill_definition_created`
- `skill_definition_updated`
- `skill_definition_deactivated`
- `competency_requirement_created`
- `competency_requirement_updated`
- `competency_requirement_deactivated`
- `employee_skill_assessed`
- `employee_skill_assessment_removed`
- `employee_development_plan_created`
- `employee_development_plan_updated`
- `employee_development_plan_activated`
- `employee_development_plan_completed`
- `employee_development_plan_cancelled`
- `employee_development_action_created`
- `employee_development_action_updated`
- `employee_development_action_cancelled`

## UI

Inside the same `/team-performance` page:

### Skills Matrix & Development Plans

KPIs:

- Skill Coverage
- Critical Gaps
- Unassessed Required
- Active Development Plans
- Overdue Development Actions

Management sections:

- Team Skills Matrix
- Priority Skill Gaps
- Development Plans
- official Skill Assessment
- Create Development Plan
- Development Actions

### Manage Framework

Admin-only modal:

- Skill Catalog
- categories
- skill descriptions
- competency requirements
- Department / Job Title / Employee override scopes
- target proficiency
- importance
- soft deactivation / history

### Employee Drawer

Adds `Skills & Development / Competencies & Growth Plan` inside the existing employee drawer.

It shows:

- Skill Coverage
- Required Skills
- Gaps
- Critical Gaps
- Current vs Target proficiency
- requirement source
- Development Plans
- Development Actions

Existing Goals & Targets, Reviews & Action Plans, Workforce Outlook, Score Breakdown, Performance History, Tasks and Activity remain intact.

## Apply

```bash
rm -rf /tmp/TOS-Patchs
git clone https://github.com/mohamedamouseo-a11y/TOS-Patchs.git /tmp/TOS-Patchs
bash /tmp/TOS-Patchs/TOS-PHASE9-SKILLS-COMPETENCIES-DEVELOPMENT-PLANS-V1-GIT-GENERATED/run_phase9_skills_competencies_development_plans_v1.sh /var/www/TOS
```

Expected core output:

- `BASELINE_CHECK=PASS`
- `TARGETS_CLEAN=PASS`
- `PHASE8_BASELINE_PRESENT=PASS`
- `PRISMA_SKILLS_MODELS=PASS`
- `PRISMA_SKILLS_MIGRATION=PASS`
- `BACKEND_SKILLS_MATRIX=PASS`
- `BACKEND_SKILLS_CATALOG=PASS`
- `BACKEND_COMPETENCY_REQUIREMENTS=PASS`
- `BACKEND_SKILL_ASSESSMENTS=PASS`
- `BACKEND_DEVELOPMENT_PLANS=PASS`
- `SKILLS_RBAC_GUARDS=PASS`
- `SKILL_REQUIREMENT_PRECEDENCE=PASS`
- `SKILLS_BULK_AGGREGATION=PASS`
- `EMPLOYEE_DEVELOPMENT_DRAFT_PRIVACY=PASS`
- `DEVELOPMENT_STATUS_FILTER_HARDENING=PASS`
- `FRONTEND_SKILLS_API=PASS`
- `FRONTEND_SKILLS_COMPONENT=PASS`
- `FRONTEND_SKILLS_DASHBOARD=PASS`
- `FRONTEND_SKILLS_DRAWER=PASS`
- `PRISMA_VALIDATE=PASS`
- `PRISMA_DEPLOY=PASS`
- `PRISMA_GENERATE=PASS`
- `BACKEND_SYNTAX=PASS`
- `PRISMA_SKILLS_CONTRACT=PASS`
- `BACKEND_SKILLS_CONTRACT=PASS`
- `SKILL_COVERAGE_SEPARATE_FROM_SCORE=PASS`
- `FRONTEND_SKILLS_INTEGRATION=PASS`
- `PHASE3_SCORE_FORMULA_REGRESSION=PASS`
- `PHASE5_INTELLIGENCE_REGRESSION=PASS`
- `PHASE6_TARGET_REGRESSION=PASS`
- `PHASE7_REVIEW_REGRESSION=PASS`
- `PHASE8_WORKFORCE_REGRESSION=PASS`
- `FRONTEND_BUILD=PASS`
- `GIT_DIFF_CHECK=PASS`
- `EXPECTED_FILE_SCOPE=PASS`
- `PHASE9_SKILLS_COMPETENCIES_DEVELOPMENT_PLANS_V1_APPLIED=YES`
- `NO_GIT_COMMIT_OR_PUSH_PERFORMED=YES`

## Required runtime QA before TOS push

1. Admin creates an active Skill Definition.
2. Exact active duplicate skill name/category returns `409`.
3. Manager cannot create/update/deactivate Skill Definition (`403`).
4. Admin creates Department requirement.
5. Admin creates Job Title requirement for same skill.
6. Admin creates Employee override for same skill.
7. Verify effective requirement precedence: Employee > Job Title > Department.
8. Exact duplicate active requirement for same skill/scope subject returns `409`.
9. Invalid Employee requirement returns `404`.
10. Invalid Department requirement returns `404`.
11. Admin/authorized Manager assesses a real employee skill.
12. Manager outside project scope receives `403`.
13. Team Member cannot self-assess (`403`).
14. Verify level only accepts integer 1–5.
15. Matrix returns correct current level, target, gap, requirement source and status.
16. CORE unassessed or gap >=2 becomes `CRITICAL_GAP`.
17. One-level gap becomes `NEAR`.
18. Current >= target becomes `MET`.
19. Verify Skill Coverage denominator uses effective requirements only.
20. Verify skill changes do not change Performance Score.
21. Manager creates DRAFT development plan for real employee.
22. Employee cannot see DRAFT plan.
23. Manager activates plan; employee can then see it.
24. Manager creates development actions.
25. Employee can move own action `TODO → IN_PROGRESS → COMPLETED`.
26. Employee cannot cancel action or rewrite title/description/due date.
27. Manager cannot complete plan while open actions remain (`409`).
28. After actions complete/cancel, manager completes plan.
29. Optional sourceReviewId must belong to the same employee.
30. Phase 7 review/action records are not mutated by development-plan operations.
31. Workspace audit records exist for all tested mutations.
32. Matrix/plan endpoints use bulk queries and avoid Prisma calls inside employee/skill/action loops.
33. Record skills matrix and development-plan response times.
34. Verify Phases 3,5,6,7,8 remain operational.
35. Verify `/team-performance` shows exactly one Skills & Development section.
36. Verify Employee Drawer includes Skills & Development plus all prior sections.
37. Verify desktop/mobile/light/dark UI.
38. Clean only proven Phase 9 QA records.
39. Build frontend.
40. **Deploy current build to runtime directory:** copy `frontend/dist/` contents to `/opt/apps/tamiyouz-front/build/`.
41. Reload existing `tamiyouz-frontend` PM2 service only.
42. Verify `tamiyouz-system` and `tamiyouz-frontend` ONLINE and `/team-performance` HTTP 200.
43. Final Git status contains only Phase 9 expected source/migration files.

## Expected final Git status

```text
 M backend/prisma/schema.prisma
 M backend/src/routes/tasks.routes.js
 M frontend/src/lib/api.js
 M frontend/src/pages/TeamPerformanceDashboard.jsx
?? backend/prisma/migrations/202609021130_phase9_skills_competencies_development/
?? frontend/src/components/performance/SkillsDevelopment.jsx
```

OpenHands must not commit or push TOS.

Final TOS push remains manual through Developer Hub after QA passes.
