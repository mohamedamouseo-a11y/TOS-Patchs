# TOS_TASK_DETAILS_V2_8D

Patch: `TOS-UXUI-TASK-DETAILS-V2-8D-RIGHT-RAIL-TCS-VIEWPORT-FIT`

Baseline chain: `TOS_TASK_DETAILS_V2_7`

## Scope

Final visual-fit pass for the canonical Overview right rail at 1664×936.

Preserved from V2.7:
- Description/editor physically LEFT.
- Canonical rail physically RIGHT.
- Hero and exactly four primary controls unchanged.
- Existing Quick actions, Task information, Tags, and Task Details TCS Assistant DOM/content unchanged.
- Global floating TCS launcher remains separate.

V2.8D only reduces right-rail vertical density and slightly lifts the rail so the existing Task Details TCS Assistant card fits fully above the fixed footer.

## Safety

- CSS-only.
- `ProfessionalTaskBoard.jsx` must remain byte-identical during patch execution.
- No API, DB, permissions, task business logic, upload, TWS, Ramzy, or TCS logic changes.
- Build/deploy is guarded and rolls back on failure.
- No Git operation is performed in `/var/www/TOS`.

## Visual QA

Viewport: `1664×936`, Light Mode.

Expected:
- Description/editor LEFT.
- Canonical Overview rail RIGHT.
- Quick actions visible.
- Task information visible.
- Tags visible.
- Task Details TCS Assistant card fully visible inside the rail.
- Global floating TCS launcher remains separate.
