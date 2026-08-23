#!/usr/bin/env python3
import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TARGET_ALERTS_PAGE = "client/src/pages/AlertsPage.tsx"
TARGET_APP = "client/src/App.tsx"
TARGET_LAYOUT = "client/src/components/DashboardLayout.tsx"
TARGET_ROUTERS = "server/routers.ts"

EXPECTED_BLOBS = {
    TARGET_ALERTS_PAGE: "af31dd7fe1dea55cfb6aed54efdf894fd79ceba9",
    TARGET_APP: "6c6a3de898329e812c37d209e2e3861c1e5cdb31",
    TARGET_LAYOUT: "e587fa6b0b31b1c8b758fe2b2682e00890939254",
    TARGET_ROUTERS: "3b5e01459d09e23fc2aa08bc3d0f1742acd0f699",
}

NEW_FILES = {
    "server/alertVisibility.ts": '''const ROLE_LEVELS: Record<string, number> = {
  super_admin: 7,
  admin: 6,
  ceo: 5,
  cmo: 4,
  director: 3,
  team_leader: 2,
  employee: 1,
};

/**
 * Alerts use targetRole as the minimum role that should receive the event.
 * Unknown/custom roles fall back to exact matching so they are not exposed
 * more broadly by accident.
 */
export function canRoleSeeAlert(userRole: string, targetRole?: string | null) {
  if (!targetRole) return true;

  const userLevel = ROLE_LEVELS[userRole];
  const targetLevel = ROLE_LEVELS[targetRole];

  if (!userLevel || !targetLevel) return userRole === targetRole;
  return userLevel >= targetLevel;
}
''',
    "server/alertVisibility.test.ts": '''import { describe, expect, it } from "vitest";
import { canRoleSeeAlert } from "./alertVisibility";

describe("canRoleSeeAlert", () => {
  it("shows team-leader alerts to the team leader and management above it", () => {
    expect(canRoleSeeAlert("team_leader", "team_leader")).toBe(true);
    expect(canRoleSeeAlert("director", "team_leader")).toBe(true);
    expect(canRoleSeeAlert("ceo", "team_leader")).toBe(true);
    expect(canRoleSeeAlert("admin", "team_leader")).toBe(true);
  });

  it("does not expose team-leader alerts to employees", () => {
    expect(canRoleSeeAlert("employee", "team_leader")).toBe(false);
  });

  it("shows untargeted alerts to every role", () => {
    expect(canRoleSeeAlert("employee", null)).toBe(true);
    expect(canRoleSeeAlert("director", undefined)).toBe(true);
  });

  it("uses exact matching for unknown custom roles", () => {
    expect(canRoleSeeAlert("custom_ops", "custom_ops")).toBe(true);
    expect(canRoleSeeAlert("admin", "custom_ops")).toBe(false);
  });
});
''',
}

