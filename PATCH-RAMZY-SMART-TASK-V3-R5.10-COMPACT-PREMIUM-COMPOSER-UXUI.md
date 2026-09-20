# Ramzy Smart Task V3 — R5.10: Compact Premium Composer UX/UI

Baseline TOS:
`9252bebed01adeeffdf88d8f7eefdfa30418d107`

Scope ONLY:
Redesign the Smart Task composer UX/UI shown in live QA so it feels compact, premium, native to TOS, and easier to complete.

This is primarily FRONTEND UX/UI.
Do NOT change Smart Task business logic, AI behavior, writing memory, intent rules, project permissions, assignee permissions, approval flow, task payload, backend routes, or Prisma.

## Live QA problems to fix

From the current live composer:

1. There are effectively TWO scroll areas:
   - Ramzy panel/messages scroll
   - Smart Task card/body scroll
   This makes the form awkward to navigate.

2. Project picker expands inline and consumes a large part of the card.

3. Smart Task still uses purple/indigo UI for:
   - Write/Improve with Ramzy buttons
   - active project filter
   - focus rings
   - selected chips / primary actions
   - Review & create
   This clashes with the cream/champagne/gold TOS visual language already used by the panel and R5.9 bubble.

4. The form feels like a long form placed inside another scrolling window rather than a polished composer.

5. The current Project picker pushes Due date / Priority / Assignee far below the fold.

6. The footer/composer underneath competes visually with the Smart Task card.

---

# A) ONE scroll experience

Remove the Smart Task card's independent vertical scrollbar.

Current card/body uses:
- `max-height: 60vh`
- `.ramzy-smart-task-card-body { overflow-y: auto; }`

Change the layout so:
- Ramzy messages/panel remains the single main vertical scroll owner.
- Smart Task card grows naturally inside that scroll.
- `.ramzy-smart-task-card-body` must NOT create its own vertical scrollbar during normal desktop use.
- no nested wheel/trackpad scrolling traps.

Keep horizontal overflow protected.

The card can have a sensible max-width, but do not cap its normal content to a second scrolling viewport.

Mobile exception:
- if a safety max-height is truly required on very short mobile screens, use a single deliberate responsive fallback only; desktop/tablet must not have nested scrolling.

---

# B) Compact Smart Task card hierarchy

Keep all existing fields/logic but improve grouping.

## Header
Use a polished compact header:
- title: `Create task` / `إنشاء مهمة`
- short muted subtitle
- small close button
- cream/white card surface
- subtle gold/champagne divider/accent

Do not enlarge the header.

## Content spacing
Reduce vertical waste:
- body gap around 8–10 px
- compact labels
- consistent 8–10 px control height rhythm
- do not make fields cramped

Use the same warm TOS surface language as the Ramzy panel.

---

# C) Title + AI action

Desktop:
- Title input gets most of the row width.
- AI action remains on the same row when space allows.
- Button text remains exact from R5.6:
  - Write Title with Ramzy
  - Improve Title with Ramzy
  - Arabic equivalents

Narrow/mobile:
- AI action can move below the input full-width/auto-width cleanly.

Restyle `.ramzy-smart-task-ai-btn`:
- NO purple/indigo
- warm cream/champagne background
- muted gold border
- dark warm text / gold accent
- Sparkles icon
- subtle hover/focus
- loading state preserved

Do NOT change click behavior.

---

# D) Description + AI action

Keep Description textarea compact:
- default visual height roughly 90–110 px desktop
- still resizable where appropriate
- no oversized blank area

The action MUST remain clearly:
- `Write Description with Ramzy`
- `Improve Description with Ramzy`
- Arabic equivalents

Style it with the same TOS gold/cream button system.

Place it directly under or attached to the Description field so it reads as a field action, not random text.

Keep autocomplete and intent assist functional.

---

# E) Project picker becomes a COMPACT DROPDOWN / POPOVER

