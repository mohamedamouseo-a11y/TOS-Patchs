#!/usr/bin/env python3
from pathlib import Path
import sys

repo = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS").resolve()
path = repo / "frontend/src/components/performance/PerformanceReviews.jsx"
if path.exists():
    raise SystemExit("PHASE7_COMPONENT_ALREADY_EXISTS=FAIL")
path.parent.mkdir(parents=True, exist_ok=True)

content = r'''import { useEffect, useMemo, useState } from "react";
import {
  AlertCircle,
  CalendarClock,
  CheckCircle2,
  ClipboardCheck,
  ListChecks,
  MessageSquareText,
  Plus,
  Send,
  UserCheck,
  X,
} from "lucide-react";
import { Badge, Card, Notice } from "../ui/Primitives";
import { api } from "../../lib/api";
import { getErrorMessage } from "../../lib/errors";

const REVIEW_TRIGGERS = [
  ["PERIODIC", "Periodic review"],
  ["TARGET_MISSED", "Missed target"],
  ["TARGET_AT_RISK", "Target at risk"],
  ["SCORE_DROP", "Score drop"],
  ["OVERDUE", "Overdue work"],
  ["NO_ACTIVITY", "No activity"],
  ["WORKLOAD_ISSUE", "Workload issue"],
  ["MANAGER_INITIATED", "Manager initiated"],
];

const MANAGER_ROLES = new Set(["SUPER_ADMIN", "ADMIN", "MANAGER", "PROJECT_MANAGER"]);

function canManageReviews(user) {
  return MANAGER_ROLES.has(String(user?.role || "").toUpperCase());
}

function dateInput(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return new Date(date.getTime() - date.getTimezoneOffset() * 60000).toISOString().slice(0, 10);
}

function formatDate(value) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat("en-GB", { day: "2-digit", month: "short", year: "numeric" }).format(date);
}

function formatHours(value) {
  const hours = Number(value || 0);
  if (!Number.isFinite(hours) || hours <= 0) return "0h";
  return `${Math.round(hours * 10) / 10}h`;
}

function reviewStatusTone(status) {
  if (status === "COMPLETED") return "success";
  if (status === "SHARED") return "warning";
  if (status === "IN_PROGRESS") return "info";
  return "neutral";
}

function reviewStatusLabel(status) {
  return String(status || "DRAFT").replaceAll("_", " ");
}

function actionStatusClasses(status) {
  if (status === "COMPLETED") return "bg-emerald-50 text-emerald-700 ring-emerald-200 dark:bg-emerald-400/10 dark:text-emerald-300 dark:ring-emerald-400/20";
  if (status === "IN_PROGRESS") return "bg-amber-50 text-amber-700 ring-amber-200 dark:bg-amber-400/10 dark:text-amber-300 dark:ring-amber-400/20";
  if (status === "CANCELLED") return "bg-zinc-100 text-zinc-500 ring-zinc-200 dark:bg-white/10 dark:text-zinc-400 dark:ring-white/10";
  return "bg-orange-50 text-orange-700 ring-orange-200 dark:bg-orange-400/10 dark:text-orange-300 dark:ring-orange-400/20";
}

function MiniKpi({ icon: Icon, label, value, note = "" }) {
  return (
    <div className="rounded-2xl border border-zinc-200 bg-white p-3 dark:border-white/10 dark:bg-white/[0.03]">
      <div className="flex items-center justify-between gap-2">
        <p className="text-[10px] font-black uppercase tracking-[0.08em] text-zinc-400">{label}</p>
        <Icon size={15} className="text-zinc-400" />
      </div>
      <p className="mt-2 text-xl font-black text-zinc-950 dark:text-white">{value}</p>
      {note ? <p className="mt-1 text-[10px] font-bold text-zinc-400">{note}</p> : null}
    </div>
  );
}

function ReviewModal({ review = null, initialEmployeeId = "", employees = [], selectedRange, user, onClose, onChanged }) {
  const canManage = canManageReviews(user);
  const [detail, setDetail] = useState(review);
  const [loading, setLoading] = useState(Boolean(review?.id));
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [employeeComment, setEmployeeComment] = useState(review?.employeeComment || "");
  const [actionForm, setActionForm] = useState({ title: "", description: "", dueDate: "", priority: "MEDIUM" });
  const [form, setForm] = useState(() => ({
    employeeId: review?.employeeId || initialEmployeeId || employees[0]?.id || "",
    periodStart: dateInput(review?.periodStart || selectedRange?.start),
    periodEnd: dateInput(review?.periodEnd || selectedRange?.end),
    triggerType: review?.triggerType || "PERIODIC",
    triggerReference: review?.triggerReference || "",
    title: review?.title || "",
    strengths: review?.strengths || "",
    improvementAreas: review?.improvementAreas || "",
    managerNotes: review?.managerNotes || "",
    followUpAt: dateInput(review?.followUpAt),
  }));

  const reviewId = detail?.id || review?.id || null;
  const employee = useMemo(() => employees.find((item) => item.id === (detail?.employeeId || form.employeeId)) || detail?.employee || null, [employees, detail, form.employeeId]);
  const isOwnEmployee = Boolean(user?.id && (detail?.employeeId || form.employeeId) === user.id);

  async function reload(id = reviewId) {
    if (!id) return;
    setLoading(true);
    setError("");
    try {
      const next = await api.tasks.performanceReview(id);
      setDetail(next);
      setEmployeeComment(next?.employeeComment || "");
      setForm({
        employeeId: next.employeeId,
        periodStart: dateInput(next.periodStart),
        periodEnd: dateInput(next.periodEnd),
        triggerType: next.triggerType || "PERIODIC",
        triggerReference: next.triggerReference || "",
        title: next.title || "",
        strengths: next.strengths || "",
        improvementAreas: next.improvementAreas || "",
        managerNotes: next.managerNotes || "",
        followUpAt: dateInput(next.followUpAt),
      });
    } catch (err) {
      setError(getErrorMessage(err, "Unable to load performance review."));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (review?.id) reload(review.id);
  }, [review?.id]);

  async function saveReview(event) {
    event.preventDefault();
    if (!canManage) return;
    setSaving(true);
    setError("");
    try {
      if (reviewId) {
        const updated = await api.tasks.updatePerformanceReview(reviewId, {
          triggerType: form.triggerType,
          triggerReference: form.triggerReference || null,
          title: form.title || null,
          strengths: form.strengths || null,
          improvementAreas: form.improvementAreas || null,
          managerNotes: form.managerNotes || null,
          followUpAt: form.followUpAt || null,
        });
        setDetail(updated);
        await reload(updated.id);
      } else {
        const created = await api.tasks.createPerformanceReview({
          employeeId: form.employeeId,
          periodStart: form.periodStart,
          periodEnd: form.periodEnd,
          triggerType: form.triggerType,
          triggerReference: form.triggerReference || null,
          title: form.title || null,
          strengths: form.strengths || null,
          improvementAreas: form.improvementAreas || null,
          managerNotes: form.managerNotes || null,
          followUpAt: form.followUpAt || null,
        });
        setDetail(created);
        await reload(created.id);
      }
      onChanged?.();
    } catch (err) {
      setError(getErrorMessage(err, "Unable to save performance review."));
    } finally {
      setSaving(false);
    }
  }

  async function runReviewAction(action) {
    if (!reviewId) return;
    setSaving(true);
    setError("");
    try {
      if (action === "share") await api.tasks.sharePerformanceReview(reviewId);
      if (action === "complete") await api.tasks.completePerformanceReview(reviewId);
      await reload(reviewId);
      onChanged?.();
    } catch (err) {
      setError(getErrorMessage(err, `Unable to ${action} review.`));
    } finally {
      setSaving(false);
    }
  }

  async function acknowledge() {
    if (!reviewId || !isOwnEmployee) return;
    setSaving(true);
    setError("");
    try {
      await api.tasks.acknowledgePerformanceReview(reviewId, { employeeComment: employeeComment || null });
      await reload(reviewId);
      onChanged?.();
    } catch (err) {
      setError(getErrorMessage(err, "Unable to acknowledge performance review."));
    } finally {
      setSaving(false);
    }
  }

  async function addAction(event) {
    event.preventDefault();
    if (!reviewId || !actionForm.title.trim()) return;
    setSaving(true);
    setError("");
    try {
      await api.tasks.createPerformanceAction(reviewId, {
        title: actionForm.title.trim(),
        description: actionForm.description || null,
        dueDate: actionForm.dueDate || null,
        priority: actionForm.priority,
      });
      setActionForm({ title: "", description: "", dueDate: "", priority: "MEDIUM" });
      await reload(reviewId);
      onChanged?.();
    } catch (err) {
      setError(getErrorMessage(err, "Unable to add action item."));
    } finally {
      setSaving(false);
    }
  }

  async function updateAction(action, status) {
    if (!reviewId) return;
    setSaving(true);
    setError("");
    try {
      await api.tasks.updatePerformanceAction(reviewId, action.id, { status });
      await reload(reviewId);
      onChanged?.();
    } catch (err) {
      setError(getErrorMessage(err, "Unable to update action item."));
    } finally {
      setSaving(false);
    }
  }

  async function cancelAction(action) {
    if (!reviewId || !canManage) return;
    setSaving(true);
    setError("");
    try {
      await api.tasks.cancelPerformanceAction(reviewId, action.id);
      await reload(reviewId);
      onChanged?.();
    } catch (err) {
      setError(getErrorMessage(err, "Unable to cancel action item."));
    } finally {
      setSaving(false);
    }
  }

  const actions = detail?.actions || [];
  const openActions = actions.filter((action) => ["OPEN", "IN_PROGRESS"].includes(action.status));
  const editable = canManage && detail?.status !== "COMPLETED";

  return (
    <div className="fixed inset-0 z-[70] grid place-items-center bg-black/55 p-3" role="dialog" aria-modal="true" aria-label="Performance review">
      <div className="max-h-[94vh] w-full max-w-4xl overflow-hidden rounded-3xl border border-zinc-200 bg-white shadow-2xl dark:border-white/10 dark:bg-zinc-950">
        <header className="flex items-start justify-between gap-3 border-b border-zinc-100 p-4 dark:border-white/10">
          <div>
            <p className="text-[10px] font-black uppercase tracking-[0.1em] text-amber-500">Performance Review</p>
            <h2 className="mt-1 text-lg font-black text-zinc-950 dark:text-white">{detail?.id ? (detail.title || `${employee?.name || "Employee"} review`) : "Start a new review"}</h2>
            {detail?.id ? <div className="mt-2 flex flex-wrap items-center gap-2"><Badge tone={reviewStatusTone(detail.status)}>{reviewStatusLabel(detail.status)}</Badge><span className="text-[11px] font-bold text-zinc-400">{formatDate(detail.periodStart)} — {formatDate(detail.periodEnd)}</span></div> : null}
          </div>
          <button type="button" onClick={onClose} className="rounded-xl p-2 text-zinc-400 hover:bg-zinc-100 dark:hover:bg-white/10" aria-label="Close review"><X size={20} /></button>
        </header>

        <div className="max-h-[calc(94vh-76px)] overflow-y-auto p-4">
          {error ? <div className="mb-3"><Notice type="error">{error}</Notice></div> : null}
          {loading ? <div className="h-48 animate-pulse rounded-2xl bg-zinc-100 dark:bg-white/[0.05]" /> : (
            <>
              {detail?.id ? (
                <div className="mb-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-5">
                  <MiniKpi icon={UserCheck} label="Score snapshot" value={detail.snapshotScore ?? "—"} note={detail.snapshotStatus || "No Activity"} />
                  <MiniKpi icon={ClipboardCheck} label="Target" value={detail.snapshotTargetAchievement != null ? `${detail.snapshotTargetAchievement}%` : "—"} note={detail.snapshotTargetStatus || "No Target"} />
                  <MiniKpi icon={CheckCircle2} label="Completed" value={`${detail.snapshotCompletedTasks || 0}/${detail.snapshotTotalTasks || 0}`} />
                  <MiniKpi icon={AlertCircle} label="Overdue" value={detail.snapshotOverdueTasks || 0} />
                  <MiniKpi icon={CalendarClock} label="Follow-up" value={formatDate(detail.followUpAt)} />
                </div>
              ) : null}

              {canManage ? (
                <form onSubmit={saveReview} className="rounded-2xl border border-zinc-100 p-4 dark:border-white/10">
                  <div className="grid gap-3 md:grid-cols-2">
                    {!detail?.id ? (
                      <label className="text-xs font-black text-zinc-600 dark:text-zinc-300">Employee
                        <select value={form.employeeId} onChange={(event) => setForm((current) => ({ ...current, employeeId: event.target.value }))} className="mt-1.5 w-full rounded-xl border border-zinc-200 bg-white px-3 py-2.5 text-xs font-bold dark:border-white/10 dark:bg-zinc-900 dark:text-white">
                          {employees.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
                        </select>
                      </label>
                    ) : <div><p className="text-[10px] font-black uppercase text-zinc-400">Employee</p><p className="mt-1 text-sm font-black text-zinc-950 dark:text-white">{employee?.name || detail.employeeId}</p></div>}
                    <label className="text-xs font-black text-zinc-600 dark:text-zinc-300">Reason
                      <select value={form.triggerType} onChange={(event) => setForm((current) => ({ ...current, triggerType: event.target.value }))} disabled={!editable && Boolean(detail?.id)} className="mt-1.5 w-full rounded-xl border border-zinc-200 bg-white px-3 py-2.5 text-xs font-bold disabled:opacity-60 dark:border-white/10 dark:bg-zinc-900 dark:text-white">
                        {REVIEW_TRIGGERS.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
                      </select>
                    </label>
                    {!detail?.id ? <><label className="text-xs font-black text-zinc-600 dark:text-zinc-300">Period start<input type="date" value={form.periodStart} onChange={(event) => setForm((current) => ({ ...current, periodStart: event.target.value }))} className="mt-1.5 w-full rounded-xl border border-zinc-200 bg-white px-3 py-2.5 text-xs font-bold dark:border-white/10 dark:bg-zinc-900 dark:text-white" /></label><label className="text-xs font-black text-zinc-600 dark:text-zinc-300">Period end<input type="date" value={form.periodEnd} onChange={(event) => setForm((current) => ({ ...current, periodEnd: event.target.value }))} className="mt-1.5 w-full rounded-xl border border-zinc-200 bg-white px-3 py-2.5 text-xs font-bold dark:border-white/10 dark:bg-zinc-900 dark:text-white" /></label></> : null}
                    <label className="text-xs font-black text-zinc-600 dark:text-zinc-300">Follow-up date<input type="date" value={form.followUpAt} onChange={(event) => setForm((current) => ({ ...current, followUpAt: event.target.value }))} disabled={!editable && Boolean(detail?.id)} className="mt-1.5 w-full rounded-xl border border-zinc-200 bg-white px-3 py-2.5 text-xs font-bold disabled:opacity-60 dark:border-white/10 dark:bg-zinc-900 dark:text-white" /></label>
                    <label className="text-xs font-black text-zinc-600 dark:text-zinc-300">Reference<input value={form.triggerReference} onChange={(event) => setForm((current) => ({ ...current, triggerReference: event.target.value }))} disabled={!editable && Boolean(detail?.id)} placeholder="Alert, target or context reference" className="mt-1.5 w-full rounded-xl border border-zinc-200 bg-white px-3 py-2.5 text-xs font-bold disabled:opacity-60 dark:border-white/10 dark:bg-zinc-900 dark:text-white" /></label>
                  </div>
                  <label className="mt-3 block text-xs font-black text-zinc-600 dark:text-zinc-300">Review title<input value={form.title} onChange={(event) => setForm((current) => ({ ...current, title: event.target.value }))} disabled={!editable && Boolean(detail?.id)} placeholder="Monthly performance review" className="mt-1.5 w-full rounded-xl border border-zinc-200 bg-white px-3 py-2.5 text-xs font-bold disabled:opacity-60 dark:border-white/10 dark:bg-zinc-900 dark:text-white" /></label>
                  <div className="mt-3 grid gap-3 md:grid-cols-2">
                    <label className="text-xs font-black text-zinc-600 dark:text-zinc-300">Strengths<textarea rows={4} value={form.strengths} onChange={(event) => setForm((current) => ({ ...current, strengths: event.target.value }))} disabled={!editable && Boolean(detail?.id)} className="mt-1.5 w-full resize-y rounded-xl border border-zinc-200 bg-white px-3 py-2.5 text-xs font-medium disabled:opacity-60 dark:border-white/10 dark:bg-zinc-900 dark:text-white" /></label>
                    <label className="text-xs font-black text-zinc-600 dark:text-zinc-300">Improvement areas<textarea rows={4} value={form.improvementAreas} onChange={(event) => setForm((current) => ({ ...current, improvementAreas: event.target.value }))} disabled={!editable && Boolean(detail?.id)} className="mt-1.5 w-full resize-y rounded-xl border border-zinc-200 bg-white px-3 py-2.5 text-xs font-medium disabled:opacity-60 dark:border-white/10 dark:bg-zinc-900 dark:text-white" /></label>
                  </div>
                  <label className="mt-3 block text-xs font-black text-zinc-600 dark:text-zinc-300">Manager notes<textarea rows={4} value={form.managerNotes} onChange={(event) => setForm((current) => ({ ...current, managerNotes: event.target.value }))} disabled={!editable && Boolean(detail?.id)} className="mt-1.5 w-full resize-y rounded-xl border border-zinc-200 bg-white px-3 py-2.5 text-xs font-medium disabled:opacity-60 dark:border-white/10 dark:bg-zinc-900 dark:text-white" /></label>
                  {(!detail?.id || editable) ? <div className="mt-3 flex justify-end"><button type="submit" disabled={saving || !form.employeeId} className="rounded-xl bg-zinc-950 px-4 py-2.5 text-xs font-black text-white disabled:opacity-50 dark:bg-white dark:text-zinc-950">{detail?.id ? "Save review" : "Create draft"}</button></div> : null}
                </form>
              ) : (
                <div className="rounded-2xl border border-zinc-100 p-4 dark:border-white/10">
                  <h3 className="text-sm font-black text-zinc-950 dark:text-white">Manager review</h3>
                  <div className="mt-3 grid gap-3 md:grid-cols-2"><div><p className="text-[10px] font-black uppercase text-zinc-400">Strengths</p><p className="mt-1 whitespace-pre-wrap text-xs leading-5 text-zinc-700 dark:text-zinc-300">{detail?.strengths || "—"}</p></div><div><p className="text-[10px] font-black uppercase text-zinc-400">Improvement areas</p><p className="mt-1 whitespace-pre-wrap text-xs leading-5 text-zinc-700 dark:text-zinc-300">{detail?.improvementAreas || "—"}</p></div></div>
                  {detail?.managerNotes ? <div className="mt-3"><p className="text-[10px] font-black uppercase text-zinc-400">Notes</p><p className="mt-1 whitespace-pre-wrap text-xs leading-5 text-zinc-700 dark:text-zinc-300">{detail.managerNotes}</p></div> : null}
                </div>
              )}

              {detail?.id ? (
                <section className="mt-4 rounded-2xl border border-zinc-100 p-4 dark:border-white/10">
                  <div className="flex items-center justify-between gap-3"><div><h3 className="text-sm font-black text-zinc-950 dark:text-white">Action Plan</h3><p className="mt-1 text-[11px] font-bold text-zinc-400">Clear coaching actions with owners, dates and follow-through.</p></div><Badge>{actions.filter((item) => item.status !== "CANCELLED").length}</Badge></div>
                  <div className="mt-3 space-y-2">
                    {actions.length ? actions.map((action) => (
                      <div key={action.id} className="rounded-xl border border-zinc-100 p-3 dark:border-white/10">
                        <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                          <div className="min-w-0"><div className="flex flex-wrap items-center gap-2"><p className="text-xs font-black text-zinc-950 dark:text-white">{action.title}</p><span className={`rounded-full px-2 py-0.5 text-[9px] font-black ring-1 ring-inset ${actionStatusClasses(action.status)}`}>{reviewStatusLabel(action.status)}</span><span className="text-[9px] font-black text-zinc-400">{action.priority}</span></div>{action.description ? <p className="mt-1 text-[11px] leading-5 text-zinc-500 dark:text-zinc-400">{action.description}</p> : null}<p className="mt-1 text-[10px] font-bold text-zinc-400">Due {formatDate(action.dueDate)}</p></div>
                          {action.status !== "CANCELLED" && action.status !== "COMPLETED" ? <div className="flex shrink-0 flex-wrap gap-1.5">{action.status === "OPEN" ? <button type="button" disabled={saving} onClick={() => updateAction(action, "IN_PROGRESS")} className="rounded-lg border border-zinc-200 px-2 py-1 text-[10px] font-black text-zinc-600 dark:border-white/10 dark:text-zinc-300">Start</button> : null}<button type="button" disabled={saving} onClick={() => updateAction(action, "COMPLETED")} className="rounded-lg border border-emerald-200 px-2 py-1 text-[10px] font-black text-emerald-700 dark:border-emerald-400/20 dark:text-emerald-300">Complete</button>{canManage ? <button type="button" disabled={saving} onClick={() => cancelAction(action)} className="rounded-lg border border-red-200 px-2 py-1 text-[10px] font-black text-red-600 dark:border-red-400/20 dark:text-red-300">Cancel</button> : null}</div> : null}
                        </div>
                      </div>
                    )) : <p className="rounded-xl border border-dashed border-zinc-200 p-4 text-center text-xs font-bold text-zinc-400 dark:border-white/10">No coaching actions yet.</p>}
                  </div>
                  {canManage && detail.status !== "COMPLETED" ? <form onSubmit={addAction} className="mt-3 grid gap-2 rounded-xl bg-zinc-50 p-3 dark:bg-white/[0.03] md:grid-cols-[1.2fr_1.4fr_.8fr_.7fr_auto]"><input value={actionForm.title} onChange={(event) => setActionForm((current) => ({ ...current, title: event.target.value }))} placeholder="Action title" className="rounded-lg border border-zinc-200 bg-white px-2.5 py-2 text-xs font-bold dark:border-white/10 dark:bg-zinc-900 dark:text-white" /><input value={actionForm.description} onChange={(event) => setActionForm((current) => ({ ...current, description: event.target.value }))} placeholder="Description" className="rounded-lg border border-zinc-200 bg-white px-2.5 py-2 text-xs dark:border-white/10 dark:bg-zinc-900 dark:text-white" /><input type="date" value={actionForm.dueDate} onChange={(event) => setActionForm((current) => ({ ...current, dueDate: event.target.value }))} className="rounded-lg border border-zinc-200 bg-white px-2.5 py-2 text-xs font-bold dark:border-white/10 dark:bg-zinc-900 dark:text-white" /><select value={actionForm.priority} onChange={(event) => setActionForm((current) => ({ ...current, priority: event.target.value }))} className="rounded-lg border border-zinc-200 bg-white px-2.5 py-2 text-xs font-bold dark:border-white/10 dark:bg-zinc-900 dark:text-white"><option>LOW</option><option>MEDIUM</option><option>HIGH</option><option>URGENT</option></select><button type="submit" disabled={saving || !actionForm.title.trim()} className="rounded-lg bg-amber-400 px-3 py-2 text-xs font-black text-zinc-950 disabled:opacity-50"><Plus size={14} /></button></form> : null}
                </section>
              ) : null}

              {detail?.id && detail.status !== "DRAFT" ? (
                <section className="mt-4 rounded-2xl border border-zinc-100 p-4 dark:border-white/10">
                  <div className="flex items-center gap-2"><MessageSquareText size={16} className="text-zinc-400" /><h3 className="text-sm font-black text-zinc-950 dark:text-white">Employee Acknowledgment</h3></div>
                  {detail.employeeAcknowledgedAt ? <div className="mt-3 rounded-xl bg-emerald-50 p-3 dark:bg-emerald-400/[0.06]"><p className="text-xs font-black text-emerald-700 dark:text-emerald-300">Acknowledged {formatDate(detail.employeeAcknowledgedAt)}</p><p className="mt-1 whitespace-pre-wrap text-xs text-zinc-600 dark:text-zinc-300">{detail.employeeComment || "No employee comment."}</p></div> : isOwnEmployee ? <div className="mt-3"><textarea rows={3} value={employeeComment} onChange={(event) => setEmployeeComment(event.target.value)} placeholder="Add your comment or acknowledgment…" className="w-full resize-y rounded-xl border border-zinc-200 bg-white px-3 py-2.5 text-xs dark:border-white/10 dark:bg-zinc-900 dark:text-white" /><button type="button" disabled={saving} onClick={acknowledge} className="mt-2 inline-flex items-center gap-2 rounded-xl bg-amber-400 px-3 py-2 text-xs font-black text-zinc-950"><Send size={14} /> Acknowledge review</button></div> : <p className="mt-3 text-xs font-bold text-zinc-400">Waiting for employee acknowledgment.</p>}
                </section>
              ) : null}

              {detail?.id && canManage ? <div className="mt-4 flex flex-wrap justify-end gap-2">{detail.status === "DRAFT" ? <button type="button" disabled={saving} onClick={() => runReviewAction("share")} className="rounded-xl bg-amber-400 px-4 py-2.5 text-xs font-black text-zinc-950">Share with employee</button> : null}{["SHARED", "IN_PROGRESS"].includes(detail.status) ? <button type="button" disabled={saving || openActions.length > 0} onClick={() => runReviewAction("complete")} className="rounded-xl bg-emerald-600 px-4 py-2.5 text-xs font-black text-white disabled:opacity-40" title={openActions.length ? "Complete or cancel open actions first" : "Complete review"}>Complete review</button> : null}</div> : null}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export function PerformanceReviewsPanel({ user, employees = [], selectedRange, employeeFilter = "all", departmentFilter = "all", refreshToken = 0 }) {
  const canManage = canManageReviews(user);
  const [summary, setSummary] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [editor, setEditor] = useState(null);
  const [nonce, setNonce] = useState(0);

  async function load() {
    if (!selectedRange?.start || !selectedRange?.end || selectedRange?.invalid) return;
    setLoading(true);
    setError("");
    const params = {
      start: selectedRange.start.toISOString(),
      end: selectedRange.end.toISOString(),
      employeeId: employeeFilter !== "all" ? employeeFilter : "",
      department: departmentFilter !== "all" ? departmentFilter : "",
    };
    try {
      const [summaryPayload, reviewsPayload] = await Promise.all([
        api.tasks.performanceReviewSummary(params),
        api.tasks.performanceReviews({ ...params, limit: 40 }),
      ]);
      setSummary(summaryPayload?.summary || null);
      setReviews(reviewsPayload?.reviews || []);
    } catch (err) {
      setError(getErrorMessage(err, "Unable to load performance reviews."));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, [selectedRange?.start?.getTime(), selectedRange?.end?.getTime(), selectedRange?.invalid, employeeFilter, departmentFilter, refreshToken, nonce]);

  function changed() {
    setNonce((value) => value + 1);
  }

  return (
    <>
      <Card className="overflow-hidden p-0">
        <div className="flex flex-col gap-2 border-b border-zinc-100 p-4 dark:border-white/10 sm:flex-row sm:items-center sm:justify-between">
          <div><p className="text-[11px] font-black uppercase tracking-[0.1em] text-amber-500">Reviews & Coaching</p><h2 className="mt-1 text-base font-black text-zinc-950 dark:text-white">Performance Reviews & Action Plans</h2><p className="mt-1 text-[11px] font-bold text-zinc-400">Turn scores, targets and alerts into documented coaching, follow-ups and accountable actions.</p></div>
          {canManage ? <button type="button" onClick={() => setEditor({ review: null, employeeId: employeeFilter !== "all" ? employeeFilter : employees[0]?.id || "" })} disabled={!employees.length} className="inline-flex items-center gap-2 rounded-xl bg-zinc-950 px-3 py-2 text-xs font-black text-white disabled:opacity-40 dark:bg-white dark:text-zinc-950"><Plus size={14} /> Start Review</button> : null}
        </div>
        {error ? <div className="p-4"><Notice type="error">{error}</Notice></div> : null}
        {loading && !summary ? <div className="h-32 animate-pulse bg-zinc-50 dark:bg-white/[0.03]" /> : (
          <>
            <div className="grid gap-3 p-4 sm:grid-cols-2 xl:grid-cols-5"><MiniKpi icon={CalendarClock} label="Reviews Due" value={summary?.reviewsDue || 0} /><MiniKpi icon={ListChecks} label="Open Actions" value={summary?.openActionPlans || 0} /><MiniKpi icon={AlertCircle} label="Overdue Actions" value={summary?.overdueActions || 0} /><MiniKpi icon={UserCheck} label="Need Follow-up" value={summary?.employeesNeedingFollowUp || 0} note="employees" /><MiniKpi icon={ClipboardCheck} label="Completed Reviews" value={summary?.completed || 0} /></div>
            <div className="border-t border-zinc-100 p-4 dark:border-white/10">
              <div className="mb-3 flex items-center justify-between"><h3 className="text-sm font-black text-zinc-950 dark:text-white">Review History</h3><span className="text-[10px] font-bold text-zinc-400">{reviews.length} in selected period</span></div>
              {reviews.length ? <div className="grid gap-2 md:grid-cols-2 xl:grid-cols-3">{reviews.slice(0, 12).map((review) => {
                const open = (review.actions || []).filter((action) => ["OPEN", "IN_PROGRESS"].includes(action.status)).length;
                const overdue = (review.actions || []).filter((action) => ["OPEN", "IN_PROGRESS"].includes(action.status) && action.dueDate && new Date(action.dueDate) < new Date()).length;
                return <button key={review.id} type="button" onClick={() => setEditor({ review, employeeId: review.employeeId })} className="rounded-2xl border border-zinc-100 p-3 text-left transition hover:-translate-y-0.5 hover:border-amber-200 hover:shadow-sm dark:border-white/10"><div className="flex items-start justify-between gap-2"><div className="min-w-0"><p className="truncate text-xs font-black text-zinc-950 dark:text-white">{review.employee?.name || review.employeeId}</p><p className="mt-0.5 truncate text-[10px] font-bold text-zinc-400">{review.title || REVIEW_TRIGGERS.find(([value]) => value === review.triggerType)?.[1] || review.triggerType}</p></div><Badge tone={reviewStatusTone(review.status)}>{reviewStatusLabel(review.status)}</Badge></div><div className="mt-3 grid grid-cols-3 gap-2 text-center text-[10px]"><div><p className="text-zinc-400">Score</p><p className="font-black text-zinc-900 dark:text-white">{review.snapshotScore ?? "—"}</p></div><div><p className="text-zinc-400">Actions</p><p className="font-black text-zinc-900 dark:text-white">{open}</p></div><div><p className="text-zinc-400">Overdue</p><p className={`font-black ${overdue ? "text-red-600" : "text-zinc-900 dark:text-white"}`}>{overdue}</p></div></div><p className="mt-2 text-[10px] font-bold text-zinc-400">Follow-up {formatDate(review.followUpAt)}</p></button>;
              })}</div> : <div className="rounded-2xl border border-dashed border-zinc-200 p-6 text-center text-xs font-bold text-zinc-400 dark:border-white/10">No reviews in this period yet.</div>}
            </div>
          </>
        )}
      </Card>
      {editor ? <ReviewModal review={editor.review} initialEmployeeId={editor.employeeId} employees={employees} selectedRange={selectedRange} user={user} onClose={() => setEditor(null)} onChanged={changed} /> : null}
    </>
  );
}

export function EmployeeReviewsSection({ user, employee, selectedRange }) {
  const canManage = canManageReviews(user);
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [editor, setEditor] = useState(null);
  const [nonce, setNonce] = useState(0);

  async function load() {
    if (!employee?.id || !selectedRange?.start || !selectedRange?.end || selectedRange?.invalid) return;
    setLoading(true);
    setError("");
    try {
      const payload = await api.tasks.performanceReviews({ employeeId: employee.id, start: selectedRange.start.toISOString(), end: selectedRange.end.toISOString(), limit: 20 });
      setReviews(payload?.reviews || []);
    } catch (err) {
      setError(getErrorMessage(err, "Unable to load review history."));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, [employee?.id, selectedRange?.start?.getTime(), selectedRange?.end?.getTime(), selectedRange?.invalid, nonce]);

  return (
    <>
      <section className="mt-4 rounded-2xl border border-zinc-100 p-4 dark:border-white/10">
        <div className="flex items-center justify-between gap-3"><div><h3 className="text-sm font-black text-zinc-950 dark:text-white">Reviews & Action Plans</h3><p className="mt-1 text-[11px] font-bold text-zinc-400">Coaching history for the selected performance period.</p></div>{canManage ? <button type="button" onClick={() => setEditor({ review: null, employeeId: employee.id })} className="rounded-xl border border-zinc-200 px-2.5 py-1.5 text-[10px] font-black text-zinc-700 hover:border-amber-300 dark:border-white/10 dark:text-zinc-200">Start review</button> : null}</div>
        {error ? <div className="mt-3"><Notice type="error">{error}</Notice></div> : null}
        {loading ? <div className="mt-3 h-20 animate-pulse rounded-xl bg-zinc-100 dark:bg-white/[0.05]" /> : reviews.length ? <div className="mt-3 space-y-2">{reviews.slice(0, 5).map((review) => <button key={review.id} type="button" onClick={() => setEditor({ review, employeeId: employee.id })} className="flex w-full items-center justify-between gap-3 rounded-xl border border-zinc-100 p-3 text-left hover:border-amber-200 dark:border-white/10"><div className="min-w-0"><p className="truncate text-xs font-black text-zinc-950 dark:text-white">{review.title || REVIEW_TRIGGERS.find(([value]) => value === review.triggerType)?.[1] || "Performance review"}</p><p className="mt-0.5 text-[10px] font-bold text-zinc-400">{formatDate(review.periodStart)} — {formatDate(review.periodEnd)} · {(review.actions || []).filter((action) => ["OPEN", "IN_PROGRESS"].includes(action.status)).length} open actions</p></div><Badge tone={reviewStatusTone(review.status)}>{reviewStatusLabel(review.status)}</Badge></button>)}</div> : <p className="mt-3 rounded-xl border border-dashed border-zinc-200 p-4 text-center text-xs font-bold text-zinc-400 dark:border-white/10">No reviews recorded for this period.</p>}
      </section>
      {editor ? <ReviewModal review={editor.review} initialEmployeeId={employee.id} employees={[employee]} selectedRange={selectedRange} user={user} onClose={() => setEditor(null)} onChanged={() => setNonce((value) => value + 1)} /> : null}
    </>
  );
}
'''

path.write_text(content)
print("FRONTEND_REVIEW_COMPONENT=PASS")
print("FRONTEND_REVIEW_MODAL=PASS")
print("FRONTEND_EMPLOYEE_REVIEW_DRAWER=PASS")
