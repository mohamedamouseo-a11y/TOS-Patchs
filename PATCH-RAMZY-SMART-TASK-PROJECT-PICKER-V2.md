# PATCH — RAMZY SMART TASK PROJECT PICKER V2

## الهدف
تحسين خطوة **اختيار المشروع** داخل مسار **إنشاء مهمة ذكية** في Ramzy بحيث تكون واضحة، سريعة، ومناسبة لعدد مشاريع كبير، بدون تلخبط المستخدم أو إجباره على كتابة الاسم يدويًا.

## المشكلة الحالية
في خطوة `اختار المشروع` داخل Smart Task Creator يتم عرض المشاريع كـ chips كثيرة داخل مساحة صغيرة. هذا يسبب:
- زحمة بصرية.
- صعوبة الوصول للمشروع المطلوب بسرعة.
- تكرار/تشابه أسماء المشاريع يزيد اللبس.
- عدم وضوح هل المشروع Active أو Archived.
- صعوبة الاستخدام عندما يكون عدد المشاريع كبيرًا.

## التصميم المطلوب
استبدال قائمة الـchips الحالية بـ **Project Picker / Searchable Combobox** مخصص لـRamzy.

### 1. رأس الخطوة
اعرض:
- `اختر المشروع`
- نص مساعد صغير: `ابحث بالاسم أو اختر من المشاريع النشطة`

### 2. Smart Search / Searchable Combobox
حقل بحث واضح داخل الـcard:

`ابحث عن مشروع...`

السلوك:
- البحث يبدأ أثناء الكتابة بدون زر Search.
- Debounce خفيف 200–300ms إن كان البحث عبر API.
- يدعم البحث بالعربي والإنجليزي.
- البحث يكون case-insensitive.
- لا يعتبر كلمات مثل `مهمة ذكية` أو `مهمة جديدة` اسم مشروع.

### 3. Active Projects First
عند فتح الخطوة بدون كتابة أي شيء:
- اعرض المشاريع `ACTIVE` فقط افتراضيًا.
- رتب النتائج بالأكثر استخدامًا/الأحدث تعاملًا إن كانت هذه البيانات متاحة بدون تغيير business logic.
- إن لم تكن متاحة، استخدم ترتيبًا ثابتًا منطقيًا مثل updatedAt desc أو name asc.

المطلوب أن يرى المستخدم أولًا المشاريع التي يمكن العمل عليها فعلًا.

### 4. Archived Projects
المشاريع المؤرشفة لا تظهر وسط النتائج الافتراضية.

أضف اختيارًا ثانويًا صغيرًا:
`إظهار المشاريع المؤرشفة`

عند تفعيله:
- يمكن أن تظهر المشاريع المؤرشفة.
- يجب أن تحمل Badge واضح `مؤرشف`.
- لا تخلطها بصريًا مع Active بدون تمييز.

إذا كانت قواعد النظام تمنع إنشاء مهمة على مشروع مؤرشف، اسمح بعرضه في البحث فقط عند الحاجة لكن لا تسمح باختياره، مع توضيح السبب.

### 5. نتيجة المشروع
كل نتيجة في الـdropdown تعرض قدر الإمكان:
- اسم المشروع — العنصر الأساسي.
- اسم الشركة/العميل إن كان متاحًا بالفعل في البيانات.
- Badge للحالة: `نشط` / `مؤرشف`.
- أي معرف قصير فقط إذا كان ضروريًا للتمييز بين أسماء متشابهة.

لا تعرض Metadata غير مهمة.

### 6. Recent Projects
إذا كان من السهل استخراجه من البيانات الحالية بدون تغيير backend كبير:
أضف قسمًا صغيرًا أعلى النتائج:
`المشاريع الأخيرة`
ويعرض آخر 3–5 مشاريع تعامل معها المستخدم.

هذا Enhancement اختياري، وليس شرطًا إذا احتاج تغييرًا معماريًا كبيرًا.

### 7. اختيار المشروع
عند الضغط على المشروع:
- يتم تثبيت الاختيار داخل Smart Task draft.
- تغلق القائمة.
- يظهر المشروع المختار كـ selected row/card واضحة.
- ينتقل Ramzy للخطوة التالية مباشرة إذا كانت كل المتطلبات اللازمة متوفرة.

أضف زرًا صغيرًا:
`تغيير المشروع`
بدل إعادة فتح الخطوة كاملة من البداية.

