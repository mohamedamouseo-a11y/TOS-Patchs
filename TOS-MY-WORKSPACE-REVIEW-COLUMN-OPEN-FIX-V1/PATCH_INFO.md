# TOS My Workspace — Review Column Open Fix V1

PATCH=TOS-MY-WORKSPACE-REVIEW-COLUMN-OPEN-FIX-V1

## Symptom
In `/my-workspace`, tasks in the **Review** column can render with `task.project.id` available but without a direct `task.projectId`. Their project name is visible, but the task title is not wired to the open-task action.

## Root cause
`WorkspaceTaskCard` only enables opening when `task.projectId` exists, while the app-level opener already supports `task.project?.id || task.projectId`.

## Fix
- Resolve project identity from `task.projectId || task.project?.id`.
- Use the same resolved project id both for the card open gate and `openTask()`.
- Normalize the task passed to the parent opener so `projectId` is present.
- No backend, DB, Task Details layout, TCS, or Ramzy changes.

NO_BROWSER_QA=YES
NO_SCREENSHOTS=YES
NO_VISUAL_QA=YES
PUSH=NO
