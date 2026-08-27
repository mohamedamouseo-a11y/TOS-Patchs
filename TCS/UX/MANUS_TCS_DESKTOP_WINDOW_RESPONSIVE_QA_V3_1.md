# TCS Desktop Window Responsive QA V3.1

Implementation repository: `mohamedamouseo-a11y/TOS`
Branch: `main` ONLY
Production workdir: `/var/www/TOS`
Expected starting SHA: `19212c4ab3176f54aebc8179891e5106fad0b099`

## Purpose

This is a **QA-first continuation only** for the remaining unverified parts of TCS Desktop Window UX/UI Polish V3.

Do NOT redesign TCS again. Do NOT rewrite the desktop-window implementation. Do NOT touch backend/database/socket contracts unless a concrete reproducible frontend regression proves a source fix is required.

The V3 implementation is already pushed and deployed. The only currently outstanding gates are live responsive and interaction verification that were blocked previously by browser subsystem failure.

## Hard rules

1. Work on `main` only.
2. Start from exact SHA `19212c4ab3176f54aebc8179891e5106fad0b099` unless remote main has legitimately advanced; if it advanced, inspect first and stop if incompatible.
3. Preserve all existing TCS commits and mechanics.
4. Do not make source changes unless a real reproducible defect is observed during QA.
5. If no defect is found: **NO CODE COMMIT, NO PUSH, NO DEPLOY**. Return QA evidence only.
6. If a real defect is found: make the smallest frontend-only fix, validate it, commit locally, then push ONLY through TOS Developer Hub / GitHub integration inside the running system. Never use terminal git push, SSH, GH CLI, or Deploy Key.
7. Never fabricate screenshots, users, sessions, messages, or QA results.
8. No database migration.
9. Do not alter unrelated applications or existing Ramzy behavior.

## Step 1 — Baseline verification

Verify:
- `/var/www/TOS`
- branch `main`
- starting SHA / remote relationship
- frontend build state
- live preflight
- production TCS launcher/window opens successfully

Record safe receipts only.

## Step 2 — Responsive TCS window QA

Use the existing draggable/resizable TCS desktop window itself. Do not simulate success only by editing DOM classes.

Test at minimum these actual internal window widths:

### Large
- >= 1120px internal ChatPanel width
- expected class: `tos-chat-window-size-large`
- rail + message workspace usable
- details panel usable when opened

### Medium
- 760px–1119px internal ChatPanel width
- expected class: `tos-chat-window-size-medium`
- rail + message workspace remain usable
- details panel opens as contained overlay
- no horizontal clipping of main composer/message controls

### Narrow
- < 760px internal ChatPanel width
- expected class: `tos-chat-window-size-narrow`
- message-first layout
- desktop rail hidden as intended
- mobile/narrow controls are reachable
- details panel opens as contained overlay
- composer remains visible and usable
- message history remains the primary scroll area

For all three sizes capture screenshots and measured TCS window / ChatPanel bounds.

## Step 3 — Fresh post-V3 interaction regression

On the deployed V3 build verify:

1. Launcher drag remains smooth.
2. Launcher cannot escape TOS frame.
3. Launcher position persists after reload for the same user.
4. Launcher avoids Ramzy / does not cover it improperly.
5. Launcher opens TCS.
6. Launcher toggles/close behavior works.
7. TCS desktop window drag works.
8. Window cannot escape TOS frame.
9. Window resize works.
10. Window minimize/restore works.
11. Window maximize/restore works.
12. Window geometry persists after reload for the same user.
13. `/chat` deep-link still opens the internal TCS window.
14. Closing TCS restores the underlying TOS page route correctly.
15. Arabic RTL is visually valid.
16. English LTR is visually valid.
17. Light and dark modes are visually valid.
18. No fresh `ChatPanel render error` occurs in browser console during the QA path.
19. Dashboard / Tasks / TWS or TGWS / Settings / Ramzy remain usable after opening and closing TCS.

## Step 4 — Chat functional smoke

With the authenticated session(s) already available, verify without inventing credentials:
- existing conversations render
- selecting a conversation/channel works
- message history renders
- composer accepts input
- search/mentions/files/task/reply/reaction controls visible where expected for the chosen chat context
- unread badge/global TCS awareness does not obviously regress

If two authenticated users are already available, do one safe A→B realtime smoke. If not available, state `TWO_USER_REALTIME_QA=NOT_AVAILABLE` and do not fabricate it.

## Step 5 — Defect policy

If NO defect is found:
- do not edit code
- do not commit
- do not push
- do not deploy
- final status may be PASS if all mandatory responsive and interaction gates above pass

If a defect IS found:
- record exact reproduction
- identify root cause
- make the smallest frontend-only fix
- run `npm run build`
- run `git diff --check`
- run bounded `TACS` scan
- run `./scripts/tos-production-preflight.sh --live`
- commit locally
- review and push via TOS Developer Hub only
- frontend-only deploy using official script
- rerun the failed QA plus regression gates

## Deliverable

Return one ZIP in this session:

`TCS_DESKTOP_WINDOW_RESPONSIVE_QA_V3_1_REPORT.zip`

Include:
- final report markdown
- responsive QA matrix
- large / medium / narrow screenshots
- measured bounds/class evidence
- browser-console summary
- interaction regression matrix
- push/deploy receipts only if a real source fix was required
- SHA256SUMS

Final report must include:

```text
START_SHA=
FINAL_SHA=
SOURCE_CHANGE_REQUIRED=
NEW_COMMIT=
PUSH=
DEPLOYMENT=
LARGE_WINDOW_QA=
MEDIUM_WINDOW_QA=
NARROW_WINDOW_QA=
DETAILS_OVERLAY_MEDIUM=
DETAILS_OVERLAY_NARROW=
COMPOSER_CONTAINMENT=
MESSAGE_SCROLL_CONTAINMENT=
LAUNCHER_DRAG=
LAUNCHER_FRAME_CLAMP=
LAUNCHER_PERSISTENCE=
RAMZY_SEPARATION=
WINDOW_DRAG=
WINDOW_RESIZE=
WINDOW_MINIMIZE_RESTORE=
WINDOW_MAXIMIZE_RESTORE=
WINDOW_FRAME_CLAMP=
WINDOW_GEOMETRY_PERSISTENCE=
CHAT_DEEP_LINK=
ARABIC_RTL=
ENGLISH_LTR=
LIGHT_MODE=
DARK_MODE=
CHATPANEL_RENDER_ERROR=
TOS_SHELL_REGRESSION=
TWO_USER_REALTIME_QA=
FINAL_STATUS=
```

`FINAL_STATUS=PASS` only if Large + Medium + Narrow responsive QA and the mandatory interaction regression gates are all actually verified, with no unresolved critical/high TCS defect.