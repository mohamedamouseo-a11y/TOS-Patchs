# PATCH — RAMZY SMART TASK R5.13C
# Stronger Title + Description Writing Intelligence

Baseline TOS:
`8b593df76498c31f2da8fb86ce4fa32459a359f1`

Scope: AI writing quality only.
No bubble work. No date-picker work. No provider/model change. No extra model call. No DB change.

Current writing context already includes:
- project name/client
- description
- requirements
- acceptance criteria
- recent personal task style
- recent project task examples
- ranking by relevance/recency

Improve use of existing context only.

1) In `ramzySmartTaskContext.service.js`:
`getSmartTaskWritingContext()` already fetches `type` and `projectType`.
Include both in `formatWritingContextForPrompt()` when present.

2) Strengthen `taskTitlePrompt()`:
- concise, action-oriented
- prefer action + deliverable/outcome + useful project/domain qualifier when supported
- use project terminology and user's recent naming style when relevant
- preserve user intent
- improve minimally if title is already good
- never invent people/dates/priority/IDs/credentials/unsupported facts
- output title only

3) Strengthen `taskDescriptionPrompt()`:
- produce useful work description, not title paraphrase
- when supported: what to do + expected deliverable/result + relevant known project/client context + known requirement
- 2–4 concise sentences/lines
- do not invent acceptance criteria/requirements
- do not infer assignee/date/priority
- do not copy historical examples verbatim
- current user input highest priority
- output description only

4) Sparse input:
- with project selected, use allowed project context/examples to add useful specificity
- without project, use typed input only

5) Frontend informational hint beside writing AI controls:
with project context:
EN `Using project context + task style`
AR `يستخدم سياق المشروع + أسلوب مهامك`

without project:
EN `Select a project for smarter suggestions`
AR `اختر مشروعًا لاقتراحات أذكى`

Hint must not block buttons.

6) Preserve:
- current provider/model
- one model call per title/description request
- permissions/scope
- secret filtering
- language detection
- existing endpoints

Tests:
- type/projectType included when present
- title prompt stronger contract
- description prompt stronger contract
- no extra model call
- project scope tests unchanged
- backend tests + frontend build

Live smoke:
- improve weak title with project selected
- write/improve description with project selected
- verify result uses real project context without invented facts
- AR + EN

Deploy changed backend/frontend, commit + push.

Return ONLY:
```
PATCH=RAMZY-SMART-TASK-R5.13C-WRITING
PASS/FAIL=
PROJECT_CONTEXT=
TITLE_AI=
DESCRIPTION_AI=
SPARSE_INPUT=
CONTEXT_HINT=
NO_EXTRA_MODEL_CALL=
RBAC_PRESERVED=
BACKEND_TEST=
FRONTEND_BUILD=
LIVE_QA=
LIVE_DEPLOY=
COMMIT=
PUSH=
ERROR=
```