### 8. No Match
إذا لم توجد نتيجة:
اعرض:
`لا يوجد مشروع مطابق`

مع اقتراح:
`جرّب كتابة جزء من اسم المشروع أو اسم الشركة`

لا تجعل Ramzy يخمن Project ID أو يختار مشروعًا تلقائيًا من نتيجة ضعيفة.

### 9. Keyboard UX
يدعم:
- Arrow Up / Down
- Enter للاختيار
- Escape للإغلاق
- focus واضح

### 10. Mobile / Small Height
في panel Ramzy الصغير:
- dropdown يكون داخل حدود نافذة Ramzy.
- أقصى ارتفاع للنتائج مع scroll داخلي.
- لا يطرد composer خارج الشاشة.
- لا يسبب horizontal scroll.

## Logic Rules
- لا تغيّر صلاحيات المشروع.
- لا تغيّر task creation approval flow.
- لا تنشئ المهمة قبل الموافقة.
- لا تخمن projectId.
- لا ترسل كلمات Smart Task العامة كاسم مشروع إلى `lookup_project`.
- لو المستخدم كتب اسم مشروع نصًا داخل رسالته، يمكن الاستفادة من lookup الحالي ثم عرض أفضل match للمراجعة إذا كانت الثقة غير قطعية.
- لو المستخدم اختار المشروع من الـpicker، اعتبر الاختيار deterministic واستخدم الـprojectId مباشرة.

## Implementation Guidance
ابدأ بفحص:
- `frontend/src/components/RamzyAssistant.jsx`
- Smart Task Creator components/functions داخل نفس الملف أو الملفات المستخرجة منه.
- API الحالية لجلب المشاريع.
- أي endpoint مستخدم حاليًا في project lookup.

يفضل إعادة استخدام API المشاريع الموجودة بدل إضافة endpoint جديد إذا كانت توفر:
- id
- name
- status / archived state
- company/client label عند توفره

إذا كانت القائمة الحالية تُحمّل كل المشاريع مرة واحدة وكان العدد معقولًا، نفذ filtering محليًا.
إذا كان العدد كبيرًا، استخدم search endpoint موجود أو أضف query خفيفة فقط إذا لزم.

## Visual Direction
النمط المطلوب:
- Compact.
- Premium.
- واضح جدًا.
- أقل زحمة من chips الحالية.
- Search field + dropdown results.
- Active status واضح ولكن غير مزعج.
- نفس Design System الخاص بـRamzy/TOS.

## Acceptance Criteria
- المستخدم يستطيع الوصول لأي Active project بسرعة عبر البحث.
- Active projects تظهر افتراضيًا.
- Archived projects لا تظهر افتراضيًا.
- يمكن إظهار Archived عند الحاجة مع تمييز واضح.
- لا توجد قائمة chips مزدحمة كواجهة الاختيار الأساسية.
- اختيار المشروع يثبت بالـprojectId الحقيقي.
- لا يوجد auto-guess لمشروع غير مؤكد.
- لا تغيير في approval / permissions / task execution logic.
- يعمل جيدًا في 1920x1080 و1664x936 و1366x768.

## QA Scenarios
1. افتح Smart Task بدون كتابة مشروع → Active projects تظهر.
2. ابحث عن جزء من اسم مشروع عربي → النتائج الصحيحة تظهر.
3. ابحث باسم إنجليزي → النتائج الصحيحة تظهر.
4. اختر مشروعًا → يتم تثبيت الاختيار والانتقال للخطوة التالية.
5. افتح `تغيير المشروع` → يمكن تبديله بدون فقد باقي المسودة.
6. ابحث عن Archived project → لا يظهر افتراضيًا.
7. فعّل إظهار المؤرشف → يظهر مع Badge واضح.
8. ابحث عن اسم غير موجود → No-match state واضحة.
9. اختبر keyboard navigation.
10. اختبر Ramzy في 1366x768 بدون clipping/overlap.

## OpenHands Prompt

