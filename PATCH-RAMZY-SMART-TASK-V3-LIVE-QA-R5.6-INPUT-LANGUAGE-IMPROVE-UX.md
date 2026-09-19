# Ramzy Smart Task V3 — Live QA R5.6: Input-Language AI + Clear Improve UX

Baseline TOS:
`85ddc87f691637ffd95a5ae4c269e15dad5eb59a`

IMPORTANT:
This patch SUPERSEDES and REPLACES the unimplemented patch:
`PATCH-RAMZY-SMART-TASK-V3-LIVE-QA-R5.5-UI-LANGUAGE-AI.md`

Do NOT implement the R5.5 UI-language rule.
The AI language must follow the language the USER TYPES, not the TOS interface language.

Scope ONLY:
1. Make Title AI output follow the language the user started typing in.
2. Make Description AI output follow the language the user started typing in.
3. Make Write/Improve actions visually obvious as clickable buttons.
4. Clarify Write vs Improve behavior and labels.
5. Do NOT touch projects, assignees, feature tip, task approval, task creation, or permissions.

## 1) Canonical language rule — INPUT language, not UI language

Do NOT use `isEnglish` as the source of truth for AI output language.

Detect the language from the user's typed task content.

Required field logic:

### Title AI
- If Title already contains user text:
  - detect/remember the language the user STARTED the Title in
  - Improve Title must return that language
- If Title is empty and Description has user text:
  - Write Title uses the Description's detected input language
- If both are empty:
  - no AI call; show inline guidance

### Description AI
- If Description already contains user text:
  - detect/remember the language the user STARTED the Description in
  - Improve Description must return that language
- If Description is empty and Title has user text:
  - Write Description uses the Title's detected input language
- If both are empty:
  - no AI call; show inline guidance

### Detection
Implement a small deterministic frontend helper, e.g. `detectSmartTaskInputLanguage(text)`.

Ignore digits, punctuation, whitespace, emoji, URLs until a meaningful alphabetic script is found.

- first meaningful Arabic letter => `ar`
- first meaningful Latin letter => `en`

"Started in" means the first meaningful script the user typed for that field, not whichever language later becomes the majority.

Prefer storing the detected language per draft field:
- titleInputLanguage
- descriptionInputLanguage

Rules:
- set it when the field first gets meaningful typed text
- do not flip it later just because brand/technical words from another language appear
- if the user fully clears that field, reset that field's detected language so new typing can establish a new language
- fallback only when no meaningful language can be detected: use the other field's detected language; if still unavailable, use current UI language as last fallback

Examples:
- Title starts `تصميم landing page جديد` => output Arabic
- Title starts `Create بوست رمضان` => output English
- Description starts Arabic while title is English => Improve Description stays Arabic
- Empty Description + Arabic Title => Write Description returns Arabic

Frontend sends the detected language to the existing AI endpoints:
`language: "ar" | "en"`

Backend must obey that requested language. Harden the existing title/description prompts enough to say the requested language is based on the user's typed content and must be used for normal prose. Brand names, URLs, acronyms, technical identifiers, and proper nouns may remain unchanged.

Do NOT infer language again from UI on backend.

## 2) Exact Write vs Improve behavior

The action mode depends on whether the TARGET field already has meaningful content.

### Title
If Title is empty:
- label EN: `Write Title with Ramzy`
- label AR UI: `اكتب العنوان مع رمزي`
- use Description as context if available
- generate a concise title

If Title has content:
- label EN: `Improve Title with Ramzy`
- label AR UI: `حسّن العنوان مع رمزي`
- improve the EXISTING title
- preserve intent/meaning
- make it clearer, more professional, concise
- do not invent task facts

### Description
If Description is empty:
- label EN: `Write Description with Ramzy`
- label AR UI: `اكتب الوصف مع رمزي`
- use Title as context if available
- generate a useful concise description

If Description has content:
- label EN EXACTLY: `Improve Description with Ramzy`
- label AR UI: `حسّن الوصف مع رمزي`
- improve the EXISTING description
- preserve meaning and concrete facts
- improve clarity, wording, structure, readability
- do not silently turn it into a different task
- do not invent assignee, deadline, priority, acceptance criteria, or unsupported facts

