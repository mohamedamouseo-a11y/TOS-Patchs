#!/usr/bin/env python3
from pathlib import Path

ROOT = Path('/var/www/TOS')
TASKS = ROOT / 'backend/src/routes/tasks.routes.js'
TOOLS = ROOT / 'backend/src/agency-operator/tools/createRamzyTools.js'
AGENT = ROOT / 'backend/src/agency-operator/agents/ramzyAgencyOperator.js'
SPECIALISTS = ROOT / 'backend/src/agency-operator/agents/specialistAgents.js'
PROMPT = ROOT / 'backend/src/agency-operator/prompts/ramzyPrompt.js'
SERVICE = ROOT / 'backend/src/agency-operator/services/ramzyTeamPerformance.service.js'

for path, key in [(TASKS, 'TASKS'), (TOOLS, 'TOOLS'), (AGENT, 'AGENT'), (SPECIALISTS, 'SPECIALISTS'), (PROMPT, 'PROMPT')]:
    if not path.exists():
        raise SystemExit(f'PHASE6_RAMZY_PERFORMANCE_ERROR={key}_NOT_FOUND')
if SERVICE.exists():
    raise SystemExit('PHASE6_RAMZY_PERFORMANCE_ERROR=SERVICE_ALREADY_EXISTS')

# -----------------------------------------------------------------------------
# 1) Reuse the exact existing Team Performance / Workforce read models.
#    We only export the already-existing builders; their logic is unchanged.
# -----------------------------------------------------------------------------
tasks = TASKS.read_text(encoding='utf-8')
old = 'async function buildTeamPerformanceExportDataset(req, payload = {}) {'
new = 'export async function buildTeamPerformanceExportDataset(req, payload = {}) {'
if old not in tasks:
    raise SystemExit('PHASE6_RAMZY_PERFORMANCE_ERROR=TEAM_DATASET_ANCHOR_NOT_FOUND')
tasks = tasks.replace(old, new, 1)

old = 'async function buildWorkforceForecast(req, payload = {}) {'
new = 'export async function buildWorkforceForecast(req, payload = {}) {'
if old not in tasks:
    raise SystemExit('PHASE6_RAMZY_PERFORMANCE_ERROR=WORKFORCE_ANCHOR_NOT_FOUND')
tasks = tasks.replace(old, new, 1)
TASKS.write_text(tasks, encoding='utf-8')

