# TSheets Casual — P02 / B01 / V1

## End-user feature
- T-Sheets Lab now appears as a nested item directly under TWS in the expanded TOS sidebar.
- Clicking it opens `/tws/sheets-lab`.
- The embedded editor is visually rebranded from Casual Sheets to **T-Sheets** at runtime.
- The original TSheets editor remains untouched.

## Fast-path architecture
This batch does **not** rebuild or patch the Casual Sheets source.

Because the iframe is same-origin, the TOS wrapper applies a branding layer after the editor loads:
- replaces visible "Casual Sheets" text with "T-Sheets";
- replaces the upstream brand mark visually with a green spreadsheet mark + T-Sheets wordmark;
- updates accessibility/title attributes;
- blocks the upstream home-logo navigation so it cannot accidentally open a nested TOS page.

This keeps upstream source clean and makes the batch fast.

## Tracked TOS files
- `frontend/src/components/layout/Sidebar.jsx`
- `frontend/src/pages/tws/TSheetsCasualLab.jsx`

No backend, DB, or upstream-source changes.
