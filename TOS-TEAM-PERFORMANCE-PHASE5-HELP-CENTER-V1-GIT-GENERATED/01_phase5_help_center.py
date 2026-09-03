#!/usr/bin/env python3
from pathlib import Path

ROOT = Path('/var/www/TOS')
DASHBOARD = ROOT / 'frontend/src/pages/TeamPerformanceDashboard.jsx'
HELP = ROOT / 'frontend/src/components/performance/TeamPerformanceHelpCenter.jsx'

if not DASHBOARD.exists():
    raise SystemExit('PHASE5_HELP_CENTER_ERROR=DASHBOARD_NOT_FOUND')
if HELP.exists():
    raise SystemExit('PHASE5_HELP_CENTER_ERROR=HELP_COMPONENT_ALREADY_EXISTS')

help_component = r'''import { useEffect, useMemo, useState } from "react";
import { BookOpen, Calculator, Database, Lightbulb, Search, ShieldCheck, X } from "lucide-react";

function HelpBlock({ icon: Icon, label, children, tone = "zinc" }) {
  const shell = {
    zinc: "border-zinc-200 bg-zinc-50/80 dark:border-white/10 dark:bg-white/[0.035]",
    blue: "border-blue-200 bg-blue-50/70 dark:border-blue-400/15 dark:bg-blue-400/[0.06]",
    amber: "border-amber-200 bg-amber-50/70 dark:border-amber-400/15 dark:bg-amber-400/[0.06]",
    emerald: "border-emerald-200 bg-emerald-50/70 dark:border-emerald-400/15 dark:bg-emerald-400/[0.06]",
  }[tone];
  return (
    <div className={`rounded-2xl border p-4 ${shell}`}>
      <div className="flex items-center gap-2">
        <Icon size={16} className="text-zinc-500 dark:text-zinc-300" />
        <p className="text-[10px] font-black uppercase tracking-[0.1em] text-zinc-500 dark:text-zinc-300">{label}</p>
      </div>
      <div className="mt-2 text-xs font-bold leading-6 text-zinc-700 dark:text-zinc-200">{children}</div>
    </div>
  );
}

export function TeamPerformanceHelpCenter({ open, onClose, lang = "en", initialArticle = "overview" }) {
  const isAr = String(lang || "").toLowerCase().startsWith("ar");
  const tx = (ar, en) => (isAr ? ar : en);
  const [query, setQuery] = useState("");
  const [selectedKey, setSelectedKey] = useState(initialArticle || "overview");

  const articles = useMemo(() => [
    {
      key: "overview", group: tx("الأساسيات", "Basics"),
      title: tx("كيف تعمل صفحة أداء الفريق؟", "How Team Performance works"),
      subtitle: tx("النطاق الحي، الفلاتر، ومن يدخل في الحسابات.", "Live scope, filters, and who is included."),
      meaning: tx("هذه الصفحة هي شاشة الإدارة اليومية لأداء الفريق. تعرض فقط المستخدمين ACTIVE داخل الصلاحيات الحالية والفترة والفلاتر المختارة.", "This page is the daily management view of team performance. It uses ACTIVE users only, inside the current permission scope, reporting period and filters."),
      calculation: tx("الفترة، الموظف، القسم، الحالة والبحث تضيق نفس مجموعة البيانات. المستخدم DISABLED لا يدخل أي KPI أو Ranking أو Compare أو management signal. المستخدم PENDING لا يظهر في التقرير الحي ولا الأرشيف.", "Reporting period, employee, department, status and search narrow the same dataset. DISABLED users do not affect KPIs, ranking, comparison or management signals. PENDING users are excluded from both live performance and the archive."),
      source: tx("TOS Team Performance report + دليل المستخدمين الحي. الحالة تأتي من User.status.", "TOS Team Performance report plus the live user directory. Account inclusion is driven by User.status."),
      use: tx("ابدأ بالفترة والقسم، ثم اقرأ KPIs وManagement Summary. افتح Drill-down أو Employee Drawer عندما تحتاج السبب والتفاصيل.", "Start with the reporting period and department, then read the KPIs and Management Summary. Use Drill-down or the Employee Drawer when you need the underlying detail."),
    },
    {
      key: "period-compare", group: tx("الأساسيات", "Basics"),
      title: tx("الفترة والمقارنة", "Reporting period & comparison"),
      subtitle: tx("كيف تعمل From / To وPrevious period.", "How From / To and comparison ranges work."),
      meaning: tx("الفترة الحالية تحدد العمل الذي يتم قياسه. المقارنة تضيف فترة مرجعية مستقلة ولا تغير الفترة الحالية.", "The current period defines the work being measured. Comparison adds a separate reference period without changing the current period."),
      calculation: tx("Today / Yesterday / Week / Month / Quarter / Year تحسب نطاقها تلقائيًا. Custom يستخدم From وTo. Previous period يستخدم فترة مساوية مباشرة قبل الحالية، مع خيارات Previous month وPrevious year وCustom وOff.", "Today / Yesterday / Week / Month / Quarter / Year calculate their ranges automatically. Custom uses From and To. Previous period uses an equal-length period immediately before the current range, with Previous month, Previous year, Custom and Off also available."),
      source: tx("نطاق التاريخ في TeamPerformanceDashboard ثم نفس Team Performance API للفترة الحالية وفترة المقارنة.", "Date-range logic in TeamPerformanceDashboard, then the same Team Performance API for the current and comparison ranges."),
      use: tx("استخدم Previous period لفهم هل الأداء تحسن فعلاً مقارنة بفترة مساوية، واستخدم Previous year للموسمية.", "Use Previous period to see whether performance improved against an equal-length baseline, and Previous year when seasonality matters."),
    },
    {
      key: "average-score", group: tx("المؤشرات", "KPIs"),
      title: tx("Average Score", "Average Score"),
      subtitle: tx("متوسط درجة الأداء للموظفين الذين لديهم Score.", "Mean performance score for employees who have a score."),
      meaning: tx("يعطي مستوى أداء الفريق المقاس في النطاق الحالي.", "Shows the measured performance level of the current team scope."),
      calculation: tx("مجموع Performance Score للموظفين الذين لديهم Score ÷ عددهم. No Activity لا يدخل المتوسط. الفلاتر الحالية تطبق قبل المتوسط الظاهر على الشاشة.", "Sum of Performance Score for employees with a score divided by their count. No Activity rows are excluded. Current page filters are applied before the displayed average is calculated."),
      source: tx("performanceScore من Team Performance report، ثم filtered employee scope في الواجهة.", "performanceScore from the Team Performance report, then the filtered employee scope in the UI."),
      use: tx("راقب الاتجاه مع Compare، لكن لا تستخدم المتوسط وحده للحكم على أفراد الفريق؛ افتح توزيع الحالات والموظفين.", "Track its direction with Compare, but do not use the average alone to judge individuals; inspect statuses and employee detail."),
    },
    {
      key: "top-performer", group: tx("المؤشرات", "KPIs"),
      title: tx("Top Performer", "Top Performer"),
      subtitle: tx("أعلى موظف حاصل على Performance Score في النطاق الحالي.", "Highest-scoring employee in the current scope."),
      meaning: tx("يعرض صاحب أعلى Score بين الموظفين المقاسين حاليًا.", "Shows the employee with the highest Performance Score among currently measured employees."),
      calculation: tx("الصفوف التي لها Score ترتب تنازليًا؛ أول صف هو Top Performer. No Activity ليس له Rank. عند تشغيل Compare، الدلتا تقارن نفس الموظف بالفترة المقارنة.", "Scored rows are sorted descending; the first scored row is the Top Performer. No Activity has no rank. With Compare enabled, the delta compares that same employee against the comparison period."),
      source: tx("Team Performance ranking + نفس employee ID في بيانات المقارنة.", "Team Performance ranking plus the same employee ID in comparison-period data."),
      use: tx("استخدمه كنقطة دخول لمعرفة ما الذي يعمل جيدًا، ثم افتح Employee Drawer لمراجعة Score breakdown والمهام.", "Use it as a starting point for what is working well, then open the Employee Drawer to inspect score breakdown and tasks."),
    },
    {
      key: "completed-tasks", group: tx("المؤشرات", "KPIs"),
      title: tx("Completed Tasks", "Completed Tasks"),
      subtitle: tx("المهام المكتملة من إجمالي المهام في النطاق.", "Completed work out of total tasks in scope."),
      meaning: tx("يعرض حجم التسليم ونسبة الإكمال للفترة المختارة.", "Shows delivery volume and completion rate for the selected period."),
      calculation: tx("Completed = مجموع completedTasks. Total = مجموع totalTasks. Completion rate = Completed ÷ Total × 100 عندما يكون Total أكبر من صفر.", "Completed is the sum of completedTasks. Total is the sum of totalTasks. Completion rate is Completed divided by Total times 100 when Total is greater than zero."),
      source: tx("حالة المهام في Team Performance report داخل الفترة والنطاق الحاليين.", "Task status data in the Team Performance report for the current period and scope."),
      use: tx("قارنه بالـOverdue وبالجودة/Score. ارتفاع الإكمال وحده لا يعني أن التنفيذ كان في الموعد أو بكفاءة.", "Read it together with Overdue and the score. High completion alone does not prove work was on time or efficient."),
    },
    {
      key: "overdue-tasks", group: tx("المؤشرات", "KPIs"),
      title: tx("Overdue Tasks", "Overdue Tasks"),
      subtitle: tx("عدد المهام المتأخرة في النطاق الحالي.", "Count of overdue tasks in the current scope."),
      meaning: tx("يقيس ضغط التأخير الحالي على الفريق.", "Measures current delivery-delay pressure on the team."),
      calculation: tx("يجمع overdueTasks للموظفين الظاهرين في النطاق الحالي. في مكوّن On-time من Performance Score، العمل المتأخر يطبق penalty مقداره 5 نقاط لكل overdue حتى حد أقصى 25 نقطة.", "Sums overdueTasks for employees in the current scope. Inside the On-time score component, overdue work applies a 5-point penalty per overdue task, capped at 25 points."),
      source: tx("Task due dates / completion state داخل Team Performance report.", "Task due dates and completion state inside the Team Performance report."),
      use: tx("ابدأ بالموظفين ذوي أعلى Overdue Pressure ثم افتح المهام نفسها من Drill-down لتحديد العائق الحقيقي.", "Start with employees carrying the highest overdue pressure, then open the actual tasks from Drill-down to identify the operational blocker."),
    },
    {
      key: "logged-hours", group: tx("المؤشرات", "KPIs"),
      title: tx("Logged Hours", "Logged Hours"),
      subtitle: tx("إجمالي actualHours المسجلة على المهام.", "Total actualHours recorded on tasks."),
      meaning: tx("يعرض الوقت الفعلي المسجل على العمل في النطاق الحالي.", "Shows actual time recorded on work in the current scope."),
      calculation: tx("مجموع actualHours للموظفين والمهام داخل النطاق، ويعرض برقم عشري مناسب.", "Sum of actualHours across employees and tasks in scope, displayed in a compact hour format."),
      source: tx("Task.actualHours في TOS.", "Task.actualHours in TOS."),
      use: tx("قارنه بالتسليم والـEfficiency. ساعات كثيرة مع إنجاز ضعيف قد تستحق مراجعة تقدير الوقت أو توزيع العمل.", "Read it beside delivery and Efficiency. High hours with weak output can justify checking estimates or workload allocation."),
    },
    {
      key: "performance-score", group: tx("الدرجة", "Score"),
      title: tx("Performance Score", "Performance Score"),
      subtitle: tx("درجة 0–100 مبنية على خمسة مكونات فعلية.", "A 0–100 score built from five measurable components."),
      meaning: tx("الـScore يلخص التسليم، الالتزام بالموعد، كفاءة الوقت، جودة سير العمل والاستمرارية. هو مؤشر إداري وليس قرار HR آلي.", "The score summarizes delivery, timeliness, time efficiency, workflow quality and consistency. It is a management indicator, not an automated HR decision."),
      calculation: tx("الأوزان: Completion 35%، On-time/Overdue 25%، Time Efficiency 20%، Workflow Quality 10%، Consistency 10%. إذا لم توجد بيانات مؤهلة لمكوّن، يتم Skipped ويعاد تطبيع الأوزان المتاحة إلى 100 بدلاً من معاقبة الموظف على بيانات ناقصة.", "Weights: Completion 35%, On-time/Overdue 25%, Time Efficiency 20%, Workflow Quality 10%, Consistency 10%. If a component has no eligible data it is skipped and available weights are normalized back to 100, rather than penalizing the employee for missing data."),
      source: tx("Task status، dueDate، completedAt، estimated/actual hours، وTaskActivity workflow/status signals.", "Task status, dueDate, completedAt, estimated/actual hours, plus TaskActivity workflow and status signals."),
      use: tx("افتح Score breakdown لمعرفة أي مكوّن خفض النتيجة. لا تتعامل مع رقم واحد بدون قراءة Confidence والمهام والـtrend.", "Open Score breakdown to see which component drives the result. Do not use one number without reading Confidence, tasks and trend."),
      details: [
        tx("Completion: نسبة completed ÷ total.", "Completion: completed divided by total."),
        tx("On-time: للمهام المكتملة التي لديها dueDate وcompletedAt، ثم penalty للتأخير الحالي حتى 25 نقطة.", "On-time: uses completed tasks that have both dueDate and completedAt, then applies current overdue penalty up to 25 points."),
        tx("Efficiency: تستخدم المهام التي لديها estimatedHours وactualHours؛ التنفيذ عند التقدير يساوي 100، والزيادة في الوقت تخفض النتيجة مع clamp من 0 إلى 100.", "Efficiency: uses tasks with estimatedHours and actualHours; finishing at estimate scores 100, while overruns reduce the score, clamped to 0–100."),
        tx("Workflow: يقارن clean workflows مع revision loops من إشارات تغيير الحالة.", "Workflow: compares clean workflows against revision loops from status-change signals."),
        tx("Consistency: 60% تغطية unique active tasks + 40% تغطية status changes المعتدلة.", "Consistency: 60% unique active-task coverage plus 40% moderate status-change coverage."),
        tx("Confidence: High عند 4–5 مكونات متاحة، Medium عند 3، Low عند 0–2.", "Confidence: High with 4–5 available components, Medium with 3, Low with 0–2."),
        tx("Status: 85+ Excellent، 70–84 On Track، 50–69 Needs Attention، أقل من 50 At Risk. عدم وجود نشاط meaningful = No Activity بدون Score/Rank.", "Status: 85+ Excellent, 70–84 On Track, 50–69 Needs Attention, below 50 At Risk. No meaningful activity means No Activity with no score or rank."),
      ],
    },
    {
      key: "management-summary", group: tx("الإدارة", "Management"),
      title: tx("Management Summary", "Management Summary"),
      subtitle: tx("ملخص سريع لما يحتاج انتباه الإدارة الآن.", "Fast summary of what needs management attention now."),
      meaning: tx("يجمع Doing well، Needs attention، Overdue pressure وFocus now من نفس الموظفين الظاهرين بعد الفلاتر.", "Groups Doing well, Needs attention, Overdue pressure and Focus now from the same employees visible after filters."),
      calculation: tx("Rule-based فقط: أعلى الأداء، At Risk/Needs Attention، أعلى overdue، وإشارات محددة مثل at-risk / overdue / no activity / behind target. لا يوجد Management Score جديد ولا AI recommendation.", "Rule-based only: strongest performers, At Risk/Needs Attention, highest overdue pressure and deterministic signals such as at-risk, overdue, no activity and behind-target counts. It creates no new Management Score and no AI recommendation."),
      source: tx("filteredEmployees + target summary الموجودة بالفعل في Team Performance.", "Existing filteredEmployees plus the target summary already loaded by Team Performance."),
      use: tx("استخدمه لترتيب أول 3 نقاط تبدأ بها يومك، ثم افتح الموظف أو المهمة للتحقق من السبب.", "Use it to choose the first few items to inspect today, then open the employee or task to verify the reason."),
    },
    {
      key: "drilldown", group: tx("الإدارة", "Management"),
      title: tx("Drill-down & Navigation", "Drill-down & Navigation"),
      subtitle: tx("Company → Department → Employee → Task بدون شاشة تقارير ثانية.", "Company → Department → Employee → Task without another reporting screen."),
      meaning: tx("يسمح بالنزول من نظرة الشركة إلى القسم ثم الموظف والمهام داخل نفس النطاق المفلتر.", "Lets you move from company view to department, employee and tasks inside the same filtered scope."),
      calculation: tx("Department metrics تجمع موظفي filteredEmployees فقط. مهام الموظف تحمل من نفس userDashboard source المستخدم في Employee Drawer وللفترة الحالية.", "Department metrics aggregate filteredEmployees only. Employee tasks load from the same userDashboard source already used by the Employee Drawer and use the current reporting period."),
      source: tx("filteredEmployees + api.tasks.userDashboard + onOpenTask الموجود بالفعل في TOS.", "filteredEmployees plus api.tasks.userDashboard and the existing TOS onOpenTask navigation."),
      use: tx("ابدأ بالقسم صاحب Attention/Overdue الأعلى، افتح موظفًا، ثم Open task للوصول للمهمة الأصلية مباشرة.", "Start with the department carrying the most attention/overdue pressure, choose an employee, then Open task to reach the original task directly."),
    },
    {
      key: "executive", group: tx("الإدارة", "Management"),
      title: tx("Executive Command Center", "Executive Command Center"),
      subtitle: tx("صورة إدارية Admin-only من إشارات موجودة بالفعل.", "Admin-only management view built from existing signals."),
      meaning: tx("يجمع الأداء، targets، coaching/reviews، capacity، skills، talent/succession وrecognition في Snapshot تنفيذي.", "Aggregates performance, targets, coaching/reviews, capacity, skills, talent/succession and recognition into an executive snapshot."),
      calculation: tx("هو aggregation وترتيب severity لإشارات موجودة؛ لا ينشئ employee score جديد ولا قرار HR آلي.", "It aggregates and severity-orders existing signals; it does not create a new employee score or an automated HR decision."),
      source: tx("Executive workforce endpoint المبني على وحدات الأداء والقوى العاملة والمهارات والمواهب والمراجعات والتقدير.", "Executive workforce endpoint built from the existing performance, workforce, skills, talent, review and recognition modules."),
      use: tx("استخدم Snapshot لأولويات الإدارة، وافتح View executive details فقط عندما تحتاج Decision Domains وDepartment Health.", "Use Snapshot for management priorities; open View executive details only when you need Decision Domains and Department Health."),
    },
    {
      key: "targets", group: tx("الوحدات المتقدمة", "Advanced"),
      title: tx("Goals & Targets", "Goals & Targets"),
      subtitle: tx("Actual vs Target منفصل عن Performance Score.", "Actual vs Target, separate from Performance Score."),
      meaning: tx("يقيس هل الموظف أو القسم يحقق KPI targets المعرفة له خلال الفترة.", "Measures whether an employee or department is meeting configured KPI targets in the period."),
      calculation: tx("Achievement هو متوسط نسب تحقيق المقاييس المعرفة فقط: Score، Completion، Completed Tasks، Logged Hours، وMax Overdue. 110%+ = Exceeded، 90%+ = On Target، أقل من 90% = Behind Target، وأقل من 75% يعد at-risk داخل target logic. Employee target يتقدم على Department target.", "Achievement is the average of configured measurable target metrics only: Score, Completion, Completed Tasks, Logged Hours and Max Overdue. 110%+ = Exceeded, 90%+ = On Target, below 90% = Behind Target, and below 75% is at-risk inside target logic. Employee target overrides Department target."),
      source: tx("Performance targets + نفس Team Performance metrics الحالية.", "Performance targets plus the same current Team Performance metrics."),
      use: tx("استخدمه لقياس الاتفاق على هدف واضح، وليس لاستبدال Performance Score أو تفسير كل سبب وراء الأداء.", "Use it to check performance against an agreed target; it does not replace Performance Score or explain every cause behind the result."),
    },
    {
      key: "intelligence", group: tx("الوحدات المتقدمة", "Advanced"),
      title: tx("Performance Intelligence", "Performance Intelligence"),
      subtitle: tx("تنبيهات وtrend rules من بيانات الأداء الحالية.", "Rule-based alerts and trend signals from performance data."),
      meaning: tx("يلخص التحسن/الهبوط والتنبيهات والقسم الذي يحتاج انتباه بدون إنشاء Score آخر.", "Summarizes improvement, decline, alerts and department attention signals without creating another score."),
      calculation: tx("قواعد deterministic تستخدم Performance Score/history والمهام والإشارات الحالية. Critical/Warning تحددها قواعد الوحدة، وليست حكمًا من نموذج AI.", "Deterministic rules use Performance Score/history, tasks and current signals. Critical/Warning classifications come from module rules, not an AI judgement."),
      source: tx("Team Performance Intelligence endpoint + تاريخ الأداء الموجود.", "Team Performance Intelligence endpoint plus existing performance history."),
      use: tx("افتحه عندما تحتاج تفسير trend أو قائمة alerts، ثم راجع الموظف والمهمة قبل اتخاذ إجراء.", "Open it when you need trend context or the alert list, then inspect the employee and task before acting."),
    },
    {
      key: "team-table", group: tx("المرجع", "Reference"),
      title: tx("Team Performance table", "Team Performance table"),
      subtitle: tx("الترتيب والتفاصيل لكل موظف حي.", "Ranking and detail for each live employee."),
      meaning: tx("يعرض Rank، employee، department، Score، target، completed، completion، hours، overdue، compare وstatus.", "Shows Rank, employee, department, Score, target, completed work, completion, hours, overdue, comparison and status."),
      calculation: tx("Rank يعطى للموظفين الذين لديهم Score فقط، بترتيب Score تنازليًا. No Activity يبقى rank = null. الجدول يتبع نفس الفلاتر الحالية.", "Rank is assigned only to employees with a score, sorted by score descending. No Activity keeps rank = null. The table follows the same current filters."),
      source: tx("byUser ACTIVE من Team Performance report + target/comparison data المحملة لنفس النطاق.", "ACTIVE byUser rows from the Team Performance report plus target/comparison data loaded for the same scope."),
      use: tx("اضغط الموظف لفتح Employee Drawer ومراجعة Score breakdown والمهام والactivity/history.", "Open an employee to inspect Score breakdown, tasks, activity and history in the Employee Drawer."),
    },
    {
      key: "archive", group: tx("المرجع", "Reference"),
      title: tx("Archived Members", "Archived Members"),
      subtitle: tx("تاريخ DISABLED محفوظ لكنه خارج الأداء الحي.", "DISABLED history is preserved but excluded from live performance."),
      meaning: tx("يحفظ نتائج الموظفين المعطلين للفترة التاريخية بدون إظهارهم كأعضاء عاملين.", "Preserves historical results for disabled employees without treating them as live team members."),
      calculation: tx("DISABLED يذهب إلى archivedByUser، rank = null، ولا يدخل live KPIs/ranking/comparison/management signals أو الوحدات المتقدمة الحية. PENDING لا يذهب إلى live أو archive.", "DISABLED rows go to archivedByUser with rank = null and are excluded from live KPIs, ranking, comparison, management signals and live advanced modules. PENDING appears in neither live performance nor the archive."),
      source: tx("User.status + archivedByUser من Team Performance report.", "User.status plus archivedByUser from the Team Performance report."),
      use: tx("افتح القسم فقط عند مراجعة تاريخ موظف سابق/معطل. لا تستخدمه لقراءة حالة الفريق الحالية.", "Open it only when reviewing historical performance for a disabled member. Do not use it to interpret the current active team."),
    },
    {
      key: "deep-dive", group: tx("الوحدات المتقدمة", "Advanced"),
      title: tx("Deep Dive modules", "Deep Dive modules"),
      subtitle: tx("Reviews، Workforce، Skills، Talent، Recognition.", "Reviews, Workforce, Skills, Talent and Recognition."),
      meaning: tx("هذه الوحدات تضيف سياقًا أعمق بعد القراءة اليومية: coaching/reviews، workload/capacity، skills development، talent/succession، recognition/rewards.", "These modules add deeper context after the daily view: coaching/reviews, workload/capacity, skills development, talent/succession and recognition/rewards."),
      calculation: tx("كل وحدة تستخدم قواعدها وبياناتها الموجودة. لا تعتبر أي واحدة منها بديلًا عن Performance Score ولا يوجد hidden composite score يجمعها كلها.", "Each module uses its own existing rules and data. None replaces Performance Score and there is no hidden composite score combining them all."),
      source: tx("وحدات Performance Reviews، Workforce Planning، Skills Development، Talent Succession، Recognition Rewards في TOS.", "The existing Performance Reviews, Workforce Planning, Skills Development, Talent Succession and Recognition Rewards modules in TOS."),
      use: tx("افتح Deep Dive فقط عندما تحتاج تحليل أعمق أو إجراء متابعة، وليس كجزء إلزامي من قراءة الصفحة اليومية.", "Open Deep Dive only when you need deeper analysis or follow-up action; it is not required for the normal daily scan."),
    },
  ], [isAr]);

  useEffect(() => {
    if (!open) return undefined;
    setSelectedKey(initialArticle || "overview");
    const onKeyDown = (event) => {
      if (event.key === "Escape") onClose?.();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [open, initialArticle, onClose]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return articles;
    return articles.filter((article) => [article.title, article.subtitle, article.group, article.meaning, article.calculation, article.source, article.use]
      .some((value) => String(value || "").toLowerCase().includes(q)));
  }, [articles, query]);

  const selected = articles.find((article) => article.key === selectedKey) || articles[0];

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[90] flex justify-end" role="dialog" aria-modal="true" aria-label={tx("مركز مساعدة أداء الفريق", "Team Performance Help Center")}>
      <button type="button" className="absolute inset-0 bg-black/55" onClick={onClose} aria-label={tx("إغلاق مركز المساعدة", "Close Help Center")} />
      <section className="relative flex h-full w-full max-w-5xl flex-col bg-white shadow-2xl dark:bg-zinc-950">
        <header className="flex flex-col gap-3 border-b border-zinc-200 p-4 dark:border-white/10 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-[10px] font-black uppercase tracking-[0.12em] text-amber-500">TEAM PERFORMANCE HELP CENTER</p>
            <h2 className="mt-1 text-xl font-black text-zinc-950 dark:text-white">{tx("افهم الرقم قبل القرار", "Understand the number before the decision")}</h2>
            <p className="mt-1 text-xs font-bold text-zinc-400">{tx("المعنى · طريقة الحساب · المصدر · كيف تستخدمه", "Meaning · Calculation · Source · How to use it")}</p>
          </div>
          <button type="button" onClick={onClose} className="grid h-10 w-10 shrink-0 place-items-center rounded-xl border border-zinc-200 text-zinc-500 hover:border-amber-300 dark:border-white/10 dark:text-zinc-300" aria-label={tx("إغلاق", "Close")}><X size={19} /></button>
        </header>

        <div className="grid min-h-0 flex-1 lg:grid-cols-[300px_minmax(0,1fr)]">
          <aside className="min-h-0 border-b border-zinc-200 p-3 dark:border-white/10 lg:border-b-0 lg:border-r">
            <label className="flex min-h-10 items-center gap-2 rounded-xl border border-zinc-200 bg-white px-3 dark:border-white/10 dark:bg-zinc-900">
              <Search size={15} className="text-zinc-400" />
              <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder={tx("ابحث في المساعدة...", "Search help...")} className="w-full bg-transparent text-xs font-bold text-zinc-800 outline-none placeholder:text-zinc-400 dark:text-white" />
            </label>
            <div className="mt-3 max-h-[calc(100vh-160px)] space-y-1 overflow-y-auto pr-1">
              {filtered.map((article) => (
                <button key={article.key} type="button" onClick={() => setSelectedKey(article.key)} className={`w-full rounded-xl border px-3 py-2.5 text-left transition ${selectedKey === article.key ? "border-amber-300 bg-amber-50 dark:border-amber-400/25 dark:bg-amber-400/10" : "border-transparent hover:border-zinc-200 hover:bg-zinc-50 dark:hover:border-white/10 dark:hover:bg-white/[0.03]"}`}>
                  <span className="block text-[9px] font-black uppercase tracking-[0.08em] text-amber-500">{article.group}</span>
                  <span className="mt-0.5 block text-xs font-black text-zinc-900 dark:text-white">{article.title}</span>
                </button>
              ))}
              {!filtered.length ? <p className="py-6 text-center text-xs font-bold text-zinc-400">{tx("لا توجد نتائج مطابقة.", "No matching help topics.")}</p> : null}
            </div>
          </aside>

          <main className="min-h-0 overflow-y-auto p-4 sm:p-5">
            <div className="mx-auto max-w-3xl">
              <div className="flex items-start gap-3">
                <div className="grid h-11 w-11 shrink-0 place-items-center rounded-2xl bg-amber-50 text-amber-600 dark:bg-amber-400/10 dark:text-amber-300"><BookOpen size={21} /></div>
                <div>
                  <p className="text-[10px] font-black uppercase tracking-[0.1em] text-amber-500">{selected.group}</p>
                  <h3 className="mt-1 text-2xl font-black text-zinc-950 dark:text-white">{selected.title}</h3>
                  <p className="mt-1 text-sm font-bold text-zinc-400">{selected.subtitle}</p>
                </div>
              </div>

              <div className="mt-5 grid gap-3 sm:grid-cols-2">
                <HelpBlock icon={BookOpen} label={tx("ما معناه؟", "What it means")} tone="blue">{selected.meaning}</HelpBlock>
                <HelpBlock icon={Calculator} label={tx("كيف يتم حسابه؟", "How it is calculated")} tone="amber">{selected.calculation}</HelpBlock>
                <HelpBlock icon={Database} label={tx("المصدر", "Source")} tone="zinc">{selected.source}</HelpBlock>
                <HelpBlock icon={Lightbulb} label={tx("كيف تستخدمه؟", "How to use it")} tone="emerald">{selected.use}</HelpBlock>
              </div>

              {selected.details?.length ? (
                <div className="mt-4 rounded-2xl border border-zinc-200 p-4 dark:border-white/10">
                  <div className="flex items-center gap-2"><Calculator size={16} className="text-amber-500" /><p className="text-xs font-black text-zinc-950 dark:text-white">{tx("تفاصيل المعادلة", "Formula details")}</p></div>
                  <ul className="mt-3 space-y-2 text-xs font-bold leading-6 text-zinc-600 dark:text-zinc-300">
                    {selected.details.map((item) => <li key={item} className="flex gap-2"><span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-amber-500" /><span>{item}</span></li>)}
                  </ul>
                </div>
              ) : null}

              <div className="mt-4 flex items-start gap-2 rounded-2xl border border-emerald-200 bg-emerald-50/70 p-3 text-xs font-bold leading-5 text-emerald-800 dark:border-emerald-400/15 dark:bg-emerald-400/[0.06] dark:text-emerald-200">
                <ShieldCheck size={17} className="mt-0.5 shrink-0" />
                <span>{tx("هذا المركز يشرح قواعد TOS الحالية فقط. فتحه أو البحث داخله لا يغير أي Score أو بيانات أو صلاحيات.", "This Help Center explains the current TOS rules only. Opening or searching it does not change any score, data or permissions.")}</span>
              </div>
            </div>
          </main>
        </div>
      </section>
    </div>
  );
}
'''

