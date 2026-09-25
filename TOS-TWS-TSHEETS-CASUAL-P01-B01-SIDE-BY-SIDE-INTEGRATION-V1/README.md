# TSheets Casual — P01 / B01 / V1

## End-user feature
A second experimental spreadsheet can be opened inside TOS at `/tws/sheets-lab`.

The existing TSheets editor remains untouched at `/tws/sheets/:id`.

## Architecture
Casual Sheets stays isolated at `/var/www/TOS/vendor/tsheets-casual-upstream`.
The upstream web bundle is built with base `/tws-casual-runtime/`, then the TOS frontend build syncs that runtime into its own production `dist`.
The experimental TWS route renders the isolated runtime in an iframe.

No sidebar item and no TSheets rebranding yet. Those are P02.

## Tracked TOS changes
- frontend/src/pages/tws/TSheetsCasualLab.jsx
- frontend/src/pages/tws/TwsPage.jsx
- frontend/scripts/syncTsheetsCasualRuntime.mjs
- frontend/package.json

No backend or DB changes. No old TSheets files edited. No commit/push.
