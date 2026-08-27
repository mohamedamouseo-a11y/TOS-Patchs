# TCS V8 — Visual Excellence Refinement

## Context

Implementation repo: `mohamedamouseo-a11y/TOS`
Working directory: `/var/www/TOS`
Branch: `main`
Required base SHA: `73d632614701962fa62ad3fee21ac9bc51825415`

Prompt repo: `mohamedamouseo-a11y/TOS-Patchs`

V7 is technically successful and must be preserved, but live screenshots show that the TCS desktop-window UI still needs a final visual-quality pass before it can be considered a truly premium chat product.

This is NOT a feature release. This is NOT a backend release. This is NOT another generic CSS polish pass.

The goal is to make the existing TCS experience visually excellent, calm, focused, cohesive, and unmistakably chat-first.

## Preserve without regression

Do not break or redesign the existing:
- draggable TCS floating launcher
- launcher position persistence
- desktop-window drag / resize / minimize / maximize / restore / close
- frame clamping
- V5 contained overlays
- V6 saved messages
- V6 server-backed drafts
- realtime, unread, typing, receipts, reactions, threads, files, meetings, huddles, tasks, decisions
- TNC
- Ramzy
- Arabic/English and RTL/LTR
- dark/light themes

No backend or Prisma changes are expected.

## Screenshot-led issues to fix

### 1. Reduce top-toolbar density
The current conversation header exposes too many primary pills/buttons at once (search, files, tasks, focus, details, chat tools, etc.). It reads like an admin toolbar rather than a premium chat header.

Refactor the presentation hierarchy only:
- keep 2–3 highest-frequency actions directly visible
- move secondary actions into one clean overflow/tools menu
- preserve every existing action and permission
- keep state discoverable and keyboard accessible
- do not remove functionality

The visual priority should be:
1. conversation identity/status
2. message reading
3. composer
4. secondary utilities

### 2. Simplify the conversation rail
The V7 rail is still too card-heavy and form-heavy.

Improve it so it scans like a mature communication product:
- reduce nested boxes/card-within-card appearance
- make search one clean top control
- make All / Unread / Pinned / Direct / Projects / Archive compact filters instead of a large panel
- move `Choose a member` / `Start conversation` and group creation behind a compact New conversation action or expandable control
- give conversation rows cleaner avatar/presence, title, last activity and unread hierarchy
- avoid extreme black/white selected rows; use a more refined selected state
- reduce repeated generic labels such as `Direct chat` where a real participant/conversation name can be shown safely from existing data
- do not fabricate names or data

### 3. Make the main message canvas feel like a conversation, not a bordered empty dashboard card
Current screenshots show a very large bordered blank panel when the conversation has few messages.

Refine the canvas:
- reduce the heavy outer card/border feeling around the whole message stream
- make the message lane itself the visual focus
- keep date separators subtle
- improve message grouping rhythm
- make sender metadata quieter but clearer
- improve bubble geometry and max widths
- improve owner/non-owner visual distinction without loud gradients
- avoid huge dead-space feeling when only one or two messages exist
- preserve scrolling, pagination, jump-to-latest and message actions

### 4. Rebuild the composer presentation visually
The composer is currently too visually dominant, with an oversized outlined container.

Keep all composer capabilities but make it feel more refined:
- reduce thick amber framing
- use a calm neutral shell with accent only for focus/send state
- keep textarea, attachment, mic and send actions balanced
- visually integrate the send button with the composer instead of making it look detached
- keep draft-sync status truthful but visually quiet
- attachment/drop/paste states must remain obvious when active
- preserve keyboard shortcuts and accessibility

### 5. Narrow-window mode must become a true single-column chat experience
The V7 narrow screenshot is still dense: many top actions, mobile tabs, conversation chips and controls compete at once.

For `tos-chat-window-size-narrow`:
- main conversation becomes the only permanent column
- rail/conversation list opens as a contained drawer/sheet inside the TCS window
- details/tools open as contained drawer/sheet
- do not keep a squeezed permanent rail
- reduce top header actions to essential controls
- avoid long rows of horizontal chips
- use one compact conversation selector/navigation control
- composer must remain fully visible and stable
- no horizontal overflow
- all overlays remain inside the TCS desktop window

Do this using existing state where possible. Do not build a second chat architecture.

### 6. Medium mode should be intentionally designed, not a squeezed large layout
For `tos-chat-window-size-medium`:
- use a compact 2-pane layout where appropriate
- rail width and density should remain comfortable
- details should use overlay/drawer rather than creating a cramped three-column state
- keep conversation header single-line or cleanly wrapped
- keep composer full width within message workspace

