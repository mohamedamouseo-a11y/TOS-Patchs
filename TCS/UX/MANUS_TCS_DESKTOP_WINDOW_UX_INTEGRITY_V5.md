# MANUS — TCS Desktop Window UX Integrity V5

## Mission
Complete the current TCS desktop-window experience on top of the latest TOS `main` without redesigning or rebuilding features that already exist.

This is **V5 UX Integrity**, not another visual redesign.

The current TCS already has:
- draggable launcher with per-user saved position
- launcher clamped inside the TOS app frame
- Ramzy avoidance
- draggable/resizable/minimize/maximize TCS desktop window
- per-user window geometry persistence
- component-width-aware ChatPanel presentation
- Premium Chat Workspace Redesign V4
- existing realtime/unread/chat/backend feature set

Preserve all of the above.

---

## Repositories and execution target

### Prompt repository ONLY
`mohamedamouseo-a11y/TOS-Patchs`

Do NOT implement product code here.

### Actual implementation
- Working directory: `/var/www/TOS`
- Repository: `mohamedamouseo-a11y/TOS`
- Branch: `main`
- Required remote base before implementation: `cd7455579f9a6ef1015eedca18df93d6b7134ca8`

Before editing, verify local/remote lineage and preserve all TNC work already above TCS V4.

Do not reset or revert TNC.

---

# Objective
Finish the TCS desktop-window interaction model so that the entire chat experience behaves like a real application window inside TOS.

The result must be coherent, contained, responsive to the TCS window itself, and must never misrepresent local-only state as persisted backend state.

---

# Mandatory V5 scope

## 1. Keep every TCS secondary surface inside the TCS desktop window

Audit every ChatPanel secondary UI surface, including at minimum:
- workspace search
- mobile/message action sheet
- task conversion form/fallback
- thread panel
- template drawer
- profile card
- meeting modal
- huddle/call surface
- details panel overlays
- any additional dialog/drawer/popover owned by TCS

When `presentation="desktop-window"`:
- these surfaces MUST be visually and interactively contained by the TCS desktop window
- they MUST NOT use the browser viewport as their visual frame
- they MUST NOT cover the entire TOS application unless the TCS desktop window itself is maximized
- they MUST NOT escape `.tos-premium-app-frame`
- dragging/resizing the TCS window must not leave detached overlays behind

Use the cleanest existing React/CSS architecture. Do not create a second chat system or duplicate business logic.

For normal page presentation, preserve existing behavior unless a shared safe improvement is clearly beneficial.

---

## 2. Make desktop-window responsiveness truly component-width driven

V3/V4 introduced component-width awareness, but audit remaining viewport-breakpoint assumptions such as `sm:*`, `lg:*`, `fixed inset-0`, browser-width-only behavior, and mobile action visibility.

For `presentation="desktop-window"`, the UX must be based on the TCS window width/height rather than the browser width.

Required behavior:

### Large window
- channel/conversation rail visible
- conversation workspace visible
- optional details panel can coexist when enough room exists
- message stream remains the visual priority

### Medium window
- rail remains usable without crushing the message stream
- details panel becomes an internal overlay/drawer if necessary
- header actions compact intelligently

### Narrow window
- one primary workspace column
- channel/conversation navigation remains reachable through an internal drawer/tab/navigation control
- message actions remain accessible
- composer remains visible and usable
- no horizontal overflow
- no browser-level modal takeover

### Height constraints
Also audit short-height windows.
The titlebar, message stream and composer must remain usable when the window is resized vertically.
Avoid large decorative/header sections consuming most of the available height.

---

## 3. Fix authoritative Read UX

Current `useChat` already contains the real `markRead()` API path.
The ChatPanel UI must not claim only a local read operation when the real backend read operation exists.

Required:
- expose/reuse the existing authoritative `markRead()` from `useChat`
- the visible "mark current scope read" action must call the real API path
- reconcile local `lastReadAt`, visible unread state and scope unread counters after success
- preserve non-blocking behavior on network failure
- failure must not falsely display a success message
- do not create a new backend endpoint

Do not break the existing global TCS unread lifecycle or exact-scope backend reconciliation.

---

## 4. Remove misleading fake-persistence UX for Task / Decision fallbacks

Current real backend actions already exist for:
- message -> task
- decision marking

Audit the current catch/fallback behavior.

A failed backend request must NOT result in UI wording that makes the user believe a real system Task/Decision was persisted when it only exists in local component state.

Required behavior:
- first attempt the existing real backend action
- on failure, show an explicit unsynced/error state
- a local draft may be offered only as a clearly labeled draft/retry aid
- never count an unsynced local draft as a real persisted task/decision
- provide Retry where practical using the existing backend action
- retain the original message relationship in the retry draft
- do not create new backend schema/endpoints

If the current backend operation succeeds, keep the existing successful UX.

---

## 5. Branding consistency inside the window

Use canonical product branding:
- `TCS`
- `Tamayouz Chat System`

Avoid mixed/legacy naming when the visible product identity can be improved safely.
Do not rename backend route names or internal technical identifiers unnecessarily.

Arabic and English must both remain correct.

---

## 6. Preserve launcher/window mechanics exactly unless fixing a proven defect

Do NOT regress:
- free launcher dragging
- per-user launcher position persistence
- app-frame clamping
- Ramzy collision avoidance
- open/close toggle
- smart initial window placement near launcher
- manual window dragging
- resizing
- minimize/restore
- maximize/restore
- geometry persistence
- RTL resize behavior
- reduced-motion behavior

Do not rebuild this geometry system.

---

## 7. TNC / Ramzy interoperability regression check

