# OpenHands Prompt — Ramzy Contextual Smart Task V1

نفّذ الباتش فقط على السيرفر الحالي لـ TOS فوق Smart Task Composer V1 المطبق حاليًا.

## الهدف
خلي واجهة Ramzy الأساسية بسيطة دائمًا بدون زر Smart Task ثابت أو Widgets إضافية.
الاختيارات الذكية تظهر فقط لما المستخدم يطلب إنشاء مهمة، وبعد انتهاء العملية تختفي.

## ممنوع
- لا تعمل `git pull`
- لا تعمل `git reset`
- لا تعمل `git checkout`
- لا تعمل `git commit`
- لا تعمل `git push`
- لا تعدّل أي ملف يدويًا
- لا تغيّر Backend أو Database أو Routes أو Permissions
- لا تتجاوز Approval Flow الحالي في Ramzy
- لا تضف أي زر دائم جديد في Composer أو Welcome screen

## التنفيذ
شغّل الأمر التالي كما هو:

```bash
curl -fsSL "https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/main/TOS-RAMZY-CONTEXTUAL-SMART-TASK-V1-GIT-GENERATED/run_ramzy_contextual_smart_task_v1.py" -o /tmp/run_ramzy_contextual_smart_task_v1.py && python3 /tmp/run_ramzy_contextual_smart_task_v1.py
```

## السلوك المطلوب
- Ramzy يظل Chat بسيط في الحالة العادية.
- إزالة زر `Smart task / مهمة ذكية` الدائم من Composer.
- إزالة زر إنشاء المهمة السريع من Welcome screen.
- لما المستخدم يكتب طلب إنشاء مهمة مثل:
  - `اعمل تاسك تصميم بوست`
  - `أنشئ مهمة`
  - `create a new task landing page`
  يتم اكتشاف Create Task intent تلقائيًا.
- لو اسم المهمة موجود في نفس الرسالة، يتم استخراجه والانتقال مباشرة لاختيارات المشروع.
- لو الاسم غير موجود، يطلب الاسم أولًا.
- بعدها تظهر اختيارات مؤقتة داخل مسار المحادثة نفسه:
  - المشاريع الحقيقية
  - Due Date presets
  - Priority
  - Assignee من الفريق الحقيقي
  - `خلي رمزي يقترح` عند الحاجة
- بعد اكتمال الاختيارات تختفي الـSmart UI ويرجع Ramzy للشات الطبيعي.
- `افتح التاسك القديم` أو طلب عرض مهمة موجودة لا يجب أن يشغّل Create Task flow.
- إنشاء المهمة النهائي يستمر عبر `CREATE_TASK` + Approval الحالي فقط.

## Guards
- HEAD المتوقع: `048592147387e2b49382f605a04f8d2efd64f61c`
- الباتش يتوقع Smart Task Composer V1 موجود حاليًا في الـdirty worktree.
- Smart Task CSS يجب أن يكون في حالة V1 الأصلية قبل Visual Correction القديم.
- لا تعمل Visual Correction patch القديم؛ هذا الباتش يستبدل اتجاه الزر الدائم بالكامل.

## بعد التنفيذ
1. لا تعمل أي تعديل إضافي.
2. لا تعمل push.
3. أرسل stdout/stderr كاملًا كما ظهر.
4. إذا ظهر `PASS_FAIL=PASS` جرّب يدويًا:
   - رسالة عادية → لا تظهر أي Smart UI.
   - `اعمل تاسك تصميم بوست` → تظهر اختيارات المشروع مباشرة.
   - `أنشئ مهمة` → يطلب اسم المهمة ثم الاختيارات.
   - `افتح التاسك القديم` → لا يفتح Create Task flow.
5. لا تعمل push إلا بعد نجاح التجربة اليدوية.
