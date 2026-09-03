# TOS UX/UI Phase 01 — Dashboard V4

Dashboard-only patch, rebased/validated against the latest TOS code after HEAD advanced to `ee59c7c8e47aadc4c489b17948649208ce2b041c`.

V4 no longer blocks on unrelated repository HEAD movement. It guards the exact committed `main.jsx` and `Dashboard.jsx` blobs plus the Dashboard DOM contract, so unrelated Ramzy/Team Performance work can advance safely.

Run:

```bash
bash TOS-UXUI-PHASE-01-DASHBOARD-GITHUB-REFERENCE-V4/apply_phase01_dashboard_v4.sh /var/www/TOS
```

Expected changes only:
- `frontend/src/main.jsx` — one CSS import.
- `frontend/src/styles/dashboard-github-reference.css` — Dashboard-only visual layer.

The script builds and validates, but never commits or pushes TOS.