# TOS UX/UI Phase 01 — Dashboard V2

**One screen only:** TOS Dashboard.

This is the rebased Phase 01 package after OpenHands correctly stopped V1 because the live TOS HEAD had moved from `8b29fd2ec2c96ce422b927711310b35fe6c52c61` to `495201cfa490f643d9e28252eb523a4e278f385c`.

## Verification before V2
The newer TOS commit is exactly one commit ahead of the old baseline. Its changed files are limited to Topbar and Team Performance related files. `frontend/src/main.jsx` is unchanged and still has blob `0035c796b14f106b276d53421b8ba4bf1ae99514`. The Dashboard target itself was not changed by that intervening commit.

Therefore Phase 01 can be safely rebased to the current TOS HEAD without changing the intended Dashboard UX/UI design.

## Reference
The GitHub / Developer Hub screen inside TOS remains the visual reference:
- warm ivory / restrained gold light mode,
- slate / gold dark mode,
- stronger text contrast,
- consistent cards, borders and shadows,
- clearer nested rows, filters, controls and hover states,
- no business-logic or data-flow changes.

Ramzy and TCS remain excluded from Phase 01.

## Exact current baseline
- Expected TOS HEAD: `495201cfa490f643d9e28252eb523a4e278f385c`
- Expected `frontend/src/main.jsx` blob: `0035c796b14f106b276d53421b8ba4bf1ae99514`
- Expected source stylesheet Git blob: `595b772283a8280db8fb247c37746ca2de1b2eb7`

The script refuses to run if the TOS working tree is not clean, if any baseline guard differs, or if the Dashboard patch already appears applied.

## Deployment sequence
1. Patch package lives in **TOS-Patchs only**.
2. OpenHands Online updates/pulls `TOS-Patchs` on the server.
3. OpenHands runs the V2 apply script against `/var/www/TOS`.
4. Script applies only the Dashboard visual layer and runs the frontend production build.
5. OpenHands returns the report, `git status`, and `git diff`.
6. OpenHands does **not** commit and does **not** push TOS.
7. After review/approval, the user performs Push from inside the TOS system.

## OpenHands command
```bash
bash TOS-UXUI-PHASE-01-DASHBOARD-GITHUB-REFERENCE-V2/apply_phase01_dashboard_v2.sh /var/www/TOS
```

Expected success marker:
```text
PHASE01_DASHBOARD_V2=PASS
```

If any guard fails, stop and return the exact terminal output. Do not reset, stash, force, commit, or push.
