# TSheets Casual — P00 / B01 / V1

**Patch ID:** `TOS-TWS-TSHEETS-CASUAL-P00-B01-UPSTREAM-SOURCE-BASELINE-V1`

## End-user feature
None yet. This is a foundation-only batch.

## What this batch does
- Clones the original public `CasualOffice/sheets` source exactly as upstream.
- Pins it to upstream commit:
  `87a63902d94c85b3c50d3210055373a3d3bae991`
- Initializes the three upstream git submodules recursively.
- Uses HTTPS transparently for submodules so server GitHub SSH keys are not required.
- Places the untouched source at:
  `/var/www/tsheets-casual-upstream`
- Verifies the source is not tracked-dirty.
- Verifies the existing `/var/www/TOS` worktree is unchanged.

## Intentionally NOT done
- No dependency install.
- No build.
- No runtime/service.
- No TOS route.
- No sidebar.
- No branding.
- No database/backend changes.
- No commit or push in the TOS repository.

This keeps the first execution short. The expensive install/build happens once in **P00-B02**, using this already-cloned source.

## Next
`TOS-TWS-TSHEETS-CASUAL-P00-B02-BASELINE-INSTALL-BUILD-SMOKE-V1`
