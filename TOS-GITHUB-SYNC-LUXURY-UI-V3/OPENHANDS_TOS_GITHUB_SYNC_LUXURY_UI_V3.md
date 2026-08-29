# TOS GitHub Sync — Luxury Executive UI V3

## Target
Apply to `/var/www/TOS` on baseline:

`66f7dd32794e9c5bb42dd63222b9a0bc5d4a7ee9`

Target page:
`/settings#github`

Primary component:
`frontend/src/components/GithubAdvancedAdmin.jsx`

## Objective
Rebuild the VISUAL PRESENTATION of the existing GitHub Sync page into an ultra-premium executive control center matching the approved luxury mockup direction.

This must look materially more premium than the current baseline in BOTH dark and light mode while preserving every current function, section, control, safety guard, API call, and data source.

This is a visual redesign, not a business-logic rewrite.

---

# NON-NEGOTIABLE PRESERVATION CONTRACT

Do NOT remove, hide, replace, or weaken any existing functional capability.

Preserve all existing:
- repository status
- Last Review
- Last Push
- Refresh
- Review Push
- Execute Push
- Pull Review
- Two-way Sync
- Source Archive
- Cancel operation
- connection settings
- token verification
- repository selector
- branch selector
- local TOS path
- save settings
- disconnect
- changed files information
- Changes by Type
- Recent Sync Activity
- Repository Information
- Logs & Advanced Actions
- operation logs/progress
- review fingerprint safety
- active operation recovery
- all API contracts
- all auth/permission behavior
- Arabic/English support

NO backend changes.
NO Prisma changes.
NO database changes.
NO auth changes.
NO fake metrics or invented backend data.

Use only data already available in the current component/API.

---

# GLOBAL SHELL SAFETY

Do NOT redesign the global TOS sidebar/header/navigation outside the GitHub page.

Only redesign the GitHub Sync content rendered by `GithubAdvancedAdmin.jsx` and minimal existing shared UI styling if strictly required.

The existing global Settings shell must remain intact.

---

# APPROVED VISUAL DIRECTION

The page must feel like a luxury enterprise command center:
- executive
- restrained
- high-trust
- cinematic without being flashy
- premium spacing
- refined typography
- layered surfaces
- champagne-gold detailing
- subtle emerald success states
- crisp hierarchy
- no gaming/neon style

The redesign must produce a CLEAR visual delta from baseline. Merely changing a few colors is NOT acceptable.

---

# DARK MODE

Use a premium near-black / deep navy surface system.

Suggested visual tokens:
- canvas: `#070A0F` / `#090D14`
- raised surface: `#0D121B` / `#111722`
- secondary raised: `#151B25`
- primary text: `#F7F5EF`
- secondary text: `#A8AFBB`
- champagne gold: `#C9973B` / `#D9AE5B`
- subtle gold border: rgba(217,174,91,.22)
- emerald healthy: `#21B779`
- blue info: restrained muted blue only
- danger: muted red, not neon

Use:
- subtle radial highlight behind hero
- very thin gold edge accents
- low-opacity inner highlights
- soft premium shadows
- no large glowing borders
- no excessive gradients

---

# LIGHT MODE

Use warm ivory / porcelain rather than plain white.

Suggested visual tokens:
- canvas: `#F7F3EC`
- primary surface: `#FFFDF9`
- secondary surface: `#F8F3E9`
- primary text: `#17130E`
- secondary text: `#6E665B`
- champagne gold: `#B9852E` / `#C99C4A`
- border: `#E9DFC9`
- emerald healthy: `#168A5B`

Use:
- very subtle warm shadows
- thin champagne dividers
- clean ivory cards
- no sterile pure-white dashboard look

Dark and light layouts must be structurally identical.

---

# LAYOUT BLUEPRINT

## 1. Luxury Hero Header

Create a compact but premium hero at the top of GitHub Sync content.

