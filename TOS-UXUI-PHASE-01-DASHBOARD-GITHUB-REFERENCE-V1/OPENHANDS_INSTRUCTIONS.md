# OpenHands — TOS UX/UI Phase 01

Execute **one screen only: Dashboard**.

## Required sequence
1. On the server, update/pull the `TOS-Patchs` repository.
2. Do **not** pull code changes from this patch package into the TOS Git history.
3. Run:

```bash
bash TOS-UXUI-PHASE-01-DASHBOARD-GITHUB-REFERENCE-V1/apply_phase01_dashboard.sh /var/www/TOS
```

4. The script must verify the exact TOS baseline, apply only the Dashboard visual layer, and run the frontend production build.
5. Do **not** create a commit in TOS.
6. Do **not** push TOS to GitHub.
7. Return the complete terminal output from the script plus:

```bash
git -C /var/www/TOS status --short
git -C /var/www/TOS diff -- frontend/src/main.jsx
git -C /var/www/TOS diff --no-index /dev/null frontend/src/styles/dashboard-github-reference.css || true
```

## Scope contract
- Screen: Dashboard only.
- Design reference: current GitHub / Developer Hub screen inside TOS.
- Light mode: warm ivory/gold premium hierarchy.
- Dark mode: slate/gold premium hierarchy.
- Fix faint/hidden typography and weak contrast.
- Unify card borders, shadows, nested rows, filters, hover states and progress tracks on this screen.
- No business logic or data-flow change.
- No Ramzy change in Phase 01.
- No TCS change in Phase 01.
- No commit and no push from OpenHands.

If any guard fails, stop immediately and report the exact mismatch. Do not force, reset, stash, overwrite, commit, or push.
