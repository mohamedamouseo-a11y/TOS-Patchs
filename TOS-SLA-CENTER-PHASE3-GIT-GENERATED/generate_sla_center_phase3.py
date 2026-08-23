#!/usr/bin/env python3
import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TARGET_APP = "client/src/App.tsx"
TARGET_LAYOUT = "client/src/components/DashboardLayout.tsx"
TARGET_ROUTERS = "server/routers.ts"

EXPECTED_BLOBS = {
    TARGET_APP: "2018e4716cbcbdd2f0934aae18b132d92b7c3aa1",
    TARGET_LAYOUT: "138d9187e6a28fa6ef3753be2166ede489884e2b",
    TARGET_ROUTERS: "c0d9dcdd0582f75d34bc946fdf995cf0ea04e1a6",
}

NEW_FILES = {
    "server/slaCenter.ts": '''import { getSlaBusinessDate, getTaskSlaState } from "./sla";

export type SlaCenterTask = {
  id: number;
  employeeId: number;
  clientId?: number | null;
  title: string;
  date: string;
  status: string;
  estimatedHours?: string | number | null;
  actualHours?: string | number | null;
};

export type SlaCenterEmployee = {
  id: number;
  name: string;
  departmentId: number;
};

export type SlaCenterNamedEntity = {
  id: number;
  name: string;
};

type MutableMetrics = {
  totalTasks: number;
  breached: number;
  atRisk: number;
  overrun: number;
  completed: number;
  review: number;
  onTrack: number;
  delayDaysTotal: number;
};

export type SlaMetrics = Omit<MutableMetrics, "delayDaysTotal"> & {
  compliancePct: number;
  avgDelayDays: number;
};

export type SlaDrilldownRow = SlaMetrics & {
  id: string;
  name: string;
};

const SLA_TIMEZONE = process.env.SLA_TIMEZONE || "Africa/Cairo";
const DAY_MS = 24 * 60 * 60 * 1000;

function emptyMetrics(): MutableMetrics {
  return {
    totalTasks: 0,
    breached: 0,
    atRisk: 0,
    overrun: 0,
    completed: 0,
    review: 0,
    onTrack: 0,
    delayDaysTotal: 0,
  };
}

function dateToUtcMs(value: string) {
  const [year, month, day] = value.split("-").map(Number);
  return Date.UTC(year, month - 1, day);
}

export function getSlaDelayDays(dueDate: string, businessDate: string) {
  const diff = dateToUtcMs(businessDate) - dateToUtcMs(dueDate);
  return Math.max(0, Math.floor(diff / DAY_MS));
}

function isEstimateOverrun(task: SlaCenterTask) {
  return Boolean(
    task.estimatedHours &&
    task.actualHours &&
    Number(task.actualHours) > Number(task.estimatedHours) * 1.5,
  );
}

function addTask(metrics: MutableMetrics, task: SlaCenterTask, businessDate: string) {
  metrics.totalTasks += 1;
  const state = getTaskSlaState(task, businessDate);

  if (state === "breached") {
    metrics.breached += 1;
    metrics.delayDaysTotal += getSlaDelayDays(task.date, businessDate);
  } else if (state === "due_today") {
    metrics.atRisk += 1;
  } else if (state === "completed") {
    metrics.completed += 1;
  } else if (state === "review") {
    metrics.review += 1;
  } else {
    metrics.onTrack += 1;
  }

  if (isEstimateOverrun(task)) metrics.overrun += 1;
}

function finalizeMetrics(metrics: MutableMetrics): SlaMetrics {
  const compliancePct = metrics.totalTasks
    ? Math.round(((metrics.totalTasks - metrics.breached) / metrics.totalTasks) * 1000) / 10
    : 100;
  const avgDelayDays = metrics.breached
    ? Math.round((metrics.delayDaysTotal / metrics.breached) * 10) / 10
    : 0;

  return {
    totalTasks: metrics.totalTasks,
    breached: metrics.breached,
    atRisk: metrics.atRisk,
    overrun: metrics.overrun,
    completed: metrics.completed,
    review: metrics.review,
    onTrack: metrics.onTrack,
    compliancePct,
    avgDelayDays,
  };
}

function buildRows(
  tasks: SlaCenterTask[],
  businessDate: string,
  resolveGroup: (task: SlaCenterTask) => { id: string; name: string },
) {
  const groups = new Map<string, { id: string; name: string; metrics: MutableMetrics }>();

  for (const task of tasks) {
    const group = resolveGroup(task);
    const existing = groups.get(group.id) || { ...group, metrics: emptyMetrics() };
    addTask(existing.metrics, task, businessDate);
    groups.set(group.id, existing);
  }

  return Array.from(groups.values())
    .map((group): SlaDrilldownRow => ({
      id: group.id,
      name: group.name,
      ...finalizeMetrics(group.metrics),
    }))
    .sort((a, b) => b.breached - a.breached || b.atRisk - a.atRisk || a.name.localeCompare(b.name));
}

export function buildSlaCenterDashboard(input: {
  tasks: SlaCenterTask[];
  employees: SlaCenterEmployee[];
  departments: SlaCenterNamedEntity[];
  clients: SlaCenterNamedEntity[];
  businessDate?: string;
}) {
  const businessDate = input.businessDate || getSlaBusinessDate();
  const employeeMap = new Map(input.employees.map(employee => [employee.id, employee]));
  const departmentMap = new Map(input.departments.map(department => [department.id, department]));
  const clientMap = new Map(input.clients.map(client => [client.id, client]));
  const overall = emptyMetrics();

  for (const task of input.tasks) addTask(overall, task, businessDate);

  const departments = buildRows(input.tasks, businessDate, task => {
    const employee = employeeMap.get(task.employeeId);
    const department = employee ? departmentMap.get(employee.departmentId) : undefined;
    return {
      id: department ? String(department.id) : "unknown",
      name: department?.name || "Unknown Department",
    };
  });

  const employees = buildRows(input.tasks, businessDate, task => {
    const employee = employeeMap.get(task.employeeId);
    return {
      id: employee ? String(employee.id) : `unknown-${task.employeeId}`,
      name: employee?.name || `Employee #${task.employeeId}`,
    };
  });

  const clients = buildRows(input.tasks, businessDate, task => {
    const client = task.clientId ? clientMap.get(task.clientId) : undefined;
    return {
      id: client ? String(client.id) : "unassigned",
      name: client?.name || "Unassigned",
    };
  });

  const topBreaches = input.tasks
    .filter(task => getTaskSlaState(task, businessDate) === "breached")
    .map(task => {
      const employee = employeeMap.get(task.employeeId);
      const department = employee ? departmentMap.get(employee.departmentId) : undefined;
      const client = task.clientId ? clientMap.get(task.clientId) : undefined;
      return {
        taskId: task.id,
        title: task.title,
        employeeName: employee?.name || `Employee #${task.employeeId}`,
        departmentName: department?.name || "Unknown Department",
        clientName: client?.name || "Unassigned",
        dueDate: task.date,
        delayDays: getSlaDelayDays(task.date, businessDate),
        status: task.status,
      };
    })
    .sort((a, b) => b.delayDays - a.delayDays || a.dueDate.localeCompare(b.dueDate))
    .slice(0, 10);

  return {
    businessDate,
    timezone: SLA_TIMEZONE,
    summary: finalizeMetrics(overall),
    drilldowns: { departments, employees, clients },
    topBreaches,
  };
}
''',
    "server/slaCenter.test.ts": '''import { describe, expect, it } from "vitest";
import { buildSlaCenterDashboard, getSlaDelayDays } from "./slaCenter";

const employees = [
  { id: 1, name: "Mona", departmentId: 10 },
  { id: 2, name: "Omar", departmentId: 20 },
];
const departments = [
  { id: 10, name: "Marketing" },
  { id: 20, name: "Operations" },
];
const clients = [{ id: 100, name: "Acme" }];

describe("SLA Center aggregation", () => {
  it("calculates current compliance, risk, breach aging, and overruns", () => {
    const dashboard = buildSlaCenterDashboard({
      businessDate: "2026-08-23",
      employees,
      departments,
      clients,
      tasks: [
        { id: 1, employeeId: 1, clientId: 100, title: "Late", date: "2026-08-20", status: "todo", estimatedHours: "2", actualHours: "4" },
        { id: 2, employeeId: 1, clientId: 100, title: "Today", date: "2026-08-23", status: "in_progress" },
        { id: 3, employeeId: 2, clientId: null, title: "Future", date: "2026-08-25", status: "todo" },
        { id: 4, employeeId: 2, clientId: null, title: "Done", date: "2026-08-19", status: "done" },
        { id: 5, employeeId: 2, clientId: null, title: "Review", date: "2026-08-18", status: "review" },
      ],
    });

    expect(dashboard.summary.totalTasks).toBe(5);
    expect(dashboard.summary.breached).toBe(1);
    expect(dashboard.summary.atRisk).toBe(1);
    expect(dashboard.summary.overrun).toBe(1);
    expect(dashboard.summary.compliancePct).toBe(80);
    expect(dashboard.summary.avgDelayDays).toBe(3);
    expect(dashboard.topBreaches[0].taskId).toBe(1);
  });

  it("builds department, employee and client drilldowns", () => {
    const dashboard = buildSlaCenterDashboard({
      businessDate: "2026-08-23",
      employees,
      departments,
      clients,
      tasks: [
        { id: 1, employeeId: 1, clientId: 100, title: "Late", date: "2026-08-20", status: "todo" },
        { id: 2, employeeId: 2, clientId: null, title: "Today", date: "2026-08-23", status: "todo" },
      ],
    });

    expect(dashboard.drilldowns.departments.map(row => row.name)).toEqual(["Marketing", "Operations"]);
    expect(dashboard.drilldowns.employees.map(row => row.name)).toEqual(["Mona", "Omar"]);
    expect(dashboard.drilldowns.clients.map(row => row.name)).toEqual(["Acme", "Unassigned"]);
  });

  it("calculates calendar-day breach aging", () => {
    expect(getSlaDelayDays("2026-08-20", "2026-08-23")).toBe(3);
    expect(getSlaDelayDays("2026-08-23", "2026-08-23")).toBe(0);
  });
});
''',
    "client/src/pages/SlaCenterPage.tsx": '''import { useMemo, useState } from "react";
import { useLocation } from "wouter";
import { trpc } from "@/lib/trpc";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  AlertTriangle,
  BriefcaseBusiness,
  Building2,
  Clock3,
  Gauge,
  Inbox,
  Loader2,
  RefreshCw,
  ShieldCheck,
  Users,
} from "lucide-react";

type Drilldown = "departments" | "employees" | "clients";

const DRILLDOWNS: Array<{ key: Drilldown; label: string; icon: typeof Users }> = [
  { key: "departments", label: "Departments", icon: Building2 },
  { key: "employees", label: "Employees", icon: Users },
  { key: "clients", label: "Clients", icon: BriefcaseBusiness },
];

export default function SlaCenterPage() {
  const [, setLocation] = useLocation();
  const [dimension, setDimension] = useState<Drilldown>("departments");
  const { data, isLoading, error, refetch, isFetching } = trpc.slaCenter.dashboard.useQuery(undefined, {
    refetchInterval: 60_000,
  });

  const rows = useMemo(() => data?.drilldowns[dimension] ?? [], [data, dimension]);

  if (isLoading) {
    return <div className="flex h-64 items-center justify-center"><Loader2 className="h-8 w-8 animate-spin text-primary" /></div>;
  }

  if (error || !data) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <AlertTriangle className="mx-auto mb-3 h-9 w-9 text-destructive" />
          <p className="font-semibold">Unable to load SLA Center</p>
          <p className="mt-1 text-sm text-muted-foreground">{error?.message || "No SLA data available."}</p>
          <Button className="mt-4" variant="outline" onClick={() => refetch()}>Retry</Button>
        </CardContent>
      </Card>
    );
  }

  const summary = data.summary;
  const kpis = [
    { label: "Current Compliance", value: `${summary.compliancePct}%`, note: "Visible task SLA health", icon: ShieldCheck },
    { label: "Breached", value: summary.breached, note: "Currently past due", icon: AlertTriangle },
    { label: "At Risk", value: summary.atRisk, note: "Due today, not completed", icon: Gauge },
    { label: "Average Delay", value: `${summary.avgDelayDays}d`, note: "Active breach aging", icon: Clock3 },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <div className="mb-2 flex items-center gap-2 text-sm font-medium text-primary">
            <Gauge className="h-4 w-4" />
            SLA Operations
          </div>
          <h1 className="text-2xl font-bold tracking-tight">SLA Center</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Current SLA health across your visible teams and clients. Business date: {data.businessDate} ({data.timezone}).
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" onClick={() => setLocation("/inbox")}>
            <Inbox className="mr-2 h-4 w-4" /> Operational Inbox
          </Button>
          <Button variant="outline" onClick={() => refetch()} disabled={isFetching}>
            <RefreshCw className={`mr-2 h-4 w-4 ${isFetching ? "animate-spin" : ""}`} /> Refresh
          </Button>
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {kpis.map((kpi) => (
          <Card key={kpi.label}>
            <CardContent className="flex items-center justify-between p-5">
              <div>
                <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{kpi.label}</p>
                <p className="mt-1 text-3xl font-bold">{kpi.value}</p>
                <p className="mt-1 text-xs text-muted-foreground">{kpi.note}</p>
              </div>
              <div className="rounded-xl border bg-muted/40 p-3"><kpi.icon className="h-5 w-5 text-primary" /></div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader className="pb-3">
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div>
              <CardTitle className="text-lg">SLA Drill-down</CardTitle>
              <p className="mt-1 text-sm text-muted-foreground">Compare compliance and active risk by operating dimension.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              {DRILLDOWNS.map((item) => (
                <Button key={item.key} size="sm" variant={dimension === item.key ? "default" : "outline"} onClick={() => setDimension(item.key)}>
                  <item.icon className="mr-1.5 h-4 w-4" /> {item.label}
                </Button>
              ))}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto rounded-xl border">
            <table className="w-full min-w-[820px] text-sm">
              <thead className="bg-muted/40 text-left text-xs uppercase tracking-wide text-muted-foreground">
                <tr>
                  <th className="px-4 py-3">{DRILLDOWNS.find(item => item.key === dimension)?.label}</th>
                  <th className="px-4 py-3">Compliance</th>
                  <th className="px-4 py-3">Tasks</th>
                  <th className="px-4 py-3">Breached</th>
                  <th className="px-4 py-3">At Risk</th>
                  <th className="px-4 py-3">Overrun</th>
                  <th className="px-4 py-3">Avg Delay</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {rows.map((row) => (
                  <tr key={row.id} className="hover:bg-muted/20">
                    <td className="px-4 py-3 font-medium">{row.name}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        <span className="w-12 font-semibold">{row.compliancePct}%</span>
                        <div className="h-1.5 w-24 overflow-hidden rounded-full bg-muted">
                          <div className="h-full rounded-full bg-primary" style={{ width: `${Math.max(0, Math.min(100, row.compliancePct))}%` }} />
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3">{row.totalTasks}</td>
                    <td className="px-4 py-3"><Badge variant={row.breached ? "destructive" : "outline"}>{row.breached}</Badge></td>
                    <td className="px-4 py-3"><Badge variant={row.atRisk ? "secondary" : "outline"}>{row.atRisk}</Badge></td>
                    <td className="px-4 py-3">{row.overrun}</td>
                    <td className="px-4 py-3">{row.avgDelayDays}d</td>
                  </tr>
                ))}
                {rows.length === 0 && (
                  <tr><td colSpan={7} className="px-4 py-10 text-center text-muted-foreground">No SLA tasks in this scope.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between gap-3">
            <div>
              <CardTitle className="text-lg">Breach Aging</CardTitle>
              <p className="mt-1 text-sm text-muted-foreground">Oldest active breaches in your current visibility scope.</p>
            </div>
            <Badge variant="outline">Top {Math.min(10, data.topBreaches.length)}</Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          {data.topBreaches.map((item) => (
            <div key={item.taskId} className="flex flex-col gap-3 rounded-xl border p-4 md:flex-row md:items-center md:justify-between">
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <p className="font-semibold">{item.title}</p>
                  <Badge variant="destructive">{item.delayDays}d late</Badge>
                </div>
                <p className="mt-1 text-xs text-muted-foreground">
                  {item.employeeName} · {item.departmentName} · {item.clientName} · Due {item.dueDate}
                </p>
              </div>
              <Badge variant="outline">{item.status.replace("_", " ")}</Badge>
            </div>
          ))}
          {data.topBreaches.length === 0 && (
            <div className="py-10 text-center text-muted-foreground">
              <ShieldCheck className="mx-auto mb-3 h-9 w-9 text-muted-foreground/40" />
              <p className="font-medium">No active SLA breaches.</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
''',
}

