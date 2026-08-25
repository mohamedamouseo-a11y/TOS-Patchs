#!/usr/bin/env python3
import difflib
import hashlib
import subprocess
import sys
from pathlib import Path

TARGET_BASE_HEAD = "9aedaf3b9970c0a036f509b0e6ec800dd814f511"
TARGET_FILE = "frontend/src/pages/TeamPage.jsx"
EXPECTED_BLOB = "813b9e82308dfb3ad8ee4ce4321c3e5527b2bb84"

DETAILS_START = '      {selectedOption && selectedDetails && <div ref={departmentDetailsRef}'
DETAILS_END = '\n    </div>\n  );\n}\nfunction dateTimeLocalValue'

REPLACEMENTS = [
    ('className="mt-5 scroll-mt-28 overflow-hidden rounded-[30px] border border-zinc-100 bg-zinc-50/60 p-4 dark:border-white/10 dark:bg-white/[0.03]"', 'className="mt-4 scroll-mt-28 overflow-hidden rounded-[24px] border border-zinc-100 bg-zinc-50/60 p-3.5 dark:border-white/10 dark:bg-white/[0.03]"', 1),
    ('className="mb-4 flex items-start justify-between gap-3"', 'className="mb-3 flex items-start justify-between gap-2.5"', 1),
    ('className="mt-1 text-2xl font-black text-zinc-950 dark:text-white"', 'className="mt-0.5 text-xl font-black text-zinc-950 dark:text-white"', 1),
    ('className="grid h-10 w-10 place-items-center rounded-2xl border border-zinc-200 bg-white text-zinc-500 dark:border-white/10 dark:bg-zinc-950"', 'className="grid h-9 w-9 place-items-center rounded-xl border border-zinc-200 bg-white text-zinc-500 dark:border-white/10 dark:bg-zinc-950"', 1),
    ('className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_330px]"', 'className="grid gap-3 xl:grid-cols-[minmax(0,1fr)_300px]"', 1),
    ('className="min-w-0 rounded-[26px] border border-zinc-100 bg-white p-4 dark:border-white/10 dark:bg-zinc-900/80"', 'className="min-w-0 rounded-[22px] border border-zinc-100 bg-white p-3.5 dark:border-white/10 dark:bg-zinc-900/80"', 1),
    ('className="flex flex-wrap gap-2 border-b border-zinc-100 pb-3 dark:border-white/10"', 'className="flex flex-wrap gap-1.5 border-b border-zinc-100 pb-2.5 dark:border-white/10"', 1),
    ('"inline-flex items-center gap-2 whitespace-nowrap rounded-2xl px-4 py-2.5 text-xs font-black transition"', '"inline-flex items-center gap-1.5 whitespace-nowrap rounded-xl px-3 py-2 text-[11px] font-black transition"', 1),
    ('activeTab === "info" && <div className="mt-5 grid gap-4 lg:grid-cols-[1fr_1.15fr]"', 'activeTab === "info" && <div className="mt-4 grid gap-3 lg:grid-cols-[1fr_1.15fr]"', 1),
    ('className="rounded-[24px] border border-zinc-100 bg-zinc-50 p-5 dark:border-white/10 dark:bg-white/[0.04]"', 'className="rounded-[20px] border border-zinc-100 bg-zinc-50 p-4 dark:border-white/10 dark:bg-white/[0.04]"', 1),
    ('className="mt-4 space-y-4 text-xs"', 'className="mt-3 space-y-3 text-xs"', 1),
    ('className="rounded-[24px] border border-zinc-100 p-5 dark:border-white/10"', 'className="rounded-[20px] border border-zinc-100 p-4 dark:border-white/10"', 1),
    ('className="mt-4 grid gap-2 sm:grid-cols-2"', 'className="mt-3 grid gap-2 sm:grid-cols-2"', 1),
    ('className="flex min-w-0 items-center gap-2 rounded-2xl bg-zinc-50 p-2.5 dark:bg-white/5"', 'className="flex min-w-0 items-center gap-2 rounded-xl bg-zinc-50 p-2 dark:bg-white/5"', 1),
    ('activeTab === "projects" && isDesignDepartment && <div className="mt-5"', 'activeTab === "projects" && isDesignDepartment && <div className="mt-4"', 1),
    ('className="grid gap-3 rounded-[22px] border border-zinc-100 p-4 text-xs dark:border-white/10 md:grid-cols-[1.5fr_repeat(4,0.7fr)]"', 'className="grid gap-2.5 rounded-[18px] border border-zinc-100 p-3 text-xs dark:border-white/10 md:grid-cols-[1.5fr_repeat(4,0.7fr)]"', 1),
    ('activeTab === "settings" && isDesignDepartment && <div className="mt-5 rounded-[26px] border border-zinc-100 bg-zinc-50/60 p-5 dark:border-white/10 dark:bg-white/[0.03]"', 'activeTab === "settings" && isDesignDepartment && <div className="mt-4 rounded-[22px] border border-zinc-100 bg-zinc-50/60 p-4 dark:border-white/10 dark:bg-white/[0.03]"', 1),
    ('className="grid gap-5 xl:grid-cols-2 xl:divide-x xl:divide-x-reverse xl:divide-zinc-100 dark:xl:divide-white/10"', 'className="grid gap-4 xl:grid-cols-2 xl:divide-x xl:divide-x-reverse xl:divide-zinc-100 dark:xl:divide-white/10"', 2),
    ('className="my-6 border-t border-zinc-100 dark:border-white/10"', 'className="my-5 border-t border-zinc-100 dark:border-white/10"', 1),
    ('className="mt-6 flex justify-end border-t border-zinc-100 pt-5 dark:border-white/10"', 'className="mt-5 flex justify-end border-t border-zinc-100 pt-4 dark:border-white/10"', 1),
    ('className="rounded-2xl bg-violet-600 px-5 py-3 text-sm font-black text-white disabled:opacity-50"', 'className="rounded-xl bg-violet-600 px-4 py-2.5 text-xs font-black text-white disabled:opacity-50"', 1),
    ('activeTab === "activity" && isDesignDepartment && <div className="mt-5"><div className="flex flex-wrap justify-between gap-5 px-2 py-3"', 'activeTab === "activity" && isDesignDepartment && <div className="mt-4"><div className="flex flex-wrap justify-between gap-4 px-1 py-2"', 1),
    ('className="mt-4 rounded-[24px] border border-zinc-100 p-4 dark:border-white/10"', 'className="mt-3 rounded-[20px] border border-zinc-100 p-3.5 dark:border-white/10"', 1),
    ('className="flex items-center justify-between gap-4 py-3"', 'className="flex items-center justify-between gap-3 py-2.5"', 1),
    ('<aside className="rounded-[26px] border border-zinc-100 bg-white p-4 dark:border-white/10 dark:bg-zinc-900/80"><div className="flex items-center justify-between gap-3"><div><div className="text-lg font-black text-zinc-950 dark:text-white">', '<aside className="rounded-[22px] border border-zinc-100 bg-white p-3.5 dark:border-white/10 dark:bg-zinc-900/80"><div className="flex items-center justify-between gap-2.5"><div><div className="text-base font-black text-zinc-950 dark:text-white">', 1),
    ('className="mt-4 space-y-3"', 'className="mt-3 space-y-2.5"', 1),
    ('"rounded-[22px] border p-4"', '"rounded-[18px] border p-3"', 1),
    ('size="h-12 w-12" radius="rounded-full"', 'size="h-10 w-10" radius="rounded-full"', 1),
    ('className="grid h-12 w-12 place-items-center rounded-full bg-white text-zinc-400 dark:bg-zinc-950"', 'className="grid h-10 w-10 place-items-center rounded-full bg-white text-zinc-400 dark:bg-zinc-950"', 1),
    ('className="mt-4 rounded-[22px] border border-zinc-100 bg-zinc-50 p-3 dark:border-white/10 dark:bg-white/[0.04]"', 'className="mt-3 rounded-[18px] border border-zinc-100 bg-zinc-50 p-2.5 dark:border-white/10 dark:bg-white/[0.04]"', 1),
    ('className="mt-3 w-full rounded-xl bg-zinc-950 px-4 py-3 text-xs font-black text-white disabled:opacity-50 dark:bg-white dark:text-zinc-950"', 'className="mt-2.5 w-full rounded-xl bg-zinc-950 px-4 py-2.5 text-xs font-black text-white disabled:opacity-50 dark:bg-white dark:text-zinc-950"', 1),
    ('className="mt-4 rounded-2xl bg-violet-50 px-3 py-3 text-[10px] font-bold leading-5 text-violet-700 dark:bg-violet-500/10 dark:text-violet-200"', 'className="mt-3 rounded-xl bg-violet-50 px-3 py-2.5 text-[10px] font-bold leading-5 text-violet-700 dark:bg-violet-500/10 dark:text-violet-200"', 1),
]

