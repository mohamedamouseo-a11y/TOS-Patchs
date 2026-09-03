# TOS UX/UI Phase 01 — Dashboard Dark Consistency V6

Screenshot-driven correction for Dashboard dark mode only.

V5 built successfully but the lower Dashboard cards still rendered light. V6 adds a dedicated `tos-dashboard-page` root class and scopes dark overrides directly to that page, removing the brittle selector dependency.

Run:

```bash
bash TOS-UXUI-PHASE-01-DASHBOARD-DARK-CONSISTENCY-V6/apply_phase01_dashboard_dark_v6.sh /var/www/TOS
```

No reset, stash, commit, or push. After PASS, visually review Dashboard dark mode before pushing from inside TOS.
