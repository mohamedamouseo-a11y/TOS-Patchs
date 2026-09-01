#!/usr/bin/env python3
from pathlib import Path
import sys

repo = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS").resolve()

api_path = repo / "frontend/src/lib/api.js"
api = api_path.read_text()
anchor = '    teamPerformanceIntelligence: (params = {}) => request(`/api/tasks/reports/team-performance/intelligence${queryString(params)}`),\n'
if api.count(anchor) != 1:
    raise SystemExit(f"API_ANCHOR=FAIL count={api.count(anchor)}")
api_add = anchor + '''    teamPerformanceTargetsSummary: (params = {}) => request(`/api/tasks/reports/team-performance/targets/summary${queryString(params)}`),
    performanceTargets: (params = {}) => request(`/api/tasks/reports/team-performance/targets${queryString(params)}`),
    createPerformanceTarget: (payload = {}) => request("/api/tasks/reports/team-performance/targets", { method: "POST", body: JSON.stringify(payload || {}) }),
    bulkCreatePerformanceTargets: (payload = {}) => request("/api/tasks/reports/team-performance/targets/bulk", { method: "POST", body: JSON.stringify(payload || {}) }),
    updatePerformanceTarget: (targetId, payload = {}) => request(`/api/tasks/reports/team-performance/targets/${encodeURIComponent(targetId)}`, { method: "PATCH", body: JSON.stringify(payload || {}) }),
    deactivatePerformanceTarget: (targetId) => request(`/api/tasks/reports/team-performance/targets/${encodeURIComponent(targetId)}`, { method: "DELETE" }),
    copyPerformanceTarget: (targetId, payload = {}) => request(`/api/tasks/reports/team-performance/targets/${encodeURIComponent(targetId)}/copy`, { method: "POST", body: JSON.stringify(payload || {}) }),
'''
api_path.write_text(api.replace(anchor, api_add, 1))
print("FRONTEND_TARGET_API=PASS")

path = repo / "frontend/src/pages/TeamPerformanceDashboard.jsx"
text = path.read_text()

def replace_once(old, new, label):
    global text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}=FAIL count={count}")
    text = text.replace(old, new, 1)

replace_once('''  const [intelligenceError, setIntelligenceError] = useState("");

  const selectedRange = useMemo''', '''  const [intelligenceError, setIntelligenceError] = useState("");

  const [targetData, setTargetData] = useState(null);
  const [targetLoading, setTargetLoading] = useState(false);
  const [targetError, setTargetError] = useState("");
  const [targetManagerOpen, setTargetManagerOpen] = useState(false);
  const [targetList, setTargetList] = useState([]);
  const [targetSaving, setTargetSaving] = useState(false);
  const [targetBulkMode, setTargetBulkMode] = useState(false);
  const [targetForm, setTargetForm] = useState({ scopeType: "EMPLOYEE", employeeId: "", department: "", periodType: "MONTHLY", effectiveFrom: "", effectiveTo: "", targetScore: "85", targetCompletionRate: "90", targetCompletedTasks: "", targetLoggedHours: "", maxOverdueTasks: "2" });

  const selectedRange = useMemo''', "TARGET_STATE")

replace_once('''  const allEmployees = teamData?.byUser || [];
  const departments = useMemo''', '''  useEffect(() => {
    if (!selectedRange.start || !selectedRange.end || selectedRange.invalid) return;
    let ignore = false;
    async function loadTargets() {
      setTargetLoading(true);
      setTargetError("");
      try {
        const data = await api.tasks.teamPerformanceTargetsSummary({ start: selectedRange.start.toISOString(), end: selectedRange.end.toISOString(), employeeId: employeeFilter !== "all" ? employeeFilter : "", department: departmentFilter !== "all" ? departmentFilter : "" });
        if (!ignore) setTargetData(data);
      } catch (err) {
        if (!ignore) { setTargetData(null); setTargetError(getErrorMessage(err, "Unable to load performance targets.")); }
      } finally { if (!ignore) setTargetLoading(false); }
    }
    loadTargets();
    return () => { ignore = true; };
  }, [selectedRange.start?.getTime(), selectedRange.end?.getTime(), selectedRange.invalid, employeeFilter, departmentFilter, refreshNonce, realtimeRefreshVersion]);

  const allEmployees = teamData?.byUser || [];
  const departments = useMemo''', "TARGET_EFFECT")

