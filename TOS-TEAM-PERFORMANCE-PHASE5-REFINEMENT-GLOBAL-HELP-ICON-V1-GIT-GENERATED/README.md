# TOS Team Performance — Phase 5 Refinement: Global Help Icon V1

Baseline TOS HEAD: `4fa7ad74489f1e09e16dd63292c240d8a7e6f726`

This refinement is designed to run **after** Phase 5 Help Center + Topbar Help refinement have been applied locally and before they are committed/pushed.

## Goal

Keep the `?` Help Center icon visible in the premium Topbar on **all normal authenticated TOS pages** and for **all authenticated users**.

The existing `TeamPerformanceHelpCenter` component/content is reused unchanged. The help modal is mounted globally in `App.jsx` through a small bridge so it is not constrained by the sticky/backdrop-filter Topbar.

## Changes

- `frontend/src/components/layout/Topbar.jsx`
  - removes the Team Performance-only conditional prop
  - always renders the `CircleHelp` icon
  - emits `tos:global-help`
- `frontend/src/App.jsx`
  - mounts one global Help Center bridge
  - listens for `tos:global-help`
  - removes old Team Performance-only Topbar wiring
- `frontend/src/pages/TeamPerformanceDashboard.jsx`
  - removes the duplicate local Help Center state/listener/render
- `frontend/src/components/performance/TeamPerformanceHelpCenter.jsx`
  - existing Phase 5 content is preserved; no business-logic change

## Safety

No backend, Prisma/schema, migration, package, RBAC, score logic, or Ramzy changes.

Expected working tree before and after this refinement:

```text
 M frontend/src/App.jsx
 M frontend/src/components/layout/Topbar.jsx
 M frontend/src/pages/TeamPerformanceDashboard.jsx
?? frontend/src/components/performance/TeamPerformanceHelpCenter.jsx
```

Run:

```bash
bash run_phase5_global_help_icon_v1.sh
```

Do not commit or push from OpenHands.
