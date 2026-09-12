# TOS Task Details V2.11F_R2 — Editor Toolbar Live Scope Wrap + More Fix

VERSION=TOS_TASK_DETAILS_V2_11F_R2
PATCH=TOS-UXUI-TASK-DETAILS-V2-11F-R2-EDITOR-TOOLBAR-LIVE-SCOPE-WRAP-MORE-FIX
PARENT_PATCH=TOS_TASK_DETAILS_V2_11F_R1
BASELINE_CHAIN=TOS_TASK_DETAILS_V2_11E_R1
BASE_TOS_COMMIT=cd019d60434943d625fde9d2ea2ddee7e68d2028
MICRO_STEP=EDITOR_TOOLBAR_LIVE_SCOPE_WRAP_MORE_FIX_ONLY
PATCH_SCOPE=CSS_ONLY

## Why R2 exists
V2.11F_R1 built and deployed successfully, but authenticated visual QA proved its CSS had no visible effect: the toolbar remained in one nowrap row, right-side controls stayed clipped, More/Less was not visible, and the closed/open state rules did not apply.

The source audit identified the exact reason. R1 targeted a root selector that does not exist in the live Task Details DOM:

`.tos-task-details-modal[data-task-details-reference="v2"]`

The actual live Task Details root is:

`.tos-task-details-reference-v1[data-content-dir].tos-task-details-reference-v2`

R2 therefore keeps the same presentation-only goal but reanchors every toolbar rule to the real live root with enough specificity to supersede the existing canonical `flex-wrap: nowrap !important` and `overflow-x: auto !important` toolbar rules.

## Scope
- CSS-only Description editor-toolbar presentation correction.
- Use the real live Task Details root/scope.
- Closed decluttered state keeps History, Inline formatting, Lists, Alignment + RTL/LTR, and More available.
- Closed state hides Block/Paragraph/Font/Font Size, Color, and Insert groups.
- Open state restores every actual editor group.
- Toolbar wraps inside the Description column instead of clipping or horizontally scrolling.
- More/Less remains visible and non-shrinking at all audited viewport widths.
- No editor command behavior, save behavior, lists functionality, RTL/LTR functionality, links, images, uploads, undo/redo, API, DB, permissions, Hero, Primary Tabs, Right Rail, TCS, or Ramzy changes.

## Apply
```bash
python3 \
/var/www/TOS-Patchs/TOS-UXUI-TASK-DETAILS-V2-11F-R2-EDITOR-TOOLBAR-LIVE-SCOPE-WRAP-MORE-FIX/apply_tos_task_details_v2_11f_r2_editor_toolbar_live_scope_wrap_more_fix.py \
/var/www/TOS
```

## Mandatory visual QA
Authenticated Light Mode, Task Details → Overview → Description editor:
- 1664x936
- 1440x900
- 1366x768
- 1280x800

At every width capture and verify:
1. More Formatting CLOSED.
2. More Formatting OPEN.

PUSH=NO until ChatGPT inspects valid Task Details screenshots and gives visual approval.
