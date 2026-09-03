# TOS UX/UI Phase 01 — Dashboard Dark Consistency V5

Screenshot-driven correction for the Dashboard only.

Observed issue after V4: Light mode was coherent, but in Dark mode the lower Dashboard Card surfaces (Performance, Quick Actions, Projects, Activity, Files and TWS) remained visually white/light while the upper Dashboard was dark.

V5 appends scoped dark-mode overrides to the existing Phase 01 stylesheet. It does not touch Dashboard business logic, Ramzy, TCS, or Light mode.

Run:

```bash
bash TOS-UXUI-PHASE-01-DASHBOARD-DARK-CONSISTENCY-V5/apply_phase01_dashboard_dark_v5.sh /var/www/TOS
```

Expected starting state is the exact uncommitted V4 Phase 01 state (`main.jsx` import + untracked Dashboard stylesheet). OpenHands must not reset, stash, commit, or push. After visual approval, the user performs Push from inside TOS.
