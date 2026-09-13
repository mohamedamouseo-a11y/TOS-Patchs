# TOS Task Details V2.11J_R1 — Responsive Primary Tabs Fix

VERSION=TOS_TASK_DETAILS_V2_11J_R1
PATCH=TOS-UXUI-TASK-DETAILS-V2-11J-R1-PRIMARY-TABS-RESPONSIVE-FIX
BASELINE_CHAIN=TOS_TASK_DETAILS_V2_11J
BASE_TOS_COMMIT=e417a3255fce78955cb6ce2347995124de6ae2be
MICRO_STEP=PRIMARY_TABS_RESPONSIVE_FIX_ONLY
PATCH_SCOPE=CSS_ONLY

## Objective
Fix the 1366x768 primary Task Details tab clipping introduced after promoting Comments to the primary tab row.

## Required visual outcome
- Keep the primary order: Overview → Comments → Checklist → Attachments → Activity → Subtasks.
- Keep all six tabs visible at 1366x768 without right-edge clipping or overlap.
- Keep Comments permanently visible.
- Keep count badges visible.
- Preserve the 1664x936 composition.
- Do not alter Comments logic, notification routing, More Actions behavior, backend, APIs, task data, Hero, Description, Waiting Client Conversation, Right Rail, TCS or Ramzy.

## Implementation
A narrowly scoped responsive CSS payload activates only between 1024px and 1440px. The tab row becomes an equal-width, non-wrapping flex row with compact spacing; icons/counts remain non-shrinking while labels may ellipsize only if absolutely necessary.

## Installer
```bash
python3 \
  /var/www/TOS-Patchs/TOS-UXUI-TASK-DETAILS-V2-11J-R1-PRIMARY-TABS-RESPONSIVE-FIX/apply_tos_task_details_v2_11j_r1_primary_tabs_responsive_fix.py \
  /var/www/TOS
```

PUSH=NO
