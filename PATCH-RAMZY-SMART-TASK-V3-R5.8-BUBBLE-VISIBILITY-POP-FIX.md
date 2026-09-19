# Ramzy Smart Task V3 — R5.8: Thought Bubble Visibility + Correct Pop CTA

Baseline TOS:
`4ec0924f8b57e3c1f165957c0472288ab047f070`

Scope ONLY:
Fix the R5.7 thought bubble so users actually see it and clicking it works.
Do NOT touch writing memory, autocomplete, intent assist, AI writing, projects, assignees, approvals, permissions, or backend.

## Confirmed R5.7 defects

### 1) Bubble is rendered in the wrong place
Current JSX renders `thoughtBubbleVisible` only inside:

```jsx
{!messages.length && !loading && (
  <div className="ramzy-welcome">
    ...
    {thoughtBubbleVisible && ...}
  </div>
)}
```

Therefore users with an existing conversation/history never see the bubble.
It also cannot act as a launcher-adjacent announcement while Ramzy is closed.

### 2) It can be marked "seen" without ever being visible
`showThoughtBubble()` starts the ~7.8 second dismiss timer as soon as execution is available.
Even when the JSX condition above prevents the bubble from rendering, the timer later calls `dismissThoughtBubble()` and stores:
`tos.ramzy.smart-task-thought-bubble.v3.<userId> = 1`

So a user can permanently "see" v3 in storage without seeing anything on screen.

### 3) Pop click uses nonexistent component state/refs
Current `popThoughtBubble()` calls:
- `setIsOpen(true)`
- `setInput(...)`
- `inputRef.current`

Those are not the RamzyAssistant APIs.
The component actually uses:
- `setOpen(true)`
- `setMinimized(false)`
- `setComposerValue(...)`
- `composerRef.current`

This would throw on click.

### 4) Initial dismissed state can be stale if user id is not present on first render
The state initializer returns dismissed=true when `!user?.id`, but does not reliably re-evaluate storage when the user id becomes available.

---

# Required fix

## A) New v4 announcement key
Use a NEW key so users affected by the broken v3 can see the corrected bubble:

`tos.ramzy.smart-task-thought-bubble.v4.<userId>`

Do NOT reuse v3.

When `user.id` changes/becomes available:
- read the v4 key for that exact user
- synchronize dismissed/visible state
- never permanently dismiss only because the initial render had no user id

## B) Render bubble independently of chat history
Move the thought bubble OUTSIDE the `!messages.length && !loading` welcome block.

Preferred placement:
inside `.ramzy-launcher-wrap`, visually attached to the Ramzy launcher/avatar.

It must be able to appear when:
- Ramzy is closed
- Ramzy has old conversation messages
- Ramzy is open
- history exists

Do NOT require:
- empty messages
- empty conversation
- loading=false for chat history

Do not show if:
- `status.executionControl.canExecute !== true`
- Smart Task is already open
- v4 was already seen

## C) Only mark seen when it was actually presented
The auto-hide timer may start only after:
- valid user id exists
- execution is allowed
- the bubble is in visible/renderable state

On:
- auto-hide after the actual visible sequence
- explicit dismiss
- click/pop
then mark v4 seen.

Do not start a hidden timer that writes the seen flag.

## D) Sequence/timing
Keep playful 3-beat sequence:

Arabic:
1. `يا بطل تميز 👋`
2. `ما تيجي نعمل تاسك مع بعض؟ ✨`
3. `افتحني واكتب «اعمل تاسك» وأنا هساعدك تجهزها خطوة بخطوة.`

English:
1. `Hey Tamiyouz hero 👋`
2. `Want to build a task together? ✨`
3. `Open me and type “create a task” — I’ll help you build it step by step.`

Timing:
- beat 1 immediately
- beat 2 ~1.4 s
- beat 3 ~2.8 s
- keep final message visible ~5 s
- total roughly 7.8–8.5 s

Keep small, non-blocking, responsive, RTL/LTR, dark mode.
Use the existing pop/bounce idea.

## E) Correct click/pop behavior
On bubble click:
1. set popping animation
2. after ~220 ms:
   - mark v4 seen
   - hide bubble
   - `setOpen(true)`
   - `setMinimized(false)`
   - `setHidden(false)` if needed
   - `setComposerValue(isEnglish ? "Create a task" : "اعمل تاسك")`
   - focus `composerRef.current`
3. DO NOT auto-send
4. DO NOT directly create/open Smart Task
5. user can edit the prefilled text

Remove all references to:
- `setIsOpen`
- `setInput`
- `inputRef`

## F) Close button
Tiny X must:
- stop propagation
- mark v4 seen
- hide bubble
- not open Ramzy

## G) Prevent timer leaks
Track ALL sequence timers and auto-hide timer.
Clear them on:
- dismiss
- pop
- unmount
- user change
- Smart Task opening

No state updates after unmount.

## H) CSS / placement
Bubble must visually originate from the launcher:
- positioned relative to `.ramzy-launcher-wrap`
- safe placement based on `launcherSide`
- trailing thought circles toward avatar
- readable max width
- must not be clipped by panel/container
- z-index above ordinary page content
- no horizontal viewport overflow
- mobile-safe

Do not place it inside `.ramzy-messages`.

## I) Regression tests
Add focused tests proving:
1. bubble is NOT inside the `!messages.length` welcome condition
2. existing messages do not prevent bubble visibility
3. closed Ramzy launcher can show bubble
4. no v4 seen flag is written before actual visible presentation
5. v4 is marked on auto-hide/dismiss/click
6. user id becoming available after mount can still show bubble
7. pop uses `setOpen + setComposerValue + composerRef`
8. no `setIsOpen/setInput/inputRef` references remain
9. click prefills but does not send
10. Smart Task open suppresses/cleans bubble timers

## Verify
- frontend build PASS
- existing Ramzy tests PASS
- no backend change/reload required
- live QA with a test user/current authorized user:
  - clear ONLY the v4 key if needed for smoke
  - reload live page
  - bubble visibly appears beside Ramzy even with existing history
  - wait through all 3 messages
  - click => pop animation, Ramzy opens, composer contains `اعمل تاسك`/English equivalent, nothing auto-sent
- atomic frontend deploy
- commit + push TOS main

Return only:
```
PATCH=RAMZY-SMART-TASK-V3-R5.8
PASS/FAIL=
ROOT_CAUSE=
BUBBLE_WITH_HISTORY=PASS/FAIL
BUBBLE_WHEN_CLOSED=PASS/FAIL
SEEN_ONLY_AFTER_VISIBLE=PASS/FAIL
POP_CTA=PASS/FAIL
INVALID_REFS_REMOVED=PASS/FAIL
PREFILL_NO_AUTOSEND=PASS/FAIL
TIMER_CLEANUP=PASS/FAIL
FRONTEND_BUILD=PASS/FAIL
BACKEND_TEST=PASS/FAIL
LIVE_BUBBLE_VISIBLE=PASS/FAIL
LIVE_POP=PASS/FAIL
LIVE_DEPLOY=PASS/FAIL
COMMIT=
PUSH=YES/NO
ERROR=
```
