# TOS Global Header Premium Dark UX/UI V1

Purpose: fix the global topbar visual mismatch in Dark Mode without changing light mode, navigation logic, permissions, notifications, profile behavior, language/theme switching, sidebar, or Team Performance functionality.

## Why
`Topbar.jsx` already contains dark Tailwind classes, but the global design-system CSS layer can override the topbar background/surface. The result can be a bright/white header inside an otherwise premium dark page.

## Result
Dark mode only:
- compact 68px premium topbar
- deep charcoal/graphite surface
- restrained gold accent glow
- low-contrast border and shadow
- smaller title/subtitle hierarchy
- unified dark action cluster
- cleaner user chip
- compact notification/theme/language buttons
- notification badge remains clearly visible
- responsive mobile sizing

Light mode remains unchanged.

## Files applied to TOS
- modified: `frontend/src/components/layout/Topbar.jsx`
- added: `frontend/src/components/layout/premiumHeaderDark.css`

The runner is intentionally designed to execute on the current local working tree that already contains the approved Team Performance Premium Dark + Phase 1 UX changes.

## Run
```bash
bash run_global_header_premium_dark_v1.sh
```

The runner validates the exact expected working tree, applies the generator, performs dark-only scope guards, runs `git diff --check`, and builds the frontend.

It does not commit or push TOS.
