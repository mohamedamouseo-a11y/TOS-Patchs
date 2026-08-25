#!/usr/bin/env python3
import difflib
import hashlib
import subprocess
import sys
from pathlib import Path

TARGET_BASE_HEAD = "d71a7ded2b0e2d6b0cb82d916f7649e88699e391"
TARGET_FILE = "frontend/src/pages/TeamPerformanceDashboard.jsx"
EXPECTED_BLOB = "2639ab89d95361d2985d61b6a5e00fec18574a1b"

REPLACEMENTS = [
    ('className="relative z-20 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"', 'className="relative z-20 flex flex-col gap-2.5 sm:flex-row sm:items-center sm:justify-between"', 1),
    ('className="mt-1 text-xs font-bold text-zinc-400">{t.dateFilter.currentPeriod}', 'className="mt-0.5 text-[11px] font-bold text-zinc-400">{t.dateFilter.currentPeriod}', 1),
    ('className={`inline-flex items-center gap-2 rounded-2xl border px-4 py-3 text-sm font-black shadow-sm transition ${isOpen ? "border-amber-300 bg-amber-50 text-amber-700 shadow-lg shadow-amber-500/10 dark:border-amber-400/40 dark:bg-amber-400/10 dark:text-amber-200" : "border-zinc-200 bg-white text-zinc-900 hover:border-amber-300 dark:border-white/10 dark:bg-white/[0.04] dark:text-white dark:hover:border-amber-400/40"}`}', 'className={`inline-flex items-center gap-2 rounded-xl border px-3.5 py-2.5 text-xs font-black shadow-sm transition ${isOpen ? "border-amber-300 bg-amber-50 text-amber-700 shadow-md shadow-amber-500/10 dark:border-amber-400/40 dark:bg-amber-400/10 dark:text-amber-200" : "border-zinc-200 bg-white text-zinc-900 hover:border-amber-300 dark:border-white/10 dark:bg-white/[0.04] dark:text-white dark:hover:border-amber-400/40"}`}', 1),
    ('className="rounded-xl bg-zinc-100 px-2 py-1 text-[11px] text-zinc-500 dark:bg-white/10 dark:text-zinc-300">{rangeLabel}', 'className="rounded-lg bg-zinc-100 px-2 py-0.5 text-[10px] text-zinc-500 dark:bg-white/10 dark:text-zinc-300">{rangeLabel}', 1),
    ('className="absolute left-0 top-full mt-3 w-[min(92vw,360px)] rounded-3xl border border-zinc-200 bg-white p-3 text-right shadow-2xl shadow-zinc-950/10 dark:border-white/10 dark:bg-zinc-950 dark:shadow-black/40"', 'className="absolute left-0 top-full mt-2 w-[min(92vw,340px)] rounded-2xl border border-zinc-200 bg-white p-2.5 text-right shadow-xl shadow-zinc-950/10 dark:border-white/10 dark:bg-zinc-950 dark:shadow-black/40"', 1),
    ('className={`flex w-full items-center justify-between rounded-2xl px-4 py-3 text-sm font-black transition ${draftPreset === item.key ? "border border-amber-300 bg-amber-50 text-amber-700 dark:border-amber-400/40 dark:bg-amber-400/10 dark:text-amber-200" : "text-zinc-600 hover:bg-zinc-50 dark:text-zinc-300 dark:hover:bg-white/5"}`}', 'className={`flex w-full items-center justify-between rounded-xl px-3 py-2.5 text-xs font-black transition ${draftPreset === item.key ? "border border-amber-300 bg-amber-50 text-amber-700 dark:border-amber-400/40 dark:bg-amber-400/10 dark:text-amber-200" : "text-zinc-600 hover:bg-zinc-50 dark:text-zinc-300 dark:hover:bg-white/5"}`}', 1),
    ('className="mt-3 space-y-3 rounded-2xl border border-zinc-100 bg-zinc-50 p-3 dark:border-white/10 dark:bg-white/[0.03]"', 'className="mt-2.5 space-y-2 rounded-xl border border-zinc-100 bg-zinc-50 p-2.5 dark:border-white/10 dark:bg-white/[0.03]"', 1),
    ('className="mt-2 w-full rounded-2xl border border-zinc-200 bg-white px-4 py-3 text-sm font-bold text-zinc-900 outline-none transition focus:border-amber-400 dark:border-white/10 dark:bg-zinc-900 dark:text-white"', 'className="mt-1.5 w-full rounded-xl border border-zinc-200 bg-white px-3.5 py-2.5 text-xs font-bold text-zinc-900 outline-none transition focus:border-amber-400 dark:border-white/10 dark:bg-zinc-900 dark:text-white"', 2),
    ('className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-xs font-black text-red-700 dark:border-red-500/20 dark:bg-red-500/10 dark:text-red-300"', 'className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-[11px] font-black text-red-700 dark:border-red-500/20 dark:bg-red-500/10 dark:text-red-300"', 2),
    ('className="rounded-2xl border border-zinc-200 px-4 py-3 text-xs font-black text-zinc-600 transition hover:bg-zinc-50 dark:border-white/10 dark:text-zinc-300 dark:hover:bg-white/5"', 'className="rounded-xl border border-zinc-200 px-3 py-2.5 text-[11px] font-black text-zinc-600 transition hover:bg-zinc-50 dark:border-white/10 dark:text-zinc-300 dark:hover:bg-white/5"', 1),
    ('className="rounded-2xl bg-gradient-to-l from-amber-500 to-yellow-300 px-4 py-3 text-xs font-black text-zinc-950 shadow-lg shadow-amber-500/20 transition hover:scale-[1.01] disabled:cursor-not-allowed disabled:opacity-50"', 'className="rounded-xl bg-gradient-to-l from-amber-500 to-yellow-300 px-3 py-2.5 text-[11px] font-black text-zinc-950 shadow-md shadow-amber-500/20 transition hover:scale-[1.01] disabled:cursor-not-allowed disabled:opacity-50"', 1),
    ('className="mt-2 min-h-[52px] w-full rounded-2xl border border-zinc-200 bg-white px-4 text-sm font-black text-zinc-900 outline-none transition focus:border-amber-400 disabled:cursor-not-allowed disabled:bg-zinc-50 disabled:text-zinc-400 dark:border-white/10 dark:bg-zinc-900 dark:text-white"', 'className="mt-1.5 min-h-[44px] w-full rounded-xl border border-zinc-200 bg-white px-3.5 text-xs font-black text-zinc-900 outline-none transition focus:border-amber-400 disabled:cursor-not-allowed disabled:bg-zinc-50 disabled:text-zinc-400 dark:border-white/10 dark:bg-zinc-900 dark:text-white"', 1),
    ('<Card className="p-5">', '<Card className="p-4">', 5),
    ('className="mb-5 flex items-center justify-between gap-3"', 'className="mb-3.5 flex items-center justify-between gap-2.5"', 4),
    ('className="mt-1 text-lg font-black text-zinc-950 dark:text-white"', 'className="mt-0.5 text-base font-black text-zinc-950 dark:text-white"', 3),
    ('<div className="space-y-3">', '<div className="space-y-2.5">', 1),
    ('className="grid grid-cols-[110px_1fr_54px] items-center gap-3 text-xs font-black text-zinc-500 dark:text-zinc-400"', 'className="grid grid-cols-[104px_1fr_48px] items-center gap-2.5 text-[11px] font-black text-zinc-500 dark:text-zinc-400"', 1),
    ('className="h-3 overflow-hidden rounded-full bg-zinc-100 dark:bg-white/10"', 'className="h-2.5 overflow-hidden rounded-full bg-zinc-100 dark:bg-white/10"', 1),
    ('className="rounded-3xl border border-dashed border-zinc-200 p-8 text-center text-sm font-bold text-zinc-400 dark:border-white/10"', 'className="rounded-2xl border border-dashed border-zinc-200 p-6 text-center text-xs font-bold text-zinc-400 dark:border-white/10"', 2),
    ('<div className="space-y-4">', '<div className="space-y-3">', 1),
    ('className="rounded-3xl border border-zinc-100 bg-zinc-50/80 p-4 dark:border-white/10 dark:bg-white/[0.03]"', 'className="rounded-2xl border border-zinc-100 bg-zinc-50/80 p-3 dark:border-white/10 dark:bg-white/[0.03]"', 2),
    ('className="mb-2 flex items-center justify-between gap-3 text-sm font-black"', 'className="mb-1.5 flex items-center justify-between gap-2.5 text-xs font-black"', 1),
    ('className="mt-2 flex items-center justify-between text-[11px] font-bold text-zinc-400"', 'className="mt-1.5 flex items-center justify-between text-[10px] font-bold text-zinc-400"', 1),
    ('className="grid gap-3 lg:grid-cols-3"', 'className="grid gap-2.5 lg:grid-cols-3"', 1),
    ('className="grid gap-5 border-b border-zinc-100 p-5 dark:border-white/10 lg:grid-cols-[1fr_2fr] lg:items-center"', 'className="grid gap-3.5 border-b border-zinc-100 p-4 dark:border-white/10 lg:grid-cols-[.9fr_2.1fr] lg:items-center"', 1),
    ('className="flex items-center gap-4"', 'className="flex items-center gap-3"', 1),
    ('className="grid h-20 w-20 shrink-0 place-items-center overflow-hidden rounded-[28px] bg-zinc-100 text-2xl font-black text-zinc-500 dark:bg-white/10 dark:text-zinc-200"', 'className="grid h-16 w-16 shrink-0 place-items-center overflow-hidden rounded-2xl bg-zinc-100 text-xl font-black text-zinc-500 dark:bg-white/10 dark:text-zinc-200"', 1),
    ('className="mt-1 truncate text-2xl font-black text-zinc-950 dark:text-white"', 'className="mt-0.5 truncate text-xl font-black text-zinc-950 dark:text-white"', 1),
    ('className="grid gap-3 sm:grid-cols-3"', 'className="grid gap-2.5 sm:grid-cols-3"', 1),
    ('className="rounded-3xl bg-zinc-50 p-4 dark:bg-white/[0.04]"', 'className="rounded-2xl bg-zinc-50 p-3 dark:bg-white/[0.04]"', 3),
    ('className="text-xs font-black text-zinc-400"', 'className="text-[11px] font-black text-zinc-400"', 3),
    ('className="mt-2 text-3xl font-black text-zinc-950 dark:text-white"', 'className="mt-1 text-2xl font-black text-zinc-950 dark:text-white"', 3),
    ('className="px-5 py-3 text-sm font-black text-zinc-400"', 'className="px-4 py-2 text-xs font-black text-zinc-400"', 1),
    ('className="grid gap-4 md:grid-cols-2 xl:grid-cols-4"', 'className="grid gap-3 md:grid-cols-2 xl:grid-cols-4"', 1),
    ('className="grid gap-5 xl:grid-cols-[1.1fr_.9fr]"', 'className="grid gap-4 xl:grid-cols-[1.1fr_.9fr]"', 1),
    ('className="grid gap-5 xl:grid-cols-[.9fr_1.1fr]"', 'className="grid gap-4 xl:grid-cols-[.9fr_1.1fr]"', 1),
    ('className="mb-3 flex items-center gap-3"', 'className="mb-2 flex items-center gap-2.5"', 1),
    ('className="grid h-11 w-11 place-items-center rounded-2xl bg-zinc-950 text-white dark:bg-white dark:text-zinc-950"', 'className="grid h-9 w-9 place-items-center rounded-xl bg-zinc-950 text-white dark:bg-white dark:text-zinc-950"', 1),
    ('<FolderOpen size={17} />', '<FolderOpen size={15} />', 1),
    ('className="mt-2 text-[11px] font-bold text-zinc-400">{project.totalTasks}', 'className="mt-1.5 text-[10px] font-bold text-zinc-400">{project.totalTasks}', 1),
    ('className="rounded-3xl border border-dashed border-zinc-200 p-8 text-center text-sm font-bold text-zinc-400 dark:border-white/10 md:col-span-2"', 'className="rounded-2xl border border-dashed border-zinc-200 p-6 text-center text-xs font-bold text-zinc-400 dark:border-white/10 md:col-span-2"', 1),
    ('className="mt-1 text-xl font-black text-zinc-950 dark:text-white">{t.tasksTable.title}', 'className="mt-0.5 text-lg font-black text-zinc-950 dark:text-white">{t.tasksTable.title}', 1),
    ('className="overflow-x-auto rounded-3xl border border-zinc-100 dark:border-white/10"', 'className="overflow-x-auto rounded-2xl border border-zinc-100 dark:border-white/10"', 1),
    ('className="w-full min-w-[1040px] border-collapse text-right text-sm"', 'className="w-full min-w-[980px] border-collapse text-right text-xs"', 1),
    ('<th className="px-4 py-3">', '<th className="px-3 py-2.5">', 8),
    ('<td className="px-4 py-3">', '<td className="px-3 py-2.5">', 6),
    ('className="max-w-[280px] px-4 py-3 font-black"', 'className="max-w-[260px] px-3 py-2.5 font-black"', 1),
    ('className="px-4 py-3 font-black text-amber-600 dark:text-amber-200"', 'className="px-3 py-2.5 font-black text-amber-600 dark:text-amber-200"', 1),
    ('className="inline-flex items-center gap-2 whitespace-nowrap rounded-xl border border-blue-200 bg-blue-50 px-3 py-2 text-xs font-black text-blue-700 transition hover:border-blue-300 hover:bg-blue-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-400 disabled:cursor-not-allowed disabled:opacity-40 dark:border-blue-400/20 dark:bg-blue-500/10 dark:text-blue-200 dark:hover:bg-blue-500/20"', 'className="inline-flex items-center gap-1.5 whitespace-nowrap rounded-lg border border-blue-200 bg-blue-50 px-2.5 py-1.5 text-[11px] font-black text-blue-700 transition hover:border-blue-300 hover:bg-blue-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-400 disabled:cursor-not-allowed disabled:opacity-40 dark:border-blue-400/20 dark:bg-blue-500/10 dark:text-blue-200 dark:hover:bg-blue-500/20"', 1),
    ('className="bg-white px-4 py-10 text-center text-sm font-bold text-zinc-400 dark:bg-transparent"', 'className="bg-white px-3 py-7 text-center text-xs font-bold text-zinc-400 dark:bg-transparent"', 1),
]

