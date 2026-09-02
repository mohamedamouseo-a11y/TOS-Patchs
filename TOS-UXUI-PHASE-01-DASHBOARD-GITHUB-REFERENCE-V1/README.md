# TOS UX/UI Phase 01 — Dashboard

**One screen only:** TOS Dashboard.

## Reference
The current GitHub / Developer Hub screen inside TOS is the visual reference for this phase.

The package aligns the Dashboard with the same design DNA:
- warm ivory / restrained gold light mode,
- slate / gold dark mode,
- stronger text contrast,
- consistent cards, borders and shadows,
- clearer nested rows, filters, controls and hover states,
- no business-logic or data-flow changes.

Ramzy and TCS are intentionally excluded from Phase 01.

## Exact TOS baseline
- Expected TOS HEAD: `8b29fd2ec2c96ce422b927711310b35fe6c52c61`
- Expected `frontend/src/main.jsx` blob: `0035c796b14f106b276d53421b8ba4bf1ae99514`

The apply script refuses to run if the target baseline or target files do not match. It must not be forced.

## Files delivered by this patch package
- `dashboard-github-reference.css` — Dashboard-only visual layer.
- `apply_phase01_dashboard.sh` — guarded server application + frontend build validation.
- `OPENHANDS_INSTRUCTIONS.md` — exact OpenHands execution contract.

## Deployment sequence
This follows the established TOS workflow:

1. This package is pushed to **TOS-Patchs** only.
2. OpenHands Online pulls/updates `TOS-Patchs` on the server.
3. OpenHands runs the apply script against `/var/www/TOS`.
4. OpenHands validates the build and returns its report/diff.
5. OpenHands does **not** commit and does **not** push TOS.
6. After the result is reviewed and approved, the user performs the normal Push from the TOS system itself to the TOS project repository.

## OpenHands command
From the local `TOS-Patchs` checkout:

```bash
bash TOS-UXUI-PHASE-01-DASHBOARD-GITHUB-REFERENCE-V1/apply_phase01_dashboard.sh /var/www/TOS
```

Expected success markers include:

```text
PHASE01_DASHBOARD=PASS
SCREEN=Dashboard
BUSINESS_LOGIC_CHANGED=NO
RAMZY_CHANGED=NO
TCS_CHANGED=NO
COMMIT_CREATED=NO
PUSH_PERFORMED=NO
```

If a guard fails, stop and return the exact terminal output. Do not reset, stash, overwrite, commit, or push.