### 7. Localization quality is part of visual quality
The Arabic screenshots still expose English labels such as `Advanced search`, `Direct chat`, `Start`, or `You` in some states.

Audit every visible TCS V8 surface in Arabic mode:
- no accidental English UI labels except established product/acronym terms such as TCS, Drive, or explicit technical commands where intentionally retained
- use existing translation infrastructure/patterns
- do not hardcode a second localization system

English mode must remain clean and fully LTR.

### 8. Improve visual hierarchy and typography
- reduce excessive font-weight 900/950 where it creates noise
- use stronger hierarchy through size/spacing/contrast, not boldness everywhere
- standardize radius scale
- standardize border opacity
- standardize shadow/elevation levels
- keep amber/gold as an accent, not the border of every component
- make light mode feel warm-premium, not washed-out white
- make dark mode retain the strong V7 quality without excessive near-black blocks

### 9. Active launcher state while window is open
The floating TCS launcher remains visually prominent while the full TCS window is already open.

Refine only its active presentation:
- when TCS window is open, reduce the launcher to a compact active/dock state or another clean low-noise representation
- preserve drag behavior and position persistence
- preserve ability to close/restore if currently provided
- do not remove the launcher entirely unless existing interaction remains obvious and safe
- do not overlap Ramzy

### 10. Secondary contained surfaces
Keep V5 containment and give all existing contained surfaces the same V8 design language:
- Thread
- profile
- templates
- search
- meeting
- huddle
- task/decision drafts
- details panels

Do not move anything back to browser-level fixed overlays.

## Implementation strategy

First inspect the current `ChatPanel.jsx`, `TcsDesktopWindow.jsx`, `TcsFloatingLauncher.jsx`, `index.css`, and translation patterns.

Prefer focused component/presentation changes over stacking another giant uncontrolled CSS layer.

It is acceptable to add small presentation subcomponents if that materially reduces duplicated markup and improves maintainability, but do not rewrite the chat domain.

Expected scope is frontend-only.

## Visual QA requirements

Live QA after deploy must include screenshots of:
1. Large Arabic Light
2. Large Arabic Dark
3. Large English Light
4. Large English Dark
5. Medium Arabic Light
6. Narrow Arabic Light
7. Narrow English Dark

Also capture at least one content-rich conversation if an already-authorized existing conversation with multiple messages is available.

If no content-rich conversation is available, do NOT send or fabricate production messages. Use non-persistent browser-only visual inspection techniques if needed and clearly document that limitation.

QA must explicitly verify:
- no horizontal overflow
- no text clipping
- no accidental English labels in Arabic mode
- narrow mode uses true single-column conversation + contained drawers
- active launcher state is less visually noisy while the window is open
- composer is visibly calmer than V7
- top toolbar has reduced primary-action density
- rail is visibly simpler than V7
- dark/light and RTL/LTR
- Ramzy coexistence
- minimize/maximize/restore/drag/resize remain unchanged
- drafts/saved messages still present
- no viewport-level TCS overlays introduced

## Validation

Run:
- `git diff --check`
- `cd frontend && npm run build`
- `./scripts/tos-production-preflight.sh --live`

If frontend-only, deploy with:
`./scripts/tos-production-deploy.sh --scope frontend`

## Commit / Push rules

- Work only in `/var/www/TOS`
- Actual implementation repo: `mohamedamouseo-a11y/TOS`
- Branch: `main` only
- No new branch
- No force push
- Commit locally
- DO NOT use terminal `git push`
- DO NOT use SSH push
- DO NOT use GitHub CLI push
- DO NOT use PAT/deploy-key push
- Final push ONLY through the authenticated TOS Developer Hub / GitHub integration inside the running TOS system
- Push to `mohamedamouseo-a11y/TOS` `main`

If Developer Hub push is blocked, STOP and report the exact blocker. Do not fall back to another push method.

## Final report

Return:
`TCS_V8_VISUAL_EXCELLENCE_REFINEMENT_REPORT.zip`

Include:
- base SHA
- final local commit SHA
- verified remote SHA
- changed files
- build/preflight/deploy evidence
- Developer Hub push receipt
- all required screenshots
- before/after comparison notes against V7 screenshots
- any remaining visual debt

## Acceptance standard

Do not mark COMPLETE merely because build and deploy pass.

V8 is complete only if the live screenshots visibly demonstrate:
- calmer hierarchy
- chat-first composition
- reduced toolbar density
- simplified rail
- calmer composer
- true narrow single-column behavior
- consistent Arabic localization
- premium light and dark modes
- preserved window mechanics and TCS functionality
