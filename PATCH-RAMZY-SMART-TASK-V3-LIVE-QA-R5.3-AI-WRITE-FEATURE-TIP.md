# Ramzy Smart Task V3 — Live QA R5.3: Make AI Write Actions Interactive + New Feature Tip

Baseline TOS (latest pushed version):
`3cf6fe9c30aa434e7d3921a10b38a77b640ec4cd`

Scope ONLY:
1. Fix Smart Task "Write title / Improve title" so it actually reacts and uses Ramzy AI.
2. Fix Smart Task "Write with Ramzy / Improve with Ramzy" for Description so it actually reacts and uses Ramzy AI.
3. Replace the current persistent first-use onboarding card with a lightweight temporary "new capability" tip.
4. Do NOT touch project picker, assignees, task approval, permissions, or unrelated Ramzy behavior.

## Confirmed current UX defect

Current frontend disables the AI buttons behind hard prerequisites:
- Title button requires a selected project AND title/description.
- Description button requires a selected project AND title.

This makes the controls feel static/dead before those fields are satisfied.

Current backend also requires `projectId` for both AI-writing endpoints, even though writing a title/description does not inherently require a project.

## A) AI Title — must feel alive

Keep using Ramzy's EXISTING configured AI provider/model:
`getAgentRuntimeSettings() -> createMastraModel(settings)`

Do not add a provider/key.

Required:
- Button remains clickable whenever it is not currently loading.
- It MUST NOT require project selection.
- Input sources:
  - rough title => improve it
  - description only => generate a concise title
  - title + description => improve using both
- If BOTH title and description are empty:
  - do not call AI
  - show a small inline helper/error immediately:
    Arabic: `اكتب فكرة بسيطة في العنوان أو الوصف الأول.`
    English equivalent.
  - button still gives visible click feedback; never silently no-op.
- While calling AI:
  - spinner
  - label Arabic: `رمزي بيكتب...`
  - English: `Ramzy is writing...`
  - prevent duplicate requests only while loading
- Success replaces ONLY the title field.
- User can still edit it afterward.
- Never auto-save/create the task.
- Max 180 chars.
- No invented assignee/deadline/priority/facts.

## B) AI Description — must feel alive

Same interaction rules:
- MUST NOT require project selection.
- Button clickable whenever not loading.
- Sources:
  - title only => generate useful concise description
  - existing description => improve it
  - title + description => improve using both
- If title and description are both empty:
  - show immediate inline helper:
    Arabic: `اكتب عنوان أو فكرة بسيطة الأول علشان رمزي يقدر يساعدك.`
    English equivalent.
  - no silent return.
- During request show spinner + `رمزي بيكتب...`.
- Success updates ONLY Description.
- Max 4000 chars.
- No auto-save/create.

## C) Backend AI endpoints — project context optional

For:
- `POST /api/agent/task-create/suggest-title`
- `POST /api/agent/task-create/suggest-description`

Change `projectId` from REQUIRED to OPTIONAL.

Rules:
- Still require normal Ramzy execution access.
- If `projectId` is provided:
  - run existing `assertAgentTaskCreateAccess` before using any project context.
- If no `projectId`:
  - AI writing is allowed using only the supplied title/description.
- Keep existing runtime model/provider configuration exactly.
- Do not widen task creation permissions.
- These endpoints generate text only; they do not create tasks.

Frontend should send:
`projectId: smartTask.project?.id || null`

Do not disable the AI actions merely because project is not selected.

## D) Replace current onboarding card with a temporary "new feature" tip

The current implementation is a persistent card shown in the empty Ramzy welcome state until dismissed. Replace it.

Goal:
Let existing daily Ramzy users notice that task creation is a NEW capability without annoying them.

Required UX:
- Small speech-bubble / cloud / toast visually associated with Ramzy.
- Non-blocking.
- Can appear near the Ramzy launcher or inside the panel header/welcome area, whichever is cleaner and stable.
- Copy example:
  Arabic:
  `جديد ✨ تقدر تطلب مني أعمل لك مهمة، وأنا هساعدك تجهزها خطوة بخطوة.`
  English equivalent.
- Optional small CTA:
  `جرّب إنشاء مهمة`
  which opens the EXISTING Smart Task flow.
- Auto-hide after about 6 seconds.
- User can dismiss earlier.
- Show once per user PER FEATURE VERSION using a new versioned key, e.g.:
  `tos.ramzy.smart-task-feature-tip.v2.<userId>`
- Mark seen on auto-hide, dismiss, or CTA.
- This is NOT "first time user opens Ramzy"; it is a one-time new-feature announcement for current users.
- Only show when `status.executionControl.canExecute === true`.
- Do not require empty conversation/history.
- Do not block chat, composer, or Smart Task.
- If Ramzy is already open, show unobtrusively; if collapsed, a small launcher-adjacent bubble is acceptable.
- Light/dark responsive styling.
- No modal.

## E) Do NOT touch
- project filters/status logic
- archived behavior
- assignee endpoint/list/recommendation
- approval workflow
- task creation payload
- project/user permissions
- AI provider/model settings
- unrelated Ramzy chat/voice behavior

## Files to inspect
- `frontend/src/components/RamzyAssistant.jsx`
- `frontend/src/components/ramzySmartTaskComposerV1.css`
- `frontend/src/lib/api.js`
- `backend/src/routes/agent.routes.js`
- `backend/src/agency-operator/services/ramzyAi.service.js`
- `backend/src/agency-operator/services/ramzySmartTask.service.js`
- existing Ramzy tests

## Regression coverage

Add focused tests proving:
1. Title AI does not require projectId.
2. Description AI does not require projectId.
3. Empty title+description produces visible UI guidance, not silent no-op.
4. During AI request the control shows loading state and cannot duplicate-submit.
5. Existing configured Ramzy model path remains used.
6. Feature tip uses new versioned per-user key, auto-hides, and is not gated by empty message history.
7. Project picker and assignee code are unchanged by this patch.

## Verify
- `npm --prefix frontend run build`
- `npm --prefix backend run test:ramzy`
- backend restart/reload because routes change
- authenticated live smoke:
  - suggest-title without projectId => success with valid title/description input
  - suggest-description without projectId => success with valid input
- deploy using existing safe/atomic process
- commit + push exact changes to TOS main

Return only:
```
PATCH=RAMZY-SMART-TASK-V3-LIVE-QA-R5.3
PASS/FAIL=
AI_TITLE_INTERACTIVE=PASS/FAIL
AI_DESCRIPTION_INTERACTIVE=PASS/FAIL
TITLE_API_NO_PROJECT=<status>
DESCRIPTION_API_NO_PROJECT=<status>
FEATURE_TIP=PASS/FAIL
FEATURE_TIP_AUTOHIDE=PASS/FAIL
ASSIGNEES_UNCHANGED=PASS/FAIL
PROJECT_PICKER_UNCHANGED=PASS/FAIL
FRONTEND_BUILD=PASS/FAIL
BACKEND_TEST=PASS/FAIL
LIVE_DEPLOY=PASS/FAIL
COMMIT=
PUSH=YES/NO
ERROR=
```