replace_once('''  const selectedEmployee = allEmployees.find((employee) => employee.id === selectedEmployeeId) || null;

  function changeSort''', '''  const selectedEmployee = allEmployees.find((employee) => employee.id === selectedEmployeeId) || null;
  const targetByEmployee = useMemo(() => new Map((targetData?.rows || []).map((row) => [row.employeeId, row])), [targetData]);
  const selectedEmployeeTarget = selectedEmployee ? targetByEmployee.get(selectedEmployee.id) || null : null;
  const canManageTargets = ["SUPER_ADMIN", "ADMIN", "MANAGER", "PROJECT_MANAGER"].includes(String(user?.role || "").toUpperCase());

  function changeSort''', "TARGET_MAP")

replace_once('''  const periodLabel = selectedRange.start && selectedRange.end
    ? `${formatDate(selectedRange.start)} — ${formatDate(selectedRange.end)}`
    : "Choose a valid period";
''', r'''  function dateInputValue(date) {
    if (!date) return "";
    const value = new Date(date);
    return new Date(value.getTime() - value.getTimezoneOffset() * 60000).toISOString().slice(0, 10);
  }

  function targetNumber(value) {
    if (value === "" || value === null || value === undefined) return null;
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }

  async function openTargetManager() {
    if (!canManageTargets || !selectedRange.start || !selectedRange.end) return;
    setTargetManagerOpen(true);
    setTargetForm((current) => ({ ...current, employeeId: current.employeeId || filteredEmployees[0]?.id || allEmployees[0]?.id || "", department: current.department || departments[0] || "", periodType: preset === "week" ? "WEEKLY" : preset === "year" ? "YEARLY" : preset === "custom" ? "CUSTOM" : "MONTHLY", effectiveFrom: dateInputValue(selectedRange.start), effectiveTo: dateInputValue(selectedRange.end) }));
    try {
      const data = await api.tasks.performanceTargets({ start: selectedRange.start.toISOString(), end: selectedRange.end.toISOString() });
      setTargetList(data?.targets || []);
    } catch (err) { setToast({ type: "error", message: getErrorMessage(err, "Unable to load target history.") }); }
  }

  async function saveTarget(event) {
    event.preventDefault();
    setTargetSaving(true);
    try {
      const payload = { scopeType: targetForm.scopeType, employeeId: targetForm.scopeType === "EMPLOYEE" ? targetForm.employeeId : null, department: targetForm.scopeType === "DEPARTMENT" ? targetForm.department : null, periodType: targetForm.periodType, effectiveFrom: targetForm.effectiveFrom, effectiveTo: targetForm.effectiveTo, targetScore: targetNumber(targetForm.targetScore), targetCompletionRate: targetNumber(targetForm.targetCompletionRate), targetCompletedTasks: targetNumber(targetForm.targetCompletedTasks), targetLoggedHours: targetNumber(targetForm.targetLoggedHours), maxOverdueTasks: targetNumber(targetForm.maxOverdueTasks) };
      if (targetBulkMode && targetForm.scopeType === "EMPLOYEE") await api.tasks.bulkCreatePerformanceTargets({ employeeIds: filteredEmployees.map((employee) => employee.id), target: payload });
      else await api.tasks.createPerformanceTarget(payload);
      const data = await api.tasks.performanceTargets({ start: selectedRange.start.toISOString(), end: selectedRange.end.toISOString() });
      setTargetList(data?.targets || []);
      setRefreshNonce((value) => value + 1);
      setToast({ type: "success", message: targetBulkMode ? "Targets applied to filtered employees." : "Performance target saved." });
    } catch (err) { setToast({ type: "error", message: getErrorMessage(err, "Unable to save performance target.") }); }
    finally { setTargetSaving(false); }
  }

  async function deactivateTarget(targetId) {
    setTargetSaving(true);
    try { await api.tasks.deactivatePerformanceTarget(targetId); setTargetList((current) => current.map((item) => item.id === targetId ? { ...item, isActive: false } : item)); setRefreshNonce((value) => value + 1); }
    catch (err) { setToast({ type: "error", message: getErrorMessage(err, "Unable to deactivate target.") }); }
    finally { setTargetSaving(false); }
  }

  async function copyTarget(target) {
    setTargetSaving(true);
    try { await api.tasks.copyPerformanceTarget(target.id, { effectiveFrom: selectedRange.start.toISOString(), effectiveTo: selectedRange.end.toISOString(), periodType: targetForm.periodType }); setRefreshNonce((value) => value + 1); setToast({ type: "success", message: "Target copied to selected period." }); }
    catch (err) { setToast({ type: "error", message: getErrorMessage(err, "Unable to copy target.") }); }
    finally { setTargetSaving(false); }
  }

  const periodLabel = selectedRange.start && selectedRange.end
    ? `${formatDate(selectedRange.start)} — ${formatDate(selectedRange.end)}`
    : "Choose a valid period";
''', "TARGET_FUNCTIONS")

