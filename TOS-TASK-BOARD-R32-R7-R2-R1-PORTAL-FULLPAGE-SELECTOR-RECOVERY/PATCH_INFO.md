# TOS-TASK-BOARD-R32-R7-R2-R1-PORTAL-FULLPAGE-SELECTOR-RECOVERY

Purpose: recover R32_R7_R2 after its preflight assumed the legacy full-page selector must exist verbatim in source CSS. Live DevTools proved the actual conflict is runtime CSS, and source topology proves the portal host is an ancestor of the full-page overlay, while the modal is inside that overlay.

Fix:
- Add one final desktop geometry bridge after R32_R7_R1.
- Correct topology: portal-host -> fullpage overlay -> task modal.
- Re-assert R5 geometry variables with higher specificity than legacy full-page `width:100%`, `height:100dvh`, `position:relative`, and Trello modal fixed-size rules.
- Preserve normal R7_R1 persisted/default geometry, compact minimize, explicit maximize, and mobile fullscreen.
- No backend/API/database changes.
- No source push.

Expected source baseline: live `/var/www/TOS` with R32_R7_R1_R1 applied successfully.
