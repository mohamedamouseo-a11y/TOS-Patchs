# TOS Task Details V2.12 Phase 1 R19 — Reset Actual Scroll Owners

VERSION=TOS_TASK_DETAILS_V2_12_PHASE1_R19_RESET_ACTUAL_SCROLL_OWNERS
PATCH=TOS-UXUI-TASK-DETAILS-V2-12-PHASE1-R19-RESET-ACTUAL-SCROLL-OWNERS
BASELINE=LIVE_R18

## QA finding
R18 resets `taskDetailsBodyRef`, but production QA shows a newly opened task still appears at the previous vertical position. Therefore the stale position is owned by an outer/ancestor scroll container, not only by `taskDetailsBodyRef`.

## Fix
- Keep R18 behavior, then also reset the modal, full-page Task Details shell, premium page viewport, scrollable ancestors, document scrolling element, and window scroll position.
- Run immediately, on two animation frames, and one short post-layout timeout whenever `task.id` changes.
- Do not change layout, Right Rail geometry, Assignee behavior, Sidebar, backend, DB, TCS, or Ramzy.

NO_BROWSER_QA=YES
NO_SCREENSHOTS=YES
NO_VISUAL_QA=YES
PUSH=NO
