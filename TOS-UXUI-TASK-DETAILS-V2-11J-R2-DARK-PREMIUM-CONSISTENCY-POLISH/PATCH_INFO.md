# TOS Task Details V2.11J_R2 — Dark Premium Consistency Polish

VERSION=TOS_TASK_DETAILS_V2_11J_R2
PATCH=TOS-UXUI-TASK-DETAILS-V2-11J-R2-DARK-PREMIUM-CONSISTENCY-POLISH
BASELINE_CHAIN=TOS_TASK_DETAILS_V2_11J_R1
BASE_TOS_COMMIT=LIVE_AHEAD_OF_GITHUB_MAIN_ALLOWED
MICRO_STEP=DARK_MODE_VISUAL_CONSISTENCY_ONLY
PATCH_SCOPE=CSS_ONLY

## Objective
Polish Task Details dark mode so the Hero, primary tabs, Description/editor and Right Rail use one coherent premium graphite surface system with restrained warm-gold accents.

## Required visual outcome
- Dark mode only; light mode is untouched.
- Remove the bright white primary-tabs strip in dark mode.
- Keep the active tab readable with a restrained warm-gold state.
- Convert Hero controls to dark graphite cards instead of bright white blocks.
- Remove the black rectangular background behind the task title.
- Keep Description/editor hierarchy consistent and readable.
- Harmonize Right Rail cards/buttons with the same dark surface/border system.
- Preserve V2.11J_R1 responsive tab behavior and all six primary tabs.
- Preserve Comments, Notification Center routing, Hero structure, Description logic, Waiting Client Conversation, Right Rail logic, TCS and Ramzy.

## Installer
```bash
python3 \
  /var/www/TOS-Patchs/TOS-UXUI-TASK-DETAILS-V2-11J-R2-DARK-PREMIUM-CONSISTENCY-POLISH/apply_tos_task_details_v2_11j_r2_dark_premium_consistency_polish.py \
  /var/www/TOS
```

PUSH=NO
