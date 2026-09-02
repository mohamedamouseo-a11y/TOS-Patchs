# OpenHands Instructions — TOS UX/UI Phase 01 Dashboard V3

V2 already applied the intended Dashboard files, built successfully, then failed because Git collapsed the untracked `frontend/src/styles/` directory in porcelain output. Do not revert those intended changes.

## Rules
- Do NOT reset TOS.
- Do NOT stash.
- Do NOT commit.
- Do NOT push.
- Do NOT change any file beyond the two approved Dashboard files.
- Do NOT modify Ramzy or TCS.
- Do NOT alter business logic or data flow.

## Target
- TOS path: `/var/www/TOS`
- Expected TOS HEAD: `495201cfa490f643d9e28252eb523a4e278f385c`
- Screen: Dashboard only

## Execute
Update/pull TOS-Patchs first, then run:

```bash
bash TOS-UXUI-PHASE-01-DASHBOARD-GITHUB-REFERENCE-V3/apply_phase01_dashboard_v3.sh /var/www/TOS
```

The V3 script is idempotent. It accepts either:
1. a clean unapplied Phase 01 baseline and applies the two intended files, or
2. the exact already-applied V2 state and validates/preserves it.

It rejects staged changes, unrelated files, mixed/partial states, altered CSS, unexpected main.jsx content, or a changed TOS HEAD.

## Return
Return the exact final markers and terminal report, including:
- `PHASE01_DASHBOARD_V3=PASS/FAIL`
- build result
- `PATCH_STATE`
- `PATCH_ACTION`
- exact git status
- main.jsx diff
- CSS SHA256
- `BUSINESS_LOGIC_CHANGED`
- `RAMZY_CHANGED`
- `TCS_CHANGED`
- `COMMIT_CREATED`
- `PUSH_PERFORMED`
- `READY_FOR_VISUAL_REVIEW`

After the report, stop. Do not commit or push.