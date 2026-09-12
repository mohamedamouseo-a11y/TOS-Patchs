# TOS Task Details V2.11D — Description / Editor Premium Lock

VERSION=TOS_TASK_DETAILS_V2_11D
PATCH=TOS-UXUI-TASK-DETAILS-V2-11D-DESCRIPTION-EDITOR-PREMIUM-LOCK
BASELINE_CHAIN=TOS_TASK_DETAILS_V2_11C
MICRO_STEP=DESCRIPTION_EDITOR_ONLY

## Scope
Only the Overview Description panel and existing PremiumTaskRichTextEditor presentation.

### Target
- Premium Description panel shell.
- Clean title/action header.
- Restore the existing editor header + formatting toolbar that canonical V2 had visually hidden.
- Premium toolbar controls, editor canvas and statistics footer.
- Preserve existing Edit/Fullscreen/Save actions and all rich-text behavior.
- Preserve Arabic/English content direction from the existing editor.

## Frozen
Hero, Task Identity, four Hero controls, B1 Status/Priority custom dropdowns, B2 Due Date calendar, B3 Assignees selector, V2.11C Primary Tabs, Right Rail, Quick Actions, Task Information, Tags, Ramzy, TCS, APIs, DB, permissions, task business logic, upload logic and TWS.

## Technical boundary
CSS-only. ProfessionalTaskBoard.jsx and taskBoardParts.jsx must remain byte-identical.

Visual QA viewport: 1664x936, Light mode.
PUSH=NO until ChatGPT visual QA passes.
