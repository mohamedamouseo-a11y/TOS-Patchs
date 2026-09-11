# TOS Task Details V2.10D

VERSION=TOS_TASK_DETAILS_V2_10D

PATCH=TOS-UXUI-TASK-DETAILS-V2-10D-HERO-BOTTOM-SPACING-GLOBAL-ASSISTANT-COLLISION-FIX

BASELINE_CHAIN=TOS_TASK_DETAILS_V2_9D

## Visual scope only

1. Add 12px of real Hero height/bottom breathing room so all four approved Hero controls show their complete lower border/radius instead of sitting on the clipped Hero edge.
2. Keep the canonical Overview rail aligned after the small Hero height increase.
3. While full-page Task Details is open at the reference desktop breakpoint, visually dock the existing global TCS launcher and Ramzy launcher into a safe topbar zone, overriding only their saved inline left/top presentation so they cannot cover Tags, the Task Details TCS Assistant card, the editor, or the footer.

## Frozen scope

- Hero title, mountain, quote, four-control identities and task values.
- Tabs and Overview content.
- Description/editor physical LEFT.
- Canonical Right Rail physical RIGHT and its existing Quick Actions / Task Information / Tags / Task Details TCS Assistant content.
- All Task APIs, data contracts, permissions, business logic, uploads, TWS, Ramzy logic, TCS logic, chat behavior and persistence.
- No JSX/React source mutation. CSS-only.

## Installer guarantees

The installer requires the V2.9D runtime lineage, guards the real Task Details/TCS/Ramzy selectors, hashes React sources before/after, backs up the Task Details stylesheet and live build, runs the production frontend build, stages and swaps the published build, verifies runtime markers, and rolls back on failure.

## Visual QA

Viewport: `1664x936`

Screenshot exact name:
`TOS__TASK-DETAILS__V2-10D__LIGHT__1664x936__VISUAL-QA.png`

No push before ChatGPT visual approval.
