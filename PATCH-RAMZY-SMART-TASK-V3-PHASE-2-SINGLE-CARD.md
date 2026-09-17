# PATCH-RAMZY-SMART-TASK-V3-PHASE-2-SINGLE-CARD

## Baseline
TOS main baseline: `9a799960f4946e3aba9e8fdcc80458d907a3e1b9`

## Goal
Replace the current linear 5-step Smart Task wizard inside Ramzy with one compact professional task-creation card inside the chat.

This phase is UX/state restructuring only. Preserve current permission, project, assignee, approval and task-creation behavior.

## Current flow to replace
`TITLE -> PROJECT -> DUE -> PRIORITY -> ASSIGNEE -> REVIEW`

Current UI has `Step X of 5`, progress bars and forces the user through separate screens.

## New Phase 2 flow
When the canonical CREATE_TASK intent from Phase 1 opens Smart Task, render ONE card containing all current core fields:

1. Task title — required
2. Description — optional
3. Project — required using the existing project picker/search behavior
4. Due date — required choice, including existing `NONE`
5. Priority — required choice, including existing `AUTO`
6. Assignee — required choice, including existing `AUTO` and `NONE`

No sequential steps. The user can edit/change any field without losing the rest of the draft.

## Card design
Header:
- Arabic: `إنشاء مهمة`
- English: `Create task`
- Small helper: `كمّل البيانات الأساسية ثم راجع المهمة`
- Close/cancel button
- Remove `Step X of 5`
- Remove the 5-segment progress bar

Body:

### Title
- Dedicated input inside the card, not the main Ramzy composer.
- If Phase 1 intent parser already extracted a title, prefill it.
- If title is empty, focus this input when practical.
- Required.
- Max length should remain compatible with current backend; UI may cap at 500 chars.

### Description
- Optional compact textarea inside the card.
- Placeholder: `اكتب وصفًا مختصرًا للمهمة — اختياري`
- Preserve line breaks.
- Max length <= backend CREATE_TASK limit (10,000); recommended UI max 4,000.
- Do NOT add AI generation/suggestion yet; that belongs to a later phase.

### Project
Reuse the existing `TOS_SMART_TASK_PROJECT_PICKER_V2` search UI and current data source.

Compact behavior:
- Before selection: show project search/picker.
- After selection: collapse picker to a selected-project row/chip with `تغيير` / `Change`.
- Clicking Change reopens picker without clearing title, description, due, priority or assignee.
- Keep current AUTO project option in Phase 2.

DO NOT implement Phase 3 permission-aware project filtering here.
DO NOT change project RBAC here.

### Due date
Render existing choices inline as compact selectable chips:
- TODAY
- TOMORROW
- IN_2_DAYS
- IN_1_WEEK
- NONE

Selected choice must have a clear selected state.
Changing it must not move the user to another step.

### Priority
Render existing choices inline as compact selectable chips:
- HIGH
- MEDIUM
- LOW
- AUTO

Selected choice must have a clear selected state.

### Assignee
For Phase 2, keep the CURRENT assignee data source and semantics.

Render compactly, preferably as a select/combobox or compact picker so the card does not become a wall of chips.
Must preserve:
- AUTO (`خلي رمزي يقترح الأنسب`)
- NONE (`بدون تحديد`)
- existing user options

DO NOT implement Phase 4 permission-aware assignee filtering or smart ranking yet.

## Footer / readiness
The card footer should show a compact readiness state.

Submit button:
- Arabic: `مراجعة وإنشاء`
- English: `Review & create`
- disabled until all required current fields are selected:
  - non-empty title
  - project object selected (including current AUTO semantics)
  - dueKind selected
  - priority selected
  - assignee object selected (including AUTO/NONE)

Description is optional.

If incomplete, make missing fields visually understandable without noisy error messages.

## State changes
Refactor Smart Task state away from wizard navigation.

Expected draft shape should remain conceptually similar to:

```js
{
  title: "",
  description: "",
  project: null,
  dueKind: "",
  dueDate: null,
  priority: "",
  assignee: null,
}
```

A temporary UI-only picker state is fine, but do not keep sequential business steps as the interaction model.

Remove or stop using obsolete wizard-only helpers where no longer needed:
- `smartTaskStepNumber`
- `captureSmartTaskTitle`
- transitions such as `step: "DUE"`, `step: "PRIORITY"`, `step: "ASSIGNEE"`, `step: "REVIEW"`

