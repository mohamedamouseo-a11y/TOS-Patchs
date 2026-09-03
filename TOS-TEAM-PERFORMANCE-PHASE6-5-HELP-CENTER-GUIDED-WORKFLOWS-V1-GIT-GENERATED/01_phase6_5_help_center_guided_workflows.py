#!/usr/bin/env python3
from pathlib import Path

TOS = Path("/var/www/TOS")
TARGET = TOS / "frontend/src/components/performance/TeamPerformanceHelpCenter.jsx"

CONTENT = r"""import { useEffect, useMemo, useState } from "react";
import { BookOpen, ChevronDown, ExternalLink, Search, Sparkles, X } from "lucide-react";

function actionLabel(isAr, action) {
  if (!action) return "";
  const labels = {
    teamPerformance: ["فتح أداء الفريق", "Open Team Performance"],
    kpis: ["فتح مؤشرات الأداء", "Open KPIs"],
    summary: ["فتح الملخص الإداري", "Open management summary"],
    executive: ["فتح مركز القيادة", "Open Executive Command Center"],
    archive: ["فتح الأرشيف", "Open archive"],
    permissions: ["فتح الصلاحيات", "Open permissions"],
  };
  const pair = labels[action.labelKey] || ["فتح", "Open"];
  return isAr ? pair[0] : pair[1];
}

export function TeamPerformanceHelpCenter({ open, onClose, lang = "en", initialArticle = "overview" }) {
  const isAr = String(lang || "").toLowerCase().startsWith("ar");
  const tx = (ar, en) => (isAr ? ar : en);
  const [query, setQuery] = useState("");
  const [selectedKey, setSelectedKey] = useState(initialArticle || "overview");
  const [detailsOpen, setDetailsOpen] = useState(false);

  const workflows = useMemo(() => [
    {
      key: "overview",
      group: tx("الأساسيات", "Basics"),
      title: tx("كيف أراجع أداء الفريق؟", "How do I review team performance?"),
      description: tx("ابدأ بالفترة والفلاتر، ثم انتقل من المؤشرات إلى تفاصيل الموظفين عند الحاجة.", "Start with the period and filters, then move from KPIs to employee detail when needed."),
      keywords: tx(["أداء", "فريق", "مؤشرات", "ملخص"], ["performance", "team", "kpi", "summary"]),
      steps: [
        { text: tx("افتح صفحة أداء الفريق.", "Open Team Performance."), action: { page: "teamPerformance", anchor: "team-performance-kpis", labelKey: "teamPerformance" } },
        { text: tx("اختر الفترة المطلوبة ثم القسم أو الموظف إن لزم.", "Choose the reporting period, then department or employee if needed.") },
        { text: tx("راجع مؤشرات الأداء الأساسية والاتجاهات.", "Review the main performance KPIs and trends."), action: { page: "teamPerformance", anchor: "team-performance-kpis", labelKey: "kpis" } },
        { text: tx("راجع الملخص الإداري لمعرفة أين تحتاج المتابعة.", "Review the management summary to see where follow-up is needed."), action: { page: "teamPerformance", anchor: "team-performance-management-summary", labelKey: "summary" } },
        { text: tx("افتح الموظف أو الـDrill-down عندما تحتاج السبب وراء الرقم.", "Open employee detail or drill-down when you need the reason behind a number.") },
      ],
      details: [
        tx("التقرير الحي يشمل المستخدمين النشطين فقط داخل نطاق صلاحياتك.", "The live report includes ACTIVE users only inside your permission scope."),
        tx("المستخدم المعطل لا يدخل مؤشرات التقرير الحي، والمستخدم المعلّق لا يظهر في التقرير الحي أو الأرشيف.", "DISABLED users do not affect live KPIs, while PENDING users are excluded from both live performance and archive."),
        tx("الفترة والفلاتر تضيق نفس مجموعة البيانات المستخدمة في العرض.", "Period and filters narrow the same dataset used by the view."),
      ],
      ramzyPrompt: tx("لخص أداء فريقي في الفترة الحالية باستخدام بيانات أداء الفريق المسموح لي بها، ووضح أهم نقاط القوة والمخاطر وما الذي يستحق المتابعة.", "Summarize my team's performance for the current period using only Team Performance data I am authorized to access. Highlight strengths, risks, and what needs follow-up."),
    },
    {
      key: "performance-decline",
      group: tx("التحليل", "Analysis"),
      title: tx("كيف أعرف سبب انخفاض أداء موظف؟", "Why did an employee's performance decline?"),
      description: tx("راجع الدرجة ومكوناتها ثم ارجع إلى التأخير والساعات والنشاط الفعلي.", "Review the score and its components, then trace overdue work, hours, and activity."),
      keywords: tx(["انخفاض", "موظف", "درجة", "أسباب"], ["decline", "employee", "score", "reason"]),
      steps: [
        { text: tx("افتح أداء الفريق واختر الفترة المطلوبة.", "Open Team Performance and select the reporting period."), action: { page: "teamPerformance", anchor: "team-performance-kpis", labelKey: "teamPerformance" } },
        { text: tx("ابحث عن الموظف وافتح تفاصيله.", "Find the employee and open their detail.") },
        { text: tx("راجع درجة الأداء ومكوناتها لمعرفة أي مكوّن انخفض.", "Review the performance score breakdown to identify the weak component.") },
        { text: tx("راجع المهام المتأخرة والساعات المسجلة والنشاط.", "Review overdue tasks, logged hours, and activity.") },
        { text: tx("قارن بالفترة السابقة قبل استخلاص نتيجة إدارية.", "Compare with a previous period before drawing a management conclusion.") },
      ],
      details: [
        tx("درجة الأداء = 35% الإنجاز + 25% الالتزام بالموعد/التأخير + 20% كفاءة الوقت + 10% جودة سير العمل + 10% الاستمرارية.", "Performance Score = 35% Completion + 25% On-time/Overdue + 20% Time Efficiency + 10% Workflow Quality + 10% Consistency."),
        tx("إذا لم تتوفر بيانات مؤهلة لمكوّن، يتم استبعاده وإعادة تطبيع الأوزان المتاحة إلى 100.", "If a component has no eligible data, it is skipped and the available weights are normalized back to 100."),
        tx("عدم وجود نشاط مؤهل يعني عدم وجود درجة أو ترتيب؛ لا يتم اختراع صفر.", "No eligible activity means no score and no rank; a fake zero is not assigned."),
      ],
      ramzyPrompt: tx("اشرح لي سبب انخفاض أداء الموظف الذي سأختاره في الفترة الحالية باستخدام بيانات أداء الفريق المسموح لي بها، ووضح درجة الأداء ومكوناتها والمهام المتأخرة والساعات المسجلة بدون افتراض بيانات غير موجودة.", "Explain why the employee I select has lower performance in the current period using only Team Performance data I am authorized to access. Explain the performance score, its components, overdue tasks, and logged hours without inventing missing data."),
    },
    {
      key: "period-compare",
      group: tx("التحليل", "Analysis"),
      title: tx("كيف أقارن الأداء بفترة سابقة؟", "How do I compare performance periods?"),
      description: tx("ثبّت الفترة الحالية ثم اختر مرجع مقارنة مناسبًا واقرأ الاتجاه لا الرقم وحده.", "Fix the current period, select a relevant comparison baseline, and read the trend rather than a single number."),
      keywords: tx(["مقارنة", "فترة", "سابق", "اتجاه"], ["compare", "period", "previous", "trend"]),
      steps: [
        { text: tx("افتح أداء الفريق واختر الفترة الحالية.", "Open Team Performance and choose the current period."), action: { page: "teamPerformance", anchor: "team-performance-kpis", labelKey: "teamPerformance" } },
        { text: tx("فعّل المقارنة واختر الفترة السابقة أو الشهر السابق أو العام السابق أو نطاقًا مخصصًا.", "Enable comparison and choose previous period, previous month, previous year, or a custom range.") },
        { text: tx("راجع تغير متوسط الدرجة والإنجاز والتأخير.", "Review changes in average score, completion, and overdue work.") },
        { text: tx("افتح تفاصيل الموظف إذا كان التغير محصورًا في شخص أو مجموعة.", "Open employee detail if the change is concentrated in a person or group.") },
      ],
      details: [
        tx("الفترة السابقة تستخدم نطاقًا مساويًا مباشرة قبل الفترة الحالية عندما يكون هذا الخيار مستخدمًا.", "Previous period uses an equal-length range immediately before the current period when that option is selected."),
        tx("المقارنة لا تغيّر الفترة الحالية؛ هي تضيف مرجعًا مستقلًا.", "Comparison does not change the current period; it adds a separate reference baseline."),
      ],
      ramzyPrompt: tx("قارن أداء فريقي في الفترة الحالية بالفترة المرجعية المختارة وفسر أهم التغيرات باستخدام البيانات المسموح لي بها فقط.", "Compare my team's current performance with the selected reference period and explain the most important changes using only data I am authorized to access."),
    },
    {
      key: "overdue",
      group: tx("التحليل", "Analysis"),
      title: tx("كيف أعرف سبب التأخير؟", "How do I investigate overdue work?"),
      description: tx("ابدأ بحجم التأخير ثم انزل إلى الموظف والمهمة والسياق التشغيلي.", "Start with overdue pressure, then drill into the employee, task, and operational context."),
      keywords: tx(["متأخر", "تأخير", "موعد", "مهام"], ["overdue", "delay", "due", "tasks"]),
      steps: [
        { text: tx("افتح مؤشرات أداء الفريق وحدد حجم المهام المتأخرة.", "Open Team Performance KPIs and identify overdue pressure."), action: { page: "teamPerformance", anchor: "team-performance-kpis", labelKey: "kpis" } },
        { text: tx("حدد الموظف أو القسم الذي يحمل أعلى ضغط تأخير.", "Identify the employee or department carrying the highest overdue pressure.") },
        { text: tx("افتح الـDrill-down وراجع المهمة والموعد والحالة والنشاط.", "Open drill-down and review the task, due date, status, and activity.") },
        { text: tx("افصل بين عائق تشغيلي وبين ضعف في المتابعة قبل اتخاذ إجراء.", "Separate an operational blocker from a follow-up issue before acting.") },
      ],
      details: [
        tx("مؤشر المهام المتأخرة يجمع المهام المتأخرة داخل النطاق الحالي.", "Overdue Tasks sums overdue work inside the current scope."),
        tx("في مكوّن الالتزام بالموعد، التأخير يطبق خصمًا قدره 5 نقاط لكل مهمة متأخرة بحد أقصى 25 نقطة.", "Inside the on-time component, overdue work applies a 5-point penalty per overdue task, capped at 25 points."),
      ],
      ramzyPrompt: tx("حلل أسباب التأخير الحالية في فريقي باستخدام بيانات المهام وأداء الفريق المسموح لي بها، وحدد أين أحتاج مراجعة تشغيلية بدون افتراض أسباب غير موجودة.", "Analyze current overdue work in my team using authorized task and Team Performance data, and identify where operational review is needed without inventing causes."),
    },
    {
      key: "goals",
      group: tx("الإدارة", "Management"),
      title: tx("كيف أراجع الأهداف ونسبة تحقيقها؟", "How do I review goals and target achievement?"),
      description: tx("راجع الهدف والفترة والنتيجة المحققة، ثم اربط الفجوة ببيانات الأداء الفعلية.", "Review the target, period, achieved result, and then connect any gap to actual performance data."),
      keywords: tx(["هدف", "أهداف", "تحقيق", "نسبة"], ["goal", "target", "achievement"]),
      steps: [
        { text: tx("افتح أداء الفريق وانتقل إلى قسم الأهداف.", "Open Team Performance and go to Goals & Targets."), action: { page: "teamPerformance", anchor: "phase1-targets", labelKey: "teamPerformance" } },
        { text: tx("اختر الهدف والفترة والموظف أو الفريق المطلوب.", "Select the goal, period, and employee or team.") },
        { text: tx("راجع القيمة المستهدفة مقابل المحقق ونسبة الإنجاز.", "Compare the target value with the achieved value and achievement rate.") },
        { text: tx("افتح تفاصيل الأداء لفهم سبب الفجوة بدل الحكم من الهدف وحده.", "Open performance detail to understand the gap instead of judging from the target alone.") },
      ],
      details: [tx("الأهداف تستخدم منطق TOS الحالي؛ مركز المساعدة لا يغيّر طريقة حسابها.", "Goals use existing TOS logic; Help Center does not change target calculations.")],
      ramzyPrompt: tx("راجع أهداف فريقي في الفترة الحالية واشرح أين توجد فجوات في التحقيق اعتمادًا على البيانات المسموح لي بها فقط.", "Review my team's current goals and explain where achievement gaps exist using only data I am authorized to access."),
    },
    {
      key: "workforce",
      group: tx("الإدارة", "Management"),
      title: tx("كيف أراجع ضغط العمل والسعة؟", "How do I review workload and capacity?"),
      description: tx("استخدم السعة والطلب والاستخدام والتأخير لتحديد أين تحتاج الموازنة التشغيلية.", "Use capacity, demand, utilization, and overdue pressure to identify where operational balancing is needed."),
      keywords: tx(["سعة", "ضغط", "عمل", "قوى"], ["capacity", "workload", "workforce", "utilization"]),
      steps: [
        { text: tx("افتح أداء الفريق وانتقل إلى تخطيط القوى العاملة.", "Open Team Performance and go to Workforce Planning."), action: { page: "teamPerformance", anchor: "phase4-workforce", labelKey: "teamPerformance" } },
        { text: tx("راجع السعة والطلب المخطط ونسبة الاستخدام.", "Review capacity, planned demand, and utilization.") },
        { text: tx("قارن الضغط بالمهام المتأخرة ومؤشرات المخاطر.", "Compare workload pressure with overdue work and risk signals.") },
        { text: tx("استخدم النتيجة لإعادة توزيع العمل تشغيليًا، وليس كحكم موارد بشرية آلي.", "Use the result for operational workload balancing, not as an automated HR judgment.") },
      ],
      details: [
        tx("مستوى الثقة يوضح قوة البيانات المتاحة ولا يمثل تقييمًا شخصيًا للموظف.", "Confidence indicates the strength of available evidence; it is not a personal employee rating."),
        tx("مخاطر السعة إشارة تشغيلية وليست قرارًا وظيفيًا.", "Capacity risk is an operational signal, not an employment decision."),
      ],
      ramzyPrompt: tx("راجع ضغط العمل والسعة لفريقي واشرح لي الموظفين أو الأقسام التي تحتاج مراجعة تشغيلية اعتمادًا على بيانات تخطيط القوى العاملة المسموح لي بها فقط.", "Review my team's workload and capacity and explain which employees or departments need operational review using only Workforce data I am authorized to access."),
    },
    {
      key: "reviews",
      group: tx("التطوير", "Development"),
      title: tx("كيف أتابع المراجعات وخطط التحسين؟", "How do I follow reviews and coaching actions?"),
      description: tx("راجع المراجعة وخطة العمل والمتابعة بدل الاكتفاء بدرجة الأداء.", "Review the performance review, action plan, and follow-up instead of relying on the score alone."),
      keywords: tx(["مراجعة", "تحسين", "توجيه", "خطة"], ["review", "coaching", "improvement", "action plan"]),
      steps: [
        { text: tx("افتح قسم المراجعات والتوجيه.", "Open Reviews & Coaching."), action: { page: "teamPerformance", anchor: "phase4-reviews", labelKey: "teamPerformance" } },
        { text: tx("اختر الموظف ودورة المراجعة المطلوبة.", "Select the employee and review cycle.") },
        { text: tx("راجع الملاحظات والإجراءات وخطة التحسين.", "Review feedback, actions, and improvement plan.") },
        { text: tx("تابع حالة الإجراء وإقرار الموظف عندما يكون ذلك متاحًا.", "Follow action status and employee acknowledgment where applicable.") },
      ],
      details: [tx("المراجعة البشرية وخطة التحسين تظل قرارات بشرية؛ النظام يقدم الأدلة والسجل.", "Human review and improvement plans remain human decisions; the system provides evidence and history.")],
      ramzyPrompt: tx("لخص لي المراجعات وخطط التحسين المفتوحة لفريقي وما يحتاج متابعة اعتمادًا على البيانات المسموح لي بها.", "Summarize open reviews and improvement actions for my team and what needs follow-up using only data I am authorized to access."),
    },
    {
      key: "skills",
      group: tx("التطوير", "Development"),
      title: tx("كيف أعرف فجوات المهارات وخطة التطوير؟", "How do I review skill gaps and development plans?"),
      description: tx("قارن المستوى الحالي بالمستوى المطلوب ثم تابع خطة التطوير المرتبطة بالفجوة.", "Compare current and required skill levels, then follow the development plan tied to the gap."),
      keywords: tx(["مهارات", "فجوة", "تطوير", "مستوى"], ["skills", "gap", "development", "level"]),
      steps: [
        { text: tx("افتح قسم المهارات والتطوير.", "Open Skills & Development."), action: { page: "teamPerformance", anchor: "phase4-skills", labelKey: "teamPerformance" } },
        { text: tx("اختر الموظف أو الدور المطلوب.", "Select the employee or role.") },
        { text: tx("قارن المستوى الحالي بالمستوى المطلوب.", "Compare the current level with the required level.") },
        { text: tx("راجع خطة التطوير وحالتها وتاريخ المتابعة.", "Review the development plan, status, and follow-up history.") },
      ],
      details: [tx("فجوة المهارة تعكس الفرق المسجل بين المستوى الحالي والمطلوب، ولا تستبدل التقييم المهني البشري.", "A skill gap reflects the recorded difference between current and required levels; it does not replace professional human assessment.")],
      ramzyPrompt: tx("راجع فجوات المهارات وخطط التطوير في فريقي باستخدام البيانات المسموح لي بها وحدد الأولويات التي تحتاج متابعة.", "Review skill gaps and development plans in my team using authorized data and identify priorities that need follow-up."),
    },
    {
      key: "talent",
      group: tx("المواهب", "Talent"),
      title: tx("كيف أراجع المواهب وخطط التعاقب؟", "How do I review talent and succession planning?"),
      description: tx("استخدم بيانات الأداء مع تقييمات الإمكانات والجاهزية البشرية لبناء صورة متوازنة.", "Use performance evidence together with human-entered potential and readiness assessments."),
      keywords: tx(["مواهب", "تعاقب", "جاهزية", "إمكانات"], ["talent", "succession", "readiness", "potential"]),
      steps: [
        { text: tx("افتح قسم المواهب والتعاقب.", "Open Talent & Succession."), action: { page: "teamPerformance", anchor: "phase4-talent", labelKey: "teamPerformance" } },
        { text: tx("راجع بيانات الأداء وسجل التطوير.", "Review performance and development history.") },
        { text: tx("راجع تقييم الإمكانات والجاهزية المسجل بشريًا.", "Review human-entered potential and readiness assessments.") },
        { text: tx("استخدم الصورة كمدخل للنقاش الإداري، لا كقرار ترقية آلي.", "Use the view as management input, not an automated promotion decision.") },
      ],
      details: [tx("الإمكانات والجاهزية قيم بشرية الإدخال وليستا استنتاجًا آليًا من درجة الأداء.", "Potential and readiness are human-entered values and are not automatically inferred from Performance Score.")],
      ramzyPrompt: tx("لخص بيانات المواهب والتعاقب المتاحة لفريقي ووضح ما يحتاج نقاشًا إداريًا بدون إصدار قرارات ترقية أو تعاقب آلية.", "Summarize available talent and succession data for my team and highlight what needs management discussion without making automated promotion or succession decisions."),
    },
    {
      key: "recognition",
      group: tx("المواهب", "Talent"),
      title: tx("كيف أراجع التقدير والمكافآت؟", "How do I review recognition and rewards?"),
      description: tx("راجع الدورة والترشيحات والاعتمادات والنتائج المنشورة مع الحفاظ على الموافقات البشرية.", "Review cycles, nominations, approvals, and published recognition while preserving human approval."),
      keywords: tx(["تقدير", "مكافآت", "ترشيح", "جوائز"], ["recognition", "rewards", "nomination", "awards"]),
      steps: [
        { text: tx("افتح قسم التقدير والمكافآت.", "Open Recognition & Rewards."), action: { page: "teamPerformance", anchor: "phase4-recognition", labelKey: "teamPerformance" } },
        { text: tx("اختر الدورة المطلوبة وراجع الترشيحات.", "Select the relevant cycle and review nominations.") },
        { text: tx("راجع حالة الاعتماد قبل النشر.", "Review approval status before publishing.") },
        { text: tx("راجع التقديرات أو الجوائز المنشورة وسجلها.", "Review published recognition or awards and their history.") },
      ],
      details: [tx("التقدير والمكافآت لا تُمنح تلقائيًا من درجة الأداء؛ الموافقات البشرية تبقى مطلوبة.", "Recognition and rewards are not automatically granted from Performance Score; human approvals remain required.")],
      ramzyPrompt: tx("لخص دورات التقدير والمكافآت والترشيحات الحالية لفريقي وما يحتاج اعتمادًا أو متابعة دون اتخاذ قرار آلي.", "Summarize current recognition cycles and nominations for my team and what needs approval or follow-up without making automated decisions."),
    },
    {
      key: "executive",
      group: tx("الإدارة", "Management"),
      title: tx("كيف أعرف أين تحتاج الإدارة للتدخل؟", "How do I identify management priorities?"),
      description: tx("ابدأ بالمؤشرات التنفيذية ثم قائمة الأولويات وإشارات الأقسام للوصول إلى المشكلة الأساسية.", "Start with executive KPIs, then priority queue and department signals to reach the underlying issue."),
      keywords: tx(["إدارة", "تدخل", "أولوية", "تنفيذي"], ["management", "priority", "executive", "intervention"]),
      steps: [
        { text: tx("افتح مركز القيادة التنفيذي.", "Open the Executive Command Center."), action: { page: "teamPerformance", anchor: "team-performance-executive", labelKey: "executive" } },
        { text: tx("راجع المؤشرات التنفيذية والملخص التنفيذي.", "Review executive KPIs and the executive brief.") },
        { text: tx("راجع قائمة الأولويات وإشارات الأقسام.", "Review the priority queue and department signals.") },
        { text: tx("افتح التفاصيل التشغيلية قبل تحديد الإجراء الإداري.", "Open operational detail before deciding on a management action.") },
      ],
      details: [tx("لا يوجد قرار أو درجة تنفيذية جديدة يتم اختراعها داخل مركز المساعدة؛ يتم تفسير مؤشرات TOS الحالية فقط.", "Help Center does not invent a new executive score or decision; it explains existing TOS signals only.")],
      ramzyPrompt: tx("حدد لي أهم أولويات الإدارة في أداء الفريق حاليًا باستخدام المؤشرات التنفيذية والبيانات المسموح لي بها، واشرح سبب كل أولوية.", "Identify the most important management priorities in current team performance using authorized executive signals and explain why each one matters."),
    },
    {
      key: "export",
      group: tx("التقارير", "Reports"),
      title: tx("كيف أصدر تقرير الأداء؟", "How do I export a performance report?"),
      description: tx("اضبط الفترة والفلاتر أولًا ثم صدّر نفس مجموعة البيانات المسموح لك بها.", "Set the period and filters first, then export the same dataset you are authorized to view."),
      keywords: tx(["تصدير", "إكسل", "بي دي إف", "تقرير"], ["export", "excel", "pdf", "report"]),
      steps: [
        { text: tx("افتح أداء الفريق واختر الفترة.", "Open Team Performance and choose the period."), action: { page: "teamPerformance", anchor: "team-performance-kpis", labelKey: "teamPerformance" } },
        { text: tx("طبّق الفلاتر المطلوبة.", "Apply the required filters.") },
        { text: tx("اختر تصدير Excel أو PDF من أدوات التقرير.", "Choose Excel or PDF export from report actions.") },
        { text: tx("راجع الملف الناتج وتأكد أن النطاق يطابق ما يظهر لك.", "Review the resulting file and confirm its scope matches what you can see.") },
      ],
      details: [tx("التصدير يستخدم نفس نطاق صلاحيات أداء الفريق ولا يوسّع الرؤية.", "Export uses the same Team Performance permission scope and does not expand visibility.")],
      ramzyPrompt: tx("ساعدني في فهم التقرير الذي سأصدره من أداء الفريق ووضح أهم ما يجب مراجعته في الفترة والفلاتر الحالية.", "Help me understand the Team Performance report I am about to export and highlight what I should review for the current period and filters."),
    },
    {
      key: "archive",
      group: tx("التقارير", "Reports"),
      title: tx("كيف أراجع موظفًا معطلًا أو سابقًا؟", "How do I review archived performance?"),
      description: tx("استخدم الأرشيف للبيانات التاريخية بدون إدخال الحسابات المعطلة في مؤشرات الأداء الحية.", "Use archive for historical data without allowing disabled accounts to affect live performance KPIs."),
      keywords: tx(["أرشيف", "معطل", "سابق", "موظف"], ["archive", "disabled", "former", "employee"]),
      steps: [
        { text: tx("افتح قسم الأرشيف داخل أداء الفريق.", "Open the archive section inside Team Performance."), action: { page: "teamPerformance", anchor: "team-performance-archive", labelKey: "archive" } },
        { text: tx("ابحث عن الموظف المعطل المطلوب.", "Find the disabled employee you need.") },
        { text: tx("راجع السجل التاريخي المتاح دون خلطه بالمؤشرات الحية.", "Review available historical records without mixing them into live KPIs.") },
      ],
      details: [
        tx("النشط يظهر في التقرير الحي داخل نطاق الصلاحية.", "ACTIVE users appear in the live report inside the authorized scope."),
        tx("المعطل تاريخي فقط ولا يؤثر على مؤشرات التقرير الحي.", "DISABLED users are historical only and do not affect live KPIs."),
        tx("المعلّق لا يظهر في التقرير الحي ولا الأرشيف وفق القاعدة الحالية.", "PENDING users are excluded from both live performance and archive under the current rule."),
      ],
      ramzyPrompt: tx("اشرح لي الفرق بين الأداء الحي والأرشيف وكيف أراجع السجل التاريخي لموظف معطل دون خلطه بمؤشرات الفريق الحالية.", "Explain the difference between live performance and archive, and how to review historical data for a disabled employee without mixing it into current team KPIs."),
    },
    {
      key: "permissions",
      group: tx("الصلاحيات", "Permissions"),
      title: tx("من يمكنه رؤية أداء الموظفين؟", "Who can view employee performance?"),
      description: tx("الرؤية تعتمد على صلاحيات الأداء الحالية، والروابط داخل المساعدة لا تمنح أي صلاحية جديدة.", "Visibility depends on current performance permissions; Help Center links never grant additional access."),
      keywords: tx(["صلاحيات", "رؤية", "فريق", "موظفين"], ["permissions", "visibility", "team", "employees"]),
      steps: [
        { text: tx("راجع مستوى الوصول الفعلي للمستخدم: شخصي أو فريق أو الجميع.", "Review the user's effective visibility level: self, team, or all.") },
        { text: tx("للمستخدم المخول، افتح صفحة الصلاحيات لمراجعة الإعدادات.", "For an authorized user, open Permissions to review settings."), action: { page: "permissions", anchor: "", labelKey: "permissions" } },
        { text: tx("اختبر صفحة أداء الفريق بعد أي تعديل مصرح به.", "Verify Team Performance after any authorized permission change.") },
      ],
      details: [
        tx("مشاهدة أدائك الشخصي = performance.view_self.", "View own performance = performance.view_self."),
        tx("مشاهدة أداء الفريق = performance.view_team.", "View team performance = performance.view_team."),
        tx("مشاهدة أداء كل الموظفين = performance.view_all.", "View all employee performance = performance.view_all."),
        tx("النطاق الفعلي في الخادم هو المرجع؛ مركز المساعدة لا يبني صلاحيات موازية.", "Server-side effective scope remains authoritative; Help Center does not implement parallel permission rules."),
      ],
      ramzyPrompt: tx("اشرح لي نطاق رؤية أداء الفريق المتاح لحسابي وما الفرق بين الرؤية الشخصية ورؤية الفريق ورؤية جميع الموظفين بدون تغيير أي صلاحية.", "Explain the Team Performance visibility scope available to my account and the difference between self, team, and all-employee visibility without changing any permission."),
    },
  ], [isAr]);

  useEffect(() => {
    if (!open) return undefined;
    setSelectedKey(initialArticle || "overview");
    setDetailsOpen(false);
    const onKeyDown = (event) => {
      if (event.key === "Escape") onClose?.();
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [open, initialArticle, onClose]);

  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (!needle) return workflows;
    return workflows.filter((item) => {
      const haystack = [
        item.title,
        item.description,
        ...(item.keywords || []),
        ...(item.steps || []).map((step) => step.text),
      ].join(" ").toLowerCase();
      return haystack.includes(needle);
    });
  }, [query, workflows]);

  useEffect(() => {
    if (!filtered.some((item) => item.key === selectedKey)) {
      setSelectedKey(filtered[0]?.key || "overview");
      setDetailsOpen(false);
    }
  }, [filtered, selectedKey]);

  const selected = workflows.find((item) => item.key === selectedKey) || filtered[0] || workflows[0];

  const navigate = (action) => {
    if (!action || typeof window === "undefined") return;
    onClose?.();
    requestAnimationFrame(() => {
      window.dispatchEvent(new CustomEvent("tos:help-navigate", { detail: action }));
    });
  };

  const askRamzy = () => {
    if (!selected?.ramzyPrompt || typeof window === "undefined") return;
    window.dispatchEvent(new CustomEvent("tos:ramzy-help", {
      detail: {
        topicKey: selected.key,
        prompt: selected.ramzyPrompt,
        source: "help-center",
      },
    }));
    onClose?.();
  };

  if (!open) return null;

  const groups = [...new Set(filtered.map((item) => item.group))];

  return (
    <div className="fixed inset-0 z-[90] flex items-center justify-center bg-black/55 p-3 backdrop-blur-sm sm:p-5" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose?.(); }}>
      <section role="dialog" aria-modal="true" aria-labelledby="team-performance-help-title" className="flex max-h-[92vh] w-full max-w-6xl overflow-hidden rounded-3xl border border-zinc-200 bg-white shadow-2xl dark:border-white/10 dark:bg-zinc-950">
        <aside className="hidden w-80 shrink-0 border-r border-zinc-200 bg-zinc-50/80 p-4 dark:border-white/10 dark:bg-white/[0.025] md:block">
          <div className="relative">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400" />
            <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder={tx("بحث في مركز المساعدة", "Search Help Center")} aria-label={tx("بحث في مركز المساعدة", "Search Help Center")} className="w-full rounded-2xl border border-zinc-200 bg-white py-2.5 pl-9 pr-3 text-sm font-bold text-zinc-800 outline-none focus:ring-2 focus:ring-amber-400 dark:border-white/10 dark:bg-zinc-900 dark:text-white" />
          </div>
          <div className="mt-4 max-h-[72vh] space-y-4 overflow-y-auto pr-1">
            {groups.map((group) => (
              <div key={group}>
                <p className="mb-2 px-2 text-[10px] font-black uppercase tracking-[0.12em] text-zinc-400">{group}</p>
                <div className="space-y-1">
                  {filtered.filter((item) => item.group === group).map((item) => (
                    <button key={item.key} type="button" onClick={() => { setSelectedKey(item.key); setDetailsOpen(false); }} className={`w-full rounded-xl px-3 py-2 text-start text-sm font-bold transition ${selected?.key === item.key ? "bg-amber-100 text-amber-950 dark:bg-amber-400/15 dark:text-amber-200" : "text-zinc-600 hover:bg-white dark:text-zinc-300 dark:hover:bg-white/[0.05]"}`}>
                      {item.title}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </aside>

        <main className="min-w-0 flex-1 overflow-y-auto">
          <div className="sticky top-0 z-10 flex items-start justify-between gap-4 border-b border-zinc-200 bg-white/95 p-4 backdrop-blur dark:border-white/10 dark:bg-zinc-950/95 sm:p-5">
            <div>
              <div className="flex items-center gap-2 text-amber-600 dark:text-amber-300"><BookOpen size={18} /><span className="text-xs font-black">{tx("مركز المساعدة", "Help Center")}</span></div>
              <h2 id="team-performance-help-title" className="mt-1 text-xl font-black text-zinc-950 dark:text-white">{tx("دليل أداء الفريق", "Team Performance Guide")}</h2>
            </div>
            <button type="button" onClick={onClose} aria-label={tx("إغلاق مركز المساعدة", "Close Help Center")} className="grid h-10 w-10 place-items-center rounded-xl border border-zinc-200 text-zinc-500 transition hover:bg-zinc-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-400 dark:border-white/10 dark:text-zinc-300 dark:hover:bg-white/[0.06]"><X size={18} /></button>
          </div>

          <div className="border-b border-zinc-200 p-4 dark:border-white/10 md:hidden">
            <div className="relative">
              <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400" />
              <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder={tx("بحث في مركز المساعدة", "Search Help Center")} className="w-full rounded-2xl border border-zinc-200 bg-white py-2.5 pl-9 pr-3 text-sm font-bold dark:border-white/10 dark:bg-zinc-900 dark:text-white" />
            </div>
            <select value={selected?.key || ""} onChange={(e) => { setSelectedKey(e.target.value); setDetailsOpen(false); }} className="mt-2 w-full rounded-2xl border border-zinc-200 bg-white p-2.5 text-sm font-bold dark:border-white/10 dark:bg-zinc-900 dark:text-white">
              {filtered.map((item) => <option key={item.key} value={item.key}>{item.title}</option>)}
            </select>
          </div>

          {selected ? (
            <article className="p-4 sm:p-6">
              <p className="text-xs font-black text-amber-600 dark:text-amber-300">{selected.group}</p>
              <h3 className="mt-1 text-2xl font-black tracking-tight text-zinc-950 dark:text-white">{selected.title}</h3>
              <p className="mt-2 max-w-3xl text-sm font-semibold leading-7 text-zinc-500 dark:text-zinc-400">{selected.description}</p>

              <div className="mt-6 space-y-3">
                {selected.steps.map((step, index) => (
                  <div key={`${selected.key}-${index}`} className="rounded-2xl border border-zinc-200 p-4 dark:border-white/10">
                    <div className="flex items-start gap-3">
                      <span className="grid h-7 w-7 shrink-0 place-items-center rounded-full bg-amber-100 text-xs font-black text-amber-800 dark:bg-amber-400/15 dark:text-amber-200">{index + 1}</span>
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-bold leading-6 text-zinc-800 dark:text-zinc-100">{step.text}</p>
                        {step.action ? (
                          <button type="button" onClick={() => navigate(step.action)} className="mt-2 inline-flex items-center gap-1.5 rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-xs font-black text-amber-800 transition hover:bg-amber-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-400 dark:border-amber-400/20 dark:bg-amber-400/[0.08] dark:text-amber-200">
                            <ExternalLink size={14} />{actionLabel(isAr, step.action)}
                          </button>
                        ) : null}
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              <button type="button" aria-expanded={detailsOpen} onClick={() => setDetailsOpen((value) => !value)} className="mt-5 flex w-full items-center justify-between rounded-2xl border border-zinc-200 bg-zinc-50 px-4 py-3 text-start text-sm font-black text-zinc-800 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-400 dark:border-white/10 dark:bg-white/[0.035] dark:text-zinc-100">
                <span>{tx("لمزيد من التفاصيل", "More details")}</span>
                <ChevronDown size={18} className={`transition ${detailsOpen ? "rotate-180" : ""}`} />
              </button>

              {detailsOpen ? (
                <div className="mt-3 rounded-2xl border border-zinc-200 p-4 dark:border-white/10">
                  <ul className="space-y-2">
                    {(selected.details || []).map((detail, index) => (
                      <li key={`${selected.key}-detail-${index}`} className="flex gap-2 text-sm font-semibold leading-6 text-zinc-600 dark:text-zinc-300">
                        <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-amber-500" />
                        <span>{detail}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}

              {selected.ramzyPrompt ? (
                <button type="button" onClick={askRamzy} className="mt-5 inline-flex items-center gap-2 rounded-2xl bg-zinc-950 px-4 py-3 text-sm font-black text-white transition hover:bg-zinc-800 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-400 dark:bg-amber-400 dark:text-zinc-950 dark:hover:bg-amber-300">
                  <Sparkles size={17} />{tx("اسأل رمزي عن هذا الموضوع", "Ask Ramzy about this topic")}
                </button>
              ) : null}
            </article>
          ) : (
            <div className="p-8 text-center text-sm font-bold text-zinc-500">{tx("لا توجد نتائج مطابقة.", "No matching help topics.")}</div>
          )}
        </main>
      </section>
    </div>
  );
}
"""

