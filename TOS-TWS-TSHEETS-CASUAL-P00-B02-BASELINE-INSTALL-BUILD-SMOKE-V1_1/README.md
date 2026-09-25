# TSheets Casual — P00 / B02 / V1_1

Fix for the P00-B02 V1 build failure.

## Root cause
The Casual Sheets checkout intentionally lives under `/var/www/TOS/vendor`.
Its linked `vendor/design-system` declares React as a peer dependency. During
TypeScript compilation, resolution escaped the nested checkout and found the
parent TOS React 19 type package, while the Casual Sheets web app uses React 18.
That produced TS2786 JSX component incompatibilities such as Button/Badge/IconButton.

## Fix
No upstream source code is edited.

During the build only, the runner creates temporary links inside the design
system's untracked `node_modules` pointing to the Casual Sheets web app's own:
- React
- React DOM
- @types/react 18
- @types/react-dom 18

The links are removed after build (including on failure).

## Credit/time optimization
V1 already installed dependencies and built the expensive Univer fork. V1_1:
- reuses the installed pnpm workspace,
- reuses existing Univer `lib/` artifacts when present,
- only rebuilds the SDK/web app and performs localhost smoke.

If the fork artifacts are genuinely missing it falls back to upstream setup.

No TOS route/sidebar/branding/deploy/DB/PM2/nginx changes are made.
