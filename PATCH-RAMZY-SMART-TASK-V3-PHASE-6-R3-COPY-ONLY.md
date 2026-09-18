# PATCH-RAMZY-SMART-TASK-V3-PHASE-6-R3-COPY-ONLY

Baseline local commit:
cae41f62e5f4e6dd1399f0f65ce4ff46f6949858

Phase 6 logic is accepted. Fix copy only.

## Exact labels
Replace the remaining old Phase 6 labels everywhere they are user-facing in Smart Task / approval detail / approval revision UI:

- Collapsed toggle:
  - EN: Advanced details
  - AR: تفاصيل إضافية

- Expanded toggle:
  - EN: Hide advanced details
  - AR: إخفاء التفاصيل الإضافية

- Estimated hours:
  - EN: Estimated hours
  - AR: الساعات المتوقعة

- Start date:
  - EN: Start date
  - AR: تاريخ البداية

- Reminder:
  - EN: Reminder time
  - AR: وقت التذكير

Also update any exact-label test to assert these final strings.

## Do not change
- reminder validation behavior
- CUSTOM due validation
- advanced validation logic
- submit disabled logic
- RBAC
- approval flow
- CREATE_TASK pipeline
- persistence
- tests unrelated to copy
- Phase 7
- backup files

## Verify
- frontend build PASS
- backend Ramzy tests PASS
- only copy/test changes
- ONE NEW COMMIT
- COMMIT ONLY
- DO NOT PUSH

## Return only
PATCH=RAMZY-SMART-TASK-V3-PHASE-6-R3-COPY-ONLY
PASS/FAIL=
BASELINE_COMMIT=cae41f6
R3_NEW_COMMIT=
LABELS_EXACT=
LOGIC_CHANGED=NO
PHASE7_INCLUDED=NO
FRONTEND_BUILD=
BACKEND_TEST=
UNTRACKED_BACKUPS_UNSTAGED=
ERROR=
