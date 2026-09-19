# Ramzy Smart Task V3 — R5.9: Premium TOS-Branded Thought Bubble UX/UI

Baseline TOS:
`73480e33a4dfffd5e9aab2948d1f940976d6826e`

Scope ONLY:
Redesign the R5.8 Ramzy thought bubble UX/UI to look premium, polished, and native to the existing TOS visual system.

This is a FRONTEND VISUAL/UX refinement only.

Do NOT change:
- v4 visibility/seen logic
- sequence timing
- pop behavior
- composer prefill behavior
- auto-send behavior
- Smart Task logic
- writing memory/autocomplete/intent
- projects
- assignees
- approvals
- backend
- permissions

## Product direction

The current bubble visually feels like a generic purple tooltip.
TOS uses a warm premium visual language: cream/off-white surfaces, champagne/gold accents, warm dark text, soft borders, and subtle shadows.

Redesign the thought bubble so it looks like it belongs to TOS itself.

It should feel:
- premium
- friendly
- clean
- modern SaaS
- subtly playful
- visually connected to Ramzy
- not cartoonish
- not loud
- not purple/indigo

---

# A) Bubble structure

Refactor the current one-line bubble markup into a structured compact card while preserving the same click behavior.

Suggested structure:

```jsx
<button className="ramzy-thought-bubble ...">
  <span className="ramzy-thought-bubble-topline">
    <span className="ramzy-thought-bubble-badge">
      <Sparkles ... />
      {isEnglish ? "New with Ramzy" : "جديد مع رمزي"}
    </span>
    <span className="ramzy-thought-bubble-dismiss">...</span>
  </span>

  <span className="ramzy-thought-bubble-copy">
    <strong>...</strong>
    <span className="ramzy-thought-bubble-message">...</span>
  </span>

  <span className="ramzy-thought-bubble-cta">
    ...
  </span>

  <span className="ramzy-thought-tail" aria-hidden="true">...</span>
</button>
```

The entire card remains clickable for the existing pop CTA.
The X still stops propagation and only dismisses.

Do NOT nest an actual <button> inside the outer <button>.
The CTA is a styled span/div, not another button.

---

# B) Copy hierarchy

Keep the 3 existing sequence beats, but present them with better visual hierarchy.

Arabic:

Step 0:
- headline: `يا بطل تميز 👋`
- supporting: `عندي لك حاجة جديدة.`

Step 1:
- headline: `ما تيجي نعمل تاسك مع بعض؟ ✨`
- supporting: `قول لي اللي محتاجه وأنا هرتبه معاك خطوة بخطوة.`

Step 2:
- headline: `جاهز نبدأ؟`
- supporting: `افتحني واكتب «اعمل تاسك» وأنا هساعدك تجهزها.`
- CTA: `ابدأ مع رمزي`

English equivalent:

Step 0:
- `Hey Tamiyouz hero 👋`
- `I’ve got something new for you.`

Step 1:
- `Want to build a task together? ✨`
- `Tell me what you need and I’ll shape it with you step by step.`

Step 2:
- `Ready to start?`
- `Open me and type “create a task” — I’ll help you build it.`
- CTA: `Start with Ramzy`

Do not change timing from R5.8.

---

# C) TOS color system

Remove the purple/indigo look from the thought bubble.

Use a warm palette visually consistent with the live TOS UI.

Preferred light theme palette:
- main surface: warm off-white / cream
- secondary surface: very light champagne
- border: soft gold/champagne
- primary accent: muted TOS gold
- text: warm charcoal
- secondary text: warm gray
- CTA: soft gold tint, not a bright saturated button

Example fallbacks only if no existing theme token is available:
- surface: `#fffdf8`
- surface-alt: `#fbf4e6`
- border: `#ead7aa`
- gold: `#c79a43`
- gold-dark: `#8b692c`
- text: `#2e2a23`
- muted: `#71695d`

IMPORTANT:
Before hardcoding these, inspect existing TOS/Ramzy theme variables/classes and reuse established tokens wherever possible.
Prefer existing CSS variables over introducing a second visual system.

No purple/indigo in this component.

---

# D) Premium visual treatment

## Card
- width: approximately 300–340 px desktop
- mobile: max width `calc(100vw - 28px)`
- generous but compact padding
- radius: ~18–22 px
- thin champagne/gold border
- layered soft shadow
- optional subtle inner highlight
- no harsh black shadow
- no glass blur that hurts readability

## Accent
Add one restrained premium detail:
- a thin gold top/side accent line OR
- a tiny warm radial glow behind the Sparkles badge

Do not add large gradients or flashy neon.

## New badge
Small pill:
- Sparkles icon
- `جديد مع رمزي` / `New with Ramzy`
- soft champagne background
- muted gold text/border
- uppercase only in English if it matches existing TOS typography

## CTA
At the bottom:
- visually obvious but compact
- gold-tinted background
- optional Arrow icon if already imported / easy to use
- text `ابدأ مع رمزي` / `Start with Ramzy`
- hover moves/brightens very slightly

The entire bubble remains clickable; CTA is visual affordance only.

---

# E) Thought-tail connection to avatar

Make it actually feel like a thought bubble coming from Ramzy.

Use:
- one small connector bubble near the card
- one smaller connector dot nearer Ramzy avatar
- both warm cream/gold bordered

Position based on `launcherSide`.

