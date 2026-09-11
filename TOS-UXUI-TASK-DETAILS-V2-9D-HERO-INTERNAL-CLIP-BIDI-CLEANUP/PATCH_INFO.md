# TOS_TASK_DETAILS_V2_9D

PATCH=TOS-UXUI-TASK-DETAILS-V2-9D-HERO-INTERNAL-CLIP-BIDI-CLEANUP
BASELINE_CHAIN=TOS_TASK_DETAILS_V2_8D
MODE=CSS_ONLY
REFERENCE_VIEWPORT=1664x936

## Fix scope
- Keep all four Hero control cards fully inside the Hero boundary.
- Restore visible bottom borders/radii; no clipped cards.
- Constrain long mixed Arabic/English Hero summary text to two safe lines.
- Prevent Hero summary text from colliding with the mountain/quote area.

## Frozen scope
- Overview Description/Editor physical LEFT.
- Canonical Right Rail physical RIGHT.
- Quick Actions / Task Information / Tags / TCS Assistant.
- Tabs and their order.
- App shell / sidebar / topbar.
- APIs, DB, permissions, task business logic, upload logic, TWS, Ramzy, TCS logic.

## Visual QA
Screenshot exact name:
`TOS__TASK-DETAILS__V2-9D__LIGHT__1664x936__VISUAL-QA.png`

No push before ChatGPT Visual QA.
