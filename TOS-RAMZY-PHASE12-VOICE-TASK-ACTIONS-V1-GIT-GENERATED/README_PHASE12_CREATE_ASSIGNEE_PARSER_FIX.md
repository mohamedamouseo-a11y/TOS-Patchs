# Phase 12 Create Assignee Parser Fix

This corrective patch is for the known Phase 12 state where the main patch applied successfully but the regression test failed because `اعمل تاسك ليوسف` produced an empty `assigneeQuery`.

## Root cause

The CREATE_TASK parser required whitespace after the Arabic assignment prefix `ل`, so it accepted `ل يوسف` but not the common attached form `ليوسف`. The previous tail split could also keep project text inside the assignee value, for example `يوسف في مشروع Cuir`.

## Fix

- Accept both `ليوسف` and `ل يوسف`.
- Support English `for Youssef` / `to Yousef`.
- Strip project/date tail phrases from the assignee query.
- Add regression coverage for Arabic attached/spaced forms, English, and project-tail input.
- Do not reset, clean, commit, or push `/var/www/TOS`.
- Continue validation from the existing known Phase 12 partial working tree.

## Run

```bash
cd /var/www/TOS-Patchs
git pull --ff-only origin main
cd TOS-RAMZY-PHASE12-VOICE-TASK-ACTIONS-V1-GIT-GENERATED
bash run_phase12_create_assignee_parser_fix.sh
```