replace_once('''        actions={<Badge tone="success"><ShieldCheck size={14} /> Live data</Badge>}
      />''', '''        actions={<div className="flex items-center gap-2">{canManageTargets ? <button type="button" onClick={openTargetManager} className="rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-xs font-black text-amber-700 hover:bg-amber-100 dark:border-amber-400/20 dark:bg-amber-400/10 dark:text-amber-300">Manage Targets</button> : null}<Badge tone="success"><ShieldCheck size={14} /> Live data</Badge></div>}
      />''', "TARGET_BUTTON")

intelligence_anchor = '''      <Card className="overflow-hidden p-0">
        <div className="flex flex-col gap-2 border-b border-zinc-100 p-4 dark:border-white/10 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-[11px] font-black uppercase tracking-[0.1em] text-amber-500">Performance Intelligence</p>'''
target_section = '''      <Card className="overflow-hidden p-0">
        <div className="flex flex-col gap-2 border-b border-zinc-100 p-4 dark:border-white/10 sm:flex-row sm:items-center sm:justify-between"><div><p className="text-[11px] font-black uppercase tracking-[0.1em] text-amber-500">Goals & Targets</p><h2 className="mt-1 text-base font-black text-zinc-950 dark:text-white">Actual vs Target</h2><p className="mt-1 text-[11px] font-bold text-zinc-400">Target achievement is separate from the Phase 3 performance score. Employee targets override department targets.</p></div>{canManageTargets ? <button type="button" onClick={openTargetManager} className="rounded-xl border border-zinc-200 px-3 py-2 text-xs font-black text-zinc-700 hover:border-amber-300 dark:border-white/10 dark:text-zinc-200">Manage</button> : null}</div>
        {targetError ? <div className="p-4"><Notice type="error">{targetError}</Notice></div> : null}
        {targetLoading && !targetData ? <div className="h-24 animate-pulse bg-zinc-50 dark:bg-white/[0.03]" /> : <div className="grid gap-3 p-4 sm:grid-cols-2 xl:grid-cols-5"><KpiCard icon={CheckCircle2} label="On Target" value={targetData?.summary?.onTarget || 0} tone="green" /><KpiCard icon={TrendingDown} label="Behind Target" value={targetData?.summary?.behind || 0} tone="red" /><KpiCard icon={TrendingUp} label="Exceeded" value={targetData?.summary?.exceeded || 0} tone="gold" /><KpiCard icon={BarChart3} label="Avg Achievement" value={targetData?.summary?.averageAchievement != null ? `${targetData.summary.averageAchievement}%` : "—"} note={`${targetData?.summary?.configured || 0} configured employees`} /><KpiCard icon={BriefcaseBusiness} label="Departments On Target" value={`${targetData?.summary?.departmentsOnTarget || 0}/${targetData?.summary?.departmentsConfigured || 0}`} /></div>}
      </Card>

      <Card className="overflow-hidden p-0">
        <div className="flex flex-col gap-2 border-b border-zinc-100 p-4 dark:border-white/10 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-[11px] font-black uppercase tracking-[0.1em] text-amber-500">Performance Intelligence</p>'''
replace_once(intelligence_anchor, target_section, "TARGET_SUMMARY_UI")

replace_once('''                    <th className="px-3 py-3 text-right font-black"><button type="button" onClick={() => changeSort("score")}>Score</button></th>
                    <th className="px-3 py-3 text-right font-black"><button type="button" onClick={() => changeSort("completed")}>Completed</button></th>''', '''                    <th className="px-3 py-3 text-right font-black"><button type="button" onClick={() => changeSort("score")}>Score</button></th>
                    <th className="px-3 py-3 text-right font-black">Target</th>
                    <th className="px-3 py-3 text-right font-black"><button type="button" onClick={() => changeSort("completed")}>Completed</button></th>''', "TARGET_TABLE_HEADER")

