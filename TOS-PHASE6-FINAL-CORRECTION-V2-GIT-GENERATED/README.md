# TOS Phase 6 — Final Correction V2

Baseline TOS HEAD remains:

`9773ffa21fabe90c87823081984ebb6bb55999e1`

This correction is designed to run **after Phase 6 V1 has already been applied locally and before the Developer Hub push**.

It intentionally accepts the dirty Phase 6 V1 working tree and does not reset, commit, or push TOS.

## Why V2 exists

Phase 6 V1 runtime QA exposed several hardening gaps:

1. Admin writes could accept a nonexistent employee ID because admin returned before subject validation.
2. Exact duplicate active targets for the same subject and exact period were allowed.
3. Target list/write authorization reused the full Team Performance aggregation path, creating unnecessary task/activity queries and contributing to slow period tests.
4. Manager RBAC needed an explicit regression test. Managers are intentionally allowed to manage targets **inside their authorized project scope**; unauthorized employees/departments must return HTTP 403.

## What V2 changes

Only `backend/src/routes/tasks.routes.js` is additionally corrected on top of the V1 working tree.

### Subject validation

Before target create/update/copy:

- Employee IDs must resolve to a real eligible TOS user.
- Client/former-employee targets are rejected.
- Department targets must resolve to an active DepartmentUnit or a real department used by an eligible employee.

Bulk employee target creation validates all employee IDs in one query.

### Manager RBAC

Expected behavior:

- ADMIN / system admin: authorized company target management.
- MANAGER / PROJECT_MANAGER: allowed only for employees/departments reachable through projects they belong to.
- Manager targeting an employee outside authorized project scope: HTTP 403.
- Other roles: target mutation HTTP 403.

A manager being accepted for an employee inside scope is **not a failure**.

### Duplicate policy

V2 prevents accidental **exact active duplicates** when all of these match:

- scope type
- employee or department
- period type
- effectiveFrom
- effectiveTo

HTTP 409 is returned.

Intentional overlapping historical periods remain allowed and deterministic; the existing latest-effective-target precedence remains unchanged.

### Performance hardening

Target list and target write authorization no longer call the full `buildTeamPerformanceExportDataset()` aggregation merely to determine access.

Instead, a lightweight target scope resolver loads:

- authorized project memberships
- authorized user IDs
- authorized department values

Bulk authorization and duplicate checks are bulk queries, not per-employee queries.

Target Summary and Intelligence still use the real Team Performance dataset because those endpoints need actual Phase 3 metrics.

### Target Summary lookup hardening

Effective employee/department targets are indexed into maps after one target query, avoiding repeated array scans for every employee/department.

## Phase 3 safety

V2 does not modify:

- Completion 35%
- On-Time 25%
- Efficiency 20%
- Workflow 10%
- Consistency 10%
- eligible on-time denominator
- No Activity null score/rank
- primary-assignee semantics

## Existing QA data

Phase 6 V1 tests created target records in the database. Do **not** blindly delete all targets.

Before final production push, identify records created by the Phase 6 QA run using their audit entries/timestamps. Remove or deactivate only records that can be proven to be test data. Invalid employee-ID test rows and exact duplicate test rows should not remain active.

## Apply

```bash
rm -rf /tmp/TOS-Patchs
git clone https://github.com/mohamedamouseo-a11y/TOS-Patchs.git /tmp/TOS-Patchs
bash /tmp/TOS-Patchs/TOS-PHASE6-FINAL-CORRECTION-V2-GIT-GENERATED/run_phase6_final_correction_v2.sh /var/www/TOS
```

Expected core output:

- `BASELINE_CHECK=PASS`
- `PHASE6_V1_WORKTREE_CHECK=PASS`
- `TARGET_ACCESS_HARDENING=PASS`
- `INVALID_EMPLOYEE_VALIDATION=PASS`
- `MANAGER_SCOPE_ENFORCEMENT=PASS`
- `EXACT_DUPLICATE_GUARD=PASS`
- `LIGHTWEIGHT_TARGET_SCOPE=PASS`
- `BULK_NO_N_PLUS_ONE=PASS`
- `BACKEND_SYNTAX=PASS`
- `PRISMA_VALIDATE=PASS`
- `PRISMA_DEPLOY=PASS`
- `PRISMA_GENERATE=PASS`
- `PHASE3_SCORE_FORMULA_REGRESSION=PASS`
- `FRONTEND_BUILD=PASS`
- `GIT_DIFF_CHECK=PASS`
- `PHASE6_FINAL_CORRECTION_V2_APPLIED=YES`
- `NO_GIT_COMMIT_OR_PUSH_PERFORMED=YES`

## Required final QA

1. Valid admin employee target → 201.
2. Invalid employee ID → 404.
3. First exact target → 201; exact duplicate active target → 409.
4. Same subject with a different period/date range remains allowed.
5. Authorized Manager employee target → 201.
6. Unauthorized Manager employee target → 403.
7. Bulk request containing any invalid employee → 404 and creates zero rows.
8. Bulk request containing any unauthorized employee → 403 and creates zero rows.
9. Target list period endpoint returns without full task/activity aggregation.
10. Summary/Intelligence still return correct target achievement and Phase 3 scores.
11. No Activity remains `performanceScore=null`.
12. Existing Phase 5 intelligence remains intact.
13. Clean up only proven QA test target records before final push.

OpenHands must not commit or push TOS. Final TOS push is performed manually through Developer Hub.