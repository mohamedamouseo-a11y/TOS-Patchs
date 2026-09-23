# TOS THRS Explicit Hourly Permission Request V1

يضيف اختيارًا مستقلًا باسم **طلب إذن** داخل نموذج THRS مع الحفاظ على النوع الداخلي `LEAVE` والتعامل مع أنواع `HOURS` فقط.

- طلب الإجازة يعرض أنواع `DAYS` فقط.
- طلب الإذن يعرض أنواع `HOURS` فقط.
- الإذن يعرض: التاريخ + من الساعة + إلى الساعة + السبب.
- Shadowing / TOS approval / THRS sync بدون تغيير.
- لا Backend changes ولا DB migration.

التطبيق:
```bash
python3 TOS-THRS-EXPLICIT-HOURLY-PERMISSION-REQUEST-V1/apply_thrs_explicit_hourly_permission_request_v1.py /var/www/TOS
```

Acceptance: يظهر `طلب إذن` مستقل، يظل payload canonical `LEAVE`, build ينجح و `/thrs` يرجع HTTP 200.
