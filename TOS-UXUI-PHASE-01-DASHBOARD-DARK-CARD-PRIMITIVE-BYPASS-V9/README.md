# TOS UX/UI Phase 01 — Dashboard Dark Card Primitive Bypass V9

Screenshot-driven correction for the remaining white lower Dashboard sections in Dark Mode.

## Root cause addressed
All remaining white sections are rendered through the shared `Card` primitive, which injects the global `tos-premium-card` class. The upper Dashboard blocks that already render correctly do not use that primitive. V9 keeps the Dashboard-only presentation classes but renders the five lower Dashboard surfaces as native sections, bypassing the shared Card styling conflict. The TWS widget gets an opt-in `dashboardSurface` mode so only its Dashboard instance bypasses the shared Card primitive.

No business logic, Ramzy, TCS, or Light Mode behavior is changed.

## Run

```bash
bash TOS-UXUI-PHASE-01-DASHBOARD-DARK-CARD-PRIMITIVE-BYPASS-V9/apply_phase01_dashboard_dark_v9.sh /var/www/TOS
```

OpenHands must not reset, stash, commit, or push. After visual approval, the user performs Push from inside TOS.
