# OpenHands Prompt — Ramzy Typing Performance V1

نفّذ الباتش فقط على السيرفر الحالي لـ TOS.

## ممنوع
- لا تعمل `git pull`
- لا تعمل `git reset`
- لا تعمل `git checkout`
- لا تعمل `git commit`
- لا تعمل `git push`
- لا تعدّل أي ملف يدويًا
- لا تغيّر Backend أو Database أو Routes أو Permissions

## التنفيذ
شغّل الأمر التالي كما هو:

```bash
curl -fsSL "https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/main/TOS-RAMZY-TYPING-PERFORMANCE-V1-GIT-GENERATED/run_ramzy_typing_performance_v1.py" -o /tmp/run_ramzy_typing_performance_v1.py && python3 /tmp/run_ramzy_typing_performance_v1.py
```

الباتش مربوط بالـ baseline التالي:
`509c51eeab1a9b880d902aac5082aa6124996c9b`

ويتحقق من blob ملف Ramzy قبل أي تعديل:
`138c04ef2959ba3d3e99a767653311958dae1195`

بعد التنفيذ:
1. لا تعمل أي تعديل إضافي.
2. لا تعمل push.
3. أرسل stdout/stderr كاملًا كما ظهر.
4. لو ظهر `PASS_FAIL=PASS` اذكر أن المطلوب التالي هو تجربة الكتابة داخل Ramzy يدويًا قبل الـ push.
