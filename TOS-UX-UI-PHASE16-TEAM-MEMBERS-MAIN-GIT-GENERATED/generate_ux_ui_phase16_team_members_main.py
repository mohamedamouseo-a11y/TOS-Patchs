#!/usr/bin/env python3
import difflib
import hashlib
import subprocess
import sys
from pathlib import Path

TARGET_BASE_HEAD = "0a38f1d8f03243f0a8be476f862ef7d225841e6c"
TARGET_FILE = "frontend/src/pages/TeamPage.jsx"
EXPECTED_BLOB = "e9e098e3a2e7ac7070ed6c6d6d6c674573a9a222"

MINI_START = "function MiniStat("
MINI_END = "\n\nfunction ProjectsPopupModal("

STATS_START = '      {!showAllTeamPage && <div className={cn("mb-6 grid gap-6 md:grid-cols-5"'
STATS_END = "\n\n      {!showAllTeamPage && <DepartmentManagementPanel"

LIST_TITLE = '<h2 className="text-lg font-black text-zinc-950 dark:text-white">{lang === "en" ? "All Team" : "كل الفريق"}</h2>'
LIST_START = '      <div className="mb-5 rounded-[28px] border border-zinc-100 bg-white p-4 shadow-sm dark:border-white/10 dark:bg-zinc-900/70">'
LIST_END = "\n\n      {selectedDetailUser &&"

MINI_REPLACEMENTS = [
    ('relative grid h-24 w-24 shrink-0 place-items-center rounded-full', 'relative grid h-18 w-18 shrink-0 place-items-center rounded-full', 1),
    ('grid h-[70px] w-[70px] place-items-center rounded-full bg-white shadow-inner', 'grid h-[52px] w-[52px] place-items-center rounded-full bg-white shadow-inner', 1),
    ('text-3xl font-black', 'text-xl font-black', 1),
    ('mt-3 text-sm font-black text-zinc-950 dark:text-white', 'mt-2 text-xs font-black text-zinc-950 dark:text-white', 1),
    ('mt-1 text-xs font-black', 'mt-0.5 text-[10px] font-black', 1),
]

STATS_REPLACEMENTS = [
    ('mb-6 grid gap-6 md:grid-cols-5', 'mb-5 grid gap-4 md:grid-cols-5', 1),
]

LIST_REPLACEMENTS = [
    ('mb-5 rounded-[28px] border border-zinc-100 bg-white p-4 shadow-sm', 'mb-5 rounded-[24px] border border-zinc-100 bg-white p-3.5 shadow-sm', 1),
    ('mb-4 flex flex-wrap items-center justify-between gap-3', 'mb-3 flex flex-wrap items-center justify-between gap-2.5', 1),
    ('mt-1 text-xs font-bold text-zinc-500', 'mt-0.5 text-[11px] font-bold text-zinc-500', 1),
    ('inline-flex items-center gap-2 rounded-2xl bg-zinc-950 px-4 py-2 text-xs font-black', 'inline-flex items-center gap-2 rounded-xl bg-zinc-950 px-3.5 py-2 text-xs font-black', 1),
    ('rounded-2xl border border-zinc-200 px-4 py-2 text-xs font-black text-zinc-700 dark:border-white/10 dark:text-zinc-300', 'rounded-xl border border-zinc-200 px-3.5 py-2 text-xs font-black text-zinc-700 dark:border-white/10 dark:text-zinc-300', 1),
    ('rounded-2xl border border-zinc-200 px-4 py-2 text-xs font-black text-zinc-700 transition hover:border-amber-200', 'rounded-xl border border-zinc-200 px-3.5 py-2 text-xs font-black text-zinc-700 transition hover:border-amber-200', 1),
    ('mb-4 grid gap-3', 'mb-3 grid gap-2.5', 1),
    ('w-full rounded-2xl bg-zinc-50 py-3 text-sm', 'w-full rounded-xl bg-zinc-50 py-2.5 text-sm', 1),
    ('rounded-2xl bg-zinc-50 px-4 py-3 text-sm font-bold', 'rounded-xl bg-zinc-50 px-3.5 py-2.5 text-sm font-bold', 3),
    ('inline-flex items-center justify-center gap-2 rounded-2xl border border-zinc-200 bg-white px-4 py-3 text-xs font-black', 'inline-flex items-center justify-center gap-2 rounded-xl border border-zinc-200 bg-white px-3.5 py-2.5 text-xs font-black', 1),
    ('h-16 animate-pulse rounded-2xl bg-zinc-50', 'h-14 animate-pulse rounded-xl bg-zinc-50', 1),
    ('rounded-2xl bg-zinc-50 p-10 text-center', 'rounded-xl bg-zinc-50 p-7 text-center', 1),
    ('overflow-hidden rounded-[22px] border border-zinc-100', 'overflow-hidden rounded-[18px] border border-zinc-100', 1),
    ('className="px-4 py-3"', 'className="px-3 py-2.5"', 12),
    ('size="h-11 w-11"', 'size="h-10 w-10"', 1),
    ('rounded-full bg-zinc-50 px-3 py-1 text-[11px] font-black', 'rounded-full bg-zinc-50 px-2.5 py-1 text-[10px] font-black', 2),
    ('rounded-full border px-3 py-1 text-[11px] font-black', 'rounded-full border px-2.5 py-1 text-[10px] font-black', 1),
    ('inline-flex items-center gap-2 rounded-full border border-blue-100 bg-blue-50 px-3 py-1 text-xs font-black', 'inline-flex items-center gap-1.5 rounded-full border border-blue-100 bg-blue-50 px-2.5 py-1 text-[11px] font-black', 1),
    ('rounded-xl border border-zinc-200 px-3 py-2 text-xs font-black', 'rounded-lg border border-zinc-200 px-2.5 py-1.5 text-[11px] font-black', 1),
    ('border-t border-zinc-100 bg-zinc-50 p-3 text-center', 'border-t border-zinc-100 bg-zinc-50 p-2.5 text-center', 1),
    ('rounded-2xl bg-white px-5 py-2 text-xs font-black', 'rounded-xl bg-white px-4 py-1.5 text-[11px] font-black', 1),
]

