# MANUS — TCS Premium Chat Workspace Redesign V4

## Repositories and runtime
- Prompt repository only: `mohamedamouseo-a11y/TOS-Patchs`
- Actual implementation repository: `mohamedamouseo-a11y/TOS`
- Branch: `main` only
- Production workdir: `/var/www/TOS`
- Start from remote TOS main SHA: `19212c4ab3176f54aebc8179891e5106fad0b099`
- TCS = Tamayouz Chat System.

## Objective
Redesign the TCS chat UX/UI as a premium, calm, modern team-chat workspace inside the existing draggable TCS desktop window, while preserving every existing chat capability and realtime behavior.

This is a real UX/UI redesign, not a cosmetic color pass.

The current ChatPanel is functionally rich but visually dense. Reduce cognitive load, improve hierarchy, improve discoverability, and make the primary actions obvious without deleting capabilities.

## Non-negotiable preservation
Do NOT break, remove, duplicate, or reimplement existing TCS features, including:
- direct conversations
- group conversations
- project general chat
- public/private channels
- replies/threads
- reactions
- message edit/delete
- typing indicators
- delivery/read receipts
- presence
- attachments/files/Google Drive
- pasted images
- voice recording
- meetings/huddles/calls where currently supported
- message-to-task
- pins/decisions/notes where supported
- mentions
- search
- notifications/unread/realtime
- permissions/private-channel security
- Arabic/English
- light/dark
- current draggable launcher mechanics
- current draggable/resizable/minimize/maximize TCS desktop window mechanics

No backend/database work unless a proven frontend contract defect makes it unavoidable. No Prisma migration.

## UX direction
Design TCS as a focused three-layer chat workspace:

### 1. Left/side navigation rail
Make the conversation/channel rail cleaner and easier to scan.
- Strong active-conversation state.
- Unread indicator/count is obvious but not noisy.
- Separate Direct Messages, Groups, Project, and Channels with restrained hierarchy.
- Keep creation actions available but do not show too many primary buttons at once.
- Use progressive disclosure for secondary actions.
- Search/filter should be compact and predictable.
- Presence/avatar/name/time/unread treatment should feel consistent.
- Long names must truncate gracefully.
- Empty/loading/error states must look intentional.

### 2. Main conversation surface
Make the message stream the visual focus.
- Premium conversation header with conversation/channel identity, presence/member summary, and only high-value actions visible.
- Secondary actions go into compact overflow/menus rather than filling the header.
- Message grouping by sender/time where sensible.
- Cleaner spacing rhythm between messages.
- Differentiate current user messages without using oversized bubbles.
- Attachments, files, replies, reactions, mentions, edited state, delivery/read state must remain visible but visually subordinate to the message itself.
- Hover actions should appear only when useful and must not cause layout shift.
- Thread/reply context should be immediately understandable.
- Unread divider/new-message marker should be visually clear.
- System/activity messages should look different from human chat messages.
- Improve loading skeletons and empty conversation state.

### 3. Composer
The composer must feel like the primary interaction surface.
- Stable at the bottom of the conversation area.
- Clear text input hierarchy.
- Send action obvious.
- Attachment/voice/emoji/template/extra actions grouped logically.
- Avoid an always-visible wall of icons; use progressive disclosure where appropriate.
- Reply/edit context must be clearly shown immediately above the input.
- Drag/drop/paste upload feedback must remain clear.
- Disabled/sending/uploading states must be obvious.
- Keyboard interaction must remain fast.

## Details/context panel
The details panel should behave like a contextual inspector rather than a permanent third dashboard.
- Large window: side inspector is allowed.
- Medium/narrow window: open as overlay/drawer within the TCS window.
- Sections should be grouped with clear titles and collapse behavior where useful.
- Members, pins, files, tasks, decisions, notes, search-related context must remain accessible.
- Do not permanently consume message width unless the window is large enough.

## Remove visual clutter from the primary surface
Existing advanced/management features such as dashboards, metrics, filters, command controls, moderation/insights, templates, channel tools, etc. must remain available but should not compete with daily chatting.

Use progressive disclosure:
- primary daily chat actions remain visible
- secondary actions go into contextual menus, drawers, tabs, or expandable areas
- admin/management tools should feel secondary, not like the default chat experience

Do not delete functionality just to make the UI simpler.

## Desktop-window adaptive behavior
The layout must adapt to the actual TCS window/container width, not browser viewport width.

Use the existing `presentation="desktop-window"` and current `ResizeObserver`/window-size classes where appropriate.

Required behavior:
- Large: rail + main conversation, optional contextual details inspector.
- Medium: compact rail + main conversation; details as overlay/drawer.
- Narrow: single-column conversation-first experience; rail/details accessible through internal drawers/tabs/buttons.

No critical action may become unreachable when the window is resized.
No horizontal overflow.
No fixed min-height that makes the chat unusable inside the resizable desktop window.

