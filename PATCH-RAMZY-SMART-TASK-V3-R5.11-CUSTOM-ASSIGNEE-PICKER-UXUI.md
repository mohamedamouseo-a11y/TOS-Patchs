# Ramzy Smart Task V3 — R5.11: Custom Assignee Picker UX/UI

Baseline TOS:
`95fc32abc3caa27614e528601a2a30ad239b821e`

Scope ONLY:
Replace the Smart Task Assignee native HTML <select> with a compact, premium TOS-styled custom combobox/dropdown.

## Confirmed live defect

Live QA on Windows/Chrome shows the current Assignee native <select> opening as a huge browser-native menu that escapes the Ramzy panel and covers a large portion of the page.

This is a frontend UX defect caused by using the native `<select>`, not a backend/permissions problem.

Do NOT change:
- assignee endpoint
- returned assignee list
- assignability/permission rules
- recommendation algorithm
- AUTO recommendation semantics
- Unassigned semantics
- selected assignee payload
- project picker
- AI logic
- memory/intent
- approval flow
- backend
- Prisma

---

# A) Replace native select with custom picker

Current source uses:

```jsx
<select className="ramzy-smart-task-select" ...>
  ...
</select>
```

Replace ONLY this Smart Task Assignee control with a custom React combobox/listbox.

Suggested state:
- `assigneePickerOpen`
- `assigneeSearch`
- `assigneePickerFocusIndex`

Reuse existing:
- `smartTaskAssignees`
- `smartTaskAssigneesLoading`
- `smartTaskAssigneesError`
- `smartTaskRecommendedAssigneeId`
- `chooseSmartTaskAssignee()`

No API changes.

---

# B) Closed trigger states

Use one compact TOS-styled trigger button/input.

### No project selected
Disabled trigger:
- EN: `Select a project first`
- AR: `اختر المشروع أولاً`

### Project selected, no assignee selected
- EN: `Select assignee...`
- AR: `اختر المنفذ...`

### AUTO selected
Show:
- `✨ Let Ramzy suggest`
- AR: `✨ خلي رمزي يقترح الأنسب`

### Unassigned selected
Show:
- `Unassigned`
- AR: `بدون تحديد`

### Specific user selected
Show:
- user name
- department in muted secondary text if available
- do not expose extra unrelated metadata

Use a ChevronDown icon if already imported or easy to import.

---

# C) Open dropdown / popover

Open a contained dropdown anchored to the Assignee field.

It MUST:
- stay inside the Ramzy panel width
- never open as a browser-native menu
- never escape across the whole page
- overlay below/above neighboring form content without expanding the whole Smart Task excessively
- max-height ~240–300 px
- scroll only inside the result list if necessary
- use TOS cream/champagne/gold visuals
- dark mode support
- high enough z-index inside Ramzy
- no viewport horizontal overflow

Suggested structure:
```
ramzy-assignee-picker
  ramzy-assignee-trigger
  ramzy-assignee-popover
    ramzy-assignee-search
    ramzy-assignee-option (AUTO)
    ramzy-assignee-option (NONE)
    ramzy-assignee-option* users
```

---

# D) Search

Add local search inside the dropdown.

Search across:
- name
- department
- role only if already present in loaded data

Rules:
- local filtering only
- no extra API request while typing
- case-insensitive
- trim whitespace
- clear search when picker closes or selection changes

Placeholder:
- EN: `Search assignee...`
- AR: `ابحث عن منفذ...`

If no match:
- EN: `No matching assignee`
- AR: `لا يوجد منفذ مطابق`

---

# E) Ordering

Keep special actions first:

1. AUTO — Let Ramzy suggest
2. NONE — Unassigned
3. Recommended user if `smartTaskRecommendedAssigneeId` exists
4. Remaining users

Do not duplicate the recommended user.

Recommended user should get a small badge:
- EN: `Recommended`
- AR: `مقترح`

Do not alter how the recommendation itself is calculated.

---

# F) Keyboard UX

Support:
- Enter / Space opens trigger
- ArrowDown / ArrowUp moves highlighted option
- Enter selects highlighted option
- Escape closes
- Tab leaves naturally
- type/search input works normally