replace_once('''                      <td className="px-3 py-3 text-right"><ScorePopover employee={employee} /></td>
                      <td className="px-3 py-3 text-right font-black text-zinc-900 dark:text-white">{employee.completedTasks}/{employee.totalTasks}</td>''', '''                      <td className="px-3 py-3 text-right"><ScorePopover employee={employee} /></td>
                      <td className="px-3 py-3 text-right">{targetByEmployee.get(employee.id)?.achievementPercent != null ? <div><p className="font-black text-zinc-900 dark:text-white">{targetByEmployee.get(employee.id).achievementPercent}%</p><p className="text-[10px] font-bold text-zinc-400">{targetByEmployee.get(employee.id).status}</p></div> : <span className="font-black text-zinc-400">—</span>}</td>
                      <td className="px-3 py-3 text-right font-black text-zinc-900 dark:text-white">{employee.completedTasks}/{employee.totalTasks}</td>''', "TARGET_TABLE_CELL")

replace_once('''                <section className="mt-4 rounded-2xl border border-zinc-100 p-4 dark:border-white/10">
                  <div className="flex items-center justify-between"><h3 className="text-sm font-black text-zinc-950 dark:text-white">Score Breakdown</h3>''', '''                <section className="mt-4 rounded-2xl border border-amber-100 bg-amber-50/30 p-4 dark:border-amber-400/15 dark:bg-amber-400/[0.035]"><div className="flex items-center justify-between gap-3"><div><h3 className="text-sm font-black text-zinc-950 dark:text-white">Goals & Targets</h3><p className="mt-1 text-[11px] font-bold text-zinc-400">{selectedEmployeeTarget?.source ? `${selectedEmployeeTarget.source.toLowerCase()} target` : "No target configured"}</p></div>{selectedEmployeeTarget?.achievementPercent != null ? <div className="text-right"><p className="text-2xl font-black text-amber-600 dark:text-amber-300">{selectedEmployeeTarget.achievementPercent}%</p><p className="text-[10px] font-black text-zinc-400">{selectedEmployeeTarget.status}</p></div> : null}</div>{selectedEmployeeTarget?.metrics?.length ? <div className="mt-3 overflow-x-auto"><table className="w-full min-w-[520px] text-[11px]"><thead className="text-zinc-400"><tr><th className="py-2 text-left">KPI</th><th className="py-2 text-right">Actual</th><th className="py-2 text-right">Target</th><th className="py-2 text-right">Gap</th><th className="py-2 text-right">Status</th></tr></thead><tbody>{selectedEmployeeTarget.metrics.map((metric) => <tr key={metric.key}><td className="py-2 font-black">{metric.key}</td><td className="py-2 text-right">{metric.actual ?? "—"}</td><td className="py-2 text-right">{metric.key === "Overdue" ? `≤ ${metric.target}` : metric.target}</td><td className="py-2 text-right font-black">{metric.gap ?? "—"}</td><td className="py-2 text-right font-black">{metric.status}</td></tr>)}</tbody></table></div> : <p className="mt-3 text-xs font-bold text-zinc-400">Assign an employee or department target to track actual vs target.</p>}</section>

                <section className="mt-4 rounded-2xl border border-zinc-100 p-4 dark:border-white/10">
                  <div className="flex items-center justify-between"><h3 className="text-sm font-black text-zinc-950 dark:text-white">Score Breakdown</h3>''', "TARGET_DRAWER")

modal_anchor = '''      {drawerOpen && selectedEmployee ? (
        <div className="fixed inset-0 z-50 flex justify-end"'''
