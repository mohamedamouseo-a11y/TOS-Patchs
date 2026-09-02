#!/usr/bin/env python3
from pathlib import Path
import sys

repo = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
path = repo / "frontend/src/components/performance/ExecutiveCommandCenter.jsx"
if path.exists():
    raise SystemExit("Phase 12 component already exists")
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(r'''import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  BarChart3,
  BriefcaseBusiness,
  CheckCircle2,
  Gauge,
  GraduationCap,
  RefreshCw,
  ShieldCheck,
  Sparkles,
  Target,
  UsersRound,
} from "lucide-react";
import { Badge, Card, Notice } from "../ui/Primitives";
import { api } from "../../lib/api";
import { getErrorMessage } from "../../lib/errors";

const ADMIN_ROLES = new Set(["SUPER_ADMIN", "ADMIN"]);
const HORIZONS = [7, 14, 30];

function Kpi({ icon: Icon, label, value, note, tone = "neutral" }) {
  const toneClass = tone === "danger"
    ? "border-red-100 bg-red-50/60 dark:border-red-400/15 dark:bg-red-400/[0.05]"
    : tone === "warning"
      ? "border-orange-100 bg-orange-50/60 dark:border-orange-400/15 dark:bg-orange-400/[0.05]"
      : tone === "success"
        ? "border-emerald-100 bg-emerald-50/60 dark:border-emerald-400/15 dark:bg-emerald-400/[0.05]"
        : tone === "gold"
          ? "border-amber-100 bg-amber-50/60 dark:border-amber-400/15 dark:bg-amber-400/[0.05]"
          : "border-zinc-100 bg-zinc-50/60 dark:border-white/10 dark:bg-white/[0.025]";
  return (
    <div className={`rounded-2xl border p-3 ${toneClass}`}>
      <div className="flex items-center justify-between gap-2">
        <p className="text-[10px] font-black uppercase tracking-[0.08em] text-zinc-400">{label}</p>
        <Icon size={15} className="text-zinc-400" />
      </div>
      <p className="mt-2 text-2xl font-black text-zinc-950 dark:text-white">{value}</p>
      {note ? <p className="mt-1 text-[10px] font-bold text-zinc-400">{note}</p> : null}
    </div>
  );
}

function severityTone(severity) {
  if (severity === "critical") return "danger";
  if (severity === "warning") return "warning";
  if (severity === "info") return "blue";
  return "neutral";
}

function severityClasses(severity) {
  if (severity === "critical") return "border-red-200 bg-red-50/70 dark:border-red-400/20 dark:bg-red-400/[0.055]";
  if (severity === "warning") return "border-orange-200 bg-orange-50/70 dark:border-orange-400/20 dark:bg-orange-400/[0.055]";
  return "border-zinc-100 bg-zinc-50/70 dark:border-white/10 dark:bg-white/[0.025]";
}

function DomainCard({ title, icon: Icon, children }) {
  return (
    <div className="rounded-2xl border border-zinc-100 p-3 dark:border-white/10">
      <div className="flex items-center gap-2">
        <Icon size={14} className="text-amber-500" />
        <p className="text-[10px] font-black uppercase tracking-[0.08em] text-zinc-400">{title}</p>
      </div>
      <div className="mt-2 space-y-1 text-[11px] font-bold text-zinc-600 dark:text-zinc-300">{children}</div>
    </div>
  );
}

export function ExecutiveCommandCenterPanel({
  user,
  selectedRange,
  employeeFilter = "all",
  departmentFilter = "all",
  refreshToken = "",
  onOpenEmployee = null,
}) {
  const role = String(user?.role || "").toUpperCase();
  const canView = ADMIN_ROLES.has(role);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [horizonDays, setHorizonDays] = useState(14);
  const [localRefresh, setLocalRefresh] = useState(0);

  async function load() {
    if (!canView || !selectedRange?.start || !selectedRange?.end || selectedRange?.invalid) return;
    setLoading(true);
    setError("");
    try {
      const result = await api.tasks.executiveCommandCenter({
        start: selectedRange.start.toISOString(),
        end: selectedRange.end.toISOString(),
        horizonDays,
        employeeId: employeeFilter !== "all" ? employeeFilter : "",
        department: departmentFilter !== "all" ? departmentFilter : "",
      });
      setData(result);
    } catch (err) {
      setData(null);
      setError(getErrorMessage(err, "Unable to load the Executive Workforce Command Center."));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [canView, selectedRange?.start?.getTime?.(), selectedRange?.end?.getTime?.(), selectedRange?.invalid, employeeFilter, departmentFilter, refreshToken, localRefresh, horizonDays]);

  const summary = data?.summary || {};
  const attentionEmployees = Number(summary.atRiskEmployees || 0) + Number(summary.needsAttentionEmployees || 0);
  const topPriorities = useMemo(() => (data?.priorities || []).slice(0, 10), [data]);
  const domains = data?.domains || {};

  if (!canView) return null;

  return (
    <Card className="overflow-hidden p-0">
      <div className="flex flex-col gap-3 border-b border-zinc-100 p-4 dark:border-white/10 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-[11px] font-black uppercase tracking-[0.1em] text-amber-500">Executive Workforce Command Center</p>
            <Badge tone="blue">Phase 12</Badge>
            <Badge tone="success"><ShieldCheck size={12} /> Admin only</Badge>
          </div>
          <h2 className="mt-1 text-lg font-black text-zinc-950 dark:text-white">Company Workforce Decision View</h2>
          <p className="mt-1 max-w-4xl text-[11px] font-bold leading-5 text-zinc-400">One executive view across performance, targets, coaching, capacity, skills, talent, succession and recognition. It aggregates existing signals only — no new employee score and no automated HR decision.</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <div className="flex rounded-xl border border-zinc-200 p-1 dark:border-white/10">
            {HORIZONS.map((days) => (
              <button key={days} type="button" onClick={() => setHorizonDays(days)} className={`rounded-lg px-2.5 py-1.5 text-[10px] font-black ${horizonDays === days ? "bg-zinc-950 text-white dark:bg-white dark:text-zinc-950" : "text-zinc-500"}`}>{days}d</button>
            ))}
          </div>
          <button type="button" onClick={() => setLocalRefresh((value) => value + 1)} className="rounded-xl border border-zinc-200 p-2 text-zinc-500 dark:border-white/10" aria-label="Refresh executive command center"><RefreshCw size={16} className={loading ? "animate-spin" : ""} /></button>
        </div>
      </div>

      {error ? <div className="p-4"><Notice type="error">{error}</Notice></div> : null}
      {loading && !data ? <div className="h-64 animate-pulse bg-zinc-50 dark:bg-white/[0.025]" /> : data ? (
        <>
          <div className="grid gap-3 p-4 sm:grid-cols-2 xl:grid-cols-5">
            <Kpi icon={BarChart3} label="Avg Performance" value={summary.averagePerformanceScore ?? "—"} note={`${summary.employeeCount || 0} employees in scope`} tone="gold" />
            <Kpi icon={AlertTriangle} label="Needs Attention" value={attentionEmployees} note={`${summary.atRiskEmployees || 0} at risk · ${summary.needsAttentionEmployees || 0} needs attention`} tone={attentionEmployees ? "danger" : "success"} />
            <Kpi icon={Gauge} label="Critical Capacity" value={summary.criticalCapacityEmployees || 0} note={`${summary.highCapacityEmployees || 0} additional high risk · ${horizonDays}d horizon`} tone={Number(summary.criticalCapacityEmployees || 0) ? "danger" : "success"} />
            <Kpi icon={GraduationCap} label="Critical Skill Gaps" value={summary.criticalSkillGaps || 0} note={summary.overallSkillCoveragePercent == null ? "Coverage not configured" : `${summary.overallSkillCoveragePercent}% skill coverage`} tone={Number(summary.criticalSkillGaps || 0) ? "warning" : "success"} />
            <Kpi icon={BriefcaseBusiness} label="Succession Gaps" value={summary.uncoveredCriticalRoles || 0} note={`${summary.readyNowCandidates || 0} ready-now candidates`} tone={Number(summary.uncoveredCriticalRoles || 0) ? "warning" : "success"} />
          </div>

          <div className="grid gap-4 border-t border-zinc-100 p-4 dark:border-white/10 xl:grid-cols-[.8fr_1.2fr]">
            <section>
              <div className="flex items-center justify-between gap-2">
                <div><h3 className="text-sm font-black text-zinc-950 dark:text-white">Executive Brief</h3><p className="mt-1 text-[10px] font-bold text-zinc-400">Transparent summary of existing Phase 3–11 signals.</p></div>
                <div className="flex gap-1"><Badge tone={Number(summary.criticalPriorities || 0) ? "danger" : "success"}>{summary.criticalPriorities || 0} critical</Badge><Badge tone={Number(summary.warningPriorities || 0) ? "warning" : "neutral"}>{summary.warningPriorities || 0} warnings</Badge></div>
              </div>
              <div className="mt-3 space-y-2">
                {(data.brief || []).map((line, index) => (
                  <div key={`${line}-${index}`} className="flex gap-2 rounded-xl border border-zinc-100 p-2.5 dark:border-white/10">
                    <Sparkles size={14} className="mt-0.5 shrink-0 text-amber-500" />
                    <p className="text-[11px] font-bold leading-5 text-zinc-700 dark:text-zinc-300">{line}</p>
                  </div>
                ))}
              </div>
              <div className="mt-3 grid grid-cols-2 gap-2">
                <div className="rounded-xl bg-zinc-50 p-2.5 dark:bg-white/[0.03]"><p className="text-[10px] font-black text-zinc-400">Pending recognition</p><p className="mt-1 text-lg font-black">{summary.pendingRecognitionDecisions || 0}</p></div>
                <div className="rounded-xl bg-zinc-50 p-2.5 dark:bg-white/[0.03]"><p className="text-[10px] font-black text-zinc-400">Overdue coaching</p><p className="mt-1 text-lg font-black">{Number(summary.overdueReviewFollowUps || 0) + Number(summary.overdueReviewActions || 0)}</p></div>
              </div>
            </section>

            <section>
              <div className="mb-3 flex items-center justify-between gap-2">
                <div><h3 className="text-sm font-black text-zinc-950 dark:text-white">Executive Priority Queue</h3><p className="mt-1 text-[10px] font-bold text-zinc-400">Severity ordering only — no hidden composite risk score.</p></div>
                <Badge>{data.priorities?.length || 0} signals</Badge>
              </div>
              {topPriorities.length ? (
                <div className="grid gap-2 md:grid-cols-2">
                  {topPriorities.map((item) => (
                    <button key={item.id} type="button" onClick={() => item.employeeId ? onOpenEmployee?.(item.employeeId) : undefined} disabled={!item.employeeId} className={`rounded-2xl border p-3 text-left ${severityClasses(item.severity)} ${item.employeeId ? "transition hover:-translate-y-0.5 hover:shadow-sm" : "cursor-default"}`}>
                      <div className="flex items-start justify-between gap-2">
                        <div className="min-w-0"><p className="text-xs font-black text-zinc-950 dark:text-white">{item.title}</p><p className="mt-1 text-[10px] font-black text-zinc-400">{item.domain} · {item.source || "TOS"}</p></div>
                        <Badge tone={severityTone(item.severity)}>{item.severity}</Badge>
                      </div>
                      {item.detail ? <p className="mt-2 text-[11px] leading-5 text-zinc-600 dark:text-zinc-300">{item.detail}</p> : null}
                      {item.suggestedAction ? <p className="mt-2 text-[10px] font-bold text-zinc-400">Next review: {item.suggestedAction}</p> : null}
                    </button>
                  ))}
                </div>
              ) : <div className="rounded-2xl border border-dashed border-zinc-200 p-6 text-center text-xs font-bold text-zinc-400 dark:border-white/10">No material executive priority is surfaced for the selected scope.</div>}
            </section>
          </div>

          <div className="border-t border-zinc-100 p-4 dark:border-white/10">
            <div className="mb-3"><h3 className="text-sm font-black text-zinc-950 dark:text-white">Decision Domains</h3><p className="mt-1 text-[10px] font-bold text-zinc-400">Each domain keeps its original methodology. Phase 12 does not blend them into a replacement score.</p></div>
            <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
              <DomainCard title="Performance" icon={BarChart3}><p>Average: <b>{domains.performance?.averageScore ?? "—"}</b></p><p>At risk: <b>{domains.performance?.atRisk || 0}</b> · Attention: <b>{domains.performance?.needsAttention || 0}</b></p></DomainCard>
              <DomainCard title="Targets" icon={Target}><p>On target: <b>{domains.targets?.onTarget || 0}</b> · Behind: <b>{domains.targets?.behind || 0}</b></p><p>Avg achievement: <b>{domains.targets?.averageAchievement == null ? "—" : `${domains.targets.averageAchievement}%`}</b></p></DomainCard>
              <DomainCard title="Reviews" icon={CheckCircle2}><p>Open: <b>{domains.reviews?.open || 0}</b></p><p>Overdue follow-ups/actions: <b>{Number(domains.reviews?.overdueFollowUps || 0) + Number(domains.reviews?.overdueActions || 0)}</b></p></DomainCard>
              <DomainCard title="Capacity" icon={Gauge}><p>Utilization: <b>{domains.workforce?.teamUtilizationPercent == null ? "—" : `${domains.workforce.teamUtilizationPercent}%`}</b></p><p>Critical/High: <b>{domains.workforce?.critical || 0}/{domains.workforce?.high || 0}</b></p></DomainCard>
              <DomainCard title="Skills" icon={GraduationCap}><p>Coverage: <b>{domains.skills?.coveragePercent == null ? "—" : `${domains.skills.coveragePercent}%`}</b></p><p>Critical gaps: <b>{domains.skills?.criticalGaps || 0}</b> · Active plans: <b>{domains.skills?.activePlans || 0}</b></p></DomainCard>
              <DomainCard title="Talent & Succession" icon={BriefcaseBusiness}><p>High potential: <b>{domains.talent?.highPotentialEmployees || 0}</b> · Ready now: <b>{domains.talent?.readyNowCandidates || 0}</b></p><p>Uncovered critical roles: <b>{domains.talent?.uncoveredCriticalRoles || 0}</b></p></DomainCard>
              <DomainCard title="Recognition" icon={Sparkles}><p>Open cycles: <b>{domains.recognition?.openCycles || 0}</b> · Pending: <b>{domains.recognition?.pendingNominations || 0}</b></p><p>Published: <b>{domains.recognition?.publishedRecognitions || 0}</b></p></DomainCard>
              <DomainCard title="Workforce Scope" icon={UsersRound}><p>Employees: <b>{summary.employeeCount || 0}</b></p><p>No Activity: <b>{summary.noActivityEmployees || 0}</b> · Behind targets: <b>{summary.targetBehindEmployees || 0}</b></p></DomainCard>
            </div>
          </div>

          <div className="border-t border-zinc-100 p-4 dark:border-white/10">
            <div className="mb-3 flex items-center justify-between gap-2"><div><h3 className="text-sm font-black text-zinc-950 dark:text-white">Department Health Signals</h3><p className="mt-1 text-[10px] font-bold text-zinc-400">Counts are source signals, not a department score.</p></div><Badge>{data.departments?.length || 0} departments</Badge></div>
            <div className="hidden overflow-x-auto md:block">
              <table className="w-full min-w-[900px] text-[11px]">
                <thead className="text-zinc-400"><tr><th className="py-2 text-left">Department</th><th className="py-2 text-right">Avg Score</th><th className="py-2 text-right">Attention</th><th className="py-2 text-right">Behind Target</th><th className="py-2 text-right">Capacity Risk</th><th className="py-2 text-right">Critical Gaps</th><th className="py-2 text-right">Succession Gaps</th><th className="py-2 text-right">Overdue Coaching</th></tr></thead>
                <tbody className="divide-y divide-zinc-100 dark:divide-white/10">
                  {(data.departments || []).map((row) => (
                    <tr key={row.department}><td className="py-2.5 font-black text-zinc-950 dark:text-white">{row.department}</td><td className="py-2.5 text-right font-black">{row.averagePerformanceScore ?? "—"}</td><td className="py-2.5 text-right">{Number(row.atRisk || 0) + Number(row.needsAttention || 0)}</td><td className="py-2.5 text-right">{row.targetBehind || 0}</td><td className="py-2.5 text-right">{row.capacityCriticalHigh || 0}</td><td className="py-2.5 text-right">{row.criticalSkillGaps || 0}</td><td className="py-2.5 text-right">{row.successionGaps || 0}</td><td className="py-2.5 text-right">{row.overdueReviewActions || 0}</td></tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="grid gap-2 md:hidden">
              {(data.departments || []).map((row) => (
                <div key={row.department} className="rounded-2xl border border-zinc-100 p-3 dark:border-white/10"><div className="flex items-center justify-between"><p className="text-xs font-black">{row.department}</p><p className="text-lg font-black">{row.averagePerformanceScore ?? "—"}</p></div><div className="mt-2 grid grid-cols-3 gap-2 text-center text-[10px]"><div><p className="text-zinc-400">Attention</p><p className="font-black">{Number(row.atRisk || 0) + Number(row.needsAttention || 0)}</p></div><div><p className="text-zinc-400">Capacity</p><p className="font-black">{row.capacityCriticalHigh || 0}</p></div><div><p className="text-zinc-400">Skills</p><p className="font-black">{row.criticalSkillGaps || 0}</p></div></div></div>
              ))}
            </div>
          </div>
        </>
      ) : null}
    </Card>
  );
}

export default ExecutiveCommandCenterPanel;
''')
print("FRONTEND_EXECUTIVE_COMPONENT=PASS")
