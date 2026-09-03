# TOS UX/UI Phase 01 — Dashboard Dark Consistency V7

Recovery/fix for the V6 guard bug.

V6 used an exact-line grep for the new Dashboard root class, so indentation caused a false failure. V7 uses a robust class check and safely handles either:
- the V5 state, or
- a partial/already-applied V6 state.

Scope: Dashboard only. No Ramzy, TCS, business logic, commit, or push.

Run:

```bash
bash TOS-UXUI-PHASE-01-DASHBOARD-DARK-CONSISTENCY-V7/apply_phase01_dashboard_dark_v7.sh /var/www/TOS
```
