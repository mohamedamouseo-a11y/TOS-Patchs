# TOS Task Details V2.11I — Top Header Greeting/Profile Widget Fix

VERSION=TOS_TASK_DETAILS_V2_11I
PATCH=TOS-UXUI-TASK-DETAILS-V2-11I-TOP-HEADER-GREETING-PROFILE-WIDGET-FIX
BASELINE_CHAIN=TOS_TASK_DETAILS_V2_11H
BASE_TOS_COMMIT=LIVE_AHEAD_OF_GITHUB_MAIN_ALLOWED
MICRO_STEP=TOP_HEADER_GREETING_PROFILE_WIDGET_FIX_ONLY
PATCH_SCOPE=TASK_DETAILS_RAMZY_CLOSED_LAUNCHER_CSS_ONLY

## Why
V2.11H achieved its intended Task Details change, but visual QA exposed a separate responsive defect in the global top-header assistant presentation:
- At desktop width the Ramzy greeting could shrink into a narrow vertical text stack.
- The avatar/greeting composition could look detached from the top-header band.
- The defect was visible around the 1664px reference viewport and required regression protection at 1366px.

## Goal
Keep the existing Ramzy avatar/greeting presentation clean, horizontal and contained in the top-header safe zone while Task Details V2 is mounted.

Required result:
- 1664x936: Ramzy avatar is fully inside the header safe band.
- 1664x936: greeting/identity copy is horizontal and readable, never a vertical word stack.
- 1366x768: compact avatar-only treatment remains inside the header; greeting/label stays hidden as previously approved.
- No collision with TCS, search, user profile, breadcrumbs or Task Details content.
- Existing user profile block remains visually unchanged.

## Protected scope
Do not change:
- Task Details Hero/title/controls.
- Description section/editor/content.
- Primary Tabs.
- Right Rail.
- Waiting Client Conversation.
- TCS component or its behavior.
- Ramzy component/JS, open panel, chat, drag, close or conversation behavior.
- APIs, DB, permissions, task data or backend.

## Implementation
CSS-only patch appended to `frontend/src/styles/taskDetailsCanonicalReferenceV2.css`.
The patch uses the existing Task Details scope and only targets the closed Ramzy launcher presentation classes.

## Apply
```bash
python3 \
/var/www/TOS-Patchs/TOS-UXUI-TASK-DETAILS-V2-11I-TOP-HEADER-GREETING-PROFILE-WIDGET-FIX/apply_tos_task_details_v2_11i_top_header_greeting_profile_widget_fix.py \
/var/www/TOS
```

## Visual QA
Light Mode mandatory:
1. 1664x936 — full Task Details page/top header.
2. 1664x936 — top-header close detail.
3. 1366x768 — full Task Details page/top header.
4. 1366x768 — top-header close detail.

PUSH=NO until ChatGPT visually approves the screenshots.
