# PATCH — RAMZY SMART TASK R5.13
# Daily Smart-Task Awareness Bubble + Custom Date/Time UX + Stronger Writing Intelligence

Baseline TOS:
`8b593df76498c31f2da8fb86ce4fa32459a359f1`

This patch supersedes the unimplemented R5.12 date-picker patch.

Goal:
1. Teach eligible users ONE feature only: creating a Smart Task with Ramzy.
2. Replace ugly native Start Date / Reminder Time browser pickers and eliminate 1970.
3. Make Title/Description AI improvements visibly more useful by using the context that already exists more effectively.

Keep scope tight. No DB migration.

---

## A) DAILY SMART-TASK AWARENESS BUBBLE

Current problem:
The existing thought bubble uses:
`tos.ramzy.smart-task-thought-bubble.v4.<userId>`
and permanently dismisses after the first display/auto-timeout.

Replace this with a daily awareness lifecycle.

### Eligibility
Show only when:
- Ramzy is allowed for the user
- `permissions.actions.CREATE_TASK === true`
- `executionControl.globalExecutionAllowed === true`
- no Smart Task is currently open
- onboarding not completed
- it has not already shown today
- shown on fewer than 10 distinct local calendar days

### Frequency
- Once per local calendar day.
- Maximum 10 shown days.
- Start counting from the first eligible display.
- Use per-user localStorage; no DB migration.

Suggested key:
`tos.ramzy.smart-task-awareness.v1.<userId>`

Suggested data:
```json
{
  "firstShownDate": "YYYY-MM-DD",
  "lastShownDate": "YYYY-MM-DD",
  "shownDays": 3,
  "completed": false
}
```

Do not use a 24-hour timer. Use local calendar date.

### Timing / content
- Wait ~2 seconds after eligibility is known.
- Show the existing premium thought-cloud visual beside Ramzy.
- ONE feature only. Do not rotate through unrelated Ramzy capabilities.

Copy:

AR first state:
`أقدر أساعدك تعمل مهمة ذكية ✨`

AR second state after ~2 seconds:
`اضغط هنا وخلي رمزي يجهز المهمة معاك: العنوان، المشروع، الموعد، الأولوية والمنفذ.`

CTA:
`جرّب مهمة ذكية`

EN:
`I can help you create a Smart Task ✨`
then
`Tap here and Ramzy will guide you through the title, project, due date, priority, and assignee.`
CTA:
`Try a Smart Task`

No long tutorial and no multi-feature carousel.

### Click behavior
Clicking the bubble must:
- open Ramzy
- directly launch the existing Smart Task builder
- do NOT merely insert text and leave the user wondering what to send
- reuse existing permission-aware `startSmartTask()` path
- keep project/permission logic unchanged

### Dismiss behavior
- X / auto-hide = hide for TODAY only.
- It may appear again tomorrow.
- Showing it counts as one shown day.
- Clicking it does NOT permanently complete onboarding unless Smart Task use succeeds.

### Completion
After a successful Smart Task proposal is created through:
`api.agent.createTaskProposal(...)`
mark:
`completed=true`

After completion, never show this awareness bubble again for that user/browser.

Do not mark complete on:
- opening Ramzy
- clicking the bubble
- opening Smart Task
- cancelling Smart Task
- failed proposal

If shownDays reaches 10 without completion, stop showing.

Do not interfere with the normal Ramzy launcher/greeting.

---

## B) CUSTOM START DATE + REMINDER PICKERS

Replace ONLY the Smart Task advanced-detail controls:
- Start Date
- Reminder Time

Do NOT redesign the Due Date preset chips.

### Fix epoch bug
In `frontend/src/lib/smartTaskDueDate.js`:

`smartTaskLocalDateValue(value)`
and
`smartTaskLocalDateTimeValue(value)`

must return `""` immediately for:
- null
- undefined
- empty string

Never call `new Date(null)` for an empty Smart Task value.

Regression:
empty Start Date / Reminder must never render 1970.

### Start Date
Replace native `<input type="date">` with a custom compact TOS picker:
- custom trigger
- localized selected value
- empty placeholder
- calendar icon
- month/year header
- previous/next month
- 7-column day grid
- selected day
- today indicator
- Today / Clear / Done
- outside click + Escape
- light/dark
- AR/EN
- responsive

Empty picker opens on CURRENT month, never 1970.

Keep existing conversion:
`smartTaskStartDateIso(localYYYYMMDD)`

### Reminder Time
Replace native `<input type="datetime-local">` with custom:
- same date calendar
- hour 01–12
- minutes 00/05/10...55
- AM/PM segmented selector
- Now / Clear / Done
- localized closed-field display
- outside click + Escape
- light/dark
- AR/EN
- responsive

Empty reminder opens with current local date and the next sensible 5-minute time.

Keep conversion:
`smartTaskLocalDateTimeIso(localYYYYMMDDTHH:mm)`

Preserve all existing validation:
- future reminder
- reminder <= due date
- start date <= due date

Draft selection must not commit on outside-close/Escape.
Done commits.
Clear clears.

No new date library/package.

Style in existing TOS cream/champagne/warm-gold design.
Popover must stay compact and inside/anchored to Ramzy; no full-screen native popup.

