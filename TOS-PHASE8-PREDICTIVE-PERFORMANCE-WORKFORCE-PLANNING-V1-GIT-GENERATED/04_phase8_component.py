#!/usr/bin/env python3
from pathlib import Path
import sys

repo = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS").resolve()
path = repo / "frontend/src/components/performance/WorkforcePlanning.jsx"
if path.exists():
    raise SystemExit("WORKFORCE_COMPONENT_ALREADY_PRESENT=FAIL")
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(r'''import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  ArrowRightLeft,
  BarChart3,
  CalendarDays,
  CheckCircle2,
  Clock3,
  Gauge,
  RefreshCw,
  Settings2,
  ShieldCheck,
  TrendingUp,
  UsersRound,
  X,
} from "lucide-react";
import { Badge, Card, Notice } from "../ui/Primitives";
import { api } from "../../lib/api";
import { getErrorMessage } from "../../lib/errors";

const HORIZONS = [7, 14, 30];

function hours(value) {
  const n = Number(value || 0);
  if (!Number.isFinite(n)) return "—";
  return `${Math.round(n * 10) / 10}h`;
}

function pct(value) {
  if (value == null || !Number.isFinite(Number(value))) return "—";
  return `${Math.round(Number(value) * 10) / 10}%`;
}

function dateLabel(value) {
  if (!value) return "—";
  try {
    return new Intl.DateTimeFormat("en-GB", { day: "2-digit", month: "short" }).format(new Date(value));
  } catch {
    return "—";
  }
}

function todayInput() {
  const now = new Date();
  const local = new Date(now.getTime() - now.getTimezoneOffset() * 60000);
  return local.toISOString().slice(0, 10);
}

function riskTone(risk) {
  if (risk === "CRITICAL" || risk === "HIGH") return "danger";
  if (risk === "WATCH") return "warning";
  if (risk === "HEALTHY") return "success";
  return "neutral";
}

function outlookTone(outlook) {
  if (outlook === "AT_RISK") return "danger";
  if (outlook === "WATCH") return "warning";
  if (outlook === "POSITIVE") return "success";
  if (outlook === "STABLE") return "blue";
  return "neutral";
}

function human(value) {
  return String(value || "—").replaceAll("_", " ").toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase());
}

function loadBarClass(value) {
  const n = Number(value || 0);
  if (n >= 125) return "bg-red-500";
  if (n > 100) return "bg-orange-500";
  if (n >= 85) return "bg-amber-400";
  return "bg-emerald-500";
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

export function WorkforcePlanningPanel({
  user,
  employees = [],
  employeeFilter = "all",
  departmentFilter = "all",
  refreshToken = "",
  onOpenEmployee = null,
  onData = null,
}) {
  const [horizonDays, setHorizonDays] = useState(14);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [localRefresh, setLocalRefresh] = useState(0);
  const [capacityOpen, setCapacityOpen] = useState(false);
  const [plans, setPlans] = useState([]);
  const [planLoading, setPlanLoading] = useState(false);
  const [planSaving, setPlanSaving] = useState(false);
  const [toast, setToast] = useState(null);
  const [form, setForm] = useState({ employeeId: "", weeklyCapacityHours: "40", effectiveFrom: todayInput(), effectiveTo: "", note: "" });

  const role = String(user?.role || "").toUpperCase();
  const canManage = ["SUPER_ADMIN", "ADMIN", "MANAGER", "PROJECT_MANAGER"].includes(role);

  useEffect(() => {
    let ignore = false;
    async function loadForecast() {
      setLoading(true);
      setError("");
      try {
        const result = await api.tasks.workforceForecast({
          horizonDays,
          employeeId: employeeFilter !== "all" ? employeeFilter : "",
          department: departmentFilter !== "all" ? departmentFilter : "",
        });
        if (!ignore) {
          setData(result);
          if (typeof onData === "function") onData(result);
        }
      } catch (err) {
        if (!ignore) {
          setData(null);
          if (typeof onData === "function") onData(null);
          setError(getErrorMessage(err, "Unable to load workforce forecast."));
        }
      } finally {
        if (!ignore) setLoading(false);
      }
    }
    loadForecast();
    return () => { ignore = true; };
  }, [horizonDays, employeeFilter, departmentFilter, refreshToken, localRefresh]);

  const employeeMap = useMemo(() => new Map(employees.map((employee) => [employee.id, employee])), [employees]);

  async function refreshPlans() {
    setPlanLoading(true);
    try {
      const result = await api.tasks.workforceCapacityPlans({});
      setPlans(result?.plans || []);
    } catch (err) {
      setToast({ type: "error", message: getErrorMessage(err, "Unable to load capacity plans.") });
    } finally {
      setPlanLoading(false);
    }
  }

  async function openCapacityManager() {
    if (!canManage) return;
    const first = employees[0]?.id || data?.rows?.[0]?.employeeId || "";
    setForm((current) => ({ ...current, employeeId: current.employeeId || first }));
    setCapacityOpen(true);
    await refreshPlans();
  }

  async function savePlan(event) {
    event.preventDefault();
    setPlanSaving(true);
    try {
      await api.tasks.createWorkforceCapacityPlan({
        employeeId: form.employeeId,
        weeklyCapacityHours: Number(form.weeklyCapacityHours),
        effectiveFrom: form.effectiveFrom,
        effectiveTo: form.effectiveTo || null,
        note: form.note || null,
      });
      setToast({ type: "success", message: "Capacity plan saved." });
      await refreshPlans();
      setLocalRefresh((value) => value + 1);
    } catch (err) {
      setToast({ type: "error", message: getErrorMessage(err, "Unable to save capacity plan.") });
    } finally {
      setPlanSaving(false);
    }
  }

  async function deactivatePlan(planId) {
    setPlanSaving(true);
    try {
      await api.tasks.deactivateWorkforceCapacityPlan(planId);
      setPlans((current) => current.map((plan) => plan.id === planId ? { ...plan, isActive: false } : plan));
      setLocalRefresh((value) => value + 1);
    } catch (err) {
      setToast({ type: "error", message: getErrorMessage(err, "Unable to deactivate capacity plan.") });
    } finally {
      setPlanSaving(false);
    }
  }

  const summary = data?.summary || {};
  const atRiskCount = Number(summary.criticalEmployees || 0) + Number(summary.highRiskEmployees || 0);

  return (
    <>
      <Card className="overflow-hidden p-0">
        <div className="flex flex-col gap-3 border-b border-zinc-100 p-4 dark:border-white/10 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <p className="text-[11px] font-black uppercase tracking-[0.1em] text-amber-500">Predictive Performance & Workforce Planning</p>
              <Badge tone="blue">Rule-based</Badge>
            </div>
            <h2 className="mt-1 text-base font-black text-zinc-950 dark:text-white">Forward Outlook & Capacity</h2>
            <p className="mt-1 max-w-3xl text-[11px] font-bold leading-5 text-zinc-400">Forward-looking operational signals from due work, estimates, capacity, recent performance, targets and coaching actions. No hidden AI score and no automatic task reassignment.</p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {HORIZONS.map((days) => (
              <button key={days} type="button" onClick={() => setHorizonDays(days)} className={`rounded-xl border px-3 py-2 text-xs font-black ${horizonDays === days ? "border-amber-300 bg-amber-50 text-amber-700 dark:border-amber-400/30 dark:bg-amber-400/10 dark:text-amber-200" : "border-zinc-200 text-zinc-500 dark:border-white/10 dark:text-zinc-300"}`}>{days} days</button>
            ))}
            <button type="button" onClick={() => setLocalRefresh((value) => value + 1)} className="rounded-xl border border-zinc-200 p-2 text-zinc-500 dark:border-white/10" aria-label="Refresh workforce forecast"><RefreshCw size={16} className={loading ? "animate-spin" : ""} /></button>
            {canManage ? <button type="button" onClick={openCapacityManager} className="inline-flex items-center gap-2 rounded-xl border border-zinc-200 px-3 py-2 text-xs font-black text-zinc-700 hover:border-amber-300 dark:border-white/10 dark:text-zinc-200"><Settings2 size={15} /> Manage Capacity</button> : null}
          </div>
        </div>

        {error ? <div className="p-4"><Notice type="error">{error}</Notice></div> : null}
        {toast ? <div className="px-4 pt-4"><Notice type={toast.type === "success" ? "success" : "error"}>{toast.message}</Notice></div> : null}

        {loading && !data ? <div className="h-56 animate-pulse bg-zinc-50 dark:bg-white/[0.025]" /> : data ? (
          <>
            <div className="grid gap-3 p-4 sm:grid-cols-2 xl:grid-cols-5">
              <MiniMetric label="Available Capacity" value={hours(summary.totalCapacityHours)} note={`${summary.businessDays || 0} business days`} />
              <MiniMetric label="Planned Demand" value={hours(summary.totalPlannedHours)} note={`${summary.unestimatedDueTasks || 0} due tasks unestimated`} />
              <MiniMetric label="Capacity Gap" value={hours(summary.capacityGapHours)} note={`${pct(summary.teamUtilizationPercent)} team utilization`} />
              <MiniMetric label="At Risk" value={atRiskCount} note={`${summary.watchEmployees || 0} on watch`} />
              <MiniMetric label="Upcoming Deadlines" value={summary.upcomingDueTasks || 0} note={`${summary.overdueOpenTasks || 0} already overdue`} />
            </div>

            <div className="border-t border-zinc-100 dark:border-white/10">
              <div className="hidden overflow-x-auto md:block">
                <table className="w-full min-w-[1050px] text-[11px]">
                  <thead className="bg-zinc-50 text-zinc-400 dark:bg-white/[0.025]"><tr><th className="px-3 py-3 text-left">Employee</th><th className="px-3 py-3 text-left">Outlook</th><th className="px-3 py-3 text-right">Load</th><th className="px-3 py-3 text-right">Demand</th><th className="px-3 py-3 text-right">Capacity</th><th className="px-3 py-3 text-right">Due</th><th className="px-3 py-3 text-right">Overdue</th><th className="px-3 py-3 text-right">Score</th><th className="px-3 py-3 text-right">Target</th><th className="px-3 py-3 text-right">Confidence</th></tr></thead>
                  <tbody className="divide-y divide-zinc-100 dark:divide-white/10">
                    {(data.rows || []).map((row) => (
                      <tr key={row.employeeId} onClick={() => onOpenEmployee?.(row.employeeId)} className={onOpenEmployee ? "cursor-pointer hover:bg-amber-50/40 dark:hover:bg-amber-400/[0.03]" : ""}>
                        <td className="px-3 py-3"><p className="font-black text-zinc-950 dark:text-white">{row.name}</p><p className="text-[10px] font-bold text-zinc-400">{row.department || "—"} · {row.capacitySource}</p></td>
                        <td className="px-3 py-3"><div className="flex flex-wrap gap-1"><Badge tone={outlookTone(row.outlook)}>{human(row.outlook)}</Badge><Badge tone={riskTone(row.capacityRisk)}>{human(row.capacityRisk)}</Badge></div></td>
                        <td className="px-3 py-3 text-right"><p className="font-black">{pct(row.utilizationPercent)}</p><div className="ml-auto mt-1 h-1.5 w-20 overflow-hidden rounded-full bg-zinc-100 dark:bg-white/10"><div className={`h-full rounded-full ${loadBarClass(row.utilizationPercent)}`} style={{ width: `${Math.min(100, Math.max(0, Number(row.utilizationPercent || 0)))}%` }} /></div></td>
                        <td className="px-3 py-3 text-right font-black">{hours(row.plannedRemainingHours)}</td>
                        <td className="px-3 py-3 text-right">{hours(row.capacityHours)}</td>
                        <td className="px-3 py-3 text-right">{row.dueTasks}</td>
                        <td className={`px-3 py-3 text-right font-black ${row.overdueOpenTasks ? "text-red-600" : "text-zinc-400"}`}>{row.overdueOpenTasks}</td>
                        <td className="px-3 py-3 text-right font-black">{row.performanceScore ?? "—"}<span className="ml-1 text-[9px] text-zinc-400">{row.scoreDelta != null ? `${row.scoreDelta > 0 ? "+" : ""}${row.scoreDelta}` : ""}</span></td>
                        <td className="px-3 py-3 text-right">{row.targetAchievement != null ? `${row.targetAchievement}%` : "—"}</td>
                        <td className="px-3 py-3 text-right"><Badge tone={row.forecastConfidence === "HIGH" ? "success" : row.forecastConfidence === "LOW" ? "warning" : "neutral"}>{human(row.forecastConfidence)}</Badge></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="grid gap-2 p-3 md:hidden">
                {(data.rows || []).map((row) => (
                  <button key={row.employeeId} type="button" onClick={() => onOpenEmployee?.(row.employeeId)} className="rounded-2xl border border-zinc-100 p-3 text-left dark:border-white/10">
                    <div className="flex items-start justify-between gap-3"><div><p className="text-xs font-black text-zinc-950 dark:text-white">{row.name}</p><p className="text-[10px] font-bold text-zinc-400">{row.department || "—"}</p></div><Badge tone={outlookTone(row.outlook)}>{human(row.outlook)}</Badge></div>
                    <div className="mt-3 grid grid-cols-4 gap-2 text-center text-[10px]"><div><p className="text-zinc-400">Load</p><p className="font-black">{pct(row.utilizationPercent)}</p></div><div><p className="text-zinc-400">Demand</p><p className="font-black">{hours(row.plannedRemainingHours)}</p></div><div><p className="text-zinc-400">Capacity</p><p className="font-black">{hours(row.capacityHours)}</p></div><div><p className="text-zinc-400">Overdue</p><p className="font-black text-red-600">{row.overdueOpenTasks}</p></div></div>
                  </button>
                ))}
              </div>
            </div>

            <div className="grid gap-4 border-t border-zinc-100 p-4 dark:border-white/10 xl:grid-cols-3">
              <section>
                <div className="mb-3 flex items-center gap-2"><ArrowRightLeft size={16} className="text-amber-500" /><h3 className="text-sm font-black text-zinc-950 dark:text-white">Reallocation Opportunities</h3></div>
                <div className="space-y-2">{data.recommendations?.length ? data.recommendations.slice(0, 6).map((item, index) => <div key={`${item.fromEmployeeId}-${item.toEmployeeId}-${index}`} className="rounded-xl border border-zinc-100 p-3 text-[11px] dark:border-white/10"><p className="font-black text-zinc-900 dark:text-white">{item.fromEmployee} → {item.toEmployee}</p><p className="mt-1 text-zinc-500">Consider moving about <b>{hours(item.suggestedHours)}</b> · {item.reason}</p></div>) : <p className="rounded-xl border border-dashed border-zinc-200 p-4 text-xs font-bold text-zinc-400 dark:border-white/10">No material reallocation opportunity from estimated work.</p>}</div>
              </section>

              <section>
                <div className="mb-3 flex items-center gap-2"><UsersRound size={16} className="text-amber-500" /><h3 className="text-sm font-black text-zinc-950 dark:text-white">Department Capacity</h3></div>
                <div className="space-y-2">{(data.departments || []).slice(0, 7).map((item) => <div key={item.department} className="rounded-xl border border-zinc-100 p-3 dark:border-white/10"><div className="flex items-center justify-between gap-3"><div><p className="text-xs font-black text-zinc-950 dark:text-white">{item.department}</p><p className="text-[10px] font-bold text-zinc-400">{item.employees} employees · {item.overdueTasks} overdue</p></div><p className="text-sm font-black">{pct(item.utilizationPercent)}</p></div></div>)}</div>
              </section>

              <section>
                <div className="mb-3 flex items-center gap-2"><CalendarDays size={16} className="text-amber-500" /><h3 className="text-sm font-black text-zinc-950 dark:text-white">Upcoming Deadlines</h3></div>
                <div className="space-y-2">{data.upcomingDeadlines?.length ? data.upcomingDeadlines.slice(0, 7).map((task) => <div key={task.taskId} className="rounded-xl border border-zinc-100 p-3 dark:border-white/10"><div className="flex justify-between gap-3"><div className="min-w-0"><p className="truncate text-xs font-black text-zinc-950 dark:text-white">{task.title}</p><p className="truncate text-[10px] font-bold text-zinc-400">{task.employeeName || "—"} · {task.projectName || "—"}</p></div><p className="shrink-0 text-[10px] font-black text-zinc-500">{dateLabel(task.dueDate)}</p></div></div>) : <p className="rounded-xl border border-dashed border-zinc-200 p-4 text-xs font-bold text-zinc-400 dark:border-white/10">No deadlines in this horizon.</p>}</div>
              </section>
            </div>

            <div className="flex flex-col gap-2 border-t border-zinc-100 bg-zinc-50/50 px-4 py-3 text-[10px] font-bold text-zinc-400 dark:border-white/10 dark:bg-white/[0.015] sm:flex-row sm:items-center sm:justify-between"><span className="inline-flex items-center gap-1.5"><ShieldCheck size={13} /> {data.methodology?.note}</span><span>{data.methodology?.businessDays} · Watch ≥85% · High &gt;100% · Critical ≥125%</span></div>
          </>
        ) : null}
      </Card>

      {capacityOpen ? (
        <div className="fixed inset-0 z-[70] grid place-items-center bg-black/55 p-3" role="dialog" aria-modal="true" aria-label="Workforce capacity management">
          <div className="max-h-[92vh] w-full max-w-4xl overflow-y-auto rounded-3xl bg-white shadow-2xl dark:bg-zinc-950">
            <div className="flex items-center justify-between border-b border-zinc-100 p-4 dark:border-white/10"><div><p className="text-[10px] font-black uppercase tracking-[0.1em] text-amber-500">Phase 8</p><h2 className="text-lg font-black text-zinc-950 dark:text-white">Workforce Capacity Plans</h2><p className="mt-1 text-[11px] font-bold text-zinc-400">Active plans cannot overlap for the same employee. Capacity changes are explicit and auditable.</p></div><button type="button" onClick={() => setCapacityOpen(false)} className="rounded-xl p-2 text-zinc-400"><X size={20} /></button></div>
            <div className="grid gap-4 p-4 lg:grid-cols-[.9fr_1.1fr]">
              <form onSubmit={savePlan} className="space-y-3 rounded-2xl border border-zinc-100 p-4 dark:border-white/10">
                <label className="block text-xs font-black text-zinc-500">Employee<select required value={form.employeeId} onChange={(e) => setForm((current) => ({ ...current, employeeId: e.target.value }))} className="mt-1 w-full rounded-xl border border-zinc-200 bg-white p-2.5 text-xs dark:border-white/10 dark:bg-zinc-900">{employees.map((employee) => <option key={employee.id} value={employee.id}>{employee.name} · {employee.department || "—"}</option>)}</select></label>
                <label className="block text-xs font-black text-zinc-500">Weekly capacity hours<input required type="number" min="0.5" max="168" step="0.5" value={form.weeklyCapacityHours} onChange={(e) => setForm((current) => ({ ...current, weeklyCapacityHours: e.target.value }))} className="mt-1 w-full rounded-xl border border-zinc-200 bg-white p-2.5 text-xs dark:border-white/10 dark:bg-zinc-900" /></label>
                <div className="grid gap-2 sm:grid-cols-2"><label className="text-xs font-black text-zinc-500">Effective from<input required type="date" value={form.effectiveFrom} onChange={(e) => setForm((current) => ({ ...current, effectiveFrom: e.target.value }))} className="mt-1 w-full rounded-xl border border-zinc-200 bg-white p-2.5 text-xs dark:border-white/10 dark:bg-zinc-900" /></label><label className="text-xs font-black text-zinc-500">Effective to<input type="date" value={form.effectiveTo} onChange={(e) => setForm((current) => ({ ...current, effectiveTo: e.target.value }))} className="mt-1 w-full rounded-xl border border-zinc-200 bg-white p-2.5 text-xs dark:border-white/10 dark:bg-zinc-900" /></label></div>
                <label className="block text-xs font-black text-zinc-500">Note<textarea rows="3" value={form.note} onChange={(e) => setForm((current) => ({ ...current, note: e.target.value }))} className="mt-1 w-full rounded-xl border border-zinc-200 bg-white p-2.5 text-xs dark:border-white/10 dark:bg-zinc-900" placeholder="Optional planning note" /></label>
                <button type="submit" disabled={planSaving || !form.employeeId} className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-l from-amber-500 to-yellow-300 px-4 py-3 text-xs font-black text-zinc-950 disabled:opacity-50"><Gauge size={15} />{planSaving ? "Saving…" : "Save Capacity Plan"}</button>
              </form>

              <section><div className="mb-3 flex items-center justify-between"><h3 className="text-sm font-black text-zinc-950 dark:text-white">Capacity History</h3>{planLoading ? <RefreshCw size={14} className="animate-spin text-zinc-400" /> : null}</div><div className="max-h-[520px] space-y-2 overflow-y-auto">{plans.length ? plans.map((plan) => <div key={plan.id} className={`rounded-2xl border border-zinc-100 p-3 dark:border-white/10 ${plan.isActive ? "" : "opacity-50"}`}><div className="flex items-start justify-between gap-3"><div><p className="text-xs font-black text-zinc-950 dark:text-white">{plan.employee?.name || employeeMap.get(plan.employeeId)?.name || "Employee"}</p><p className="mt-1 text-[10px] font-bold text-zinc-400">{plan.weeklyCapacityHours}h/week · {dateLabel(plan.effectiveFrom)} → {plan.effectiveTo ? dateLabel(plan.effectiveTo) : "Open-ended"}</p>{plan.note ? <p className="mt-2 text-[11px] text-zinc-500">{plan.note}</p> : null}</div>{plan.isActive ? <button type="button" disabled={planSaving} onClick={() => deactivatePlan(plan.id)} className="rounded-lg border border-red-200 px-2 py-1 text-[10px] font-black text-red-600 disabled:opacity-50">Deactivate</button> : <Badge>Inactive</Badge>}</div></div>) : <div className="rounded-2xl border border-dashed border-zinc-200 p-5 text-center text-xs font-bold text-zinc-400 dark:border-white/10">No explicit capacity plans yet. Forecast uses legacy design capacity when available, otherwise the visible 40h/week fallback.</div>}</div></section>
            </div>
          </div>
        </div>
      ) : null}
    </>
  );
}

export function EmployeeWorkforceOutlook({ forecast }) {
  if (!forecast) return null;
  return (
    <section className="mt-4 rounded-2xl border border-blue-100 bg-blue-50/30 p-4 dark:border-blue-400/15 dark:bg-blue-400/[0.035]">
      <div className="flex flex-wrap items-start justify-between gap-3"><div><p className="text-[10px] font-black uppercase tracking-[0.08em] text-blue-500">Forward Outlook</p><h3 className="mt-1 text-sm font-black text-zinc-950 dark:text-white">Workforce Planning</h3><p className="mt-1 text-[11px] font-bold text-zinc-400">{forecast.capacitySource} · {forecast.weeklyCapacityHours}h/week · {forecast.forecastConfidence} confidence</p></div><div className="flex gap-1"><Badge tone={outlookTone(forecast.outlook)}>{human(forecast.outlook)}</Badge><Badge tone={riskTone(forecast.capacityRisk)}>{human(forecast.capacityRisk)}</Badge></div></div>
      <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-4"><MiniMetric label="Load" value={pct(forecast.utilizationPercent)} /><MiniMetric label="Demand" value={hours(forecast.plannedRemainingHours)} /><MiniMetric label="Capacity" value={hours(forecast.capacityHours)} /><MiniMetric label="Due / Overdue" value={`${forecast.dueTasks}/${forecast.overdueOpenTasks}`} /></div>
      {forecast.signals?.length ? <div className="mt-3 space-y-1.5">{forecast.signals.slice(0, 4).map((signal, index) => <div key={`${signal.type}-${index}`} className="flex items-start gap-2 text-[11px] font-bold text-zinc-600 dark:text-zinc-300"><AlertTriangle size={13} className={signal.severity === "critical" ? "mt-0.5 shrink-0 text-red-500" : signal.severity === "warning" ? "mt-0.5 shrink-0 text-amber-500" : "mt-0.5 shrink-0 text-blue-500"} /><span>{signal.message}</span></div>)}</div> : <div className="mt-3 flex items-center gap-2 text-[11px] font-bold text-emerald-600"><CheckCircle2 size={14} />No material forward risk signal.</div>}
    </section>
  );
}
''')
print("FRONTEND_WORKFORCE_COMPONENT=PASS")
