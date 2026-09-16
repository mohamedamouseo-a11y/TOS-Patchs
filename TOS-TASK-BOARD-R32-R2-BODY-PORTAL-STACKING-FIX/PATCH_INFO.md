# TOS-TASK-BOARD-R32-R2-BODY-PORTAL-STACKING-FIX

Small recovery patch for the R32 Trello-like task modal.

## Problem
R32/R32_R1 render the backdrop over the Tasks surface, but the Task Details dialog remains invisible in the live UI. The screenshot shows the overlay constrained to the Tasks content region instead of behaving as a viewport-level modal.

## Fix
- Render the existing Task Details/ErrorBoundary tree through `createPortal(..., document.body)`.
- Add a dedicated portal host/stacking layer.
- Keep the existing R32/R32_R1 dialog, prefetch, URL/back navigation, previous/next navigation, permissions, and task logic unchanged.
- No backend/API/database changes.

## Required live baseline
- TOS source baseline originally reviewed: `f3671756ba1c49ae7304509276d52eb5cb69d04d`
- R32 already applied live.
- R32_R1 already applied live.

## Push rule
The installer builds/deploys only. It does not git commit/push `/var/www/TOS`.
