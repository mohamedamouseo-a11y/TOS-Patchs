# TSheets Casual — P00 / B01 / V1_1

**Patch ID:** `TOS-TWS-TSHEETS-CASUAL-P00-B01-UPSTREAM-SOURCE-BASELINE-V1_1`

This supersedes **P00-B01-V1** before execution.

## Corrected location
The untouched Casual Sheets upstream source is placed **inside the TOS server project tree** at:

`/var/www/TOS/vendor/tsheets-casual-upstream`

It is NOT placed at `/var/www/tsheets-casual-upstream`, and it is NOT mixed into `frontend/src/pages/tws`.

## What this batch does
- Clone original `CasualOffice/sheets` exactly as upstream.
- Pin commit `87a63902d94c85b3c50d3210055373a3d3bae991`.
- Initialize upstream submodules recursively.
- Verify upstream tracked source is clean.
- Verify no existing tracked/staged TOS source outside the vendor target is changed.

## Intentionally not done
No install, build, runtime, route, sidebar, branding, DB, PM2, nginx, commit, or push.

The nested checkout will appear to the parent TOS repo as an untracked vendor directory. That is expected in P00; it is not a tracked TOS source modification.

## Next
`TOS-TWS-TSHEETS-CASUAL-P00-B02-BASELINE-INSTALL-BUILD-SMOKE-V1`