Do not remove unrelated Ramzy logic.

## Main composer behavior
While Smart Task card is open:
- task title is edited inside the card
- do not use the main chat composer as the title field
- keep the normal Ramzy composer visible to avoid layout jump
- disable message sending while the Smart Task card is active, or otherwise prevent ambiguous simultaneous chat + draft editing
- use a concise placeholder such as `أكمل بيانات المهمة في البطاقة أعلاه`

Closing/cancelling the card returns the composer to normal behavior.

## Submission behavior — preserve for Phase 2
Do NOT implement Phase 7 structured direct submission yet.

Keep the existing `submitSmartTask()` -> `sendMessage(... metadata.intent=CREATE_TASK)` approval path.

Update `smartTaskPrompt()` only as needed to include the optional description:
- if description is non-empty, include it clearly
- if empty, omit it or state no description

Preserve exact project ID / assignee ID behavior already present.
Preserve the current approval requirement.
No auto-create.

## Strict non-goals
Do NOT change:
- Phase 1 canonical CREATE_TASK intent parser
- `ramzy.execute_actions`
- `assertRamzyActionExecutionAllowed()`
- `assertAgentTaskCreateAccess()`
- project/workspace/board RBAC
- project visibility logic
- assignee authorization logic
- backend task creation business logic
- approval flow
- AI provider/model
- project API
- users API

Do NOT implement yet:
- Phase 3 permission-aware Project Picker
- Phase 4 Smart Assignee Picker
- Phase 5 AI description generation / workload suggestions / smarter quick details
- Phase 6 optional advanced details
- Phase 7 structured direct draft submission

## UX requirements
- One card only; no step screens.
- Compact enough for the Ramzy panel.
- No horizontal scroll.
- Internal project results may scroll.
- Long project/user names must truncate safely.
- Light and dark mode compatible.
- Arabic RTL and English LTR compatible.
- Preserve current card if project/due/priority/assignee is changed.
- Do not clear previously entered fields accidentally.

## Files expected
Primary:
- `frontend/src/components/RamzyAssistant.jsx`
- `frontend/src/components/ramzySmartTaskComposerV1.css`

Avoid backend changes in Phase 2.

## Verification for this phase
Per current workflow, do SOURCE/BUILD verification now; full authenticated visual/runtime QA will be done after all phases are complete.

Required now:
- inspect baseline before modifying
- timestamped backup outside repo
- frontend build PASS
- no backend changes
- deploy via current atomic deployment flow
- commit + push main
- clean worktree

Do NOT spend time on screenshots/browser visual QA in this phase.

## Return contract

```text
PATCH=RAMZY-SMART-TASK-V3-PHASE-2-SINGLE-CARD
PASS/FAIL=<result>
BASELINE_COMMIT=9a79996
PHASE2_NEW_COMMIT=<sha>
SINGLE_CARD_UI=YES/NO
WIZARD_STEP_UI_REMOVED=YES/NO
TITLE_INSIDE_CARD=YES/NO
DESCRIPTION_FIELD=YES/NO
PROJECT_PICKER_REUSED=YES/NO
PROJECT_CHANGE_PRESERVES_DRAFT=YES/NO
DUE_INLINE_SELECTION=YES/NO
PRIORITY_INLINE_SELECTION=YES/NO
ASSIGNEE_COMPACT_PICKER=YES/NO
ALL_FIELDS_EDITABLE_WITHOUT_STEP_NAV=YES/NO
SUBMIT_DISABLED_UNTIL_REQUIRED_FIELDS=YES/NO
DESCRIPTION_INCLUDED_IN_PROMPT=YES/NO
MAIN_COMPOSER_NOT_USED_FOR_TITLE=YES/NO
PHASE1_INTENT_CHANGED=NO
PROJECT_RBAC_CHANGED=NO
ASSIGNEE_RBAC_CHANGED=NO
APPROVAL_LOGIC_CHANGED=NO
BACKEND_CHANGED=NO
FRONTEND_BUILD=PASS/FAIL
LIVE_DEPLOY=PASS/FAIL
PUSH=YES/NO
WORKTREE_CLEAN=YES/NO
FILES_CHANGED=<paths>
ERROR=<NONE or exact error>
```
