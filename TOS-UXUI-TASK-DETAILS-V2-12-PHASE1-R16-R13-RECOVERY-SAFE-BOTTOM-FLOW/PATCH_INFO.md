# TOS Task Details V2.12 Phase 1 R16 — R13 Recovery + Safe Bottom Flow

VERSION=TOS_TASK_DETAILS_V2_12_PHASE1_R16_R13_RECOVERY_SAFE_BOTTOM_FLOW
PATCH=TOS-UXUI-TASK-DETAILS-V2-12-PHASE1-R16-R13-RECOVERY-SAFE-BOTTOM-FLOW
BASELINE=LIVE_R15

## QA finding
R13 had the correct visual composition: Task/Hero unchanged, rail in the physical right empty lane. R14/R15 attempted to fix the lower rail cutoff but introduced excessive/unstable bottom geometry and blank canvas at the scroll end.

## Fix
- Restore the R13 structural rail slot behavior (`height:0`) and keep its physical-right docking unchanged.
- Explicitly neutralize R14/R15 min-height/auto-height overrides.
- Add only a small normal-flow bottom reserve (120px) after the Task Details layout so the final right-rail card is reachable by the existing single Task Details scroller.
- No second scrollbar.
- No Task/Hero movement or resizing.
- No change to Sidebar, backend, DB, TCS or Ramzy.

NO_BROWSER_QA=YES
NO_SCREENSHOTS=YES
NO_VISUAL_QA=YES
PUSH=NO
