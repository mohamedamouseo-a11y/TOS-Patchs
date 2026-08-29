# TOS GitHub Sync Premium UI V1

## Patch Type
Frontend UX/UI redesign specification only.

## Target Repository
`/var/www/TOS`

GitHub: `mohamedamouseo-a11y/TOS`

## Required Baseline
`66f7dd32794e9c5bb42dd63222b9a0bc5d4a7ee9`

Do not implement this patch on any older baseline.

## Target Page
`/settings#github`

Primary component:
`frontend/src/components/GithubAdvancedAdmin.jsx`

Use existing shared UI primitives/tokens when useful. Do not rewrite GitHub logic.

---

# Objective
Transform the existing GitHub Sync / Developer Hub screen into a premium executive-grade control center while preserving every existing behavior and API contract.

The redesign must feel:
- premium
- modern
- calm
- high-trust
- operational
- consistent with TOS dark/gold identity

This phase is visual/interaction polish only.

---

# Non-Negotiable Functional Contract

Do NOT change:
- GitHub API endpoints
- token verification behavior
- repository loading
- branch loading
- status loading
- review flow
- push flow
- pull flow
- two-way sync flow
- operation polling
- safety checks
- sessionStorage operation recovery
- connected repository source of truth
- backend API version contract
- authentication
- permissions
- database
- Prisma

No backend changes unless a rendering-only blocker is proven and explicitly documented.

---

# Visual Direction

## Theme
Premium dark executive control center.

Base:
- near-black / charcoal surfaces
- restrained warm gold accents
- subtle warm highlights
- low-noise borders
- soft depth, not heavy glow

Avoid:
- gaming/neon look
- excessive gradients
- oversized glass blur
- loud gold fills everywhere
- excessive shadows
- dashboard clutter

## Visual hierarchy
The page must immediately answer:
1. Are we connected?
2. Which repository/branch is active?
3. Is the repo synchronized?
4. Is there anything to review?
5. What is the next safe action?

---

# Layout Architecture

## 1. Premium Hero / Control Header
Replace the current flat top card with a premium hero panel.

Must include:
- TOS Developer Hub eyebrow
- `Advanced GitHub Sync` title
- concise subtitle
- live connection state
- repository + branch identity
- compact health/status chips

Suggested visual order:

Left:
- icon
- eyebrow
- title
- subtitle

Right:
- Connected / Disconnected state
- `owner/repo`
- branch chip

The hero must remain compact and operational, not marketing-heavy.

---

## 2. Repository Health Summary
Create a clear status strip / card group for:
- Ahead
- Behind
- Working Tree
- Remote

Each metric should use:
- icon
- short label
- primary value
- status tone

Desired states:
- healthy/synced = green
- attention = warm amber
- blocked/error = red
- neutral = zinc

Do not rely on color alone; include text/icon state.

---

## 3. Review → Push Workflow
Turn the current quick steps row into a premium operational stepper.

Stages:
1. Refresh Status
2. Review Changes
3. Execute Approved Action
4. Verify / Complete

Requirements:
- obvious current step
- completed step state
- locked/disabled state
- safe primary action
- minimal helper text
- clear operation progress

Do not alter action enablement logic.

The most dangerous action must not visually dominate before review is complete.

---

## 4. Last Review / Last Push
Refine these into compact high-signal cards.

Last Review should show:
- action
- result
- timestamp if available

Last Push should show:
- commit SHA (shortened visually only)
- message
- actor/email if already provided by API
- recorded state

No new backend fields.

---

## 5. Changes by Type
Improve the current analytics panel.

Keep existing data only.

Use:
- large total count
- clean ring/donut presentation OR premium count summary if existing implementation is CSS-only
- New / Modified / Deleted / Other legend
- empty-state treatment when total = 0

No new chart dependency unless already present in TOS.

---

## 6. Recent Sync Activity
Convert to a premium activity timeline/list.

Each row should communicate:
- status indicator
- action title
- concise secondary detail
- timestamp

States:
- success
- running
- warning
- blocked/error

Long text must truncate gracefully with accessible title/tooltip behavior if existing patterns support it.

---

## 7. Alerts / Safety / Errors
All operation blockers and warnings must look deliberate and trustworthy.

Use structured callouts:
- icon
- short title
- concise detail
- optional safe action

Never render raw HTML/backend gateway responses.

Preserve existing sanitized error behavior.

---

## 8. Connection Settings
Restyle the current connection section into a premium collapsible panel.

Fields include existing values only:
- GitHub Personal Access Token
- Local TOS path
- Repository
- Branch

Requirements:
- clearer labels
- better input contrast
- clean password visibility control
- aligned Verify / Load / Save / Disconnect actions
- dangerous Disconnect action visually separated

