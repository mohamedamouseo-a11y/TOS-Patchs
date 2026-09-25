# TSheets Casual — P00 / B02 / V1

**Patch ID:** `TOS-TWS-TSHEETS-CASUAL-P00-B02-BASELINE-INSTALL-BUILD-SMOKE-V1`

## End-user feature
None yet. This confirms the untouched Casual Sheets baseline can be installed, built, and started successfully on the TOS server before we integrate it.

## Uses existing P00-B01 source
No clone and no source re-download:
`/var/www/TOS/vendor/tsheets-casual-upstream`

Pinned upstream:
`87a63902d94c85b3c50d3210055373a3d3bae991`

## What it does
1. Verify pinned source + submodules.
2. Activate upstream-required pnpm 10.33.4.
3. Run upstream `scripts/setup-fork.sh` once.
4. Run frozen-lockfile workspace install.
5. Build `@casualoffice/sheets` SDK.
6. Build `@sheet/web`.
7. Start Vite preview on **127.0.0.1:4173 only**.
8. Require HTTP 200 + valid HTML.
9. Stop preview.
10. Restore temporary Univer package-manifest swaps and require tracked upstream source clean.
11. Verify no existing tracked/staged TOS source outside the vendor folder changed.

## Not done
No TOS route, sidebar, branding, persistence integration, PM2, nginx, database, commit, or push.

## Why this may take longer once
The upstream source vendors a large Univer fork and its own documented setup builds that fork before the web app. This is the one expensive baseline preparation. Later phases reuse the installed workspace and build artifacts/caches rather than repeating the clone/setup unnecessarily.