def main():
    if not TARGET.exists():
        raise SystemExit(f"PHASE6_5_ERROR=TARGET_NOT_FOUND:{TARGET}")
    before = TARGET.read_text(encoding="utf-8")
    if 'key: "overview"' not in before or "TeamPerformanceHelpCenter" not in before:
        raise SystemExit("PHASE6_5_ERROR=UNEXPECTED_HELP_CENTER_BASE")
    TARGET.write_text(CONTENT, encoding="utf-8")
    after = TARGET.read_text(encoding="utf-8")
    required = [
        'key: "performance-decline"',
        'key: "permissions"',
        "ramzyPrompt",
        "tos:help-navigate",
        "tos:ramzy-help",
        "اسأل رمزي عن هذا الموضوع",
        "Ask Ramzy about this topic",
        "لمزيد من التفاصيل",
        "More details",
    ]
    missing = [marker for marker in required if marker not in after]
    if missing:
        raise SystemExit("PHASE6_5_ERROR=MISSING_MARKERS:" + ",".join(missing))
    count = after.count("      key: ")
    if count < 14:
        raise SystemExit(f"PHASE6_5_ERROR=WORKFLOW_COUNT:{count}")
    print("PHASE6_5_HELP_CENTER_WRITE=PASS")
    print(f"WORKFLOW_COUNT={count}")
    print("ASK_RAMZY_BRIDGE=tos:ramzy-help")
    print("NAV_BRIDGE=tos:help-navigate")

if __name__ == "__main__":
    main()
