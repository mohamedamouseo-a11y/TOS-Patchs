# TOS Task Details V2.11A R2

VERSION=TOS_TASK_DETAILS_V2_11A_R2
PATCH=TOS-UXUI-TASK-DETAILS-V2-11A-R2-HERO-WIDTH-ONLY
BASELINE_CHAIN=TOS_TASK_DETAILS_V2_11A_R1
MICRO_STEP=HERO_WIDTH_ONLY

## Purpose
Repair only the remaining Hero width failure after V2.11A R1.

## Confirmed root cause
V2.5 still contains a higher-specificity selector:

`body:has(.tos-task-details-reference-v1[data-content-dir]) .tos-task-details-layout`

That rule keeps the Task Details layout in a two-column grid and outranks the lower-specificity R1 `display:block` override. The Hero therefore remains trapped inside the first grid column.

## Scope
- Force the Task Details layout context to a true full-width block with a stronger selector.
- Force the main column to 100% of the Task Details canvas.
- Force the Hero to 100% of that main canvas.

## Frozen
- Task identity placement from R1
- Mountain / quote placement from R1
- Title / subtitle styling
- Four controls
- Tabs
- Description/editor
- Right rail content
- Ramzy
- TCS
- APIs / DB / permissions / task logic / upload / TWS

## QA target
Viewport: 1664x936, Light mode.
The Hero left edge and right edge must align with the complete Task Details content canvas. No visual judgement is required yet for the four controls; those belong to V2.11B.

PUSH=NO until ChatGPT visual QA passes.
