# PATCH — RAMZY SMART TASK R5.14
# Daily Smart-Task Awareness Bubble

Baseline TOS:
`7707b195b1876fdd4a3afe9544e417279a3224f3`

Scope: awareness bubble only.
Do NOT touch date/time pickers, AI writing, backend, DB, permissions model, or Smart Task payload logic.

## Goal
Teach each eligible user that Ramzy can create a Smart Task.

## Replace current one-time bubble behavior
Current bubble permanently dismisses with:
`tos.ramzy.smart-task-thought-bubble.v4.<userId>`

Replace with per-user daily state:
`tos.ramzy.smart-task-awareness.v1.<userId>`

Suggested value:
```json
{"lastShownDate":"YYYY-MM-DD","shownDays":0,"completed":false}
```

Use LOCAL calendar date, not a rolling 24-hour timer.

## Eligibility
Show only when all are true:
- Ramzy is allowed
- `status.permissions.actions.CREATE_TASK === true`
- `status.executionControl.globalExecutionAllowed === true`
- no Smart Task is currently open
- onboarding not completed
- not already shown today
- shownDays < 10

Wait about 2 seconds after eligibility is known before showing.

## Content
Keep the existing premium thought-cloud visual beside Ramzy.
One feature only: Smart Task creation.

AR:
1. `أقدر أساعدك تعمل مهمة ذكية ✨`
2. after ~2s: `اضغط هنا وخلي رمزي يجهز المهمة معاك: العنوان، المشروع، الموعد، الأولوية والمنفذ.`
CTA: `جرّب مهمة ذكية`

EN:
1. `I can help you create a Smart Task ✨`
2. after ~2s: `Tap here and Ramzy will guide you through the title, project, due date, priority, and assignee.`
CTA: `Try a Smart Task`

Do not rotate through other Ramzy features.

## Behavior
- Count a day when the bubble is shown.
- X or auto-hide = hide for TODAY only.
- It may show again on the next local calendar day.
- Stop after 10 shown days if user never completes the flow.
- Bubble click must open Ramzy and directly call/reuse the existing Smart Task start flow.
- Do NOT only insert `Create a task` into composer.
- Clicking/opening/cancelling does NOT mark complete.

## Completion
Only after successful `api.agent.createTaskProposal(...)`:
- set `completed=true`
- hide bubble
- never show it again for that user/browser

Failed proposal must not complete onboarding.

## Preserve
- all Ramzy/TOS RBAC
- project/workspace scope
- current Smart Task builder
- launcher drag/open behavior
- date/time pickers from R5.13B
- no DB migration

## Focused tests
1. eligible user: bubble appears after ~2s
2. max once per local day
3. next local day: appears again
4. stops after 10 shown days
5. click opens Smart Task directly
6. X/auto-hide does not permanently complete
7. successful proposal sets completed
8. completed user never sees it again
9. no CREATE_TASK permission => no bubble

Run focused frontend tests/build, live visual smoke, deploy frontend, commit.
User handles system push separately if server GitHub auth is unavailable.

Return ONLY:
```
PATCH=RAMZY-SMART-TASK-R5.14-DAILY-BUBBLE
PASS/FAIL=
DAILY_BUBBLE=
ONCE_PER_DAY=
TEN_DAY_LIMIT=
DIRECT_SMART_TASK=
COMPLETION_STOP=
RBAC_PRESERVED=
FRONTEND_BUILD=
LIVE_QA=
LIVE_DEPLOY=
COMMIT=
PUSH=
ERROR=
```
