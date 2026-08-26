# TCS — Draggable Desktop Window UX V2

## Objective

Transform TCS from a page/side-navigation experience into a true **desktop-style chat window inside TOS**.

The user experience must feel like a small application running inside the TOS application frame:

- A draggable TCS launcher that behaves with the same smooth interaction quality as Ramzy.
- The launcher can be moved anywhere **inside the TOS application frame only**.
- Its last position is persisted per user.
- Clicking it opens TCS in a large movable/resizable internal window.
- The TCS window is NOT a sidebar panel and MUST NOT replace the current TOS page.
- The TCS window itself can be positioned left/right/center as the user wants, dragged and resized, while remaining fully inside the TOS frame.
- Window position, size, and minimized/open preference are persisted per user where appropriate.
- Existing TCS realtime, unread, permissions, messaging, attachments, collaboration and backend behavior must be preserved.
- Improve TCS UX/UI for the larger desktop-window form factor without rebuilding the chat domain.

This is a frontend UX architecture task, not a new chat system.

---

## Repositories and execution model

Prompt source only:
- `mohamedamouseo-a11y/TOS-Patchs`

Actual implementation:
- working directory: `/var/www/TOS`
- repository: `mohamedamouseo-a11y/TOS`
- branch: `main` ONLY

Expected current remote/local base before this task:
- `0635ac049fde67bde53015504c5f4268e38a575f`
- `feat(tcs): add floating animated launcher`

Do not rewrite or recreate previous TCS commits.

### Push rule — CRITICAL

After implementation and local commit:

- **DO NOT run terminal `git push`.**
- **DO NOT use SSH, Deploy Key, GH CLI, or token-based terminal push.**
- Push using the running TOS application's **Developer Hub / GitHub integration** from inside the system, exactly like the previous successful TCS in-system workflow.
- Destination: `mohamedamouseo-a11y/TOS`
- Branch: `main`
- No force push.

`TOS-Patchs` receives no implementation code.

---

# 1. Audit first — reuse Ramzy interaction patterns

Before writing code, inspect the current production implementations, especially:

- `frontend/src/components/RamzyAssistant.jsx`
- `frontend/src/components/TcsFloatingLauncher.jsx`
- `frontend/src/App.jsx`
- `frontend/src/components/ChatPanel.jsx`
- `frontend/src/hooks/useChat.js`
- `frontend/src/hooks/useGlobalTcsUnread.js`
- `frontend/src/lib/socket.js`
- `frontend/src/lib/realtimeStateSync.js`
- `frontend/src/components/layout/Sidebar.jsx`
- the current global CSS containing Ramzy and TCS launcher styles

Use Ramzy as the interaction-quality reference for:

- drag threshold / click-vs-drag handling
- pointer capture if applicable
- smooth movement
- saved per-user position
- viewport/frame resize reconciliation
- safe position clamping
- side-aware opening
- minimized state patterns
- reduced-motion support

Do NOT copy Ramzy blindly. Reuse/abstract only what is appropriate.

Where practical, extract a small reusable frontend geometry/drag helper so Ramzy and TCS do not maintain two inconsistent implementations. Do not risk a Ramzy regression merely to force abstraction; a clean TCS-local implementation using the same proven pattern is acceptable.

---

# 2. Define the TOS desktop boundary

The draggable launcher and the TCS window must be constrained to the **TOS application frame**, not merely the browser viewport.

Use the live TOS shell boundary represented by the main application frame (currently the element using `tos-premium-app-frame`) or a clean explicit ref added to the equivalent canonical shell container.

Requirements:

- Obtain bounds with `getBoundingClientRect()` from the actual TOS frame.
- Launcher cannot be dragged beyond any edge of that frame.
- TCS window cannot be dragged or resized beyond that frame.
- Respect the frame's inner padding/gap with a small safe margin.
- If viewport or frame size changes, re-clamp both launcher and window into legal positions.
- If a saved position/size is no longer legal after screen-size change, restore the closest valid position/size automatically.
- Do not rely on hard-coded browser coordinates such as permanent `right:22px; bottom:116px` for final placement.

Desktop and mobile/narrow layouts must use the actual frame dimensions.

---

# 3. TCS launcher — fully draggable and persistent

Replace the current sticky fixed launcher behavior with a proper draggable launcher.

## Interaction

The launcher must:

- move freely in X and Y anywhere inside the TOS frame
- feel smooth like Ramzy
- distinguish drag from click using a small drag threshold
- not accidentally open TCS when the user intended to drag
- remain keyboard-accessible
- remain touch/pointer friendly
- keep the existing `TCS` identity visibly clear
- preserve realtime unread badge and attention animation
- preserve `prefers-reduced-motion`

## Persistence

Persist the final legal launcher position per authenticated user, for example with a versioned key such as:

`tos.tcs.launcher.position.v2.<userId>`

Do not persist continuously on every pointer-move if unnecessary; persist on drag end and when clamped by a meaningful layout change.

## Default position

For users with no saved position:

- choose a sensible default that does not overlap Ramzy
- keep enough space for both launchers
- do not assume Ramzy itself is always at its default location

If practical, implement collision-aware initial placement only. Do not over-engineer dynamic collision physics between Ramzy and TCS.

---

# 4. TCS must open as an internal desktop window, NOT a page/sidebar

This is the most important UX change.

When the user clicks the TCS launcher:

- DO NOT navigate the primary TOS workspace to a full-page chat screen.
- DO NOT open TCS in the sidebar.
- DO NOT replace Dashboard/Tasks/TWS/etc.
- Open a separate TCS desktop window layered **inside the TOS application frame** over the current page.

The user should be able to keep working on the underlying TOS page while the TCS window is open.

Reuse the existing `ChatPanel` / TCS implementation as the functional content of the window. Do not duplicate its data/socket/business logic.

If current `ChatPanel` assumes full-page sizing, refactor presentation boundaries cleanly so the same TCS content works in the desktop-window shell.

---

# 5. TCS desktop window behavior

Create a dedicated shell, e.g. conceptually:

- `TcsDesktopWindow`
- or another appropriately named component

Do not mix all window geometry code into `App.jsx`.

## Window capabilities

The TCS window must support:

1. **Drag**
   - drag by a dedicated title/header area
   - never drag when selecting messages, scrolling, clicking buttons, or using composer controls
   - smooth pointer movement
   - full clamp inside TOS frame

2. **Resize**
   - desktop: resize from appropriate edges/corners or a clean resize grip
   - enforce minimum useful chat size
   - enforce maximum size equal to legal frame area
   - never allow any part of the window outside the frame
   - narrow/mobile can use a constrained near-full-frame mode instead of tiny manual resizing

3. **Minimize**
   - minimize the TCS window without losing current chat state
   - minimized state should reduce to a compact internal bar/chip near the launcher or another clean location inside frame
   - clicking launcher while minimized should restore it

4. **Close**
   - close the desktop window while keeping the floating launcher visible
   - closing must not mark unrelated notifications read

5. **Maximize / Restore**
   - provide a maximize action on desktop
   - maximize to the legal interior of the TOS app frame, not browser fullscreen
   - restore previous position/size accurately

6. **Z-order / focus**
   - when clicked/opened, TCS should be above normal TOS content
   - do not cover critical global modal layers that intentionally require a higher z-index
   - TCS and Ramzy must coexist without destructive z-index conflicts

---

# 6. Smart opening direction / position

The user wants the window to appear left or right depending on where they place the launcher and depending on available space.

Implement smart initial placement only when the user has no previously saved TCS window geometry:

- if launcher is on the left side, prefer opening the window to its right
- if launcher is on the right side, prefer opening the window to its left
- if there is insufficient space, choose the side/position with more legal room
- clamp the final window inside the TOS frame

After the user manually drags/resizes the TCS window, respect the user's saved geometry instead of forcing side-aware placement every time.

Persist window geometry per user, e.g.:

`tos.tcs.window.geometry.v2.<userId>`

Suggested persisted data:

```json
{
  "x": 0,
  "y": 0,
  "width": 0,
  "height": 0,
  "maximized": false
}
```

Persist only safe non-sensitive UI geometry.

---

# 7. Route / deep-link compatibility

TCS is no longer a normal sidebar/page destination, but existing route/deep-link behavior must not become broken.

Requirements:

- Remove any remaining normal TCS sidebar navigation entry.
- Launcher is the primary UX entrypoint.
- Direct navigation to `/chat` must still be handled safely.
- Preferred behavior for `/chat`: open the TCS desktop window while keeping the shell stable rather than restoring the obsolete full-page TCS experience.
- Browser back/forward must not leave the application in an impossible state.
- Do not create navigation loops.
- If route synchronization becomes complex, prioritize launcher/window correctness while preserving `/chat` as a supported open-window deep link.