Do not persist secrets in frontend storage.

---

# Component Styling Rules

## Cards
- consistent radius
- subtle 1px border
- layered dark surfaces
- soft inner/outer contrast
- avoid excessive box-shadow

## Buttons
Primary:
- gold/warm accent only for the next safe primary action

Secondary:
- dark elevated surface

Success:
- green state, not full saturated fill unless necessary

Danger:
- reserved for destructive/blocked actions

Disabled:
- visibly disabled but still legible

## Typography
Use existing TOS font stack.

Hierarchy:
- strong page title
- medium section titles
- compact operational labels
- muted metadata

Avoid tiny low-contrast text.

## Spacing
Increase breathing room between functional groups while keeping the screen compact.

Use consistent spacing rhythm rather than arbitrary margins.

---

# Interaction Polish

Allowed:
- subtle hover elevation
- border emphasis
- 150–220ms transitions
- gentle status pulse only for active operation
- skeleton/loading placeholders
- smooth section expansion

Not allowed:
- large motion
- animated gradients
- bouncing buttons
- distracting glow
- layout shift while polling

Respect reduced motion where feasible.

---

# Responsive Contract

Desktop is the primary target, but page must remain usable at:
- 1440+
- 1280
- 1024
- tablet width
- mobile width

On narrow screens:
- stack metric cards cleanly
- stepper may become vertical
- action buttons wrap without overflow
- token/repo/branch inputs remain usable
- no horizontal page scroll

---

# Localization Contract

Preserve Arabic/English support already driven by `usePreferences()`.

Do not hardcode a new English-only interface.

RTL must remain readable and structurally correct.

---

# Accessibility

Minimum:
- visible focus states
- disabled states remain understandable
- buttons keep labels/icons
- status not communicated by color alone
- adequate dark-theme contrast
- form labels remain associated/clear

---

# Implementation Scope

Preferred scope:
- `frontend/src/components/GithubAdvancedAdmin.jsx`
- minimal existing shared styles/primitives only if required

Do not redesign unrelated Settings pages in this patch.

Do not create a new design system.

Do not refactor GitHub business logic.

---

# Acceptance Criteria

1. `/settings#github` loads with no runtime errors.
2. Existing connected TOS repository remains displayed from API data.
3. Repository/branch selectors still work.
4. Verify token flow still works.
5. Refresh status still works.
6. Review Push still works.
7. Review Pull still works if currently available.
8. Review Sync still works if currently available.
9. Execute action remains protected by review state.
10. Active operation polling/recovery remains intact.
11. Success/error messages remain functional.
12. No raw gateway HTML appears.
13. Desktop layout is visibly premium and more structured than current baseline.
14. Responsive layout has no horizontal overflow.
15. Arabic and English modes still render.
16. Frontend build passes.
17. No backend/Prisma/database changes.

---

# Validation — Short Run

Do not run the full repository test suite.

Run only:
1. focused inspection of changed component
2. frontend build
3. page smoke test for `/settings#github`
4. verify browser console has no breaking error
5. verify existing controls still render and retain handlers

Target execution time: 10–15 minutes.

If a blocker requires broad investigation, STOP and report instead of continuing autonomously.

---

# Commit Contract

After implementation in `/var/www/TOS` create ONE local commit:

`feat(ui): premium redesign github sync control center`

DO NOT PUSH.

---

# Deployment Contract

After successful build, deploy using the canonical TOS frontend deployment flow and verify the actual nginx serving directory.

Do not change backend deployment unless backend was intentionally changed (which is not expected in this patch).

---

# Required Implementation Report

Create after implementation:

`/var/www/TOS-Patchs/GitHub/PremiumUI/TOS_GITHUB_SYNC_PREMIUM_UI_V1_REPORT.md`

Report must include:

```text
BASELINE_SHA=
ROOT_CAUSE=
FILES_CHANGED=
BACKEND_CHANGED=NO
DATABASE_CHANGED=NO
UI_SCOPE=
FRONTEND_BUILD=
DESKTOP_SMOKE_TEST=
RESPONSIVE_CHECK=
ARABIC_CHECK=
ENGLISH_CHECK=
GITHUB_FUNCTIONS_PRESERVED=
FINAL_LOCAL_SHA=
WORKING_TREE=
DEPLOYMENT=
PUSH_PERFORMED=NO
BLOCKER=
```

---

# Stop Condition

This patch is complete when the GitHub Developer Hub page has the premium visual hierarchy described above, all existing GitHub functions remain intact, frontend build passes, the result is deployed locally/production per existing TOS flow, and one local commit is ready for manual review/push.