Use:
- `role="combobox"` on trigger/wrapper as appropriate
- `aria-expanded`
- `aria-controls`
- `role="listbox"`
- `role="option"`
- `aria-selected`

Keep focus visible.

---

# G) Outside click

Clicking outside the assignee picker closes it.

Changing project:
- closes assignee picker
- clears assignee search/focus state
- preserves existing logic that clears a specific assignee when project changes

Opening another Smart Task popover such as Project picker should close Assignee picker if needed so they do not overlap.

---

# H) Visual design

Match R5.10 TOS premium system:
- warm off-white / cream surface
- champagne/gold border
- warm dark text
- muted gold accent
- subtle shadow
- 10–12 px control padding
- ~10 px radius
- compact rows
- no purple/indigo

Semantic error/loading colors stay as-is.

AUTO option:
- Sparkles
- subtle gold tint

Recommended option:
- soft gold highlight/badge

Selected option:
- warm champagne/gold selected state

Hover/focus:
- soft gold border/background

Dark mode:
- warm charcoal surface
- muted gold border
- off-white text
- no purple

---

# I) Preserve existing recommendation message

Current optional message:
`Workload suggestion: <name>`

Keep the information but visually integrate it better.

Preferred:
- small inline recommendation banner above trigger OR inside dropdown header
- TOS gold/champagne style
- existing `Use` behavior still works if kept

Do not duplicate recommendation excessively. If the recommended option/badge is clear enough, the separate banner may be reduced, but do not remove the user's ability to apply the recommendation.

---

# J) Responsive

At ~1000px / ~1250px / 1440px:
- dropdown stays inside Ramzy
- no native menu
- no horizontal overflow
- no page-covering list

On mobile/narrow:
- dropdown width = available Smart Task card width
- max-height smaller if necessary
- touch targets remain usable

---

# K) Regression checks

Verify:
1. native Smart Task assignee `<select>` is removed.
2. no browser-native page-sized dropdown can occur.
3. AUTO still selects `{ auto: true }` through existing logic.
4. NONE still selects `{ none: true }`.
5. specific user still calls existing `chooseSmartTaskAssignee(user)`.
6. project change still clears specific assignee according to existing rules.
7. recommended assignee unchanged.
8. only ACTIVE/assignable users returned by backend remain used.
9. no backend file changed.
10. project picker unchanged.
11. review/create payload unchanged.

---

# L) Verification

Run:
- `npm --prefix frontend run build`
- `npm --prefix backend run test:ramzy` regression only

Live visual QA:
- open Smart Task
- select a project
- open Assignee
- verify dropdown stays inside Ramzy panel
- search by name
- select AUTO
- select Unassigned
- select a real user
- verify recommendation badge/message if available
- verify keyboard Arrow/Enter/Escape
- verify at ~1000 px width
- verify dark mode if supported

Deploy:
- atomic frontend deploy
- backend restart NOT required
- HTTPS 200
- commit + push TOS main

Return only:

```
PATCH=RAMZY-SMART-TASK-V3-R5.11
PASS/FAIL=
NATIVE_SELECT_REMOVED=PASS/FAIL
CUSTOM_ASSIGNEE_PICKER=PASS/FAIL
SEARCH=PASS/FAIL
KEYBOARD=PASS/FAIL
AUTO_OPTION=PASS/FAIL
UNASSIGNED_OPTION=PASS/FAIL
RECOMMENDED_OPTION=PASS/FAIL
NO_PAGE_ESCAPE=PASS/FAIL
TOS_GOLD_UI=PASS/FAIL
ASSIGNEE_LOGIC_UNCHANGED=PASS/FAIL
PROJECT_PICKER_UNCHANGED=PASS/FAIL
BACKEND_UNCHANGED=PASS/FAIL
RESPONSIVE_1000=PASS/FAIL
DARK_MODE=PASS/FAIL
FRONTEND_BUILD=PASS/FAIL
BACKEND_TEST=PASS/FAIL
LIVE_VISUAL_SMOKE=PASS/FAIL
LIVE_DEPLOY=PASS/FAIL
COMMIT=
PUSH=YES/NO
ERROR=
```