modal = '''      {targetManagerOpen ? <div className="fixed inset-0 z-[60] grid place-items-center bg-black/55 p-3" role="dialog" aria-modal="true"><div className="max-h-[92vh] w-full max-w-4xl overflow-y-auto rounded-3xl bg-white shadow-2xl dark:bg-zinc-950"><div className="flex items-center justify-between border-b border-zinc-100 p-4 dark:border-white/10"><div><p className="text-[10px] font-black uppercase tracking-[0.1em] text-amber-500">Phase 6</p><h2 className="text-lg font-black text-zinc-950 dark:text-white">Goals & Target Management</h2></div><button type="button" onClick={() => setTargetManagerOpen(false)} className="rounded-xl p-2 text-zinc-400"><X size={20} /></button></div><form onSubmit={saveTarget} className="grid gap-4 p-4 lg:grid-cols-[1fr_.9fr]"><div className="space-y-3"><div className="grid gap-2 sm:grid-cols-2"><select value={targetForm.scopeType} onChange={(e) => setTargetForm((c) => ({ ...c, scopeType: e.target.value }))} className="rounded-xl border p-2 dark:bg-zinc-900"><option value="EMPLOYEE">Employee</option><option value="DEPARTMENT">Department</option></select><select value={targetForm.periodType} onChange={(e) => setTargetForm((c) => ({ ...c, periodType: e.target.value }))} className="rounded-xl border p-2 dark:bg-zinc-900"><option>WEEKLY</option><option>MONTHLY</option><option>QUARTERLY</option><option>YEARLY</option><option>CUSTOM</option></select></div>{targetForm.scopeType === "EMPLOYEE" ? <select value={targetForm.employeeId} onChange={(e) => setTargetForm((c) => ({ ...c, employeeId: e.target.value }))} className="w-full rounded-xl border p-2 dark:bg-zinc-900">{allEmployees.map((employee) => <option key={employee.id} value={employee.id}>{employee.name}</option>)}</select> : <select value={targetForm.department} onChange={(e) => setTargetForm((c) => ({ ...c, department: e.target.value }))} className="w-full rounded-xl border p-2 dark:bg-zinc-900">{departments.map((department) => <option key={department}>{department}</option>)}</select>}<div className="grid gap-2 sm:grid-cols-2"><input type="date" required value={targetForm.effectiveFrom} onChange={(e) => setTargetForm((c) => ({ ...c, effectiveFrom: e.target.value }))} className="rounded-xl border p-2 dark:bg-zinc-900" /><input type="date" required value={targetForm.effectiveTo} onChange={(e) => setTargetForm((c) => ({ ...c, effectiveTo: e.target.value }))} className="rounded-xl border p-2 dark:bg-zinc-900" /></div><div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-3">{[["targetScore","Target Score"],["targetCompletionRate","Completion %"],["targetCompletedTasks","Completed Tasks"],["targetLoggedHours","Logged Hours"],["maxOverdueTasks","Max Overdue"]].map(([key,label]) => <label key={key} className="text-xs font-black text-zinc-500">{label}<input type="number" min="0" max={key === "targetScore" || key === "targetCompletionRate" ? "100" : undefined} step={key === "targetLoggedHours" ? "0.1" : "1"} value={targetForm[key]} onChange={(e) => setTargetForm((c) => ({ ...c, [key]: e.target.value }))} className="mt-1 w-full rounded-xl border p-2 dark:bg-zinc-900" /></label>)}</div>{targetForm.scopeType === "EMPLOYEE" ? <label className="flex items-center gap-2 text-xs font-black"><input type="checkbox" checked={targetBulkMode} onChange={(e) => setTargetBulkMode(e.target.checked)} />Apply to all filtered employees ({filteredEmployees.length})</label> : null}<button type="submit" disabled={targetSaving || (targetBulkMode && !filteredEmployees.length)} className="w-full rounded-xl bg-gradient-to-l from-amber-500 to-yellow-300 px-4 py-3 text-xs font-black text-zinc-950 disabled:opacity-50">{targetSaving ? "Saving…" : targetBulkMode ? "Apply Targets" : "Save Target"}</button></div><div><h3 className="mb-2 text-sm font-black">Target History</h3><div className="max-h-[520px] space-y-2 overflow-y-auto">{targetList.map((target) => <div key={target.id} className={`rounded-2xl border p-3 ${target.isActive ? "" : "opacity-50"}`}><p className="text-xs font-black">{target.scopeType === "EMPLOYEE" ? allEmployees.find((e) => e.id === target.employeeId)?.name || "Employee target" : target.department}</p><p className="mt-1 text-[10px] text-zinc-400">{target.periodType} · {formatDate(target.effectiveFrom)} — {formatDate(target.effectiveTo)}</p><p className="mt-2 text-[10px]">Score {target.targetScore ?? "—"} · Completion {target.targetCompletionRate ?? "—"} · Tasks {target.targetCompletedTasks ?? "—"} · Hours {target.targetLoggedHours ?? "—"} · Overdue ≤ {target.maxOverdueTasks ?? "—"}</p>{target.isActive ? <div className="mt-2 flex gap-2"><button type="button" onClick={() => copyTarget(target)} className="rounded-lg border px-2 py-1 text-[10px] font-black">Copy</button><button type="button" onClick={() => deactivateTarget(target.id)} className="rounded-lg border border-red-200 px-2 py-1 text-[10px] font-black text-red-600">Deactivate</button></div> : null}</div>)}</div></div></form></div></div> : null}

      {drawerOpen && selectedEmployee ? (
        <div className="fixed inset-0 z-50 flex justify-end"'''
replace_once(modal_anchor, modal, "TARGET_MANAGER_MODAL")

path.write_text(text)
print("FRONTEND_TARGET_SUMMARY_UI=PASS")
print("FRONTEND_TARGET_MANAGER_UI=PASS")
print("FRONTEND_TARGET_DRAWER=PASS")
