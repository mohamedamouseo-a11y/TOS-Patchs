# Smart Task V3 — Live QA R4: Correct Project Status Grouping

Baseline local commit:
a2fa9888b6f7ad13f3aad2d0a62036fe190dab96

Fix ONLY the project-status grouping defect introduced in R3.

Current bug:
smartTaskProjectGroup() incorrectly groups PLANNING and DELAYED under "active".
Required grouping is:
- active: ACTIVE only
- other: PLANNING, DELAYED, ON_HOLD
- closed: COMPLETED, CANCELLED
- unknown/empty: other

Also align exact labels with the R3 contract:
- PLANNING => Planning / تخطيط
- ON_HOLD => On hold / متوقف مؤقتًا

Do not change any other behavior, styling, sorting, filtering, permissions, API, backend, DB, or selection logic.

Strengthen the focused regression test so it asserts the exact group mapping for all six statuses and the exact Arabic labels above.

Verify:
npm --prefix frontend run build
npm --prefix backend run test:ramzy

ONE NEW COMMIT.
COMMIT ONLY.
DO NOT PUSH.

Return only:
PATCH=SMART-TASK-V3-LIVE-QA-R4-GROUPING-FIX
PASS/FAIL=
BASELINE=
NEW_COMMIT=
GROUP_MAPPING=
LABELS=
FRONTEND_BUILD=
BACKEND_TEST=
ERROR=