Left side:
- small TOS Developer Hub eyebrow
- large `Advanced GitHub Sync` title
- one concise subtitle
- repository identity row with GitHub icon
- `owner/repo · branch`
- Connected state pill

Right side:
- live health indicator using existing status data
- Refresh/Sync-related safe action only if already supported
- compact overflow/secondary action area only if existing functionality maps to it

Do NOT invent a new backend action.

Hero must visually feel like the most premium part of the page.

---

## 2. Executive Workflow Stepper

Immediately below hero, render a sophisticated horizontal 4-stage flow:

1. Refresh
2. Review
3. Execute Push
4. Complete

Design:
- thin connector rail
- numbered circular nodes
- active node uses gold/green emphasis depending on state
- completed nodes get calm success treatment
- locked/pending nodes remain readable
- concise helper text below each node
- no giant buttons inside the stepper

Existing action enablement rules must remain unchanged.

On tablet/mobile, convert to a clean stacked/vertical flow.

---

## 3. Four Premium Status Cards

Create a single row of four compact executive cards using existing data:

### Repository Status
- healthy/attention state
- current branch
- working tree state

### Last Review
- latest available review/action state
- result
- safe Review button remains available

### Last Push
- short SHA
- commit message
- timestamp / actor if available

### Ahead / Behind
- Ahead value
- Behind value
- Remote/branch health signal

Cards must have:
- premium icon container
- strong headline/value
- concise metadata
- subtle accent border
- balanced heights

Do not remove information currently available in baseline cards.

---

## 4. Quick Action / Review Controls

Preserve the actual working controls for:
- Refresh
- Review Push
- Execute Push

Integrate them elegantly under/within the workflow area without deleting any current safety messaging or disabled states.

Dangerous Execute action must never appear enabled before current review contract allows it.

---

## 5. Main Intelligence Grid

Desktop: 3-column premium grid inspired by the approved mockup.

### Left — Change Intelligence
Use CURRENT Changes by Type data only:
- donut/ring visual
- total changes in center
- New
- Modified
- Deleted
- Other

Do not introduce fake historical sync analytics.

### Center — Recent Sync Activity
Premium vertical timeline:
- node
- connector
- action title
- short detail
- time/status
- success/warning/error distinction

Use only existing activity/operation/status data.

### Right — Repository Information
Display existing repository information in an elegant key/value panel:
- repository
- branch
- commit
- permission
- working tree
- last sync
- remote health where available

Do not omit current Repository Information fields.

At narrower widths collapse cleanly to 2 columns then 1.

---

## 6. Connection Settings

Keep the entire existing Connection Settings feature.

Restyle as a premium accordion/details card with:
- icon/title/subtitle
- refined Show / Hide control
- luxury input fields
- token visibility control
- repository and branch selectors
- Verify / Load / Save actions
- Disconnect visually separated as destructive

Do not move secrets to frontend storage.

---

## 7. Logs & Advanced Actions

Keep the entire section and ALL current advanced controls.

Restyle as premium collapsible command panel.

Must preserve:
- Pull Review
- Two-way Sync
- Source Archive
- Cancel operation when available
- operation log/progress UI
- any existing advanced controls in baseline

No control may disappear just because the section is collapsed.

---

# INTERNAL GITHUB NAVIGATION

The baseline internal GitHub navigation/anchor rail may be retained but must be visually refined and compact.

Do not create a second large application sidebar.

If retained:
- slim luxury rail
- gold active state
- dark/light parity
- clear anchors
- no wasted width

If it makes the page feel overcrowded at 1366px, collapse it into compact tabs/anchor pills WITHOUT removing destinations.

---

# TYPOGRAPHY

Use existing TOS font stack.

Hierarchy:
- page title: strong, elegant, premium
- section titles: high contrast
- operational labels: compact and clear
- metadata: readable, not tiny

Do NOT use decorative serif fonts if they are not already part of TOS.

No tiny low-contrast labels.

