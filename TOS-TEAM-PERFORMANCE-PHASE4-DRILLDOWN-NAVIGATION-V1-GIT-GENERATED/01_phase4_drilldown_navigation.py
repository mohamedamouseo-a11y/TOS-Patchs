#!/usr/bin/env python3
from pathlib import Path

ROOT = Path('/var/www/TOS')
DASHBOARD = ROOT / 'frontend/src/pages/TeamPerformanceDashboard.jsx'
NAVIGATOR = ROOT / 'frontend/src/components/performance/PerformanceDrilldownNavigator.jsx'


def fail(message: str):
    raise SystemExit(f'PHASE4 DRILLDOWN PATCH ERROR: {message}')


def insert_after(text: str, anchor: str, addition: str, label: str) -> str:
    if addition.strip() in text:
        return text
    if anchor not in text:
        fail(f'missing anchor: {label}')
    return text.replace(anchor, anchor + addition, 1)


text = DASHBOARD.read_text(encoding='utf-8')
original = text

for marker in [
    'ManagementSummary',
    'ExecutiveCommandCenterPanel',
    'PerformanceDisclosure',
    'ArchivedPerformanceMembers',
    'onOpenTask = null',
]:
    if marker not in text:
        fail(f'expected Team Performance marker missing: {marker}')

import_anchor = 'import { ManagementSummary } from "../components/performance/ManagementSummary";\n'
text = insert_after(
    text,
    import_anchor,
    'import { PerformanceDrilldownNavigator } from "../components/performance/PerformanceDrilldownNavigator";\n',
    'ManagementSummary import',
)

anchor = '''      <ManagementSummary\n        employees={filteredEmployees}\n        targetSummary={targetData?.summary || null}\n        periodLabel={periodLabel}\n        onOpenEmployee={openEmployee}\n      />\n\n      <ExecutiveCommandCenterPanel'''
replacement = '''      <ManagementSummary\n        employees={filteredEmployees}\n        targetSummary={targetData?.summary || null}\n        periodLabel={periodLabel}\n        onOpenEmployee={openEmployee}\n      />\n\n      <PerformanceDisclosure\n        id="phase4-drilldown-disclosure"\n        eyebrow="Drill-down & Navigation"\n        title="Company → Department → Employee → Task"\n        description="Navigate the current filtered scope without adding another reporting screen."\n        summary={`${filteredEmployees.length} employees in scope`}\n      >\n        <PerformanceDrilldownNavigator\n          employees={filteredEmployees}\n          selectedRange={selectedRange}\n          onOpenEmployee={openEmployee}\n          onOpenTask={onOpenTask}\n        />\n      </PerformanceDisclosure>\n\n      <ExecutiveCommandCenterPanel'''

if '<PerformanceDrilldownNavigator' not in text:
    if anchor not in text:
        fail('Management Summary / Executive Command Center anchor missing')
    text = text.replace(anchor, replacement, 1)

if text == original:
    fail('dashboard was not changed')
DASHBOARD.write_text(text, encoding='utf-8')