BEHAVIOR_MARKERS = [
    'api.tasks.userDashboard({',
    'useRealtimeVersion(["tasks", "teamPerformance", "projects", "users"]',
    'setDatePreset(',
    'setCustomStart(',
    'setCustomEnd(',
    'setSelectedUserId(',
    'setSelectedJobTitle(',
    'setSelectedProjectId(',
    'getDateRange(',
    'applyFilter',
    'resetFilter',
    'onOpenTask(task)',
    'setDashboardData(',
    'setDashboardError(',
]


def run_git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def git_blob_sha(path):
    data = path.read_bytes()
    header = f"blob {len(data)}\0".encode()
    return hashlib.sha1(header + data).hexdigest()


def sha256_text(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: generate_ux_ui_phase20_team_performance_main.py <repo> <patch-output>")

    repo = Path(sys.argv[1]).resolve()
    patch_path = Path(sys.argv[2]).resolve()
    target = repo / TARGET_FILE

    branch = run_git(repo, "branch", "--show-current")
    head = run_git(repo, "rev-parse", "HEAD")
    if branch != "main":
        raise SystemExit(f"BRANCH={branch}; expected main")
    if head != TARGET_BASE_HEAD:
        raise SystemExit(f"HEAD={head}; expected {TARGET_BASE_HEAD}")
    if not target.is_file():
        raise SystemExit(f"missing target: {TARGET_FILE}")

    blob = git_blob_sha(target)
    if blob != EXPECTED_BLOB:
        raise SystemExit(f"TARGET_BLOB={blob}; expected {EXPECTED_BLOB}")

    tracked_diff = run_git(repo, "diff", "--name-only")
    if tracked_diff:
        raise SystemExit(f"TRACKED_DIFF_NOT_EMPTY={tracked_diff}")

    before = target.read_text(encoding="utf-8")
    after = before
    occurrences = 0

    for index, (old, new, expected_count) in enumerate(REPLACEMENTS, 1):
        count = after.count(old)
        if count != expected_count:
            raise SystemExit(f"ANCHOR_{index}_COUNT={count}; expected {expected_count}")
        after = after.replace(old, new)
        occurrences += expected_count

    if after == before:
        raise SystemExit("NO_CHANGES")

    for marker in BEHAVIOR_MARKERS:
        before_count = before.count(marker)
        after_count = after.count(marker)
        if before_count != after_count:
            raise SystemExit(f"BEHAVIOR_MARKER_CHANGED={marker!r}:{before_count}->{after_count}")

    if before.count("api.") != after.count("api."):
        raise SystemExit("API_CALLS_CHANGED")
    if before.count("useRealtimeVersion(") != after.count("useRealtimeVersion("):
        raise SystemExit("REALTIME_LOGIC_CHANGED")
    if before.count("onOpenTask") != after.count("onOpenTask"):
        raise SystemExit("TASK_OPEN_BEHAVIOR_CHANGED")

    if any(line.rstrip() != line for line in after.splitlines()):
        raise SystemExit("TRAILING_WHITESPACE_DETECTED")

    diff = "".join(difflib.unified_diff(
        before.splitlines(keepends=True),
        after.splitlines(keepends=True),
        fromfile=f"a/{TARGET_FILE}",
        tofile=f"b/{TARGET_FILE}",
    ))
    if not diff:
        raise SystemExit("EMPTY_PATCH")

    patch_path.parent.mkdir(parents=True, exist_ok=True)
    patch_path.write_text(diff, encoding="utf-8")

    new_bytes = after.encode("utf-8")
    new_blob = hashlib.sha1(f"blob {len(new_bytes)}\0".encode() + new_bytes).hexdigest()
    patch_sha256 = hashlib.sha256(diff.encode("utf-8")).hexdigest()

    print(f"TARGET_BASE_HEAD={TARGET_BASE_HEAD}")
    print(f"TARGET_FILE={TARGET_FILE}")
    print(f"EXPECTED_BLOB={EXPECTED_BLOB}")
    print("SOURCE_SCOPE=ONE_FILE")
    print("PERFORMANCE_SCOPE=TEAM_PERFORMANCE_MAIN_ONLY")
    print("PERFORMANCE_PRESENTATION_CHANGED=YES")
    print("DATE_FILTER_PRESENTATION_CHANGED=YES")
    print("USER_FILTERS_PRESENTATION_CHANGED=YES")
    print("USER_SUMMARY_PRESENTATION_CHANGED=YES")
    print("KPI_PRESENTATION_CHANGED=YES")
    print("CHARTS_PRESENTATION_CHANGED=YES")
    print("PROJECT_CARDS_PRESENTATION_CHANGED=YES")
    print("TASK_TABLE_PRESENTATION_CHANGED=YES")
    print("PERFORMANCE_BEHAVIOR_CHANGED=NO")
    print("FILTER_BEHAVIOR_CHANGED=NO")
    print("TASK_OPEN_BEHAVIOR_CHANGED=NO")
    print("API_CALLS_CHANGED=NO")
    print("REALTIME_LOGIC_CHANGED=NO")
    print("ROUTES_CHANGED=NO")
    print("PERMISSIONS_CHANGED=NO")
    print("BACKEND_INCLUDED=NO")
    print(f"REPLACEMENT_ANCHORS={len(REPLACEMENTS)}")
    print(f"REPLACEMENT_OCCURRENCES={occurrences}")
    print(f"SOURCE_BEFORE_SHA256={sha256_text(before)}")
    print(f"SOURCE_AFTER_SHA256={sha256_text(after)}")
    print(f"NEW_BLOB={new_blob}")
    print(f"PATCH_SHA256={patch_sha256}")
    print(f"PATCH_PATH={patch_path}")


if __name__ == "__main__":
    main()
