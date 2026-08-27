# TCS V9 — Final Visual Polish + Narrow QA

## Mission
Perform one final, tightly-scoped UX/UI refinement of TCS based on the V8 production screenshots. This is NOT a redesign and MUST NOT add backend/database/features. Preserve all V6/V7/V8 behavior and mechanics.

## Implementation target
- Working directory: `/var/www/TOS`
- Repository: `mohamedamouseo-a11y/TOS`
- Branch: `main` only
- Required base SHA: `14d96c606300e05457e13ed1b868c21093dc697a`

## Primary objective
Close the remaining screenshot-led visual debt so TCS reads as a premium chat product rather than an admin/dashboard surface.

## 1. Active launcher behavior while TCS window is open
The V8 screenshots still show the TCS launcher as a visually prominent floating pill/orb inside the chat composition while the TCS desktop window is already open.

Refine this state so it never competes with the chat canvas/composer:
- When TCS is open, reduce the launcher to a very small unobtrusive dock/orb OR hide it completely if that remains consistent with existing toggle/close behavior.
- It must never cover message content, composer controls, scrollbars, resize handles, or contained overlays.
- Preserve drag persistence and open/close semantics when closed.
- Preserve unread accessibility semantics.
- Do not change Ramzy behavior.

## 2. Conversation rail refinement
The V8 light screenshots still feel card-heavy because many conversation rows render as large repeated rounded gray blocks.

Refine the rail to feel like a premium communication product:
- Use flatter, denser conversation rows with subtle separators/spacing instead of stacked card tiles.
- Keep the selected conversation clearly visible but less visually heavy than a solid oversized black card when possible.
- Improve scan hierarchy for name, unread, presence/avatar, and recency where data already exists.
- Do not fabricate metadata.
- Keep Project chat / Direct chat switching clear and compact.
- Keep search and filters readable without making the rail feel like a dashboard.
- Preserve direct/group/channel functionality and all existing event handlers.

## 3. Header cleanup verification
V8 final hook already moved secondary actions out of the permanent toolbar. Preserve that.

Final visible large-window header should prioritize:
- conversation identity/context
- Search
- Focus mode
- Chat tools

Files / Tasks / Details must remain reachable from existing tools/secondary surfaces, not permanently occupy equal visual weight in the header.

## 4. Narrow-mode final polish
V8 did not produce final post-deployment narrow screenshots because the browser extension timed out. V9 must explicitly validate and, if needed, refine narrow mode.

Required narrow behavior:
- Main conversation is the primary permanent column.
- Rail/navigation must become a contained drawer/sheet or compact switcher, not squeeze beside the message canvas.
- Details/thread/profile/search/task/meeting/template/huddle surfaces must remain contained inside the TCS window.
- Composer must remain fully usable with no clipped send/attachment/mic controls.
- No browser-viewport overlays escaping the TCS frame.
- No overlap with window controls or resize boundaries.

## 5. Message canvas / composer micro-polish
Only make minimal changes if screenshots show need:
- Keep the calmer V8 message lane.
- Preserve restrained accent usage.
- Avoid oversized empty whitespace framing that feels unfinished.
- Keep composer neutral and first-class, not bordered like an admin form.
- Ensure sender/meta/bubble contrast remains clear in Light/Dark.

## 6. Arabic / English consistency
- Remove any remaining mixed-language labels visible in Arabic mode where translations already exist.
- Preserve native RTL alignment and icon flow.
- Preserve clean LTR English layout.
- Do not introduce a second i18n mechanism.

## Non-goals
- No backend changes.
- No Prisma/database migration.
- No new chat features.
- No TNC work.
- No Ramzy changes.
- No launcher/window architecture rewrite.
- No broad design-system rewrite outside TCS.

## Validation
Run:
- `git diff --check`
- `cd /var/www/TOS/frontend && npm run build`
- `./scripts/tos-production-preflight.sh --live`

Live visual QA MUST include final post-deployment screenshots of:
1. Large Arabic Light
2. Large Arabic Dark
3. Large English Light
4. Large English Dark
5. Medium Arabic Light
6. Narrow Arabic Light
7. Narrow English Dark

Also capture one screenshot with TCS open that proves the active launcher no longer competes with the chat canvas/composer.

If authenticated browser tooling fails again, retry using the available normal browser route/session without mutating production data. Do NOT fabricate screenshots. If impossible, report the exact blocker.

## Commit / push / deploy
- Commit locally in `/var/www/TOS`.
- No new branch.
- DO NOT use terminal `git push`.
- DO NOT use SSH push, GH CLI, PAT, or deploy key.
- Push ONLY through the running TOS Developer Hub / GitHub integration.
- Target: `mohamedamouseo-a11y/TOS` → `main`.
- Frontend-only deploy after successful in-system push:
  `./scripts/tos-production-deploy.sh --scope frontend`

## Final artifact
Return:
`TCS_V9_FINAL_VISUAL_POLISH_AND_NARROW_QA_REPORT.zip`

Include:
- final local SHA
- verified remote main SHA
- changed file list
- Developer Hub push receipt
- frontend deploy receipt
- build/preflight results
- all 7 required final screenshots
- explicit before/after notes for launcher, rail, and narrow mode
- any remaining visual debt
