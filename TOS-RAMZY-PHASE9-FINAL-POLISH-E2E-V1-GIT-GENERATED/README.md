# TOS — Ramzy Phase 9: Final Polish & E2E

Baseline TOS HEAD:

`1642787ecdb41015be37329a72d6485b79961abb`

## Purpose

Close the Ramzy refinement roadmap with source-level privacy polish, complete Arabic/English UI polish, evidence presentation cleanup, and production smoke/E2E guards.

## Main changes

- Removes the remaining alias clarification path that asked the user for a database ID.
- Removes the `assigneeId` fallback from approval-card display so an internal user ID cannot appear when the assignee name is absent.
- Adds bilingual Arabic/English suggestions, approval titles/details/actions/statuses, response action labels and error copy.
- Expands the composer wording from tasks/projects to the wider TOS scope introduced in Phase 7.
- Shows a human-readable authorized scope beside every Evidence source without exposing scope IDs.
- Adds compact theme-safe styling for the Evidence disclosure.
- Adds `ramzyFinalPolishE2E.static.test.js` covering Phase 7 knowledge, Phase 8 RBAC/evidence, ID-leak guards and final UI localization.
- Runner uses the real production backend PM2 name `tamiyouz-system` with `tamiyouz-backend` as a compatibility fallback.
- Runner verifies `/api/agent/status` and `/api/agent/audit` reject anonymous requests, while health/dashboard/team-performance/tasks remain healthy.
- Runner verifies the built frontend is byte-for-byte deployed to `/opt/apps/tamiyouz-front/build`.

## TOS files changed

Exactly 4 files:

- `backend/src/agency-operator/services/ramzySystemIntelligence.service.js`
- `backend/src/agency-operator/tests/ramzyFinalPolishE2E.static.test.js` (new)
- `frontend/src/components/RamzyAssistant.jsx`
- `frontend/src/index.css`

No Prisma/schema/migration/package changes. No Performance Score, performance permission defaults, task action semantics, or approval execution rules are changed.

## Run

```bash
cd /var/www/TOS-Patchs
git pull --ff-only origin main
cd TOS-RAMZY-PHASE9-FINAL-POLISH-E2E-V1-GIT-GENERATED
bash run_phase9_ramzy_final_polish_e2e_v1.sh
```

Do not commit or push TOS from OpenHands. The owner pushes manually after review.
