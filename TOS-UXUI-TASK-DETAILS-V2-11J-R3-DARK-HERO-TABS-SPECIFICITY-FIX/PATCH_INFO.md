# TOS Task Details V2.11J_R3 — Dark Hero + Tabs Specificity Fix

VERSION=TOS_TASK_DETAILS_V2_11J_R3
PATCH=TOS-UXUI-TASK-DETAILS-V2-11J-R3-DARK-HERO-TABS-SPECIFICITY-FIX
BASELINE_CHAIN=TOS_TASK_DETAILS_V2_11J_R2
PATCH_SCOPE=CSS_ONLY

## Why R3 exists
V2.11J_R2 visually fixed the title background, Description/editor and Right Rail, but two bright Light-mode surfaces remained in Dark Mode:

1. Hero control cards (Assignees / Status / Priority / Due date) remained white.
2. The primary tabs strip remained white.

The live stylesheet contains later high-specificity V2.11B/V2.11C selectors using `body:has(...)` plus `!important`. Those selectors outrank the R2 dark selectors. R3 does not redesign anything; it only adds stronger dark-mode overrides that match the actual live selector chain.

## Frozen / unchanged
- Light Mode
- Hero geometry/order
- Primary tab order and R1 responsiveness
- Comments logic/panel/editor
- Description/editor styling already fixed by R2
- Right Rail styling already fixed by R2
- Waiting Client Conversation
- TNC routing
- TCS / Ramzy
- backend / API / database / permissions
- App.jsx / ProfessionalTaskBoard.jsx

## Required visual outcome
- Dark Hero control cards are graphite, not white.
- Assignee, Status, Priority and Due-date inner controls are dark.
- Status keeps a restrained warm-gold tint only.
- Primary tabs container is graphite, not white.
- Active tab keeps restrained warm-gold state.
- At 1366px all six tabs remain visible with no clipping/overlap.

## Installer
```bash
python3 \
  /var/www/TOS-Patchs/TOS-UXUI-TASK-DETAILS-V2-11J-R3-DARK-HERO-TABS-SPECIFICITY-FIX/apply_tos_task_details_v2_11j_r3_dark_hero_tabs_specificity_fix.py \
  /var/www/TOS
```

Fallback patch repo path is allowed if `/var/www/TOS-Patchs` does not exist.

PUSH=NO
