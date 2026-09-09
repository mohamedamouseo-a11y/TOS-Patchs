# OpenHands Prompt — Ramzy Smart Task Button Visual Correction V1

نفّذ الباتش فقط على السيرفر الحالي لـ TOS فوق Smart Task Composer V1 المطبق حاليًا.

## ممنوع
- لا تعمل `git pull`
- لا تعمل `git reset`
- لا تعمل `git checkout`
- لا تعمل `git commit`
- لا تعمل `git push`
- لا تعدّل أي ملف يدويًا
- لا تغيّر أي Logic داخل Smart Task
- لا تغيّر Backend أو Database أو Routes أو Permissions

## التنفيذ
شغّل الأمر التالي كما هو:

```bash
curl -fsSL "https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/main/TOS-RAMZY-SMART-TASK-BUTTON-VISUAL-CORRECTION-V1-GIT-GENERATED/run_ramzy_smart_task_button_visual_correction_v1.py" -o /tmp/run_ramzy_smart_task_button_visual_correction_v1.py && python3 /tmp/run_ramzy_smart_task_button_visual_correction_v1.py
```

## المطلوب
- تعديل Visual فقط لزر `مهمة ذكية / Smart task`.
- إزالة الشكل البنفسجي الحالي بصريًا.
- جعل الزر بنفس هوية Ramzy الذهبية / beige glass.
- النص والأيقونة في سطر واحد بدون wrapping.
- ارتفاع الزر 48px ليطابق Voice control.
- Hover وActive premium gold.
- Dark Mode متناسق.
- على Mobile يتحول الزر إلى أيقونة فقط للحفاظ على المساحة.
- ممنوع تغيير Smart Task workflow أو Approval Flow.

## Guards
- HEAD المتوقع: `048592147387e2b49382f605a04f8d2efd64f61c`
- Smart Task CSS الحالي يجب أن يطابق الحالة التي أنتجها V1 قبل التصحيح.
- يجب أن يكون Smart Task source موجودًا بالفعل.

## بعد التنفيذ
1. لا تعمل أي تعديل إضافي.
2. لا تعمل push.
3. أرسل stdout/stderr كاملًا كما ظهر.
4. إذا ظهر `PASS_FAIL=PASS`، جرّب شكل الزر على الموقع وأرسل Screenshot قبل الـpush.