---

## C) MAKE TITLE / DESCRIPTION AI FEEL ACTUALLY SMARTER

Current implementation already has useful context:
- selected project
- client
- project description
- requirements
- acceptance criteria
- user's recent task style in the selected project
- recent project task examples
- relevance/recency ranking

Do NOT replace this system.
Improve how it is used.

### 1. Use currently fetched project type
`getSmartTaskWritingContext()` already fetches:
- `type`
- `projectType`

but `formatWritingContextForPrompt()` does not include them.

Add them to the prompt context when present:
- Type
- Project type

### 2. Stronger title behavior
Update `taskTitlePrompt()` so Improve/Write does more than synonym rewriting.

Require:
- concise action-oriented title
- when supported by user/project context, prefer:
  `action + deliverable/outcome + useful project/domain qualifier`
- remove vague filler
- preserve exact user intent
- use project terminology when relevant
- follow the user's recent task naming style when it helps
- do NOT invent people, dates, priority, IDs, credentials, or unsupported facts
- output title only

If the original is already strong, improve minimally rather than rewriting for no reason.

### 3. Stronger description behavior
Update `taskDescriptionPrompt()` to produce a concise useful work description, not a paraphrase of the title.

When supported by known context:
- what needs to be done
- expected deliverable/result
- relevant project/client/domain context
- relevant known requirement

Rules:
- 2–4 concise sentences or compact lines
- do not invent requirements or acceptance criteria
- do not infer assignee/date/priority
- do not copy historical examples verbatim
- current user input remains highest priority
- output description only

### 4. Sparse-input behavior
When input is vague/short and a project IS selected:
- use project context + ranked examples to make the result meaningfully more specific
- only use facts actually present in allowed project context
- no hallucinated details

When no project is selected:
- continue to work from typed content only
- do not pretend project context exists

### 5. Visible context hint
Near the Title/Description AI buttons, when project writing context is loaded, show one subtle compact indicator:

EN:
`Using project context + task style`

AR:
`يستخدم سياق المشروع + أسلوب مهامك`

When no project is selected:
EN:
`Select a project for smarter suggestions`
AR:
`اختر مشروعًا لاقتراحات أذكى`

This is informational only.
Do not block the AI buttons.

### 6. No extra AI call
Do NOT add another model call just to create context.
Reuse existing writing context / ranking.
Keep current provider/model/settings.
Keep cost/latency low.

---

## D) SECURITY / EXISTING BEHAVIOR

Preserve:
- Ramzy granular permissions
- native TOS RBAC
- project/workspace scope
- approvals
- provider/model
- Smart Task proposal payload
- project picker
- assignee picker
- Due Date preset chips
- priority behavior
- input-language detection
- writing memory/context security filters
- secret filtering
- archived-project behavior

No DB/schema migration.

---

## E) TESTS

Focused only.

Bubble:
1. eligible user gets bubble after ~2s
2. max once per local day
3. appears on following day if not completed
4. stops after 10 shown days
5. click opens Smart Task directly
6. X/auto-hide does not permanently complete
7. successful proposal marks complete
8. completed user never sees it again
9. user without CREATE_TASK never sees it

Date/time:
10. null/undefined/"" never becomes 1970
11. no native date/datetime input for Smart Task Start Date/Reminder
12. date round-trip
13. noon/midnight AM-PM
14. Clear/Done/Escape/outside
15. dark + AR/EN basic rendering

Writing:
16. Type/projectType appear in writing context when present
17. prompts require stronger action/deliverable behavior
18. no new model call
19. existing Smart Task writing/project-scope tests pass

Run frontend build + relevant backend tests.

Live QA:
- daily bubble visual/click flow
- custom Start Date
- custom Reminder
- Title Improve with selected project
- Description Write/Improve with selected project
- AR + EN
- no 1970

Deploy changed frontend/backend only.
Commit + push.

---

## RETURN ONLY

```
PATCH=RAMZY-SMART-TASK-R5.13
PASS/FAIL=
DAILY_BUBBLE=PASS/FAIL
ONCE_PER_DAY=PASS/FAIL
TEN_DAY_LIMIT=PASS/FAIL
BUBBLE_DIRECT_SMART_TASK=PASS/FAIL
COMPLETION_STOP=PASS/FAIL
EPOCH_1970_FIX=PASS/FAIL
START_DATE_PICKER=PASS/FAIL
REMINDER_PICKER=PASS/FAIL
NO_NATIVE_PICKERS=PASS/FAIL
WRITING_CONTEXT_UPGRADE=PASS/FAIL
TITLE_AI_UPGRADE=PASS/FAIL
DESCRIPTION_AI_UPGRADE=PASS/FAIL
NO_EXTRA_MODEL_CALL=PASS/FAIL
RBAC_PRESERVED=PASS/FAIL
BACKEND_TEST=PASS/FAIL
FRONTEND_BUILD=PASS/FAIL
LIVE_QA=PASS/FAIL
LIVE_DEPLOY=PASS/FAIL
DB_MIGRATION=NO
COMMIT=
PUSH=YES/NO
ERROR=
```