# -----------------------------------------------------------------------------
# 2) Add a compact, read-only Ramzy adapter over the existing builders.
# -----------------------------------------------------------------------------
service = r'''import { buildTeamPerformanceExportDataset, buildWorkforceForecast } from "../../routes/tasks.routes.js";

const PERFORMANCE_STATUS_THRESHOLDS = [
  { min: 85, label: "Excellent" },
  { min: 70, label: "On Track" },
  { min: 50, label: "Needs Attention" },
  { min: 0, label: "At Risk" },
];

const SCORE_METHOD = Object.freeze({
  weights: {
    completion: 35,
    onTimeOverdue: 25,
    timeEfficiency: 20,
    workflowQuality: 10,
    consistency: 10,
  },
  statusThresholds: {
    excellent: "85-100",
    onTrack: "70-84",
    needsAttention: "50-69",
    atRisk: "below 50",
    noActivity: "no meaningful activity => no score and no rank",
  },
  confidence: {
    high: "4-5 covered components",
    medium: "3 covered components",
    low: "0-2 covered components",
  },
  missingDataRule: "A component with no eligible data is skipped and the available weights are normalized back to 100. Missing eligible data does not automatically reduce the employee score.",
  source: "TOS Team Performance server-side scoring model",
});

function clean(value) {
  return String(value || "")
    .normalize("NFKD")
    .replace(/[\u064B-\u065F\u0670]/g, "")
    .toLowerCase()
    .replace(/[\s_-]+/g, " ")
    .trim();
}

function startOfDay(date) {
  const next = new Date(date);
  next.setHours(0, 0, 0, 0);
  return next;
}

function endOfDay(date) {
  const next = new Date(date);
  next.setHours(23, 59, 59, 999);
  return next;
}

function periodRange(preset = "month", startValue = null, endValue = null) {
  const now = new Date();
  if (startValue || endValue) {
    const start = startValue ? startOfDay(new Date(startValue)) : null;
    const end = endValue ? endOfDay(new Date(endValue)) : null;
    if (!start || !end || Number.isNaN(start.getTime()) || Number.isNaN(end.getTime()) || start > end) {
      throw new Error("A valid start and end date are required when using a custom Team Performance period");
    }
    return { preset: "custom", start, end };
  }

  const key = String(preset || "month").toLowerCase();
  if (key === "today") return { preset: key, start: startOfDay(now), end: endOfDay(now) };
  if (key === "yesterday") {
    const day = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 1);
    return { preset: key, start: startOfDay(day), end: endOfDay(day) };
  }
  if (key === "week") {
    const weekday = now.getDay() || 7;
    return { preset: key, start: startOfDay(new Date(now.getFullYear(), now.getMonth(), now.getDate() - weekday + 1)), end: endOfDay(now) };
  }
  if (key === "quarter") {
    const quarterStartMonth = Math.floor(now.getMonth() / 3) * 3;
    return { preset: key, start: startOfDay(new Date(now.getFullYear(), quarterStartMonth, 1)), end: endOfDay(now) };
  }
  if (key === "year") return { preset: key, start: startOfDay(new Date(now.getFullYear(), 0, 1)), end: endOfDay(now) };
  return { preset: "month", start: startOfDay(new Date(now.getFullYear(), now.getMonth(), 1)), end: endOfDay(now) };
}

function periodPayload(range) {
  return {
    preset: range.preset,
    start: range.start.toISOString(),
    end: range.end.toISOString(),
  };
}

function compactBreakdown(breakdown = null) {
  if (!breakdown || typeof breakdown !== "object") return null;
  return Object.fromEntries(Object.entries(breakdown).map(([key, value]) => [key, {
    score: value?.score ?? null,
    achieved: value?.achieved ?? 0,
    max: value?.max ?? 0,
    skipped: Boolean(value?.skipped),
  }]));
}

function coveredComponents(breakdown = null) {
  if (!breakdown || typeof breakdown !== "object") return 0;
  return Object.values(breakdown).filter((value) => !value?.skipped).length;
}

function statusReason(row) {
  if (row?.performanceScore == null) return "No Activity: there is no meaningful activity for a Performance Score, so the employee is unscored and unranked.";
  const score = Number(row.performanceScore);
  const band = PERFORMANCE_STATUS_THRESHOLDS.find((item) => score >= item.min)?.label || "At Risk";
  if (band === "Excellent") return `Performance Score ${score} is at least 85, therefore the status is Excellent.`;
  if (band === "On Track") return `Performance Score ${score} is between 70 and 84, therefore the status is On Track.`;
  if (band === "Needs Attention") return `Performance Score ${score} is between 50 and 69, therefore the status is Needs Attention.`;
  return `Performance Score ${score} is below 50, therefore the status is At Risk.`;
}

function componentEvidence(row) {
  const breakdown = compactBreakdown(row?.scoreBreakdown);
  if (!breakdown) return [];
  const labels = {
    completion: "Completion",
    onTime: "On-time / Overdue",
    efficiency: "Time Efficiency",
    workflow: "Workflow Quality",
    consistency: "Consistency",
  };
  return Object.entries(breakdown).map(([key, value]) => ({
    component: labels[key] || key,
    result: value.skipped ? "Skipped" : `${value.achieved}/${value.max}`,
    componentScore: value.score,
    skipped: value.skipped,
  }));
}

function performanceEvidence(row) {
  if (!row) return null;
  const breakdown = compactBreakdown(row.scoreBreakdown);
  const covered = coveredComponents(breakdown);
  const evidence = [statusReason(row)];
  if (Number(row.overdueTasks || 0) > 0) evidence.push(`${Number(row.overdueTasks)} overdue task(s) are present in the selected reporting period.`);
  if (Number(row.totalTasks || 0) > 0) evidence.push(`${Number(row.completedTasks || 0)} of ${Number(row.totalTasks || 0)} task(s) are completed (${Number(row.completionRate || 0)}% completion).`);
  evidence.push(`Score confidence is ${row.scoreConfidence || "Low"}; ${covered} of 5 score components have eligible data.`);
  return evidence;
}

function compactEmployee(row) {
  if (!row) return null;
  return {
    name: row.name || "—",
    department: row.department || null,
    jobTitle: row.jobTitle || null,
    rank: row.rank ?? null,
    performanceScore: row.performanceScore ?? null,
    status: row.status || "No Activity",
    confidence: row.scoreConfidence || "Low",
    completedTasks: Number(row.completedTasks || 0),
    totalTasks: Number(row.totalTasks || 0),
    completionRate: Number(row.completionRate || 0),
    overdueTasks: Number(row.overdueTasks || 0),
    loggedHours: Number(row.actualHours || 0),
    scoreBreakdown: compactBreakdown(row.scoreBreakdown),
    componentEvidence: componentEvidence(row),
    explanation: performanceEvidence(row),
  };
}

function compactSummary(dataset) {
  const rows = Array.isArray(dataset?.rows) ? dataset.rows : [];
  const atRisk = rows.filter((row) => row.status === "At Risk").length;
  const needsAttention = rows.filter((row) => row.status === "Needs Attention").length;
  const noActivity = rows.filter((row) => row.performanceScore == null).length;
  const summary = dataset?.summary || {};
  return {
    employeeCount: rows.length,
    scoredEmployees: rows.filter((row) => row.performanceScore != null).length,
    averageScore: summary.avgScore ?? null,
    topPerformer: summary.topPerformer ? compactEmployee(summary.topPerformer) : null,
    completedTasks: Number(summary.completedTasks || 0),
    totalTasks: Number(summary.totalTasks || 0),
    completionRate: Number(summary.completionRate || 0),
    overdueTasks: Number(summary.overdueTasks || 0),
    loggedHours: Number(summary.actualHours || 0),
    atRiskEmployees: atRisk,
    needsAttentionEmployees: needsAttention,
    noActivityEmployees: noActivity,
    attention: rows
      .filter((row) => ["At Risk", "Needs Attention"].includes(row.status))
      .sort((a, b) => Number(a.performanceScore ?? 999) - Number(b.performanceScore ?? 999))
      .slice(0, 5)
      .map(compactEmployee),
  };
}

function resolveEmployee(rows, { employeeId = null, employeeQuery = null } = {}) {
  const list = Array.isArray(rows) ? rows : [];
  if (employeeId) {
    const match = list.find((row) => row.id === employeeId) || null;
    return match ? { match, ambiguous: false, candidates: [] } : { match: null, ambiguous: false, candidates: [] };
  }
  const query = clean(employeeQuery);
  if (!query) return { match: null, ambiguous: false, candidates: [] };
  const exact = list.filter((row) => [row.name, row.email].some((value) => clean(value) === query));
  if (exact.length === 1) return { match: exact[0], ambiguous: false, candidates: [] };
  if (exact.length > 1) return { match: null, ambiguous: true, candidates: exact.slice(0, 5) };
  const starts = list.filter((row) => clean(row.name).startsWith(query));
  if (starts.length === 1) return { match: starts[0], ambiguous: false, candidates: [] };
  if (starts.length > 1) return { match: null, ambiguous: true, candidates: starts.slice(0, 5) };
  const contains = list.filter((row) => clean(row.name).includes(query) || clean(row.email).includes(query));
  if (contains.length === 1) return { match: contains[0], ambiguous: false, candidates: [] };
  if (contains.length > 1) return { match: null, ambiguous: true, candidates: contains.slice(0, 5) };
  return { match: null, ambiguous: false, candidates: [] };
}

function compactWorkforceRow(row) {
  if (!row) return null;
  return {
    name: row.name || "—",
    department: row.department || null,
    jobTitle: row.jobTitle || null,
    capacityRisk: row.capacityRisk || "UNKNOWN",
    outlook: row.outlook || null,
    forecastConfidence: row.forecastConfidence || null,
    weeklyCapacityHours: row.weeklyCapacityHours ?? null,
    capacityHours: row.capacityHours ?? null,
    capacitySource: row.capacitySource || null,
    plannedRemainingHours: row.plannedRemainingHours ?? null,
    utilizationPercent: row.utilizationPercent ?? null,
    capacityGapHours: row.capacityGapHours ?? null,
    dueTasks: Number(row.dueTasks || 0),
    upcomingDueTasks: Number(row.upcomingDueTasks || 0),
    overdueOpenTasks: Number(row.overdueOpenTasks || 0),
    unestimatedDueTasks: Number(row.unestimatedDueTasks || 0),
    unscheduledOpenTasks: Number(row.unscheduledOpenTasks || 0),
    performanceScore: row.performanceScore ?? null,
    performanceStatus: row.performanceStatus || "No Activity",
    scoreDelta: row.scoreDelta ?? null,
    targetAchievement: row.targetAchievement ?? null,
    targetStatus: row.targetStatus || "No Target",
    signals: Array.isArray(row.signals) ? row.signals.map((signal) => ({ type: signal.type, severity: signal.severity, message: signal.message })) : [],
  };
}

function workforceReason(row) {
  if (!row) return [];
  const reasons = [`Workforce Forecast classifies the current capacity risk as ${row.capacityRisk || "UNKNOWN"}.`];
  if (row.utilizationPercent != null) reasons.push(`Planned utilization is ${row.utilizationPercent}% across the forecast horizon.`);
  if (Number(row.overdueOpenTasks || 0) > 0) reasons.push(`${Number(row.overdueOpenTasks)} overdue open task(s) are contributing operational pressure.`);
  if (Number(row.unestimatedDueTasks || 0) > 0) reasons.push(`${Number(row.unestimatedDueTasks)} due task(s) are missing estimates, reducing forecast certainty.`);
  for (const signal of row.signals || []) reasons.push(String(signal.message || "").trim()).filter(Boolean);
  return [...new Set(reasons.filter(Boolean))];
}

function sourceMetadata() {
  return {
    performance: "Same server-side Team Performance dataset used by TOS Team Performance exports, targets and intelligence.",
    scoring: "Same existing Performance Score calculation; this Ramzy adapter creates no new score.",
    workforce: "Same existing Workforce Forecast builder used by Team Performance workforce planning.",
    accountScope: "Live performance rows are ACTIVE-only. DISABLED and PENDING users are not returned in live Team Performance results.",
    permissionScope: "The existing Team Performance / Workforce builders enforce the requesting user's current TOS scope before data reaches Ramzy.",
  };
}

export async function getRamzyTeamPerformance({
  user,
  mode = "SUMMARY",
  employeeQuery = null,
  employeeId = null,
  periodPreset = "month",
  start = null,
  end = null,
  department = null,
  horizonDays = 14,
} = {}) {
  if (!user?.id) throw new Error("Authenticated user is required for Team Performance intelligence");
  const normalizedMode = String(mode || "SUMMARY").toUpperCase();
  const sources = sourceMetadata();

  if (normalizedMode === "METHODOLOGY") {
    return {
      type: "TEAM_PERFORMANCE_METHODOLOGY",
      methodology: SCORE_METHOD,
      sources,
      readOnly: true,
    };
  }

  const range = periodRange(periodPreset, start, end);
  const dataset = await buildTeamPerformanceExportDataset({ user }, {
    start: range.start.toISOString(),
    end: range.end.toISOString(),
    department: department || null,
  });
  const rows = Array.isArray(dataset?.rows) ? dataset.rows : [];
  const resolution = resolveEmployee(rows, { employeeId, employeeQuery });

  if ((employeeId || employeeQuery) && resolution.ambiguous) {
    return {
      type: "TEAM_PERFORMANCE_EMPLOYEE_AMBIGUOUS",
      period: periodPayload(range),
      candidates: resolution.candidates.map((row, index) => ({ option: index + 1, name: row.name, department: row.department || null, jobTitle: row.jobTitle || null })),
      message: "More than one authorized ACTIVE employee matches the requested name. Ask the user to choose by number or provide a fuller name.",
      sources,
      readOnly: true,
    };
  }

  if ((employeeId || employeeQuery) && !resolution.match) {
    return {
      type: "TEAM_PERFORMANCE_EMPLOYEE_NOT_VISIBLE",
      period: periodPayload(range),
      message: "No matching ACTIVE employee exists inside the requesting user's authorized Team Performance scope for this period. Do not guess or reveal users outside this scope.",
      sources,
      readOnly: true,
    };
  }

  if (normalizedMode === "EMPLOYEE") {
    return {
      type: "TEAM_PERFORMANCE_EMPLOYEE",
      period: periodPayload(range),
      employee: compactEmployee(resolution.match),
      methodology: SCORE_METHOD,
      sources,
      readOnly: true,
    };
  }

  if (normalizedMode === "WORKFORCE") {
    const forecast = await buildWorkforceForecast({ user }, {
      horizonDays: Math.max(1, Math.min(90, Number(horizonDays || 14))),
      employeeId: resolution.match?.id || null,
      department: department || null,
    });
    const forecastRows = Array.isArray(forecast?.rows) ? forecast.rows : [];
    const selectedForecast = resolution.match
      ? forecastRows.find((row) => row.employeeId === resolution.match.id) || null
      : null;
    return {
      type: resolution.match ? "TEAM_PERFORMANCE_WORKFORCE_EMPLOYEE" : "TEAM_PERFORMANCE_WORKFORCE_SUMMARY",
      forecastHorizonDays: Number(forecast?.horizonDays || horizonDays || 14),
      employee: resolution.match ? compactEmployee(resolution.match) : null,
      workforce: selectedForecast
        ? { ...compactWorkforceRow(selectedForecast), explanation: workforceReason(selectedForecast) }
        : null,
      workforceSummary: forecast?.summary ? {
        employeeCount: Number(forecast.summary.employeeCount || 0),
        teamUtilizationPercent: forecast.summary.teamUtilizationPercent ?? null,
        criticalEmployees: Number(forecast.summary.criticalEmployees || 0),
        highRiskEmployees: Number(forecast.summary.highRiskEmployees || 0),
        watchEmployees: Number(forecast.summary.watchEmployees || 0),
        overdueOpenTasks: Number(forecast.summary.overdueOpenTasks || 0),
        unestimatedDueTasks: Number(forecast.summary.unestimatedDueTasks || 0),
      } : null,
      topCapacityRisk: resolution.match ? [] : forecastRows.slice(0, 5).map((row) => ({ ...compactWorkforceRow(row), explanation: workforceReason(row) })),
      sources,
      readOnly: true,
    };
  }

  return {
    type: "TEAM_PERFORMANCE_SUMMARY",
    period: periodPayload(range),
    summary: compactSummary(dataset),
    methodology: SCORE_METHOD,
    sources,
    readOnly: true,
  };
}
'''
SERVICE.write_text(service, encoding='utf-8')

