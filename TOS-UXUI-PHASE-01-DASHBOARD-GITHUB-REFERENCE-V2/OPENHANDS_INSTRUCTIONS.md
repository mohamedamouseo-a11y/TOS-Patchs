# OpenHands Instructions — TOS UX/UI Phase 01 Dashboard V2

Execute only this Phase 01 package on the server.

## Hard rules
- Do NOT push to the TOS GitHub repository.
- Do NOT create any commit in TOS.
- Do NOT reset, stash, clean, overwrite, checkout, or force the TOS working tree.
- Do NOT change Ramzy.
- Do NOT change TCS.
- Do NOT make business-logic/data-flow changes.
- One screen only: Dashboard.

## Why V2 exists
V1 correctly stopped because live TOS HEAD had moved. V2 is guarded against the current baseline:

`495201cfa490f643d9e28252eb523a4e278f385c`

The intervening commit did not modify `frontend/src/main.jsx` or the Dashboard target, so the same Dashboard visual package is intentionally reused against the new baseline.

## Execute
First update/pull the local TOS-Patchs checkout. Then from that checkout run:

```bash
bash TOS-UXUI-PHASE-01-DASHBOARD-GITHUB-REFERENCE-V2/apply_phase01_dashboard_v2.sh /var/www/TOS
```

## On failure
Stop immediately and return the exact terminal output. Do not try to repair, reset, stash, force, commit, or push.

## On success
Return:
- PHASE01_DASHBOARD_V2 status
- build result
- exact changed files
- git status
- git diff summary/details for `frontend/src/main.jsx`
- CSS SHA256
- BUSINESS_LOGIC_CHANGED=YES/NO
- RAMZY_CHANGED=YES/NO
- TCS_CHANGED=YES/NO
- COMMIT_CREATED=NO
- PUSH_PERFORMED=NO

Then stop. The user performs the later Push from inside TOS after review.
