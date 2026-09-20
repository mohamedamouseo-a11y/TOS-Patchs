# PATCH — RAMZY SMART TASK R5.12
# Custom Start Date + Reminder Date/Time Pickers

Baseline TOS:
`8fac68094c197d02040b0349d39c08194e131867`

Goal:
Replace the browser-native Start Date and Reminder Time popups inside Ramzy Smart Task advanced details with compact TOS-native custom pickers.

User-visible target:
The two controls shown in Smart Task advanced details:
- Start Date
- Reminder Time

Do NOT redesign Due Date chips.
Do NOT change task creation logic, approval flow, RBAC, backend payload shape, project picker, assignee picker, AI behavior, or other Ramzy UI.

---

## 1) Fix the 01/01/1970 bug first

Confirmed root cause exists in:
`frontend/src/lib/smartTaskDueDate.js`

Current helpers call `new Date(value)` without rejecting null/empty.
In JS, `new Date(null)` becomes epoch 1970.

Fix:

`smartTaskLocalDateValue(value)`
- if value is null / undefined / empty string => return `""`
- invalid date => `""`

`smartTaskLocalDateTimeValue(value)`
- same empty guard
- invalid date => `""`

Add regression tests:
- null => ""
- undefined => ""
- "" => ""
- valid ISO remains correctly formatted

No Smart Task field may render 1970 when its actual value is empty.

---

## 2) Replace ONLY these native Smart Task inputs

Current Smart Task advanced JSX uses:

```
<input type="date" ... startDate ... />
<input type="datetime-local" ... reminderAt ... />
```

Replace those two controls with custom TOS pickers.

Do NOT use:
- native `type="date"`
- native `type="datetime-local"`
for these two Smart Task advanced controls.

Do not add a new npm package.
Use React + existing lucide icons + Date/Intl.

RevisionEditor may remain unchanged in this patch unless sharing the component is trivial and zero-risk.
Primary scope is the visible Smart Task advanced composer from the supplied screenshots.

---

## 3) Shared compact picker foundation

Implement small reusable local components/helpers, preferably in:
- `frontend/src/components/RamzyAssistant.jsx`
or a focused new component file if cleaner.

Suggested components:
- `RamzyDatePicker`
- `RamzyDateTimePicker`

They must use controlled values and return existing ISO-compatible values through current helpers.

Requirements:
- anchored popover under trigger
- remains inside Ramzy panel
- no browser-native popup
- no portal outside panel unless necessary
- high enough z-index above Smart Task card
- close on outside click
- close on Escape
- only one date/time picker open at a time
- compact enough for current Ramzy panel
- no nested giant scroll area
- keyboard-focus visible
- AR/EN copy
- RTL/LTR safe
- light + dark mode

Use TOS cream / champagne / warm-gold visual language already used by Smart Task.

---

## 4) Start Date picker UX

Closed field:
- looks like current premium Smart Task input
- Calendar icon
- when empty:
  - EN: `Select start date`
  - AR: `اختر تاريخ البداية`
- when selected: human-readable localized date, never raw ISO
- optional small clear icon/button when value exists

Open popover:
- header: Month + Year
- previous month button
- next month button
- weekday header
- standard 7-column calendar grid
- selected day clearly highlighted
- today has subtle outline/dot
- adjacent-month filler days may be muted or omitted
- footer actions:
  - Today / اليوم
  - Clear / مسح
  - Done / تم

Behavior:
- opening with empty value starts at current month, NOT January 1970
- opening with value starts at selected month
- selecting a date updates local selection
- Done commits and closes
- Clear sets `startDate = null`
- preserve existing `smartTaskStartDateIso()` conversion semantics
- do not invent new validation rules

---

## 5) Reminder Date + Time picker UX

Closed field:
- Calendar/clock icon
- empty:
  - EN: `Select reminder`
  - AR: `اختر وقت التذكير`
- selected: localized date + time
- clear button when selected

Open popover:
A compact two-part layout:

### Date
Same calendar behavior as Start Date.

### Time
Custom controls, NOT native browser time picker.

Use:
- hour selector: 01–12
- minute selector: 00, 05, 10 ... 55
- AM / PM segmented control

Keep them visually compact and custom-styled.

Optional quick chips if they fit without clutter:
- 09:00 AM
- 12:00 PM
- 03:00 PM
- 06:00 PM

Do not make quick chips mandatory if they hurt compactness.

Footer:
- Now / الآن (round to nearest next 5 minutes if needed)
- Clear / مسح
- Done / تم

Behavior:
- empty picker opens on current date and sensible next time, e.g. current time rounded forward to 5 minutes
- never epoch/1970
- selected local date/time converts using existing `smartTaskLocalDateTimeIso()`
- existing validation remains authoritative:
  - reminder must be future
  - reminder must not exceed due date when due date exists
- validation errors continue to render through current Smart Task error path
- Clear sets `reminderAt = null`

---

## 6) State handling