HELP.parent.mkdir(parents=True, exist_ok=True)
HELP.write_text(help_component, encoding='utf-8')

text = DASHBOARD.read_text(encoding='utf-8')

old = '  Clock3,\n  Download,'
new = '  Clock3,\n  CircleHelp,\n  Download,'
if old not in text:
    raise SystemExit('PHASE5_HELP_CENTER_ERROR=LUCIDE_ANCHOR_NOT_FOUND')
text = text.replace(old, new, 1)

old = 'import { PerformanceDrilldownNavigator } from "../components/performance/PerformanceDrilldownNavigator";\n'
new = old + 'import { TeamPerformanceHelpCenter } from "../components/performance/TeamPerformanceHelpCenter";\n'
if old not in text:
    raise SystemExit('PHASE5_HELP_CENTER_ERROR=IMPORT_ANCHOR_NOT_FOUND')
text = text.replace(old, new, 1)

old = '  const [toast, setToast] = useState(null);\n\n  const [intelligenceData, setIntelligenceData] = useState(null);'
new = '  const [toast, setToast] = useState(null);\n  const [helpCenterOpen, setHelpCenterOpen] = useState(false);\n  const [helpArticle, setHelpArticle] = useState("overview");\n\n  const [intelligenceData, setIntelligenceData] = useState(null);'
if old not in text:
    raise SystemExit('PHASE5_HELP_CENTER_ERROR=STATE_ANCHOR_NOT_FOUND')