# -----------------------------------------------------------------------------
# 3) Register the read-only Team Performance tool.
# -----------------------------------------------------------------------------
tools = TOOLS.read_text(encoding='utf-8')
anchor = 'import { lookupRamzyProjects, lookupRamzyUsers, searchRamzyTasks } from "../services/ramzySystemIntelligence.service.js";\n'
addition = anchor + 'import { getRamzyTeamPerformance } from "../services/ramzyTeamPerformance.service.js";\n'
if anchor not in tools:
    raise SystemExit('PHASE6_RAMZY_PERFORMANCE_ERROR=TOOLS_IMPORT_ANCHOR_NOT_FOUND')
tools = tools.replace(anchor, addition, 1)

anchor = '''  const getRecentChatContextTool = createTool({\n'''
tool_block = r'''  const getTeamPerformanceTool = createTool({
    id: "get_team_performance",
    description: "Read-only Team Performance intelligence using the same authorized server-side dataset as the Team Performance page. Use for performance score/status/confidence, team KPIs, employee performance explanations, and Workforce capacity risk. Never invent a score.",
    inputSchema: z.object({
      mode: z.enum(["SUMMARY", "EMPLOYEE", "METHODOLOGY", "WORKFORCE"]).default("SUMMARY"),
      employeeQuery: z.string().min(1).max(160).optional(),
      employeeId: z.string().optional(),
      periodPreset: z.enum(["today", "yesterday", "week", "month", "quarter", "year"]).default("month"),
      start: z.string().max(64).optional(),
      end: z.string().max(64).optional(),
      department: z.string().max(160).optional(),
      horizonDays: z.number().int().min(1).max(90).default(14),
    }),
    execute: async (input) => executeLogged("get_team_performance", input, () => getRamzyTeamPerformance({ user, ...input })),
  });

'''
if anchor not in tools:
    raise SystemExit('PHASE6_RAMZY_PERFORMANCE_ERROR=TOOLS_INSERT_ANCHOR_NOT_FOUND')