---

# COMPONENT DETAILS

Cards:
- 18–24px radius depending on hierarchy
- 1px refined borders
- layered background surfaces
- restrained shadow
- consistent padding

Buttons:
- gold reserved for primary safe action
- emerald for healthy/success state where appropriate
- secondary buttons remain dark/neutral
- destructive remains clearly red
- disabled must remain legible

Pills:
- compact
- thin border
- status dot/icon + label

Inputs:
- 12–14px radius
- high readability
- strong focus ring
- theme-correct background

---

# MICRO-INTERACTIONS

Allowed:
- 160–200ms hover/focus transitions
- subtle card border elevation
- subtle active-operation pulse
- smooth accordion transition if existing structure allows

Avoid:
- bouncing
- animated gradients
- large glow
- layout shifts during polling

Respect reduced motion where practical.

---

# RESPONSIVE

Must work at:
- 1920
- 1440
- 1280
- 1024
- tablet
- mobile

No horizontal page scrolling.
No clipped buttons.
No hidden critical information.

---

# IMPLEMENTATION SCOPE

Preferred changed file:
`frontend/src/components/GithubAdvancedAdmin.jsx`

Minimal supporting changes in existing frontend primitives/styles are allowed ONLY if necessary.

No new design system.
No business logic refactor.

---

# ACCEPTANCE GATE

Implementation is PASS only if ALL are true:

1. `GithubAdvancedAdmin.jsx` materially changes from baseline.
2. Dark mode clearly matches premium luxury executive direction.
3. Light mode clearly matches premium warm-ivory executive direction.
4. Every baseline section still exists.
5. Every baseline GitHub action still exists.
6. No backend/API/auth/Prisma/database changes.
7. No fake statistics/data introduced.
8. Refresh works.
9. Review Push remains present and safety gated.
10. Execute Push remains present and safety gated.
11. Pull Review remains present.
12. Two-way Sync remains present.
13. Source Archive remains present.
14. Connection Settings remains complete.
15. Logs & Advanced Actions remains complete.
16. Changes by Type remains present.
17. Recent Sync Activity remains present.
18. Repository Information remains present.
19. Arabic and English remain supported.
20. Dark/light theme switching renders correctly.
21. Frontend build passes.
22. `/settings#github` smoke test passes.
23. No console-breaking runtime error.
24. No horizontal overflow at 1280 desktop.

If any existing functionality disappears, V3 is FAILED and must not be committed.

---

# EXECUTION LIMIT

Keep this run short.

- Do not scan the whole repo.
- Inspect only this component and minimal dependencies.
- Do not run broad tests.
- Run ONE frontend build.
- Run ONE focused page smoke check.
- Target: 10–15 minutes.
- If blocked, STOP and report instead of long investigation.

---

# COMMIT

After successful implementation create exactly one LOCAL commit:

`feat(ui): luxury github sync experience v3`

DO NOT PUSH.

---

# DEPLOYMENT

Deploy frontend using the current canonical TOS frontend deployment flow after the build passes.

Do not restart/change backend unless absolutely required for the normal frontend deployment flow.

---

# FINAL RESPONSE

Return only:

```text
BASELINE_SHA=
FILES_CHANGED=
FUNCTIONS_REMOVED=NO
BACKEND_CHANGED=NO
PRISMA_CHANGED=NO
DATABASE_CHANGED=NO
DARK_MODE=PASS/FAIL
LIGHT_MODE=PASS/FAIL
ALL_EXISTING_SECTIONS_PRESERVED=PASS/FAIL
ALL_EXISTING_ACTIONS_PRESERVED=PASS/FAIL
FRONTEND_BUILD=PASS/FAIL
PAGE_SMOKE_TEST=PASS/FAIL
FINAL_LOCAL_SHA=
WORKING_TREE=
DEPLOYMENT=
PUSH_PERFORMED=NO
BLOCKER=
```