## Visual design system
Stay consistent with TOS rather than copying another product.
- premium neutral surfaces
- restrained amber/TOS accent
- strong typography hierarchy
- fewer nested bordered cards
- fewer heavy shadows
- consistent radii
- consistent 4/8px spacing rhythm
- compact but comfortable density
- smooth subtle transitions
- excellent dark mode
- Arabic RTL must look native, not mirrored awkwardly
- English LTR equally polished
- accessible contrast/focus states
- `prefers-reduced-motion` respected

Reference quality bar: modern Slack / Microsoft Teams / Linear / Discord-level clarity and interaction quality, but keep original TOS identity and do not copy their UI verbatim.

## Architecture constraints
- Prefer refactoring/presentation components over adding another parallel chat implementation.
- Reuse existing ChatPanel state and hooks.
- Do not create a second socket.
- Do not create a second unread/notification system.
- Do not fork the chat feature set into a separate TCS implementation.
- Avoid huge CSS-only hacks when a small structural component split would improve maintainability.
- If ChatPanel is too monolithic for safe UX work, extract focused presentational components while keeping behavior/state contracts intact.

## Suggested implementation scope
Inspect first, then change only what materially improves the experience. Likely files may include:
- `frontend/src/components/ChatPanel.jsx`
- focused new presentational TCS components if justified
- `frontend/src/index.css`
- small `App.jsx` presentation wiring only if needed

Do not touch launcher/window geometry mechanics unless a visual integration issue requires a tiny compatible adjustment.

## Required QA
At minimum:
1. `git diff --check`
2. frontend build
3. no `TACS` legacy naming in changed scope
4. Large TCS desktop window live QA
5. Medium TCS desktop window live QA
6. Narrow TCS desktop window live QA
7. Arabic RTL
8. English LTR
9. Light mode
10. Dark mode
11. Direct conversation
12. Project/channel conversation
13. send message
14. reply/thread
15. reactions
16. edit/delete where permitted
17. attachments/files
18. unread/realtime preserved
19. composer reply/edit/upload states
20. details/context panel behavior
21. launcher drag/persistence still works
22. desktop window drag/resize/minimize/maximize/persistence still works
23. no horizontal overflow or unreachable controls at narrow widths
24. browser console checked for render/runtime errors
25. TOS shell regression smoke test: Sidebar, Ramzy, Tasks, TWS/TGWS, Settings

If live browser QA is unavailable, do not claim PASS for those gates. Report the exact blocker honestly.

## Commit / push / deploy workflow
- Implement in `/var/www/TOS`.
- Create local commit(s) in the TOS working copy.
- DO NOT run terminal `git push`.
- DO NOT use SSH push.
- DO NOT use GitHub CLI push.
- DO NOT use deploy key push.
- DO NOT push implementation code to `TOS-Patchs`.
- Push ONLY from inside the running TOS system using the existing Developer Hub / GitHub integration Push action.
- Push target: `mohamedamouseo-a11y/TOS`
- Branch: `main`
- Verify resulting remote SHA from inside the system.
- Deploy frontend using the existing official TOS production deployment workflow only after successful in-system push.

## Final report
Return exactly:
`TCS_PREMIUM_CHAT_WORKSPACE_REDESIGN_V4_REPORT.zip`

Include:
- before/after UX summary
- exact changed files
- screenshots for Large/Medium/Narrow where browser QA is available
- Arabic/English and Light/Dark evidence where available
- build result
- live QA results per gate
- in-system Developer Hub push evidence
- remote final SHA
- deployment result
- known limitations/blockers

Required final fields:
```text
IMPLEMENTATION_WORKDIR=/var/www/TOS
IMPLEMENTATION_REPO=mohamedamouseo-a11y/TOS
IMPLEMENTATION_BRANCH=main
BASE_SHA=19212c4ab3176f54aebc8179891e5106fad0b099
PROMPT_REPO=mohamedamouseo-a11y/TOS-Patchs
CODE_PUSHED_TO_PATCH_REPO=NO
TERMINAL_GIT_PUSH_USED=NO
SSH_PUSH_USED=NO
GITHUB_CLI_PUSH_USED=NO
DEPLOY_KEY_PUSH_USED=NO
IN_SYSTEM_DEVELOPER_HUB_PUSH_USED=
REMOTE_FINAL_SHA=
FRONTEND_BUILD=
LARGE_WINDOW_QA=
MEDIUM_WINDOW_QA=
NARROW_WINDOW_QA=
ARABIC_RTL_QA=
ENGLISH_LTR_QA=
LIGHT_MODE_QA=
DARK_MODE_QA=
DEPLOYMENT=
FINAL_STATUS=
```

`FINAL_STATUS=PASS` only when mandatory engineering gates pass, in-system push succeeds, deployment succeeds, and there is no unresolved critical/high UX regression.