NAVIGATOR.parent.mkdir(parents=True, exist_ok=True)
NAVIGATOR.write_text(r'''import { useEffect, useMemo, useState } from "react";
import {
  ArrowLeft,
  Building2,
  ChevronLeft,
  ChevronRight,
  ListChecks,
  Search,
  UserRound,
  UsersRound,
} from "lucide-react";
import { api } from "../../lib/api";
import { getErrorMessage } from "../../lib/errors";

const DEPARTMENT_PAGE_SIZE = 6;
const EMPLOYEE_PAGE_SIZE = 8;
const TASK_PAGE_SIZE = 6;

function normalize(value = "") {
  return String(value || "").trim().toLowerCase();
}

function departmentName(employee) {
  return String(employee?.department || "").trim() || "No department";
}

function formatHours(value) {
  const hours = Number(value || 0);
  if (!Number.isFinite(hours) || hours <= 0) return "0h";
  if (hours < 1) return `${Math.round(hours * 60)}m`;
  return `${Math.round(hours * 10) / 10}h`;
}

function formatDate(value) {
  if (!value) return "—";
  try {
    return new Intl.DateTimeFormat("en-GB", { day: "2-digit", month: "short", year: "numeric" }).format(new Date(value));
  } catch {
    return "—";
  }
}

function scoreTone(score) {
  if (score == null) return "text-zinc-400";
  if (score >= 85) return "text-emerald-600 dark:text-emerald-300";
  if (score >= 70) return "text-amber-600 dark:text-amber-300";
  if (score >= 50) return "text-orange-600 dark:text-orange-300";
  return "text-red-600 dark:text-red-300";
}

function statusTone(status) {
  if (status === "Excellent") return "bg-emerald-50 text-emerald-700 dark:bg-emerald-400/10 dark:text-emerald-300";
  if (status === "On Track") return "bg-amber-50 text-amber-700 dark:bg-amber-400/10 dark:text-amber-300";
  if (status === "Needs Attention") return "bg-orange-50 text-orange-700 dark:bg-orange-400/10 dark:text-orange-300";
  if (status === "At Risk") return "bg-red-50 text-red-700 dark:bg-red-400/10 dark:text-red-300";
  return "bg-zinc-100 text-zinc-500 dark:bg-white/[0.06] dark:text-zinc-300";
}

function clampPage(page, totalItems, pageSize) {
  const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));
  return Math.min(Math.max(1, page), totalPages);
}

function PageControls({ page, totalItems, pageSize, onChange }) {
  const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));
  if (totalPages <= 1) return null;
  return (
    <div className="flex items-center justify-between gap-3 border-t border-zinc-100 pt-3 dark:border-white/10">
      <p className="text-[10px] font-bold text-zinc-400">Page {page} of {totalPages}</p>
      <div className="flex items-center gap-1.5">
        <button type="button" onClick={() => onChange(Math.max(1, page - 1))} disabled={page <= 1} className="grid h-8 w-8 place-items-center rounded-lg border border-zinc-200 text-zinc-500 disabled:opacity-35 dark:border-white/10 dark:text-zinc-300" aria-label="Previous page"><ChevronLeft size={15} /></button>
        <button type="button" onClick={() => onChange(Math.min(totalPages, page + 1))} disabled={page >= totalPages} className="grid h-8 w-8 place-items-center rounded-lg border border-zinc-200 text-zinc-500 disabled:opacity-35 dark:border-white/10 dark:text-zinc-300" aria-label="Next page"><ChevronRight size={15} /></button>
      </div>
    </div>
  );
}

function Breadcrumb({ level, department, employee, onCompany, onDepartment }) {
  return (
    <div className="flex flex-wrap items-center gap-1.5 text-[10px] font-black">
      <button type="button" onClick={onCompany} className={`rounded-full px-2.5 py-1 ${level === "company" ? "bg-zinc-950 text-white dark:bg-white dark:text-zinc-950" : "bg-zinc-100 text-zinc-500 hover:text-amber-700 dark:bg-white/[0.06] dark:text-zinc-300"}`}>Company</button>
      {department ? <><ChevronRight size={12} className="text-zinc-300" /><button type="button" onClick={onDepartment} className={`rounded-full px-2.5 py-1 ${level === "department" ? "bg-zinc-950 text-white dark:bg-white dark:text-zinc-950" : "bg-zinc-100 text-zinc-500 hover:text-amber-700 dark:bg-white/[0.06] dark:text-zinc-300"}`}>{department}</button></> : null}
      {employee ? <><ChevronRight size={12} className="text-zinc-300" /><span className="rounded-full bg-amber-100 px-2.5 py-1 text-amber-700 dark:bg-amber-400/10 dark:text-amber-300">{employee.name}</span><ChevronRight size={12} className="text-zinc-300" /><span className="rounded-full bg-zinc-100 px-2.5 py-1 text-zinc-500 dark:bg-white/[0.06] dark:text-zinc-300">Tasks</span></> : null}
    </div>
  );
}

export function PerformanceDrilldownNavigator({ employees = [], selectedRange = null, onOpenEmployee, onOpenTask }) {
  const activeEmployees = useMemo(() => (employees || []).filter((employee) => employee?.accountStatus !== "DISABLED" && employee?.accountStatus !== "PENDING"), [employees]);
  const [level, setLevel] = useState("company");
  const [selectedDepartment, setSelectedDepartment] = useState("");
  const [selectedEmployeeId, setSelectedEmployeeId] = useState("");
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(1);
  const [tasks, setTasks] = useState([]);
  const [taskLoading, setTaskLoading] = useState(false);
  const [taskError, setTaskError] = useState("");

  const selectedEmployee = useMemo(() => activeEmployees.find((employee) => employee.id === selectedEmployeeId) || null, [activeEmployees, selectedEmployeeId]);

  const departments = useMemo(() => {
    const grouped = new Map();
    activeEmployees.forEach((employee) => {
      const name = departmentName(employee);
      const current = grouped.get(name) || { name, employees: 0, scored: 0, scoreTotal: 0, overdue: 0, attention: 0 };
      current.employees += 1;
      if (employee.performanceScore != null) {
        current.scored += 1;
        current.scoreTotal += Number(employee.performanceScore || 0);
      }
      current.overdue += Number(employee.overdueTasks || 0);
      if (["At Risk", "Needs Attention"].includes(employee.status)) current.attention += 1;
      grouped.set(name, current);
    });
    return [...grouped.values()].map((item) => ({ ...item, avgScore: item.scored ? Math.round((item.scoreTotal / item.scored) * 10) / 10 : null })).sort((a, b) => a.name.localeCompare(b.name));
  }, [activeEmployees]);

  useEffect(() => {
    if (selectedDepartment && !activeEmployees.some((employee) => departmentName(employee) === selectedDepartment)) {
      setLevel("company");
      setSelectedDepartment("");
      setSelectedEmployeeId("");
      setQuery("");
      setPage(1);
    }
  }, [activeEmployees, selectedDepartment]);

  useEffect(() => {
    if (selectedEmployeeId && !activeEmployees.some((employee) => employee.id === selectedEmployeeId)) {
      setLevel(selectedDepartment ? "department" : "company");
      setSelectedEmployeeId("");
      setTasks([]);
      setTaskError("");
      setQuery("");
      setPage(1);
    }
  }, [activeEmployees, selectedDepartment, selectedEmployeeId]);

  useEffect(() => {
    if (level !== "employee" || !selectedEmployeeId || !selectedRange?.start || !selectedRange?.end || selectedRange?.invalid) {
      if (level !== "employee") {
        setTasks([]);
        setTaskError("");
        setTaskLoading(false);
      }
      return undefined;
    }
    let ignore = false;
    async function loadTasks() {
      setTaskLoading(true);
      setTaskError("");
      try {
        const payload = await api.tasks.userDashboard({
          userId: selectedEmployeeId,
          start: selectedRange.start.toISOString(),
          end: selectedRange.end.toISOString(),
        });
        if (!ignore) setTasks(payload?.tasks || []);
      } catch (error) {
        if (!ignore) {
          setTasks([]);
          setTaskError(getErrorMessage(error, "Unable to load employee tasks."));
        }
      } finally {
        if (!ignore) setTaskLoading(false);
      }
    }
    loadTasks();
    return () => { ignore = true; };
  }, [level, selectedEmployeeId, selectedRange?.start?.getTime?.(), selectedRange?.end?.getTime?.(), selectedRange?.invalid]);

  function resetSearch() {
    setQuery("");
    setPage(1);
  }

  function goCompany() {
    setLevel("company");
    setSelectedDepartment("");
    setSelectedEmployeeId("");
    setTasks([]);
    setTaskError("");
    resetSearch();
  }

  function goDepartment(name = selectedDepartment) {
    if (!name) return goCompany();
    setSelectedDepartment(name);
    setSelectedEmployeeId("");
    setTasks([]);
    setTaskError("");
    setLevel("department");
    resetSearch();
  }

  function goEmployee(employee) {
    if (!employee) return;
    setSelectedDepartment(departmentName(employee));
    setSelectedEmployeeId(employee.id);
    setLevel("employee");
    resetSearch();
  }

  const normalizedQuery = normalize(query);

  const filteredDepartments = useMemo(() => departments.filter((item) => !normalizedQuery || normalize(item.name).includes(normalizedQuery)), [departments, normalizedQuery]);
  const departmentPage = clampPage(page, filteredDepartments.length, DEPARTMENT_PAGE_SIZE);
  const visibleDepartments = filteredDepartments.slice((departmentPage - 1) * DEPARTMENT_PAGE_SIZE, departmentPage * DEPARTMENT_PAGE_SIZE);

  const departmentEmployees = useMemo(() => activeEmployees.filter((employee) => departmentName(employee) === selectedDepartment), [activeEmployees, selectedDepartment]);
  const filteredDepartmentEmployees = useMemo(() => departmentEmployees.filter((employee) => {
    if (!normalizedQuery) return true;
    return normalize(`${employee.name || ""} ${employee.jobTitle || ""} ${employee.status || ""}`).includes(normalizedQuery);
  }), [departmentEmployees, normalizedQuery]);
  const employeePage = clampPage(page, filteredDepartmentEmployees.length, EMPLOYEE_PAGE_SIZE);
  const visibleDepartmentEmployees = filteredDepartmentEmployees.slice((employeePage - 1) * EMPLOYEE_PAGE_SIZE, employeePage * EMPLOYEE_PAGE_SIZE);

  const filteredTasks = useMemo(() => tasks.filter((task) => {
    if (!normalizedQuery) return true;
    return normalize(`${task.title || ""} ${task.project?.name || task.projectName || ""} ${task.status || ""} ${task.priority || ""}`).includes(normalizedQuery);
  }), [tasks, normalizedQuery]);
  const taskPage = clampPage(page, filteredTasks.length, TASK_PAGE_SIZE);
  const visibleTasks = filteredTasks.slice((taskPage - 1) * TASK_PAGE_SIZE, taskPage * TASK_PAGE_SIZE);

  const searchPlaceholder = level === "company" ? "Search departments…" : level === "department" ? "Search employees…" : "Search tasks…";

  return (
    <div className="rounded-[20px] border border-zinc-200/80 bg-white p-3 dark:border-white/10 dark:bg-zinc-950/30">
      <div className="flex flex-col gap-3 border-b border-zinc-100 pb-3 dark:border-white/10 lg:flex-row lg:items-center lg:justify-between">
        <div className="min-w-0">
          <Breadcrumb level={level} department={selectedDepartment} employee={selectedEmployee} onCompany={goCompany} onDepartment={() => goDepartment()} />
          <p className="mt-2 text-[10px] font-bold text-zinc-400">Current reporting filters remain authoritative. Drill-down only narrows the already-visible ACTIVE employee scope.</p>
        </div>
        <label className="flex min-h-9 w-full items-center gap-2 rounded-xl border border-zinc-200 bg-zinc-50 px-3 lg:max-w-xs dark:border-white/10 dark:bg-white/[0.035]">
          <Search size={14} className="text-zinc-400" />
          <input value={query} onChange={(event) => { setQuery(event.target.value); setPage(1); }} placeholder={searchPlaceholder} className="w-full bg-transparent text-[11px] font-bold text-zinc-700 outline-none placeholder:text-zinc-400 dark:text-zinc-200" />
        </label>
      </div>

      {level === "company" ? (
        <div className="pt-3">
          <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2"><Building2 size={16} className="text-amber-500" /><div><p className="text-xs font-black text-zinc-950 dark:text-white">Company departments</p><p className="text-[10px] font-bold text-zinc-400">{departments.length} departments · {activeEmployees.length} employees in the current scope</p></div></div>
          </div>
          {visibleDepartments.length ? (
            <div className="grid gap-2 md:grid-cols-2 xl:grid-cols-3">
              {visibleDepartments.map((department) => (
                <button key={department.name} type="button" onClick={() => goDepartment(department.name)} className="rounded-2xl border border-zinc-200 p-3 text-left transition hover:border-amber-300 hover:bg-amber-50/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-400 dark:border-white/10 dark:bg-white/[0.02] dark:hover:border-amber-400/25 dark:hover:bg-amber-400/[0.04]">
                  <div className="flex items-start justify-between gap-3"><div className="min-w-0"><p className="truncate text-xs font-black text-zinc-950 dark:text-white">{department.name}</p><p className="mt-1 text-[10px] font-bold text-zinc-400">{department.employees} employees</p></div><ChevronRight size={15} className="shrink-0 text-zinc-300" /></div>
                  <div className="mt-3 grid grid-cols-3 gap-2 text-[9px]"><div><p className="text-zinc-400">Avg score</p><p className={`mt-0.5 font-black ${scoreTone(department.avgScore)}`}>{department.avgScore ?? "—"}</p></div><div><p className="text-zinc-400">Attention</p><p className={`mt-0.5 font-black ${department.attention ? "text-orange-600 dark:text-orange-300" : "text-zinc-500 dark:text-zinc-300"}`}>{department.attention}</p></div><div><p className="text-zinc-400">Overdue</p><p className={`mt-0.5 font-black ${department.overdue ? "text-red-600 dark:text-red-300" : "text-zinc-500 dark:text-zinc-300"}`}>{department.overdue}</p></div></div>
                </button>
              ))}
            </div>
          ) : <div className="rounded-xl border border-dashed border-zinc-200 p-5 text-center text-[11px] font-bold text-zinc-400 dark:border-white/10">No departments match this search.</div>}
          <div className="mt-3"><PageControls page={departmentPage} totalItems={filteredDepartments.length} pageSize={DEPARTMENT_PAGE_SIZE} onChange={setPage} /></div>
        </div>
      ) : null}

      {level === "department" ? (
        <div className="pt-3">
          <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2"><UsersRound size={16} className="text-amber-500" /><div><p className="text-xs font-black text-zinc-950 dark:text-white">{selectedDepartment}</p><p className="text-[10px] font-bold text-zinc-400">{departmentEmployees.length} employees in the current scope</p></div></div>
            <button type="button" onClick={goCompany} className="inline-flex items-center gap-1.5 rounded-lg border border-zinc-200 px-2.5 py-1.5 text-[10px] font-black text-zinc-500 dark:border-white/10 dark:text-zinc-300"><ArrowLeft size={13} /> Departments</button>
          </div>
          {visibleDepartmentEmployees.length ? (
            <div className="grid gap-2 md:grid-cols-2">
              {visibleDepartmentEmployees.map((employee) => (
                <button key={employee.id} type="button" onClick={() => goEmployee(employee)} className="flex items-center justify-between gap-3 rounded-2xl border border-zinc-200 p-3 text-left transition hover:border-amber-300 hover:bg-amber-50/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-400 dark:border-white/10 dark:bg-white/[0.02] dark:hover:border-amber-400/25 dark:hover:bg-amber-400/[0.04]">
                  <div className="flex min-w-0 items-center gap-2.5"><div className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-zinc-100 text-xs font-black text-zinc-500 dark:bg-white/[0.06]">{String(employee.name || "U").slice(0, 1)}</div><div className="min-w-0"><p className="truncate text-xs font-black text-zinc-950 dark:text-white">{employee.name}</p><p className="truncate text-[9px] font-bold text-zinc-400">{employee.jobTitle || employee.role || "—"}</p></div></div>
                  <div className="flex shrink-0 items-center gap-2"><span className={`rounded-full px-2 py-1 text-[9px] font-black ${statusTone(employee.status || "No Activity")}`}>{employee.status || "No Activity"}</span><span className={`min-w-7 text-right text-sm font-black ${scoreTone(employee.performanceScore)}`}>{employee.performanceScore ?? "—"}</span><ChevronRight size={14} className="text-zinc-300" /></div>
                </button>
              ))}
            </div>
          ) : <div className="rounded-xl border border-dashed border-zinc-200 p-5 text-center text-[11px] font-bold text-zinc-400 dark:border-white/10">No employees match this search.</div>}
          <div className="mt-3"><PageControls page={employeePage} totalItems={filteredDepartmentEmployees.length} pageSize={EMPLOYEE_PAGE_SIZE} onChange={setPage} /></div>
        </div>
      ) : null}

      {level === "employee" && selectedEmployee ? (
        <div className="pt-3">
          <div className="mb-3 flex flex-col gap-3 rounded-2xl border border-zinc-200 bg-zinc-50/70 p-3 dark:border-white/10 dark:bg-white/[0.025] sm:flex-row sm:items-center sm:justify-between">
            <div className="flex min-w-0 items-center gap-2.5"><div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-amber-100 text-sm font-black text-amber-700 dark:bg-amber-400/10 dark:text-amber-300"><UserRound size={18} /></div><div className="min-w-0"><p className="truncate text-sm font-black text-zinc-950 dark:text-white">{selectedEmployee.name}</p><p className="truncate text-[10px] font-bold text-zinc-400">{selectedDepartment} · {selectedEmployee.jobTitle || selectedEmployee.role || "—"}</p></div></div>
            <div className="flex flex-wrap items-center gap-2"><button type="button" onClick={() => goDepartment()} className="inline-flex items-center gap-1.5 rounded-lg border border-zinc-200 px-2.5 py-1.5 text-[10px] font-black text-zinc-500 dark:border-white/10 dark:text-zinc-300"><ArrowLeft size={13} /> Employees</button><button type="button" onClick={() => onOpenEmployee?.(selectedEmployee.id)} className="rounded-lg border border-amber-200 bg-amber-50 px-2.5 py-1.5 text-[10px] font-black text-amber-700 hover:bg-amber-100 dark:border-amber-400/20 dark:bg-amber-400/10 dark:text-amber-300">Open employee details</button></div>
          </div>

          <div className="mb-3 flex items-center gap-2"><ListChecks size={16} className="text-amber-500" /><div><p className="text-xs font-black text-zinc-950 dark:text-white">Tasks in selected period</p><p className="text-[10px] font-bold text-zinc-400">Task data uses the same employee dashboard source as the existing Employee Drawer.</p></div></div>

          {taskError ? <div className="mb-3 rounded-xl border border-red-200 bg-red-50 p-3 text-[10px] font-bold text-red-700 dark:border-red-400/20 dark:bg-red-400/[0.06] dark:text-red-300">{taskError}</div> : null}
          {taskLoading ? <div className="grid gap-2">{[1, 2, 3].map((item) => <div key={item} className="h-12 animate-pulse rounded-xl bg-zinc-100 dark:bg-white/[0.05]" />)}</div> : visibleTasks.length ? (
            <div className="grid gap-2">
              {visibleTasks.map((task) => (
                <div key={task.id} className="flex flex-col gap-2 rounded-2xl border border-zinc-200 p-3 dark:border-white/10 dark:bg-white/[0.02] sm:flex-row sm:items-center sm:justify-between">
                  <div className="min-w-0"><p className="truncate text-[11px] font-black text-zinc-950 dark:text-white">{task.title}</p><p className="mt-1 truncate text-[9px] font-bold text-zinc-400">{task.project?.name || task.projectName || "No project"} · {task.status || "No status"} · Due {formatDate(task.dueDate)}</p></div>
                  <div className="flex shrink-0 items-center gap-2"><span className="text-[10px] font-black text-zinc-500 dark:text-zinc-300">{formatHours(task.actualHours)}</span>{onOpenTask ? <button type="button" onClick={() => onOpenTask(task)} className="rounded-lg border border-amber-200 px-2.5 py-1.5 text-[10px] font-black text-amber-700 hover:bg-amber-50 dark:border-amber-400/20 dark:text-amber-300 dark:hover:bg-amber-400/10">Open task</button> : <span className="rounded-lg bg-zinc-100 px-2.5 py-1.5 text-[9px] font-black text-zinc-400 dark:bg-white/[0.06]">Task navigation unavailable</span>}</div>
                </div>
              ))}
            </div>
          ) : <div className="rounded-xl border border-dashed border-zinc-200 p-5 text-center text-[11px] font-bold text-zinc-400 dark:border-white/10">No tasks match the selected period and search.</div>}
          {!taskLoading ? <div className="mt-3"><PageControls page={taskPage} totalItems={filteredTasks.length} pageSize={TASK_PAGE_SIZE} onChange={setPage} /></div> : null}
        </div>
      ) : null}
    </div>
  );
}

export default PerformanceDrilldownNavigator;
''', encoding='utf-8')

print('TEAM_PERFORMANCE_PHASE4_DRILLDOWN_NAVIGATION_V1_APPLIED=YES')
print('DRILLDOWN_LEVELS=COMPANY_DEPARTMENT_EMPLOYEE_TASK')
print('DEFAULT_DISCLOSURE_COLLAPSED=YES')
print('DEPARTMENT_SEARCH=YES')
print('EMPLOYEE_SEARCH=YES')
print('TASK_SEARCH=YES')
print('DEPARTMENT_PAGINATION=YES')
print('EMPLOYEE_PAGINATION=YES')
print('TASK_PAGINATION=YES')
print('EMPLOYEE_DRAWER_REUSED=YES')
print('EXISTING_TASK_NAVIGATION_REUSED=YES')
print('NEW_BACKEND_ENDPOINT=NO')
print('NEW_SCORE_CREATED=NO')