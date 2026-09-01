#!/usr/bin/env python3
import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

EXPECTED_HEAD = "63f59932776e29e32bacdf5214744d2662a3b8e3"
TARGETS = {
    "backend/src/routes/tasks.routes.js": "eca6fef34e9831e648b1385fbc4e36750a222a36",
    "frontend/src/pages/TeamPerformanceDashboard.jsx": "68e20b16d4fd0a204b3b60bafcdb64c8c1096a44",
    ".gitignore": "7bfd8c2b36433ae94d0f88a1911075238e855d62",
}

BACKEND_REPLACEMENTS = [
    (
'''    prisma.taskActivity.findMany({
      where: { 
        userId: { in: accessibleUserIds }, 
        createdAt: timeRange,
        task: {
          archivedAt: null,
          projectId: { in: accessibleProjectIds },
          assigneeId: { in: accessibleUserIds }
        }
      },
      select: { id: true, taskId: true, type: true, metadata: true, createdAt: true, userId: true }
    }),
''',
'''    prisma.taskActivity.findMany({
      where: {
        createdAt: timeRange,
        task: {
          archivedAt: null,
          projectId: { in: accessibleProjectIds },
          assigneeId: { in: accessibleUserIds }
        }
      },
      select: {
        id: true,
        taskId: true,
        type: true,
        metadata: true,
        createdAt: true,
        userId: true,
        task: { select: { assigneeId: true, projectId: true } }
      }
    }),
'''
    ),
    (
'''    prisma.taskActivity.findMany({
      where: { 
        userId: { in: accessibleUserIds }, 
        createdAt: prevTimeRange,
        task: { archivedAt: null, projectId: { in: accessibleProjectIds }, assigneeId: { in: accessibleUserIds } }
      },
      select: { id: true, taskId: true, type: true, metadata: true, createdAt: true, userId: true }
    })
''',
'''    prisma.taskActivity.findMany({
      where: {
        createdAt: prevTimeRange,
        task: { archivedAt: null, projectId: { in: accessibleProjectIds }, assigneeId: { in: accessibleUserIds } }
      },
      select: {
        id: true,
        taskId: true,
        type: true,
        metadata: true,
        createdAt: true,
        userId: true,
        task: { select: { assigneeId: true, projectId: true } }
      }
    })
'''
    ),
    (
'''  for (const act of allActivities) {
    // Use task assigneeId for performance attribution, not activity actor
    const employeeId = act.task?.assigneeId || act.userId;
    if (!userActivitiesMap.has(employeeId)) userActivitiesMap.set(employeeId, []);
    userActivitiesMap.get(employeeId).push(act);
  }
''',
'''  for (const act of allActivities) {
    // Performance belongs to the task's primary assignee, never the activity actor.
    const employeeId = act.task?.assigneeId;
    if (!employeeId) continue;
    if (!userActivitiesMap.has(employeeId)) userActivitiesMap.set(employeeId, []);
    userActivitiesMap.get(employeeId).push(act);
  }
'''
    ),
    (
'''  for (const act of allPrevActivities) {
    // Use task assigneeId for performance attribution, not activity actor
    const employeeId = act.task?.assigneeId || act.userId;
    if (!userPrevActivitiesMap.has(employeeId)) userPrevActivitiesMap.set(employeeId, []);
    userPrevActivitiesMap.get(employeeId).push(act);
  }
''',
'''  for (const act of allPrevActivities) {
    // Performance belongs to the task's primary assignee, never the activity actor.
    const employeeId = act.task?.assigneeId;
    if (!employeeId) continue;
    if (!userPrevActivitiesMap.has(employeeId)) userPrevActivitiesMap.set(employeeId, []);
    userPrevActivitiesMap.get(employeeId).push(act);
  }
'''
    ),
    (
'''    efficiencyScores,
    onTimeCompleted,
    workflowScore,
    consistencyScore
  } = metrics;
''',
'''    efficiencyScores,
    onTimeCompleted,
    eligibleOnTimeCompleted,
    workflowScore,
    consistencyScore
  } = metrics;
'''
    ),
    (
'''  // B. On-Time/Overdue (25%)
  if (completed > 0) {
    const onTimeRatio = onTimeCompleted / completed;
    const baseScore = Math.round(onTimeRatio * 100);
    const overduePenalty = Math.min(25, overdue * 5);
    const onTimeScore = Math.max(0, baseScore - overduePenalty);
    const achieved = Math.round(onTimeScore * weights.onTime / 100);
    breakdown.onTime = { score: onTimeScore, max: weights.onTime, achieved: Math.min(achieved, weights.onTime) };
    availableWeight += weights.onTime;
    achievedScore += breakdown.onTime.achieved;
  } else if (total > 0) {
    // Tasks exist but none completed
    breakdown.onTime = { score: 0, max: weights.onTime, achieved: 0 };
    availableWeight += weights.onTime;
    achievedScore += 0;
  } else {
    breakdown.onTime = { score: 0, max: weights.onTime, achieved: 0, skipped: true };
  }
''',
'''  // B. On-Time/Overdue (25%)
  // Only completed tasks with both dueDate and completedAt are eligible.
  if (eligibleOnTimeCompleted > 0) {
    const onTimeRatio = onTimeCompleted / eligibleOnTimeCompleted;
    const baseScore = Math.round(onTimeRatio * 100);
    const overduePenalty = Math.min(25, overdue * 5);
    const onTimeScore = Math.max(0, baseScore - overduePenalty);
    const achieved = Math.round(onTimeScore * weights.onTime / 100);
    breakdown.onTime = { score: onTimeScore, max: weights.onTime, achieved: Math.min(achieved, weights.onTime) };
    availableWeight += weights.onTime;
    achievedScore += breakdown.onTime.achieved;
  } else {
    // Missing due/completion dates must not reduce the employee score.
    breakdown.onTime = { score: 0, max: weights.onTime, achieved: 0, skipped: true };
  }
'''
    ),
    (
'''// On-Time calculation test endpoint (for verification only)
router.get("/reports/team-performance/test-ontime", asyncHandler(async (req, res) => {
  const { completed, onTimeCompleted, eligibleOnTimeCompleted } = req.query;
  const c = Number(completed) || 0;
  const oc = Number(onTimeCompleted) || 0;
  const ec = Number(eligibleOnTimeCompleted) || 0;
  let breakdown = {};
  let score = null;
  let skipped = true;
  if (ec > 0) {
    const raw = Math.round((oc / ec) * 100);
    score = raw;
    skipped = false;
    breakdown = { score: raw, max: 25, achieved: Math.round(raw * 25 / 100) };
  }
  res.json({ input: { completed: c, onTimeCompleted: oc, eligibleOnTimeCompleted: ec }, breakdown, skipped });
}));
''',
''
    ),
    (
'''    // Clamp to start date
    if (periodStart < startDate) {
      periodStart = new Date(startDate);
      if (periodStart > periodEnd) break;
    }
''',
'''    // Clamp partial first/last periods to the requested history window.
    // This prevents future days in the current week/month from affecting overdue/history metrics.
    if (periodEnd > endDate) periodEnd = new Date(endDate);
    if (periodStart < startDate) periodStart = new Date(startDate);
    if (periodStart > periodEnd) break;
'''
    ),
]

