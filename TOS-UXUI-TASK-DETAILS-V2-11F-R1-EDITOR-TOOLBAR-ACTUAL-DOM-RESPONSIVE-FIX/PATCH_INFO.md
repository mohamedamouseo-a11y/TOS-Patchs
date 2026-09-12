# TOS Task Details V2.11F_R1 — Editor Toolbar Actual DOM Alignment Fix

VERSION=TOS_TASK_DETAILS_V2_11F_R1
PATCH=TOS-UXUI-TASK-DETAILS-V2-11F-R1-EDITOR-TOOLBAR-ACTUAL-DOM-RESPONSIVE-FIX
PARENT_PATCH=TOS_TASK_DETAILS_V2_11F
BASELINE_CHAIN=TOS_TASK_DETAILS_V2_11E_R1
BASE_TOS_COMMIT=cd019d60434943d625fde9d2ea2ddee7e68d2028
MICRO_STEP=EDITOR_TOOLBAR_ACTUAL_DOM_RESPONSIVE_FIX_ONLY
PATCH_SCOPE=CSS_ONLY

## Why R1 exists
V2.11F correctly targeted toolbar clipping/wrapping, but its installer and payload assumed non-existent editor group classes (`tos-editor-group-font`, `tos-editor-group-basic`, `tos-editor-group-direction`). The declared baseline actually uses:
- `tos-editor-group-history`
- `tos-editor-group-block` (Paragraph + Font + Font Size)
- `tos-editor-group-inline` (Bold/Italic/Underline/Strike)
- `tos-editor-group-list`
- `tos-editor-group-align` (alignment + RTL/LTR)
- `tos-editor-group-color`
- `tos-editor-group-insert`

The failed V2.11F installer stopped before modifying source/build/live output. R1 is therefore applied directly on the approved V2.11E_R1 baseline and does not require the V2.11F runtime marker.

## Scope
- CSS-only presentation fix.
- No editor command, save, list, RTL/LTR, link, image, upload, undo/redo, API, DB, permission, Hero, Tabs, Right Rail, TCS or Ramzy logic changes.
- Closed decluttered state keeps: History, Inline formatting, Lists, Alignment + RTL/LTR, More.
- Closed state hides: Block/Font/Size, Color, Insert.
- Open state restores every actual toolbar group and wraps them inside the Description column.
- More remains visible/clickable at all audited widths.

## Apply
```bash
python3 \
TOS-UXUI-TASK-DETAILS-V2-11F-R1-EDITOR-TOOLBAR-ACTUAL-DOM-RESPONSIVE-FIX/apply_tos_task_details_v2_11f_r1_editor_toolbar_actual_dom_responsive_fix.py \
/var/www/TOS
```

## Mandatory visual QA
Light Mode, Description editor, both More closed/open at:
- 1664x936
- 1440x900
- 1366x768
- 1280x800

PUSH=NO until ChatGPT inspects all 8 Drive screenshots.