The field value must remain editable after AI response.
Never auto-save/create the task.

## 3) Make the AI buttons obviously clickable

Current controls look too much like static text.

Restructure the Title and Description AI actions into clear action rows/buttons.

Required:
- visible button border
- visible light background/tint
- Sparkles icon
- pointer cursor
- clear hover state
- clear active/pressed state
- keyboard focus-visible state
- dark mode equivalent
- button text fully readable; do not shorten Description action to generic `Improve with Ramzy`
- keep within Ramzy panel, no horizontal overflow

Recommended:
- action button below the field or clearly attached to it
- compact SaaS button, not a tiny ghost text link

Do NOT disable because Project is not selected.
Only disable while that same AI request is in progress.

If both Title and Description are empty, button stays clickable and returns visible inline guidance rather than silently doing nothing.

## 4) Loading feedback

For Title:
- write mode: `Ramzy is writing the title...` / `رمزي بيكتب العنوان...`
- improve mode: `Ramzy is improving the title...` / `رمزي بيحسّن العنوان...`

For Description:
- write mode: `Ramzy is writing the description...` / `رمزي بيكتب الوصف...`
- improve mode: `Ramzy is improving the description...` / `رمزي بيحسّن الوصف...`

Spinner visible.
No duplicate request while loading.

## 5) Backend prompt semantics

Keep the SAME configured Ramzy provider/model/API.

Update `taskTitlePrompt` and `taskDescriptionPrompt` so mode is explicit:
- WRITE when target field empty
- IMPROVE when target field has content

For IMPROVE:
- preserve original intent and factual content
- improve language/clarity only
- output in the detected input language supplied by frontend

For WRITE:
- create the missing target field using the other field as context
- output in the detected input language supplied by frontend

You may pass an explicit `mode: "write" | "improve"` to the existing endpoints/services if useful.

No new provider.
No new API key.
No task-side effects.

## 6) Do NOT touch

- project picker/status/filter/archive
- assignee endpoint or recommendation
- feature-tip behavior
- approval flow
- task creation payload
- permissions
- Ramzy chat/voice
- unrelated CSS/API methods

## 7) Regression tests

Add focused tests proving:
1. Arabic-started Title => Title AI language `ar`.
2. English-started Title => Title AI language `en`.
3. Arabic-started Description => Description AI language `ar`.
4. English-started Description => Description AI language `en`.
5. Mixed text does not flip after the field's starting language is captured.
6. Clearing a field resets its captured language.
7. Empty Title falls back to Description language.
8. Empty Description falls back to Title language.
9. Labels are EXACT:
   - Write Title with Ramzy
   - Improve Title with Ramzy
   - Write Description with Ramzy
   - Improve Description with Ramzy
10. AI buttons remain clickable without project selection.
11. Buttons show visible loading state.
12. Same configured Ramzy model path remains unchanged.
13. Projects and assignees code unchanged.

## Verify

- `npm --prefix frontend run build`
- `npm --prefix backend run test:ramzy`
- backend reload only if backend source changed
- atomic frontend deploy
- live smoke:
  - Arabic typed Title -> Arabic title suggestion
  - English typed Title -> English title suggestion
  - Arabic typed Description -> Arabic improved description
  - English typed Description -> English improved description
- commit + push exact changes to TOS main

Return only:
```
PATCH=RAMZY-SMART-TASK-V3-LIVE-QA-R5.6
PASS/FAIL=
INPUT_LANGUAGE_TITLE=PASS/FAIL
INPUT_LANGUAGE_DESCRIPTION=PASS/FAIL
WRITE_IMPROVE_LOGIC=PASS/FAIL
BUTTON_UX=PASS/FAIL
TITLE_LABELS=PASS/FAIL
DESCRIPTION_LABELS=PASS/FAIL
PROJECT_REQUIRED_FOR_AI=NO
PROVIDER_UNCHANGED=PASS/FAIL
ASSIGNEES_UNCHANGED=PASS/FAIL
PROJECT_PICKER_UNCHANGED=PASS/FAIL
FRONTEND_BUILD=PASS/FAIL
BACKEND_TEST=PASS/FAIL
LIVE_DEPLOY=PASS/FAIL
COMMIT=
PUSH=YES/NO
ERROR=
```
