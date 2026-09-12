# TOS Task Details V2.11F — Editor Toolbar Responsive + More Formatting Fix

VERSION=TOS_TASK_DETAILS_V2_11F
PATCH=TOS-UXUI-TASK-DETAILS-V2-11F-EDITOR-TOOLBAR-RESPONSIVE-MORE-FORMATTING-FIX
BASELINE_CHAIN=TOS_TASK_DETAILS_V2_11E_R1
BASE_TOS_COMMIT=cd019d60434943d625fde9d2ea2ddee7e68d2028
MICRO_STEP=EDITOR_TOOLBAR_RESPONSIVE_MORE_FORMATTING_FIX_ONLY

## Why
The editor audit confirmed that the Task Details Description toolbar is forced into a single nowrap row while overflow is clipped/hidden. That makes controls disappear as the approved main column narrows at 1440, 1366, and 1280. The existing `More Formatting` state already exists in the editor JSX, but older CSS scoping does not reliably restore the extended groups in the current canonical Task Details layout.

## Scope
- CSS-only Task Details Description editor-toolbar presentation fix.
- Keep existing editor commands, save behavior, HTML model, lists, RTL/LTR, links, images, undo/redo and upload logic untouched.
- Preserve the intentional decluttered behavior:
  - collapsed state: core tools + More Formatting remain reachable;
  - expanded state: every extended formatting group is explicitly visible and wraps inside the current editor width.
- Remove horizontal clipping as a mechanism for hiding controls.
- Make toolbar rows wrap cleanly at the audited viewport families: 1664, 1440, 1366, 1280.
- Preserve V2.11E_R1 Right Rail / floating-assistant responsive work, V2.11D_R1 editor/rail geometry, V2.11C tabs, Hero and task behavior.

## Frozen source
The installer verifies hashes before/after and must not change:
- `frontend/src/components/ProfessionalTaskBoard.jsx`
- `frontend/src/features/tasks/taskBoardParts.jsx`
- `frontend/src/components/TcsFloatingLauncher.jsx`
- `frontend/src/components/RamzyAssistant.jsx`

The only source file modified by this patch is:
- `frontend/src/styles/taskDetailsCanonicalReferenceV2.css`

## Apply
```bash
python3 \
TOS-UXUI-TASK-DETAILS-V2-11F-EDITOR-TOOLBAR-RESPONSIVE-MORE-FORMATTING-FIX/apply_tos_task_details_v2_11f_editor_toolbar_responsive_more_formatting_fix.py \
/var/www/TOS
```

## Mandatory visual QA
Light Mode, Task Details → Overview → Description editor:
- 1664x936
- 1440x900
- 1366x768
- 1280x800

At every width test two UI-only states:
1. `More Formatting` closed.
2. `More Formatting` opened.

PASS requires:
- toolbar has no accidental horizontal clipping;
- More Formatting button is visible/clickable in the collapsed state;
- opening More visibly restores every extended group;
- extended groups wrap inside the Description column rather than disappearing;
- no Editor ↔ Right Rail or Tabs ↔ Right Rail regression;
- no Right Rail, Hero, Tabs, TCS, Ramzy or editor-function changes.

This patch does NOT certify editor commands functionally. Bullet/Numbered/Nested/RTL/LTR/Save/Reload remain a separate safe-QA-data phase as established by the audit.

PUSH=NO until ChatGPT inspects the actual Drive screenshots and gives visual approval.