FRONTEND_REPLACEMENTS = [
    (
'''  if (preset === "today") {
    start = startOfDay(now);
    end = endOfDay(now);
  } else if (preset === "yesterday") {
''',
'''  if (preset === "all") {
    return { start: null, end: null, isInvalid: false, label: t.presets.all };
  } else if (preset === "today") {
    start = startOfDay(now);
    end = endOfDay(now);
  } else if (preset === "7d") {
    start = startOfDay(new Date(now.getFullYear(), now.getMonth(), now.getDate() - 6));
    end = endOfDay(now);
  } else if (preset === "30d") {
    start = startOfDay(new Date(now.getFullYear(), now.getMonth(), now.getDate() - 29));
    end = endOfDay(now);
  } else if (preset === "yesterday") {
'''
    ),
    (
'''  } else if (preset === "month") {
    start = startOfDay(new Date(now.getFullYear(), now.getMonth(), 1));
    end = endOfDay(now);
  } else if (preset === "year") {
''',
'''  } else if (preset === "month") {
    start = startOfDay(new Date(now.getFullYear(), now.getMonth(), 1));
    end = endOfDay(now);
  } else if (preset === "quarter") {
    const quarterStartMonth = Math.floor(now.getMonth() / 3) * 3;
    start = startOfDay(new Date(now.getFullYear(), quarterStartMonth, 1));
    end = endOfDay(now);
  } else if (preset === "year") {
'''
    ),
]