BEHAVIOR_MARKERS = [
    'setSelectedDepartmentKey("")', 'setActiveTab(tab.key)', 'saveLeadership', 'saveDesignSettings',
    'setEditingLeadership', 'setDraftManagerId', 'setDraftDeputyId', 'api.', 'api.users.',
    'api.projects.', 'api.permissions.', 'useRealtimeRefresh(',
]
EXCLUDED_MARKERS = [
    'function MiniStat(', 'selectedDetailUser && (() => {', 'showInviteDrawer && canManageTeamUsers',
    'function FormerEmployeesModal(', 'assignProject.user && (', 'separationRequest.user && (',
    'PermissionOverridesFullPage',
]

def sha256_text(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def git(*args, cwd):
    return subprocess.check_output(["git", *args], cwd=cwd, text=True).strip()

def replace_exact(block, old, new, expected):
    count = block.count(old)
    if count != expected:
        raise SystemExit(f"ANCHOR_COUNT={count}; expected {expected}: {old[:120]}")
    return block.replace(old, new)

def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: generator.py <repo> <patch-output>")
    repo = Path(sys.argv[1]).resolve()
    patch_path = Path(sys.argv[2]).resolve()
    target = repo / TARGET_FILE

    branch = git("branch", "--show-current", cwd=repo)
    head = git("rev-parse", "HEAD", cwd=repo)
    if branch != "main": raise SystemExit(f"BRANCH={branch}; expected main")
    if head != TARGET_BASE_HEAD: raise SystemExit(f"HEAD={head}; expected {TARGET_BASE_HEAD}")
    if git("diff", "--name-only", cwd=repo): raise SystemExit("TRACKED_DIFF_NOT_EMPTY")
    blob = git("hash-object", "--", TARGET_FILE, cwd=repo)
    if blob != EXPECTED_BLOB: raise SystemExit(f"BLOB={blob}; expected {EXPECTED_BLOB}")

    source = target.read_text(encoding="utf-8")
    if source.count(DETAILS_START) != 1:
        raise SystemExit(f"DETAILS_START_COUNT={source.count(DETAILS_START)}; expected 1")
    start = source.index(DETAILS_START)
    post_start = source[start:]
    if post_start.count(DETAILS_END) != 1:
        raise SystemExit(f"POST_START_DETAILS_END_COUNT={post_start.count(DETAILS_END)}; expected 1")
    end = source.index(DETAILS_END, start)

    prefix, details, suffix = source[:start], source[start:end], source[end:]
    before_behavior = {m: source.count(m) for m in BEHAVIOR_MARKERS}
    before_excluded = {m: source.count(m) for m in EXCLUDED_MARKERS}

    changed = details
    replacement_total = 0
    for old, new, expected in REPLACEMENTS:
        changed = replace_exact(changed, old, new, expected)
        replacement_total += expected
    if changed == details: raise SystemExit("NO_DETAILS_CHANGE")

    updated = prefix + changed + suffix
    if updated[:len(prefix)] != prefix: raise SystemExit("UI18_DEPARTMENT_MAIN_CHANGED")
    if updated[-len(suffix):] != suffix: raise SystemExit("OUTSIDE_DETAILS_SUFFIX_CHANGED")
    if before_behavior != {m: updated.count(m) for m in BEHAVIOR_MARKERS}:
        raise SystemExit("DEPARTMENT_BEHAVIOR_CHANGED")
    if before_excluded != {m: updated.count(m) for m in EXCLUDED_MARKERS}:
        raise SystemExit("EXCLUDED_SURFACE_MARKERS_CHANGED")

    patch = "".join(difflib.unified_diff(source.splitlines(keepends=True), updated.splitlines(keepends=True), fromfile=f"a/{TARGET_FILE}", tofile=f"b/{TARGET_FILE}"))
    patch = f"diff --git a/{TARGET_FILE} b/{TARGET_FILE}\n" + patch
    patch_path.write_text(patch, encoding="utf-8")
    raw = updated.encode("utf-8")
    new_blob = hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest()

    print(f"TARGET_BASE_HEAD={TARGET_BASE_HEAD}")
    print(f"TARGET_FILE={TARGET_FILE}")
    print(f"EXPECTED_BLOB={EXPECTED_BLOB}")
    print(f"NEW_BLOB={new_blob}")
    print(f"PATCH_SHA256={hashlib.sha256(patch.encode('utf-8')).hexdigest()}")
    print("SOURCE_SCOPE=ONE_FILE")
    print("DEPARTMENT_DETAILS_SCOPE=DEPARTMENT_DETAILS_ONLY")
    print("UI18_DEPARTMENT_MAIN_CHANGED=NO")
    print("UI17_MEMBER_DETAILS_CHANGED=NO")
    print("INVITE_DRAWER_CHANGED=NO")
    print("FORMER_MEMBERS_CHANGED=NO")
    print("PROJECT_ASSIGNMENT_DIALOG_CHANGED=NO")
    print("SEPARATION_DIALOG_CHANGED=NO")
    print("PERMISSIONS_UI_CHANGED=NO")
    print("DEPARTMENT_BEHAVIOR_CHANGED=NO")
    print("TEAM_BEHAVIOR_CHANGED=NO")
    print("API_CALLS_CHANGED=NO")
    print("ROUTES_CHANGED=NO")
    print("PERMISSIONS_CHANGED=NO")
    print("BACKEND_INCLUDED=NO")
    print(f"PREFIX_SHA256={sha256_text(prefix)}")
    print(f"SUFFIX_SHA256={sha256_text(suffix)}")
    print(f"DETAILS_BLOCK_BEFORE_SHA256={sha256_text(details)}")
    print(f"DETAILS_BLOCK_AFTER_SHA256={sha256_text(changed)}")
    print(f"REPLACEMENTS={replacement_total}")
    print(f"PATCH_PATH={patch_path}")

if __name__ == "__main__":
    main()
