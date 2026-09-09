# TOS — Ramzy Smart Task Composer V1

## Goal
تسهيل إنشاء التاسكات داخل Ramzy بدل الاعتماد على أسئلة نصية طويلة أو إدخال تفاصيل كثيرة يدويًا.

## UX Flow
1. اضغط `مهمة ذكية`.
2. اكتب اسم التاسك فقط ثم Enter.
3. اختر المشروع من المشاريع الحقيقية في TOS أو `خلي رمزي يقترح`.
4. اختر Due Date سريع: اليوم / بكرة / بعد يومين / بعد أسبوع / بدون موعد.
5. اختر Priority أو دع Ramzy يقترحها.
6. اختر Assignee من أعضاء الفريق الحقيقيين أو `خلي رمزي يقترح الأنسب`.
7. راجع الملخص واضغط `سلّمها لرمزي`.
8. Ramzy يستخدم مسار `CREATE_TASK` الحالي ويعرض Approval Draft قبل التنفيذ.

## Files changed on TOS
- `frontend/src/components/RamzyAssistant.jsx`
- `frontend/src/components/ramzySmartTaskComposerV1.css` (new)

## Existing APIs reused
- `api.projects.list({ summary: true })`
- `api.users.list({ summary: true })`
- existing `api.agent.streamMessage(...)`
- existing Ramzy `CREATE_TASK` approval flow

## Safety
- No backend changes.
- No DB schema changes.
- No routes changes.
- No permission changes.
- No direct task creation bypass.
- No git commit or git push.
- Baseline guard: `db1efe2ccf30552ab7c65f7bc672861adf66cc05`.
- Ramzy source blob guard: `509c40b4f283d39fb50e7e2dc146797392d6d1ca`.

After a successful run, visually test the full smart-task flow before pushing the server changes to TOS main.
