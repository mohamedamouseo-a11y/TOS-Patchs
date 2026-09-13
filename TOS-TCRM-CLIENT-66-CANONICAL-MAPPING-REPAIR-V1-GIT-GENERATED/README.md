# TOS-TCRM Client 66 Canonical Mapping Repair V1

This is a one-time controlled database reconciliation for CRM client `66` (`Modern House Furniture`).

It changes only the existing `tos_crm_project_deliveries.project_id` mapping from the stale near-empty shell:

`cmsusfbox007gmxl9y1lubgwe`

to the established operational project:

`cmqgbwzwp0003iml9dtnuaafk`

The script requires strict preconditions, executes inside a transaction, updates exactly one mapping row, and verifies the result before commit.

It does **not**:

- modify either Project row
- archive/delete/merge the stale project
- alter tasks, members, files, activity, or task services
- change schema or source code
- run a TCRM sync
- deploy or restart services

After this repair is independently verified, the next phase is a single controlled TCRM sync for client 66, followed by TOS-side verification that `crmHandoverBrief` was stored on the same canonical operational project without creating another duplicate.
