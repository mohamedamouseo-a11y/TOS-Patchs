# TOS Team Performance — Phase 5 Refinement: Topbar Help V1

Baseline TOS commit:

`4fa7ad74489f1e09e16dd63292c240d8a7e6f726`

This refinement is designed to run **after Phase 5 Help Center V1 has already been applied locally but before it is committed/pushed**.

Expected pre-apply working tree:

```text
 M frontend/src/pages/TeamPerformanceDashboard.jsx
?? frontend/src/components/performance/TeamPerformanceHelpCenter.jsx
```

## What changes

- Adds a `?` / CircleHelp icon to the global premium Topbar beside notifications.
- The icon appears when the active page is Team Performance.
- Clicking it opens the existing Team Performance Help Center.
- Removes the duplicate `Help Center` text button from the Team Performance page header.
- Reuses all Phase 5 Help Center content, search, Arabic/English behavior, backdrop/X/Escape close logic.
- Keeps the Help Center contextual to Team Performance until help content is intentionally built for other TOS pages.

## Files changed in TOS after successful refinement

```text
 M frontend/src/App.jsx
 M frontend/src/components/layout/Topbar.jsx
 M frontend/src/pages/TeamPerformanceDashboard.jsx
?? frontend/src/components/performance/TeamPerformanceHelpCenter.jsx
```

No backend, Prisma, schema, migration, package, score logic, RBAC, or Ramzy changes.

## Run

```bash
cd /var/www/TOS-Patchs/TOS-TEAM-PERFORMANCE-PHASE5-REFINEMENT-TOPBAR-HELP-V1-GIT-GENERATED
bash run_phase5_topbar_help_refinement_v1.sh
```

The runner verifies the exact baseline and exact Phase 5 pre-apply working tree before making any change, builds the frontend, runs `git diff --check`, and does not commit or push TOS.