ALERTS_PAGE_CONTENT = '''import { useMemo, useState } from "react";
import { trpc } from "@/lib/trpc";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  AlertTriangle,
  Bell,
  CheckCheck,
  CheckCircle2,
  Clock3,
  Gauge,
  Inbox,
  Loader2,
} from "lucide-react";
import { toast } from "sonner";

type InboxFilter = "all" | "unread" | "breached" | "overrun";

const FILTERS: Array<{ key: InboxFilter; label: string }> = [
  { key: "all", label: "All" },
  { key: "unread", label: "Unread" },
  { key: "breached", label: "Breached" },
  { key: "overrun", label: "Overrun" },
];

const SEVERITY_WEIGHT: Record<string, number> = {
  critical: 3,
  warning: 2,
  info: 1,
};

function alertTypeLabel(type: string) {
  if (type === "deadline_missed") return "SLA Breach";
  if (type === "overdue_task") return "Time Overrun";
  if (type === "low_productivity") return "Productivity";
  return "System";
}

export default function AlertsPage() {
  const [filter, setFilter] = useState<InboxFilter>("all");
  const utils = trpc.useUtils();
  const { data: alerts, isLoading } = trpc.alerts.list.useQuery();
  const { data: summary } = trpc.alerts.summary.useQuery();

  const refreshInbox = async () => {
    await Promise.all([
      utils.alerts.list.invalidate(),
      utils.alerts.summary.invalidate(),
      utils.alerts.unreadCount.invalidate(),
    ]);
  };

  const markReadMutation = trpc.alerts.markRead.useMutation({
    onSuccess: async () => {
      toast.success("Alert marked as read");
      await refreshInbox();
    },
    onError: (err) => toast.error(err.message),
  });

  const markAllReadMutation = trpc.alerts.markAllRead.useMutation({
    onSuccess: async (result) => {
      toast.success(result.updated ? `${result.updated} alerts marked as read` : "Inbox is already clear");
      await refreshInbox();
    },
    onError: (err) => toast.error(err.message),
  });

  const filteredAlerts = useMemo(() => {
    const rows = [...(alerts ?? [])].filter((alert) => {
      if (filter === "unread") return !alert.isRead;
      if (filter === "breached") return alert.type === "deadline_missed";
      if (filter === "overrun") return alert.type === "overdue_task";
      return true;
    });

    rows.sort((a, b) => {
      if (a.isRead !== b.isRead) return a.isRead ? 1 : -1;
      const severityDiff = (SEVERITY_WEIGHT[b.severity] || 0) - (SEVERITY_WEIGHT[a.severity] || 0);
      if (severityDiff) return severityDiff;
      return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime();
    });

    return rows;
  }, [alerts, filter]);

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  const filterCounts: Record<InboxFilter, number> = {
    all: summary?.total ?? alerts?.length ?? 0,
    unread: summary?.unread ?? 0,
    breached: summary?.breached ?? 0,
    overrun: summary?.overrun ?? 0,
  };

  const statCards = [
    { label: "Unread", value: summary?.unread ?? 0, icon: Inbox, note: "Needs attention" },
    { label: "Breached", value: summary?.breached ?? 0, icon: AlertTriangle, note: "Past due" },
    { label: "Overrun", value: summary?.overrun ?? 0, icon: Clock3, note: "Above estimate" },
    { label: "Critical", value: summary?.critical ?? 0, icon: Gauge, note: "Highest severity" },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div>
          <div className="mb-2 flex items-center gap-2 text-sm font-medium text-primary">
            <Inbox className="h-4 w-4" />
            SLA Operations
          </div>
          <h1 className="text-2xl font-bold tracking-tight">Operational Inbox</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            One queue for SLA breaches, time overruns, and operational alerts.
          </p>
        </div>
        <Button
          variant="outline"
          onClick={() => markAllReadMutation.mutate()}
          disabled={markAllReadMutation.isPending || (summary?.unread ?? 0) === 0}
        >
          {markAllReadMutation.isPending ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <CheckCheck className="mr-2 h-4 w-4" />
          )}
          Mark all read
        </Button>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {statCards.map((stat) => (
          <Card key={stat.label}>
            <CardContent className="flex items-center justify-between p-5">
              <div>
                <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{stat.label}</p>
                <p className="mt-1 text-3xl font-bold">{stat.value}</p>
                <p className="mt-1 text-xs text-muted-foreground">{stat.note}</p>
              </div>
              <div className="rounded-xl border bg-muted/40 p-3">
                <stat.icon className="h-5 w-5 text-primary" />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="flex flex-wrap gap-2">
        {FILTERS.map((item) => (
          <Button
            key={item.key}
            size="sm"
            variant={filter === item.key ? "default" : "outline"}
            onClick={() => setFilter(item.key)}
          >
            {item.label}
            <Badge variant="secondary" className="ml-2 min-w-6 justify-center">
              {filterCounts[item.key]}
            </Badge>
          </Button>
        ))}
      </div>

      <div className="space-y-3">
        {filteredAlerts.map((alert) => {
          const AlertIcon = alert.type === "deadline_missed"
            ? AlertTriangle
            : alert.type === "overdue_task"
              ? Clock3
              : Bell;

          return (
            <Card key={alert.id} className={alert.isRead ? "opacity-65" : "border-primary/20 shadow-sm"}>
              <CardHeader className="pb-2">
                <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                  <div className="flex min-w-0 items-start gap-3">
                    <div className={`mt-0.5 rounded-lg p-2 ${alert.severity === "critical" ? "bg-destructive/10 text-destructive" : alert.severity === "warning" ? "bg-amber-500/10 text-amber-600" : "bg-muted text-muted-foreground"}`}>
                      <AlertIcon className="h-4 w-4" />
                    </div>
                    <div className="min-w-0">
                      <CardTitle className="text-base leading-6">{alert.title}</CardTitle>
                      <p className="mt-1 text-xs text-muted-foreground">
                        {new Date(alert.createdAt).toLocaleString()}
                      </p>
                    </div>
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    {!alert.isRead && <Badge>Unread</Badge>}
                    <Badge variant={alert.severity === "critical" ? "destructive" : "secondary"}>
                      {alert.severity}
                    </Badge>
                    <Badge variant="outline">{alertTypeLabel(alert.type)}</Badge>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
                  <p className="max-w-4xl text-sm leading-6 text-muted-foreground">
                    {alert.message || "No additional details."}
                  </p>
                  {!alert.isRead && (
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => markReadMutation.mutate({ id: alert.id })}
                      disabled={markReadMutation.isPending}
                    >
                      <CheckCircle2 className="mr-1.5 h-4 w-4" />
                      Mark read
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          );
        })}

        {filteredAlerts.length === 0 && (
          <Card>
            <CardContent className="py-14 text-center text-muted-foreground">
              <CheckCircle2 className="mx-auto mb-3 h-10 w-10 text-muted-foreground/40" />
              <p className="font-medium">Nothing in this queue.</p>
              <p className="mt-1 text-sm">Operational alerts matching this filter will appear here.</p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
'''

