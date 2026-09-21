# PATCH — RAMZY SMART TASK R5.15
# Stronger Title + Description AI Writing

Baseline TOS:
`d26372aec910ded8941f5227994c985dd5623b7f`

Scope: Title/Description writing intelligence only.
Do NOT touch daily bubble, date/time pickers, provider/model, permissions, DB, or Smart Task payload flow.

## Goal
Make Ramzy Title/Description suggestions feel meaningfully smarter, not like simple rewriting.

## Existing context to keep and reuse
Current Smart Task writing context already includes:
- project name
- client
- project description
- requirements
- acceptance criteria
- user's recent task examples in the project
- recent project task examples
- relevance/recency ranking

Do NOT replace this system and do NOT add another AI/model call.

## 1) Use all already-fetched project metadata
`getSmartTaskWritingContext()` already fetches:
- `type`
- `projectType`

Add them to `formatWritingContextForPrompt()` when present.

## 2) Stronger Title behavior
Update `taskTitlePrompt()`.

Requirements:
- concise and action-oriented
- when supported by context, prefer:
  `action + deliverable/outcome + useful domain/project qualifier`
- use project terminology when relevant
- use the user's recent task naming style only as style guidance
- remove vague filler
- preserve exact user intent
- if current title is already strong, improve minimally
- never invent people, dates, priority, IDs, credentials, requirements, or unsupported facts
- output title only

Examples of desired improvement:
- weak: `landing page`
- better when context supports it: `Build campaign landing page for lead capture`

Do not hardcode example content into output.

## 3) Stronger Description behavior
Update `taskDescriptionPrompt()`.

Description should add useful execution clarity, not just paraphrase the title.

When supported by known context, include:
- what needs to be done
- expected deliverable/result
- relevant project/client/domain context
- relevant known requirement

Rules:
- 2–4 concise sentences or compact lines
- current user input is highest priority
- no invented requirement/acceptance criteria
- no inferred assignee/date/priority
- do not copy historical examples verbatim
- output description only

## 4) Sparse input
If user input is short/vague AND a project is selected:
- use allowed project context + ranked examples to make suggestion more specific
- only use facts actually present in context

If no project selected:
- continue using typed content only
- do not fabricate project context

## 5) Small UX hint
Near the Title/Description AI controls show a subtle compact hint.

When project writing context is loaded:
EN: `Using project context + task style`
AR: `يستخدم سياق المشروع + أسلوب مهامك`

When no project selected:
EN: `Select a project for smarter suggestions`
AR: `اختر مشروعًا لاقتراحات أذكى`

Informational only. Do not disable AI buttons.

## Preserve
- current provider/model/settings
- one model call per title/description request
- input-language detection
- project/workspace/Ramzy RBAC
- secret filtering
- project example visibility scope
- existing endpoints and response shape
- R5.14 daily bubble
- R5.13B date/time pickers

No DB migration.

## Focused verification
1. `type` / `projectType` appear in writing context when present
2. weak title + selected project produces more task-specific result
3. description is useful execution context, not title paraphrase
4. vague input uses only real allowed project facts
5. no-project case still works
6. no extra model call
7. AR + EN
8. backend relevant tests pass
9. frontend build passes
10. live smoke for Title Improve + Description Write/Improve

Deploy changed frontend/backend only.
Commit locally.
User handles push through TOS system if server GitHub auth is unavailable.

Return ONLY:
```
PATCH=RAMZY-SMART-TASK-R5.15-WRITING-INTELLIGENCE
PASS/FAIL=
PROJECT_METADATA_CONTEXT=
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
