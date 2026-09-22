# TOS My Workspace Created-Date Sort V1

Adds a fifth selector to **My Workspace** beside:
- All tasks
- Day
- Month

New selector:
- Date order
- Newest first
- Oldest first

Behavior:
- Sorts the already-filtered My Workspace tasks by `createdAt`.
- Existing search/project/day/month filters continue to work unchanged.
- No backend/API/database changes.
- Default option preserves the current order.

Apply:

```bash
python3 TOS-MY-WORKSPACE-CREATED-DATE-SORT-V1/apply_my_workspace_created_date_sort_v1.py /var/www/TOS
```

Then use the normal frontend build/deploy flow. No commit/push is performed by the patch.
