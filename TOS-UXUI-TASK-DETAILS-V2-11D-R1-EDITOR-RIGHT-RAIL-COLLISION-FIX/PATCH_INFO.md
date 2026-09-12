# TOS Task Details V2.11D_R1

VERSION=TOS_TASK_DETAILS_V2_11D_R1
PATCH=TOS-UXUI-TASK-DETAILS-V2-11D-R1-EDITOR-RIGHT-RAIL-COLLISION-FIX
BASELINE_CHAIN=TOS_TASK_DETAILS_V2_11D
MICRO_STEP=EDITOR_RIGHT_RAIL_COLLISION_FIX_ONLY

## Scope
CSS-only visual micro-fix for the Overview Description/Editor physical width at desktop breakpoints.

- Preserve the existing V2.11D Description/Editor styling and logic.
- Keep the Description/Editor physically LEFT of the existing absolute Right Rail.
- Remove all Editor/Right-Rail overlap at the 1664x936 reference viewport.
- Keep the editor shell, toolbar, content and save action inside the main column.
- Compact the existing toolbar controls slightly at desktop width so the complete toolbar remains usable inside the corrected main column.
- Do not alter the Right Rail itself.
- Do not alter Hero, controls B/B1/B2/B3, tabs V2.11C, backend, APIs, permissions, uploads or TWS.
- ProfessionalTaskBoard.jsx and taskBoardParts.jsx must remain byte-identical.

RUNTIME=--tos-task-details-v2-11d-r1-editor-right-rail-collision-fix-runtime
REFERENCE_VIEWPORT=1664x936
PUSH=NO
