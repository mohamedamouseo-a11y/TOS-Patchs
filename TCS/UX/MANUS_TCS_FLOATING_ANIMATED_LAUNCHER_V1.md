# TCS Floating Animated Launcher — V1

## Goal
Replace the current TCS navigation experience so TCS is NOT shown as a normal Sidebar item. Instead, TCS must appear as a persistent floating animated launcher similar in behavior/visual prominence to the existing Ramzy launcher, with a clear `TCS` label and unread state.

## Repositories and execution model
- Prompt source only: `mohamedamouseo-a11y/TOS-Patchs`
- Actual implementation workdir: `/var/www/TOS`
- Actual implementation repo: `mohamedamouseo-a11y/TOS`
- Branch: `main` only
- Do not create a branch.
- Do not implement code in TOS-Patchs.

## Current production baseline
Start from the current deployed `TOS/main`, which already includes the completed TCS global unread/realtime work. Preserve all current TCS functionality, unread reconciliation, reconnect recovery, visibility recovery, direct/group/channel chat behavior, authorization rules, and backend logic.

## Required UX change
1. Remove TCS from the normal Sidebar navigation list.
2. Preserve the existing TCS route/page and deep-link behavior. Removing the Sidebar item must NOT remove or rename the route.
3. Add a floating TCS launcher that is visible throughout the authenticated TOS shell, similar in placement/prominence to Ramzy but visually distinct.
4. The launcher must clearly show `TCS` on or immediately attached to the floating icon. Do not use only a generic chat icon.
5. Use a subtle professional animation, not distracting:
   - soft pulse / breathing motion / gentle glow or float,
   - respect `prefers-reduced-motion`,
   - no excessive bouncing/spinning.
6. Show the existing global TCS unread count on the launcher as a badge.
   - cap visual number at `99+`.
   - keep accessible `aria-label` with the real unread count.
7. When a new TCS realtime notification arrives outside TCS, the launcher may receive a brief attention pulse, but must not continuously animate more aggressively.
8. Clicking the floating launcher opens TCS using the existing navigation/routing mechanism.
9. When the user is already inside TCS, choose the cleaner UX after inspection of current Ramzy behavior:
   - either keep the launcher visible in an active state, or
   - hide/minimize it while TCS is open.
   Do not create duplicate navigation controls that feel broken.
10. Preserve mobile/narrow-screen usability. The launcher must not cover primary buttons, chat composer, bottom nav, modals, Ramzy, or important content.
11. If Ramzy is also floating, position both launchers intentionally as a coordinated floating action stack/group with safe spacing rather than overlapping.
12. Keep light/dark mode and Arabic/English layout correct.
13. No backend/schema/database change should be needed for this task.

## Implementation guidance
Audit and reuse the existing Ramzy floating launcher pattern where appropriate, but do NOT couple TCS business state to Ramzy internals. TCS should have its own component/state boundary and reuse the already implemented global TCS unread hook/state.

Likely production files may include:
- `frontend/src/App.jsx`
- `frontend/src/components/layout/Sidebar.jsx`
- existing Ramzy launcher/component files discovered during audit
- a new small TCS launcher component if that produces cleaner separation

Do not touch obsolete root `client/`, root `server/`, or `drizzle/`.

## Acceptance criteria
- No normal TCS item remains in Sidebar desktop or mobile navigation.
- TCS page/route still works directly and through the launcher.
- Floating TCS launcher is visible across TOS authenticated pages.
- Launcher clearly displays `TCS`.
- Professional subtle animation works and honors reduced-motion.
- Unread badge updates using the existing global realtime/unread implementation.
- No stale unread/toast regression.
- Ramzy and TCS launchers do not overlap.
- Desktop, mobile, Arabic, English, light, dark remain usable.
- No authorization/security regression.
- No schema migration.

## Validation
Before commit:
```bash
cd /var/www/TOS
./scripts/tos-production-preflight.sh --live
cd frontend
npm run build
cd ..
git diff --check
! grep -Rni --exclude-dir=node_modules --exclude-dir=dist --exclude-dir=.git 'TACS' frontend/src backend/src
```

Inspect the final changed-file list and ensure changes are limited to the intended frontend TCS/shell UX files unless a small shared UI helper is objectively required.

## Commit
Create a clear local commit, e.g.:
`feat(tcs): add floating animated launcher`

Do not force push and do not create a new branch.

## PUSH — FROM INSIDE TOS SYSTEM ONLY
This is critical.

DO NOT push from terminal.
DO NOT run `git push`.
DO NOT use SSH, GitHub CLI, PAT, or deploy key for the push.

After coding, validation, and local commit:
1. Open the running TOS system.
2. Open Developer Hub / GitHub integration inside TOS.
3. Use the system's own Push action.
4. Push the current `/var/www/TOS` implementation to:
   - repository: `mohamedamouseo-a11y/TOS`
   - branch: `main`
5. Verify from inside Developer Hub that the remote SHA equals the local commit SHA.
6. If the in-system push fails, do not substitute terminal push. Report the in-system error exactly and stop before deployment.

## Deploy
Only after successful in-system push and SHA equality:
```bash
cd /var/www/TOS
./scripts/tos-production-deploy.sh --scope frontend
```

Backend should not be restarted for this frontend-only UX change.

After deploy:
- live preflight
- frontend PM2 online
- verify TCS launcher visually in the live system
- verify Sidebar no longer contains TCS
- verify launcher opens TCS
- verify unread badge survives refresh and realtime update where a safe test is available
- verify Ramzy/TCS non-overlap on desktop and mobile

## Final report
Return:
`TCS_FLOATING_ANIMATED_LAUNCHER_V1_REPORT.zip`

Include:
- starting SHA
- changed files
- final local SHA
- in-system push evidence
- remote SHA
- frontend build receipt
- deploy receipt
- live QA matrix
- screenshots if the environment can capture them safely
- no secrets

Final status must explicitly include:
```text
IMPLEMENTATION_WORKDIR=/var/www/TOS
IMPLEMENTATION_REPO=mohamedamouseo-a11y/TOS
BRANCH=main
TCS_IN_SIDEBAR=NO
TCS_FLOATING_LAUNCHER=PASS|FAIL
TCS_LABEL_VISIBLE=PASS|FAIL
ANIMATION=PASS|FAIL
REDUCED_MOTION=PASS|FAIL
UNREAD_BADGE=PASS|FAIL
RAMZY_NON_OVERLAP=PASS|FAIL
MOBILE=PASS|FAIL
LIGHT_DARK=PASS|FAIL
AR_EN=PASS|FAIL
IN_SYSTEM_PUSH=PASS|FAIL
TERMINAL_GIT_PUSH_USED=NO
REMOTE_FINAL_SHA=
DEPLOY_SCOPE=frontend
DEPLOYMENT=PASS|FAIL
```