TNC work is now on top of TCS V4.
Verify, without redesigning TNC:
- TCS launcher remains usable with Ramzy
- TCS window remains usable when TNC is opened/closed
- no impossible z-index trap
- no blocked launcher hit area
- TNC changes are not reverted

Only change TNC-specific code if a directly proven TCS interoperability defect requires a minimal fix.

---

# Explicit non-goals

Do NOT:
- build a new chat backend
- duplicate ChatPanel
- duplicate sockets
- create another unread subsystem
- add polling
- replace Prisma schema
- create a DB migration
- remove current TNC features
- revert TCS V4
- move TCS back into Sidebar
- turn TCS back into a full page as the primary interaction
- replace the existing Developer Hub push workflow
- create a branch

---

# Expected implementation preference

Prefer minimal, reusable changes around the existing architecture, likely involving only what is objectively necessary among:
- `frontend/src/components/ChatPanel.jsx`
- `frontend/src/hooks/useChat.js`
- `frontend/src/components/TcsDesktopWindow.jsx`
- `frontend/src/index.css`
- `frontend/src/App.jsx` only if containment/host plumbing objectively requires it

Reuse existing APIs and current state architecture.

---

# Validation gates

Run all relevant checks before committing.

Mandatory:
1. `git diff --check`
2. frontend production build
3. existing frontend/static checks available in the repo
4. backend tests only if any backend/shared contract file was touched
5. no Prisma schema/migration change
6. no legacy root-stack changes
7. bounded scan for legacy `TACS` naming in changed TCS-visible surfaces

## Manual / browser QA
Validate at minimum:

### Launcher/window
- drag launcher to left/right/top/bottom safe edges
- reload and confirm saved launcher position
- open/close via launcher
- drag window to all safe edges
- resize window large -> medium -> narrow -> large
- minimize/restore
- maximize/restore
- reload and verify geometry persistence
- verify nothing escapes the TOS frame

### Containment
From desktop-window mode open:
- workspace search
- thread
- template drawer
- profile card
- task action
- decision action
- meeting where permitted
- huddle/call surface where permitted

Confirm every TCS-owned surface stays logically inside the TCS desktop-window experience and does not detach from the moved/resized window.

### Responsive
Test at least:
- large desktop-window width
- medium width
- narrow width while browser itself remains desktop-sized
- short-height window
- Arabic
- English
- Light
- Dark

### Functional regression
Confirm existing capabilities still work or remain unchanged:
- direct conversations
- project/general chat
- channels/private channels
- groups
- message send
- reply/thread
- reactions
- edit/delete
- typing
- attachments/paste/Drive
- unread
- read/delivery receipts
- mentions
- search
- pins/decisions
- message-to-task
- meetings/huddles where supported

Do not fabricate users or mutate unrelated business data merely for QA.

---

# Commit and Push

After validation:
- create one coherent local commit in `/var/www/TOS`
- preferred message: `fix(tcs): complete desktop window UX integrity v5`

## CRITICAL PUSH POLICY
Final GitHub push MUST happen from inside the running TOS system using its existing Developer Hub / GitHub integration Push action.

Target:
- repository: `mohamedamouseo-a11y/TOS`
- branch: `main`

ABSOLUTELY FORBIDDEN:
- terminal `git push`
- SSH push
- GitHub CLI push
- deploy-key push
- push to `TOS-Patchs`
- force push
- new branch

If the in-system Developer Hub push fails, STOP and report the sanitized blocker. Do not fall back to another push method.

Verify the resulting remote SHA after the in-system push.

---

# Deployment

If this remains frontend-only, deploy with the canonical production workflow:

`./scripts/tos-production-deploy.sh --scope frontend`

Only after successful in-system GitHub push.

If an objectively necessary backend change was made, use the appropriate canonical scope and explain why.

Run final live preflight / HTTP smoke checks after deployment.

---

# Final report

Return one ZIP:

`TCS_DESKTOP_WINDOW_UX_INTEGRITY_V5_REPORT.zip`

It must include:
- implementation summary
- exact files changed
- why each change was necessary
- validation commands/results
- frontend build result
- containment QA matrix
- large/medium/narrow/short-height QA
- Arabic/English + Light/Dark QA
- task/decision persistence behavior result
- authoritative read behavior result
- TNC/Ramzy interoperability result
- local commit SHA
- in-system Developer Hub push evidence
- remote final SHA
- deployment result
- screenshots if browser QA is available

End with exactly these fields:

```text
IMPLEMENTATION_WORKDIR=/var/www/TOS
IMPLEMENTATION_REPO=mohamedamouseo-a11y/TOS
IMPLEMENTATION_BRANCH=main
PROMPT_REPO=mohamedamouseo-a11y/TOS-Patchs
BASE_SHA=cd7455579f9a6ef1015eedca18df93d6b7134ca8
CODE_PUSHED_TO_PATCH_REPO=NO
TERMINAL_GIT_PUSH_USED=NO
SSH_PUSH_USED=NO
GITHUB_CLI_PUSH_USED=NO
DEPLOY_KEY_PUSH_USED=NO
IN_SYSTEM_DEVELOPER_HUB_PUSH_USED=YES
IN_SYSTEM_PUSH_TARGET=mohamedamouseo-a11y/TOS
IN_SYSTEM_PUSH_BRANCH=main
IN_SYSTEM_PUSH_RESULT=
REMOTE_FINAL_SHA=
DEPLOYMENT=
TCS_V5_STATUS=
```

`TCS_V5_STATUS=PASS` only when mandatory validation passes, the in-system push succeeds, remote SHA is verified, deployment succeeds, and there is no unresolved critical/high TCS regression.