APP_REPLACEMENTS = [
    (
        'import AlertsPage from "./pages/AlertsPage";\n',
        'import AlertsPage from "./pages/AlertsPage";\nimport SlaCenterPage from "./pages/SlaCenterPage";\n',
    ),
    (
        '        <Route path="/inbox" component={AlertsPage} />\n',
        '        <Route path="/sla-center" component={SlaCenterPage} />\n        <Route path="/inbox" component={AlertsPage} />\n',
    ),
]

LAYOUT_REPLACEMENTS = [
    (
        '  MessageSquare, Activity, Sun, Moon, BookOpen, Eye, EyeOff, Mail, Github, Cloud,\n',
        '  MessageSquare, Activity, Sun, Moon, BookOpen, Eye, EyeOff, Mail, Github, Cloud, Gauge,\n',
    ),
    (
        '  { icon: BarChart, label: "Analytics", path: "/analytics", minRole: 2 },\n',
        '  { icon: BarChart, label: "Analytics", path: "/analytics", minRole: 2 },\n  { icon: Gauge, label: "SLA Center", path: "/sla-center", minRole: 2 },\n',
    ),
]

ROUTER_REPLACEMENTS = [
    (
        'import { canRoleSeeAlert } from "./alertVisibility";\n',
        'import { canRoleSeeAlert } from "./alertVisibility";\nimport { buildSlaCenterDashboard } from "./slaCenter";\n',
    ),
    (
'''  // ---- Alerts ----
  alerts: router({''',
'''  // ---- SLA Center ----
  slaCenter: router({
    dashboard: teamLeaderProcedure.query(async ({ ctx }) => {
      const visible = await getVisibleEmployeeIds(ctx.user);
      const [allEmployees, allDepartments, allClients] = await Promise.all([
        getAllEmployees(),
        getAllDepartments(),
        getAllClients(),
      ]);
      const scopedEmployees = (visible === 'all'
        ? allEmployees
        : allEmployees.filter(employee => (visible as number[]).includes(employee.id)))
        .filter(employee => employee.isActive);
      const taskLists = await Promise.all(scopedEmployees.map(employee => getTasksByEmployee(employee.id)));

      return buildSlaCenterDashboard({
        employees: scopedEmployees.map(employee => ({
          id: employee.id,
          name: employee.name,
          departmentId: employee.departmentId,
        })),
        departments: allDepartments.map(department => ({ id: department.id, name: department.name })),
        clients: allClients.map(client => ({ id: client.id, name: client.name })),
        tasks: taskLists.flat().map(task => ({
          id: task.id,
          employeeId: task.employeeId,
          clientId: task.clientId,
          title: task.title,
          date: task.date,
          status: task.status,
          estimatedHours: task.estimatedHours,
          actualHours: task.actualHours,
        })),
      });
    }),
  }),

  // ---- Alerts ----
  alerts: router({''',
    ),
]


