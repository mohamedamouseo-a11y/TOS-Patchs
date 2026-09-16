# TOS Task Details V2.12 Phase 1 R30 — Time Tracking Premium Rebuild

VERSION=TOS_TASK_DETAILS_V2_12_PHASE1_R30
PATCH=TOS-UXUI-TASK-DETAILS-V2-12-PHASE1-R30-TIME-TRACKING-PREMIUM-REBUILD
BASE_TOS_COMMIT=dc1357a5dcf64000d42dcb98da3df8577efdb0ae
BASE_PATCH_CHAIN=R29
PATCH_SCOPE=TIME_TRACKING_PRESENTATION_ONLY

## Objective
Rebuild the existing Task Details → Time Tracking presentation into the approved premium TOS visual direction while preserving every timer, estimate, permission, and save behavior.

## Latest-code review
The patch was prepared against the latest TOS GitHub main reviewed at `dc1357a5dcf64000d42dcb98da3df8577efdb0ae` and the latest prepared/live Phase 1 patch chain through R29.

The existing Time Tracking implementation is retained:
- `activeTaskTab === "time"` remains the entry condition.
- Expected time editing and `updateEstimatedHours` remain unchanged.
- Remaining time, tracked time, variance, and task total time calculations remain unchanged.
- `startTimeTimer`, `pauseTimeTimer`, `stopTimeTimer`, `cancelTimeTimer`, and manual-time entry behavior remain unchanged.
- Permission checks remain unchanged.

## Implementation
- Add one semantic CSS hook only: `tos-task-time-tracking-panel` on the existing Time Tracking section.
- Add a dedicated imported stylesheet: `taskDetailsV2_12_Phase1R30TimeTrackingPremium.css`.
- Recompose the existing markup visually through CSS only after the single hook is added.
- Premium light/dark parity with warm-gold TOS accents, compact metric cards, refined central tracked-time ring, and a cleaner session-control footer.
- Responsive behavior retained and improved for 1366px and smaller desktop widths.

## Frozen
No changes to:
- timer functions or timer state
- task APIs
- backend / database
- permissions
- task data
- primary tab logic
- R26/R28/R29 behavior
- TCS
- Ramzy
- right rail
- Comments / notifications

## Production installer
```bash
python3 \
  <PATCH_REPO>/TOS-UXUI-TASK-DETAILS-V2-12-PHASE1-R30-TIME-TRACKING-PREMIUM-REBUILD/apply_r30_production.py \
  /var/www/TOS
```

PUSH=NO