tools = tools.replace(anchor, tool_block + anchor, 1)

old = '''    getTaskDetailsTool,\n    getRecentChatContextTool,\n'''
new = '''    getTaskDetailsTool,\n    getTeamPerformanceTool,\n    getRecentChatContextTool,\n'''
if old not in tools:
    raise SystemExit('PHASE6_RAMZY_PERFORMANCE_ERROR=TOOLS_RETURN_ANCHOR_NOT_FOUND')
tools = tools.replace(old, new, 1)
TOOLS.write_text(tools, encoding='utf-8')

# -----------------------------------------------------------------------------
# 4) Make the tool available to specialist agents too.
# -----------------------------------------------------------------------------
agent = AGENT.read_text(encoding='utf-8')
old = '''    getTaskDetailsTool: tools.getTaskDetailsTool,\n    getRecentChatContextTool: tools.getRecentChatContextTool,\n'''
new = '''    getTaskDetailsTool: tools.getTaskDetailsTool,\n    getTeamPerformanceTool: tools.getTeamPerformanceTool,\n    getRecentChatContextTool: tools.getRecentChatContextTool,\n'''
if old not in agent:
    raise SystemExit('PHASE6_RAMZY_PERFORMANCE_ERROR=AGENT_READ_TOOLS_ANCHOR_NOT_FOUND')