def run(cmd, cwd=None, check=True):
    return subprocess.run(cmd, cwd=cwd, check=check, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def git_blob(repo: Path, path: str):
    return run(["git", "hash-object", path], cwd=repo).stdout.strip()


def assert_clean_target(repo: Path, path: str):
    unstaged = subprocess.run(["git", "diff", "--quiet", "--", path], cwd=repo)
    staged = subprocess.run(["git", "diff", "--cached", "--quiet", "--", path], cwd=repo)
    if unstaged.returncode != 0 or staged.returncode != 0:
        raise RuntimeError(f"Target file has local changes: {path}")


def replace_once(path: Path, old: str, new: str):
    content = path.read_text()
    count = content.count(old)
    if count != 1:
        raise RuntimeError(f"Expected exactly one anchor in {path}, found {count}")
    path.write_text(content.replace(old, new, 1))


def main():
    repo = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    output = Path(sys.argv[2] if len(sys.argv) > 2 else "/var/tmp/TOS_SLA_CENTER_PHASE3.patch").resolve()

    if not (repo / ".git").exists():
        raise RuntimeError(f"Not a git repository: {repo}")

    branch = run(["git", "branch", "--show-current"], cwd=repo).stdout.strip()
    if branch != "main":
        raise RuntimeError(f"Expected branch main, found {branch or '(detached)'}")

    for path, expected in EXPECTED_BLOBS.items():
        full = repo / path
        if not full.exists():
            raise RuntimeError(f"Missing target file: {path}")
        assert_clean_target(repo, path)
        actual = git_blob(repo, path)
        if actual != expected:
            raise RuntimeError(f"Baseline mismatch for {path}: expected {expected}, found {actual}")

    for path in NEW_FILES:
        if (repo / path).exists():
            raise RuntimeError(f"New Phase 3 file already exists: {path}")

    temp_root = Path(tempfile.mkdtemp(prefix="tos-sla-center-phase3-"))
    worktree = temp_root / "repo"
    try:
        run(["git", "worktree", "add", "--detach", str(worktree), "HEAD"], cwd=repo)

        for old, new in APP_REPLACEMENTS:
            replace_once(worktree / TARGET_APP, old, new)
        for old, new in LAYOUT_REPLACEMENTS:
            replace_once(worktree / TARGET_LAYOUT, old, new)
        for old, new in ROUTER_REPLACEMENTS:
            replace_once(worktree / TARGET_ROUTERS, old, new)

        for path, content in NEW_FILES.items():
            target = worktree / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
            run(["git", "add", "-N", "--", path], cwd=worktree)

        expected_paths = sorted([TARGET_APP, TARGET_LAYOUT, TARGET_ROUTERS, *NEW_FILES.keys()])
        changed = run(["git", "diff", "--name-only"], cwd=worktree).stdout.strip().splitlines()
        if sorted(changed) != expected_paths:
            raise RuntimeError(f"Unexpected patch scope: {changed}; expected {expected_paths}")

        patch = run(["git", "diff", "--binary", "--", *expected_paths], cwd=worktree).stdout
        if not patch.strip():
            raise RuntimeError("Generated patch is empty")
        output.write_text(patch)

        apply_check = subprocess.run(["git", "apply", "--check", str(output)], cwd=repo, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if apply_check.returncode != 0:
            raise RuntimeError(f"git apply --check failed:\n{apply_check.stderr}")

        digest = hashlib.sha256(output.read_bytes()).hexdigest()
        print(f"PATCH={output}")
        print(f"SHA256={digest}")
        print("FILES=")
        for path in expected_paths:
            print(path)
    finally:
        subprocess.run(["git", "worktree", "remove", "--force", str(worktree)], cwd=repo, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        shutil.rmtree(temp_root, ignore_errors=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
