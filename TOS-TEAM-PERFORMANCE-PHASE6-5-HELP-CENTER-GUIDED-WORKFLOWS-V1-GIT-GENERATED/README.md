# TOS Team Performance Phase 6.5 — Guided Workflows & Full Localization

This patch completes the current partial Phase 6.5 implementation on TOS baseline:

`5831f3763a43d43ae16891208f653e03b39f4936`

## Why this patch exists

A previous direct implementation correctly added the supporting navigation/Ramzy bridges in:

- `frontend/src/App.jsx`
- `frontend/src/components/RamzyAssistant.jsx`
- `frontend/src/pages/TeamPerformanceDashboard.jsx`

but `TeamPerformanceHelpCenter.jsx` reverted to the older Phase 5 article-style content.

This patch intentionally preserves those three local modifications and replaces only:

- `frontend/src/components/performance/TeamPerformanceHelpCenter.jsx`

with the final Phase 6.5 Guided Workflows UI.

## Required pre-state

HEAD must be exactly:

`5831f3763a43d43ae16891208f653e03b39f4936`

`git status --short` must contain exactly:

```text
 M frontend/src/App.jsx
 M frontend/src/components/RamzyAssistant.jsx
 M frontend/src/pages/TeamPerformanceDashboard.jsx
```

The runner also verifies that:

- `App.jsx` already contains `tos:help-navigate`
- `RamzyAssistant.jsx` already contains `tos:ramzy-help`

If not, it stops without modifying TOS.

## Result

Exactly four TOS frontend files should be modified:

```text
 M frontend/src/App.jsx
 M frontend/src/components/RamzyAssistant.jsx
 M frontend/src/components/performance/TeamPerformanceHelpCenter.jsx
 M frontend/src/pages/TeamPerformanceDashboard.jsx
```

The Help Center contains 14 guided workflows, Arabic/English localized UI, collapsed More Details, SPA navigation actions, and an Ask Ramzy handoff.

No backend, RBAC, database, Prisma, migration, package, or Performance Score changes are made.

## Apply

```bash
cd /var/www/TOS-Patchs
git pull --ff-only origin main

cd /var/www/TOS-Patchs/TOS-TEAM-PERFORMANCE-PHASE6-5-HELP-CENTER-GUIDED-WORKFLOWS-V1-GIT-GENERATED
bash run_phase6_5_help_center_guided_workflows_v1.sh
```

The runner builds and deploys the frontend to the existing `tamiyouz-frontend` PM2 service.

It does **not** commit or push the TOS repository.
