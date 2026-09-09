# OpenHands Prompt — Ramzy Smart Task Composer V1

نفّذ الباتش فقط على السيرفر الحالي لـ TOS.

## ممنوع
- لا تعمل `git pull`
- لا تعمل `git reset`
- لا تعمل `git checkout`
- لا تعمل `git commit`
- لا تعمل `git push`
- لا تعدّل أي ملف يدويًا
- لا تغيّر Backend أو Database أو Routes أو Permissions
- لا تتجاوز Approval Flow الحالي في Ramzy

## التنفيذ
شغّل الأمر التالي كما هو:

```bash
curl -fsSL "https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/main/TOS-RAMZY-SMART-TASK-COMPOSER-V1-GIT-GENERATED/run_ramzy_smart_task_composer_v1.py" -o /tmp/run_ramzy_smart_task_composer_v1.py && python3 /tmp/run_ramzy_smart_task_composer_v1.py
```

الباتش مربوط بالـ baseline التالي:
`db1efe2ccf30552ab7c65f7bc672861adf66cc05`

ويتحقق من blob ملف Ramzy قبل أي تعديل:
`509c40b4f283d39fb50e7e2dc146797392d6d1ca`

## المطلوب من الباتش
- إضافة Smart Task Creator داخل Ramzy.
- المستخدم يكتب اسم التاسك فقط أولًا.
- بعدها تظهر المشاريع الحقيقية كاختيارات سريعة.
- Due Date presets: اليوم / بكرة / بعد يومين / بعد أسبوع / بدون موعد.
- Priority choices: High / Medium / Low / خلي رمزي يقترح.
- أعضاء الفريق الحقيقيون يظهرون كاختيارات للـAssignee.
- خيار `خلي رمزي يقترح` للمشروع والمنفذ والأولوية.
- زر `مهمة ذكية` يظل ظاهرًا داخل Composer للوصول السريع في أي محادثة.
- في النهاية يتم إرسال Structured Prompt لمسار `CREATE_TASK` الحالي.
- يجب الحفاظ على Approval Flow الحالي: لا يتم إنشاء المهمة فعليًا قبل اعتماد المستخدم الصريح.

## بعد التنفيذ
1. لا تعمل أي تعديل إضافي.
2. لا تعمل push.
3. أرسل stdout/stderr كاملًا كما ظهر.
4. إذا ظهر `PASS_FAIL=PASS`، المطلوب التالي هو تجربة Smart Task Creator يدويًا على الموقع قبل الـpush.
