# TOS My Workspace Review Column Open Fix V2

Fixes Review-column task opening across the My Workspace -> Tasks handoff.

Root cause targeted: some review tasks resolve their project through `task.board.projectId`; the existing handoff/context validation only accepted `task.projectId` / `task.project.id`, so the click looked valid in My Workspace but Task Board rejected the task context.

Frontend only. No backend/DB/TCS/Ramzy changes. No Task Details scroll patch changes.