APP_REPLACEMENTS = [
    (
        '        <Route path="/alerts" component={AlertsPage} />\n',
        '        <Route path="/inbox" component={AlertsPage} />\n        <Route path="/alerts" component={AlertsPage} />\n',
    ),
]

LAYOUT_REPLACEMENTS = [
    (
        '  { icon: Bell, label: "Notifications", path: "/alerts", minRole: 1 },\n',
        '  { icon: Bell, label: "Operational Inbox", path: "/inbox", minRole: 1 },\n',
    ),
    (
'''              {filteredMainNav.map(item => {
                const isActive = item.path === '/' ? location === '/' : location.startsWith(item.path);
                const isNotifications = item.path === '/alerts';
                const isHelpCenter = item.path === '/help';''',
'''              {filteredMainNav.map(item => {
                const isInbox = item.path === '/inbox';
                const isActive = item.path === '/'
                  ? location === '/'
                  : isInbox
                    ? location.startsWith('/inbox') || location.startsWith('/alerts')
                    : location.startsWith(item.path);
                const isNotifications = isInbox;
                const isHelpCenter = item.path === '/help';''',
    ),
]

ROUTER_REPLACEMENTS = [
    (
        'import { generateDailyReport as aiGenerateDailyReport, analyzePerformance, checkDeadlines } from "./ai-agent";\n',
        'import { generateDailyReport as aiGenerateDailyReport, analyzePerformance, checkDeadlines } from "./ai-agent";\nimport { canRoleSeeAlert } from "./alertVisibility";\n',
    ),
    (
'''async function getVisibleEmployeeIds(user: User): Promise<number[] | 'all'> {
  if (['super_admin', 'admin', 'ceo', 'cmo'].includes(user.role)) return 'all';
  const employee = await getEmployeeByUserId(user.id);
  if (!employee) return [];
  if (user.role === 'director' || user.role === 'team_leader') {
    const deptEmployees = await getEmployeesByDepartment(employee.departmentId);
    return deptEmployees.map(e => e.id);
  }
  return [employee.id];
}
''',
'''async function getVisibleEmployeeIds(user: User): Promise<number[] | 'all'> {
  if (['super_admin', 'admin', 'ceo', 'cmo'].includes(user.role)) return 'all';
  const employee = await getEmployeeByUserId(user.id);
  if (!employee) return [];
  if (user.role === 'director' || user.role === 'team_leader') {
    const deptEmployees = await getEmployeesByDepartment(employee.departmentId);
    return deptEmployees.map(e => e.id);
  }
  return [employee.id];
}

async function getVisibleAlertsForUser(
  user: User,
  filters?: { type?: string; isRead?: boolean },
) {
  const allAlerts = await getAlerts(filters);
  const roleVisible = allAlerts.filter((alert) => canRoleSeeAlert(user.role, alert.targetRole));
  const visibleEmployees = await getVisibleEmployeeIds(user);

  if (visibleEmployees === 'all') return roleVisible;
  return roleVisible.filter(
    (alert) => !alert.employeeId || visibleEmployees.includes(alert.employeeId),
  );
}
''',
    ),
    (
'''  // ---- Alerts ----
  alerts: router({
    list: protectedProcedure
      .input(z.object({ type: z.string().optional(), isRead: z.boolean().optional() }).optional())
      .query(async ({ ctx, input }) => {
        const allAlerts = await getAlerts({ targetRole: ctx.user.role, ...input });
        const visible = await getVisibleEmployeeIds(ctx.user);
        if (visible === 'all') return allAlerts;
        return allAlerts.filter(a => !a.employeeId || (visible as number[]).includes(a.employeeId));
      }),
    markRead: protectedProcedure
      .input(z.object({ id: z.number() }))
      .mutation(({ input }) => markAlertRead(input.id)),
    unreadCount: protectedProcedure.query(({ ctx }) => getUnreadAlertCount(ctx.user.role)),
  }),''',
'''  // ---- Operational Inbox / Alerts ----
  alerts: router({
    list: protectedProcedure
      .input(z.object({ type: z.string().optional(), isRead: z.boolean().optional() }).optional())
      .query(({ ctx, input }) => getVisibleAlertsForUser(ctx.user, input)),

    summary: protectedProcedure.query(async ({ ctx }) => {
      const visibleAlerts = await getVisibleAlertsForUser(ctx.user);
      return {
        total: visibleAlerts.length,
        unread: visibleAlerts.filter((alert) => !alert.isRead).length,
        critical: visibleAlerts.filter((alert) => alert.severity === 'critical').length,
        breached: visibleAlerts.filter((alert) => alert.type === 'deadline_missed').length,
        overrun: visibleAlerts.filter((alert) => alert.type === 'overdue_task').length,
      };
    }),

    markRead: protectedProcedure
      .input(z.object({ id: z.number() }))
      .mutation(async ({ ctx, input }) => {
        const visibleAlerts = await getVisibleAlertsForUser(ctx.user);
        if (!visibleAlerts.some((alert) => alert.id === input.id)) {
          throw new TRPCError({ code: 'NOT_FOUND', message: 'Alert not found.' });
        }
        return markAlertRead(input.id);
      }),

    markAllRead: protectedProcedure.mutation(async ({ ctx }) => {
      const unreadAlerts = await getVisibleAlertsForUser(ctx.user, { isRead: false });
      await Promise.all(unreadAlerts.map((alert) => markAlertRead(alert.id)));
      return { updated: unreadAlerts.length };
    }),

    unreadCount: protectedProcedure.query(async ({ ctx }) => {
      const unreadAlerts = await getVisibleAlertsForUser(ctx.user, { isRead: false });
      return unreadAlerts.length;
    }),
  }),''',
    ),
]


