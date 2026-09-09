# OpenHands Prompt — Ramzy Contextual Smart Task V1 R2

نفّذ الباتش فقط على السيرفر الحالي لـ TOS.

## الهدف
خلي واجهة Ramzy الأساسية بسيطة دائمًا بدون زر Smart Task ثابت أو Widgets إضافية.
الاختيارات الذكية تظهر فقط لما المستخدم يطلب إنشاء مهمة، وبعد انتهاء العملية تختفي.

## مهم
Smart Task Composer V1 أصبح موجودًا بالفعل داخل TOS main الحالي، لذلك R2 مبني على الحالة الـcommitted الحالية وليس على dirty Smart Task قديم.

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
curl -fsSL "https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/main/TOS-RAMZY-CONTEXTUAL-SMART-TASK-V1-GIT-GENERATED/run_ramzy_contextual_smart_task_v1_r2.py" -o /tmp/run_ramzy_contextual_smart_task_v1_r2.py && python3 /tmp/run_ramzy_contextual_smart_task_v1_r2.py
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
- HEAD المتوقع: `6d23d9f5ef56856cd87ea671d1b11e474e3a39b7`
- Ramzy source blob المتوقع: `f9210e68d6faa72112f7846a80dda3652dbdd60f`
- Smart Task CSS blob المتوقع: `18ac594a6db8d5f919c39405e2ee4f5824056eeb`
- ملفات Ramzy المستهدفة يجب أن تكون clean قبل التنفيذ؛ unrelated dirty files مسموحة ويجب الحفاظ عليها.

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
