#!/usr/bin/env python3
from pathlib import Path
import sys

repo = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
path = repo / "frontend/src/components/performance/RecognitionRewards.jsx"
if path.exists():
    raise SystemExit("Phase 11 component already exists")
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(r'''import { useEffect, useMemo, useState } from "react";
import {
  Award,
  CalendarDays,
  CheckCircle2,
  Clock3,
  Gift,
  Plus,
  RefreshCw,
  Settings2,
  Trophy,
  UsersRound,
  X,
} from "lucide-react";
import { Badge, Card, Notice } from "../ui/Primitives";
import { api } from "../../lib/api";
import { getErrorMessage } from "../../lib/errors";

const MANAGER_ROLES = new Set(["SUPER_ADMIN", "ADMIN", "MANAGER", "PROJECT_MANAGER"]);
const ADMIN_ROLES = new Set(["SUPER_ADMIN", "ADMIN"]);
const REWARD_TYPES = ["NONE", "BADGE", "CERTIFICATE", "GIFT", "EXPERIENCE", "OTHER"];

function human(value) {
  return String(value || "—").replaceAll("_", " ").toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase());
}

function dateLabel(value) {
  if (!value) return "—";
  try {
    return new Intl.DateTimeFormat("en-GB", { day: "2-digit", month: "short", year: "numeric" }).format(new Date(value));
  } catch {
    return "—";
  }
}

function todayInput() {
  const now = new Date();
  const local = new Date(now.getTime() - now.getTimezoneOffset() * 60000);
  return local.toISOString().slice(0, 10);
}

function statusTone(status) {
  if (["APPROVED", "OPEN"].includes(status)) return "success";
  if (["REJECTED", "CLOSED"].includes(status)) return "danger";
  if (["PENDING", "DRAFT"].includes(status)) return "warning";
  return "neutral";
}

function MiniMetric({ icon: Icon, label, value, note }) {
  return (
    <div className="rounded-2xl border border-zinc-100 bg-zinc-50/60 p-3 dark:border-white/10 dark:bg-white/[0.025]">
      <div className="flex items-center justify-between"><p className="text-[10px] font-black uppercase tracking-[0.08em] text-zinc-400">{label}</p>{Icon ? <Icon size={15} className="text-amber-500" /> : null}</div>
      <p className="mt-1 text-xl font-black text-zinc-950 dark:text-white">{value}</p>
      {note ? <p className="mt-1 text-[10px] font-bold text-zinc-400">{note}</p> : null}
    </div>
  );
}

export function RecognitionRewardsPanel({
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
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [toast, setToast] = useState(null);
  const [localRefresh, setLocalRefresh] = useState(0);
  const [frameworkOpen, setFrameworkOpen] = useState(false);
  const [nominationOpen, setNominationOpen] = useState(false);
  const [approvalNomination, setApprovalNomination] = useState(null);
  const [saving, setSaving] = useState(false);
  const [cycleForm, setCycleForm] = useState({ name: "", cycleType: "MONTHLY", department: "", startDate: todayInput(), endDate: todayInput(), nominationStart: "", nominationEnd: "", notes: "" });
  const [categoryForm, setCategoryForm] = useState({ name: "", categoryType: "RECOGNITION", description: "", rewardType: "NONE", defaultRewardDescription: "" });
  const [nominationForm, setNominationForm] = useState({ cycleId: "", categoryId: "", nomineeEmployeeId: "", reason: "" });
  const [approvalForm, setApprovalForm] = useState({ title: "", message: "", rewardType: "NONE", rewardDescription: "", decisionNote: "", publish: true });

  const departments = useMemo(() => [...new Set(employees.map((employee) => employee.department).filter(Boolean))].sort(), [employees]);

  async function load() {
    if (!canManage) return;
    setLoading(true);
    setError("");
    try {
      const result = await api.tasks.recognitionOverview({
        employeeId: employeeFilter !== "all" ? employeeFilter : "",
        department: departmentFilter !== "all" ? departmentFilter : "",
      });
      setData(result);
    } catch (err) {
      setData(null);
      setError(getErrorMessage(err, "Unable to load recognition and performance cycles."));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, [employeeFilter, departmentFilter, refreshToken, localRefresh, canManage]);

  if (!canManage) return null;

  const cycles = data?.cycles || [];
  const categories = data?.categories || [];
  const nominations = data?.nominations || [];
  const awards = data?.awards || [];
  const summary = data?.summary || {};
  const openCycles = cycles.filter((cycle) => cycle.status === "OPEN" && cycle.nominationWindowOpen);
  const pending = nominations.filter((nomination) => nomination.status === "PENDING");

  function openNomination(employeeId = "") {
    setNominationForm({
      cycleId: openCycles[0]?.id || "",
      categoryId: categories[0]?.id || "",
      nomineeEmployeeId: employeeId || (employeeFilter !== "all" ? employeeFilter : employees[0]?.id || ""),
      reason: "",
    });
    setNominationOpen(true);
  }

  async function createCycle(event) {
    event.preventDefault();
    setSaving(true);
    try {
      await api.tasks.createRecognitionCycle({ ...cycleForm, department: cycleForm.department || null, nominationStart: cycleForm.nominationStart || null, nominationEnd: cycleForm.nominationEnd || null, notes: cycleForm.notes || null });
      setCycleForm({ name: "", cycleType: "MONTHLY", department: "", startDate: todayInput(), endDate: todayInput(), nominationStart: "", nominationEnd: "", notes: "" });
      setToast({ type: "success", message: "Performance cycle created." });
      setLocalRefresh((value) => value + 1);
    } catch (err) { setToast({ type: "error", message: getErrorMessage(err, "Unable to create performance cycle.") }); }
    finally { setSaving(false); }
  }

  async function createCategory(event) {
    event.preventDefault();
    setSaving(true);
    try {
      await api.tasks.createRecognitionCategory({ ...categoryForm, defaultRewardDescription: categoryForm.defaultRewardDescription || null });
      setCategoryForm({ name: "", categoryType: "RECOGNITION", description: "", rewardType: "NONE", defaultRewardDescription: "" });
      setToast({ type: "success", message: "Recognition category created." });
      setLocalRefresh((value) => value + 1);
    } catch (err) { setToast({ type: "error", message: getErrorMessage(err, "Unable to create recognition category.") }); }
    finally { setSaving(false); }
  }

  async function transitionCycle(cycle, action) {
    setSaving(true);
    try {
      if (action === "open") await api.tasks.openRecognitionCycle(cycle.id);
      if (action === "close") await api.tasks.closeRecognitionCycle(cycle.id);
      if (action === "deactivate") await api.tasks.deactivateRecognitionCycle(cycle.id);
      setLocalRefresh((value) => value + 1);
    } catch (err) { setToast({ type: "error", message: getErrorMessage(err, "Unable to update performance cycle.") }); }
    finally { setSaving(false); }
  }

  async function nominate(event) {
    event.preventDefault();
    setSaving(true);
    try {
      await api.tasks.createRecognitionNomination(nominationForm);
      setNominationOpen(false);
      setToast({ type: "success", message: "Recognition nomination submitted." });
      setLocalRefresh((value) => value + 1);
    } catch (err) { setToast({ type: "error", message: getErrorMessage(err, "Unable to submit nomination.") }); }
    finally { setSaving(false); }
  }

  function beginApproval(nomination) {
    setApprovalNomination(nomination);
    setApprovalForm({
      title: nomination.category?.name || "Recognition Award",
      message: "",
      rewardType: nomination.category?.rewardType || "NONE",
      rewardDescription: nomination.category?.defaultRewardDescription || "",
      decisionNote: "",
      publish: true,
    });
  }

  async function approve(event) {
    event.preventDefault();
    if (!approvalNomination) return;
    setSaving(true);
    try {
      await api.tasks.approveRecognitionNomination(approvalNomination.id, approvalForm);
      setApprovalNomination(null);
      setToast({ type: "success", message: "Nomination approved and recognition issued." });
      setLocalRefresh((value) => value + 1);
    } catch (err) { setToast({ type: "error", message: getErrorMessage(err, "Unable to approve nomination.") }); }
    finally { setSaving(false); }
  }

  async function reject(nomination) {
    setSaving(true);
    try {
      await api.tasks.rejectRecognitionNomination(nomination.id, { decisionNote: "Not selected for this recognition cycle." });
      setLocalRefresh((value) => value + 1);
    } catch (err) { setToast({ type: "error", message: getErrorMessage(err, "Unable to reject nomination.") }); }
    finally { setSaving(false); }
  }

  return (
    <>
      <Card className="overflow-hidden p-0">
        <div className="flex flex-col gap-3 border-b border-zinc-100 p-4 dark:border-white/10 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="flex flex-wrap items-center gap-2"><p className="text-[11px] font-black uppercase tracking-[0.1em] text-amber-500">Recognition, Rewards & Performance Cycles</p><Badge tone="blue">Phase 11</Badge></div>
            <h2 className="mt-1 text-base font-black text-zinc-950 dark:text-white">Recognition Cycles & Human Approval</h2>
            <p className="mt-1 max-w-3xl text-[11px] font-bold leading-5 text-zinc-400">Monthly, quarterly, annual or custom recognition cycles. Performance data is context only; TOS never auto-awards or calculates payroll, bonuses or compensation.</p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <button type="button" onClick={() => setLocalRefresh((value) => value + 1)} className="rounded-xl border border-zinc-200 p-2 text-zinc-500 dark:border-white/10" aria-label="Refresh recognition"><RefreshCw size={16} className={loading ? "animate-spin" : ""} /></button>
            <button type="button" onClick={() => openNomination()} disabled={!openCycles.length || !categories.length} className="inline-flex items-center gap-2 rounded-xl border border-zinc-200 px-3 py-2 text-xs font-black text-zinc-700 disabled:opacity-40 dark:border-white/10 dark:text-zinc-200"><Plus size={15} /> Nominate</button>
            {canConfigure ? <button type="button" onClick={() => setFrameworkOpen(true)} className="inline-flex items-center gap-2 rounded-xl bg-zinc-950 px-3 py-2 text-xs font-black text-white dark:bg-white dark:text-zinc-950"><Settings2 size={15} /> Manage Cycles</button> : null}
          </div>
        </div>

        {error ? <div className="p-4"><Notice type="error">{error}</Notice></div> : null}
        {toast ? <div className="px-4 pt-4"><Notice type={toast.type === "success" ? "success" : "error"}>{toast.message}</Notice></div> : null}

        <div className="grid gap-3 p-4 sm:grid-cols-2 xl:grid-cols-5">
          <MiniMetric icon={CalendarDays} label="Open Cycles" value={summary.openCycles || 0} note="Currently open" />
          <MiniMetric icon={Clock3} label="Pending" value={summary.pendingNominations || 0} note="Awaiting approval" />
          <MiniMetric icon={CheckCircle2} label="Approved" value={summary.approvedNominations || 0} note="Manager nominations approved" />
          <MiniMetric icon={Trophy} label="Published" value={summary.publishedRecognitions || 0} note={`${summary.recognizedEmployees || 0} recognized employees`} />
          <MiniMetric icon={Gift} label="Rewards" value={summary.rewardsIssued || 0} note="Non-payroll rewards only" />
        </div>

        <div className="grid gap-4 border-t border-zinc-100 p-4 dark:border-white/10 xl:grid-cols-[.85fr_1.15fr]">
          <section>
            <div className="mb-3 flex items-center justify-between"><div><h3 className="text-sm font-black text-zinc-950 dark:text-white">Performance Cycles</h3><p className="mt-1 text-[10px] font-bold text-zinc-400">Opening and closing a cycle never approves nominations automatically.</p></div><Badge>{cycles.length}</Badge></div>
            <div className="space-y-2">
              {cycles.slice(0, 8).map((cycle) => (
                <div key={cycle.id} className="rounded-2xl border border-zinc-100 p-3 dark:border-white/10">
                  <div className="flex items-start justify-between gap-3"><div><p className="text-xs font-black text-zinc-950 dark:text-white">{cycle.name}</p><p className="mt-1 text-[10px] font-bold text-zinc-400">{human(cycle.cycleType)} · {dateLabel(cycle.startDate)} — {dateLabel(cycle.endDate)}{cycle.department ? ` · ${cycle.department}` : " · Company"}</p></div><Badge tone={statusTone(cycle.status)}>{human(cycle.status)}</Badge></div>
                  <div className="mt-2 grid grid-cols-3 gap-2 text-center text-[10px]"><div><p className="text-zinc-400">Nominations</p><p className="font-black">{cycle.nominationCount || 0}</p></div><div><p className="text-zinc-400">Pending</p><p className="font-black">{cycle.pendingNominations || 0}</p></div><div><p className="text-zinc-400">Awards</p><p className="font-black">{cycle.awardCount || 0}</p></div></div>
                  {canConfigure ? <div className="mt-2 flex flex-wrap gap-1">{cycle.status === "DRAFT" && cycle.isActive ? <button type="button" onClick={() => transitionCycle(cycle, "open")} className="rounded-lg border px-2 py-1 text-[10px] font-black">Open</button> : null}{cycle.status === "OPEN" ? <button type="button" onClick={() => transitionCycle(cycle, "close")} className="rounded-lg border px-2 py-1 text-[10px] font-black">Close</button> : null}{cycle.status !== "OPEN" && cycle.isActive ? <button type="button" onClick={() => transitionCycle(cycle, "deactivate")} className="rounded-lg border border-red-200 px-2 py-1 text-[10px] font-black text-red-600">Deactivate</button> : null}</div> : null}
                </div>
              ))}
              {!cycles.length ? <p className="rounded-2xl border border-dashed p-5 text-center text-xs font-bold text-zinc-400">No recognition cycles configured.</p> : null}
            </div>
          </section>

          <section>
            <div className="mb-3 flex items-center justify-between"><div><h3 className="text-sm font-black text-zinc-950 dark:text-white">Recognition Nominations</h3><p className="mt-1 text-[10px] font-bold text-zinc-400">Performance snapshots support the discussion; approval remains human.</p></div><Badge tone={pending.length ? "warning" : "neutral"}>{pending.length} pending</Badge></div>
            <div className="max-h-[460px] space-y-2 overflow-y-auto">
              {nominations.slice(0, 20).map((nomination) => (
                <div key={nomination.id} className="rounded-2xl border border-zinc-100 p-3 dark:border-white/10">
                  <div className="flex items-start justify-between gap-3"><button type="button" onClick={() => onOpenEmployee?.(nomination.nomineeEmployeeId)} className="text-left"><p className="text-xs font-black text-zinc-950 dark:text-white">{nomination.employee?.name || "Employee"}</p><p className="mt-1 text-[10px] font-bold text-zinc-400">{nomination.category?.name} · {nomination.cycle?.name}</p></button><Badge tone={statusTone(nomination.status)}>{human(nomination.status)}</Badge></div>
                  <p className="mt-2 text-[11px] text-zinc-600 dark:text-zinc-300">{nomination.reason}</p>
                  <div className="mt-2 flex flex-wrap gap-2 text-[10px] font-bold text-zinc-400"><span>Score {nomination.snapshotPerformanceScore ?? "—"}</span><span>{nomination.snapshotPerformanceStatus || "No Activity"}</span><span>Target {nomination.snapshotTargetAchievement == null ? "—" : `${nomination.snapshotTargetAchievement}%`}</span></div>
                  {canConfigure && nomination.status === "PENDING" ? <div className="mt-2 flex gap-2"><button type="button" onClick={() => beginApproval(nomination)} className="rounded-lg bg-emerald-600 px-2 py-1 text-[10px] font-black text-white">Approve</button><button type="button" onClick={() => reject(nomination)} className="rounded-lg border border-red-200 px-2 py-1 text-[10px] font-black text-red-600">Reject</button></div> : null}
                </div>
              ))}
              {!nominations.length ? <p className="rounded-2xl border border-dashed p-5 text-center text-xs font-bold text-zinc-400">No nominations yet.</p> : null}
            </div>
          </section>
        </div>

        <section className="border-t border-zinc-100 p-4 dark:border-white/10">
          <div className="mb-3 flex items-center justify-between"><div><h3 className="text-sm font-black text-zinc-950 dark:text-white">Recognition & Rewards History</h3><p className="mt-1 text-[10px] font-bold text-zinc-400">Published recognitions and non-payroll reward descriptors.</p></div><Award size={18} className="text-amber-500" /></div>
          <div className="grid gap-2 md:grid-cols-2 xl:grid-cols-3">
            {awards.filter((award) => award.isPublished).slice(0, 9).map((award) => (
              <button key={award.id} type="button" onClick={() => onOpenEmployee?.(award.employeeId)} className="rounded-2xl border border-amber-100 bg-amber-50/30 p-3 text-left dark:border-amber-400/15 dark:bg-amber-400/[0.035]">
                <div className="flex items-start justify-between gap-2"><div><p className="text-xs font-black text-zinc-950 dark:text-white">{award.employee?.name || "Employee"}</p><p className="mt-0.5 text-[10px] font-bold text-amber-600 dark:text-amber-300">{award.title}</p></div><Trophy size={16} className="text-amber-500" /></div>
                <p className="mt-2 text-[10px] font-bold text-zinc-400">{award.category?.name} · {dateLabel(award.issuedAt)}</p>
                {award.rewardType !== "NONE" ? <p className="mt-1 text-[10px] font-black text-zinc-600 dark:text-zinc-300">{human(award.rewardType)}{award.rewardDescription ? ` · ${award.rewardDescription}` : ""}</p> : null}
              </button>
            ))}
            {!awards.some((award) => award.isPublished) ? <p className="col-span-full rounded-2xl border border-dashed p-5 text-center text-xs font-bold text-zinc-400">No published recognitions yet.</p> : null}
          </div>
        </section>
      </Card>

      {nominationOpen ? <div className="fixed inset-0 z-[70] grid place-items-center bg-black/55 p-3" role="dialog" aria-modal="true"><form onSubmit={nominate} className="w-full max-w-lg rounded-3xl bg-white p-4 shadow-2xl dark:bg-zinc-950"><div className="flex items-center justify-between"><div><p className="text-[10px] font-black uppercase tracking-[.1em] text-amber-500">Recognition Nomination</p><h2 className="text-lg font-black">Nominate Employee</h2></div><button type="button" onClick={() => setNominationOpen(false)} className="p-2 text-zinc-400"><X size={20} /></button></div><div className="mt-4 grid gap-3"><select required value={nominationForm.cycleId} onChange={(e) => setNominationForm((c) => ({ ...c, cycleId: e.target.value }))} className="rounded-xl border p-2 dark:bg-zinc-900">{openCycles.map((cycle) => <option key={cycle.id} value={cycle.id}>{cycle.name}</option>)}</select><select required value={nominationForm.categoryId} onChange={(e) => setNominationForm((c) => ({ ...c, categoryId: e.target.value }))} className="rounded-xl border p-2 dark:bg-zinc-900">{categories.map((category) => <option key={category.id} value={category.id}>{category.name}</option>)}</select><select required value={nominationForm.nomineeEmployeeId} onChange={(e) => setNominationForm((c) => ({ ...c, nomineeEmployeeId: e.target.value }))} className="rounded-xl border p-2 dark:bg-zinc-900">{employees.filter((employee) => employee.id !== user?.id).map((employee) => <option key={employee.id} value={employee.id}>{employee.name}</option>)}</select><textarea required rows="4" value={nominationForm.reason} onChange={(e) => setNominationForm((c) => ({ ...c, reason: e.target.value }))} placeholder="Why should this employee be recognized?" className="rounded-xl border p-2 dark:bg-zinc-900" /><button disabled={saving} className="rounded-xl bg-gradient-to-l from-amber-500 to-yellow-300 px-4 py-3 text-xs font-black text-zinc-950 disabled:opacity-50">Submit Nomination</button></div></form></div> : null}

      {approvalNomination ? <div className="fixed inset-0 z-[75] grid place-items-center bg-black/55 p-3" role="dialog" aria-modal="true"><form onSubmit={approve} className="w-full max-w-lg rounded-3xl bg-white p-4 shadow-2xl dark:bg-zinc-950"><div className="flex items-center justify-between"><div><p className="text-[10px] font-black uppercase tracking-[.1em] text-emerald-500">Human Approval</p><h2 className="text-lg font-black">Issue Recognition</h2></div><button type="button" onClick={() => setApprovalNomination(null)} className="p-2 text-zinc-400"><X size={20} /></button></div><div className="mt-4 grid gap-3"><input required value={approvalForm.title} onChange={(e) => setApprovalForm((c) => ({ ...c, title: e.target.value }))} placeholder="Recognition title" className="rounded-xl border p-2 dark:bg-zinc-900" /><textarea rows="3" value={approvalForm.message} onChange={(e) => setApprovalForm((c) => ({ ...c, message: e.target.value }))} placeholder="Recognition message" className="rounded-xl border p-2 dark:bg-zinc-900" /><select value={approvalForm.rewardType} onChange={(e) => setApprovalForm((c) => ({ ...c, rewardType: e.target.value }))} className="rounded-xl border p-2 dark:bg-zinc-900">{REWARD_TYPES.map((value) => <option key={value}>{value}</option>)}</select><input value={approvalForm.rewardDescription} onChange={(e) => setApprovalForm((c) => ({ ...c, rewardDescription: e.target.value }))} placeholder="Non-payroll reward description" className="rounded-xl border p-2 dark:bg-zinc-900" /><textarea rows="2" value={approvalForm.decisionNote} onChange={(e) => setApprovalForm((c) => ({ ...c, decisionNote: e.target.value }))} placeholder="Internal decision note" className="rounded-xl border p-2 dark:bg-zinc-900" /><label className="flex items-center gap-2 text-xs font-black"><input type="checkbox" checked={approvalForm.publish} onChange={(e) => setApprovalForm((c) => ({ ...c, publish: e.target.checked }))} /> Publish recognition</label><button disabled={saving} className="rounded-xl bg-emerald-600 px-4 py-3 text-xs font-black text-white disabled:opacity-50">Approve & Issue</button></div></form></div> : null}

      {frameworkOpen && canConfigure ? <div className="fixed inset-0 z-[72] grid place-items-center bg-black/55 p-3" role="dialog" aria-modal="true"><div className="max-h-[92vh] w-full max-w-5xl overflow-y-auto rounded-3xl bg-white shadow-2xl dark:bg-zinc-950"><div className="flex items-center justify-between border-b p-4 dark:border-white/10"><div><p className="text-[10px] font-black uppercase tracking-[.1em] text-amber-500">Phase 11 Framework</p><h2 className="text-lg font-black">Cycles & Recognition Categories</h2></div><button type="button" onClick={() => setFrameworkOpen(false)} className="p-2 text-zinc-400"><X size={20} /></button></div><div className="grid gap-5 p-4 lg:grid-cols-2"><form onSubmit={createCycle} className="space-y-3"><h3 className="text-sm font-black">Create Performance Cycle</h3><input required value={cycleForm.name} onChange={(e) => setCycleForm((c) => ({ ...c, name: e.target.value }))} placeholder="Cycle name" className="w-full rounded-xl border p-2 dark:bg-zinc-900" /><div className="grid gap-2 sm:grid-cols-2"><select value={cycleForm.cycleType} onChange={(e) => setCycleForm((c) => ({ ...c, cycleType: e.target.value }))} className="rounded-xl border p-2 dark:bg-zinc-900"><option>MONTHLY</option><option>QUARTERLY</option><option>ANNUAL</option><option>CUSTOM</option></select><select value={cycleForm.department} onChange={(e) => setCycleForm((c) => ({ ...c, department: e.target.value }))} className="rounded-xl border p-2 dark:bg-zinc-900"><option value="">Company-wide</option>{departments.map((department) => <option key={department}>{department}</option>)}</select></div><div className="grid gap-2 sm:grid-cols-2"><label className="text-[10px] font-black text-zinc-500">Start<input type="date" required value={cycleForm.startDate} onChange={(e) => setCycleForm((c) => ({ ...c, startDate: e.target.value }))} className="mt-1 w-full rounded-xl border p-2 dark:bg-zinc-900" /></label><label className="text-[10px] font-black text-zinc-500">End<input type="date" required value={cycleForm.endDate} onChange={(e) => setCycleForm((c) => ({ ...c, endDate: e.target.value }))} className="mt-1 w-full rounded-xl border p-2 dark:bg-zinc-900" /></label></div><div className="grid gap-2 sm:grid-cols-2"><label className="text-[10px] font-black text-zinc-500">Nomination opens<input type="date" value={cycleForm.nominationStart} onChange={(e) => setCycleForm((c) => ({ ...c, nominationStart: e.target.value }))} className="mt-1 w-full rounded-xl border p-2 dark:bg-zinc-900" /></label><label className="text-[10px] font-black text-zinc-500">Nomination closes<input type="date" value={cycleForm.nominationEnd} onChange={(e) => setCycleForm((c) => ({ ...c, nominationEnd: e.target.value }))} className="mt-1 w-full rounded-xl border p-2 dark:bg-zinc-900" /></label></div><textarea rows="2" value={cycleForm.notes} onChange={(e) => setCycleForm((c) => ({ ...c, notes: e.target.value }))} placeholder="Cycle notes" className="w-full rounded-xl border p-2 dark:bg-zinc-900" /><button disabled={saving} className="w-full rounded-xl bg-zinc-950 px-4 py-3 text-xs font-black text-white dark:bg-white dark:text-zinc-950">Create Cycle</button></form><form onSubmit={createCategory} className="space-y-3"><h3 className="text-sm font-black">Create Recognition Category</h3><input required value={categoryForm.name} onChange={(e) => setCategoryForm((c) => ({ ...c, name: e.target.value }))} placeholder="Category name" className="w-full rounded-xl border p-2 dark:bg-zinc-900" /><div className="grid gap-2 sm:grid-cols-2"><select value={categoryForm.categoryType} onChange={(e) => setCategoryForm((c) => ({ ...c, categoryType: e.target.value }))} className="rounded-xl border p-2 dark:bg-zinc-900"><option>RECOGNITION</option><option>REWARD</option></select><select value={categoryForm.rewardType} onChange={(e) => setCategoryForm((c) => ({ ...c, rewardType: e.target.value }))} className="rounded-xl border p-2 dark:bg-zinc-900">{REWARD_TYPES.map((value) => <option key={value}>{value}</option>)}</select></div><textarea rows="3" value={categoryForm.description} onChange={(e) => setCategoryForm((c) => ({ ...c, description: e.target.value }))} placeholder="Recognition criteria / description" className="w-full rounded-xl border p-2 dark:bg-zinc-900" /><input value={categoryForm.defaultRewardDescription} onChange={(e) => setCategoryForm((c) => ({ ...c, defaultRewardDescription: e.target.value }))} placeholder="Default non-payroll reward description" className="w-full rounded-xl border p-2 dark:bg-zinc-900" /><button disabled={saving} className="w-full rounded-xl bg-gradient-to-l from-amber-500 to-yellow-300 px-4 py-3 text-xs font-black text-zinc-950">Create Category</button></form></div><div className="grid gap-4 border-t p-4 dark:border-white/10 lg:grid-cols-2"><div><h3 className="mb-2 text-sm font-black">Cycle History</h3><div className="space-y-2">{cycles.map((cycle) => <div key={cycle.id} className="rounded-xl border p-2 text-xs dark:border-white/10"><div className="flex items-center justify-between"><span className="font-black">{cycle.name}</span><Badge tone={statusTone(cycle.status)}>{human(cycle.status)}</Badge></div><p className="mt-1 text-[10px] text-zinc-400">{human(cycle.cycleType)} · {dateLabel(cycle.startDate)} — {dateLabel(cycle.endDate)}</p></div>)}</div></div><div><h3 className="mb-2 text-sm font-black">Categories</h3><div className="space-y-2">{categories.map((category) => <div key={category.id} className="rounded-xl border p-2 text-xs dark:border-white/10"><div className="flex items-center justify-between"><span className="font-black">{category.name}</span><Badge>{human(category.categoryType)}</Badge></div><p className="mt-1 text-[10px] text-zinc-400">Reward: {human(category.rewardType)}</p></div>)}</div></div></div></div></div> : null}
    </>
  );
}

export function EmployeeRecognitionRewards({ user, employee, refreshToken = "" }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const role = String(user?.role || "").toUpperCase();
  const canView = MANAGER_ROLES.has(role) || user?.id === employee?.id;

  useEffect(() => {
    let ignore = false;
    async function load() {
      if (!canView || !employee?.id) return;
      setError("");
      try {
        const result = await api.tasks.employeeRecognition(employee.id);
        if (!ignore) setData(result);
      } catch (err) {
        if (!ignore) { setData(null); setError(getErrorMessage(err, "Unable to load recognition history.")); }
      }
    }
    load();
    return () => { ignore = true; };
  }, [employee?.id, refreshToken, canView]);

  if (!canView) return null;
  const awards = data?.awards || [];
  const nominations = data?.nominations || [];
  return (
    <section className="mt-4 rounded-2xl border border-amber-100 bg-amber-50/20 p-4 dark:border-amber-400/15 dark:bg-amber-400/[0.025]">
      <div className="flex items-center justify-between gap-3"><div><p className="text-[10px] font-black uppercase tracking-[.08em] text-amber-500">Recognition & Rewards</p><h3 className="mt-1 text-sm font-black text-zinc-950 dark:text-white">Recognition History</h3></div><Trophy size={18} className="text-amber-500" /></div>
      {error ? <div className="mt-3"><Notice type="error">{error}</Notice></div> : null}
      <div className="mt-3 grid grid-cols-3 gap-2 text-center text-[10px]"><div className="rounded-xl border bg-white p-2 dark:border-white/10 dark:bg-white/[0.03]"><p className="text-zinc-400">Awards</p><p className="text-lg font-black">{data?.summary?.awards || 0}</p></div><div className="rounded-xl border bg-white p-2 dark:border-white/10 dark:bg-white/[0.03]"><p className="text-zinc-400">Rewards</p><p className="text-lg font-black">{data?.summary?.rewards || 0}</p></div><div className="rounded-xl border bg-white p-2 dark:border-white/10 dark:bg-white/[0.03]"><p className="text-zinc-400">Pending</p><p className="text-lg font-black">{data?.summary?.pendingNominations || 0}</p></div></div>
      <div className="mt-3 space-y-2">{awards.slice(0, 6).map((award) => <div key={award.id} className="rounded-xl border border-zinc-100 bg-white p-3 dark:border-white/10 dark:bg-white/[0.03]"><div className="flex items-start justify-between gap-2"><div><p className="text-xs font-black">{award.title}</p><p className="mt-1 text-[10px] font-bold text-zinc-400">{award.category?.name} · {dateLabel(award.issuedAt)}</p></div>{award.isPublished ? <Badge tone="success">Published</Badge> : <Badge>Internal</Badge>}</div>{award.message ? <p className="mt-2 text-[11px] text-zinc-600 dark:text-zinc-300">{award.message}</p> : null}{award.rewardType !== "NONE" ? <p className="mt-2 text-[10px] font-black text-amber-700 dark:text-amber-300">{human(award.rewardType)}{award.rewardDescription ? ` · ${award.rewardDescription}` : ""}</p> : null}</div>)}{!awards.length ? <p className="py-3 text-center text-xs font-bold text-zinc-400">No recognition awards yet.</p> : null}</div>
      {MANAGER_ROLES.has(role) && nominations.length ? <div className="mt-3 border-t border-amber-100 pt-3 dark:border-amber-400/15"><p className="text-[10px] font-black uppercase text-zinc-400">Nomination History</p><div className="mt-2 flex flex-wrap gap-2">{nominations.slice(0, 6).map((nomination) => <Badge key={nomination.id} tone={statusTone(nomination.status)}>{nomination.category?.name}: {human(nomination.status)}</Badge>)}</div></div> : null}
    </section>
  );
}
''')
print("FRONTEND_RECOGNITION_COMPONENT=PASS")
