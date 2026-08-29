# TOS GitHub Sync Luxury UI V4 — SAFE STYLING ONLY

## Target
Repository: `/var/www/TOS`

Required baseline:
`66f7dd32794e9c5bb42dd63222b9a0bc5d4a7ee9`

Target page:
`/settings#github`

Primary file:
`frontend/src/components/GithubAdvancedAdmin.jsx`

## Objective
Make the existing GitHub Sync page look ultra-premium, luxury, executive, and visually close to the approved mockup direction WITHOUT changing its structure, behavior, or functionality.

This is a SKIN/STYLING patch only.

## NON-NEGOTIABLE SAFETY CONTRACT

DO NOT:
- rewrite the component
- replace the return tree
- delete JSX blocks
- move/reorder sections
- remove buttons
- remove navigation items
- remove repository status
- remove last review
- remove last push
- remove quick steps
- remove changes by type
- remove recent sync activity
- remove repository information
- remove connection settings
- remove logs & advanced actions
- change any handler
- change any API call
- change any state/effect
- change any condition
- change any business logic
- change any text content except tiny cosmetic label capitalization if strictly necessary
- touch backend / Prisma / DB / Auth
- add fake data
- add new dependencies
- use a Python script to rewrite the whole file

ALLOWED:
- edit existing `className` values
- adjust Tailwind utility classes
- refine spacing, radius, borders, shadows, typography, gradients, opacity, hover/focus states
- refine existing visual wrappers without changing hierarchy
- adjust icon sizing/color classes only
- improve responsive utility classes only

## STRUCTURE LOCK
The DOM/JSX structure must stay functionally identical.

Before editing, record:
- file line count
- count of `<section`
- count of `<article`
- count of `<Button`
- count of `onClick=`
- count of `useState(`
- count of `useEffect(`

After editing, all structural counts must match baseline exactly.

If any structural count changes, STOP and revert local changes.

## LINE DELTA GUARD
Final file line count must remain within ±15 lines of baseline.

If line delta exceeds ±15:
STOP and revert.

## DIFF GUARD
Before commit, inspect:

`git diff -- frontend/src/components/GithubAdvancedAdmin.jsx`

The diff must be overwhelmingly styling/class changes.

If the diff shows deleted JSX sections, deleted handlers, deleted conditions, altered API calls, altered state/effect logic, or large block replacement:
STOP and revert.

## VISUAL DIRECTION
Match the approved luxury concept as closely as possible while preserving the current exact layout.

### Dark mode
- background: near-black / deep navy-black
- premium layered surfaces
- thin champagne-gold borders/highlights
- subtle radial warmth, no neon
- soft inner highlights
- restrained green for healthy states
- refined amber/gold primary CTA
- elegant typography hierarchy
- expensive executive SaaS feeling

### Light mode
- warm ivory / pearl / soft stone
- champagne gold accents
- subtle emerald healthy states
- low-noise borders
- soft depth and premium shadows
- no harsh pure-white flatness

## Styling Targets

### 1. Hero
Keep same hero content and structure.
Make it visibly more premium with:
- stronger title hierarchy
- richer dark/light surfaces
- subtle gold edge/light treatment
- better connected/repository chips
- more polished spacing

### 2. Sidebar
Keep all existing items.
Improve:
- active state
- premium badge
- account card
- hover/focus
- dark/light consistency

### 3. Repository Status / Last Review / Last Push
Keep exact content and actions.
Upgrade:
- card depth
- micro-borders
- icon treatment
- status chips
- value emphasis

### 4. Quick Steps
Keep exact four steps and all logic.
Make stepper feel luxurious using styling only:
- better spacing
- connected visual rhythm
- current/completed/locked differentiation
- refined amber primary action

### 5. Changes by Type
Keep same data and structure.
Improve donut/card styling only.

### 6. Recent Sync Activity
Keep same rows and data.
Improve row separators, indicators, spacing, status treatment.

### 7. Repository Information
Keep all fields.
Make it look like a high-end metadata rail.

### 8. Connection Settings
Keep exact details structure and all controls.
Premium styling only.

### 9. Logs & Advanced Actions
Keep exact functionality and controls.
Premium styling only.

## Color Guidance
Use existing Tailwind classes only.

Dark:
- `#070A0F` feel
- `#0D121B` feel
- zinc/slate near-black surfaces
- amber/champagne accents
- emerald success

Light:
- warm off-white / stone / ivory
- amber/champagne outlines and CTAs
- emerald success
- muted slate text

Do not introduce loud gradients, neon glow, or gaming aesthetics.

## Responsive
Do not change breakpoint logic materially.
Only improve class utilities if needed.
No horizontal overflow.

## Validation — SHORT RUN ONLY
Target total execution time: 10–15 minutes.

Run only:
1. baseline structural counts
2. styling edits
3. post-edit structural counts
4. `git diff --check`
5. one frontend build
6. one smoke check of `/settings#github`

Do NOT run broad tests.
Do NOT scan the whole repository.

## Acceptance Gate
Must satisfy ALL:
- all structural counts unchanged
- line delta within ±15
- no section removed
- no button removed
- no handler/API/state/effect changed
- dark mode visibly more premium
- light mode visibly more premium
- build passes
- page renders fully

If any acceptance item fails: revert local changes and report BLOCKED.

## Commit
If and only if all gates pass, create ONE local commit:

`feat(ui): luxury polish github sync v4`

DO NOT PUSH.

## Final Response
Return only:

BASELINE_LINE_COUNT=
FINAL_LINE_COUNT=
LINE_DELTA=
SECTION_COUNT_BEFORE=
SECTION_COUNT_AFTER=
ARTICLE_COUNT_BEFORE=
ARTICLE_COUNT_AFTER=
BUTTON_COUNT_BEFORE=
BUTTON_COUNT_AFTER=
ONCLICK_COUNT_BEFORE=
ONCLICK_COUNT_AFTER=
STATE_COUNT_BEFORE=
STATE_COUNT_AFTER=
EFFECT_COUNT_BEFORE=
EFFECT_COUNT_AFTER=
FILES_CHANGED=
BUILD_STATUS=
SMOKE_TEST=
FINAL_LOCAL_SHA=
WORKING_TREE=
PUSH_PERFORMED=NO
BLOCKER=
