#!/usr/bin/env python3
import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TARGET_INDEX = "server/_core/index.ts"
TARGET_AI = "server/ai-agent.ts"
NEW_FILES = {
    "server/slaAlertDb.ts": '''import { and, eq } from "drizzle-orm";
import { alerts, type InsertAlert } from "../drizzle/schema";
import { getDb } from "./db";

/**
 * Idempotent SLA alert creation without a schema migration.
 * The alert title contains the task id + rule instance so the lookup is
 * stable even after the alert is marked as read.
 */
export async function createSlaAlertOnce(data: Omit<InsertAlert, "id">) {
  const db = await getDb();
  if (!db) return { created: false } as const;

  if (data.employeeId == null) {
    throw new Error("SLA alerts require employeeId for deduplication.");
  }

  const type = data.type ?? "system";
  const existing = await db
    .select({ id: alerts.id })
    .from(alerts)
    .where(
      and(
        eq(alerts.employeeId, data.employeeId),
        eq(alerts.type, type),
        eq(alerts.title, data.title),
      ),
    )
    .limit(1);

  if (existing[0]) return { created: false } as const;

  await db.insert(alerts).values(data);
  return { created: true } as const;
}
''',
    "server/sla.ts": '''import { getAllEmployees, getTasksByEmployee } from "./db";
import { createSlaAlertOnce } from "./slaAlertDb";

export type SlaState = "completed" | "review" | "on_track" | "due_today" | "breached";

const SLA_TIMEZONE = process.env.SLA_TIMEZONE || "Africa/Cairo";
const DEFAULT_SWEEP_INTERVAL_MS = 60 * 60 * 1000;
let sweepRunning = false;

function getDatePartsInTimeZone(date: Date, timeZone: string) {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(date);

  const year = parts.find(part => part.type === "year")?.value;
  const month = parts.find(part => part.type === "month")?.value;
  const day = parts.find(part => part.type === "day")?.value;

  if (!year || !month || !day) {
    throw new Error(`Unable to resolve SLA date in timezone ${timeZone}`);
  }

  return `${year}-${month}-${day}`;
}

export function getSlaBusinessDate(now: Date = new Date()) {
  return getDatePartsInTimeZone(now, SLA_TIMEZONE);
}

export function getTaskSlaState(
  task: { date: string; status: string },
  businessDate: string = getSlaBusinessDate(),
): SlaState {
  if (task.status === "done") return "completed";
  if (task.status === "review") return "review";
  if (task.date < businessDate) return "breached";
  if (task.date === businessDate) return "due_today";
  return "on_track";
}

export async function runSlaSweep() {
  const businessDate = getSlaBusinessDate();
  const employees = await getAllEmployees();

  let scannedTasks = 0;
  let breachedTasks = 0;
  let estimateOverruns = 0;
  let createdAlerts = 0;

  for (const employee of employees) {
    if (!employee.isActive) continue;

    const tasks = await getTasksByEmployee(employee.id);
    for (const task of tasks) {
      scannedTasks += 1;
      const slaState = getTaskSlaState(task, businessDate);

      if (slaState === "breached") {
        breachedTasks += 1;
        const result = await createSlaAlertOnce({
          employeeId: employee.id,
          type: "deadline_missed",
          title: `[Task #${task.id}] Past due since ${task.date}`,
          message: `Task "${task.title}" for ${employee.name} was expected by ${task.date} but is still "${task.status}".`,
          severity: "critical",
          targetRole: "team_leader",
        });
        if (result.created) createdAlerts += 1;
      }

      if (
        task.estimatedHours &&
        task.actualHours &&
        Number(task.actualHours) > Number(task.estimatedHours) * 1.5
      ) {
        estimateOverruns += 1;
        const result = await createSlaAlertOnce({
          employeeId: employee.id,
          type: "overdue_task",
          title: `[Task #${task.id}] Exceeded estimated hours`,
          message: `${employee.name} spent ${task.actualHours}h on "${task.title}" (estimated ${task.estimatedHours}h).`,
          severity: "warning",
          targetRole: "team_leader",
        });
        if (result.created) createdAlerts += 1;
      }
    }
  }

  return {
    businessDate,
    timezone: SLA_TIMEZONE,
    scannedTasks,
    breachedTasks,
    estimateOverruns,
    createdAlerts,
  };
}

export function startSlaScheduler() {
  if (process.env.SLA_SWEEP_ENABLED === "false") {
    console.log("[SLA] Scheduler disabled by SLA_SWEEP_ENABLED=false");
    return null;
  }

  const configuredInterval = Number(process.env.SLA_SWEEP_INTERVAL_MS || DEFAULT_SWEEP_INTERVAL_MS);
  const intervalMs = Number.isFinite(configuredInterval)
    ? Math.max(configuredInterval, 60_000)
    : DEFAULT_SWEEP_INTERVAL_MS;

  const execute = async () => {
    if (sweepRunning) {
      console.warn("[SLA] Previous sweep still running; skipping overlapping run");
      return;
    }

    sweepRunning = true;
    try {
      const result = await runSlaSweep();
      console.log("[SLA] Sweep complete", result);
    } catch (error) {
      console.error("[SLA] Sweep failed", error);
    } finally {
      sweepRunning = false;
    }
  };

  void execute();
  const timer = setInterval(() => void execute(), intervalMs);
  timer.unref?.();
  return timer;
}
''',
    "server/sla.test.ts": '''import { describe, expect, it } from "vitest";
import { getTaskSlaState } from "./sla";

describe("getTaskSlaState", () => {
  const businessDate = "2026-08-23";

  it("marks old unfinished tasks as breached", () => {
    expect(getTaskSlaState({ date: "2026-08-22", status: "todo" }, businessDate)).toBe("breached");
  });

  it("marks today's unfinished tasks as due_today", () => {
    expect(getTaskSlaState({ date: "2026-08-23", status: "in_progress" }, businessDate)).toBe("due_today");
  });

  it("keeps future tasks on track", () => {
    expect(getTaskSlaState({ date: "2026-08-24", status: "todo" }, businessDate)).toBe("on_track");
  });

  it("preserves the current review exemption", () => {
    expect(getTaskSlaState({ date: "2026-08-20", status: "review" }, businessDate)).toBe("review");
  });

  it("treats done as completed regardless of date", () => {
    expect(getTaskSlaState({ date: "2026-08-20", status: "done" }, businessDate)).toBe("completed");
  });
});
''',
}

