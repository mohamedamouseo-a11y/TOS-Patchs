# TOS-TASK-BOARD-R32-R7-R2-FULLPAGE-GEOMETRY-OVERRIDE-FIX

## Proven root cause
Live DevTools showed the Task Details modal is receiving the correct R5/R7 geometry variables, but a stronger legacy full-page selector still wins with `!important` and forces `width:100%`, `height:100dvh`, `position:relative`, and `max-width:100%`.

The confirmed conflicting selector is:

`html body .tos-task-details-fullpage.tos-task-details-reference-v1.tos-task-details-reference-v2[data-content-dir] .tos-task-details-modal`

This is why R32_R7/R7_R1 source values were deployed correctly but the visible window stayed almost full screen.

## Fix
- Add one final CSS bridge imported after R32_R7_R1.
- On desktop, bind the modal's actual rendered geometry to the existing R5 inline variables with a selector stronger than the legacy full-page rule.
- Preserve React-controlled normal/minimized/maximized geometry, drag, 8-direction resize, persistence, and compact minimize.
- Preserve mobile <=900px fullscreen behavior.
- No task logic, backend, API, DB, permissions, URL navigation, or data changes.
- No source push.

## Expected visible result
- Normal window uses the persisted/default R7_R1 geometry instead of 100%/100dvh.
- Minimized bar uses the compact React geometry instead of legacy CSS dimensions.
- Maximized state still fills the viewport only when explicitly selected.

## Apply target
`/var/www/TOS`

## Safety
Installer validates the live R7_R1 contracts and the proven legacy full-page selector before editing, builds, atomically deploys, validates runtime markers, and rolls back on failure.
