# OpenHands Prompt — TOS Project Duplicate Audit V1 (READ ONLY)

نفّذ Audit فقط على السيرفر الحالي لـ TOS.

## الهدف
اكتشاف المشاريع المكررة أو المشتبه إنها مكررة في قاعدة بيانات TOS، بدون حذف أو تعديل أي Project أو Task أو File أو Member أو أي Record آخر.

## ممنوع تمامًا
- لا تعمل `git pull`
- لا تعمل `git reset`
- لا تعمل `git checkout`
- لا تعمل `git commit`
- لا تعمل `git push`
- لا تعدّل أي ملف داخل `/var/www/TOS`
- لا تعمل DELETE / UPDATE / INSERT / UPSERT على قاعدة البيانات
- لا تعمل Archive أو Merge لأي مشروع
- لا تغيّر Backend أو Frontend أو Prisma schema أو migrations
- لا تنظف أي duplicate تلقائيًا حتى لو كان واضحًا جدًا

## التنفيذ
شغّل الأمر التالي كما هو:

```bash
curl -fsSL "https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/main/TOS-PROJECT-DUPLICATE-AUDIT-V1-READ-ONLY/audit_project_duplicates_v1.mjs" -o /tmp/audit_project_duplicates_v1.mjs && cd /var/www/TOS/backend && node /tmp/audit_project_duplicates_v1.mjs
```

## ما الذي يجب أن يراجعه الـAudit
- كل Projects الحالية والمؤرشفة.
- Project ID / Name / Code / Client / Status / Stage.
- createdAt / updatedAt / archivedAt.
- عدد Tasks / Files / Members / Meetings / Boards لكل مشروع.
- ربط TCRM إن وجد: sourceKey / crmProjectId / crmDealId / crmClientId.

## تصنيف النتائج
1. `CONFIRMED_EXTERNAL_ID`
   - نفس `crmProjectId` مربوط بأكثر من TOS Project ID.
2. `CONFIRMED_SOURCE_KEY`
   - نفس TCRM `sourceKey` مربوط بأكثر من TOS Project ID.
3. `STRONG_SAME_CLIENT_NAME`
   - مشروعان Active أو أكثر بنفس العميل + نفس اسم المشروع بعد normalization.
4. `REVIEW_NAME_ONLY`
   - نفس الاسم بعد normalization لكن العميل مختلف أو غير موجود؛ للمراجعة فقط وليس Duplicate مؤكد.

## الحماية
الـrunner يفتح Transaction في PostgreSQL بحالة `READ ONLY` قبل قراءة الداتا، لذلك أي محاولة كتابة داخل الـAudit يجب أن تفشل من قاعدة البيانات نفسها.

## المطلوب بعد التنفيذ
1. لا تعمل أي تعديل إضافي.
2. أرسل stdout/stderr كاملًا كما ظهر، بدون اختصار المجموعات.
3. أكد أن آخر التقرير يحتوي على:
   - `AUDIT_COMPLETE=YES`
   - `DATABASE_CHANGES=NONE`
   - `FILES_CHANGED=NONE`
   - `PUSH_PERFORMED=NO`
   - `READY_FOR_AUTOMATIC_CLEANUP=NO`
4. لا تحذف أو تدمج أي مشروع بعد التقرير. سنراجع المجموعات أولًا ثم نبني Cleanup Patch منفصل بموافقة صريحة.