agent = agent.replace(old, new, 1)
AGENT.write_text(agent, encoding='utf-8')

# -----------------------------------------------------------------------------
# 5) Tighten Ramzy instructions so performance answers are grounded.
# -----------------------------------------------------------------------------
prompt = PROMPT.read_text(encoding='utf-8')
anchor = '- أعطِ الأولوية للتأخير، SLA، العوائق، المهام غير المسندة، وضغط العمل.\n'
addition = anchor + '''- عند أي سؤال عن Team Performance أو Performance Score أو Status أو Confidence أو Top Performer أو Completed/Overdue/Logged Hours أو أداء موظف أو Capacity/Workforce Risk، استخدم أداة get_team_performance أولًا قبل إعطاء رقم أو سبب.\n- في أسئلة الأداء الفعلية اذكر الفترة التي تقيسها الأداة بوضوح. إذا لم يحدد المستخدم فترة فالأداة تستخدم Month-to-date مثل الوضع الافتراضي لصفحة Team Performance.\n- لا تنشئ Score أو Rating جديد. Performance Score الوحيد هو الموجود في Team Performance: Completion 35%، On-time/Overdue 25%، Time Efficiency 20%، Workflow Quality 10%، Consistency 10%، مع normalization للمكونات المتاحة فقط عند غياب بيانات مؤهلة.\n- Status يعتمد على Score الحالي: 85+ Excellent، 70-84 On Track، 50-69 Needs Attention، وأقل من 50 At Risk. No Activity غير مسجل Score أو Rank.\n- عند سؤال مثل «ليه فلان At Risk؟» اشرح أولًا أن السبب المباشر للحالة هو عبور Score للـthreshold، ثم اعرض الأدلة الحقيقية من scoreBreakdown والـCompleted/Overdue/Hours الموجودة في الأداة. لا تخمّن سببًا غير موجود.\n- عند سؤال Capacity/Workforce استخدم mode=WORKFORCE واشرح utilization والدemand والoverdue والsignals التي أعادتها الأداة. لا تحول Capacity Risk إلى حكم HR على الشخص.\n- إذا أعادت الأداة Employee Not Visible فلا تحاول الوصول للموظف بأداة أخرى للتحايل على نطاق Team Performance ولا تذكر أسماء خارج النطاق. وإذا أعادت Ambiguous اطلب من المستخدم اختيار رقم النتيجة.\n- Team Performance live data هي ACTIVE-only حسب نفس قواعد الصفحة؛ لا تُدخل DISABLED أو PENDING في KPIs أو ranking أو المقارنات الحية.\n'''
if anchor not in prompt:
    raise SystemExit('PHASE6_RAMZY_PERFORMANCE_ERROR=PROMPT_ANCHOR_NOT_FOUND')
