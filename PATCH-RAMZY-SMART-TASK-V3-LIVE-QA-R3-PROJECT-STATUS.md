# Smart Task V3 — Live QA R3: Professional Project Status Picker

Baseline:
5aac7aecdc258852ce6081b44bd66df41fefdd88

Goal: make Smart Task project picker professional and make project lifecycle status obvious using the REAL ProjectStatus values already returned by /task-create/projects.

Allowed statuses:
PLANNING, ACTIVE, ON_HOLD, DELAYED, COMPLETED, CANCELLED.

Frontend only. Do not change backend/API/DB/permissions/filtering/selection behavior.

Files:
- frontend/src/components/RamzyAssistant.jsx
- frontend/src/components/ramzySmartTaskComposerV1.css
- backend/src/agency-operator/tests/ramzySmartTaskPhase5.test.js (focused source assertions only)

Requirements:

1) Add pure status presentation helper:
smartTaskProjectStatusMeta(status, isEnglish)
Labels:
ACTIVE => Active / نشط
PLANNING => Planning / تخطيط
DELAYED => Delayed / متأخر
ON_HOLD => On hold / متوقف مؤقتًا
COMPLETED => Completed / مكتمل
CANCELLED => Cancelled / ملغي
Unknown => status text or neutral fallback.
Return label + semantic class key only; no business-logic mutation.

2) Project picker rows:
- keep current sanitized/capped name
- add compact status badge on each row
- badge must use the REAL item.status
- do not render clientName
- preserve search using name + clientName
- preserve current keyboard indexes and selection behavior

3) Professional grouping in the picker:
- Active projects: ACTIVE
- Other projects: PLANNING, DELAYED, ON_HOLD
- Closed projects: COMPLETED, CANCELLED
- hide empty section headers
- keep one flat filtered array for keyboard navigation; grouping is presentation only
- search results still respect same grouping after filtering

Section labels:
EN: Active projects / Other projects / Closed projects
AR: المشاريع النشطة / مشاريع أخرى / المشاريع المغلقة

4) Selected project row:
- show sanitized project name + compact real-status badge
- keep Change button
- no clientName

5) CSS:
- clean SaaS-style rows
- status badge pill
- subtle section headers
- ACTIVE green, PLANNING blue/neutral, DELAYED amber, ON_HOLD gray/orange, COMPLETED muted green/gray, CANCELLED muted red
- light/dark mode
- preserve R1 bounded 200px list, vertical scroll, no horizontal overflow
- preserve 2-line clamp
- no oversized blocks

6) Tests:
Assert:
- helper covers all 6 canonical statuses
- picker renders item.status through status helper
- selected row renders smartTask.project.status through status helper
- clientName is still not rendered
- filtering still references clientName
- section labels/groups exist
- existing 90-char cap and 2-line clamp remain

Verify:
npm --prefix frontend run build
npm --prefix backend run test:ramzy

ONE NEW COMMIT.
COMMIT ONLY.
DO NOT PUSH.

Return only:
PATCH=SMART-TASK-V3-LIVE-QA-R3-PROJECT-STATUS
PASS/FAIL=
BASELINE=
NEW_COMMIT=
FILES_CHANGED=
STATUS_BADGES=
GROUPS=
KEYBOARD_FILTERING_PRESERVED=
LIGHT_DARK=
FRONTEND_BUILD=
BACKEND_TEST=
ERROR=
