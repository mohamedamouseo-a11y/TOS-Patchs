# TOS Task Details V2.11H — Remove Description From Hero

VERSION=TOS_TASK_DETAILS_V2_11H
PATCH=TOS-UXUI-TASK-DETAILS-V2-11H-REMOVE-DESCRIPTION-FROM-HERO
BASELINE_CHAIN=TOS_TASK_DETAILS_V2_11G
BASE_TOS_COMMIT=LIVE_AHEAD_OF_GITHUB_MAIN_ALLOWED
MICRO_STEP=HERO_DESCRIPTION_REMOVAL_ONLY
PATCH_SCOPE=PROFESSIONAL_TASK_BOARD_JSX_ONLY

## Goal
Remove the task Description text from the Task Details Hero/header area only.

Required result:
- Hero keeps task label/title and the existing controls/metadata.
- No Description text is rendered under/beside the task title in the Hero.
- Overview -> Description remains present and unchanged.
- Existing Description editor/content is preserved.
- Waiting Client Conversation placement from V2.11G is preserved.
- Right Rail, tabs, TCS and Ramzy are preserved.

## Implementation
The installer works against the current live `/var/www/TOS` source. It removes the single Hero paragraph using `tos-task-header-description`, removes the now-unused Hero-only description summary variables, builds and deploys, and rolls back on failure.

It does NOT remove or alter `draft.description` data and does NOT modify the Overview Description editor.

## Apply
```bash
python3 \
/var/www/TOS-Patchs/TOS-UXUI-TASK-DETAILS-V2-11H-REMOVE-DESCRIPTION-FROM-HERO/apply_tos_task_details_v2_11h_remove_description_from_hero.py \
/var/www/TOS
```

## Visual QA
Light Mode at 1664x936 and 1366x768:
1. Hero screenshot: title visible, Description text absent from Hero.
2. Overview screenshot: Description section/editor still visible and content preserved.

PUSH=NO until ChatGPT visual approval. Final source push is performed by the user.