#!/usr/bin/env python3
from pathlib import Path
import sys

repo = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
path = repo / "frontend/src/components/performance/TalentSuccession.jsx"
if path.exists():
    print("FRONTEND_TALENT_COMPONENT=PASS already-present")
    raise SystemExit(0)

path.parent.mkdir(parents=True, exist_ok=True)
content = r'''import { useEffect, useMemo, useState } from "react";
import {
  Award,
  BriefcaseBusiness,
  CheckCircle2,
  Crown,
  RefreshCw,
  ShieldCheck,
  Sparkles,
  Target,
  UserRound,
  UsersRound,
  X,
} from "lucide-react";
import { Badge, Card, Notice } from "../ui/Primitives";
import { api } from "../../lib/api";
import { getErrorMessage } from "../../lib/errors";

const MANAGER_ROLES = new Set(["SUPER_ADMIN", "ADMIN", "MANAGER", "PROJECT_MANAGER"]);
const ADMIN_ROLES = new Set(["SUPER_ADMIN", "ADMIN"]);
const POTENTIAL_LEVELS = ["LOW", "MEDIUM", "HIGH"];
const READINESS = ["DEVELOPING", "READY_3_PLUS_YEARS", "READY_1_2_YEARS", "READY_NOW"];
const CRITICALITY = ["NORMAL", "HIGH", "CRITICAL"];

function human(value) {
  return String(value || "—").replaceAll("_", " ").toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase());
}

function badgeTone(value) {
  if (["HIGH", "READY_NOW", "CRITICAL"].includes(value)) return "success";
  if (["MEDIUM", "READY_1_2_YEARS", "HIGH"].includes(value)) return "warning";
  if (["LOW"].includes(value)) return "danger";
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

function NineBox({ cells = [], onOpenEmployee }) {
  const byKey = useMemo(() => new Map(cells.map((cell) => [cell.key, cell])), [cells]);
  const potentials = ["HIGH", "MEDIUM", "LOW"];
  const performances = ["LOW", "MEDIUM", "HIGH"];
  return (
    <div>
      <div className="mb-2 grid grid-cols-[90px_repeat(3,minmax(0,1fr))] gap-2 text-center text-[10px] font-black uppercase tracking-[0.06em] text-zinc-400">
        <div />
        {performances.map((performance) => <div key={performance}>{human(performance)} Performance</div>)}
      </div>
      <div className="space-y-2">
        {potentials.map((potential) => (
          <div key={potential} className="grid grid-cols-[90px_repeat(3,minmax(0,1fr))] gap-2">
            <div className="flex items-center text-[10px] font-black uppercase tracking-[0.06em] text-zinc-400">{human(potential)} Potential</div>
            {performances.map((performance) => {
              const cell = byKey.get(`${potential}_${performance}`) || { employees: [], label: "—", employeeCount: 0 };
              return (
                <div key={`${potential}_${performance}`} className="min-h-28 rounded-2xl border border-zinc-100 bg-white p-3 dark:border-white/10 dark:bg-white/[0.025]">
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-[11px] font-black text-zinc-950 dark:text-white">{cell.label}</p>
                    <Badge>{cell.employeeCount || 0}</Badge>
                  </div>
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {(cell.employees || []).slice(0, 6).map((employee) => (
                      <button key={employee.employeeId} type="button" onClick={() => onOpenEmployee?.(employee.employeeId)} className="rounded-full border border-zinc-200 px-2 py-1 text-[10px] font-black text-zinc-600 hover:border-amber-300 dark:border-white/10 dark:text-zinc-300">
                        {employee.name}
                      </button>
                    ))}
                    {(cell.employees || []).length > 6 ? <span className="text-[10px] font-black text-zinc-400">+{cell.employees.length - 6}</span> : null}
                  </div>
                </div>
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
}

export function TalentSuccessionPanel({
  user,
  employees = [],
  selectedRange,
  employeeFilter = "all",
  departmentFilter = "all",
  refreshToken = "",
  onOpenEmployee = null,
}) {
  const role = String(user?.role || "").toUpperCase();
  const canManage = MANAGER_ROLES.has(role);
  const canConfigureRoles = ADMIN_ROLES.has(role);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [toast, setToast] = useState(null);
  const [localRefresh, setLocalRefresh] = useState(0);

  const [assessmentOpen, setAssessmentOpen] = useState(false);
  const [assessmentSaving, setAssessmentSaving] = useState(false);
  const [assessmentForm, setAssessmentForm] = useState({ employeeId: "", potentialLevel: "MEDIUM", evidence: "", managerNote: "" });

  const [successionOpen, setSuccessionOpen] = useState(false);
  const [successionLoading, setSuccessionLoading] = useState(false);
  const [successionSaving, setSuccessionSaving] = useState(false);
  const [roles, setRoles] = useState([]);
  const [roleForm, setRoleForm] = useState({ title: "", department: "", criticality: "HIGH", incumbentEmployeeId: "", description: "" });
  const [candidateForm, setCandidateForm] = useState({ roleId: "", employeeId: "", readiness: "DEVELOPING", priority: "3", rationale: "" });

  const departments = useMemo(() => [...new Set(employees.map((employee) => employee.department).filter(Boolean))].sort(), [employees]);

  async function loadOverview() {
    if (!canManage || !selectedRange?.start || !selectedRange?.end || selectedRange?.invalid) return;
    setLoading(true);
    setError("");
    try {
      const result = await api.tasks.talentOverview({
        start: selectedRange.start.toISOString(),
        end: selectedRange.end.toISOString(),
        employeeId: employeeFilter !== "all" ? employeeFilter : "",
        department: departmentFilter !== "all" ? departmentFilter : "",
      });
      setData(result);
    } catch (err) {
      setData(null);
      setError(getErrorMessage(err, "Unable to load talent and succession planning."));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadOverview();
  }, [canManage, selectedRange?.start?.getTime(), selectedRange?.end?.getTime(), selectedRange?.invalid, employeeFilter, departmentFilter, refreshToken, localRefresh]);

  if (!canManage) return null;

  function openAssessment(employeeId = "") {
    const resolvedId = employeeId || (employeeFilter !== "all" ? employeeFilter : data?.rows?.[0]?.employeeId || employees[0]?.id || "");
    const row = data?.rows?.find((item) => item.employeeId === resolvedId);
    setAssessmentForm({
      employeeId: resolvedId,
      potentialLevel: row?.potentialLevel || "MEDIUM",
      evidence: row?.potentialEvidence || "",
      managerNote: row?.potentialManagerNote || "",
    });
    setAssessmentOpen(true);
  }

  async function saveAssessment(event) {
    event.preventDefault();
    setAssessmentSaving(true);
    try {
      await api.tasks.assessTalentPotential({
        employeeId: assessmentForm.employeeId,
        potentialLevel: assessmentForm.potentialLevel,
        evidence: assessmentForm.evidence || null,
        managerNote: assessmentForm.managerNote || null,
      });
      setAssessmentOpen(false);
      setToast({ type: "success", message: "Talent potential assessment saved." });
      setLocalRefresh((value) => value + 1);
    } catch (err) {
      setToast({ type: "error", message: getErrorMessage(err, "Unable to save talent assessment.") });
    } finally {
      setAssessmentSaving(false);
    }
  }

  async function loadSuccessionRoles() {
    setSuccessionLoading(true);
    try {
      const result = await api.tasks.successionRoles({ includeInactive: canConfigureRoles ? "true" : "" });
      const nextRoles = result?.roles || [];
      setRoles(nextRoles);
      setCandidateForm((current) => ({ ...current, roleId: current.roleId || nextRoles.find((item) => item.isActive)?.id || "", employeeId: current.employeeId || data?.rows?.[0]?.employeeId || employees[0]?.id || "" }));
    } catch (err) {
      setToast({ type: "error", message: getErrorMessage(err, "Unable to load succession roles.") });
    } finally {
      setSuccessionLoading(false);
    }
  }

  async function openSuccession() {
    setSuccessionOpen(true);
    await loadSuccessionRoles();
  }

  async function createRole(event) {
    event.preventDefault();
    setSuccessionSaving(true);
    try {
      await api.tasks.createSuccessionRole({
        title: roleForm.title,
        department: roleForm.department || null,
        criticality: roleForm.criticality,
        incumbentEmployeeId: roleForm.incumbentEmployeeId || null,
        description: roleForm.description || null,
      });
      setRoleForm({ title: "", department: "", criticality: "HIGH", incumbentEmployeeId: "", description: "" });
      await loadSuccessionRoles();
      setLocalRefresh((value) => value + 1);
    } catch (err) {
      setToast({ type: "error", message: getErrorMessage(err, "Unable to create succession role.") });
    } finally {
      setSuccessionSaving(false);
    }
  }

  async function nominateCandidate(event) {
    event.preventDefault();
    setSuccessionSaving(true);
    try {
      await api.tasks.nominateSuccessionCandidate(candidateForm.roleId, {
        employeeId: candidateForm.employeeId,
        readiness: candidateForm.readiness,
        priority: Number(candidateForm.priority),
        rationale: candidateForm.rationale || null,
      });
      setCandidateForm((current) => ({ ...current, rationale: "" }));
      await loadSuccessionRoles();
      setLocalRefresh((value) => value + 1);
    } catch (err) {
      setToast({ type: "error", message: getErrorMessage(err, "Unable to nominate succession candidate.") });
    } finally {
      setSuccessionSaving(false);
    }
  }

  async function deactivateRole(roleId) {
    setSuccessionSaving(true);
    try {
      await api.tasks.deactivateSuccessionRole(roleId);
      await loadSuccessionRoles();
      setLocalRefresh((value) => value + 1);
    } catch (err) {
      setToast({ type: "error", message: getErrorMessage(err, "Unable to deactivate succession role.") });
    } finally {
      setSuccessionSaving(false);
    }
  }

  async function deactivateCandidate(roleId, candidateId) {
    setSuccessionSaving(true);
    try {
      await api.tasks.deactivateSuccessionCandidate(roleId, candidateId);
      await loadSuccessionRoles();
      setLocalRefresh((value) => value + 1);
    } catch (err) {
      setToast({ type: "error", message: getErrorMessage(err, "Unable to remove succession candidate.") });
    } finally {
      setSuccessionSaving(false);
    }
  }

  const summary = data?.summary || {};

  return (
    <>
      <Card className="overflow-hidden p-0">
        <div className="flex flex-col gap-3 border-b border-zinc-100 p-4 dark:border-white/10 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <p className="text-[11px] font-black uppercase tracking-[0.1em] text-amber-500">Talent Matrix & Succession Planning</p>
              <Badge tone="blue">Phase 10</Badge>
              <Badge tone="neutral">Manager-only</Badge>
            </div>
            <h2 className="mt-1 text-base font-black text-zinc-950 dark:text-white">9-Box Talent & Succession Bench</h2>
            <p className="mt-1 max-w-3xl text-[11px] font-bold leading-5 text-zinc-400">Performance uses the existing Phase 3 score. Potential and succession readiness are explicit manager assessments. This is decision-support only — no automatic promotion, demotion or employment decision.</p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <button type="button" onClick={() => setLocalRefresh((value) => value + 1)} className="rounded-xl border border-zinc-200 p-2 text-zinc-500 dark:border-white/10" aria-label="Refresh talent data"><RefreshCw size={16} className={loading ? "animate-spin" : ""} /></button>
            <button type="button" onClick={() => openAssessment()} className="inline-flex items-center gap-2 rounded-xl border border-zinc-200 px-3 py-2 text-xs font-black text-zinc-700 hover:border-amber-300 dark:border-white/10 dark:text-zinc-200"><Sparkles size={15} /> Assess Potential</button>
            <button type="button" onClick={openSuccession} className="inline-flex items-center gap-2 rounded-xl bg-zinc-950 px-3 py-2 text-xs font-black text-white dark:bg-white dark:text-zinc-950"><Crown size={15} /> Succession Bench</button>
          </div>
        </div>

        {error ? <div className="p-4"><Notice type="error">{error}</Notice></div> : null}
        {toast ? <div className="px-4 pt-4"><Notice type={toast.type === "success" ? "success" : "error"}>{toast.message}</Notice></div> : null}

        {loading && !data ? <div className="h-52 animate-pulse bg-zinc-50 dark:bg-white/[0.025]" /> : (
          <>
            <div className="grid gap-3 p-4 sm:grid-cols-2 xl:grid-cols-6">
              <MiniMetric label="Potential Assessed" value={`${summary.assessedEmployees || 0}/${summary.employeeCount || 0}`} note={`${summary.unassessedPotential || 0} awaiting assessment`} />
              <MiniMetric label="9-Box Classified" value={summary.classifiedEmployees || 0} note="Requires score + potential" />
              <MiniMetric label="High Potential" value={summary.highPotentialEmployees || 0} note="Manager assessed" />
              <MiniMetric label="Critical Roles" value={summary.criticalRoles || 0} note={`${summary.coveredCriticalRoles || 0} with bench`} />
              <MiniMetric label="Succession Gaps" value={summary.uncoveredCriticalRoles || 0} note="Critical/high roles without candidate" />
              <MiniMetric label="Ready Now" value={summary.readyNowCandidates || 0} note="Explicit readiness nominations" />
            </div>

            <div className="border-t border-zinc-100 p-4 dark:border-white/10">
              <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                <div><h3 className="text-sm font-black text-zinc-950 dark:text-white">9-Box Talent Matrix</h3><p className="mt-1 text-[10px] font-bold text-zinc-400">No Activity or missing potential stays unclassified. Potential is never inferred.</p></div>
                <Badge>{summary.classifiedEmployees || 0} classified</Badge>
              </div>
              <div className="overflow-x-auto pb-1"><div className="min-w-[760px]"><NineBox cells={data?.matrix || []} onOpenEmployee={onOpenEmployee} /></div></div>
            </div>

            <div className="border-t border-zinc-100 p-4 dark:border-white/10">
              <div className="mb-3 flex items-center justify-between gap-2"><div><h3 className="text-sm font-black text-zinc-950 dark:text-white">Succession Coverage</h3><p className="mt-1 text-[10px] font-bold text-zinc-400">Readiness is manager-entered, not auto-calculated.</p></div><Badge>{data?.successionRoles?.length || 0} roles</Badge></div>
              {!data?.successionRoles?.length ? <div className="rounded-2xl border border-dashed border-zinc-200 p-6 text-center text-xs font-bold text-zinc-400 dark:border-white/10">No visible succession roles configured yet.</div> : (
                <div className="grid gap-2 lg:grid-cols-2">
                  {(data.successionRoles || []).map((successionRole) => (
                    <div key={successionRole.id} className="rounded-2xl border border-zinc-100 p-3 dark:border-white/10">
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0"><p className="truncate text-xs font-black text-zinc-950 dark:text-white">{successionRole.title}</p><p className="mt-0.5 text-[10px] font-bold text-zinc-400">{successionRole.department || "Company"} · Incumbent: {successionRole.incumbent?.name || "Open"}</p></div>
                        <Badge tone={successionRole.criticality === "CRITICAL" ? "danger" : successionRole.criticality === "HIGH" ? "warning" : "neutral"}>{human(successionRole.criticality)}</Badge>
                      </div>
                      <div className="mt-3 grid grid-cols-3 gap-2 text-center text-[10px]"><div><p className="text-zinc-400">Bench</p><p className="font-black">{successionRole.benchDepth || 0}</p></div><div><p className="text-zinc-400">Ready Now</p><p className="font-black text-emerald-600">{successionRole.readyNowCount || 0}</p></div><div><p className="text-zinc-400">Coverage</p><p className="font-black">{successionRole.covered ? "Covered" : "Gap"}</p></div></div>
                      <div className="mt-3 flex flex-wrap gap-1.5">{(successionRole.candidates || []).slice(0, 5).map((candidate) => <button key={candidate.id} type="button" onClick={() => onOpenEmployee?.(candidate.employeeId)} className="rounded-full border border-zinc-200 px-2 py-1 text-[10px] font-black dark:border-white/10">{candidate.employee?.name || "Candidate"} · {human(candidate.readiness)}</button>)}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </>
        )}
      </Card>

      {assessmentOpen ? (
        <div className="fixed inset-0 z-[70] grid place-items-center bg-black/55 p-3" role="dialog" aria-modal="true">
          <div className="w-full max-w-xl rounded-3xl bg-white shadow-2xl dark:bg-zinc-950">
            <div className="flex items-center justify-between border-b border-zinc-100 p-4 dark:border-white/10"><div><p className="text-[10px] font-black uppercase text-amber-500">Manager Assessment</p><h3 className="text-lg font-black">Potential Assessment</h3></div><button type="button" onClick={() => setAssessmentOpen(false)} className="rounded-xl p-2 text-zinc-400"><X size={20} /></button></div>
            <form onSubmit={saveAssessment} className="space-y-3 p-4">
              <label className="block text-xs font-black text-zinc-500">Employee<select required value={assessmentForm.employeeId} onChange={(event) => setAssessmentForm((current) => ({ ...current, employeeId: event.target.value }))} className="mt-1 w-full rounded-xl border p-2 dark:bg-zinc-900">{(data?.rows || []).map((employee) => <option key={employee.employeeId} value={employee.employeeId}>{employee.name}</option>)}</select></label>
              <label className="block text-xs font-black text-zinc-500">Potential<select value={assessmentForm.potentialLevel} onChange={(event) => setAssessmentForm((current) => ({ ...current, potentialLevel: event.target.value }))} className="mt-1 w-full rounded-xl border p-2 dark:bg-zinc-900">{POTENTIAL_LEVELS.map((value) => <option key={value} value={value}>{human(value)}</option>)}</select></label>
              <label className="block text-xs font-black text-zinc-500">Evidence<textarea rows={3} value={assessmentForm.evidence} onChange={(event) => setAssessmentForm((current) => ({ ...current, evidence: event.target.value }))} className="mt-1 w-full rounded-xl border p-2 dark:bg-zinc-900" placeholder="Observed capability, scope growth, ownership, learning evidence…" /></label>
              <label className="block text-xs font-black text-zinc-500">Manager note<textarea rows={3} value={assessmentForm.managerNote} onChange={(event) => setAssessmentForm((current) => ({ ...current, managerNote: event.target.value }))} className="mt-1 w-full rounded-xl border p-2 dark:bg-zinc-900" /></label>
              <p className="rounded-xl bg-zinc-50 p-3 text-[10px] font-bold text-zinc-500 dark:bg-white/[0.04]">Potential must be based on documented work evidence and manager judgment. Do not use protected or sensitive personal attributes.</p>
              <button type="submit" disabled={assessmentSaving || !assessmentForm.employeeId} className="w-full rounded-xl bg-gradient-to-l from-amber-500 to-yellow-300 px-4 py-3 text-xs font-black text-zinc-950 disabled:opacity-50">{assessmentSaving ? "Saving…" : "Save Potential Assessment"}</button>
            </form>
          </div>
        </div>
      ) : null}

      {successionOpen ? (
        <div className="fixed inset-0 z-[70] grid place-items-center bg-black/55 p-3" role="dialog" aria-modal="true">
          <div className="max-h-[94vh] w-full max-w-6xl overflow-y-auto rounded-3xl bg-white shadow-2xl dark:bg-zinc-950">
            <div className="flex items-center justify-between border-b border-zinc-100 p-4 dark:border-white/10"><div><p className="text-[10px] font-black uppercase text-amber-500">Succession Planning</p><h3 className="text-lg font-black">Roles & Candidate Bench</h3></div><button type="button" onClick={() => setSuccessionOpen(false)} className="rounded-xl p-2 text-zinc-400"><X size={20} /></button></div>
            {successionLoading ? <div className="h-40 animate-pulse bg-zinc-50 dark:bg-white/[0.03]" /> : (
              <div className={`grid gap-4 p-4 ${canConfigureRoles ? "xl:grid-cols-3" : "xl:grid-cols-2"}`}>
                {canConfigureRoles ? <form onSubmit={createRole} className="space-y-3 rounded-2xl border border-zinc-100 p-3 dark:border-white/10"><div className="flex items-center gap-2"><BriefcaseBusiness size={16} /><h4 className="text-sm font-black">Create Succession Role</h4></div><input required value={roleForm.title} onChange={(e) => setRoleForm((c) => ({ ...c, title: e.target.value }))} placeholder="Role title" className="w-full rounded-xl border p-2 text-xs dark:bg-zinc-900" /><select value={roleForm.department} onChange={(e) => setRoleForm((c) => ({ ...c, department: e.target.value }))} className="w-full rounded-xl border p-2 text-xs dark:bg-zinc-900"><option value="">Company / no department</option>{departments.map((department) => <option key={department}>{department}</option>)}</select><select value={roleForm.criticality} onChange={(e) => setRoleForm((c) => ({ ...c, criticality: e.target.value }))} className="w-full rounded-xl border p-2 text-xs dark:bg-zinc-900">{CRITICALITY.map((value) => <option key={value} value={value}>{human(value)}</option>)}</select><select value={roleForm.incumbentEmployeeId} onChange={(e) => setRoleForm((c) => ({ ...c, incumbentEmployeeId: e.target.value }))} className="w-full rounded-xl border p-2 text-xs dark:bg-zinc-900"><option value="">No incumbent / open role</option>{employees.map((employee) => <option key={employee.id} value={employee.id}>{employee.name}</option>)}</select><textarea rows={3} value={roleForm.description} onChange={(e) => setRoleForm((c) => ({ ...c, description: e.target.value }))} placeholder="Role context" className="w-full rounded-xl border p-2 text-xs dark:bg-zinc-900" /><button type="submit" disabled={successionSaving} className="w-full rounded-xl bg-zinc-950 px-3 py-2 text-xs font-black text-white dark:bg-white dark:text-zinc-950">Create Role</button></form> : null}

                <form onSubmit={nominateCandidate} className="space-y-3 rounded-2xl border border-zinc-100 p-3 dark:border-white/10"><div className="flex items-center gap-2"><UserRound size={16} /><h4 className="text-sm font-black">Nominate Candidate</h4></div><select required value={candidateForm.roleId} onChange={(e) => setCandidateForm((c) => ({ ...c, roleId: e.target.value }))} className="w-full rounded-xl border p-2 text-xs dark:bg-zinc-900"><option value="">Select role</option>{roles.filter((item) => item.isActive).map((item) => <option key={item.id} value={item.id}>{item.title} · {item.department || "Company"}</option>)}</select><select required value={candidateForm.employeeId} onChange={(e) => setCandidateForm((c) => ({ ...c, employeeId: e.target.value }))} className="w-full rounded-xl border p-2 text-xs dark:bg-zinc-900">{(data?.rows || []).map((employee) => <option key={employee.employeeId} value={employee.employeeId}>{employee.name}</option>)}</select><select value={candidateForm.readiness} onChange={(e) => setCandidateForm((c) => ({ ...c, readiness: e.target.value }))} className="w-full rounded-xl border p-2 text-xs dark:bg-zinc-900">{READINESS.map((value) => <option key={value} value={value}>{human(value)}</option>)}</select><select value={candidateForm.priority} onChange={(e) => setCandidateForm((c) => ({ ...c, priority: e.target.value }))} className="w-full rounded-xl border p-2 text-xs dark:bg-zinc-900">{[1,2,3,4,5].map((value) => <option key={value} value={value}>Bench priority {value}</option>)}</select><textarea rows={3} value={candidateForm.rationale} onChange={(e) => setCandidateForm((c) => ({ ...c, rationale: e.target.value }))} placeholder="Why this candidate / what readiness evidence exists?" className="w-full rounded-xl border p-2 text-xs dark:bg-zinc-900" /><button type="submit" disabled={successionSaving || !candidateForm.roleId || !candidateForm.employeeId} className="w-full rounded-xl bg-gradient-to-l from-amber-500 to-yellow-300 px-3 py-2 text-xs font-black text-zinc-950">Nominate Candidate</button></form>

                <div className="space-y-2 rounded-2xl border border-zinc-100 p-3 dark:border-white/10"><div className="flex items-center gap-2"><UsersRound size={16} /><h4 className="text-sm font-black">Succession Roles</h4></div>{!roles.length ? <p className="py-6 text-center text-xs text-zinc-400">No succession roles.</p> : roles.map((item) => <div key={item.id} className={`rounded-xl border p-3 ${item.isActive ? "" : "opacity-50"}`}><div className="flex items-start justify-between gap-2"><div><p className="text-xs font-black">{item.title}</p><p className="text-[10px] text-zinc-400">{item.department || "Company"} · {human(item.criticality)}</p></div>{canConfigureRoles && item.isActive ? <button type="button" onClick={() => deactivateRole(item.id)} className="text-[10px] font-black text-red-600">Deactivate</button> : null}</div><div className="mt-2 space-y-1.5">{(item.candidates || []).filter((candidate) => candidate.isActive).map((candidate) => <div key={candidate.id} className="flex items-center justify-between gap-2 rounded-lg bg-zinc-50 px-2 py-1.5 dark:bg-white/[0.04]"><button type="button" onClick={() => onOpenEmployee?.(candidate.employeeId)} className="min-w-0 truncate text-left text-[10px] font-black">{candidate.employee?.name || "Candidate"} · {human(candidate.readiness)}</button><button type="button" onClick={() => deactivateCandidate(item.id, candidate.id)} className="text-[10px] font-black text-red-600">Remove</button></div>)}</div></div>)}</div>
              </div>
            )}
          </div>
        </div>
      ) : null}
    </>
  );
}

export function EmployeeTalentSuccession({ user, employee, selectedRange, refreshToken = "" }) {
  const role = String(user?.role || "").toUpperCase();
  const canView = MANAGER_ROLES.has(role);
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!canView || !employee?.id || !selectedRange?.start || !selectedRange?.end || selectedRange?.invalid) return;
    let ignore = false;
    api.tasks.talentOverview({ start: selectedRange.start.toISOString(), end: selectedRange.end.toISOString(), employeeId: employee.id })
      .then((result) => { if (!ignore) { setData(result); setError(""); } })
      .catch((err) => { if (!ignore) { setData(null); setError(getErrorMessage(err, "Unable to load talent profile.")); } });
    return () => { ignore = true; };
  }, [canView, employee?.id, selectedRange?.start?.getTime(), selectedRange?.end?.getTime(), selectedRange?.invalid, refreshToken]);

  if (!canView) return null;
  const row = data?.rows?.[0] || null;
  return (
    <section className="mt-4 rounded-2xl border border-zinc-100 p-4 dark:border-white/10">
      <div className="flex flex-wrap items-start justify-between gap-3"><div><div className="flex items-center gap-2"><Crown size={16} className="text-amber-500" /><h3 className="text-sm font-black text-zinc-950 dark:text-white">Talent & Succession</h3><Badge tone="neutral">Manager-only</Badge></div><p className="mt-1 text-[10px] font-bold text-zinc-400">Potential, 9-box position and succession nominations are management planning data.</p></div>{row?.potentialLevel ? <Badge tone={badgeTone(row.potentialLevel)}>{human(row.potentialLevel)} Potential</Badge> : <Badge>Not Assessed</Badge>}</div>
      {error ? <div className="mt-3"><Notice type="error">{error}</Notice></div> : null}
      {!row ? <p className="mt-4 text-xs font-bold text-zinc-400">No talent assessment available for this employee.</p> : <><div className="mt-3 grid gap-2 sm:grid-cols-4"><MiniMetric label="Performance Band" value={human(row.performanceBand)} note={row.performanceScore == null ? "No Activity" : `Score ${row.performanceScore}`} /><MiniMetric label="Potential" value={row.potentialLevel ? human(row.potentialLevel) : "—"} /><MiniMetric label="9-Box" value={row.talentBoxLabel || "Unclassified"} /><MiniMetric label="Skill Coverage" value={row.skillCoveragePercent == null ? "—" : `${row.skillCoveragePercent}%`} note={`${row.criticalSkillGaps || 0} critical gaps`} /></div>{row.potentialManagerNote ? <p className="mt-3 rounded-xl bg-zinc-50 p-3 text-[11px] font-bold text-zinc-600 dark:bg-white/[0.04] dark:text-zinc-300">{row.potentialManagerNote}</p> : null}<div className="mt-3"><p className="text-[10px] font-black uppercase tracking-[0.06em] text-zinc-400">Succession Nominations</p>{!row.successionNominations?.length ? <p className="mt-2 text-xs font-bold text-zinc-400">No active succession nominations.</p> : <div className="mt-2 space-y-2">{row.successionNominations.map((nomination) => <div key={nomination.candidateId} className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-zinc-100 p-2 dark:border-white/10"><div><p className="text-xs font-black">{nomination.roleTitle}</p><p className="text-[10px] text-zinc-400">{nomination.roleDepartment || "Company"} · Priority {nomination.priority}</p></div><Badge tone={nomination.readiness === "READY_NOW" ? "success" : "warning"}>{human(nomination.readiness)}</Badge></div>)}</div>}</div></>}
    </section>
  );
}
'''
path.write_text(content)
print("FRONTEND_TALENT_COMPONENT=PASS")
print("FRONTEND_TALENT_DRAWER_COMPONENT=PASS")
