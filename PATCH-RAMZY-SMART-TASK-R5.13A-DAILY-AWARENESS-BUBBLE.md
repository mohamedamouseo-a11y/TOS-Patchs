# PATCH — RAMZY SMART TASK R5.13A
# Daily Smart-Task Awareness Bubble

Baseline TOS:
`8b593df76498c31f2da8fb86ce4fa32459a359f1`

Scope: bubble only. No date-picker work. No AI-writing work. No backend/DB changes.

Goal:
Teach eligible users that they can create a Smart Task with Ramzy.

Current issue:
The existing thought bubble permanently dismisses after first show via:
`tos.ramzy.smart-task-thought-bubble.v4.<userId>`

Replace with per-user daily onboarding state:
`tos.ramzy.smart-task-awareness.v1.<userId>`

State:
```json
{"lastShownDate":"YYYY-MM-DD","shownDays":0,"completed":false}
```

Rules:
- eligible only if Ramzy allowed + CREATE_TASK permission true + globalExecutionAllowed true + no Smart Task open
- wait about 2 seconds after eligibility
- show max once per LOCAL calendar day
- stop after 10 shown days
- X or auto-hide hides for today only
- clicking bubble opens Ramzy and launches existing Smart Task builder directly
- clicking does NOT mark complete
- successful `api.agent.createTaskProposal(...)` marks completed=true
- once completed, never show again
- failed/cancelled/opened-only Smart Task does not complete
- preserve all RBAC/project logic

Copy:
AR:
`أقدر أساعدك تعمل مهمة ذكية ✨`
then after ~2s:
`اضغط هنا وخلي رمزي يجهز المهمة معاك: العنوان، المشروع، الموعد، الأولوية والمنفذ.`
CTA: `جرّب مهمة ذكية`

EN:
`I can help you create a Smart Task ✨`
then:
`Tap here and Ramzy will guide you through the title, project, due date, priority, and assignee.`
CTA: `Try a Smart Task`

Reuse existing thought-cloud styling. Keep it compact.

Tests:
- once/day
- next local day shows again
- 10-day stop
- click starts Smart Task directly
- successful proposal completes forever
- user without CREATE_TASK never sees it

Frontend build + live smoke + deploy + commit/push.

Return ONLY:
```
PATCH=RAMZY-SMART-TASK-R5.13A-BUBBLE
PASS/FAIL=
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
