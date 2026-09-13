# TOS Task Details V2.11G — Waiting Client Conversation Below Description

VERSION=TOS_TASK_DETAILS_V2_11G
PATCH=TOS-UXUI-TASK-DETAILS-V2-11G-WAITING-CLIENT-CONVERSATION-BELOW-DESCRIPTION
BASELINE_CHAIN=TOS_TASK_DETAILS_V2_11F_R2
BASE_TOS_COMMIT=LIVE_AHEAD_OF_GITHUB_MAIN_ALLOWED
MICRO_STEP=WAITING_CLIENT_CONVERSATION_REORDER_ONLY
PATCH_SCOPE=JSX_RELOCATION_PLUS_MINIMAL_LAYOUT_CSS

## Goal
Move the existing `Waiting Client conversation` / `TOS ↔ TCRM` card out of its current position above the Task Details tabs and place it directly after the Overview `Description` section in the main Task Details column.

Target reading order:

1. Hero / task summary
2. Primary tabs
3. Description / Editor
4. Waiting Client Conversation
5. Remaining Overview content

The Right Rail stays beside the main column and is not rewritten.

## Important live-baseline note
The currently running Waiting Client conversation feature is ahead of `TOS/main`, so this installer intentionally does **not** reconstruct the conversation from GitHub source. It locates the existing live conversation block on `/var/www/TOS`, moves that exact JSX block, and preserves all of its current props, message rendering, reply logic, integration logic, and permissions.

If the live source shape cannot be identified unambiguously, the installer stops. There is no manual fallback.

## Scope
- Move the existing conversation block only.
- Add one non-functional wrapper marker:
  `data-tos-waiting-client-conversation="below-description"`
- Add minimal width/margin layout CSS for the new position.
- Preserve Description editor.
- Preserve TOS ↔ TCRM conversation behavior and data.
- Preserve Hero.
- Preserve Primary Tabs.
- Preserve Right Rail.
- Preserve TCS and Ramzy.
- No API/DB/permission/business-logic changes.

## Apply
```bash
python3 \
/var/www/TOS-Patchs/TOS-UXUI-TASK-DETAILS-V2-11G-WAITING-CLIENT-CONVERSATION-BELOW-DESCRIPTION/apply_tos_task_details_v2_11g_waiting_client_conversation_below_description.py \
/var/www/TOS
```

## Mandatory Visual QA
Use an existing task that actually has a Waiting Client conversation.

Light Mode:
- 1664x936
- 1366x768

Verify:
- Conversation is NOT between Hero and Tabs anymore.
- Description appears before Conversation.
- Conversation appears immediately after Description in the main column.
- Right Rail stays separate with no overlap.
- Conversation message bubbles/content remain visible.
- No task data is modified.

PUSH=NO until ChatGPT visually approves screenshots.
