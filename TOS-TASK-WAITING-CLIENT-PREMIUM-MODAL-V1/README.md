# TOS Task Waiting Client Premium Modal V1

## الهدف
استبدال browser `prompt()/alert()` عند نقل المهمة إلى `WAITING_CLIENT` بنافذة TOS احترافية داخل Task Details.

## ما يتغير
- Premium modal أبيض + Gold متناسق مع TOS.
- عنوان واضح ومسار الحالة الحالية → بانتظار العميل.
- textarea متعددة الأسطر بدل prompt.
- 4 أسباب سريعة:
  - في انتظار رد العميل
  - في انتظار اعتماد العميل
  - في انتظار ملفات من العميل
  - في انتظار معلومات من العميل
- Validation داخل النافذة بدون browser alert.
- زر تأكيد النقل مع loading state.
- Escape للإلغاء و Ctrl/Cmd+Enter للتأكيد.
- يحافظ على نفس `status=WAITING_CLIENT` و `blockedReason` والـ backend الحالي.

## الملف المستهدف
`frontend/src/components/ProfessionalTaskBoard.jsx`

## التطبيق
```bash
python3 TOS-TASK-WAITING-CLIENT-PREMIUM-MODAL-V1/apply_waiting_client_premium_modal_v1.py /var/www/TOS
```

بعدها build/deploy بالطريقة الإنتاجية المعتادة.

## Acceptance
- لا يظهر browser prompt أو alert عند اختيار بانتظار العميل من Task Details.
- لا يمكن التأكيد بدون سبب.
- اختيار Quick Reason يملأ textarea ويمكن تعديله.
- السبب يُحفظ في blockedReason مع تغيير الحالة.
- Cancel لا يغيّر المهمة.
- Arabic/English + dark mode يعملوا.
- build ينجح و /tasks يرجع HTTP 200.
