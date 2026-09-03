# Phase 01 Dashboard Runtime Diagnostic V10

Read-only runtime diagnosis after V9 built successfully but the Dark Dashboard cards still rendered white.

Purpose: confirm whether the V9 source markers exist, whether Vite includes the dark-card markers/colors in `frontend/dist`, and which web root/process is actually serving TOS. This package does not modify TOS source, commit, or push.

Run:

```bash
bash TOS-UXUI-PHASE-01-DASHBOARD-RUNTIME-DIAG-V10/diagnose_phase01_dashboard_runtime_v10.sh /var/www/TOS
```
