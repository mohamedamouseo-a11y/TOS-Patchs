#!/usr/bin/env python3
from pathlib import Path
import sys

repo = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
path = repo / "frontend/src/components/performance/SkillsDevelopment.jsx"
if path.exists():
    raise SystemExit("PHASE9_COMPONENT_ALREADY_PRESENT")
path.parent.mkdir(parents=True, exist_ok=True)

content = r'''import { useEffect, useMemo, useState } from "react";
import {
  AlertCircle,
  BarChart3,
  CheckCircle2,
  Clock3,
  Plus,
  RefreshCw,
  Settings2,
  UserRound,
  UsersRound,
  X,
} from "lucide-react";
import { Badge, Card, Notice } from "../ui/Primitives";
import { api } from "../../lib/api";
import { getErrorMessage } from "../../lib/errors";

const LEVEL_LABELS = {
  1: "Awareness",
  2: "Basic",
  3: "Working",
  4: "Advanced",
  5: "Expert",
};

const MANAGER_ROLES = new Set(["SUPER_ADMIN", "ADMIN", "MANAGER", "PROJECT_MANAGER"]);
const ADMIN_ROLES = new Set(["SUPER_ADMIN", "ADMIN"]);

function levelLabel(value) {
  const level = Number(value);
  return level ? `${level} · ${LEVEL_LABELS[level] || ""}` : "Not assessed";
}

function human(value) {
  return String(value || "—").replaceAll("_", " ").toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase());
}

function dateInput(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
  return local.toISOString().slice(0, 10);
}

function dateLabel(value) {
  if (!value) return "—";
  try {
    return new Intl.DateTimeFormat("en-GB", { day: "2-digit", month: "short", year: "numeric" }).format(new Date(value));
  } catch {
    return "—";
  }
}

function statusTone(status) {
  if (["MET", "COMPLETED"].includes(status)) return "success";
  if (["CRITICAL_GAP", "OVERDUE", "CANCELLED"].includes(status)) return "danger";
  if (["GAP", "UNASSESSED", "NEAR", "IN_PROGRESS"].includes(status)) return "warning";
  if (["ACTIVE"].includes(status)) return "blue";
  return "neutral";
}

function MiniMetric({ label, value, note }) {
  return (
    <div className="rounded-2xl border border-zinc-100 bg-zinc-50/60 p-3 dark:border-white/10 dark:bg-white/[0.025]">
      <p className="text-[10px] font-black uppercase tracking-[0.08em] text-zinc-400">{label}</p>
      <p className="mt-1 text-xl font-black text-zinc-950 dark:text-white">{value}</p>
      {note ? <p className="mt-1 text-[10px] font-bold text-zinc-400">{note}</p> : null}
    </div>
  );
}

function SkillLevelDots({ currentLevel, targetLevel }) {
  return (
    <div className="flex items-center gap-1" aria-label={`Current level ${currentLevel ?? 0}, target ${targetLevel ?? 0}`}>
      {[1, 2, 3, 4, 5].map((level) => (
        <span
          key={level}
          className={`h-2.5 w-2.5 rounded-full border ${level <= Number(currentLevel || 0) ? "border-emerald-500 bg-emerald-500" : level <= Number(targetLevel || 0) ? "border-amber-400 bg-amber-100 dark:bg-amber-400/20" : "border-zinc-200 bg-zinc-100 dark:border-white/10 dark:bg-white/5"}`}
        />
      ))}
    </div>
  );
}

export function SkillsDevelopmentPanel({
  user,
  employees = [],
  employeeFilter = "all",
  departmentFilter = "all",
  refreshToken = "",
  onOpenEmployee = null,
}) {
  const role = String(user?.role || "").toUpperCase();
  const canManage = MANAGER_ROLES.has(role);
  const canConfigure = ADMIN_ROLES.has(role);

  const [matrix, setMatrix] = useState(null);
  const [plans, setPlans] = useState([]);
  const [catalog, setCatalog] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [toast, setToast] = useState(null);
  const [localRefresh, setLocalRefresh] = useState(0);

  const [frameworkOpen, setFrameworkOpen] = useState(false);
  const [requirements, setRequirements] = useState([]);
  const [frameworkLoading, setFrameworkLoading] = useState(false);
  const [frameworkSaving, setFrameworkSaving] = useState(false);
  const [skillForm, setSkillForm] = useState({ name: "", category: "General", description: "" });
  const [requirementForm, setRequirementForm] = useState({ skillId: "", scopeType: "DEPARTMENT", department: "", jobTitle: "", employeeId: "", targetLevel: "3", importance: "CORE" });

  const [assessmentOpen, setAssessmentOpen] = useState(false);
  const [assessmentSaving, setAssessmentSaving] = useState(false);
  const [assessmentForm, setAssessmentForm] = useState({ employeeId: "", skillId: "", currentLevel: "3", evidence: "" });

  const [planOpen, setPlanOpen] = useState(false);
  const [planSaving, setPlanSaving] = useState(false);
  const [planForm, setPlanForm] = useState({ employeeId: "", skillId: "", title: "", objective: "", targetLevel: "", targetDate: "" });

  const [actionOpen, setActionOpen] = useState(false);
  const [actionSaving, setActionSaving] = useState(false);
  const [actionForm, setActionForm] = useState({ planId: "", title: "", description: "", dueDate: "" });

  const departments = useMemo(() => [...new Set(employees.map((employee) => employee.department).filter(Boolean))].sort(), [employees]);
  const jobTitles = useMemo(() => [...new Set(employees.map((employee) => employee.jobTitle).filter(Boolean))].sort(), [employees]);

  async function loadMain() {
    setLoading(true);
    setError("");
    try {
      const params = {
        employeeId: employeeFilter !== "all" ? employeeFilter : "",
        department: departmentFilter !== "all" ? departmentFilter : "",
      };
      const [matrixResult, planResult, catalogResult] = await Promise.all([
        api.tasks.skillsMatrix(params),
        api.tasks.developmentPlans(params),
        api.tasks.skillCatalog({}),
      ]);
      setMatrix(matrixResult);
      setPlans(planResult?.plans || []);
      setCatalog(catalogResult?.skills || []);
    } catch (err) {
      setMatrix(null);
      setPlans([]);
      setError(getErrorMessage(err, "Unable to load skills and development data."));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadMain();
  }, [employeeFilter, departmentFilter, refreshToken, localRefresh]);

  function firstEmployeeId() {
    return employeeFilter !== "all" ? employeeFilter : (matrix?.rows?.[0]?.employeeId || employees[0]?.id || "");
  }

  function openAssessment(employeeId = "", skillId = "") {
    if (!canManage) return;
    const resolvedEmployee = employeeId || firstEmployeeId();
    const resolvedSkill = skillId || catalog[0]?.id || "";
    const row = matrix?.rows?.find((item) => item.employeeId === resolvedEmployee);
    const skill = row?.skills?.find((item) => item.skillId === resolvedSkill);
    setAssessmentForm({
      employeeId: resolvedEmployee,
      skillId: resolvedSkill,
      currentLevel: String(skill?.currentLevel || 3),
      evidence: skill?.evidence || "",
    });
    setAssessmentOpen(true);
  }

  async function saveAssessment(event) {
    event.preventDefault();
    setAssessmentSaving(true);
    try {
      await api.tasks.assessEmployeeSkill({
        employeeId: assessmentForm.employeeId,
        skillId: assessmentForm.skillId,
        currentLevel: Number(assessmentForm.currentLevel),
        evidence: assessmentForm.evidence || null,
      });
      setToast({ type: "success", message: "Skill assessment saved." });
      setAssessmentOpen(false);
      setLocalRefresh((value) => value + 1);
    } catch (err) {
      setToast({ type: "error", message: getErrorMessage(err, "Unable to save skill assessment.") });
    } finally {
      setAssessmentSaving(false);
    }
  }

  function openPlan(employeeId = "", skillId = "") {
    if (!canManage) return;
    const resolvedEmployee = employeeId || firstEmployeeId();
    const row = matrix?.rows?.find((item) => item.employeeId === resolvedEmployee);
    const gap = row?.skills?.find((item) => item.skillId === skillId) || row?.skills?.find((item) => item.status !== "MET" && item.targetLevel != null);
    setPlanForm({
      employeeId: resolvedEmployee,
      skillId: skillId || gap?.skillId || "",
      title: gap ? `Develop ${gap.name}` : "",
      objective: gap ? `Close the ${gap.name} competency gap and reach the required proficiency level.` : "",
      targetLevel: gap?.targetLevel ? String(gap.targetLevel) : "",
      targetDate: "",
    });
    setPlanOpen(true);
  }

  async function savePlan(event) {
    event.preventDefault();
    setPlanSaving(true);
    try {
      await api.tasks.createDevelopmentPlan({
        employeeId: planForm.employeeId,
        skillId: planForm.skillId || null,
        title: planForm.title,
        objective: planForm.objective || null,
        targetLevel: planForm.targetLevel ? Number(planForm.targetLevel) : null,
        targetDate: planForm.targetDate || null,
      });
      setToast({ type: "success", message: "Development plan created as draft." });
      setPlanOpen(false);
      setLocalRefresh((value) => value + 1);
    } catch (err) {
      setToast({ type: "error", message: getErrorMessage(err, "Unable to create development plan.") });
    } finally {
      setPlanSaving(false);
    }
  }

  async function planAction(planId, action) {
    setPlanSaving(true);
    try {
      if (action === "activate") await api.tasks.activateDevelopmentPlan(planId);
      else if (action === "complete") await api.tasks.completeDevelopmentPlan(planId);
      else if (action === "cancel") await api.tasks.cancelDevelopmentPlan(planId);
      setLocalRefresh((value) => value + 1);
    } catch (err) {
      setToast({ type: "error", message: getErrorMessage(err, `Unable to ${action} development plan.`) });
    } finally {
      setPlanSaving(false);
    }
  }

  function openAction(planId) {
    setActionForm({ planId, title: "", description: "", dueDate: "" });
    setActionOpen(true);
  }

  async function saveAction(event) {
    event.preventDefault();
    setActionSaving(true);
    try {
      await api.tasks.createDevelopmentAction(actionForm.planId, {
        title: actionForm.title,
        description: actionForm.description || null,
        dueDate: actionForm.dueDate || null,
      });
      setActionOpen(false);
      setLocalRefresh((value) => value + 1);
    } catch (err) {
      setToast({ type: "error", message: getErrorMessage(err, "Unable to create development action.") });
    } finally {
      setActionSaving(false);
    }
  }

  async function updateActionStatus(planId, actionId, status) {
    try {
      await api.tasks.updateDevelopmentAction(planId, actionId, { status });
      setLocalRefresh((value) => value + 1);
    } catch (err) {
      setToast({ type: "error", message: getErrorMessage(err, "Unable to update development action.") });
    }
  }

  async function loadFramework() {
    if (!canConfigure) return;
    setFrameworkLoading(true);
    try {
      const [catalogResult, requirementResult] = await Promise.all([
        api.tasks.skillCatalog({ includeInactive: "true" }),
        api.tasks.skillRequirements(),
      ]);
      const skills = catalogResult?.skills || [];
      setCatalog(skills);
      setRequirements(requirementResult?.requirements || []);
      setRequirementForm((current) => ({
        ...current,
        skillId: current.skillId || skills.find((skill) => skill.isActive)?.id || "",
        department: current.department || departments[0] || "",
        jobTitle: current.jobTitle || jobTitles[0] || "",
        employeeId: current.employeeId || employees[0]?.id || "",
      }));
    } catch (err) {
      setToast({ type: "error", message: getErrorMessage(err, "Unable to load skills framework.") });
    } finally {
      setFrameworkLoading(false);
    }
  }

  async function openFramework() {
    setFrameworkOpen(true);
    await loadFramework();
  }

  async function createSkill(event) {
    event.preventDefault();
    setFrameworkSaving(true);
    try {
      await api.tasks.createSkillDefinition(skillForm);
      setSkillForm({ name: "", category: "General", description: "" });
      await loadFramework();
      setLocalRefresh((value) => value + 1);
    } catch (err) {
      setToast({ type: "error", message: getErrorMessage(err, "Unable to create skill.") });
    } finally {
      setFrameworkSaving(false);
    }
  }

  async function createRequirement(event) {
    event.preventDefault();
    setFrameworkSaving(true);
    try {
      await api.tasks.createSkillRequirement({
        skillId: requirementForm.skillId,
        scopeType: requirementForm.scopeType,
        department: requirementForm.scopeType === "DEPARTMENT" ? requirementForm.department : null,
        jobTitle: requirementForm.scopeType === "JOB_TITLE" ? requirementForm.jobTitle : null,
        employeeId: requirementForm.scopeType === "EMPLOYEE" ? requirementForm.employeeId : null,
        targetLevel: Number(requirementForm.targetLevel),
        importance: requirementForm.importance,
      });
      await loadFramework();
      setLocalRefresh((value) => value + 1);
    } catch (err) {
      setToast({ type: "error", message: getErrorMessage(err, "Unable to create competency requirement.") });
    } finally {
      setFrameworkSaving(false);
    }
  }

  async function deactivateSkill(skillId) {
    setFrameworkSaving(true);
    try {
      await api.tasks.deactivateSkillDefinition(skillId);
      await loadFramework();
      setLocalRefresh((value) => value + 1);
    } catch (err) {
      setToast({ type: "error", message: getErrorMessage(err, "Unable to deactivate skill.") });
    } finally {
      setFrameworkSaving(false);
    }
  }

  async function deactivateRequirement(requirementId) {
    setFrameworkSaving(true);
    try {
      await api.tasks.deactivateSkillRequirement(requirementId);
      await loadFramework();
      setLocalRefresh((value) => value + 1);
    } catch (err) {
      setToast({ type: "error", message: getErrorMessage(err, "Unable to deactivate requirement.") });
    } finally {
      setFrameworkSaving(false);
    }
  }

  const summary = matrix?.summary || {};
  const priorityGaps = matrix?.priorityGaps || [];
  const activePlans = plans.filter((plan) => ["DRAFT", "ACTIVE"].includes(plan.status));

  return (
    <>
      <Card className="overflow-hidden p-0">
        <div className="flex flex-col gap-3 border-b border-zinc-100 p-4 dark:border-white/10 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <p className="text-[11px] font-black uppercase tracking-[0.1em] text-amber-500">Skills, Competencies & Development</p>
              <Badge tone="blue">Phase 9</Badge>
            </div>
            <h2 className="mt-1 text-base font-black text-zinc-950 dark:text-white">Skills Matrix & Development Plans</h2>
            <p className="mt-1 max-w-3xl text-[11px] font-bold leading-5 text-zinc-400">Official proficiency assessments, role/department requirements, skill gaps and development follow-through. Skill coverage is separate from the Performance Score.</p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <button type="button" onClick={() => setLocalRefresh((value) => value + 1)} className="rounded-xl border border-zinc-200 p-2 text-zinc-500 dark:border-white/10" aria-label="Refresh skills data"><RefreshCw size={16} className={loading ? "animate-spin" : ""} /></button>
            {canManage ? <button type="button" onClick={() => openAssessment()} className="inline-flex items-center gap-2 rounded-xl border border-zinc-200 px-3 py-2 text-xs font-black text-zinc-700 hover:border-amber-300 dark:border-white/10 dark:text-zinc-200"><UserRound size={15} /> Assess Skill</button> : null}
            {canManage ? <button type="button" onClick={() => openPlan()} className="inline-flex items-center gap-2 rounded-xl border border-zinc-200 px-3 py-2 text-xs font-black text-zinc-700 hover:border-amber-300 dark:border-white/10 dark:text-zinc-200"><Plus size={15} /> Development Plan</button> : null}
            {canConfigure ? <button type="button" onClick={openFramework} className="inline-flex items-center gap-2 rounded-xl bg-zinc-950 px-3 py-2 text-xs font-black text-white dark:bg-white dark:text-zinc-950"><Settings2 size={15} /> Manage Framework</button> : null}
          </div>
        </div>

        {error ? <div className="p-4"><Notice type="error">{error}</Notice></div> : null}
        {toast ? <div className="px-4 pt-4"><Notice type={toast.type === "success" ? "success" : "error"}>{toast.message}</Notice></div> : null}

        {loading && !matrix ? <div className="h-44 animate-pulse bg-zinc-50 dark:bg-white/[0.025]" /> : (
          <>
            <div className="grid gap-3 p-4 sm:grid-cols-2 xl:grid-cols-5">
              <MiniMetric label="Skill Coverage" value={summary.overallCoveragePercent == null ? "—" : `${summary.overallCoveragePercent}%`} note={`${summary.coveredRequirements || 0}/${summary.requiredAssignments || 0} requirements met`} />
              <MiniMetric label="Critical Gaps" value={summary.criticalGaps || 0} note="Core competency gaps" />
              <MiniMetric label="Unassessed Required" value={summary.unassessedRequired || 0} note="Required skills awaiting assessment" />
              <MiniMetric label="Active Plans" value={summary.activeDevelopmentPlans || 0} note="Employee development plans" />
              <MiniMetric label="Overdue Actions" value={summary.overdueDevelopmentActions || 0} note="Development follow-up due" />
            </div>

            <div className="grid gap-4 border-t border-zinc-100 p-4 dark:border-white/10 xl:grid-cols-[1.35fr_.65fr]">
              <section>
                <div className="mb-3 flex items-center justify-between gap-2">
                  <div><h3 className="text-sm font-black text-zinc-950 dark:text-white">Team Skills Matrix</h3><p className="mt-1 text-[10px] font-bold text-zinc-400">Requirement precedence: Employee → Job Title → Department.</p></div>
                  <Badge>{matrix?.rows?.length || 0} employees</Badge>
                </div>
                <div className="hidden overflow-x-auto md:block">
                  <table className="w-full min-w-[760px] text-[11px]">
                    <thead className="text-zinc-400"><tr><th className="py-2 text-left">Employee</th><th className="py-2 text-right">Coverage</th><th className="py-2 text-right">Required</th><th className="py-2 text-right">Gaps</th><th className="py-2 text-right">Critical</th><th className="py-2 text-right">Unassessed</th><th className="py-2 text-right">Plans</th><th /></tr></thead>
                    <tbody className="divide-y divide-zinc-100 dark:divide-white/10">
                      {(matrix?.rows || []).map((row) => (
                        <tr key={row.employeeId}>
                          <td className="py-3 pr-2"><p className="font-black text-zinc-950 dark:text-white">{row.name}</p><p className="text-[10px] font-bold text-zinc-400">{row.department || "—"} · {row.jobTitle || "—"}</p></td>
                          <td className="py-3 text-right font-black">{row.coveragePercent == null ? "—" : `${row.coveragePercent}%`}</td>
                          <td className="py-3 text-right">{row.requiredSkills}</td>
                          <td className="py-3 text-right font-black text-amber-600">{row.gapSkills}</td>
                          <td className="py-3 text-right font-black text-red-600">{row.criticalGaps}</td>
                          <td className="py-3 text-right">{row.unassessedRequired}</td>
                          <td className="py-3 text-right">{row.activeDevelopmentPlans}</td>
                          <td className="py-3 pl-2 text-right"><div className="flex justify-end gap-1">{canManage ? <button type="button" onClick={() => openAssessment(row.employeeId)} className="rounded-lg border px-2 py-1 text-[10px] font-black">Assess</button> : null}<button type="button" onClick={() => onOpenEmployee?.(row.employeeId)} className="rounded-lg border border-amber-200 px-2 py-1 text-[10px] font-black text-amber-700">Open</button></div></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="grid gap-2 md:hidden">
                  {(matrix?.rows || []).map((row) => (
                    <button key={row.employeeId} type="button" onClick={() => onOpenEmployee?.(row.employeeId)} className="rounded-2xl border border-zinc-100 p-3 text-left dark:border-white/10">
                      <div className="flex items-center justify-between"><div><p className="text-xs font-black">{row.name}</p><p className="text-[10px] text-zinc-400">{row.department || "—"}</p></div><p className="text-lg font-black">{row.coveragePercent == null ? "—" : `${row.coveragePercent}%`}</p></div>
                      <div className="mt-2 grid grid-cols-3 gap-2 text-center text-[10px]"><div><p className="text-zinc-400">Gaps</p><p className="font-black">{row.gapSkills}</p></div><div><p className="text-zinc-400">Critical</p><p className="font-black text-red-600">{row.criticalGaps}</p></div><div><p className="text-zinc-400">Plans</p><p className="font-black">{row.activeDevelopmentPlans}</p></div></div>
                    </button>
                  ))}
                </div>
              </section>

              <section>
                <div className="mb-3 flex items-center justify-between"><h3 className="text-sm font-black text-zinc-950 dark:text-white">Priority Skill Gaps</h3><AlertCircle size={16} className="text-amber-500" /></div>
                <div className="max-h-[410px] space-y-2 overflow-y-auto pr-1">
                  {priorityGaps.length ? priorityGaps.slice(0, 12).map((gap) => (
                    <div key={`${gap.employeeId}:${gap.skillId}`} className="rounded-2xl border border-zinc-100 p-3 dark:border-white/10">
                      <div className="flex items-start justify-between gap-2"><div className="min-w-0"><p className="truncate text-xs font-black text-zinc-950 dark:text-white">{gap.name}</p><p className="mt-0.5 text-[10px] font-bold text-zinc-400">{gap.employeeName} · {gap.department || "—"}</p></div><Badge tone={statusTone(gap.status)}>{human(gap.status)}</Badge></div>
                      <div className="mt-2 flex items-center justify-between gap-3"><SkillLevelDots currentLevel={gap.currentLevel} targetLevel={gap.targetLevel} /><span className="text-[10px] font-black text-zinc-500">{gap.currentLevel ?? "—"} → {gap.targetLevel}</span></div>
                      <p className="mt-2 text-[10px] font-bold text-zinc-400">{gap.importance} · source {human(gap.requirementSource)}</p>
                      {canManage ? <div className="mt-2 flex gap-2"><button type="button" onClick={() => openAssessment(gap.employeeId, gap.skillId)} className="rounded-lg border px-2 py-1 text-[10px] font-black">Assess</button><button type="button" onClick={() => openPlan(gap.employeeId, gap.skillId)} className="rounded-lg border border-amber-200 px-2 py-1 text-[10px] font-black text-amber-700">Plan</button></div> : null}
                    </div>
                  )) : <p className="rounded-2xl border border-dashed p-5 text-center text-xs font-bold text-zinc-400">No configured skill gaps in this scope.</p>}
                </div>
              </section>
            </div>

            <section className="border-t border-zinc-100 p-4 dark:border-white/10">
              <div className="mb-3 flex items-center justify-between"><div><h3 className="text-sm font-black text-zinc-950 dark:text-white">Development Plans</h3><p className="mt-1 text-[10px] font-bold text-zinc-400">Turn skill gaps and review findings into trackable employee development work.</p></div><Badge>{activePlans.length} open</Badge></div>
              {!plans.length ? <p className="rounded-2xl border border-dashed p-5 text-center text-xs font-bold text-zinc-400">No development plans yet.</p> : <div className="grid gap-3 lg:grid-cols-2">{plans.slice(0, 12).map((plan) => (
                <div key={plan.id} className="rounded-2xl border border-zinc-100 p-3 dark:border-white/10">
                  <div className="flex items-start justify-between gap-2"><div><p className="text-xs font-black text-zinc-950 dark:text-white">{plan.title}</p><p className="mt-1 text-[10px] font-bold text-zinc-400">{plan.employee?.name || "Employee"}{plan.skill?.name ? ` · ${plan.skill.name}` : ""}</p></div><Badge tone={statusTone(plan.status)}>{human(plan.status)}</Badge></div>
                  {plan.objective ? <p className="mt-2 text-[11px] leading-5 text-zinc-500">{plan.objective}</p> : null}
                  <div className="mt-3 grid grid-cols-3 gap-2 text-center text-[10px]"><div><p className="text-zinc-400">Progress</p><p className="font-black">{plan.progressPercent || 0}%</p></div><div><p className="text-zinc-400">Target</p><p className="font-black">{plan.targetLevel ? levelLabel(plan.targetLevel) : "—"}</p></div><div><p className="text-zinc-400">Due</p><p className="font-black">{dateLabel(plan.targetDate)}</p></div></div>
                  <div className="mt-3 space-y-1.5">{(plan.actions || []).slice(0, 4).map((action) => <div key={action.id} className="flex items-center justify-between gap-2 rounded-xl bg-zinc-50 px-2.5 py-2 dark:bg-white/[0.03]"><div className="min-w-0"><p className="truncate text-[10px] font-black">{action.title}</p><p className="text-[9px] text-zinc-400">{dateLabel(action.dueDate)}</p></div><div className="flex items-center gap-1"><Badge tone={statusTone(action.status)}>{human(action.status)}</Badge>{action.status !== "COMPLETED" && action.status !== "CANCELLED" ? <button type="button" onClick={() => updateActionStatus(plan.id, action.id, action.status === "TODO" ? "IN_PROGRESS" : "COMPLETED")} className="rounded-lg border px-2 py-1 text-[9px] font-black">Next</button> : null}</div></div>)}</div>
                  {canManage && !["COMPLETED", "CANCELLED"].includes(plan.status) ? <div className="mt-3 flex flex-wrap gap-2"><button type="button" onClick={() => openAction(plan.id)} className="rounded-lg border px-2 py-1 text-[10px] font-black">+ Action</button>{plan.status === "DRAFT" ? <button type="button" disabled={planSaving} onClick={() => planAction(plan.id, "activate")} className="rounded-lg border border-emerald-200 px-2 py-1 text-[10px] font-black text-emerald-700">Activate</button> : null}{plan.status === "ACTIVE" ? <button type="button" disabled={planSaving} onClick={() => planAction(plan.id, "complete")} className="rounded-lg border border-emerald-200 px-2 py-1 text-[10px] font-black text-emerald-700">Complete</button> : null}<button type="button" disabled={planSaving} onClick={() => planAction(plan.id, "cancel")} className="rounded-lg border border-red-200 px-2 py-1 text-[10px] font-black text-red-600">Cancel</button></div> : null}
                </div>
              ))}</div>}
            </section>
          </>
        )}
      </Card>

      {assessmentOpen ? <div className="fixed inset-0 z-[70] grid place-items-center bg-black/55 p-3"><form onSubmit={saveAssessment} className="w-full max-w-lg rounded-3xl bg-white shadow-2xl dark:bg-zinc-950"><div className="flex items-center justify-between border-b p-4 dark:border-white/10"><div><p className="text-[10px] font-black uppercase text-amber-500">Official Assessment</p><h3 className="text-lg font-black">Assess Employee Skill</h3></div><button type="button" onClick={() => setAssessmentOpen(false)} className="p-2 text-zinc-400"><X size={20} /></button></div><div className="space-y-3 p-4"><select required value={assessmentForm.employeeId} onChange={(e) => setAssessmentForm((c) => ({ ...c, employeeId: e.target.value }))} className="w-full rounded-xl border p-2 dark:bg-zinc-900">{employees.map((employee) => <option key={employee.id} value={employee.id}>{employee.name}</option>)}</select><select required value={assessmentForm.skillId} onChange={(e) => setAssessmentForm((c) => ({ ...c, skillId: e.target.value }))} className="w-full rounded-xl border p-2 dark:bg-zinc-900">{catalog.filter((skill) => skill.isActive !== false).map((skill) => <option key={skill.id} value={skill.id}>{skill.category} · {skill.name}</option>)}</select><label className="text-xs font-black text-zinc-500">Current proficiency<select value={assessmentForm.currentLevel} onChange={(e) => setAssessmentForm((c) => ({ ...c, currentLevel: e.target.value }))} className="mt-1 w-full rounded-xl border p-2 dark:bg-zinc-900">{[1,2,3,4,5].map((level) => <option key={level} value={level}>{levelLabel(level)}</option>)}</select></label><textarea value={assessmentForm.evidence} onChange={(e) => setAssessmentForm((c) => ({ ...c, evidence: e.target.value }))} placeholder="Evidence / manager note" className="min-h-28 w-full rounded-xl border p-3 text-sm dark:bg-zinc-900" /><button type="submit" disabled={assessmentSaving || !assessmentForm.skillId} className="w-full rounded-xl bg-gradient-to-l from-amber-500 to-yellow-300 p-3 text-xs font-black text-zinc-950 disabled:opacity-50">{assessmentSaving ? "Saving…" : "Save Assessment"}</button></div></form></div> : null}

      {planOpen ? <div className="fixed inset-0 z-[70] grid place-items-center bg-black/55 p-3"><form onSubmit={savePlan} className="max-h-[92vh] w-full max-w-xl overflow-y-auto rounded-3xl bg-white shadow-2xl dark:bg-zinc-950"><div className="flex items-center justify-between border-b p-4 dark:border-white/10"><div><p className="text-[10px] font-black uppercase text-amber-500">Development</p><h3 className="text-lg font-black">Create Development Plan</h3></div><button type="button" onClick={() => setPlanOpen(false)} className="p-2 text-zinc-400"><X size={20} /></button></div><div className="space-y-3 p-4"><select required value={planForm.employeeId} onChange={(e) => setPlanForm((c) => ({ ...c, employeeId: e.target.value }))} className="w-full rounded-xl border p-2 dark:bg-zinc-900">{employees.map((employee) => <option key={employee.id} value={employee.id}>{employee.name}</option>)}</select><select value={planForm.skillId} onChange={(e) => setPlanForm((c) => ({ ...c, skillId: e.target.value }))} className="w-full rounded-xl border p-2 dark:bg-zinc-900"><option value="">General development</option>{catalog.filter((skill) => skill.isActive !== false).map((skill) => <option key={skill.id} value={skill.id}>{skill.category} · {skill.name}</option>)}</select><input required value={planForm.title} onChange={(e) => setPlanForm((c) => ({ ...c, title: e.target.value }))} placeholder="Plan title" className="w-full rounded-xl border p-2 dark:bg-zinc-900" /><textarea value={planForm.objective} onChange={(e) => setPlanForm((c) => ({ ...c, objective: e.target.value }))} placeholder="Development objective" className="min-h-28 w-full rounded-xl border p-3 text-sm dark:bg-zinc-900" /><div className="grid gap-2 sm:grid-cols-2"><select value={planForm.targetLevel} onChange={(e) => setPlanForm((c) => ({ ...c, targetLevel: e.target.value }))} className="rounded-xl border p-2 dark:bg-zinc-900"><option value="">Target from requirement</option>{[1,2,3,4,5].map((level) => <option key={level} value={level}>{levelLabel(level)}</option>)}</select><input type="date" value={planForm.targetDate} onChange={(e) => setPlanForm((c) => ({ ...c, targetDate: e.target.value }))} className="rounded-xl border p-2 dark:bg-zinc-900" /></div><button type="submit" disabled={planSaving} className="w-full rounded-xl bg-gradient-to-l from-amber-500 to-yellow-300 p-3 text-xs font-black text-zinc-950 disabled:opacity-50">{planSaving ? "Saving…" : "Create Draft Plan"}</button></div></form></div> : null}

      {actionOpen ? <div className="fixed inset-0 z-[75] grid place-items-center bg-black/55 p-3"><form onSubmit={saveAction} className="w-full max-w-lg rounded-3xl bg-white shadow-2xl dark:bg-zinc-950"><div className="flex items-center justify-between border-b p-4 dark:border-white/10"><h3 className="text-lg font-black">Add Development Action</h3><button type="button" onClick={() => setActionOpen(false)} className="p-2 text-zinc-400"><X size={20} /></button></div><div className="space-y-3 p-4"><input required value={actionForm.title} onChange={(e) => setActionForm((c) => ({ ...c, title: e.target.value }))} placeholder="Action title" className="w-full rounded-xl border p-2 dark:bg-zinc-900" /><textarea value={actionForm.description} onChange={(e) => setActionForm((c) => ({ ...c, description: e.target.value }))} placeholder="Action details" className="min-h-24 w-full rounded-xl border p-3 dark:bg-zinc-900" /><input type="date" value={actionForm.dueDate} onChange={(e) => setActionForm((c) => ({ ...c, dueDate: e.target.value }))} className="w-full rounded-xl border p-2 dark:bg-zinc-900" /><button type="submit" disabled={actionSaving} className="w-full rounded-xl bg-zinc-950 p-3 text-xs font-black text-white dark:bg-white dark:text-zinc-950">{actionSaving ? "Saving…" : "Add Action"}</button></div></form></div> : null}

      {frameworkOpen ? <div className="fixed inset-0 z-[80] grid place-items-center bg-black/55 p-3"><div className="max-h-[94vh] w-full max-w-6xl overflow-y-auto rounded-3xl bg-white shadow-2xl dark:bg-zinc-950"><div className="sticky top-0 z-10 flex items-center justify-between border-b bg-white p-4 dark:border-white/10 dark:bg-zinc-950"><div><p className="text-[10px] font-black uppercase text-amber-500">Admin Framework</p><h3 className="text-lg font-black">Skills & Competency Framework</h3></div><button type="button" onClick={() => setFrameworkOpen(false)} className="p-2 text-zinc-400"><X size={20} /></button></div>{frameworkLoading ? <div className="h-40 animate-pulse bg-zinc-50 dark:bg-white/[0.03]" /> : <div className="grid gap-5 p-4 lg:grid-cols-2"><section><h4 className="mb-3 text-sm font-black">Skill Catalog</h4><form onSubmit={createSkill} className="space-y-2 rounded-2xl border p-3 dark:border-white/10"><div className="grid gap-2 sm:grid-cols-2"><input required value={skillForm.name} onChange={(e) => setSkillForm((c) => ({ ...c, name: e.target.value }))} placeholder="Skill name" className="rounded-xl border p-2 dark:bg-zinc-900" /><input value={skillForm.category} onChange={(e) => setSkillForm((c) => ({ ...c, category: e.target.value }))} placeholder="Category" className="rounded-xl border p-2 dark:bg-zinc-900" /></div><textarea value={skillForm.description} onChange={(e) => setSkillForm((c) => ({ ...c, description: e.target.value }))} placeholder="Description" className="min-h-20 w-full rounded-xl border p-2 dark:bg-zinc-900" /><button type="submit" disabled={frameworkSaving} className="rounded-xl bg-zinc-950 px-3 py-2 text-xs font-black text-white dark:bg-white dark:text-zinc-950">Add Skill</button></form><div className="mt-3 max-h-[430px] space-y-2 overflow-y-auto">{catalog.map((skill) => <div key={skill.id} className={`flex items-center justify-between gap-2 rounded-xl border p-2.5 dark:border-white/10 ${skill.isActive ? "" : "opacity-50"}`}><div><p className="text-xs font-black">{skill.name}</p><p className="text-[10px] text-zinc-400">{skill.category}</p></div>{skill.isActive ? <button type="button" onClick={() => deactivateSkill(skill.id)} className="rounded-lg border border-red-200 px-2 py-1 text-[10px] font-black text-red-600">Deactivate</button> : <Badge>Inactive</Badge>}</div>)}</div></section><section><h4 className="mb-3 text-sm font-black">Competency Requirements</h4><form onSubmit={createRequirement} className="space-y-2 rounded-2xl border p-3 dark:border-white/10"><select required value={requirementForm.skillId} onChange={(e) => setRequirementForm((c) => ({ ...c, skillId: e.target.value }))} className="w-full rounded-xl border p-2 dark:bg-zinc-900">{catalog.filter((skill) => skill.isActive).map((skill) => <option key={skill.id} value={skill.id}>{skill.category} · {skill.name}</option>)}</select><div className="grid gap-2 sm:grid-cols-2"><select value={requirementForm.scopeType} onChange={(e) => setRequirementForm((c) => ({ ...c, scopeType: e.target.value }))} className="rounded-xl border p-2 dark:bg-zinc-900"><option value="DEPARTMENT">Department</option><option value="JOB_TITLE">Job Title</option><option value="EMPLOYEE">Employee override</option></select>{requirementForm.scopeType === "DEPARTMENT" ? <select value={requirementForm.department} onChange={(e) => setRequirementForm((c) => ({ ...c, department: e.target.value }))} className="rounded-xl border p-2 dark:bg-zinc-900">{departments.map((department) => <option key={department}>{department}</option>)}</select> : requirementForm.scopeType === "JOB_TITLE" ? <select value={requirementForm.jobTitle} onChange={(e) => setRequirementForm((c) => ({ ...c, jobTitle: e.target.value }))} className="rounded-xl border p-2 dark:bg-zinc-900">{jobTitles.map((title) => <option key={title}>{title}</option>)}</select> : <select value={requirementForm.employeeId} onChange={(e) => setRequirementForm((c) => ({ ...c, employeeId: e.target.value }))} className="rounded-xl border p-2 dark:bg-zinc-900">{employees.map((employee) => <option key={employee.id} value={employee.id}>{employee.name}</option>)}</select>}</div><div className="grid gap-2 sm:grid-cols-2"><select value={requirementForm.targetLevel} onChange={(e) => setRequirementForm((c) => ({ ...c, targetLevel: e.target.value }))} className="rounded-xl border p-2 dark:bg-zinc-900">{[1,2,3,4,5].map((level) => <option key={level} value={level}>{levelLabel(level)}</option>)}</select><select value={requirementForm.importance} onChange={(e) => setRequirementForm((c) => ({ ...c, importance: e.target.value }))} className="rounded-xl border p-2 dark:bg-zinc-900"><option>CORE</option><option>IMPORTANT</option><option>OPTIONAL</option></select></div><button type="submit" disabled={frameworkSaving || !requirementForm.skillId} className="rounded-xl bg-gradient-to-l from-amber-500 to-yellow-300 px-3 py-2 text-xs font-black text-zinc-950">Add Requirement</button></form><div className="mt-3 max-h-[430px] space-y-2 overflow-y-auto">{requirements.map((requirement) => <div key={requirement.id} className={`rounded-xl border p-2.5 dark:border-white/10 ${requirement.isActive ? "" : "opacity-50"}`}><div className="flex items-start justify-between gap-2"><div><p className="text-xs font-black">{requirement.skill?.name || "Skill"}</p><p className="text-[10px] text-zinc-400">{human(requirement.scopeType)} · {requirement.department || requirement.jobTitle || employees.find((employee) => employee.id === requirement.employeeId)?.name || requirement.employeeId || "—"}</p><p className="mt-1 text-[10px] font-black">Target {requirement.targetLevel} · {requirement.importance}</p></div>{requirement.isActive ? <button type="button" onClick={() => deactivateRequirement(requirement.id)} className="rounded-lg border border-red-200 px-2 py-1 text-[10px] font-black text-red-600">Deactivate</button> : <Badge>Inactive</Badge>}</div></div>)}</div></section></div>}</div></div> : null}
    </>
  );
}

export function EmployeeSkillsDevelopment({ user, employee, refreshToken = "" }) {
  const [matrix, setMatrix] = useState(null);
  const [plans, setPlans] = useState([]);
  const [error, setError] = useState("");
  const [localRefresh, setLocalRefresh] = useState(0);

  useEffect(() => {
    if (!employee?.id) return;
    let ignore = false;
    async function load() {
      setError("");
      try {
        const [matrixResult, planResult] = await Promise.all([
          api.tasks.skillsMatrix({ employeeId: employee.id }),
          api.tasks.developmentPlans({ employeeId: employee.id }),
        ]);
        if (!ignore) {
          setMatrix(matrixResult);
          setPlans(planResult?.plans || []);
        }
      } catch (err) {
        if (!ignore) setError(getErrorMessage(err, "Unable to load employee skills."));
      }
    }
    load();
    return () => { ignore = true; };
  }, [employee?.id, refreshToken, localRefresh]);

  const row = matrix?.rows?.[0] || null;

  async function updateAction(planId, actionId, status) {
    try {
      await api.tasks.updateDevelopmentAction(planId, actionId, { status });
      setLocalRefresh((value) => value + 1);
    } catch (err) {
      setError(getErrorMessage(err, "Unable to update development action."));
    }
  }

  return (
    <section className="mt-4 rounded-2xl border border-violet-100 bg-violet-50/20 p-4 dark:border-violet-400/15 dark:bg-violet-400/[0.025]">
      <div className="flex items-start justify-between gap-3"><div><p className="text-[10px] font-black uppercase tracking-[0.08em] text-violet-500">Skills & Development</p><h3 className="mt-1 text-sm font-black text-zinc-950 dark:text-white">Competencies & Growth Plan</h3></div>{row?.coveragePercent != null ? <div className="text-right"><p className="text-2xl font-black text-violet-600 dark:text-violet-300">{row.coveragePercent}%</p><p className="text-[9px] font-black text-zinc-400">skill coverage</p></div> : null}</div>
      {error ? <div className="mt-3"><Notice type="error">{error}</Notice></div> : null}
      {!row ? <p className="mt-3 text-xs font-bold text-zinc-400">No skills framework data configured for this employee yet.</p> : <><div className="mt-3 grid grid-cols-3 gap-2 text-center text-[10px]"><div className="rounded-xl bg-white p-2 dark:bg-white/5"><p className="text-zinc-400">Required</p><p className="font-black">{row.requiredSkills}</p></div><div className="rounded-xl bg-white p-2 dark:bg-white/5"><p className="text-zinc-400">Gaps</p><p className="font-black text-amber-600">{row.gapSkills}</p></div><div className="rounded-xl bg-white p-2 dark:bg-white/5"><p className="text-zinc-400">Critical</p><p className="font-black text-red-600">{row.criticalGaps}</p></div></div><div className="mt-3 space-y-2">{row.skills.slice(0, 10).map((skill) => <div key={skill.skillId} className="rounded-xl border border-zinc-100 bg-white p-2.5 dark:border-white/10 dark:bg-white/[0.03]"><div className="flex items-center justify-between gap-2"><div><p className="text-[11px] font-black">{skill.name}</p><p className="text-[9px] text-zinc-400">{skill.category}{skill.requirementSource ? ` · ${human(skill.requirementSource)} requirement` : ""}</p></div><Badge tone={statusTone(skill.status)}>{human(skill.status)}</Badge></div><div className="mt-2 flex items-center justify-between"><SkillLevelDots currentLevel={skill.currentLevel} targetLevel={skill.targetLevel} /><span className="text-[9px] font-black text-zinc-400">{levelLabel(skill.currentLevel)}{skill.targetLevel ? ` → ${skill.targetLevel}` : ""}</span></div></div>)}</div></>}
      {plans.length ? <div className="mt-4 border-t border-violet-100 pt-3 dark:border-violet-400/15"><div className="mb-2 flex items-center justify-between"><p className="text-xs font-black">Development Plans</p><Badge>{plans.length}</Badge></div><div className="space-y-2">{plans.slice(0, 5).map((plan) => <div key={plan.id} className="rounded-xl border border-zinc-100 bg-white p-2.5 dark:border-white/10 dark:bg-white/[0.03]"><div className="flex items-start justify-between gap-2"><div><p className="text-[11px] font-black">{plan.title}</p><p className="text-[9px] text-zinc-400">{plan.skill?.name || "General development"} · {plan.progressPercent || 0}%</p></div><Badge tone={statusTone(plan.status)}>{human(plan.status)}</Badge></div><div className="mt-2 space-y-1">{(plan.actions || []).filter((action) => action.status !== "CANCELLED").slice(0, 4).map((action) => <div key={action.id} className="flex items-center justify-between gap-2 rounded-lg bg-zinc-50 px-2 py-1.5 dark:bg-white/[0.03]"><div className="min-w-0"><p className="truncate text-[9px] font-black">{action.title}</p><p className="text-[8px] text-zinc-400">{dateLabel(action.dueDate)}</p></div><div className="flex items-center gap-1"><Badge tone={statusTone(action.status)}>{human(action.status)}</Badge>{action.status !== "COMPLETED" ? <button type="button" onClick={() => updateAction(plan.id, action.id, action.status === "TODO" ? "IN_PROGRESS" : "COMPLETED")} className="rounded border px-1.5 py-0.5 text-[8px] font-black">Next</button> : null}</div></div>)}</div></div>)}</div></div> : null}
    </section>
  );
}
'''

path.write_text(content)
print("FRONTEND_SKILLS_COMPONENT=PASS")
