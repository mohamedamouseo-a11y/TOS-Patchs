# TCS Desktop Window — UX/UI Polish V3

## Context
Implementation repo: `mohamedamouseo-a11y/TOS`
Branch: `main` only
Production working copy: `/var/www/TOS`
Expected remote/local base before this work: `ad5269bb55d6f09520b792a011f8aa8c8f2316a1`

Current mechanics are already implemented and MUST be preserved:
- draggable TCS launcher inside the TOS app frame
- per-user saved launcher position
- launcher clamped by real button bounds
- smooth pointer tracking
- launcher avoids Ramzy
- launcher toggles TCS window open/close
- TCS opens as internal desktop window, not Sidebar page
- window draggable, resizable, minimize/restore, maximize/restore
- per-user persisted window geometry
- window constrained to the TOS app frame
- existing TCS unread/realtime/chat functionality

Do NOT rewrite these mechanics unless a verified bug is found.

## Goal
Polish the TCS desktop-window experience so it feels intentionally designed for a movable large chat window rather than a full-page ChatPanel embedded inside a shell.

The result should feel like a premium desktop chat application running inside TOS.

## Required work

### 1. Audit current ChatPanel inside TcsDesktopWindow
Inspect the actual current production implementation before changing code:
- `frontend/src/components/ChatPanel.jsx`
- `frontend/src/components/TcsDesktopWindow.jsx`
- `frontend/src/components/TcsFloatingLauncher.jsx`
- relevant chat CSS in `frontend/src/index.css`
- `frontend/src/App.jsx`

Document which existing ChatPanel areas become cramped, duplicated, visually heavy, or awkward when rendered inside the movable window.

### 2. Add an explicit desktop-window presentation mode
Prefer a small explicit prop/context rather than fragile CSS guessing, e.g. `presentation="desktop-window"` or equivalent.

Do not duplicate ChatPanel or create a second chat system.

The same ChatPanel must continue powering the TCS window.

### 3. Improve internal TCS layout for the window
When rendered in desktop-window mode:
- remove/reduce redundant outer page chrome that duplicates the TCS window titlebar
- maximize usable conversation space
- keep the composer anchored and stable at the bottom
- keep message history as the primary scroll region
- preserve conversation/channel navigation, search, members/details, files, tasks, mentions, reactions, replies, edit/delete, receipts, presence, voice, meetings, huddles, pins/decisions and all current functionality
- use compact spacing appropriate for a desktop chat client
- keep important controls discoverable without crowding the header

### 4. Adaptive internal layout by window width
The UI must adapt to the TCS WINDOW width, not only browser viewport width.

Use ResizeObserver or another lightweight component-level approach if needed.

Target behavior:
- large window: conversation/navigation rail + main message area + optional details/context area where current architecture supports it
- medium window: conversation/navigation rail + main message area, details collapsible
- narrow window: main message area first; rails/drawers become overlays or collapsible panels

Do not require the user to maximize the window just to use TCS.

### 5. Window UX polish
Preserve current window controls and improve only where useful:
- clear title/identity
- drag affordance on titlebar
- minimize/maximize/close remain obvious
- double-click titlebar may toggle maximize/restore if safe
- maintain keyboard focus usability
- window should keep a premium rounded desktop-app visual style
- no content overflow outside rounded window shell
- no launcher/window overlap bugs

### 6. Launcher/window relationship
Preserve the current movable launcher.

On first open when no saved user geometry exists, continue opening intelligently based on launcher location/free space.

Once the user manually positions/resizes the window, respect saved user geometry.

Do not force the window to follow the launcher after the user has customized it.

### 7. Mobile / small frame behavior
On genuinely narrow TOS frames, use a near-maximized internal TCS window inside the frame with safe margins rather than an unusably tiny floating rectangle.

The window must still never escape the TOS frame.

### 8. Accessibility and localization
Preserve/improve:
- Arabic/English
- RTL/LTR
- light/dark
- keyboard focus
- aria labels
- `prefers-reduced-motion`

### 9. No backend/database work
This is frontend UX/UI work.

Do NOT change Prisma, backend routes, sockets, notification semantics, auth, permissions or database schema unless a real regression caused by this UI work is proven. If no backend fix is needed, leave backend untouched.

## Validation
At minimum:

```bash
cd /var/www/TOS

git diff --check
! grep -Rni --exclude-dir=node_modules --exclude-dir=dist --exclude-dir=.git 'TACS' frontend/src backend/src

cd frontend
npm run build
cd ..

./scripts/tos-production-preflight.sh --live
```

Also manually/automatically verify:
- launcher still drags smoothly
- launcher position persists after reload
- launcher stays inside TOS frame
- launcher avoids Ramzy
- launcher toggles TCS open/close
- TCS window drags
- TCS window resizes
- minimize/restore works
- maximize/restore works
- geometry persists
- window stays inside TOS frame after browser/frame resize
- TCS content is usable at large/medium/narrow window widths
- composer remains usable
- message history scroll remains correct
- unread/realtime alerts remain correct
- no Sidebar TCS entry returns
- Dashboard/Tasks/TWS/Ramzy/TOS shell regressions: none

## Commit / Push / Deploy workflow
Work and commit inside `/var/www/TOS` only.

No new branch. No force push.

DO NOT push with terminal `git push`, SSH, GH CLI, or Deploy Key.

After local commit(s) and validation, push ONLY using the running TOS Developer Hub / GitHub integration from inside the system to:
- repository: `mohamedamouseo-a11y/TOS`
- branch: `main`

After successful in-system push, verify remote SHA from inside the system.

Then deploy frontend only using the official deploy script:

```bash
cd /var/www/TOS
./scripts/tos-production-deploy.sh --scope frontend
```

Run final live preflight and UX smoke after deploy.

## Report
Return one ZIP:
`TCS_DESKTOP_WINDOW_UX_UI_POLISH_V3_REPORT.zip`

Include:
- audit summary
- changed files
- local/remote final SHA
- frontend build receipt
- live preflight receipt
- in-system push evidence
- deploy receipt
- large/medium/narrow TCS window screenshots
- QA matrix
- SHA256SUMS

Final report must explicitly state:
```text
BASE_SHA=ad5269bb55d6f09520b792a011f8aa8c8f2316a1
IMPLEMENTATION_WORKDIR=/var/www/TOS
IMPLEMENTATION_REPO=mohamedamouseo-a11y/TOS
IMPLEMENTATION_BRANCH=main
PUSH_METHOD=TOS_DEVELOPER_HUB_IN_SYSTEM
TERMINAL_GIT_PUSH_USED=NO
BACKEND_CHANGED=
PRISMA_SCHEMA_CHANGED=NO
FRONTEND_BUILD=
LIVE_PREFLIGHT=
LAUNCHER_DRAG=
LAUNCHER_PERSISTENCE=
WINDOW_DRAG=
WINDOW_RESIZE=
WINDOW_MINIMIZE=
WINDOW_MAXIMIZE=
WINDOW_PERSISTENCE=
FRAME_CONSTRAINT=
LARGE_WINDOW_UX=
MEDIUM_WINDOW_UX=
NARROW_WINDOW_UX=
TCS_REALTIME_REGRESSION=
TOS_SHELL_REGRESSION=
DEPLOYMENT=
FINAL_STATUS=
```