EXPECTED_BLOBS = {
    TARGET_INDEX: "85f0fa77bdfa764f00ae0850425fb67eb1cdf503",
    TARGET_AI: "405b25cb44abfddf10dc4b9bfaf75ff3ff765fb8",
}

INDEX_REPLACEMENTS = [
    (
        'import { createTWorkspaceNativeRouter } from "../tworkspaceNative";\n',
        'import { createTWorkspaceNativeRouter } from "../tworkspaceNative";\nimport { startSlaScheduler } from "../sla";\n',
    ),
    (
'''  server.listen(port, () => {
    console.log(`Server running on http://localhost:${port}/`);
  });''',
'''  server.listen(port, () => {
    console.log(`Server running on http://localhost:${port}/`);
    startSlaScheduler();
  });''',
    ),
]

AI_REPLACEMENTS = [
    (
'''  getTaskStats,
  getEmployeesByDepartment,
  createAlert,
} from './db';
import { TRPCError } from '@trpc/server';''',
'''  getTaskStats,
  getEmployeesByDepartment,
} from './db';
import { TRPCError } from '@trpc/server';
import { runSlaSweep } from './sla';''',
    ),
    (
'''export async function checkDeadlines(): Promise<void> {
  const today = new Date().toISOString().split('T')[0];
  const allEmployees = await getAllEmployees();

  for (const employee of allEmployees) {
    if (!employee.isActive) continue;
    const tasks = await getTasksByEmployee(employee.id);

    for (const task of tasks) {
      if (task.date < today && task.status !== 'done' && task.status !== 'review') {
        await createAlert({
          employeeId: employee.id,
          type: 'deadline_missed',
          title: `Task "${task.title}" is past due`,
          message: `Task "${task.title}" for ${employee.name} was expected by ${task.date} but is still "${task.status}".`,
          severity: 'critical',
          targetRole: 'team_leader',
        });
      }

      if (task.estimatedHours && task.actualHours &&
          Number(task.actualHours) > Number(task.estimatedHours) * 1.5) {
        await createAlert({
          employeeId: employee.id,
          type: 'overdue_task',
          title: `Task "${task.title}" exceeds estimated hours`,
          message: `${employee.name} spent ${task.actualHours}h on "${task.title}" (estimated ${task.estimatedHours}h).`,
          severity: 'warning',
          targetRole: 'team_leader',
        });
      }
    }
  }
}''',
'''export async function checkDeadlines(): Promise<void> {
  await runSlaSweep();
}''',
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
        die("usage: generate_sla_foundation_phase1.py REPO_ROOT OUTPUT_PATCH", 2)

    root = Path(sys.argv[1]).resolve()
    output = Path(sys.argv[2]).resolve()

    if not (root / ".git").is_dir():
        die(f"not a git repository: {root}", 3)

    head = run(["git", "rev-parse", "HEAD"], root).stdout.strip()
    print(f"HEAD={head}")

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

    index_text = (root / TARGET_INDEX).read_text(encoding="utf-8")
    ai_text = (root / TARGET_AI).read_text(encoding="utf-8")
    index_text = apply_replacements(index_text, INDEX_REPLACEMENTS, "INDEX")
    ai_text = apply_replacements(ai_text, AI_REPLACEMENTS, "AI")

    tmp = Path(tempfile.mkdtemp(prefix="tos-sla-phase1-"))
    try:
        run(["git", "init", "-q"], tmp)
        run(["git", "config", "user.email", "sla-phase1@tos.local"], tmp)
        run(["git", "config", "user.name", "TOS SLA Phase 1 Generator"], tmp)

        for target in EXPECTED_BLOBS:
            dst = tmp / target
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(root / target, dst)

        run(["git", "add", "--", *EXPECTED_BLOBS.keys()], tmp)
        run(["git", "commit", "-qm", "exact live source baseline"], tmp)

        (tmp / TARGET_INDEX).write_text(index_text, encoding="utf-8", newline="\n")
        (tmp / TARGET_AI).write_text(ai_text, encoding="utf-8", newline="\n")
        for target, content in NEW_FILES.items():
            dst = tmp / target
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(content, encoding="utf-8", newline="\n")

        run(["git", "add", "-N", "--", *NEW_FILES.keys()], tmp)

        proc = subprocess.run(
            ["git", "diff", "--binary", "--full-index", "--", TARGET_INDEX, TARGET_AI, *NEW_FILES.keys()],
            cwd=tmp,
            text=True,
            capture_output=True,
        )
        if proc.returncode:
            die(f"git diff failed rc={proc.returncode}", 40)
        if not proc.stdout.strip():
            die("generated patch is empty", 41)

        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(proc.stdout, encoding="utf-8", newline="\n")
        print(f"GENERATED_PATCH_SHA256={sha256(output)}")

        numstat = run(["git", "apply", "--numstat", str(output)], root).stdout.strip().splitlines()
        parsed_paths = {row.split("\t")[-1] for row in numstat if row.strip()}
        expected_paths = {TARGET_INDEX, TARGET_AI, *NEW_FILES.keys()}
        if parsed_paths != expected_paths:
            die(f"unexpected patch paths: {sorted(parsed_paths)}", 42)

        run(["git", "apply", "--check", str(output)], root)
        print("APPLY_CHECK=PASS")
        print("SLA_FOUNDATION_PHASE1_GENERATOR=PASS")
        print(f"OUTPUT={output}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
