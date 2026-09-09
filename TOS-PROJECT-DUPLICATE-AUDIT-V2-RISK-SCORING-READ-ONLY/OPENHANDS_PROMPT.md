# OpenHands Prompt — TOS Project Duplicate Audit V2 (Risk Scoring / READ ONLY)

نفّذ Audit فقط على السيرفر الحالي لـ TOS.

## الهدف
مراجعة مجموعات المشاريع المتشابهة بالاسم التي ظهرت في V1، وتحليل كل Pair داخل كل مجموعة بدرجة Risk Score بدون حذف أو تعديل أي بيانات.

## مهم
هذا Audit تحليلي فقط. التصنيف لا يعطي إذنًا للحذف أو الدمج تلقائيًا حتى لو ظهر `VERY_LIKELY_DUPLICATE`.

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
- لا تحذف أو تدمج أي Project بناءً على الـscore

## التنفيذ
شغّل الأمر التالي كما هو:

```bash
curl -fsSL "https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/main/TOS-PROJECT-DUPLICATE-AUDIT-V2-RISK-SCORING-READ-ONLY/audit_project_duplicates_v2.mjs" -o /tmp/audit_project_duplicates_v2.mjs && cd /var/www/TOS/backend && node /tmp/audit_project_duplicates_v2.mjs
```

## ما الذي يراجعه V2
لكل مجموعة لها نفس اسم المشروع بعد normalization:
- Project ID / Name / Code
- Client ID / Client Name
- Type / Status / Stage / Priority
- Start Date / Due Date / Delivery Date
- Created At / Updated At
- عدد Tasks / Files / Members / Meetings / Boards
- أعضاء الفريق User IDs لقياس Team Overlap
- TCRM sourceKey / crmProjectId / crmDealId / crmClientId
- الفرق الزمني بين تاريخ إنشاء المشروعين
- هل أحد المشروعين Empty Shell والآخر يحتوي على الشغل

## Risk Scoring
كل Pair يتم تصنيفه إلى واحد من:
- `VERY_LIKELY_DUPLICATE` — Score من 70 إلى 100
- `POSSIBLE_DUPLICATE` — Score من 35 إلى 69
- `LIKELY_LEGITIMATE` — Score أقل من 35

الـscore يأخذ في الاعتبار إشارات مثل:
- نفس Client / TCRM IDs
- قرب وقت الإنشاء
- نفس Type / Due Date / Start Date
- Team overlap
- وجود مشروع فارغ بجوار مشروع يحتوي على الشغل

ويخصم نقاط عند وجود إشارات عكسية قوية مثل:
- Clients مختلفين بوضوح
- TCRM project/source IDs مختلفة
- فرق زمني كبير مع وجود شغل فعلي في المشروعين

## الحماية
الـrunner يفتح PostgreSQL Transaction بحالة `READ ONLY` قبل قراءة البيانات. أي محاولة كتابة من داخل الـAudit يجب أن تفشل.

## المطلوب بعد التنفيذ
1. لا تعمل أي تعديل إضافي.
2. لا تعمل push.
3. أرسل stdout/stderr كاملًا كما ظهر.
4. مهم جدًا: لا تختصر الـGroups أو الـPair Scores.
5. يجب أن يحتوي آخر التقرير على:
   - `AUDIT_COMPLETE=YES`
   - `DATABASE_CHANGES=NONE`
   - `FILES_CHANGED=NONE`
   - `PUSH_PERFORMED=NO`
   - `AUTOMATIC_DELETE_ALLOWED=NO`
   - `READY_FOR_CLEANUP=NO`
   - `MANUAL_REVIEW_REQUIRED=YES`
6. لا تعمل Cleanup بعد التقرير. سنراجع أولًا كل `VERY_LIKELY_DUPLICATE` و `POSSIBLE_DUPLICATE` ونبني Cleanup Plan صريح وآمن.
