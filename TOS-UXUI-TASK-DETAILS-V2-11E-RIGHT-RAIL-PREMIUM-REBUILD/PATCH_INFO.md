# TOS Task Details V2.11E — Right Rail Premium Rebuild

VERSION=TOS_TASK_DETAILS_V2_11E
PATCH=TOS-UXUI-TASK-DETAILS-V2-11E-RIGHT-RAIL-PREMIUM-REBUILD
BASELINE_CHAIN=TOS_TASK_DETAILS_V2_11D_R1
BASE_TOS_COMMIT=fd10edb0885a148dd53a8cbd6346bbea7f2d6ab4
MICRO_STEP=RIGHT_RAIL_PREMIUM_REBUILD_ONLY

## Scope
- Rebuild the existing Overview Right Rail visually only.
- Upgrade Quick Actions, Task Information, Tags, and TCS Assistant card.
- Harden physical rail/main-column geometry for 1440, 1366, and 1280 widths.
- Preserve the V2.11D_R1 editor/rail collision fix.
- CSS-only patch. No JSX, task logic, Rich Text logic, API, DB, permission, TCS logic, or Ramzy logic changes.

## Apply
```bash
python3 \
TOS-UXUI-TASK-DETAILS-V2-11E-RIGHT-RAIL-PREMIUM-REBUILD/apply_tos_task_details_v2_11e_right_rail_premium_rebuild.py \
/var/www/TOS
```

## Visual QA
Primary viewport: 1664x936, Light Mode, Task Details → Overview.
Also inspect responsive geometry at widths 1440, 1366, and 1280.

PASS requires:
- Right Rail is visually premium, calm, compact, and aligned.
- Quick Actions, Task Information, Tags, and TCS card are clearly separated and balanced.
- Description/Editor remains physically left; Right Rail remains physically right.
- Zero overlap at 1664 / 1440 / 1366 / 1280.
- Hero B1/B2/B3, Primary Tabs V2.11C, Description Editor V2.11D/R1 remain unchanged.
- No task behavior or assistant logic changes.

PUSH=NO until visual approval.