prompt = prompt.replace(anchor, addition, 1)
PROMPT.write_text(prompt, encoding='utf-8')

# -----------------------------------------------------------------------------
# 6) Performance specialist must use the new read model rather than task counts.
# -----------------------------------------------------------------------------
specialists = SPECIALISTS.read_text(encoding='utf-8')
old = '      instructions: "قدم ملخصًا متوازنًا قائمًا على البيانات، وافصل الحقائق عن الاستنتاجات. لا تحول أعداد المهام وحدها إلى تقييم فردي قاطع.",\n'
new = '      instructions: "استخدم get_team_performance لأي Score أو Status أو Confidence أو KPI أو Capacity Risk. قدم ملخصًا متوازنًا قائمًا على نفس Team Performance server-side data، اذكر الفترة والمصدر، وافصل الحقائق عن الاستنتاجات. لا تحول أعداد المهام وحدها إلى تقييم فردي قاطع ولا تنشئ Score جديدًا.",\n'
if old not in specialists:
    raise SystemExit('PHASE6_RAMZY_PERFORMANCE_ERROR=SPECIALIST_ANCHOR_NOT_FOUND')
specialists = specialists.replace(old, new, 1)
SPECIALISTS.write_text(specialists, encoding='utf-8')

print('TEAM_PERFORMANCE_PHASE6_RAMZY_V1_APPLIED=YES')
print('RAMZY_TEAM_PERFORMANCE_TOOL=YES')
print('RAMZY_USES_EXISTING_TEAM_PERFORMANCE_DATASET=YES')
print('RAMZY_USES_EXISTING_WORKFORCE_FORECAST=YES')
print('NEW_SCORE_CREATED=NO')
print('NEW_API_ENDPOINT=NO')
print('SCHEMA_CHANGED=NO')
print('FRONTEND_CHANGED=NO')
