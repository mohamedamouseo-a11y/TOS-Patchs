# TOS GitHub Sync Premium UI V2 — Mandatory Visual Overhaul

## Target
- App repo: `mohamedamouseo-a11y/TOS`
- Server working tree: `/var/www/TOS`
- Page: `/settings#github`
- Primary component: `frontend/src/components/GithubAdvancedAdmin.jsx`
- Required baseline: `66f7dd32794e9c5bb42dd63222b9a0bc5d4a7ee9`

## Why V2 exists
The current baseline already contains a first-generation premium layout (left rail, hero, status cards, workflow, donut, activity timeline). Merely detecting those elements is NOT completion.

V2 requires a clearly visible redesign of the existing page. The baseline file MUST change.

## Non-negotiable visual delta
After implementation, a screenshot of `/settings#github` must look materially different from baseline at first glance.

The following current presentation must NOT remain unchanged:
- narrow utility left rail as the dominant navigation element
- generic white/black cards with repetitive rounded containers
- small metric chips packed inside cards
- current hero composition
- current review/push card composition
- current flat operational hierarchy

## Direction
Create an executive-grade "Git Operations Command Center" with a restrained luxury aesthetic.

### Design language
- Obsidian / graphite surfaces
- Champagne-gold accent used sparingly
- Deep layered panels rather than repeated generic cards
- Thin metallic borders and subtle inner highlights
- Stronger typography scale and more editorial spacing
- Compact but cinematic hero
- No gaming neon
- No excessive glow
- No excessive glassmorphism
- No generic SaaS dashboard look

Support both TOS dark and light themes; dark is the hero reference.

## Required new architecture

### 1. Full-width Command Hero
Replace the current hero with a stronger full-width command header.

Must contain:
- GitHub mark / GitFork icon in a premium framed emblem
- eyebrow `TOS DEVELOPER HUB`
- large `Advanced GitHub Sync`
- repository identity and active branch
- live system state block on the opposite side
- compact last sync information
- primary safe action: Refresh

The hero should feel like the top of an operations console, not a settings card.

### 2. Repository Pulse Bar
Directly below hero, create one continuous horizontal health strip rather than four tiny chips.

Sections:
- Ahead
- Behind
- Working Tree
- Remote Guard
- Branch Guard

Each section needs icon + value + label + semantic state.
Use separators inside ONE unified surface.

### 3. Review / Push Command Deck
This becomes the visual center of the page.

Two-column command deck:

Left — Safe Review
- current review state
- expected action
- files affected
- review CTA

Right — Execution
- commit message input
- reviewed fingerprint/state
- execute CTA
- destructive/safety lock state

Between them show an explicit directional progression:
`Inspect → Review → Approve → Execute`

Dangerous execute CTA must stay visually locked until review is valid.

### 4. Change Intelligence Bento
Replace the current generic changes card with a bento block:
- dominant total changes tile
- Added tile
- Modified tile
- Deleted tile
- compact CSS donut/ring only if useful
- repository cleanliness indicator

No new chart dependency.

### 5. Activity Stream
Create a sophisticated compact timeline with:
- status dot
- operation/action
- timestamp
- short detail
- current running operation visually distinct

Use a single panel with internal separators, not separate cards per event.

### 6. Connection Drawer
Connection settings should NOT visually compete with operational controls.

Move them into a premium collapsible/drawer-style section lower on the page.
Must preserve:
- PAT visibility toggle
- verify
- repo selector
- branch selector
- local path
- save
- disconnect

Disconnect must be isolated in a clearly separated danger zone.

### 7. Remove redundant chrome
Reduce repeated borders, badges, and rounded boxes.
Create hierarchy using surface levels, spacing, typography, separators and only strategic borders.

## Styling constraints
- Prefer Tailwind/classes already used by the project.
- No new UI framework.
- No new chart package.
- No backend changes.
- No API changes.
- No auth changes.
- No Prisma/database changes.
- No business-logic refactor.
- Existing Arabic/English behavior must remain.
- Existing RTL behavior must remain.
- No horizontal overflow at 1440, 1280, 1024, tablet, mobile.

## Mandatory implementation proof
Completion is INVALID if `GithubAdvancedAdmin.jsx` is byte-identical to baseline.

Required:
- `git diff -- frontend/src/components/GithubAdvancedAdmin.jsx` must show substantive JSX/class/layout changes.
- At least the Hero, Pulse Bar, Command Deck and Connection section must have changed structure/classes.
- Do not report "already implemented" because equivalent features exist; V2 explicitly redesigns their presentation.

## Functional preservation
Do not alter:
- `api.github.*` endpoint usage
- repository/branch loading logic
- token verification logic
- operation polling
- review fingerprints
- review/execute safety gates
- sessionStorage recovery
- source download
- disconnect semantics
- error sanitization

## Short execution contract
Target 10–15 minutes.

Do NOT:
- scan entire repository
- run full test suite
- investigate unrelated warnings
- touch backend
- push

Workflow:
1. Read this patch.
2. Inspect only `GithubAdvancedAdmin.jsx` and existing primitives it directly uses.
3. Implement the V2 visual overhaul.
4. Run one frontend build.
5. Smoke-test `/settings#github`.
6. Create one local commit.
7. Deploy frontend.
8. Stop.

## Acceptance
- Page is materially different from baseline screenshot/code.
- Hero is redesigned.
- Unified repository pulse bar exists.
- Review/Push command deck exists.
- Changes bento exists.
- Activity stream refined.
- Connection settings visually demoted into collapsible/drawer section.
- Dark and light modes remain readable.
- Arabic and English remain readable.
- Existing GitHub functions/handlers preserved.
- Frontend build passes.
- No backend changes.
- No push.

## Commit
Create exactly one local commit:
`feat(ui): overhaul github sync command center v2`

DO NOT PUSH.

## Return only
```text
FILES_CHANGED=
VISUAL_DELTA=PASS/FAIL
HERO_REDESIGNED=PASS/FAIL
PULSE_BAR=PASS/FAIL
COMMAND_DECK=PASS/FAIL
CHANGES_BENTO=PASS/FAIL
CONNECTION_DRAWER=PASS/FAIL
FUNCTIONS_PRESERVED=PASS/FAIL
BUILD_STATUS=
DEPLOYMENT=
FINAL_LOCAL_SHA=
WORKING_TREE=
PUSH_PERFORMED=NO
BLOCKER=
```
