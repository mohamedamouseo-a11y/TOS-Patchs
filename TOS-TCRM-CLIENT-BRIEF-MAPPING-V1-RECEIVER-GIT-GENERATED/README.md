# TOS ← TCRM Client Brief Mapping V1 — Receiver

First half of the structured Client Brief mapping.

This patch prepares TOS to store the sanitized TCRM Client Handover Brief as `Project.crmHandoverBrief` JSONB while preserving existing TOS operational data and the previously deployed duplicate-prevention logic.

## Scope

- TOS only.
- Adds `crmHandoverBrief Json?` to Prisma `Project`.
- Adds one migration file for the JSONB column.
- Adds receiver validation for object/null and a 50KB guard.
- Does not change Description mapping.
- Does not execute the migration, deploy, restart, sync, cleanup, archive, merge, or delete anything.

## Order

1. Apply this receiver patch on the TOS server and review its diff.
2. After approval, execute the migration + deploy TOS.
3. Then apply the separate TCRM sender patch so the structured brief starts flowing.
4. Run one controlled existing-client sync and verify the same TOS project received the JSON brief.
