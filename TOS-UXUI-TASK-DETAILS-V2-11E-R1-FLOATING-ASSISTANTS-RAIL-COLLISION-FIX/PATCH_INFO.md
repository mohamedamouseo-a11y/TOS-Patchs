# TOS Task Details V2.11E_R1 — Floating Assistants / Rail Collision Fix

VERSION=TOS_TASK_DETAILS_V2_11E_R1
PATCH=TOS-UXUI-TASK-DETAILS-V2-11E-R1-FLOATING-ASSISTANTS-RAIL-COLLISION-FIX
BASELINE_CHAIN=TOS_TASK_DETAILS_V2_11E
BASE_TOS_COMMIT=fd10edb0885a148dd53a8cbd6346bbea7f2d6ab4
MICRO_STEP=FLOATING_ASSISTANTS_RAIL_COLLISION_FIX_ONLY

## Why
V2.11E passed the rail/editor/tabs geometry checks, but real screenshots showed
the global TCS and Ramzy launchers covering the Right Rail at 1366x768 and
1280x800. 1664x936 and 1440x900 were already clean.

## Scope
- CSS-only responsive placement/presentation adjustment for global TCS + Ramzy launchers.
- Active only from 1280px through 1366px while Task Details V2 is mounted.
- Dock both launchers into the top-bar free zone.
- Compact launcher labels at those widths so both assistants fit without covering task content.
- Preserve assistant click/open logic; no TCS or Ramzy JS changes.
- Do not alter Right Rail cards, Description/Editor, Primary Tabs, Hero controls, APIs, DB, permissions, or task logic.

## Apply
```bash
python3 \
TOS-UXUI-TASK-DETAILS-V2-11E-R1-FLOATING-ASSISTANTS-RAIL-COLLISION-FIX/apply_tos_task_details_v2_11e_r1_floating_assistants_rail_collision_fix.py \
/var/www/TOS
```

## Visual QA
Mandatory Light Mode screenshots:
- 1366x768
- 1280x800

Regression screenshot:
- 1664x936

PASS requires:
- TCS launcher does not cover any Right Rail card.
- Ramzy launcher/greeting does not cover any Right Rail card.
- TCS and Ramzy do not overlap each other.
- No top-bar search/profile collision.
- V2.11E Right Rail remains visually unchanged.
- Editor/Rail and Tabs/Rail remain zero-overlap.
- 1664x936 remains unchanged from the approved V2.11E view.

PUSH=NO until ChatGPT reviews the actual screenshots.