Do not break notification click behavior that opens TCS.

---

# 8. TCS UX/UI redesign for the larger desktop window

Improve the visual hierarchy of TCS for a large floating window while preserving its mature functionality.

The goal is not a total redesign; it is a focused desktop-window UX refinement.

## Window chrome

Create a premium but compact title bar containing:

- TCS identity
- current active conversation/channel summary where practical
- connection/realtime state only if already available safely
- minimize
- maximize/restore
- close

The drag handle must be obvious enough but visually clean.

## Chat layout

Within the window, improve:

- conversation/channel list width and hierarchy
- active conversation header
- message reading area
- composer always reachable and visually anchored
- spacing and density for a larger window
- scroll behavior
- long text/file/message handling
- empty/loading/error states

Preserve existing capabilities:

- direct chat
- group chat
- project/general/channel chat
- private channels
- replies/threads
- reactions
- edit/delete
- read/delivery receipts
- typing/presence
- mentions
- search
- files/attachments/Drive
- pasted images
- voice recording
- meetings/huddles if already wired
- message-to-task
- pins/decisions
- moderation/insights
- commands/templates

Do not remove functionality merely to simplify layout.

## Responsive behavior

Desktop:
- large resizable desktop window
- reasonable default around a large working size, bounded by TOS frame

Tablet/narrow:
- use most of the frame while keeping a visible safe margin
- resizing may be simplified

Mobile:
- open as a near-full-frame internal window/card inside TOS frame
- no off-screen drag behavior
- launcher remains draggable within sensible bounds if practical; otherwise clamp to the frame and use a simplified touch-safe drag interaction

## Themes / locale / accessibility

- Arabic and English
- RTL and LTR
- light and dark themes
- keyboard focus
- meaningful ARIA labels
- `prefers-reduced-motion`
- controls minimum touch target quality

---

# 9. Realtime and unread behavior — must remain authoritative

Do not regress the completed Phase 2 lifecycle.

Preserve:

- global unread hydration
- singleton Socket.IO client
- background `chat:notification`
- dedupe
- reconnect rehydrate
- visibility restore rehydrate
- exact-scope notification reconciliation on read
- stale-toast fix

Launcher unread badge must keep updating whether TCS window is:

- closed
- open
- minimized
- maximized

Opening the window alone must not blindly mark everything read. Only existing exact-scope read behavior should clear relevant unread state.

When the user is actively viewing a scope and current TCS behavior marks it read, global unread should reconcile correctly.

---

# 10. Architecture constraints

Preferred structure is small and maintainable.

Possible frontend additions/refactors:

- `frontend/src/components/TcsFloatingLauncher.jsx`
- `frontend/src/components/TcsDesktopWindow.jsx`
- optional reusable geometry helper under `frontend/src/lib/` or `frontend/src/hooks/`
- small `App.jsx` integration
- focused styles
- limited `ChatPanel.jsx` responsive/container refactor

Avoid:

- a new backend
- a second chat state store
- a second socket connection
- duplicate notification logic
- duplicate conversation/message APIs
- database changes
- Prisma changes
- unrelated refactors
- obsolete root `client/` / `server/` / Drizzle stack

No backend change should be needed for this UX phase unless a genuinely blocking frontend contract bug is discovered. If no backend change is required, keep this frontend-only.

---

# 11. Required technical checks

Starting gate:

```bash
cd /var/www/TOS
test "$(git branch --show-current)" = "main"
test "$(git rev-parse HEAD)" = "0635ac049fde67bde53015504c5f4268e38a575f"
git diff --check
```

If remote/main has moved because of another authorized in-system change, inspect before proceeding. Do not reset or overwrite unrelated work.

After implementation:

```bash
cd /var/www/TOS/frontend
npm run build
cd /var/www/TOS
git diff --check
! grep -Rni --exclude-dir=node_modules --exclude-dir=dist --exclude-dir=.git 'TACS' frontend/src backend/src
./scripts/tos-production-preflight.sh --live
```

Also validate explicitly:

