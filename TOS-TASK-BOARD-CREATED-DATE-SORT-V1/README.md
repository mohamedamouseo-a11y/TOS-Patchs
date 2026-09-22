# TOS Task Board Created-Date Sort V1

Adds a board-level task order selector to the active Tasks board.

Behavior:
- **Board order**: preserves the existing manual Trello-style card order.
- **Newest first**: sorts visible tasks by `createdAt` descending.
- **Oldest first**: sorts visible tasks by `createdAt` ascending.
- Works across all visible members/tasks and composes with the existing filters.
- Saved Views persist the selected date order.
- No backend/API/database changes.

Target:
- `frontend/src/components/ProfessionalTaskBoard.jsx`

Apply source patch only:

```bash
python3 TOS-TASK-BOARD-CREATED-DATE-SORT-V1/apply_task_board_created_date_sort_v1.py /var/www/TOS
```

Then run the normal TOS frontend build/deploy flow. The patch script is idempotent and runs `git diff --check`.
