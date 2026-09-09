# TOS — Ramzy Smart Task Button Visual Correction V1

Visual-only correction for the `Smart task / مهمة ذكية` launcher after Smart Task Composer V1 is already applied on the server.

## Why
The first Smart Task launcher used an indigo/purple treatment and could wrap its label onto two lines, which visually conflicted with Ramzy's existing beige/gold flagship composer.

## Result
- 48px high premium pill aligned with the Voice control.
- Single-line icon + label.
- Beige/gold glass styling matching Ramzy's flagship light theme.
- Gold hover/active states.
- Coordinated dark mode.
- Mobile collapses to icon-only at <=640px.

## Scope
Only `frontend/src/components/ramzySmartTaskComposerV1.css` is visually amended on the current server working tree.
No Smart Task logic, API calls, approval behavior, backend, database, routes, or permissions are changed.

## Server state expected
- Git HEAD: `048592147387e2b49382f605a04f8d2efd64f61c`
- Smart Task Composer V1/R2 is already applied but not pushed yet.
- Current Smart Task CSS blob before this visual correction: `18ac594a6db8d5f919c39405e2ee4f5824056eeb`.

After PASS, visually recheck the button before pushing the combined server changes to TOS main.
