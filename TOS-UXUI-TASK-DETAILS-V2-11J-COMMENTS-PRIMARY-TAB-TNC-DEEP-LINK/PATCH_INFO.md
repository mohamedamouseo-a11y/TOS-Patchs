# TOS Task Details V2.11J — Comments Primary Tab + TNC Deep Link

VERSION=TOS_TASK_DETAILS_V2_11J
PATCH=TOS-UXUI-TASK-DETAILS-V2-11J-COMMENTS-PRIMARY-TAB-TNC-DEEP-LINK
BASELINE_CHAIN=TOS_TASK_DETAILS_V2_11I
BASE_TOS_COMMIT=29f9e8865fec1acd3468f9f94d236231c1569ebf
MICRO_STEP=COMMENTS_PRIMARY_TAB_AND_TNC_DEEP_LINK
PATCH_SCOPE=FRONTEND_JSX_ONLY

## Objective
Promote the existing Task Details **Comments** tab to the permanent primary tab row and wire existing TNC task-comment notifications so opening a comment notification lands directly on that task's Comments tab.

## Changes
- Comments is always visible as a primary tab directly after Overview.
- Existing comments count badge is preserved.
- Existing comments panel/editor/add-comment behavior is preserved byte-for-byte.
- More Actions gates **Time only**; closing More never ejects Overview/Comments/Checklist/Attachments/Activity/Subtasks.
- TNC task notifications whose explicit target tab is `comments`, or whose notification type contains `COMMENT`, open Task Details with Comments active.
- Other TNC task notifications continue to open Overview.
- Manual task opens continue to open Overview.

## Protected / unchanged
- backend / database / API routes
- permissions/auth
- addComment submit logic and comments editor behavior
- TCRM Waiting Client Conversation
- Task Details Hero
- Description/editor/content
- Right Rail
- TCS
- Ramzy
- task data

## Target source files
- `frontend/src/App.jsx`
- `frontend/src/components/ProfessionalTaskBoard.jsx`

## Installer
```bash
python3 \
  /var/www/TOS-Patchs/TOS-UXUI-TASK-DETAILS-V2-11J-COMMENTS-PRIMARY-TAB-TNC-DEEP-LINK/apply_tos_task_details_v2_11j_comments_primary_tab_tnc_deep_link.py \
  /var/www/TOS
```

The installer is guarded and transactional: exact anchors are required, the existing `addComment` function is hashed before/after, production manifest paths are validated, frontend build must pass, live frontend is swapped atomically, and source/live rollback occurs on failure.

PUSH=NO