```text
Implement PATCH-RAMZY-SMART-TASK-PROJECT-PICKER-V2 in TOS.

Goal:
Improve the "Choose Project" step inside Ramzy Smart Task Creator. The current chip-based project list is crowded and confusing when many projects exist.

Do NOT change:
- task creation business logic
- approval requirements
- project permissions
- AI provider/model behavior
- unrelated Ramzy chat features

Required UX:

1. Replace the crowded project chips as the PRIMARY project selection UI with a searchable combobox/project picker.

2. Header:
   - Arabic: "اختر المشروع"
   - helper: "ابحث بالاسم أو اختر من المشاريع النشطة"

3. Search field:
   placeholder: "ابحث عن مشروع..."
   - filter while typing
   - Arabic + English
   - case-insensitive
   - debounce 200–300ms only if API-backed

4. Default results:
   - show ACTIVE projects only
   - do NOT show archived projects by default
   - use a stable sensible ordering
   - if recent-project information already exists cheaply, show a small "Recent projects" section (max 3–5); otherwise skip it

5. Archived projects:
   add a compact secondary control:
   "إظهار المشاريع المؤرشفة"

   When enabled:
   - show archived projects
   - mark them clearly with an "مؤرشف" badge
   - if archived projects cannot receive new tasks according to current rules, display them as disabled rather than bypassing permissions

6. Each result should show:
   - project name
   - company/client label if already available
   - status badge (Active/Archived)
   Avoid unnecessary metadata.

7. Selection behavior:
   - selecting a result must use its exact projectId
   - close picker after selection
   - show selected project clearly
   - provide a compact "تغيير المشروع" action
   - preserve the rest of the Smart Task draft when changing project

8. No match state:
   "لا يوجد مشروع مطابق"
   helper:
   "جرّب كتابة جزء من اسم المشروع أو اسم الشركة"

9. Never guess projectId from weak matches.
Never send generic Smart Task words such as:
   مهمة ذكية
   مهمة جديدة
   ذكية
as project names to lookup_project.

10. Keyboard accessibility:
   ArrowUp / ArrowDown / Enter / Escape
   visible focus states

11. Responsive behavior:
   Validate inside Ramzy at:
   - 1920x1080
   - 1664x936
   - 1366x768

   The result list must have an internal max-height + scroll.
   It must not push the composer off-screen.
   No clipping / overlap / horizontal scroll.

Implementation:
- Inspect `frontend/src/components/RamzyAssistant.jsx` first.
- Reuse the existing projects API/data source where possible.
- Do not add a new endpoint unless existing project APIs cannot support the picker safely.
- If projects are already loaded client-side and dataset size is reasonable, prefer local filtering.
- If server search is necessary, keep it lightweight and permission-scoped.

Preserve:
APPROVAL_REQUIRED=YES
AUTO_CREATE_WITHOUT_APPROVAL=NO
PROJECT_PERMISSIONS_CHANGED=NO
TASK_LOGIC_CHANGED=NO

QA scenarios:
1. Open Smart Task -> active project options appear.
2. Arabic partial search works.
3. English partial search works.
4. Selecting project stores exact projectId.
5. Change project preserves other draft fields.
6. Archived hidden by default.
7. Archived visible only after explicit toggle and clearly marked.
8. No-match state works.
9. Keyboard navigation works.
10. 1366x768 has no overlap or clipping.

Before changes:
- inspect current implementation and project API
- create timestamped backups of modified production files if editing on server

After implementation:
- run frontend build
- deploy using existing atomic deployment flow
- perform authenticated live visual QA with Ramzy open
- commit and push exact source changes

Return:
PATCH=RAMZY-SMART-TASK-PROJECT-PICKER-V2
PASS/FAIL=<result>
PROJECT_PICKER_SEARCHABLE=YES/NO
ACTIVE_PROJECTS_DEFAULT=YES/NO
ARCHIVED_HIDDEN_DEFAULT=YES/NO
ARCHIVED_TOGGLE=YES/NO
EXACT_PROJECT_ID_SELECTION=YES/NO
RECENT_PROJECTS=<YES/NO/SKIPPED>
NO_WEAK_PROJECT_GUESS=YES/NO
KEYBOARD_NAVIGATION=YES/NO
DRAFT_PRESERVED_ON_PROJECT_CHANGE=YES/NO
APPROVAL_LOGIC_CHANGED=NO
PROJECT_PERMISSIONS_CHANGED=NO
TASK_LOGIC_CHANGED=NO
1920_PASS=YES/NO
1664_PASS=YES/NO
1366_PASS=YES/NO
BUILD=PASS/FAIL
LIVE_DEPLOY=PASS/FAIL
SCREENSHOTS=<names>
SOURCE_COMMIT=<sha>
PUSH=YES/NO
FILES_CHANGED=<paths>
ERROR=<NONE or exact error>
```