GITIGNORE_REPLACEMENTS = [
    (
'''# Runtime data
pids
''',
'''# Runtime data
/backend/.pm2/
pids
'''
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
            die(f"{label} replacement {index} expected 1 exact match, found {count}", 20 + index)
        text = text.replace(old, new, 1)
    return text


def main():
    if len(sys.argv) != 3:
        die("usage: generate_phase3_final_correction_v1.py REPO_ROOT OUTPUT_PATCH", 2)

    root = Path(sys.argv[1]).resolve()
    output = Path(sys.argv[2]).resolve()

    if not (root / ".git").is_dir():
        die(f"not a git repository: {root}", 3)

    head = run(["git", "rev-parse", "HEAD"], root).stdout.strip()
    print(f"HEAD={head}")
    if head != EXPECTED_HEAD:
        die(f"HEAD mismatch expected={EXPECTED_HEAD} actual={head}", 4)

    for target, expected_blob in TARGETS.items():
        path = root / target
        if not path.is_file():
            die(f"target missing: {target}", 5)
        blob = run(["git", "hash-object", target], root).stdout.strip()
        print(f"SOURCE_BLOB {target}={blob}")
        if blob != expected_blob:
            die(f"blob mismatch for {target}: expected={expected_blob} actual={blob}", 6)
        if run(["git", "diff", "--cached", "--", target], root).stdout.strip():
            die(f"target has staged changes: {target}", 7)
        if run(["git", "diff", "--", target], root).stdout.strip():
            die(f"target has tracked local changes: {target}", 8)

    source_text = {}
    newline_state = {}
    for target in TARGETS:
        raw = (root / target).read_bytes()
        if b"\r\n" in raw:
            die(f"CRLF source detected: {target}", 9)
        newline_state[target] = raw.endswith(b"\n")
        source_text[target] = raw.decode("utf-8")

    source_text["backend/src/routes/tasks.routes.js"] = apply_replacements(
        source_text["backend/src/routes/tasks.routes.js"], BACKEND_REPLACEMENTS, "BACKEND"
    )
    source_text["frontend/src/pages/TeamPerformanceDashboard.jsx"] = apply_replacements(
        source_text["frontend/src/pages/TeamPerformanceDashboard.jsx"], FRONTEND_REPLACEMENTS, "FRONTEND"
    )
    source_text[".gitignore"] = apply_replacements(
        source_text[".gitignore"], GITIGNORE_REPLACEMENTS, "GITIGNORE"
    )

    tmp = Path(tempfile.mkdtemp(prefix="tos-phase3-final-v1-"))
    try:
        run(["git", "init", "-q"], tmp)
        run(["git", "config", "user.email", "phase3-fix@tos.local"], tmp)
        run(["git", "config", "user.name", "TOS Phase 3 Final Fix Generator"], tmp)

        for target in TARGETS:
            tmp_target = tmp / target
            tmp_target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(root / target, tmp_target)
        run(["git", "add", "--"] + list(TARGETS.keys()), tmp)
        run(["git", "commit", "-qm", "exact TOS phase3 baseline"], tmp)

        for target, text in source_text.items():
            encoded = text.encode("utf-8")
            if newline_state[target] and not encoded.endswith(b"\n"):
                encoded += b"\n"
            elif not newline_state[target] and encoded.endswith(b"\n"):
                encoded = encoded[:-1]
            (tmp / target).write_bytes(encoded)

        run(["node", "--check", str(tmp / "backend/src/routes/tasks.routes.js")], tmp)
        print("BACKEND_NODE_CHECK=PASS")

        proc = subprocess.run(
            ["git", "diff", "--binary", "--full-index", "--"] + list(TARGETS.keys()),
            cwd=tmp,
            text=True,
            capture_output=True,
        )
        if proc.returncode:
            die(f"git diff failed rc={proc.returncode}", 40)
        if not proc.stdout.strip():
            die("generated patch is empty", 41)

        output.write_text(proc.stdout, encoding="utf-8", newline="\n")
        print(f"GENERATED_PATCH_SHA256={sha256(output)}")

        numstat = run(["git", "apply", "--numstat", str(output)], root).stdout.strip().splitlines()
        parsed_paths = {row.split("\t")[-1] for row in numstat if row.strip()}
        if parsed_paths != set(TARGETS.keys()):
            die(f"unexpected patch paths: {sorted(parsed_paths)}", 42)
        print("PATCH_PATHS=PASS")

        run(["git", "apply", "--check", str(output)], root)
        print("APPLY_CHECK=PASS")
        print("PHASE3_FINAL_CORRECTION_V1_GENERATOR=PASS")
        print(f"OUTPUT={output}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
