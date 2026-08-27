# Manus — TCS Premium Chat Visual UX Audit V4.1

## Role
You are performing a narrow production visual/interaction QA pass on the already deployed TCS Premium Chat Workspace Redesign V4. Do not redesign the product again unless a real visual or interaction defect is demonstrated.

## Repositories
- Prompt repository only: `mohamedamouseo-a11y/TOS-Patchs`
- Implementation working directory: `/var/www/TOS`
- Implementation repository: `mohamedamouseo-a11y/TOS`
- Branch: `main` only
- Required starting SHA: `d324e59098734463e908b454f328a8d12bfa5956`

`TOS-Patchs` stores instructions only. Never push implementation code to it.

## Objective
Visually validate the V4 TCS redesign in the real running TOS desktop-window experience and make only minimal frontend corrections if a reproducible UX/UI defect is found.

The goal is a calm, premium, modern team-chat experience where the message stream is the visual focus and secondary tools do not compete with the conversation.

## Mandatory live QA matrix
Use an existing authorized TOS session only. Do not create users, reset passwords, guess credentials, impersonate users, or mutate business data merely for QA.

Test the actual draggable/resizable TCS desktop window at these window-width states:
1. Large: >= 1120px chat shell width.
2. Medium: 760–1119px.
3. Narrow: < 760px.

For each relevant state, inspect:
- Arabic RTL / English LTR.
- Light / Dark.
- Project chat and Direct chat if available in the authorized session without creating new business data.

Capture clear screenshots proving the evaluated UI states.

## Visual and interaction checklist
### 1. Conversation rail
- hierarchy is obvious;
- current conversation is clearly selected;
- unread counts are visible but not noisy;
- search and create controls do not dominate;
- no clipping or horizontal overflow;
- rail remains usable in Large/Medium and collapses appropriately in Narrow.

### 2. Conversation header
- current chat title/type is immediately understandable;
- member/unread status is compact and useful;
- typing state remains visible;
- search/focus/details/tools actions remain discoverable;
- no duplicate or exposed hidden controls at Medium/Narrow widths;
- no wrapping that creates an oversized header.

### 3. Message stream
- message stream is the dominant visual area;
- sender grouping/continuation is easy to scan;
- timestamps/edited/read/delivery metadata are subordinate;
- own/other messages remain distinguishable without excessive visual noise;
- hover actions do not cause layout jump;
- reactions and thread/reply actions remain usable;
- long messages, attachments, mentions, meeting messages, pinned/decision states do not break layout;
- no horizontal overflow.

### 4. Composer
- composer is visually anchored and always usable;
- send action is obvious;
- attachment/voice/templates/commands/more actions are available through progressive disclosure;
- quick mentions/templates do not permanently consume vertical space;
- reply/edit state is clear;
- narrow window remains usable without crowding.

### 5. Contextual inspector/details panel
- details is secondary to conversation;
- Large may use side-by-side inspector;
- Medium/Narrow overlay must not trap or obscure required controls;
- close/toggle behavior works;
- no overflow outside TCS window.

### 6. Desktop window + launcher regression
Do not alter the mechanics unless a regression is proven. Verify:
- launcher drag is smooth;
- launcher stays inside TOS frame;
- launcher position persists per user;
- launcher does not overlap Ramzy incorrectly;
- window drag/resize/minimize/maximize/restore/close work;
- window geometry remains inside TOS frame and persists;
- opening/closing TCS does not navigate to a sidebar chat page.

### 7. Accessibility/basic quality
- keyboard focus remains visible;
- reduced-motion behavior remains safe;
- buttons do not become inaccessible due to CSS visibility rules;
- touch layout retains access to message actions through the existing mobile interaction model;
- browser console has no new TCS render/runtime errors.

## Important V4 CSS risk to inspect
Specifically verify Medium/Narrow header behavior around selectors that reveal responsive hidden controls. Ensure no unintended `.relative.hidden` element becomes visible merely because it sits inside the header. If the selector is too broad in real UI, replace it with an explicit semantic class on the intended action group rather than another brittle descendant selector.

## Change policy
### If no real defect is found
- Do not modify code.
- Do not commit.
- Do not push.
- Do not deploy.
- Return PASS with screenshots and evidence.

### If a reproducible defect is found
- Make the smallest frontend-only correction.
- Preserve all TCS features, socket/realtime/unread/read state, permissions, launcher/window mechanics, backend APIs, and database schema.
- Prefer semantic classes over fragile selectors.
- Do not introduce a second chat UI/state/socket system.
- Run `git diff --check` and frontend production build.
- Perform post-fix live QA for the affected matrix plus a Large regression check.
- Create a local commit on `main`.

## Push rule if and only if a fix was required
The final GitHub push MUST be initiated from inside the running TOS system using its existing Developer Hub / GitHub integration Push action.

Forbidden:
- terminal `git push`;
- SSH push;
- GitHub CLI push;
- deploy-key push;
- new branch;
- force push;
- implementation push to `TOS-Patchs`.

Push target:
- repository: `mohamedamouseo-a11y/TOS`
- branch: `main`

After successful in-system push, verify the remote SHA. Deploy frontend only using the canonical TOS production workflow and only after the push succeeds.

If in-system Push cannot be completed, stop and report the exact sanitized blocker. Do not fall back to terminal/SSH/CLI.

## Required report
Return `TCS_PREMIUM_CHAT_VISUAL_UX_AUDIT_V4_1_REPORT.zip` containing:
- main report;
- screenshot evidence for the completed QA matrix;
- console/runtime notes;
- exact tested window sizes;
- whether a source change was required;
- changed files if any;
- local/remote final SHA if any fix was pushed;
- in-system Developer Hub push evidence if any fix was pushed;
- build/deployment evidence if any fix was pushed.

Final status must be one of:
- `PASS_NO_CHANGE_REQUIRED`
- `PASS_FIXED_AND_DEPLOYED`
- `BLOCKED_AUTHORIZED_BROWSER_SESSION`
- `BLOCKED_BROWSER_UNAVAILABLE`
- `BLOCKED_IN_SYSTEM_PUSH`
- `FAIL_REPRODUCIBLE_DEFECT_UNRESOLVED`
