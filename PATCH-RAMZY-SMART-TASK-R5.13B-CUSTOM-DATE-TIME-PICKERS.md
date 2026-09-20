# PATCH — RAMZY SMART TASK R5.13B
# Custom Start Date + Reminder Pickers

Baseline TOS:
`8b593df76498c31f2da8fb86ce4fa32459a359f1`

Scope: Start Date + Reminder Time only.
No bubble work. No AI-writing work. No backend/DB changes. Do not touch Due Date preset chips.

1) Fix epoch bug in `frontend/src/lib/smartTaskDueDate.js`:
- `smartTaskLocalDateValue(null|undefined|"") => ""`
- `smartTaskLocalDateTimeValue(null|undefined|"") => ""`
- never render 1970 for empty values.

2) Replace ONLY Smart Task advanced inputs:
- Start Date native `type=date`
- Reminder Time native `type=datetime-local`

with custom React/TOS pickers. No new package.

Start Date:
- compact trigger + calendar icon
- localized selected text / empty placeholder
- custom month/year calendar
- prev/next month
- Today / Clear / Done
- outside click + Escape
- AR/EN, light/dark, responsive
- empty opens current month
- keep `smartTaskStartDateIso(localYYYYMMDD)`

Reminder:
- custom calendar
- hour 01–12
- minutes 00/05/.../55
- AM/PM
- Now / Clear / Done
- outside click + Escape
- AR/EN, light/dark, responsive
- empty initializes draft from current local date/time rounded forward
- keep `smartTaskLocalDateTimeIso(localYYYYMMDDTHH:mm)`

Do not commit draft on outside-close/Escape.
Done commits.
Clear clears.

Preserve existing validation and payload behavior.

Tests:
- no 1970
- no native Start/Reminder picker
- date round-trip
- AM/PM noon/midnight
- Clear/Done/Escape/outside

Frontend build + live visual QA + frontend deploy + commit/push.

Return ONLY:
```
PATCH=RAMZY-SMART-TASK-R5.13B-DATE-PICKERS
PASS/FAIL=
EPOCH_1970_FIX=
START_DATE_PICKER=
REMINDER_PICKER=
NO_NATIVE_PICKERS=
DATE_ROUNDTRIP=
TIME_AM_PM=
CLEAR_DONE_ESCAPE=
AR_EN=
DARK_RESPONSIVE=
FRONTEND_BUILD=
LIVE_QA=
LIVE_DEPLOY=
COMMIT=
PUSH=
ERROR=
```