BEHAVIOR_MARKERS = [
    'setShowInviteDrawer(true)',
    'setShowAllTeamPage(false)',
    'setShowAllTeamPage(true)',
    'setSearch(e.target.value)',
    'setDepartmentFilter(e.target.value)',
    'setRoleFilter(e.target.value)',
    'setStatusFilter(e.target.value)',
    'setShowFormerEmployees(true)',
    'setProjectsPopupUser(item)',
    'openMemberDetails(item)',
    'visibleTeamUsers.map((item) => {',
]

EXCLUDED_MARKERS = [
    'function DepartmentManagementPanel(',
    'function FormerEmployeesModal(',
    'function ProjectsPopupModal(',
    'showInviteDrawer && canManageTeamUsers',
    'selectedDetailUser && (() => {',
    'separationRequest.user && (',
    'assignProject.user && (',
]

def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()

def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()

def replace_exact(text, old, new, expected, label):
    count = text.count(old)
    if count != expected:
        raise RuntimeError(f"{label}_COUNT={count}; expected {expected}")
    return text.replace(old, new)

def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: generator.py <repo> <patch-output>")

    repo = Path(sys.argv[1]).resolve()
    patch_path = Path(sys.argv[2]).resolve()

    branch = git(repo, "branch", "--show-current")
    head = git(repo, "rev-parse", "HEAD")
    if branch != "main":
        raise RuntimeError(f"BRANCH={branch}; expected main")
    if head != TARGET_BASE_HEAD:
        raise RuntimeError(f"HEAD={head}; expected {TARGET_BASE_HEAD}")
    if git(repo, "diff", "--name-only"):
        raise RuntimeError("TRACKED_WORKTREE_NOT_CLEAN")

    target = repo / TARGET_FILE
    before = target.read_text()
    blob = git(repo, "hash-object", TARGET_FILE)
    if blob != EXPECTED_BLOB:
        raise RuntimeError(f"BLOB={blob}; expected {EXPECTED_BLOB}")

    if before.count(MINI_START) != 1 or before.count(MINI_END) != 1:
        raise RuntimeError("MINISTAT_BOUNDARY_COUNT_INVALID")
    mini_start = before.index(MINI_START)
    mini_end = before.index(MINI_END, mini_start)

    if before.count(STATS_START) != 1 or before.count(STATS_END) != 1:
        raise RuntimeError("STATS_BOUNDARY_COUNT_INVALID")
    stats_start = before.index(STATS_START)
    stats_end = before.index(STATS_END, stats_start)

    if before.count(LIST_TITLE) != 1:
        raise RuntimeError(f"LIST_TITLE_COUNT={before.count(LIST_TITLE)}; expected 1")
    list_title_pos = before.index(LIST_TITLE)
    list_start = before.rfind(LIST_START, 0, list_title_pos)
    if list_start < 0:
        raise RuntimeError("LIST_START_NOT_FOUND")
    list_end = before.index(LIST_END, list_title_pos)

    if not (mini_start < mini_end < stats_start < stats_end < list_start < list_end):
        raise RuntimeError("BOUNDARY_ORDER_INVALID")

    prefix = before[:mini_start]
    mini = before[mini_start:mini_end]
    between_mini_stats = before[mini_end:stats_start]
    stats = before[stats_start:stats_end]
    between_stats_list = before[stats_end:list_start]
    team_list = before[list_start:list_end]
    suffix = before[list_end:]

    hashes = {
        "PREFIX": digest(prefix),
        "BETWEEN_MINI_STATS": digest(between_mini_stats),
        "BETWEEN_STATS_LIST": digest(between_stats_list),
        "SUFFIX": digest(suffix),
        "MINISTAT_BEFORE": digest(mini),
        "STATS_BEFORE": digest(stats),
        "TEAM_LIST_BEFORE": digest(team_list),
    }

    updated_mini = mini
    for i, (old, new, expected) in enumerate(MINI_REPLACEMENTS, 1):
        updated_mini = replace_exact(updated_mini, old, new, expected, f"MINI_ANCHOR_{i:02d}")

    updated_stats = stats
    for i, (old, new, expected) in enumerate(STATS_REPLACEMENTS, 1):
        updated_stats = replace_exact(updated_stats, old, new, expected, f"STATS_ANCHOR_{i:02d}")

    updated_list = team_list
    for i, (old, new, expected) in enumerate(LIST_REPLACEMENTS, 1):
        updated_list = replace_exact(updated_list, old, new, expected, f"LIST_ANCHOR_{i:02d}")

    after = prefix + updated_mini + between_mini_stats + updated_stats + between_stats_list + updated_list + suffix
    if after == before:
        raise RuntimeError("NO_CHANGE")

    cursor = 0
    for unchanged in [prefix, between_mini_stats, between_stats_list, suffix]:
        found = after.find(unchanged, cursor)
        if found < 0:
            raise RuntimeError("EXCLUDED_SEGMENT_CHANGED")
        cursor = found + len(unchanged)

    for marker in BEHAVIOR_MARKERS + EXCLUDED_MARKERS:
        if before.count(marker) != after.count(marker):
            raise RuntimeError(f"MARKER_COUNT_CHANGED={marker}")

    for marker in ["api.", "useRealtimeRefresh(", "api.users.", "api.projects.", "api.permissions."]:
        if before.count(marker) != after.count(marker):
            raise RuntimeError(f"CALL_COUNT_CHANGED={marker}")

    if any(line.rstrip() != line for line in after.splitlines()):
        raise RuntimeError("TRAILING_WHITESPACE_DETECTED")

    diff = "".join(difflib.unified_diff(
        before.splitlines(True),
        after.splitlines(True),
        fromfile=f"a/{TARGET_FILE}",
        tofile=f"b/{TARGET_FILE}",
    ))
    patch = f"diff --git a/{TARGET_FILE} b/{TARGET_FILE}\n" + diff
    patch_path.write_text(patch)

    new_blob = subprocess.check_output(["git", "hash-object", "--stdin"], input=after, text=True).strip()

    print(f"TARGET_BASE_HEAD={TARGET_BASE_HEAD}")
    print(f"TARGET_FILE={TARGET_FILE}")
    print(f"EXPECTED_BLOB={EXPECTED_BLOB}")
    print(f"NEW_BLOB={new_blob}")
    print(f"PATCH_SHA256={hashlib.sha256(patch.encode()).hexdigest()}")
    print("SOURCE_SCOPE=ONE_FILE")
    print("TEAM_SCOPE=TEAM_MEMBERS_MAIN_ONLY")
    print("MINISTAT_PRESENTATION_CHANGED=YES")
    print("TEAM_LIST_PRESENTATION_CHANGED=YES")
    print("DEPARTMENT_MANAGEMENT_CHANGED=NO")
    print("MEMBER_DETAILS_CHANGED=NO")
    print("INVITE_DRAWER_CHANGED=NO")
    print("FORMER_MEMBERS_CHANGED=NO")
    print("PROJECT_ASSIGNMENT_CHANGED=NO")
    print("PERMISSIONS_UI_CHANGED=NO")
    print("TEAM_BEHAVIOR_CHANGED=NO")
    print("API_CALLS_CHANGED=NO")
    print("ROUTES_CHANGED=NO")
    print("PERMISSIONS_CHANGED=NO")
    print("BACKEND_INCLUDED=NO")
    for key, value in hashes.items():
        print(f"{key}_SHA256={value}")
    print(f"MINISTAT_AFTER_SHA256={digest(updated_mini)}")
    print(f"STATS_AFTER_SHA256={digest(updated_stats)}")
    print(f"TEAM_LIST_AFTER_SHA256={digest(updated_list)}")
    print(f"REPLACEMENTS={len(MINI_REPLACEMENTS)+len(STATS_REPLACEMENTS)+len(LIST_REPLACEMENTS)}")
    print(f"PATCH_PATH={patch_path}")

if __name__ == "__main__":
    main()