Avoid storing fake epoch defaults.

Picker draft state may initialize from:
- selected value when present
- current local date/time when empty

But Smart Task data must remain:
- `startDate: null` until the user commits a date
- `reminderAt: null` until the user commits a reminder

Cancel/outside-close:
- must NOT accidentally commit an unconfirmed draft
- preserve previous value

Done:
- commits exact selected value

Clear:
- clears immediately or commits clear consistently; choose one behavior and test it.

---

## 7) Date correctness / timezone

Preserve current semantics:
- Start Date uses `smartTaskStartDateIso(localYYYYMMDD)`
- Reminder uses `smartTaskLocalDateTimeIso(localYYYYMMDDTHH:mm)`

Do not switch to UTC calendar rendering for local date selection.
Avoid date shifting by timezone.

Tests required for:
- selected local date survives round-trip
- reminder local date/time survives round-trip
- midnight / noon AM-PM conversion
- December -> January month navigation
- leap-year February
- empty values never produce 1970

---

## 8) Visual design

Add styles to:
`frontend/src/components/ramzySmartTaskComposerV1.css`

Suggested classes:
- `.ramzy-date-picker`
- `.ramzy-date-trigger`
- `.ramzy-date-popover`
- `.ramzy-date-header`
- `.ramzy-date-grid`
- `.ramzy-date-day`
- `.ramzy-time-controls`
- `.ramzy-time-select`
- `.ramzy-time-period`
- `.ramzy-date-actions`

Style:
- #fffdf8 / #fbf4e6 surfaces
- #ead7aa borders
- #c79a43 selected/accent
- dark variants consistent with existing Ramzy Smart Task
- border-radius 10–14px
- premium subtle shadow
- no blue native browser selection UI
- do not make popover wider than Smart Task field
- max width safe on mobile

Calendar target height should stay compact, roughly 260–330px.
Reminder picker may be slightly taller but should not dominate the Ramzy panel.

If popover would overflow below the visible Smart Task panel:
- allow it to open upward or remain within the card's visible area
- do not force the whole Ramzy window to jump

---

## 9) Accessibility

- trigger uses `aria-haspopup="dialog"` or appropriate semantic
- `aria-expanded`
- popup has accessible label
- month nav buttons have AR/EN aria-labels
- selected day uses `aria-selected`
- Enter/Space selects focused control
- Escape closes
- focus ring visible
- buttons must be real buttons, not clickable divs

---

## 10) No functional regressions

Must preserve:
- `estimatedHours`
- Start Date payload field
- Reminder payload field
- Smart Task validation
- Review summary
- approval proposal payload
- project/assignee selections
- Due Date logic/chips
- priority logic
- permissions
- backend API

No backend change expected.
No DB migration.

---

## 11) Tests + live QA

Automated:
- helper null/empty regression
- calendar helper/date conversion tests
- AM/PM conversion
- current-month empty state
- no native date/datetime input for Smart Task Start Date/Reminder Time
- existing Smart Task tests pass
- frontend build PASS

Live visual QA:
1. Open Smart Task > Advanced details.
2. Start Date empty shows placeholder, not 01/01/1970.
3. Start Date opens custom calendar, not Chrome native picker.
4. Select date, clear it, reopen.
5. Reminder empty shows placeholder, not 1970.
6. Reminder opens custom date + time UI.
7. Check AM/PM.
8. Check Clear / Done / outside click / Escape.
9. Verify English.
10. Verify Arabic.
11. Verify dark mode.
12. Verify mobile/narrow panel.
13. Review & create displays selected values correctly.

Deploy frontend atomically.
Commit + push.

---

## Do NOT touch

- backend
- DB/schema
- Ramzy permission work
- TOS permission audit
- Due Date preset chips
- project picker
- assignee picker
- title/description AI
- Smart Task language detection
- approval policy
- task backend validation

---

## Return ONLY

```
PATCH=RAMZY-SMART-TASK-R5.12-CUSTOM-DATE-TIME-PICKERS
PASS/FAIL=
EPOCH_1970_FIX=PASS/FAIL
START_DATE_CUSTOM_PICKER=PASS/FAIL
REMINDER_CUSTOM_PICKER=PASS/FAIL
NO_NATIVE_PICKER=PASS/FAIL
DATE_ROUNDTRIP=PASS/FAIL
TIME_AM_PM=PASS/FAIL
CLEAR_DONE=PASS/FAIL
OUTSIDE_ESCAPE=PASS/FAIL
AR_EN=PASS/FAIL
DARK_MODE=PASS/FAIL
RESPONSIVE=PASS/FAIL
SMART_TASK_REGRESSION=PASS/FAIL
FRONTEND_BUILD=PASS/FAIL
LIVE_VISUAL_QA=PASS/FAIL
LIVE_DEPLOY=PASS/FAIL
DB_MIGRATION=NO
BACKEND_CHANGE=NO
COMMIT=
PUSH=YES/NO
ERROR=
```
