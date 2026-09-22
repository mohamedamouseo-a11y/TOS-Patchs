# TOS Task Date Sort Functional Fix V2

Fixes the existing **Newest first / Oldest first** controls in both:

- Tasks Board
- My Workspace

## Root causes

1. **My Workspace:** the summary query selected `createdAt`, but `safeMyWorkspaceTask()` stripped it from the API response before the frontend received it.
2. **Tasks Board:** V1 sorted the global task array, but did not explicitly enforce date order inside each rendered Kanban column.

## Fix

- Return `createdAt` and `updatedAt` in the compact My Workspace payload.
- Enforce creation-date sorting inside every My Workspace column.
- Enforce creation-date sorting inside every Tasks Board Kanban column.
- Use `updatedAt` only as a fallback if `createdAt` is unavailable.
- Preserve existing manual/default board order.
- No database migration or schema change.

Apply:

```bash
python3 TOS-TASK-DATE-SORT-FUNCTIONAL-FIX-V2/apply_task_date_sort_functional_fix_v2.py /var/www/TOS
```