text = text.replace(old, new, 1)

old = '  async function exportReport(format) {'
new = '''  function openHelpCenter(articleKey = "overview") {
    setHelpArticle(articleKey);
    setHelpCenterOpen(true);
  }

  async function exportReport(format) {'''
if old not in text:
    raise SystemExit('PHASE5_HELP_CENTER_ERROR=FUNCTION_ANCHOR_NOT_FOUND')
text = text.replace(old, new, 1)

old = '        actions={<div className="flex items-center gap-2">{canManageTargets ? <button type="button" onClick={openTargetManager} className="rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-xs font-black text-amber-700 hover:bg-amber-100 dark:border-amber-400/20 dark:bg-amber-400/10 dark:text-amber-300">Manage Targets</button> : null}<Badge tone="success"><ShieldCheck size={14} /> Live data</Badge></div>}\n'
new = '''        actions={<div className="flex flex-wrap items-center gap-2"><button type="button" onClick={() => openHelpCenter("overview")} className="inline-flex items-center gap-2 rounded-xl border border-zinc-200 bg-white px-3 py-2 text-xs font-black text-zinc-700 hover:border-amber-300 hover:text-amber-700 dark:border-white/10 dark:bg-white/[0.03] dark:text-zinc-200 dark:hover:border-amber-400/30 dark:hover:text-amber-300"><CircleHelp size={15} /> Help Center</button>{canManageTargets ? <button type="button" onClick={openTargetManager} className="rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-xs font-black text-amber-700 hover:bg-amber-100 dark:border-amber-400/20 dark:bg-amber-400/10 dark:text-amber-300">Manage Targets</button> : null}<Badge tone="success"><ShieldCheck size={14} /> Live data</Badge></div>}\n'''
if old not in text:
    raise SystemExit('PHASE5_HELP_CENTER_ERROR=PAGE_INTRO_ANCHOR_NOT_FOUND')
text = text.replace(old, new, 1)

old = '      />\n\n      <Card className="p-4">'
new = '''      />

      <TeamPerformanceHelpCenter
        open={helpCenterOpen}
        onClose={() => setHelpCenterOpen(false)}
        lang={lang}
        initialArticle={helpArticle}
      />

      <Card className="p-4">'''
if old not in text:
    raise SystemExit('PHASE5_HELP_CENTER_ERROR=HELP_RENDER_ANCHOR_NOT_FOUND')
text = text.replace(old, new, 1)

DASHBOARD.write_text(text, encoding='utf-8')

print('PHASE5_HELP_CENTER_COMPONENT_CREATED=YES')
print('PHASE5_HELP_CENTER_DASHBOARD_WIRED=YES')
