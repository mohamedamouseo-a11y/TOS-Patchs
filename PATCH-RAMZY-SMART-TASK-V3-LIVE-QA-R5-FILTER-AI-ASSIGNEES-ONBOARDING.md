# Ramzy Smart Task V3 — Live QA R5: Canonical Project Filters + Smart Copy + Assignee 500 + First-use Onboarding

Baseline TOS:
`89760fd11a4c2cfb7e0957994aeb34f6dea5c815`

Scope ONLY:
1. Project picker canonical lifecycle filters.
2. Smart AI assistance for Task Title + Description using Ramzy's existing configured AI provider/model.
3. Fix Smart Task assignee loader HTTP 500.
4. One-time Smart Task onboarding bubble for each user.

Do NOT change unrelated Ramzy chat behavior, task permissions, approval requirements, AI provider credentials/config, task creation semantics, database task data, or nginx/deploy logic.

## 1) Project picker — use TOS lifecycle, never invented Active/Not Active

Canonical project model currently has:
- status: PLANNING | ACTIVE | ON_HOLD | DELAYED | COMPLETED | CANCELLED
- archivedAt: separate archive state

Add a compact status filter above the Smart Task project results.

Filters must follow the canonical TOS project lifecycle:
- All
- Active
- Planning
- On hold
- Delayed
- Completed
- Cancelled
- Archived

Default = ACTIVE.

Rules:
- Never create a synthetic "Not Active" state.
- Archived means `archivedAt != null`, not a made-up status enum.
- Search text and lifecycle filter must compose together.
- Preserve project status badges and existing keyboard navigation.
- Preserve permissions/visibility.
- Archived projects may be shown only if visible to the user, but MUST be disabled/non-selectable if normal TOS task-create policy forbids creating tasks in archived projects.
- Do not bypass `assertAgentTaskCreateAccess`.
- API must return enough canonical metadata for filtering: `status`, `archivedAt` (or equivalent boolean), and whether selection is allowed.
- Preserve current project-name sanitization and do not re-expose hidden client metadata in the rendered picker.

## 2) Write with Ramzy — Smart Task Title + Description

Current code already routes description generation through:
`getAgentRuntimeSettings() -> createMastraModel(settings)`

Keep using that exact configured Ramzy AI provider/model. Do NOT add a new provider or API key.

Upgrade Smart Task AI writing into a small copilot for BOTH fields:

### Task Title
Add a Sparkles action beside/under Task Title:
- blank title + useful description/context => generate a concise task title
- rough existing title => improve/clean it
- return title only, max 180 chars
- do not invent assignee, deadline, priority, project, or facts

### Description
Keep/fix the existing Write/Improve with Ramzy action:
- use title + existing description + selected project context when available
- blank description => write a useful structured description
- existing description => improve it while preserving meaning
- max 4000 chars
- do not invent facts

### API behavior
- Use the same runtime model configuration Ramzy already uses.
- Prefer one small shared AI-copy service/endpoint with mode TITLE/DESCRIPTION if cleaner; keeping backwards compatibility is acceptable.
- Project context may be optional for title writing; if a projectId is supplied, enforce existing access before using its context.
- Never auto-save or auto-create the task.
- AI output only updates the editable field; user can change it before Review/Approval.
- Clear loading/error state per field and prevent duplicate clicks.
- Arabic/English follow current UI language.

## 3) Assignees HTTP 500 — targeted fix

Confirmed source defect in current `backend/src/routes/agent.routes.js`:
`/task-create/assignees` calls `buildAgentTaskVisibilityWhere(...)`, but the symbol is not imported in that file.

Fix the missing import from the existing agent access policy module. Do not rewrite assignment permissions.

Then verify:
- endpoint no longer returns 500 for a valid visible project
- only ACTIVE users in the canonical assignable scope are returned
- existing Super Admin / department / project assignment rules remain unchanged
- AUTO recommendation still works
- no permission widening

## 4) First-use Smart Task onboarding

When a user opens Ramzy for the first time after this feature version, show a small professional bubble/popover inside/next to Ramzy:

Arabic:
`جديد ✨ تقدر دلوقتي تنشئ مهمة كاملة من خلالي.`

CTA:
`جرّب إنشاء مهمة`

English equivalent when UI is English.

Behavior:
- CTA opens the existing Smart Task flow directly.
- Dismiss/CTA marks this onboarding as seen.
- Show once per user for this onboarding version.
- Prefer an existing user-preference persistence mechanism if already present.
- Otherwise use a versioned localStorage key scoped by user id, e.g. `tos.ramzy.smart-task-onboarding.v1.<userId>`.
- No DB migration solely for this onboarding.
- Do not show if Ramzy execution is unavailable for that user.
- Must not block normal Ramzy chat.

## UX
- Keep current Ramzy design language, light/dark modes, responsive panel.
- No horizontal overflow.
- Filters must stay compact.
- Onboarding must look like a lightweight bubble, not a blocking modal.

## Files to inspect first
- `frontend/src/components/RamzyAssistant.jsx`
- `frontend/src/components/ramzySmartTaskComposerV1.css`
- `frontend/src/lib/api.js`
- `backend/src/routes/agent.routes.js`
- `backend/src/agency-operator/services/ramzyAi.service.js`
- `backend/src/agency-operator/services/ramzySmartTask.service.js`
- `backend/src/agency-operator/policies/agentAccess.service.js`
- `backend/src/services/projectAccessScope.service.js`
- `backend/prisma/schema.prisma`

## Acceptance
- Project filter uses canonical statuses + archive state; no "Not Active".
- Default project filter = ACTIVE.
- Archived state comes from `archivedAt`.
- Archived projects cannot bypass normal create restrictions.
- Assignee endpoint valid request = 200, not 500.
- Write with Ramzy works for title and description through the existing configured Ramzy AI API/model.
- No auto-create/save from AI writing.
- First-use onboarding appears once per user/version and CTA opens Smart Task.
- Approval remains mandatory.
- Frontend build PASS.
- Ramzy backend tests PASS.
- Add focused regression tests for project filtering, assignee import/endpoint, AI title+description path, and onboarding guard.

After validation:
- deploy with the existing atomic frontend deployment process as applicable
- restart only required backend service if backend changed
- commit and push exact source changes to TOS main

Return contract:
```
PATCH=RAMZY-SMART-TASK-V3-LIVE-QA-R5
PASS/FAIL=
PROJECT_FILTER=PASS/FAIL
ASSIGNEES_500=PASS/FAIL
AI_TITLE=PASS/FAIL
AI_DESCRIPTION=PASS/FAIL
ONBOARDING=PASS/FAIL
FRONTEND_BUILD=PASS/FAIL
BACKEND_TEST=PASS/FAIL
LIVE_DEPLOY=PASS/FAIL
COMMIT=
PUSH=YES/NO
ERROR=
```
