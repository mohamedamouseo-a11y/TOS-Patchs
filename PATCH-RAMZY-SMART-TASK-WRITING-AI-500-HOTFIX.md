# PATCH — RAMZY SMART TASK WRITING AI 500 HOTFIX

Baseline:
`8fac68094c197d02040b0349d39c08194e131867`

Issue:
Smart Task `Improve Title with Ramzy` / description writing can return HTTP 500 when a project context is present.

Confirmed source:
`backend/src/agency-operator/services/ramzyAi.service.js`

`generateTaskTitle()` and `generateTaskDescription()` call:
`getSmartTaskWritingContext({ ..., db: prisma })`
but this module does not import `prisma`.

Fix:
1. Import the canonical Prisma client from the same backend module used elsewhere:
   `import { prisma } from "../../prisma.js";`
   Verify relative path against the actual file location before applying.
2. Do not create a second Prisma client.
3. Preserve provider/model/settings/prompt behavior.
4. Preserve project access/Ramzy permission checks in routes.
5. Add focused regression tests proving title + description generation with non-null projectId no longer throws `ReferenceError: prisma is not defined`.
6. Verify both:
   - title improvement with project selected
   - description write/improve with project selected
7. Backend test + live authenticated smoke.
8. Deploy backend only if needed, commit + push.

Do NOT touch:
- Smart Task UI
- date picker patch
- permissions
- provider/model configuration
- DB/schema

Return ONLY:
```
PATCH=RAMZY-SMART-TASK-WRITING-AI-500-HOTFIX
PASS/FAIL=
ROOT_CAUSE=PASS/FAIL
TITLE_WITH_PROJECT=PASS/FAIL
DESCRIPTION_WITH_PROJECT=PASS/FAIL
NO_PROVIDER_CHANGE=PASS/FAIL
BACKEND_TEST=PASS/FAIL
LIVE_SMOKE=PASS/FAIL
LIVE_DEPLOY=PASS/FAIL
DB_MIGRATION=NO
COMMIT=
PUSH=YES/NO
ERROR=
```