def die(message, code=1):
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(code)


def run(args, cwd, check=True):
    proc = subprocess.run(args, cwd=cwd, text=True, capture_output=True)
    if proc.stdout:
        print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, end="", file=sys.stderr)
    if check and proc.returncode:
        die(f"command failed rc={proc.returncode}: {' '.join(args)}", 90)
    return proc


def sha256(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def apply_replacements(text, replacements, label):
    for index, (old, new) in enumerate(replacements, start=1):
        count = text.count(old)
        print(f"{label}_REPLACEMENT_{index}_MATCHES={count}")
        if count != 1:
            die(f"{label} replacement {index} expected exactly 1 match, found {count}", 20 + index)
        text = text.replace(old, new, 1)
    return text


def main():
    if len(sys.argv) != 3:
        die("usage: generate_sla_operational_inbox_phase2.py REPO_ROOT OUTPUT_PATCH", 2)

    root = Path(sys.argv[1]).resolve()
    output = Path(sys.argv[2]).resolve()

    if not (root / ".git").is_dir():
        die(f"not a git repository: {root}", 3)

    print(f"HEAD={run(['git', 'rev-parse', 'HEAD'], root).stdout.strip()}")

    for target, expected_blob in EXPECTED_BLOBS.items():
        path = root / target
        if not path.is_file():
            die(f"target missing: {target}", 4)
        blob = run(["git", "hash-object", target], root).stdout.strip()
        print(f"SOURCE_BLOB[{target}]={blob}")
        if blob != expected_blob:
            die(f"blob mismatch for {target}: expected={expected_blob} actual={blob}", 5)
        if run(["git", "diff", "--", target], root).stdout.strip():
            die(f"target has tracked local changes: {target}", 6)
        if run(["git", "diff", "--cached", "--", target], root).stdout.strip():
            die(f"target has staged changes: {target}", 7)

    for target in NEW_FILES:
        if (root / target).exists():
            die(f"new target already exists; refusing overwrite: {target}", 8)

    alerts_text = ALERTS_PAGE_CONTENT
    app_text = apply_replacements((root / TARGET_APP).read_text(encoding="utf-8"), APP_REPLACEMENTS, "APP")
    layout_text = apply_replacements((root / TARGET_LAYOUT).read_text(encoding="utf-8"), LAYOUT_REPLACEMENTS, "LAYOUT")
    routers_text = apply_replacements((root / TARGET_ROUTERS).read_text(encoding="utf-8"), ROUTER_REPLACEMENTS, "ROUTERS")

    tmp = Path(tempfile.mkdtemp(prefix="tos-sla-phase2-"))
    try:
        run(["git", "init", "-q"], tmp)
        run(["git", "config", "user.email", "sla-phase2@tos.local"], tmp)
        run(["git", "config", "user.name", "TOS SLA Phase 2 Generator"], tmp)

        for target in EXPECTED_BLOBS:
            dst = tmp / target
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(root / target, dst)

        run(["git", "add", "--", *EXPECTED_BLOBS.keys()], tmp)
        run(["git", "commit", "-qm", "exact live source baseline"], tmp)

        (tmp / TARGET_ALERTS_PAGE).write_text(alerts_text, encoding="utf-8", newline="\n")
        (tmp / TARGET_APP).write_text(app_text, encoding="utf-8", newline="\n")
        (tmp / TARGET_LAYOUT).write_text(layout_text, encoding="utf-8", newline="\n")
        (tmp / TARGET_ROUTERS).write_text(routers_text, encoding="utf-8", newline="\n")

        for target, content in NEW_FILES.items():
            dst = tmp / target
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(content, encoding="utf-8", newline="\n")

        run(["git", "add", "-N", "--", *NEW_FILES.keys()], tmp)

        all_paths = [*EXPECTED_BLOBS.keys(), *NEW_FILES.keys()]
        proc = subprocess.run(
            ["git", "diff", "--binary", "--full-index", "--", *all_paths],
            cwd=tmp,
            text=True,
            capture_output=True,
        )
        if proc.returncode:
            if proc.stderr:
                print(proc.stderr, end="", file=sys.stderr)
            die(f"git diff failed rc={proc.returncode}", 40)
        if not proc.stdout.strip():
            die("generated patch is empty", 41)

        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(proc.stdout, encoding="utf-8", newline="\n")
        print(f"GENERATED_PATCH_SHA256={sha256(output)}")

        numstat = run(["git", "apply", "--numstat", str(output)], root).stdout.strip().splitlines()
        parsed_paths = {row.split("\t")[-1] for row in numstat if row.strip()}
        expected_paths = set(all_paths)
        if parsed_paths != expected_paths:
            die(f"unexpected patch paths: {sorted(parsed_paths)}", 42)

        run(["git", "apply", "--check", str(output)], root)
        print("APPLY_CHECK=PASS")
        print("SLA_OPERATIONAL_INBOX_PHASE2_GENERATOR=PASS")
        print(f"OUTPUT={output}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