For right-side launcher:
- tail/dots should visually lead toward lower-right / avatar

For left-side launcher:
- mirror them

For RTL/LTR, visual connection follows launcher position, not language direction alone.

Do not rely only on `[dir=rtl]` for physical side.

Use the existing classes:
`.ramzy-launcher-wrap.is-left`
`.ramzy-launcher-wrap.is-right`
or the actual side class currently emitted.

---

# F) Stable layout during message sequence

Current message text changes can make the bubble jump in size.

Fix that:
- reserve a stable content area/min-height
- smooth crossfade/slide between text beats
- avoid large width/height jumps
- do not remount the full card on every step

Animation:
- initial entrance: opacity + scale from ~0.94 + translateY(6px)
- duration ~260–340 ms
- message change: subtle 140–220 ms fade/translate
- no excessive bouncing
- keep existing final pop animation on click, but make it refined:
  - scale 1 -> 1.025 -> 0.92 + fade
  - ~220 ms

Respect:
`@media (prefers-reduced-motion: reduce)`
Disable nonessential motion and keep functionality.

---

# G) Hover / focus / accessibility

The bubble is interactive and must look interactive.

Add:
- cursor pointer
- hover: border/shadow/translateY(-1px) subtle
- active: translateY(0) / slight scale
- keyboard `:focus-visible` gold focus ring
- clear X hover target
- minimum reasonable hit area for dismiss
- maintain readable contrast

Do not let the X inherit the whole-card click.

Use semantic aria labels where needed.

---

# H) Placement and viewport safety

Preserve R5.8 launcher-adjacent placement but polish it.

Requirements:
- never clip outside viewport
- never cover the Ramzy avatar
- minimum ~12–16 px gap from avatar
- safe on 1366/1440/1920 desktop
- safe on narrow/mobile screens
- if launcher is near top/bottom edge, keep bubble within viewport
- z-index sufficient above TOS cards/sidebar but below critical modal layers

Do not make the entire page reflow.

---

# I) Open vs closed Ramzy

When Ramzy is CLOSED:
- bubble visually connects to launcher/avatar
- full premium treatment

When Ramzy is OPEN:
- keep the bubble launcher-adjacent and nonblocking OR slightly reduce its vertical offset if needed
- do not place it inside chat messages
- never cover composer/buttons

No logic change to when it shows.

---

# J) Dark mode

Create a true TOS dark equivalent:
- dark warm charcoal surface
- muted gold border/accent
- off-white text
- no purple
- shadow suitable for dark background

Do not simply invert colors.

---

# K) CSS quality

Current R5.8 thought bubble CSS is compressed into one long line.

Rewrite ONLY the thought-bubble related CSS into clean maintainable blocks:
- `.ramzy-thought-bubble`
- topline
- badge
- copy
- headline
- message
- CTA
- dismiss
- tail/dots
- side variants
- hover/focus/active
- dark
- mobile
- reduced-motion
- keyframes

Do not reformat unrelated CSS.

---

# L) Preserve behavior exactly

Must remain true:
1. key remains `tos.ramzy.smart-task-thought-bubble.v4.<userId>`
2. shows once per user/version
3. does not depend on empty chat history
4. auto-hides according to existing R5.8 timing
5. click runs pop
6. click opens Ramzy
7. click prefills `اعمل تاسك` / `Create a task`
8. no auto-send
9. X only dismisses
10. no backend change

---

# M) Regression / visual checks

Add/update focused frontend tests where practical, proving:
- v4 key unchanged
- CTA click behavior unchanged
- no auto-send
- dismiss propagation remains stopped
- side classes support mirrored tail placement
- reduced-motion CSS exists
- no purple/indigo color token remains in thought-bubble rules

Visual QA on live:
1. Desktop 1440-ish width, launcher right
2. Move launcher left and verify tail mirrors
3. Arabic UI
4. English UI
5. open Ramzy
6. closed Ramzy
7. dark mode if supported
8. mobile/narrow width
9. confirm no viewport clipping
10. confirm bubble looks consistent with TOS cream/gold cards

## Verification

Run:
- `npm --prefix frontend run build`
- `npm --prefix backend run test:ramzy` (regression only; backend unchanged)

Deploy:
- existing atomic frontend deploy
- HTTPS 200
- no backend restart required
- commit + push TOS main

Return only:

```
PATCH=RAMZY-SMART-TASK-V3-R5.9
PASS/FAIL=
TOS_COLOR_MATCH=PASS/FAIL
PREMIUM_BUBBLE_UI=PASS/FAIL
THOUGHT_TAIL=PASS/FAIL
SIDE_MIRROR=PASS/FAIL
SEQUENCE_LAYOUT_STABLE=PASS/FAIL
CTA_VISUAL=PASS/FAIL
HOVER_FOCUS=PASS/FAIL
REDUCED_MOTION=PASS/FAIL
DARK_MODE=PASS/FAIL
MOBILE_SAFE=PASS/FAIL
V4_BEHAVIOR_PRESERVED=PASS/FAIL
AUTO_SEND=NO
FRONTEND_BUILD=PASS/FAIL
BACKEND_TEST=PASS/FAIL
LIVE_VISUAL_SMOKE=PASS/FAIL
LIVE_DEPLOY=PASS/FAIL
COMMIT=
PUSH=YES/NO
ERROR=
```
