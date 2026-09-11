# TOS Task Details V2.11A R1

VERSION=TOS_TASK_DETAILS_V2_11A_R1
PATCH=TOS-UXUI-TASK-DETAILS-V2-11A-R1-HERO-FULL-CANVAS-PHYSICAL-PLACEMENT
BASELINE_CHAIN=TOS_TASK_DETAILS_V2_11A
MICRO_STEP=HERO_FULL_CANVAS_PHYSICAL_PLACEMENT

## Confirmed V2.11A visual failure

At 1664x936, the Hero still stopped at the old main-column boundary and left the physical right-side rail footprint unused. The task identity also remained displaced inward in RTL.

## Root cause

The V2.6 legacy main/side-rail flex workaround still controlled the outer body geometry. V2.11A tried to extend the Hero arithmetically from inside that constrained column. RTL logical flex-start also prevented a reliable physical-left identity placement.

## R1 repair

- Restore `.tos-task-details-layout` to the canonical full-width block canvas.
- Keep `.tos-task-main-column` full width.
- Set Hero to exactly 100% of that canvas instead of `100% + rail arithmetic`.
- Keep mountain artwork and quote physically RIGHT.
- Place task identity physically LEFT using explicit left/right margins and physical pseudo-element coordinates.
- Preserve Hero height at 254px.

## Frozen scope

No redesign of:
- four Hero controls
- tabs
- Description/editor
- canonical Right Rail cards/content
- Ramzy
- TCS
- APIs / DB / permissions / uploads / task logic / TWS

Ramzy = AI Assistant.
TCS = System Chat.

## Required QA

Viewport: 1664x936
Mode: Light
Screenshot: `TOS__TASK-DETAILS__V2-11A-R1__LIGHT__1664x936__VISUAL-QA.png`

Judge only:
- Hero reaches the full Task Details content canvas.
- Task icon/title/subtitle are physically LEFT.
- Mountain/quote remain physically RIGHT.
- No clipping or title/quote overlap.

Do not judge or redesign the four controls in this micro-step.
PUSH=NO until ChatGPT visual approval.