Do NOT keep the full results list permanently expanding the form.

## Closed state
Before a project is selected, show a compact project trigger/search field:

- label: PROJECT / المشروع
- control text:
  - `Choose a project...` / `اختر المشروع...`
- Search icon or chevron if an already-imported icon is available.
- looks like a normal TOS input.

Click/focus opens picker.

After selection:
- show selected project compactly
- optional status badge
- `Change` action
- current behavior preserved

## Open picker
Open a compact dropdown/popover anchored to the project field.

Inside:
1. status filter chips at top
2. search input
3. scrollable result list

Rules:
- Popover overlays later form fields instead of pushing them down.
- width matches project field/container
- max-height around 260–320 px
- result LIST may scroll internally because it is a dropdown; this is allowed.
- this dropdown scroll must NOT turn the whole Smart Task card into a second scrollbar.
- high enough z-index within Ramzy
- visible over Due/Priority rows
- close on:
  - project selection
  - Escape
  - outside click
- preserve keyboard arrows + Enter behavior
- preserve all canonical filters:
  All / Active / Planning / On hold / Delayed / Completed / Cancelled / Archived
- default ACTIVE remains unchanged
- archived remains disabled/non-selectable exactly as current logic
- search behavior unchanged
- permission behavior unchanged

Use a wrapper class such as:
`.ramzy-project-picker-anchor`
`.ramzy-project-picker-popover`

Do not use a portal unless genuinely necessary.
If using same DOM:
- ensure ancestors do not clip the popover
- keep the panel viewport safe

On narrow screens:
- popover may become an inline/dropdown sheet constrained to panel width
- must never overflow viewport horizontally

---

# F) TOS visual system for Smart Task

Replace the Smart Task's general purple interaction styling with the established TOS cream/champagne/gold language.

Prefer existing TOS/Ramzy CSS variables when available.

Fallback palette only if needed:
- surface: #fffdf8
- surface-alt: #fbf4e6
- border: #ead7aa
- accent: #c79a43
- accent-dark: #8b692c
- text: #2e2a23
- muted: #71695d

Apply this to:
- AI action buttons
- input focus rings
- active project filter
- selected neutral chips
- `Let Ramzy suggest`
- `Change` action where appropriate
- Review & create button
- autocomplete border/highlight
- intent assist card/actions

Do NOT recolor semantic statuses unnecessarily:
- urgent/error remain semantic red
- active/completed/status badges can keep semantic meaning

No purple/indigo for ordinary Smart Task primary UI.

---

# G) Due date / Priority compact sections

Keep ALL current choices and logic.

Improve density:
- chips slightly smaller
- consistent radius/padding
- selected neutral options use warm gold/champagne instead of purple
- hover/focus uses soft gold
- allow wrapping cleanly without huge gaps

Priority:
- URGENT may remain semantically red
- AUTO / Let Ramzy suggest uses Ramzy gold treatment

Do not change values sent to backend.

---

# H) Advanced details

Keep collapsed by default.

Restyle the toggle as a compact disclosure row:
- chevron if already available
- warm muted text
- clear hover
- no purple link appearance

When open:
- fields appear inside a soft secondary surface / inset section
- compact spacing
- no new behavior

---

# I) Assignee

Keep endpoint and recommendation logic untouched.

UX:
- select styled to match TOS
- loading/error/recommendation states remain visible
- disabled state before project selection remains clear
- no new assignee logic

---

# J) Review footer

Make the Smart Task footer visually belong to the card.

- soft warm border-top
- cream/off-white background
- Review & create button in TOS gold
- disabled state still obvious
- button must not look purple
- keep review/back/edit/submit behavior unchanged

Preferred:
- use `position: sticky; bottom: 0` ONLY if it behaves correctly inside the SINGLE Ramzy messages scroll and does not create a new scroll context.
- if sticky causes clipping/overlap, keep footer natural instead.
- correctness > forced stickiness.

Do not cover fields.

