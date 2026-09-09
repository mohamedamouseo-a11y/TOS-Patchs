# TOS — Ramzy Contextual Smart Task V1

## Product rule
Ramzy stays visually simple by default. Smart controls appear only when the current user intent needs structured choices, then disappear when the action is complete or cancelled.

## This patch
Converts Smart Task Composer V1 from permanent UI into contextual, ephemeral Smart UI.

### Removed
- Permanent `Smart task / مهمة ذكية` button in the composer.
- Smart task shortcut in the welcome screen.

### Added
- Create-task intent detection in Arabic and English.
- Optional task-title extraction from the user's natural request.
- Contextual Smart Task card inside the conversation flow.
- Existing real project/team choices, due-date presets, priority choices, and Ramzy suggestions remain available only during task creation.

## Examples
- `اعمل تاسك تصميم بوست` → task title is inferred as `تصميم بوست`, then project choices appear.
- `أنشئ مهمة` → title is requested first.
- `create a new task landing page` → title is inferred as `landing page`.
- `افتح التاسك القديم` → does not trigger create-task flow.

## Safety
- No backend changes.
- No database changes.
- No routes changes.
- No permission changes.
- Existing CREATE_TASK approval flow remains mandatory.
- No git commit or git push.

## Server-state expectation
- HEAD: `048592147387e2b49382f605a04f8d2efd64f61c`
- Smart Task Composer V1 is already applied in the current dirty worktree.
- The old button-only Visual Correction patch must not be applied first.

After successful execution, manually test normal chat, create-task intent, title-less create-task intent, and an existing-task/open-task request before pushing.
