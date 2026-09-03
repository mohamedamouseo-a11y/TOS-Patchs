# TOS UX/UI Phase 01 — Dashboard Dark Consistency V8

Screenshot-driven fix for the remaining white lower Dashboard cards in Dark Mode.

V8 adds dedicated presentation-only classes to the five lower Dashboard cards plus the TWS wrapper, then applies high-specificity dark overrides. It preserves Light Mode and does not touch business logic, Ramzy, or TCS.

Run:

```bash
bash TOS-UXUI-PHASE-01-DASHBOARD-DARK-CONSISTENCY-V8/apply_phase01_dashboard_dark_v8.sh /var/www/TOS
```

OpenHands must not reset, stash, commit, or push. After visual approval, the user performs Push from inside TOS.