---

# K) Relationship with Ramzy composer footer

While Smart Task is open, the normal Ramzy composer is intentionally non-sendable.

Make this state clearer visually:
- keep existing `Complete the task details in the card above` behavior
- slightly reduce visual prominence of the normal composer while Smart Task is active
- do NOT hide voice/settings/footer metadata unexpectedly
- do NOT change send rules

Goal: user's attention should clearly stay on the Smart Task card.

---

# L) Responsive behavior

Must look good at:
- ~1000 px browser width like supplied live screenshot
- ~1250 px width like supplied live screenshot
- 1440 px
- mobile/narrow Ramzy panel

At ~1000 px:
- no horizontal clipping
- Title button can wrap below input if necessary
- project picker stays within Ramzy panel
- no nested card scrollbar
- controls remain readable

---

# M) Accessibility

Preserve/add:
- keyboard focus-visible
- Escape closes project popover
- outside click closes project popover
- listbox/option semantics
- selected/disabled aria state
- buttons remain actual buttons
- readable contrast
- reduced motion behavior already used elsewhere is not broken

---

# N) Do NOT touch

Absolutely do not change:
- R5.9 thought bubble
- R5.6 input-language AI logic
- Write/Improve AI endpoint semantics
- R5.7 writing memory
- autocomplete matching logic
- intent analysis behavior
- project visibility/status/archive rules
- assignee API/recommendation
- approval/task creation flow
- permissions
- backend
- Prisma
- model/provider/API settings

---

# O) Regression checks

Add/update focused frontend tests where practical:

1. Smart Task card body no longer owns normal desktop vertical scroll.
2. Project results only expand inside popover/dropdown, not document flow.
3. picker closes on selection / Escape / outside click.
4. keyboard Arrow/Enter still works.
5. canonical project filters unchanged.
6. archived remains non-selectable.
7. AI labels unchanged.
8. AI buttons no longer use purple/indigo styles.
9. primary Smart Task actions use TOS gold/cream.
10. assignee logic untouched.
11. Review & create logic unchanged.
12. no backend files changed.

---

# P) Verify

Run:
- `npm --prefix frontend run build`
- `npm --prefix backend run test:ramzy` for regression only

Live visual QA:
- open Smart Task on live TOS
- verify at ~1000 px width
- verify at ~1250/1440 px
- project picker opens over form instead of pushing Due/Priority down
- only main Ramzy content has normal form scrolling
- AI buttons match TOS gold/cream
- Review & create matches TOS
- select project and verify assignee still loads
- verify Title/Description AI still clickable
- verify dark mode if supported

Deploy:
- atomic frontend deploy
- backend restart NOT required
- HTTPS 200
- commit + push TOS main

Return only:

```
PATCH=RAMZY-SMART-TASK-V3-R5.10
PASS/FAIL=
SINGLE_SCROLL=PASS/FAIL
PROJECT_POPOVER=PASS/FAIL
POPOVER_KEYBOARD=PASS/FAIL
TOS_GOLD_UI=PASS/FAIL
AI_BUTTONS=PASS/FAIL
COMPACT_LAYOUT=PASS/FAIL
REVIEW_FOOTER=PASS/FAIL
ASSIGNEES_UNCHANGED=PASS/FAIL
PROJECT_LOGIC_UNCHANGED=PASS/FAIL
AI_LOGIC_UNCHANGED=PASS/FAIL
MEMORY_INTENT_UNCHANGED=PASS/FAIL
RESPONSIVE_1000=PASS/FAIL
RESPONSIVE_1250_1440=PASS/FAIL
DARK_MODE=PASS/FAIL
FRONTEND_BUILD=PASS/FAIL
BACKEND_TEST=PASS/FAIL
LIVE_VISUAL_SMOKE=PASS/FAIL
LIVE_DEPLOY=PASS/FAIL
COMMIT=
PUSH=YES/NO
ERROR=
```
