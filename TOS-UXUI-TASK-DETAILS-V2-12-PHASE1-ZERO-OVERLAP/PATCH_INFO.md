# TOS Task Details V2.12 — Phase 1 Zero Overlap

VERSION=TOS_TASK_DETAILS_V2_12_PHASE1_ZERO_OVERLAP
PATCH=TOS-UXUI-TASK-DETAILS-V2-12-PHASE1-ZERO-OVERLAP
BASELINE_CHAIN=TOS_TASK_DETAILS_V2_11J_R3
PATCH_SCOPE=CSS_ONLY
PRIORITY=OVERLAP_FIRST

## Goal
Phase 1 fixes accidental UI collisions before any further Task Details redesign. The patch is based on the real live screenshots supplied after V2.11J_R3.

Highest-priority problems addressed:
1. Main Task Details content must never render under the right rail.
2. Assignee picker must stay viewport-bounded and scroll internally.
3. Status/Priority portal menus must stay viewport-bounded.
4. Due-date calendar must stay viewport-bounded.
5. Legacy/auxiliary Task Details flyouts are capped so they cannot grow across the full task canvas.
6. Narrow screens return the right rail to normal document flow.

## Important terminology
- **TCS = Chat System / team conversation surface.** It is not an assistant.
- **Ramzy / رمزي = AI assistant.**
- Chat System/TCS and Ramzy are separate and frozen in Phase 1.

## Frozen / unchanged
- Task APIs and backend
- Database/schema
- Permissions and authentication
- Task status/priority/assignee business logic
- Timer logic
- Comments, Activity, Attachments behavior
- Chat System/TCS behavior
- Ramzy behavior
- `App.jsx`
- `ProfessionalTaskBoard.jsx`

## Payload
`taskDetailsV2_12_Phase1ZeroOverlap.css`

Runtime marker:
`--tos-task-details-v2-12-phase1-zero-overlap-runtime`

## Installer
The installer validates the V2.11J_R3 baseline, freezes JS hashes, backs up the stylesheet/live build, appends the CSS payload, runs the production frontend build, and swaps the published static build with rollback on failure.

```bash
python3 \
  /var/www/TOS-Patchs/TOS-UXUI-TASK-DETAILS-V2-12-PHASE1-ZERO-OVERLAP/apply_tos_task_details_v2_12_phase1_zero_overlap.py \
  /var/www/TOS
```

## Visual QA acceptance
Test at minimum at 1440×900 and 1366×768 in Arabic RTL:
- Assignee dropdown open: bounded, internal scroll, no page-width takeover.
- Status dropdown open: no clipping outside viewport.
- Priority dropdown open: no clipping outside viewport.
- Due-date picker open: no viewport collision.
- Description + right rail: physical gap remains; no content underneath rail.
- Tabs + right rail: no collision.
- Light mode and Dark mode both stable.
- Chat System/TCS window and Ramzy remain separate and unchanged.

Opening dropdowns for screenshots is allowed; do not select/change task data during QA.

## Rollback
The installer prints `BACKUP_ROOT`. Restore the backed-up stylesheet and published build from that directory/live backup if rollback is required.

PUSH=NO
