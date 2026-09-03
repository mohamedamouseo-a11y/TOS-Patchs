# TOS Team Performance Phase 6.5 — Deep Link & Ramzy Draft Fix V1

This is a corrective Phase 6.5 patch for TOS baseline:

`900859bf88a007ac1b413fda0df8d9e34a49fc50`

## Why this patch exists

Post-push review of the real TOS GitHub commit confirmed the intended four Phase 6.5 files were pushed, but exposed several refinement defects:

1. Some Help Center workflow anchors referenced IDs that do not exist (`phase1-targets`, `phase4-workforce`, `phase4-reviews`, `phase4-skills`, `phase4-talent`, `phase4-recognition`).
2. Cross-page Help navigation attempted to scroll after only one animation frame; the lazy Team Performance page may not be mounted yet.
3. Targets inside closed `PerformanceDisclosure` sections need the disclosure opened before scrolling.
4. Arabic guided steps still contained the visible English term `Drill-down`.
5. Ramzy preserved an existing unsent draft, but the incoming Help Center question became inaccessible. This patch keeps the draft and exposes an explicit `استخدام سؤال مركز المساعدة / Use Help Center question` action.

## Files changed in TOS

Only:

- `frontend/src/App.jsx`
- `frontend/src/components/RamzyAssistant.jsx`
- `frontend/src/components/performance/TeamPerformanceHelpCenter.jsx`
- `frontend/src/pages/TeamPerformanceDashboard.jsx`

No backend, Prisma, database, RBAC, permission defaults, or performance scoring logic changes.

## Apply

```bash
cd /var/www/TOS-Patchs
git pull --ff-only origin main
cd TOS-TEAM-PERFORMANCE-PHASE6-5-DEEP-LINK-RAMZY-DRAFT-FIX-V1-GIT-GENERATED
bash run_phase6_5_deep_link_ramzy_draft_fix_v1.sh
```

The runner requires a clean `/var/www/TOS` at exact HEAD `900859bf88a007ac1b413fda0df8d9e34a49fc50` and performs frontend build, deployment, PM2 reload, HTTP checks, changed-file validation, and `git diff --check`.

Do not commit or push TOS from OpenHands. The owner pushes manually after review.