- only one TCS launcher exists
- TCS not shown in normal sidebar navigation
- no duplicate Socket.IO client
- launcher drag does not trigger open accidentally
- launcher cannot escape TOS frame on any edge
- launcher position persists after reload/login refresh for same user
- window cannot escape TOS frame on drag
- window cannot escape TOS frame on resize
- saved window position/size persists and safely re-clamps after viewport resize
- smart initial left/right placement works
- minimize/restore works
- maximize/restore works
- close/reopen works
- underlying TOS page remains mounted/usable while TCS window is open
- `/chat` deep link safely opens TCS window
- unread badge still works when window closed/minimized
- reconnect and visibility recovery remain intact
- Ramzy still drags/opens normally
- TCS and Ramzy do not block each other's controls
- Dashboard/Tasks/TWS/Settings shell regression smoke passes

No DB migration.

---

# 12. Commit

Create a clean logical commit after all validations pass.

Preferred message:

`feat(tcs): add draggable desktop chat window`

If a second focused commit is genuinely necessary for reusable shell geometry/tests, keep it logical and minimal.

No amend/squash of previous TCS commits.

---

# 13. In-system Developer Hub push

After local commit and validation:

1. Open the running TOS system.
2. Use **Developer Hub / GitHub integration** inside TOS.
3. Select the actual implementation repository `mohamedamouseo-a11y/TOS`.
4. Confirm branch `main`.
5. Push the local commit(s) using the in-system Push action.
6. No terminal `git push`.
7. No SSH/GH CLI/Deploy Key push.
8. No force push.
9. Verify the remote SHA shown by the system matches local HEAD.

If the in-system push fails, do not substitute another push method. Return the exact sanitized blocker.

---

# 14. Deploy

Because this should be frontend-only, after successful in-system push and SHA equality run:

```bash
cd /var/www/TOS
./scripts/tos-production-deploy.sh --scope frontend
```

If you made a genuinely required backend change, use `--scope both` and document why. No DB migration unless an explicitly reviewed schema change occurred, which is not expected.

After deploy:

- run live preflight
- verify frontend serves
- verify PM2 frontend online
- perform live visual/interaction QA

Capture desktop and narrow/mobile screenshots showing:

1. launcher moved to a non-default location
2. window opened on the suitable opposite side
3. window manually moved
4. resized window still inside frame
5. minimized state
6. maximized state inside TOS frame
7. Arabic or RTL state
8. dark mode if practical

Do not include sensitive information in screenshots.

---

# 15. Final report

Return exactly:

`TCS_DESKTOP_WINDOW_DRAGGABLE_V2_REPORT.zip`

Include:

- `TCS_DESKTOP_WINDOW_DRAGGABLE_V2_REPORT.md`
- changed-file list
- commit SHA(s)
- in-system push receipt
- local/remote final SHA equality
- frontend build receipt
- preflight/deploy receipt
- desktop-window QA matrix
- screenshots
- SHA256SUMS

Final report must state:

```text
IMPLEMENTATION_WORKDIR=/var/www/TOS
IMPLEMENTATION_REPO=mohamedamouseo-a11y/TOS
IMPLEMENTATION_BRANCH=main
BASE_SHA=0635ac049fde67bde53015504c5f4268e38a575f
NEW_COMMITS=
LOCAL_FINAL_SHA=
REMOTE_FINAL_SHA=
PUSH_METHOD=TOS_DEVELOPER_HUB_IN_SYSTEM
TERMINAL_GIT_PUSH_USED=NO
DEPLOY_SCOPE=frontend
FRONTEND_BUILD=
LIVE_PREFLIGHT=
DEPLOYMENT=
TCS_REMOVED_FROM_NORMAL_SIDEBAR=
LAUNCHER_DRAGGABLE=
LAUNCHER_POSITION_PERSISTED=
LAUNCHER_CLAMPED_TO_TOS_FRAME=
TCS_DESKTOP_WINDOW=
WINDOW_DRAGGABLE=
WINDOW_RESIZABLE=
WINDOW_GEOMETRY_PERSISTED=
WINDOW_CLAMPED_TO_TOS_FRAME=
SMART_LEFT_RIGHT_OPENING=
MINIMIZE_RESTORE=
MAXIMIZE_RESTORE=
CHAT_FUNCTIONALITY_PRESERVED=
GLOBAL_UNREAD_PRESERVED=
REALTIME_PRESERVED=
RAMZY_REGRESSION=
TOS_SHELL_REGRESSION=
MIGRATION_RUN=NO
FINAL_STATUS=
```

`FINAL_STATUS=PASS` only if the in-system push succeeded, local and remote SHA match, frontend deploy succeeded, launcher/window are fully contained by the TOS frame, and no critical TCS or Ramzy regression remains.
